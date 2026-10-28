import asyncio
import json
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright
import os
import random

INPUT_FILE = 'input.xml'
OUTPUT_FILE = 'results.json'
STORAGE_STATE = 'storage_state.json'

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

            await page.wait_for_selector('a[href="#legal"]', timeout=10000)
            await page.click('a[href="#legal"]')

            dialog_selector = '.DomPurify__domPurify___dnz'
            await page.wait_for_selector(dialog_selector, state='visible', timeout=10000)

            content_element = await page.query_selector(dialog_selector)
            if not content_element:
                raise ValueError("Dialog content not found")

            content_html = await content_element.inner_html()
            content_text = await content_element.inner_text()

            if not content_text.strip():
                raise ValueError("Scraped content is empty")

            results.append({
                'url': url,
                'status': 'success',
                'popup_content_html': content_html,
                'popup_content_text': content_text
            })

            print(f"Successfully scraped {url}")

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            results.append({
                'url': url,
                'status': 'error',
                'message': str(e)
            })
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
    urls = [u.text for u in root.findall('url') if u.text]

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


if __name__ == '__main__':
    asyncio.run(run())
