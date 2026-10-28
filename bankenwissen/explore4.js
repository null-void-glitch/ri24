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

  // Search for the Kriterien section - look at its children
  const criteriaSection = await page.evaluate(() => {
    // Find the h3 "Kriterien" element
    const allH3 = Array.from(document.querySelectorAll('h3'));
    const kriterienH3 = allH3.find(h => h.textContent.trim() === 'Kriterien');
    if (!kriterienH3) return { error: 'Kriterien h3 not found' };

    // Get its parent and siblings
    const parent = kriterienH3.closest('section, div[class], article') || kriterienH3.parentElement;
    return {
      parentTag: parent?.tagName,
      parentClass: parent?.className?.substring(0, 100),
      parentHTML: parent?.outerHTML?.substring(0, 3000)
    };
  });
  console.log('Criteria section:', JSON.stringify(criteriaSection, null, 2));

  // Get ALL text content within any element that has "Ansatz" or "Kriterien" text
  const criteriaText = await page.evaluate(() => {
    const fullText = document.body.innerText;
    const idx = fullText.indexOf('Kriterien\nAlle\n');
    if (idx === -1) return 'Kriterien section not found in text';
    return fullText.substring(idx, idx + 5000);
  });
  console.log('\nCriteria text section:', criteriaText);

  await browser.close();
}

main().catch(console.error);
