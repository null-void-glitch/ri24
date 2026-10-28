"""Read-only exploration of the /be-admin/ CRM for financing experts.
Logs in, walks the main nav, screenshots each section, dumps structure to JSON.
No writes, no data changes.

Run with the pipx playwright python:
  /home/null/.local/share/pipx/venvs/playwright/bin/python explore_crm.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://backend.regionalimmobilien24.de"
LOGIN_URL = f"{BASE_URL}/be-admin/login/"
POST_URL = f"{BASE_URL}/be-admin/request/check-login/"
EMAIL = "alexander.stumm@regionalimmobilien24.de"
PASSWORD = "e7%qv&$AL123"

OUT_DIR = Path(__file__).with_name("crm_survey")
OUT_DIR.mkdir(exist_ok=True)


def get_session_via_requests() -> str:
    """Login via HTTP requests (curl-like) to get the session ID."""
    import urllib.request
    import urllib.parse
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    fields = {"l": EMAIL, "p": PASSWORD, "goto": ""}
    body_parts = []
    for name, val in fields.items():
        body_parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{val}\r\n"
        )
    body_parts.append(f"--{boundary}--\r\n")
    body = "".join(body_parts).encode()
    req = urllib.request.Request(
        POST_URL,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": LOGIN_URL,
            "Origin": BASE_URL,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        },
        method="POST",
    )
    import ssl
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        raw = resp.read().decode()
    data = json.loads(raw)
    if not data.get("status"):
        raise RuntimeError(f"Login failed: {data}")
    sess = data["data"]["sess"]
    print(f"Session obtained: {sess}")
    return sess


def dump_nav(page) -> list[dict]:
    return page.eval_on_selector_all(
        "a[href]",
        "els => els.map(a => ({text: a.innerText.trim(), href: a.getAttribute('href')})).filter(x => x.text && x.text.length > 1)"
    )


def dump_page_structure(page) -> dict:
    forms = page.eval_on_selector_all(
        "form",
        """els => els.map(f => ({
            action: f.getAttribute('action'),
            method: f.getAttribute('method'),
            fields: Array.from(f.querySelectorAll('input,select,textarea')).map(i => ({
                tag: i.tagName.toLowerCase(),
                type: i.getAttribute('type'),
                name: i.getAttribute('name'),
                id: i.id,
                placeholder: i.getAttribute('placeholder')
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
    headings = page.eval_on_selector_all(
        "h1,h2,h3,h4",
        "els => els.map(h => ({tag: h.tagName, text: h.innerText.trim()}))"
    )
    # Grab visible text of sidebar/nav menus
    nav_items = page.eval_on_selector_all(
        "nav a, .sidebar a, .menu a, .nav a, [class*='nav'] a, [class*='menu'] a, [class*='sidebar'] a",
        "els => [...new Set(els.map(a => a.innerText.trim()))].filter(t => t.length > 1)"
    )
    # Grab card/widget titles (common dashboard patterns)
    card_titles = page.eval_on_selector_all(
        ".card-header, .widget-header, .panel-heading, .box-header, [class*='card'] h2, [class*='card'] h3",
        "els => els.map(e => e.innerText.trim()).filter(t => t)"
    )
    # Grab button labels
    buttons = page.eval_on_selector_all(
        "button, .btn",
        "els => [...new Set(els.map(e => e.innerText.trim()))].filter(t => t.length > 1)"
    )
    # Grab all visible text in main content area
    body_text = page.eval_on_selector(
        "body",
        "el => el.innerText.substring(0, 3000)"
    )
    return {
        "title": page.title(),
        "url": page.url,
        "headings": headings,
        "nav_items": nav_items,
        "card_titles": card_titles,
        "buttons": buttons,
        "forms": forms,
        "tables": tables,
        "body_text_preview": body_text,
    }


def safe_goto(page, url: str, name: str, survey: dict):
    try:
        page.goto(url, wait_until="networkidle", timeout=25000)
        time.sleep(0.8)
        page.screenshot(path=str(OUT_DIR / f"{name}.png"), full_page=True)
        data = dump_page_structure(page)
        survey[name] = data
        print(f"  captured {name} — {data['title']} @ {data['url']}")
    except Exception as e:
        print(f"  [ERR] {name}: {e}")
        survey[name] = {"error": str(e)}


def collect_nav_links(page) -> list[dict]:
    """Collect all unique nav/menu links from the current page."""
    links = page.eval_on_selector_all(
        "a[href]",
        """els => els
            .map(a => ({text: a.innerText.trim(), href: a.href}))
            .filter(x => x.text.length > 1 && x.href && !x.href.startsWith('javascript'))"""
    )
    seen = set()
    unique = []
    for lnk in links:
        key = lnk["href"]
        if key not in seen:
            seen.add(key)
            unique.append(lnk)
    return unique


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium")
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        sess = get_session_via_requests()
        dashboard_url = f"{BASE_URL}/be-admin/dashboard/?sess={sess}"
        page.goto(dashboard_url, wait_until="networkidle")
        time.sleep(1)
        if "/login" in page.url:
            print(f"Session rejected — landed on {page.url}")
            page.screenshot(path=str(OUT_DIR / "login-failed.png"), full_page=True)
            browser.close()
            return 1

        print(f"Logged in — at {page.url}")
        page.screenshot(path=str(OUT_DIR / "00-dashboard.png"), full_page=True)
        survey = {}
        survey["00-dashboard"] = dump_page_structure(page)
        print(f"Dashboard title: {survey['00-dashboard']['title']}")
        print(f"Dashboard URL: {survey['00-dashboard']['url']}")

        # Dump all nav links from dashboard
        nav_links = collect_nav_links(page)
        # Ensure session param is in all internal links
        def with_sess(url: str) -> str:
            if "sess=" not in url and BASE_URL in url:
                sep = "&" if "?" in url else "?"
                return f"{url}{sep}sess={sess}"
            return url

        (OUT_DIR / "nav_links.json").write_text(
            json.dumps(nav_links, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Found {len(nav_links)} links on dashboard.")
        for lnk in nav_links[:80]:
            print(f"  {lnk['text']!r:40s}  {lnk['href']}")

        # Visit each unique internal link that looks like a section
        base_prefix = f"{BASE_URL}/be-admin/"
        visited = {page.url}
        to_visit = [
            lnk for lnk in nav_links
            if lnk["href"].startswith(base_prefix) and lnk["href"] not in visited
        ]

        for i, lnk in enumerate(to_visit[:50], start=1):
            url = with_sess(lnk["href"])
            if url in visited:
                continue
            visited.add(url)
            slug = re.sub(r"[^a-z0-9]+", "-", lnk["text"].lower()).strip("-")[:40] or f"page-{i}"
            name = f"{i:02d}-{slug}"
            safe_goto(page, url, name, survey)
            # After visiting, collect any new sub-links
            sub_links = collect_nav_links(page)
            for sub in sub_links:
                sub_url = with_sess(sub["href"])
                if (sub["href"].startswith(base_prefix)
                        and sub_url not in visited
                        and len(to_visit) < 70):
                    sub["href"] = sub_url
                    to_visit.append(sub)

        (OUT_DIR / "survey.json").write_text(
            json.dumps(survey, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        browser.close()

    print(f"\nDone. {len(survey)} sections captured. See crm_survey/ for output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
