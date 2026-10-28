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

  // Find the Kriterien section and its full structure
  const html = await page.evaluate(() => {
    const allH3 = Array.from(document.querySelectorAll('h3'));
    const kriterienH3 = allH3.find(h => h.textContent.trim() === 'Kriterien');
    if (!kriterienH3) return 'not found';

    // Walk up to find the card container
    let container = kriterienH3.parentElement;
    for (let i = 0; i < 5; i++) {
      if (container.parentElement) container = container.parentElement;
    }
    return container.outerHTML.substring(0, 8000);
  });
  console.log('Kriterien section HTML:', html);

  await browser.close();
}

main().catch(console.error);
