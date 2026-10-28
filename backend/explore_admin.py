"""Read-only exploration of the /adm/ backend: logs in, walks the main nav,
screenshots each section and dumps its menu/table/form structure to JSON.
No writes, no saves, no data changes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "maklertexte"))

from playwright.sync_api import sync_playwright  # noqa: E402
from config import load_config  # noqa: E402

BASE_URL = "https://backend.regionalimmobilien24.de"
OUT_DIR = Path(__file__).with_name("admin_survey")
OUT_DIR.mkdir(exist_ok=True)


def extract_sess(page) -> str | None:
    m = re.search(r"admsess=([a-z0-9]+)", page.url)
    if m:
        return m.group(1)
    href = page.eval_on_selector_all(
        "a[href*='admsess=']", "els => (els[0] && els[0].href) || ''"
    )
    m = re.search(r"admsess=([a-z0-9]+)", href or "")
    return m.group(1) if m else None


def login(page, cfg, attempts=3) -> str:
    for _ in range(attempts):
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


def dump_nav(page) -> list[dict]:
    """Grab the main navigation link structure."""
    return page.eval_on_selector_all(
        "a[href]",
        """els => els.map(a => ({text: a.innerText.trim(), href: a.getAttribute('href')}))
            .filter(x => x.text)"""
    )


def dump_page_structure(page) -> dict:
    forms = page.eval_on_selector_all(
        "form",
        """els => els.map(f => ({
            action: f.getAttribute('action'),
            fields: Array.from(f.querySelectorAll('input,select,textarea')).map(i => ({
                tag: i.tagName.toLowerCase(),
                type: i.getAttribute('type'),
                name: i.getAttribute('name'),
                id: i.id
            }))
        }))"""
    )
    tables = page.eval_on_selector_all(
        "table",
        """els => els.map(t => ({
            headers: Array.from(t.querySelectorAll('th')).map(th => th.innerText.trim()),
            rowCount: t.querySelectorAll('tr').length
        }))"""
    )
    return {"title": page.title(), "url": page.url, "forms": forms, "tables": tables}


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "page"


def main() -> int:
    cfg = load_config(Path(__file__).resolve().parent.parent / "maklertexte" / ".env")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        sess = login(page, cfg)
        print(f"Login ok, session={sess}")

        page.screenshot(path=str(OUT_DIR / "00-dashboard.png"), full_page=True)
        survey = {"dashboard": dump_page_structure(page)}
        nav_links = dump_nav(page)
        (OUT_DIR / "nav_links.json").write_text(
            json.dumps(nav_links, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Found {len(nav_links)} links on dashboard.")

        targets = [
            ("01-objekte-list", "/adm/individuell/master/immo/list/?"),
            ("02-makler-list", "/adm/individuell/master/makler/list/?"),
            ("03-makler-new", "/adm/individuell/master/makler/new/?"),
            ("04-regionen-config", "/adm/individuell/regionen/config/?"),
            ("05-team-list", "/adm/individuell/master/team/list/?"),
            ("06-whitelabel-list", "/adm/individuell/master/whitelabel/list/?"),
            ("07-kontaktanfragen", "/adm/individuell/master/statistik/kontaktanfragen/?"),
            ("08-seo-config", "/adm/individuell/master/seo/config/?"),
            ("09-privatanzeigen", "/adm/individuell/master/privatanzeige/?"),
            ("10-suchauftraege", "/adm/individuell/master/suchauftrag/?"),
            ("11-static-sites", "/adm/individuell/static/sites.php?"),
            ("12-baufi-orte", "/adm/individuell/orte/?"),
        ]
        for name, path in targets:
            url = f"{BASE_URL}{path}admsess={sess}"
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / f"{name}.png"), full_page=True)
                survey[name] = dump_page_structure(page)
                print(f"  captured {name}")
            except Exception as e:
                print(f"  [ERR] {name}: {e}")
                survey[name] = {"error": str(e)}

        # Drill into one Makler edit page for the form-field pattern.
        try:
            page.goto(
                f"{BASE_URL}/adm/individuell/master/makler/list/?admsess={sess}",
                wait_until="networkidle",
            )
            href = page.eval_on_selector(
                "a[href*='makler/edit']", "el => el.href"
            )
            if href:
                page.goto(href, wait_until="networkidle")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT_DIR / "13-makler-edit.png"), full_page=True)
                survey["13-makler-edit"] = dump_page_structure(page)
                print("  captured 13-makler-edit")
        except Exception as e:
            print(f"  [ERR] makler-edit: {e}")

        (OUT_DIR / "survey.json").write_text(
            json.dumps(survey, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        browser.close()
    print("Done. See admin_survey/ for output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
