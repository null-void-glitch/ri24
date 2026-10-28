"""Scrapes all pages of the live 'alle Kontaktanfragen' table and saves the
combined row data as 42-kontaktanfragen-rows.json.

Uses JavaScript extraction in Playwright (no bs4 dependency) to work within
the playwright venv.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "maklertexte"))

from playwright.sync_api import sync_playwright
from config import load_config

BASE_URL = "https://backend.regionalimmobilien24.de"
OUT_HTML = Path(__file__).with_name("42-kontaktanfragen.html")
OUT_JSON = Path(__file__).with_name("42-kontaktanfragen-rows.json")

EXTRACT_JS = """
() => {
    const rows = Array.from(document.querySelectorAll('#DataTables_Table_0 tbody tr'));
    return rows.map(tr => {
        const tds = tr.querySelectorAll(':scope > td');
        if (tds.length < 7) return null;

        // td[0]: timestamp block — first token is internal ID, rest is date/time
        const zeitText = tds[0].innerText.trim().replace(/\\s+/g, ' ');
        const zeitParts = zeitText.split(' ');
        const zeitId = zeitParts[0] || '';
        const zeitDatum = zeitParts.slice(1).join(' ');

        // td[1]: Objekt-ID (links to expose)
        const objA = tds[1].querySelector('a');
        const objektId = objA ? objA.innerText.trim() : tds[1].innerText.trim();
        const objektHref = objA ? objA.href : '';

        // td[2]: Objektanschrift
        const objektanschrift = tds[2].innerText.trim();

        // td[3]: Vermarktung/Nutzung — extract img alt texts
        const imgs = Array.from(tds[3].querySelectorAll('img'));
        const vermarktung = imgs.map(i => i.alt || i.title || '').filter(Boolean).join(' / ')
            || tds[3].innerText.trim();

        // td[4]: Name Vorname
        const name = tds[4].innerText.trim();

        // td[5]: Empfänger
        const empfaenger = tds[5].innerText.trim();

        // td[6]: Antwort an
        const antwortAn = tds[6].innerText.trim().replace(/\\s+/g, ' ');

        // td[7]: E-Mail-Text (capped at 400 chars)
        const emailText = tds.length > 7
            ? tds[7].innerText.trim().replace(/\\s+/g, ' ').slice(0, 400)
            : '';

        return { zeitId, zeitDatum, objektId, objektHref, objektanschrift,
                 vermarktung, name, empfaenger, antwortAn, emailText };
    }).filter(Boolean);
}
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


cfg = load_config()

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/home/null/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    print("Logging in...")
    sess = login(page, cfg)
    print(f"Session: {sess}")

    url = f"{BASE_URL}/adm/individuell/master/statistik/kontaktanfragen/?admsess={sess}"
    print(f"Fetching: {url}")
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(2500)

    # Save first-page HTML for structure reference
    OUT_HTML.write_text(page.content(), encoding="utf-8")
    print(f"Saved HTML: {OUT_HTML}")

    # Determine total pages
    page_nums = [
        t.strip()
        for t in page.locator(".dataTables_wrapper a.fg-button").all_text_contents()
        if t.strip().isdigit()
    ]
    total_pages = int(page_nums[-1]) if page_nums else 1
    print(f"Total pages: {total_pages}")

    all_rows = []

    for pg in range(1, total_pages + 1):
        print(f"Page {pg}/{total_pages}...")
        rows = page.evaluate(EXTRACT_JS)
        print(f"  Got {len(rows)} rows")
        all_rows.extend(rows)

        if pg < total_pages:
            page.locator(".dataTables_wrapper a.next").click()
            page.wait_for_timeout(1500)

    browser.close()

print(f"Total rows collected: {len(all_rows)}")

out = {
    "total_real_rows": len(all_rows),
    "rows": all_rows,
}
OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {OUT_JSON} ({OUT_JSON.stat().st_size} bytes)")

for r in all_rows[:3]:
    print(f"  {r['zeitDatum']} | {r['objektId']} | {r['name']} | {r['empfaenger']}")
