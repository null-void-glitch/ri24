"""Scrapes the Whitelabel-Lizenzen list page and any discoverable sub-pages."""
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
            : (el.value||'').slice(0,80),
        label: (() => {
            if (el.id) { const l=document.querySelector('label[for="'+el.id+'"]'); if(l) return l.innerText.trim().slice(0,80); }
            const p=el.closest('li,td,div.control-group,div.form-group,p');
            return p ? p.innerText.trim().slice(0,80) : '';
        })()
    }));
    const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5')).map(h=>h.innerText.trim()).filter(Boolean);
    const tables = Array.from(document.querySelectorAll('table')).map((t,i)=>({
        id:t.id, cls:t.className,
        headers:Array.from(t.querySelectorAll('th')).map(th=>th.innerText.trim()),
        rowCount:t.querySelectorAll('tbody tr').length
    }));
    const links = Array.from(document.querySelectorAll('a')).map(a=>({
        text:a.innerText.trim().slice(0,60), href:a.href||''
    })).filter(a=>a.href&&a.href.includes('whitelabel')).slice(0,30);
    const btns = Array.from(document.querySelectorAll('a.btn,button')).map(b=>({
        text:b.innerText.trim(), href:b.href||b.getAttribute('data-href')||''
    })).slice(0,20);
    return {inputs, headings, tables, links, btns};
}"""

EXTRACT_JS = """() => {
    const t = document.querySelector('table');
    if (!t) return [];
    return Array.from(t.querySelectorAll('tbody tr')).map(tr => ({
        cells: Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim().replace(/\\s+/g,' ')),
        links: Array.from(tr.querySelectorAll('a')).map(a=>({text:a.innerText.trim(),href:a.href||''}))
    })).filter(r=>r.cells.length>0);
}"""

cfg = load_config()
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/home/null/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    print("Logging in...")
    sess = login(page, cfg)

    url = f"{BASE_URL}/adm/individuell/master/whitelabel/list/?admsess={sess}"
    print(f"Fetching {url}")
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)

    info = page.evaluate(INSPECT_JS)
    print("Headings:", info["headings"])
    print("Tables:")
    for t in info["tables"]: print(" ", t)
    print("Whitelabel links:")
    for l in info["links"]: print(" ", l)
    print("Buttons:", info["btns"])
    print(f"Inputs ({len(info['inputs'])}):")
    for inp in info["inputs"][:10]:
        print(f"  [{inp['tag']} {inp['type']}] name={inp['name']!r} val={inp['value']!r}")

    rows = page.evaluate(EXTRACT_JS)
    print(f"\nTable rows: {len(rows)}")
    for r in rows[:5]:
        print(" cells:", r["cells"])
        print(" links:", r["links"])

    html = page.content()
    (OUT_DIR / "48-whitelabel-list.html").write_text(html, encoding="utf-8")
    print(f"\nSaved 48-whitelabel-list.html ({len(html)} bytes)")

    # Save inspect + rows
    out = {"inspect": info, "rows": rows, "total": len(rows)}
    (OUT_DIR / "48-whitelabel-list.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Now try to find and scrape the edit sub-page (first row)
    if rows and rows[0]["links"]:
        edit_href = rows[0]["links"][0]["href"] if rows[0]["links"] else None
        if edit_href and "whitelabel" in edit_href:
            print(f"\nFetching edit page: {edit_href}")
            page.goto(edit_href, wait_until="load", timeout=60000)
            page.wait_for_timeout(2000)
            edit_info = page.evaluate(INSPECT_JS)
            print("Edit headings:", edit_info["headings"])
            print("Edit tables:", edit_info["tables"])
            print(f"Edit inputs ({len(edit_info['inputs'])}):")
            for inp in edit_info["inputs"]:
                if inp["type"] != "hidden":
                    print(f"  [{inp['tag']} {inp['type']}] name={inp['name']!r} label={inp['label']!r} val={inp['value']!r}")
            edit_html = page.content()
            (OUT_DIR / "48-whitelabel-edit.html").write_text(edit_html, encoding="utf-8")
            print(f"Saved 48-whitelabel-edit.html ({len(edit_html)} bytes)")
            edit_out = {"inspect": edit_info, "edit_url": edit_href}
            (OUT_DIR / "48-whitelabel-edit.json").write_text(
                json.dumps(edit_out, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    browser.close()
