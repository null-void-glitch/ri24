import asyncio
import json
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright
import os
import random

INPUT_FILE = "input2.xml"
OUTPUT_FILE = "results2.json"
STORAGE_STATE = "storage_state.json"

MIN_WAIT = 2
MAX_WAIT = 5
SAVE_INTERVAL = 1000


def atomic_save(path, data):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


async def scrape_urls(context, urls, results, start_index=0):
    for i, url in enumerate(urls[start_index:], start=start_index):
        if not url:
            continue

        if i > 0:
            wait_time = random.uniform(MIN_WAIT, MAX_WAIT)
            print(f"Waiting {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)

        print(f"Visiting: {url}")
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)

            # Wait for agency container
            await page.wait_for_selector(".anbieter", timeout=15000)

            # --- BASIC AGENCY INFO ---
            places = page.locator(".part_address .place")
            count = await places.count()

            name = await places.nth(0).inner_text() if count > 0 else None
            street = await places.nth(1).inner_text() if count > 1 else None
            city = await places.nth(2).inner_text() if count > 2 else None

            # --- CONTACT TABLE ---
            phone = await page.locator('td:has-text("Telefon") + td').inner_text()

            fax_locator = page.locator('td:has-text("Fax") + td')
            fax = (
                await fax_locator.inner_text()
                if await fax_locator.count() > 0
                else None
            )

            website_locator = page.locator('td:has-text("Website") + td a')
            website = (
                await website_locator.get_attribute("href")
                if await website_locator.count() > 0
                else None
            )

            # --- CONTACT PERSON ---
            contact_person_locator = page.locator(".ansprechpartner")
            contact_person = await contact_person_locator.inner_text()

            # --- ADDITIONAL DATA (optional section) ---
            # representative_locator = page.locator(
            #    'td:has-text("Vertretungsberechtigter") + td'
            # )
            # representative = (
            #   await representative_locator.inner_text()
            #    if await representative_locator.count() > 0
            #   else None
            # )

            # trade_register_locator = page.locator('td:has-text("Handelsregister") + td')
            # trade_register = (
            #    await trade_register_locator.inner_text()
            #    if await trade_register_locator.count() > 0
            #    else None
            # )

            # vat_locator = page.locator('td:has-text("USt-IdNr.") + td')
            # vat_id = (
            #    await vat_locator.inner_text()
            #    if await vat_locator.count() > 0
            #    else None
            # )

            results.append(
                {
                    "url": url,
                    "status": "success",
                    "agency_name": name.strip(),
                    "street": street.strip(),
                    "city": city.strip(),
                    "phone": phone.strip(),
                    "fax": fax.strip() if fax else None,
                    "website": website,
                    "contact_person": contact_person.strip(),
                    # "representative": representative.strip()
                    # if representative
                    # else None,
                    # "trade_register": trade_register.strip()
                    # if trade_register
                    # else None,
                    # "vat_id": vat_id.strip() if vat_id else None,
                }
            )

            print(f"Successfully scraped {url}")

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            results.append({"url": url, "status": "error", "message": str(e)})
        finally:
            await page.close()

        if len(results) % SAVE_INTERVAL == 0:
            atomic_save(OUTPUT_FILE, results)
            print(f"Checkpoint saved: {len(results)} items")


async def run():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()
    urls = [u.text for u in root.findall("url") if u.text]

    if not urls:
        print("No URLs found in input file.")
        return

    results = []

    async with async_playwright() as p:
        # --- FIRST RUN: visible browser to accept cookies ---
        if not os.path.exists(STORAGE_STATE):
            print("Launching visible browser to accept cookies...")

            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()

            page = await context.new_page()
            await page.goto(urls[0], timeout=60000)

            print("👉 Please accept cookies in the opened browser.")
            print("⏳ Waiting 15 seconds...")
            await asyncio.sleep(15)

            await context.storage_state(path=STORAGE_STATE)
            await browser.close()

            print("Cookies saved.")

        # --- HEADLESS RUN ---
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STORAGE_STATE)

        await scrape_urls(context, urls, results)

        await browser.close()

    atomic_save(OUTPUT_FILE, results)
    print(f"Final save: {len(results)} items")
    print(f"Done. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(run())
