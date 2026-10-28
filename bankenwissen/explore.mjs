import { chromium } from 'playwright';

const LOGIN_URL = 'https://partnerportal.qualitypool.de/login';
const USERNAME = 'stefanie.rupprecht@regionalimmobilien24.de';
const PASSWORD = 'Asdf1234!';

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Login
  console.log('Navigating to login page...');
  await page.goto(LOGIN_URL, { waitUntil: 'networkidle' });
  console.log('Login page title:', await page.title());
  console.log('Login page URL:', page.url());

  // Take a screenshot to see what we're dealing with
  await page.screenshot({ path: 'login_page.png' });

  // Print the HTML structure
  const html = await page.content();
  console.log('\n--- Page HTML (first 3000 chars) ---');
  console.log(html.substring(0, 3000));

  await browser.close();
}

main().catch(console.error);
