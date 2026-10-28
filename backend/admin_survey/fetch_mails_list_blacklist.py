"""Scrapes E-Mail Liste and Blacklist pages under Kontaktanfragen and saves
their row data as JSON for the prototype build.

E-Mail Liste: /adm/individuell/master/mails/list/
Blacklist:    /adm/individuell/master/mails/blacklist/
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "maklertexte"))

from playwright.sync_api import sync_playwright
from config import load_config

BASE_URL = "https://backend.regionalimmobilien24.de"
OUT_DIR = Path(__file__).resolve().parent

def make_extract_js(table_id):
    return f"""
() => {{
    const tbody = document.querySelector('{table_id} tbody');
    const thead = document.querySelector('{table_id} thead');
    const headers = thead ? Array.from(thead.querySelectorAll('th')).map(th => th.innerText.trim()) : [];
    if (!tbody) return {{headers, rows: []}};
    const rows = Array.from(tbody.querySelectorAll(':scope > tr')).map(tr => {{
        return Array.from(tr.querySelectorAll(':scope > td')).map(td => td.innerText.trim().replace(/\\s+/g, ' '));
    }}).filter(cells => cells.length > 0);
    return {{headers, rows}};
}}
"""


def extract_sess(page):
    m = re.search(r"admsess=([a-z0-9]+)", page.url)
    if m:
        return m.group(1)
    href = page.eval_on_selector_all(
        "a[href*='admsess=']", "els => (els[0] && els[0].href) || ''"
    )
    m = re.search(r"admsess=([a-z0-9]+)", href or "")
    return m.group(1) if m else None


def login(page, cfg):
    for _ in range(3):
        page.goto(f"{BASE_URL}/adm/", wait_until="networkidle")
        page.fill("#adm_user", cfg.username)
        page.fill("#adm_pw", cfg.password)
        page.click("#adm_login_submit")
        page.wait_for_load_state("networkidle")
        try:
            page.wait_for_url(re.compile(r"admsess=[a-z0-9]+"), timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(800)
        sess = extract_sess(page)
        if sess:
            return sess
        page.wait_for_timeout(1500)
    raise RuntimeError("Login failed")


def scrape_page(page, url, table_id, label, out_html, out_json):
    print(f"\n--- {label} ---")
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)
    print(f"Title: {page.title()}")

    # Save HTML
    out_html.write_text(page.content(), encoding="utf-8")
    print(f"Saved HTML: {out_html}")

    result = page.evaluate(make_extract_js(table_id))
    headers = result["headers"]
    print(f"Headers: {headers}")

    # Check pagination
    page_nums = []
    try:
        page_nums = [
            t.strip()
            for t in page.locator(".dataTables_wrapper a.fg-button").all_text_contents()
            if t.strip().isdigit()
        ]
    except Exception:
        pass
    total_pages = int(page_nums[-1]) if page_nums else 1
    print(f"Pages: {total_pages}")

    all_rows = list(result["rows"])
    for pg in range(2, total_pages + 1):
        print(f"  Page {pg}/{total_pages}...")
        page.locator(".dataTables_wrapper a.next").click()
        page.wait_for_timeout(1500)
        r = page.evaluate(make_extract_js(table_id))
        print(f"    {len(r['rows'])} rows")
        all_rows.extend(r["rows"])

    out = {"headers": headers, "total_real_rows": len(all_rows), "rows": all_rows}
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_json} ({len(all_rows)} rows)")
    return out


cfg = load_config()

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/home/null/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    print("Logging in...")
    sess = login(page, cfg)
    print(f"Session: {sess}")

    scrape_page(
        page,
        f"{BASE_URL}/adm/individuell/master/mails/list/?admsess={sess}",
        "#DataTables_Table_0",
        "E-Mail Liste",
        OUT_DIR / "43-mails-list.html",
        OUT_DIR / "43-mails-list-rows.json",
    )

    scrape_page(
        page,
        f"{BASE_URL}/adm/individuell/master/mails/blacklist/?admsess={sess}",
        "#DataTables_Table_0",
        "Blacklist",
        OUT_DIR / "44-mails-blacklist.html",
        OUT_DIR / "44-mails-blacklist-rows.json",
    )

    browser.close()
print("\nDone.")
