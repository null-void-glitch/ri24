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
  await page.goto(SAMPLE_COMPANY, { waitUntil: 'networkidle', timeout: 60000 });

  // Find the grid row containing the criterion and its value
  const gridRows = await page.evaluate(() => {
    // Find all links to kriterien pages
    const links = Array.from(document.querySelectorAll('a[href*="/kriterien/baufinanzierung/"]'));

    const results = [];
    for (const link of links.slice(0, 10)) {
      // Go up to the grid cell, then to grid row
      let cell = link.closest('[style*="display: grid"]');
      if (!cell) continue;

      // Get the parent row (grid row)
      const row = cell.parentElement;
      const rowHTML = row?.outerHTML?.substring(0, 1000);
      const rowText = row?.innerText?.trim();

      results.push({
        criterionName: link.textContent.trim(),
        href: link.getAttribute('href'),
        cellHTML: cell.outerHTML.substring(0, 400),
        rowText: rowText,
        rowHTML: rowHTML
      });
    }
    return results;
  });
  console.log('Grid rows:', JSON.stringify(gridRows, null, 2));

  await browser.close();
}

main().catch(console.error);
