const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const LOGIN_URL = 'https://partnerportal.qualitypool.de/login';
const BASE_URL = 'https://partnerportal.qualitypool.de';
const USERNAME = 'stefanie.rupprecht@regionalimmobilien24.de';
const PASSWORD = 'Asdf1234!';

const DELAY_MS = 1200;
const OUTPUT_DIR = path.join(__dirname, 'output');

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function slugify(str) {
  return str
    .toLowerCase()
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

function parseDataList(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n').map(l => l.trim()).filter(Boolean);

  const criterionUrls = new Map(); // url -> category
  const companyUrls = new Map(); // url -> category

  let currentCategory = 'Allgemein';
  let inCriterionSection = true;

  const criterionSections = [
    'vAllgemeine Kriterien Baufinanzierung',
    'Kriterien Forwarddarlehen',
    'Kriterian KfW Darlehen',
    'Kriterien Prolongation',
    'Kriterien Tilgung',
    'Kriterien Objekt',
    'Kriterien Person',
    'Kriterien weitere Hinweise',
  ];

  const companySections = [
    'Anbieterspezifische Kriterien',
    'Überregionale Anbieter',
    'PSD - Banken',
    'Sparda - Banken',
    'Sparkassen',
    'Volks- und Raiffeisenbanken',
    'Kriterien Bausparen und Bausparkassen',
    'Kriterien Ratenkredite',
  ];

  for (const line of lines) {
    if (line.startsWith('#')) {
      const header = line.replace(/^#+\s*/, '');
      currentCategory = header;
      inCriterionSection = !line.includes('Anbieterspezifische') && !line.includes('Überregionale') &&
        !line.includes('PSD') && !line.includes('Sparda') && !line.includes('Sparkassen') &&
        !line.includes('Volks') && !line.includes('Bausparen') && !line.includes('Ratenkredite');
      continue;
    }

    if (!line.startsWith('http')) continue;

    const url = line.replace(/\?$/, '').trim();

    if (url.includes('/kriterien/')) {
      // Always update to get the most specific category (categorized sections come after the big dump)
      criterionUrls.set(url, currentCategory);
    } else if (url.includes('/company/')) {
      if (!companyUrls.has(url)) {
        companyUrls.set(url, currentCategory);
      }
    }
  }

  return { criterionUrls, companyUrls };
}

async function login(page) {
  console.log('Logging in...');
  await page.goto(LOGIN_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('input[name="username"]', USERNAME);
  await page.fill('input[name="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.toString().includes('/login'), { timeout: 15000 });
  console.log('Logged in successfully');
}

async function scrapeCriterionPage(page, url, category) {
  await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

  const data = await page.evaluate(() => {
    // Get page heading (criterion name)
    const allH3 = Array.from(document.querySelectorAll('h3'));
    const headings = Array.from(document.querySelectorAll('h1, h2, h3'));
    let criterionName = '';
    for (const h of headings.reverse()) {
      const text = h.innerText?.trim();
      if (text && text.length > 5 && !['Kriterien Baufinanzierung', 'Produktanbieter', 'Europace', 'Meine Favoriten'].includes(text)) {
        criterionName = text;
        break;
      }
    }

    // Extract table data
    const rows = document.querySelectorAll('tr');
    const banks = [];
    let headerSkipped = false;

    rows.forEach(row => {
      const cells = row.querySelectorAll('td, th');
      if (cells.length < 2) return;

      const col1 = cells[0]?.innerText?.trim();
      const col2 = cells[1]?.innerText?.trim();

      if (!headerSkipped && (col1 === 'Produzent' || col2 === col1)) {
        headerSkipped = true;
        if (!criterionName && col2) criterionName = col2;
        return;
      }
      if (!col1) return;

      banks.push({ bank: col1, value: col2 || '' });
    });

    return { criterionName, banks };
  });

  return {
    url,
    category,
    criterion_name: data.criterionName,
    criterion_id: url.split('/').pop(),
    scraped_at: new Date().toISOString(),
    banks: data.banks,
  };
}

async function scrapeCompanyPage(page, url, category) {
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });

  const data = await page.evaluate(() => {
    // Bank name
    const h2 = document.querySelector('h2');
    const bankName = h2?.innerText?.trim() || '';

    // Last modified date
    const fullText = document.body.innerText;
    const modifiedMatch = fullText.match(/zuletzt geändert am:\s*([^\n]+)/);
    const lastModified = modifiedMatch ? modifiedMatch[1].trim() : '';

    // News items
    const news = [];
    const allText = document.body.innerText;
    const newsIdx = allText.indexOf('Neuigkeiten');
    const vertriebsIdx = allText.indexOf('Vertriebstipps');
    const formularIdx = allText.indexOf('Formulare & Medien');

    if (newsIdx !== -1) {
      const newsEnd = vertriebsIdx !== -1 ? vertriebsIdx : formularIdx !== -1 ? formularIdx : newsIdx + 2000;
      const newsText = allText.substring(newsIdx + 'Neuigkeiten'.length, newsEnd);
      const newsLines = newsText.split('\n').map(l => l.trim()).filter(Boolean);

      let i = 0;
      while (i < newsLines.length) {
        // Date format: "HH:MM - DD.MM.YY" or "DD.MM.YY"
        const timeMatch = newsLines[i]?.match(/^\d+:\d+\s*-\s*(\d+\.\d+\.\d+)/);
        const dateMatch = newsLines[i]?.match(/^(\d+\.\d+\.\d+)$/);
        if (timeMatch || dateMatch) {
          const date = timeMatch ? timeMatch[1] : dateMatch[1];
          const title = newsLines[i + 1] || '';
          if (title) news.push({ date, title });
          i += 2;
        } else {
          i++;
        }
        if (news.length >= 10) break;
      }
    }

    // Criteria links
    const criteriaLinks = Array.from(document.querySelectorAll('a[href*="/kriterien/baufinanzierung/"]'))
      .map(a => ({
        name: a.innerText.trim(),
        href: a.getAttribute('href')
      }))
      .filter((v, i, arr) => arr.findIndex(x => x.href === v.href) === i);

    return { bankName, lastModified, news, criteriaLinks };
  });

  const companyId = url.split('/company/')[1]?.replace(/\?$/, '');

  return {
    company_id: companyId,
    url,
    category,
    bank_name: data.bankName,
    last_modified: data.lastModified,
    scraped_at: new Date().toISOString(),
    recent_news: data.news,
    criteria_count: data.criteriaLinks.length,
  };
}

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

async function main() {
  const { criterionUrls, companyUrls } = parseDataList(path.join(__dirname, 'data-list.md'));

  console.log(`Found ${criterionUrls.size} unique criterion URLs`);
  console.log(`Found ${companyUrls.size} unique company URLs`);

  ensureDir(path.join(OUTPUT_DIR, 'criteria'));
  ensureDir(path.join(OUTPUT_DIR, 'companies'));
  ensureDir(path.join(OUTPUT_DIR, 'banks'));

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  await login(page);

  // Scrape criterion pages
  console.log('\n--- Scraping criterion pages ---');
  const allCriteriaData = [];
  let criterionIdx = 0;

  for (const [url, category] of criterionUrls) {
    criterionIdx++;
    const criterionId = url.split('/').pop();
    const outputFile = path.join(OUTPUT_DIR, 'criteria', `${criterionId}.json`);

    if (fs.existsSync(outputFile)) {
      console.log(`[${criterionIdx}/${criterionUrls.size}] SKIP ${criterionId} (already scraped)`);
      const existing = JSON.parse(fs.readFileSync(outputFile, 'utf8'));
      allCriteriaData.push(existing);
      continue;
    }

    console.log(`[${criterionIdx}/${criterionUrls.size}] Scraping: ${criterionId}`);

    try {
      const data = await scrapeCriterionPage(page, url, category);
      fs.writeFileSync(outputFile, JSON.stringify(data, null, 2));
      allCriteriaData.push(data);
      console.log(`  -> ${data.banks.length} banks, criterion: "${data.criterion_name}"`);
    } catch (err) {
      console.error(`  ERROR: ${err.message}`);
    }

    await sleep(DELAY_MS);
  }

  // Scrape company pages
  console.log('\n--- Scraping company pages ---');
  let companyIdx = 0;
  const companyDataMap = new Map();

  for (const [url, category] of companyUrls) {
    companyIdx++;
    const companyId = url.split('/company/')[1]?.replace(/\?$/, '');
    const outputFile = path.join(OUTPUT_DIR, 'companies', `${companyId}.json`);

    if (fs.existsSync(outputFile)) {
      console.log(`[${companyIdx}/${companyUrls.size}] SKIP ${companyId} (already scraped)`);
      const existing = JSON.parse(fs.readFileSync(outputFile, 'utf8'));
      if (existing.bank_name) companyDataMap.set(existing.bank_name, existing);
      continue;
    }

    console.log(`[${companyIdx}/${companyUrls.size}] Scraping company: ${companyId}`);

    try {
      const data = await scrapeCompanyPage(page, url, category);
      fs.writeFileSync(outputFile, JSON.stringify(data, null, 2));
      if (data.bank_name) companyDataMap.set(data.bank_name, data);
      console.log(`  -> "${data.bank_name}", modified: ${data.last_modified}, news: ${data.recent_news.length}`);
    } catch (err) {
      console.error(`  ERROR: ${err.message}`);
    }

    await sleep(DELAY_MS);
  }

  // Build bank-pivoted files
  console.log('\n--- Building bank-pivoted files ---');
  const bankData = new Map(); // bankName -> criteria map

  for (const criterionData of allCriteriaData) {
    for (const { bank, value } of criterionData.banks) {
      if (!bankData.has(bank)) {
        bankData.set(bank, { bank, criteria: {} });
      }
      bankData.get(bank).criteria[criterionData.criterion_id] = {
        name: criterionData.criterion_name,
        category: criterionData.category,
        value,
      };
    }
  }

  for (const [bankName, data] of bankData) {
    // Find company data for this bank
    const companyData = companyDataMap.get(bankName);
    if (companyData) {
      data.company_id = companyData.company_id;
      data.company_url = companyData.url;
      data.bank_category = companyData.category;
      data.last_modified = companyData.last_modified;
      data.recent_news = companyData.recent_news;
    }

    const fileName = slugify(bankName) + '.json';
    const outputFile = path.join(OUTPUT_DIR, 'banks', fileName);
    fs.writeFileSync(outputFile, JSON.stringify(data, null, 2));
  }

  console.log(`\nBuilt ${bankData.size} bank files`);

  // Summary index file
  const index = {
    generated_at: new Date().toISOString(),
    total_criteria: allCriteriaData.length,
    total_companies: companyDataMap.size,
    total_banks: bankData.size,
    criteria: allCriteriaData.map(c => ({
      id: c.criterion_id,
      name: c.criterion_name,
      category: c.category,
      bank_count: c.banks.length,
    })),
    banks: Array.from(bankData.entries()).map(([name, d]) => ({
      name,
      criteria_count: Object.keys(d.criteria).length,
      company_id: d.company_id || null,
    })),
  };

  fs.writeFileSync(path.join(OUTPUT_DIR, 'index.json'), JSON.stringify(index, null, 2));
  console.log('\nDone! Output index saved to output/index.json');

  await browser.close();
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
