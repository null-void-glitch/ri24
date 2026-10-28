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
  console.log('Logged in, URL:', page.url());
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  await login(page);

  // Explore criterion page
  console.log('\n=== CRITERION PAGE ===');
  await page.goto(SAMPLE_CRITERION, { waitUntil: 'networkidle', timeout: 30000 });
  console.log('URL:', page.url());

  const criterionHTML = await page.content();
  // Save to file for inspection
  const fs = require('fs');
  fs.writeFileSync('criterion_sample.html', criterionHTML);
  console.log('Saved criterion HTML, length:', criterionHTML.length);

  // Get text content
  const criterionText = await page.evaluate(() => document.body.innerText);
  console.log('\n--- Criterion page text (first 3000 chars) ---');
  console.log(criterionText.substring(0, 3000));

  // Explore company page
  console.log('\n=== COMPANY PAGE ===');
  await page.goto(SAMPLE_COMPANY, { waitUntil: 'networkidle', timeout: 30000 });
  console.log('URL:', page.url());

  const companyHTML = await page.content();
  fs.writeFileSync('company_sample.html', companyHTML);
  console.log('Saved company HTML, length:', companyHTML.length);

  const companyText = await page.evaluate(() => document.body.innerText);
  console.log('\n--- Company page text (first 3000 chars) ---');
  console.log(companyText.substring(0, 3000));

  await browser.close();
}

main().catch(console.error);
