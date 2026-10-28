"""Scrapes the live 'Team' list page and saves HTML + row JSON."""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "maklertexte"))
from playwright.sync_api import sync_playwright
from config import load_config

BASE_URL = "https://backend.regionalimmobilien24.de"
OUT_DIR  = Path(__file__).resolve().parent

def login(page, cfg):
    for _ in range(3):
        page.goto(f"{BASE_URL}/adm/", wait_until="networkidle")
        page.fill("#adm_user", cfg.username)
        page.fill("#adm_pw",   cfg.password)
        page.click("#adm_login_submit")
        page.wait_for_load_state("networkidle")
        try: page.wait_for_url(re.compile(r"admsess=[a-z0-9]+"), timeout=15000)
        except: pass
        page.wait_for_timeout(800)
        m = re.search(r"admsess=([a-z0-9]+)", page.url)
        if m: return m.group(1)
        page.wait_for_timeout(1500)
    raise RuntimeError("Login failed")

INSPECT_JS = """() => {
    const tables = Array.from(document.querySelectorAll('table')).map((t,i) => ({
        id: t.id, cls: t.className,
        headers: Array.from(t.querySelectorAll('th')).map(th => th.innerText.trim()),
        rowCount: t.querySelectorAll('tbody tr').length
    }));
    const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5')).map(h => h.innerText.trim()).filter(Boolean);
    const selects  = Array.from(document.querySelectorAll('select')).map(s => ({
        name: s.name, id: s.id,
        opts: Array.from(s.options).map(o => o.text.trim())
    }));
    const links = Array.from(document.querySelectorAll('a.btn, button')).map(b => b.innerText.trim()).filter(Boolean).slice(0,20);
    return {tables, headings, selects, links};
}"""

EXTRACT_JS = """(tableId) => {
    const tbody = document.querySelector(tableId + ' tbody');
    if (!tbody) return [];
    return Array.from(tbody.querySelectorAll(':scope > tr')).map(tr => {
        const tds = Array.from(tr.querySelectorAll(':scope > td'));
        const img = tr.querySelector('img');
        return {
            cells: tds.map(td => td.innerText.trim().replace(/\\s+/g,' ')),
            imgSrc: img ? img.src : '',
            rowHtml: tr.innerHTML.slice(0, 800)
        };
    }).filter(r => r.cells.length > 0);
}"""

cfg = load_config()
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/home/null/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    print("Logging in...")
    sess = login(page, cfg)
    url  = f"{BASE_URL}/adm/individuell/master/team/list/?admsess={sess}"
    print(f"Fetching {url}")
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)

    info = page.evaluate(INSPECT_JS)
    print("Headings:", info["headings"])
    print("Tables:")
    for t in info["tables"]: print(" ", t)
    print("Selects:", info["selects"])
    print("Buttons:", info["links"])

    # Save HTML
    html = page.content()
    (OUT_DIR / "45-team-list.html").write_text(html, encoding="utf-8")
    print(f"Saved HTML ({len(html)} bytes)")

    # Extract rows from first table
    rows = page.evaluate(f"() => {EXTRACT_JS[2:-2]}('#DataTables_Table_0')")
    if not rows:
        # try plain table
        rows = page.evaluate("""() => {
            const t = document.querySelector('table');
            if (!t) return [];
            return Array.from(t.querySelectorAll('tbody tr')).map(tr => ({
                cells: Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim().replace(/\\s+/g,' ')),
                imgSrc: (tr.querySelector('img') || {src:''}).src,
                rowHtml: tr.innerHTML.slice(0,800)
            })).filter(r=>r.cells.length>0);
        }""")
    print(f"Rows extracted: {len(rows)}")
    if rows:
        print("Sample row[0] cells:", rows[0]["cells"])
        print("Sample row[0] imgSrc:", rows[0]["imgSrc"][:80])

    out = {"total_real_rows": len(rows), "rows": rows}
    (OUT_DIR / "45-team-rows.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Wrote 45-team-rows.json")
    browser.close()
