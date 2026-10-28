const { chromium } = require('playwright');

const LOGIN_URL = 'https://partnerportal.qualitypool.de/login';
const USERNAME = 'stefanie.rupprecht@regionalimmobilien24.de';
const PASSWORD = 'Asdf1234!';

const SAMPLE_CRITERION = 'https://partnerportal.qualitypool.de/produktanbieter/kriterien/baufinanzierung/beleihungsauslauf-eigennutzer-max.-percent?';
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

  // Explore criterion page structure
  console.log('\n=== CRITERION PAGE STRUCTURE ===');
  await page.goto(SAMPLE_CRITERION, { waitUntil: 'networkidle', timeout: 30000 });

  // Try to find the data table
  const criterionData = await page.evaluate(() => {
    // Find all rows in the main content area
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
    return data.slice(0, 30);
  });
  console.log('Table rows:', JSON.stringify(criterionData, null, 2));

  // Find heading/title of the criterion
  const pageTitle = await page.evaluate(() => {
    const h1s = Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.innerText?.trim());
    return h1s;
  });
  console.log('Headings:', pageTitle);

  // Look for any data-testid or specific class patterns
  const mainContent = await page.evaluate(() => {
    // Try to find the main content area
    const main = document.querySelector('main') || document.querySelector('[role="main"]');
    return main ? main.innerText.substring(0, 2000) : 'no main found';
  });
  console.log('Main content:', mainContent);

  // Get all element tags used in the content
  const structure = await page.evaluate(() => {
    const elements = {};
    document.querySelectorAll('*').forEach(el => {
      const tag = el.tagName.toLowerCase();
      elements[tag] = (elements[tag] || 0) + 1;
    });
    return Object.entries(elements).sort((a, b) => b[1] - a[1]).slice(0, 20);
  });
  console.log('\nMost common elements:', structure);

  await browser.close();
}

main().catch(console.error);
