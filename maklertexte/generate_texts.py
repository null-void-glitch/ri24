"""Befüllt den "Makler Text" im Regionalimmobilien24-Backend per Playwright.

Vollausbau: iteriert regionsweise über ALLE Makler.
  1. Login ins Backend (/adm/)
  2. Regionen-Config -> autoritative Code->Slug-Zuordnung (auch Umlaute)
  3. Je Region: Makler-Liste -> alle Makler-IDs
  4. Je Makler: Region + Profil-Verzeichnis lesen, öffentliches Impressum holen,
     300-Wörter-Vorstellungstext per OpenAI (Web-Suche) erzeugen (OHNE
     Finanzdienstleistungs-Bewerbung), in TinyMCE "Makler Text" schreiben, speichern.

Fortschritt wird nach rollout_log.csv geschrieben (resümierbar/auditierbar).
Alle Selektoren/URLs wurden am echten Backend verifiziert.
"""

from __future__ import annotations

import csv
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from config import Config, load_config
from text_generator import generate_makler_text

BASE_URL = "https://backend.regionalimmobilien24.de"
PUBLIC_BASE = "https://www.regionalimmobilien24.de"

HEADLESS = True        # für sichtbares Debuggen auf False setzen
AUTO_SAVE = True       # generierten Text automatisch speichern
SKIP_FILLED = True     # Makler mit bereits vorhandenem Text überspringen (resümierbar)
LIMIT = None           # max. Anzahl zu befüllender Makler (None = alle); z.B. 2 zum Testen
ONLY_REGIONS = None    # z.B. ["bsi24"] um auf bestimmte Regionen zu beschränken

# Optionale Steuerung per Umgebungsvariablen (für den Parallel-Launcher).
if os.environ.get("ROLLOUT_REGIONS"):
    ONLY_REGIONS = [c.strip() for c in os.environ["ROLLOUT_REGIONS"].split(",") if c.strip()]
if os.environ.get("ROLLOUT_LIMIT"):
    LIMIT = int(os.environ["ROLLOUT_LIMIT"])

LOG_PATH = Path(os.environ.get("ROLLOUT_LOG")) if os.environ.get("ROLLOUT_LOG") \
    else Path(__file__).with_name("rollout_log.csv")


# --- Session / Login --------------------------------------------------------

def _extract_sess(page: Page) -> str | None:
    """Sucht den admsess-Token in der URL oder in Links der Seite."""
    m = re.search(r"admsess=([a-z0-9]+)", page.url)
    if m:
        return m.group(1)
    # Fallback: Token aus einem Link der Seite (z.B. Logout/Menü) lesen.
    href = page.eval_on_selector_all(
        "a[href*='admsess=']",
        "els => (els[0] && els[0].href) || ''",
    )
    m = re.search(r"admsess=([a-z0-9]+)", href or "")
    return m.group(1) if m else None


def login(page: Page, cfg: Config, attempts: int = 3) -> str:
    """Loggt ein und gibt den Session-Token (admsess) zurück (mit Retry)."""
    last_url = ""
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
        sess = _extract_sess(page)
        if sess:
            return sess
        last_url = page.url
        page.wait_for_timeout(1500)  # kurz warten, dann erneut versuchen
    raise RuntimeError(f"Login fehlgeschlagen — keine Session-ID ({last_url}).")


class Backend:
    """Kapselt Page + Session und erneuert die Session bei Ablauf automatisch."""

    def __init__(self, page: Page, cfg: Config) -> None:
        self.page = page
        self.cfg = cfg
        self.sess = login(page, cfg)

    def open(self, path_with_query: str) -> None:
        """Öffnet eine Backend-Seite; re-login, falls die Session abgelaufen ist."""
        url = f"{BASE_URL}{path_with_query}admsess={self.sess}"
        self.page.goto(url, wait_until="networkidle")
        self.page.wait_for_timeout(300)
        if self.page.query_selector("#adm_user") is not None:  # zurück auf Login
            self.sess = login(self.page, self.cfg)
            url = f"{BASE_URL}{path_with_query}admsess={self.sess}"
            self.page.goto(url, wait_until="networkidle")
            self.page.wait_for_timeout(300)


# --- Datenerhebung ----------------------------------------------------------

def load_region_slugs(be: Backend) -> dict[str, str]:
    """Liest die autoritative Code->Slug-Zuordnung aus der Regionen-Config."""
    be.open("/adm/individuell/regionen/config/?")
    rows = be.page.eval_on_selector_all(
        "tr", "els => els.map(r => r.innerText.replace(/\\s+/g,' ').trim())"
    )
    slugs: dict[str, str] = {}
    for row in rows:
        m = re.match(r"^([a-z]+24)\s+/([a-z0-9äöü.\-]+)/\s", row)
        if m:
            slugs[m.group(1)] = m.group(2)
    return slugs


def makler_ids_for_region(be: Backend, region_code: str) -> list[str]:
    """Alle Makler-IDs einer Region (in Reihenfolge, dedupliziert)."""
    be.open(f"/adm/individuell/master/makler/list/?portal={region_code}&")
    be.page.wait_for_timeout(400)
    hrefs = be.page.eval_on_selector_all(
        "a", "els => els.map(a => a.href).filter(h => h.includes('makler/edit'))"
    )
    ids: list[str] = []
    for h in hrefs:
        m = re.search(r"maklerid=([a-zA-Z0-9]+)", h)
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def read_makler_info(be: Backend, maklerid: str) -> dict:
    """Öffnet die Makler-Edit-Seite und liest Name, Profil-URI, aktuellen Text."""
    be.open(f"/adm/individuell/master/makler/edit/?maklerid={maklerid}&")
    be.page.wait_for_timeout(800)
    name = be.page.input_value("#name")
    profil_uri = be.page.input_value("#profil_uri_name").strip()
    current = be.page.input_value("#maklerprofil_dyn_profil_text").strip()
    return {"name": name, "profil_uri": profil_uri, "current": current}


# --- Impressum + Text -------------------------------------------------------

def build_profile_path(profil_uri: str, region_slug: str) -> str:
    return profil_uri.replace("{region}", region_slug).lstrip("/")


def fetch_impressum(page: Page, profile_path: str) -> str:
    """Lädt das Anbieter-Impressum und extrahiert den reinen Impressumsblock."""
    url = f"{PUBLIC_BASE}/{profile_path}impressum/"
    resp = page.goto(url, wait_until="networkidle")
    if not resp or resp.status >= 400:
        return ""
    page.wait_for_timeout(300)
    text = page.inner_text("body")
    start = text.find("Impressum:")
    start = start + len("Impressum:") if start >= 0 else 0
    end = text.find("©", start)
    return text[start:end if end > 0 else None].strip()


def set_makler_text_and_save(be: Backend, maklerid: str, text: str) -> None:
    """Öffnet die Edit-Seite, setzt den TinyMCE-Inhalt und speichert."""
    be.open(f"/adm/individuell/master/makler/edit/?maklerid={maklerid}&")
    be.page.wait_for_timeout(800)
    js = """(html) => {
        const ed = window.tinyMCE && tinyMCE.get('maklerprofil_dyn_profil_text_tiny');
        if (!ed) return 'no-editor';
        ed.setContent(html);
        const out = (typeof transcode4tiny === 'function')
            ? transcode4tiny(ed.getContent(), 'out') : ed.getContent();
        document.getElementById('maklerprofil_dyn_profil_text').value = out;
        return 'ok';
    }"""
    html = "".join(f"<p>{p.strip()}</p>" for p in text.split("\n\n") if p.strip())
    result = be.page.evaluate(js, html)
    if result != "ok":
        raise RuntimeError(f"TinyMCE nicht bereit: {result}")
    if AUTO_SAVE:
        be.page.click("span.btn.pitsafe:has-text('Speichern')")
        be.page.wait_for_timeout(2000)


# --- Logging ----------------------------------------------------------------

def log_result(maklerid: str, name: str, region: str, words: int, status: str) -> None:
    new_file = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new_file:
            w.writerow(["maklerid", "name", "region", "words", "status"])
        w.writerow([maklerid, name, region, words, status])


# --- Orchestrierung ---------------------------------------------------------

def main() -> int:
    cfg = load_config()
    done = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()
        page.on("dialog", lambda d: d.accept())
        be = Backend(page, cfg)
        print(f"Login ok (Session {be.sess}).")

        slugs = load_region_slugs(be)
        print(f"{len(slugs)} Regionen mit Slug geladen.")

        region_codes = ONLY_REGIONS or list(slugs.keys())
        for region_code in region_codes:
            slug = slugs.get(region_code) or cfg.region_mapping.get(region_code, "").lower()
            region_name = cfg.region_mapping.get(region_code, region_code)
            ids = makler_ids_for_region(be, region_code)
            print(f"\n=== {region_code} ({region_name}): {len(ids)} Makler ===")

            for maklerid in ids:
                if LIMIT is not None and done >= LIMIT:
                    print(f"\nLIMIT {LIMIT} erreicht — Stopp.")
                    browser.close()
                    return 0
                try:
                    info = read_makler_info(be, maklerid)
                    if SKIP_FILLED and info["current"]:
                        print(f"  [skip] {info['name']} (bereits befüllt)")
                        log_result(maklerid, info["name"], region_code, 0, "skipped_filled")
                        continue

                    path = build_profile_path(info["profil_uri"], slug)
                    impressum = fetch_impressum(page, path)
                    text = generate_makler_text(
                        cfg.openai_key, impressum, region_name, info["name"]
                    )
                    set_makler_text_and_save(be, maklerid, text)
                    words = len(text.split())
                    done += 1
                    print(f"  [ok]   {info['name']} — {words} Wörter"
                          f"{' (kein Impressum)' if not impressum else ''}")
                    log_result(maklerid, info["name"], region_code, words,
                               "ok" if impressum else "ok_no_impressum")
                except Exception as e:  # ein Fehler soll den Lauf nicht abbrechen
                    print(f"  [ERR]  {maklerid}: {type(e).__name__}: {str(e)[:120]}",
                          file=sys.stderr)
                    log_result(maklerid, "", region_code, 0, f"error:{type(e).__name__}")

        browser.close()
    print(f"\nFertig. {done} Makler befüllt. Log: {LOG_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
