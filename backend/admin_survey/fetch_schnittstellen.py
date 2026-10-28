"""Scrapes both Schnittstellen sub-pages: Sitemaps (Mitula) and Statischer Immobilien Export."""
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
        tag: el.tagName.toLowerCase(), type: el.type||'', name: el.name||'', id: el.id||'',
        value: el.tagName==='SELECT'
            ? Array.from(el.options).filter(o=>o.selected).map(o=>o.text.trim()).join(', ')
            : (el.value||'').slice(0,120),
        checked: el.checked||false,
        label: (() => {
            if (el.id) { const l=document.querySelector('label[for="'+el.id+'"]'); if(l) return l.innerText.trim().slice(0,100); }
            const p=el.closest('li,td,div.control-group,div.form-group,p');
            return p ? p.innerText.trim().slice(0,100) : '';
        })()
    }));
    const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5')).map(h=>h.innerText.trim()).filter(Boolean);
    const tables = Array.from(document.querySelectorAll('table')).map((t,i)=>({
        id:t.id, cls:t.className,
        headers:Array.from(t.querySelectorAll('th')).map(th=>th.innerText.trim()),
        rowCount:t.querySelectorAll('tbody tr').length
    }));
    const links = Array.from(document.querySelectorAll('a.btn,button')).map(b=>({
        text:b.innerText.trim().slice(0,60), href:b.href||b.getAttribute('href')||''
    })).filter(b=>b.text).slice(0,30);
    return {inputs, headings, tables, links};
}"""

EXTRACT_ROWS_JS = """() => {
    const tables = Array.from(document.querySelectorAll('table'));
    return tables.map(t => ({
        id: t.id,
        cls: t.className,
        headers: Array.from(t.querySelectorAll('th')).map(th=>th.innerText.trim()),
        rows: Array.from(t.querySelectorAll('tbody tr')).slice(0,60).map(tr=>({
            cells: Array.from(tr.querySelectorAll('td')).map(td=>td.innerText.trim().replace(/\\s+/g,' ').slice(0,120)),
            links: Array.from(tr.querySelectorAll('a')).map(a=>({text:a.innerText.trim(),href:a.href}))
        })).filter(r=>r.cells.length>0)
    }));
}"""

cfg = load_config()
pages_to_scrape = [
    ("mitula",  f"{BASE_URL}/adm/individuell/master/interface/mitula/",        "49-mitula"),
    ("static",  f"{BASE_URL}/adm/individuell/master/interface/immo/static/",   "49-immo-static"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/home/null/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    print("Logging in...")
    sess = login(page, cfg)

    for key, base_url, prefix in pages_to_scrape:
        url = f"{base_url}?admsess={sess}"
        print(f"\n{'='*60}")
        print(f"Fetching {key}: {url}")
        page.goto(url, wait_until="load", timeout=60000)
        page.wait_for_timeout(2000)

        info = page.evaluate(INSPECT_JS)
        print("Headings:", info["headings"])
        print("Tables:", info["tables"])
        print("Buttons:", info["links"])
        print(f"Inputs ({len(info['inputs'])}):")
        for inp in info["inputs"]:
            if inp["type"] != "hidden":
                lbl = inp['label'][:60]
                val = inp['value'][:60]
                print(f"  [{inp['tag']} {inp['type']}] name={inp['name']!r} label={lbl!r} val={val!r} checked={inp['checked']}")

        tables_data = page.evaluate(EXTRACT_ROWS_JS)
        for t in tables_data:
            print(f"\n  Table id={t['id']!r} cls={t['cls']!r} headers={t['headers']}")
            for row in t["rows"][:5]:
                print(f"    cells: {row['cells']}")

        html_content = page.content()
        (OUT_DIR / f"{prefix}.html").write_text(html_content, encoding="utf-8")
        out = {"inspect": info, "tables": tables_data}
        (OUT_DIR / f"{prefix}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nSaved {prefix}.html ({len(html_content)} bytes) + {prefix}.json")

    browser.close()
