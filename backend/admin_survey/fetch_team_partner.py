"""Scrapes the team member Partner-Status edit page."""
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
            ? Array.from(el.options).filter(o=>o.selected).map(o=>({val:o.value,text:o.text.trim()}))
            : (el.value || '').slice(0, 120),
        placeholder: el.placeholder || '',
        checked: el.checked || false,
        label: (() => {
            if (el.id) {
                const lbl = document.querySelector('label[for="' + el.id + '"]');
                if (lbl) return lbl.innerText.trim().slice(0,80);
            }
            const p = el.closest('li,td,div.control-group,div.form-group,p');
            return p ? p.innerText.trim().slice(0,80) : '';
        })()
    }));
    const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5')).map(h=>h.innerText.trim()).filter(Boolean);
    const imgs = Array.from(document.querySelectorAll('img')).map(i=>i.src).filter(s=>s.startsWith('http')).slice(0,10);
    const links = Array.from(document.querySelectorAll('a.btn,button')).map(b=>({text:b.innerText.trim(),href:b.href||''})).slice(0,15);
    return {inputs, headings, imgs, links};
}"""

cfg = load_config()
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/home/null/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    print("Logging in...")
    sess = login(page, cfg)

    url = f"{BASE_URL}/adm/individuell/master/team/edit/partner/?admsess={sess}&id=123"
    print(f"Fetching {url}")
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)

    info = page.evaluate(INSPECT_JS)
    print("Headings:", info["headings"])
    print("Images:", info["imgs"])
    print("Buttons/links:", info["links"])
    print(f"\nInputs ({len(info['inputs'])}):")
    for inp in info["inputs"]:
        print(f"  [{inp['tag']} type={inp['type']}] name={inp['name']!r} id={inp['id']!r}")
        print(f"    label={inp['label']!r}")
        if inp['tag'] == 'select':
            print(f"    options (first 5): {inp['value'][:5]}")
        else:
            print(f"    value={inp['value']!r}  checked={inp['checked']}")

    html = page.content()
    (OUT_DIR / "47-team-partner.html").write_text(html, encoding="utf-8")
    print(f"\nSaved 47-team-partner.html ({len(html)} bytes)")

    (OUT_DIR / "47-team-partner-inspect.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    browser.close()
