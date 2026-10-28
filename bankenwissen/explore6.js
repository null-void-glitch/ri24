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

  // Find the right panel content area (not sidemenu)
  const mainContent = await page.evaluate(() => {
    // Get the main content area excluding the sidemenu
    const sidemenu = document.querySelector('#sidemenu');
    const allDivs = Array.from(document.querySelectorAll('div'));

    // Find the main content area (should be to the right of the sidemenu)
    // Look for the Allianz section
    const allH2 = Array.from(document.querySelectorAll('h2'));
    const allianzH2 = allH2.find(h => h.textContent.includes('Allianz'));
    if (!allianzH2) return 'h2 not found';

    // Get its containing card
    const card = allianzH2.closest('.mantine-Card-root');
    return card ? card.innerText.substring(0, 5000) : 'card not found';
  });
  console.log('Main content text:', mainContent);

  // Find the criteria table/list - look for the section containing "Ansatz Elterngeld"
  const criteriaContent = await page.evaluate(() => {
    const allText = document.body.innerText;
    const idx = allText.indexOf('Ansatz Elterngeld');
    if (idx === -1) return 'Ansatz not found';

    // Go back to find the criterion and its value
    const section = allText.substring(Math.max(0, idx - 100), idx + 2000);
    return section;
  });
  console.log('\nAround Ansatz Elterngeld:', criteriaContent);

  // Look for criterion-value pairs structure in the DOM
  const criteriaDOM = await page.evaluate(() => {
    // Find elements containing "Ansatz Elterngeld"
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    const matches = [];
    while (node = walker.nextNode()) {
      if (node.textContent.includes('Ansatz Elterngeld')) {
        const parent = node.parentElement;
        const grandParent = parent?.parentElement;
        const greatGrand = grandParent?.parentElement;
        matches.push({
          text: node.textContent.trim(),
          parentTag: parent?.tagName,
          parentClass: parent?.className?.substring(0, 80),
          grandParentTag: grandParent?.tagName,
          grandParentHTML: grandParent?.outerHTML?.substring(0, 500),
          greatGrandHTML: greatGrand?.outerHTML?.substring(0, 500)
        });
      }
    }
    return matches;
  });
  console.log('\nDom elements with Ansatz Elterngeld:', JSON.stringify(criteriaDOM, null, 2));

  await browser.close();
}

main().catch(console.error);
