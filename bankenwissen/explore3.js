const { chromium } = require('playwright');

const LOGIN_URL = 'https://partnerportal.qualitypool.de/login';
const USERNAME = 'stefanie.rupprecht@regionalimmobilien24.de';
const PASSWORD = 'Asdf1234!';
const SAMPLE_COMPANY = 'https://partnerportal.qualitypool.de/produktanbieter/company/d20e1661cfb855966663a1094d37c68b?';

async function login(page) {
  await page.goto(LOGIN_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('input[name="username"]', USERNAME);
  await page.fill('input[name="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.toString().includes('/login'), { timeout: 15000 });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  await login(page);

  console.log('\n=== COMPANY PAGE STRUCTURE ===');
  await page.goto(SAMPLE_COMPANY, { waitUntil: 'networkidle', timeout: 60000 });

  // Get table rows (criteria section)
  const tableRows = await page.evaluate(() => {
    const rows = document.querySelectorAll('tr');
    const data = [];
    rows.forEach(row => {
      const cells = row.querySelectorAll('td, th');
      if (cells.length >= 2) {
        data.push({
          col1: cells[0]?.innerText?.trim(),
          col2: cells[1]?.innerText?.trim()
        });
      }
    });
    return data.slice(0, 50);
  });
  console.log('Table rows (first 50):', JSON.stringify(tableRows, null, 2));

  // Get page headings
  const headings = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('h1, h2, h3, h4')).map(h => ({
      tag: h.tagName,
      text: h.innerText.trim()
    }));
  });
  console.log('\nHeadings:', JSON.stringify(headings, null, 2));

  // Get all table count
  const tableCount = await page.evaluate(() => document.querySelectorAll('table').length);
  console.log('\nNumber of tables:', tableCount);

  // Get total row count
  const rowCount = await page.evaluate(() => document.querySelectorAll('tr').length);
  console.log('Total tr elements:', rowCount);

  await browser.close();
}

main().catch(console.error);
