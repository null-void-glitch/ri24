"""Read-only survey of the /be-admin/ CRM for financing experts.
Uses requests (no browser) — session via URL ?sess=... param.
Walks all nav links, extracts structure, saves HTML + JSON summary.

Run with:
  /home/null/work/ri24/maklertexte/.venv/bin/python survey_crm.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://backend.regionalimmobilien24.de"
LOGIN_URL = f"{BASE_URL}/be-admin/login/"
POST_URL = f"{BASE_URL}/be-admin/request/check-login/"
EMAIL = "alexander.stumm@regionalimmobilien24.de"
PASSWORD = "e7%qv&$AL123"

OUT_DIR = Path(__file__).with_name("crm_survey")
OUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9",
}


def login() -> tuple[requests.Session, str]:
    s = requests.Session()
    s.headers.update(HEADERS)
    resp = s.post(
        POST_URL,
        files={"l": (None, EMAIL), "p": (None, PASSWORD), "goto": (None, "")},
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer": LOGIN_URL,
            "Origin": BASE_URL,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("status"):
        raise RuntimeError(f"Login failed: {data}")
    sess = data["data"]["sess"]
    print(f"Logged in — sess={sess}")
    return s, sess


def add_sess(url: str, sess: str) -> str:
    if not url or url.startswith("javascript") or url.startswith("#"):
        return ""
    if not url.startswith("http"):
        url = urljoin(BASE_URL, url)
    parsed = urlparse(url)
    if not parsed.netloc or BASE_URL.split("//")[1] not in parsed.netloc:
        return ""  # external
    qs = parse_qs(parsed.query, keep_blank_values=True)
    qs["sess"] = [sess]
    new_query = urlencode({k: v[0] for k, v in qs.items()})
    return urlunparse(parsed._replace(query=new_query))


def extract_structure(soup: BeautifulSoup, url: str) -> dict:
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""

    headings = [
        {"tag": h.name, "text": h.get_text(strip=True)}
        for h in soup.find_all(["h1", "h2", "h3", "h4"])
        if h.get_text(strip=True)
    ]

    # Nav/sidebar menu items
    nav_texts = []
    for nav in soup.find_all(["nav", "ul"], class_=re.compile(r"nav|menu|sidebar", re.I)):
        for a in nav.find_all("a"):
            t = a.get_text(strip=True)
            if t and t not in nav_texts:
                nav_texts.append(t)

    # Tables
    tables = []
    for tbl in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
        rows = tbl.find_all("tr")
        tables.append({"headers": headers, "row_count": len(rows)})

    # Forms
    forms = []
    for form in soup.find_all("form"):
        fields = []
        for f in form.find_all(["input", "select", "textarea"]):
            fields.append({
                "tag": f.name,
                "type": f.get("type"),
                "name": f.get("name"),
                "placeholder": f.get("placeholder"),
            })
        forms.append({
            "action": form.get("action"),
            "method": form.get("method", "get"),
            "fields": fields,
        })

    # Card/widget/panel titles
    card_titles = []
    for sel in ["card-header", "widget-header", "panel-heading", "box-header", "box-title"]:
        for el in soup.find_all(class_=re.compile(sel, re.I)):
            t = el.get_text(strip=True)
            if t and t not in card_titles:
                card_titles.append(t)

    # Buttons
    buttons = list({btn.get_text(strip=True) for btn in soup.find_all(["button", "a"], class_=re.compile(r"btn", re.I)) if btn.get_text(strip=True)})

    # Main content text preview (first 3000 chars)
    body = soup.find("body")
    body_text = body.get_text(separator="\n", strip=True)[:3000] if body else ""

    return {
        "title": title_text,
        "url": url,
        "headings": headings,
        "nav_items": nav_texts,
        "card_titles": card_titles,
        "buttons": buttons[:30],
        "forms": forms,
        "tables": tables,
        "body_text_preview": body_text,
    }


def collect_links(soup: BeautifulSoup, sess: str) -> list[dict]:
    links = []
    seen_urls = set()
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        url = add_sess(a["href"], sess)
        if not url or url in seen_urls:
            continue
        if "/be-admin/" not in url:
            continue
        seen_urls.add(url)
        links.append({"text": text, "href": url})
    return links


def slugify(text: str, i: int) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]
    return f"{i:02d}-{s}" if s else f"{i:02d}-page"


def fetch_page(s: requests.Session, url: str) -> BeautifulSoup | None:
    try:
        resp = s.get(url, timeout=20)
        if resp.status_code != 200:
            print(f"    HTTP {resp.status_code}")
            return None
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"    Error: {e}")
        return None


def main() -> int:
    s, sess = login()

    dashboard_url = f"{BASE_URL}/be-admin/dashboard/?sess={sess}"
    soup = fetch_page(s, dashboard_url)
    if not soup:
        print("Failed to load dashboard")
        return 1

    survey = {}
    structure = extract_structure(soup, dashboard_url)
    survey["00-dashboard"] = structure
    (OUT_DIR / "00-dashboard.html").write_text(soup.prettify(), encoding="utf-8")
    print(f"Dashboard: {structure['title']}")
    print(f"Body preview:\n{structure['body_text_preview'][:500]}\n")

    # Collect all nav links
    all_links = collect_links(soup, sess)
    (OUT_DIR / "nav_links.json").write_text(
        json.dumps(all_links, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Found {len(all_links)} links on dashboard:")
    for lnk in all_links:
        print(f"  {lnk['text']!r:40s}  {lnk['href']}")

    # BFS over internal links
    visited = {dashboard_url}
    queued = {lnk["href"] for lnk in all_links}
    to_visit = [lnk for lnk in all_links if lnk["href"] not in visited]
    i = 1

    while to_visit and i <= 60:
        lnk = to_visit.pop(0)
        url = lnk["href"]
        if url in visited:
            continue
        visited.add(url)
        name = slugify(lnk["text"], i)
        print(f"  [{i:02d}] {lnk['text']!r:35s}  {url}")
        page_soup = fetch_page(s, url)
        if not page_soup:
            survey[name] = {"error": "fetch failed", "url": url}
            i += 1
            continue
        struct = extract_structure(page_soup, url)
        survey[name] = struct
        (OUT_DIR / f"{name}.html").write_text(page_soup.prettify(), encoding="utf-8")
        # Collect sub-links — only queue URLs not yet seen in any queue
        sub_links = collect_links(page_soup, sess)
        for sub in sub_links:
            if sub["href"] not in queued and sub["href"] not in visited:
                to_visit.append(sub)
                queued.add(sub["href"])
        time.sleep(0.3)
        i += 1

    (OUT_DIR / "survey.json").write_text(
        json.dumps(survey, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nDone. {len(survey)} pages captured → crm_survey/survey.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
