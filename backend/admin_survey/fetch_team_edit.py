"""Scrapes the team member edit page and saves HTML for offline analysis."""
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
    const inputs = Array.from(document.querySelectorAll('input,select,textarea')).map(el => ({
        tag: el.tagName.toLowerCase(),
        type: el.type || '',
        name: el.name || '',
        id: el.id || '',
        value: el.tagName === 'SELECT'
            ? Array.from(el.options).filter(o=>o.selected).map(o=>o.text).join(', ')
            : (el.value || '').slice(0, 80),
        placeholder: el.placeholder || '',
        label: (() => {
            if (el.id) {
                const lbl = document.querySelector('label[for="' + el.id + '"]');
                if (lbl) return lbl.innerText.trim();
            }
            const parent = el.closest('td,div,li,p');
            if (parent) return parent.innerText.trim().slice(0,60);
            return '';
        })()
    }));
    const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5')).map(h=>h.innerText.trim()).filter(Boolean);
    const tables = Array.from(document.querySelectorAll('table')).map((t,i) => ({
        id: t.id, cls: t.className,
        headers: Array.from(t.querySelectorAll('th')).map(th=>th.innerText.trim()),
        rowCount: t.querySelectorAll('tbody tr').length
    }));
    const imgs = Array.from(document.querySelectorAll('img')).map(i=>i.src).filter(Boolean).slice(0,20);
    const tabs = Array.from(document.querySelectorAll('.nav-tabs a, ul.tabs a')).map(a=>a.innerText.trim()).filter(Boolean);
    return {inputs, headings, tables, imgs, tabs};
}"""

cfg = load_config()
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/home/null/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    print("Logging in...")
    sess = login(page, cfg)

    # Scrape edit page for id=123 (first row)
    url = f"{BASE_URL}/adm/individuell/master/team/edit/?admsess={sess}&id=123"
    print(f"Fetching {url}")
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)

    info = page.evaluate(INSPECT_JS)
    print("Headings:", info["headings"])
    print("Tabs:", info["tabs"])
    print("Tables:", info["tables"])
    print("Images:", info["imgs"][:5])
    print(f"\nInputs ({len(info['inputs'])}):")
    for inp in info["inputs"]:
        print(f"  [{inp['tag']} type={inp['type']}] name={inp['name']!r} id={inp['id']!r}")
        print(f"    label={inp['label']!r}  value={inp['value']!r}")

    html = page.content()
    (OUT_DIR / "46-team-edit.html").write_text(html, encoding="utf-8")
    print(f"\nSaved 46-team-edit.html ({len(html)} bytes)")

    # Also dump full inspect info as JSON
    (OUT_DIR / "46-team-edit-inspect.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Saved 46-team-edit-inspect.json")
    browser.close()
