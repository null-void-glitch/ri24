"""SEO-Text-Rollout für die Makler-Landingpage (immobilienportal-partner-werden).

Navigiert pro Region durch:
  edit_region_sites → findet die Makler-Landingpage
  edit_region_page  → findet Sektion "Ansprechpartner"
  edit_region_section → findet Element "Partnerseiten-Inhalt"
  edit_region_element → entsperrt falls nötig, befüllt CKEditor, speichert

Aufruf (Einzelregion):
    ROLLOUT_REGION=aai24 .venv/bin/python rollout_seo.py

Aufruf (alle Regionen):
    .venv/bin/python rollout_seo.py

Optionen:
    AUTO_SAVE=0     Probelauf ohne Speichern
    SKIP_FILLED=1   (Standard) Region überspringen, wenn Text bereits regionalisiert ist
    WORKERS=3       Parallelität (default 3)
    ROLLOUT_REGIONS=aai24,ami24   nur diese Regionen
"""

from __future__ import annotations

import asyncio
import csv
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright

from config import load_config
from generate_texts import BASE_URL
from rollout_parallel import do_login, open_backend
from seo_text_generator import generate_seo_text

WORKERS      = int(os.environ.get("WORKERS", "3"))
AUTO_SAVE    = os.environ.get("AUTO_SAVE", "1") != "0"
SKIP_FILLED  = os.environ.get("SKIP_FILLED", "1") != "0"
ONLY_REGION  = os.environ.get("ROLLOUT_REGION", "")
ONLY_REGIONS = (
    [c.strip() for c in os.environ["ROLLOUT_REGIONS"].split(",") if c.strip()]
    if os.environ.get("ROLLOUT_REGIONS") else None
)
EXCLUDE_REGIONS = {
    c.strip()
    for c in os.environ.get("EXCLUDE_REGIONS", "").split(",")
    if c.strip()
}
LOG_PATH = Path(os.environ.get("ROLLOUT_LOG", "rollout_seo_log.csv"))

PAGE_DIR        = "immobilienportal-partner-werden"
SECTION_KEYWORD = "Ansprechpartner"
ELEMENT_KEYWORD = "Partnerseiten-Inhalt"

# CKEditor: liest Inhalt des ersten (einzigen) Editors auf der Seite.
READ_JS = """() => {
    if (!window.CKEDITOR) return '';
    const keys = Object.keys(CKEDITOR.instances);
    if (!keys.length) return '';
    return CKEDITOR.instances[keys[0]].getData();
}"""

# CKEditor: befüllt den ersten Editor und synchronisiert die Textarea.
FILL_JS = """(html) => {
    if (!window.CKEDITOR) return 'no-CKEDITOR';
    const keys = Object.keys(CKEDITOR.instances);
    if (!keys.length) return 'no-editor';
    const editor = CKEDITOR.instances[keys[0]];
    if (!editor) return 'no-instance';
    if (editor.status !== 'ready') return 'not-ready:' + editor.status;
    editor.setData(html);
    editor.updateElement();   // Synct CKEditor → Textarea (Pflicht vor Form-Submit)
    return 'ok';
}"""


# ── Zustand ──────────────────────────────────────────────────────────────────

class State:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sess = ""
        self.log_lock = asyncio.Lock()
        self.login_lock = asyncio.Lock()
        # Serialisiert ALLE Backend-Zugriffe (Lesen + Schreiben) pro Session.
        self.backend_lock = asyncio.Lock()

    async def log(self, code: str, region: str, chars: int, status: str) -> None:
        async with self.log_lock:
            new = not LOG_PATH.exists()
            with LOG_PATH.open("a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if new:
                    w.writerow(["code", "region", "chars", "status"])
                w.writerow([code, region, chars, status])


# ── Backend-Navigation ───────────────────────────────────────────────────────

async def find_page_id(page, st: State, code: str) -> str | None:
    """Gibt die page_id der Makler-Landingpage für diese Region zurück."""
    async with st.backend_lock:
        await open_backend(
            page, st,
            f"/adm/individuell/regionen/edit_region_sites.php?regio={code}&")
        await page.wait_for_timeout(800)
        rows = await page.evaluate(f"""() => {{
            const rows = [];
            document.querySelectorAll('tr.form_inline').forEach(tr => {{
                const dirInput = tr.querySelector('input[name="dir"]');
                const editLink = tr.querySelector('a[href*="edit_region_page"]');
                if (dirInput && editLink) {{
                    rows.push({{ dir: dirInput.value, href: editLink.href }});
                }}
            }});
            return rows;
        }}""")
        for r in rows:
            if PAGE_DIR in r["dir"]:
                m = re.search(r"page_id=([a-z0-9]+)", r["href"])
                return m.group(1) if m else None
    return None


async def find_section_id(page, st: State, code: str, page_id: str) -> str | None:
    """Gibt die section_id der Ansprechpartner-Sektion zurück."""
    async with st.backend_lock:
        await open_backend(
            page, st,
            f"/adm/individuell/regionen/edit_region_page.php"
            f"?regio={code}&page_id={page_id}&")
        await page.wait_for_timeout(600)
        rows = await page.evaluate("""() => {
            const rows = [];
            document.querySelectorAll('tr.form_inline').forEach(tr => {
                const bez = tr.querySelector('input[name="section_bez"]');
                const id_ = tr.querySelector('input[name="section_id"]');
                if (bez && id_) rows.push({ bez: bez.value, id: id_.value });
            });
            return rows;
        }""")
        for r in rows:
            if SECTION_KEYWORD in r["bez"]:
                return r["id"]
    return None


async def find_element_info(
    page, st: State, code: str, page_id: str, section_id: str
) -> dict | None:
    """Gibt {'element_id': str, 'locked': bool, 'copy_id': str} zurück.

    Schloss-Logik des CMS:
      GESPERRT  → Link hat element_id=X&copy=Y  (Schloss-Icon; Klick erstellt Kopie Y)
      EDITIERBAR → Link hat element_id=X ohne copy=  (offenes Schloss; direkter Edit)
      ZURÜCKSETZEN → Link hat old_element_id=X&new_element_id=Y  (ignorieren)
    """
    async with st.backend_lock:
        await open_backend(
            page, st,
            f"/adm/individuell/regionen/edit_region_section.php"
            f"?regio={code}&page_id={page_id}&section_id={section_id}&")
        await page.wait_for_timeout(600)

        links = await page.eval_on_selector_all(
            "a[href*='edit_region_element']",
            "els => els.map(a => ({ href: a.href, "
            "label: (a.closest('tr') || a).innerText.replace(/\\s+/g,' ').trim().slice(0,120) }))"
        )

    for lnk in links:
        href = lnk["href"]
        label = lnk["label"]

        if ELEMENT_KEYWORD not in label:
            continue
        if "old_element_id" in href:
            continue  # Zurücksetzen-Spalte — ignorieren

        m_eid  = re.search(r"element_id=([a-z0-9]+)", href)
        m_copy = re.search(r"copy=([a-z0-9]+)", href)
        if not m_eid:
            continue

        eid     = m_eid.group(1)
        copy_id = m_copy.group(1) if m_copy else ""

        if copy_id:
            # Geschlossenes Schloss: element_id=X&copy=Y → entsperren nötig
            return {"element_id": eid, "locked": True, "copy_id": copy_id}
        else:
            # Offenes Schloss: element_id=X ohne copy → direkt editierbar
            return {"element_id": eid, "locked": False, "copy_id": ""}

    return None


async def read_and_fill(
    page, st: State, code: str, page_id: str, section_id: str,
    element_info: dict, html: str
) -> tuple[str, str]:
    """Öffnet das Element (entsperrt falls nötig), liest Inhalt, füllt und speichert.

    Gibt (alter_inhalt, save_btn_typ) zurück.
    """
    async with st.backend_lock:
        if element_info["locked"]:
            # Schloss-Icon-URL: erstellt Kopie copy_id und öffnet deren Editor.
            path = (
                f"/adm/individuell/regionen/edit_region_element.php"
                f"?regio={code}&page_id={page_id}&section_id={section_id}"
                f"&element_id={element_info['element_id']}"
                f"&copy={element_info['copy_id']}&"
            )
        else:
            path = (
                f"/adm/individuell/regionen/edit_region_element.php"
                f"?regio={code}&page_id={page_id}&section_id={section_id}"
                f"&element_id={element_info['element_id']}&"
            )
        await open_backend(page, st, path)
        # CKEditor braucht etwas Zeit zum Initialisieren.
        for _ in range(6):
            await page.wait_for_timeout(700)
            status = await page.evaluate(
                "() => window.CKEDITOR "
                "? (Object.keys(CKEDITOR.instances)[0] "
                "   ? CKEDITOR.instances[Object.keys(CKEDITOR.instances)[0]].status "
                "   : 'no-instance') "
                ": 'no-CKEDITOR'"
            )
            if status == "ready":
                break

        old_content = await page.evaluate(READ_JS)

        if html:
            result = await page.evaluate(FILL_JS, html)
            if result != "ok":
                raise RuntimeError(f"CKEditor fill fehlgeschlagen: {result!r}")
            if AUTO_SAVE:
                # Speichern-Button: nach dem Entsperren ist es ein
                # <input type="submit" class="display fixed"> ohne value-Text.
                # Fallback auf den allgemeinen Speichern-Button.
                saved = await page.evaluate("""() => {
                    const b1 = document.querySelector('input[type="submit"].display.fixed');
                    if (b1) { b1.click(); return 'display-fixed'; }
                    const b2 = document.querySelector('input[type="submit"][value="Speichern"]');
                    if (b2) { b2.click(); return 'value-speichern'; }
                    const b3 = document.querySelector('input.btn-primary.pitsafe');
                    if (b3) { b3.click(); return 'btn-primary'; }
                    const b4 = document.querySelector('input[type="submit"]');
                    if (b4) { b4.click(); return 'generic-submit'; }
                    return 'not-found';
                }""")
                if saved == "not-found":
                    raise RuntimeError("Kein Speichern-Button gefunden")
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    await page.wait_for_timeout(3000)
                await page.wait_for_timeout(400)
                return old_content, saved

    return old_content, "dry_run"


# ── Region verarbeiten ───────────────────────────────────────────────────────

async def process_region(page, st: State, code: str, region_name: str) -> None:
    prefix = f"[{code} / {region_name}]"

    try:
        # Seiten-ID ermitteln.
        page_id = await find_page_id(page, st, code)
        if not page_id:
            print(f"  {prefix}  Makler-Landingpage nicht gefunden — übersprungen")
            await st.log(code, region_name, 0, "skip:no_page")
            return

        # Sektions-ID ermitteln.
        section_id = await find_section_id(page, st, code, page_id)
        if not section_id:
            print(f"  {prefix}  Sektion Ansprechpartner nicht gefunden — übersprungen")
            await st.log(code, region_name, 0, "skip:no_section")
            return

        # Element-Info ermitteln.
        el_info = await find_element_info(page, st, code, page_id, section_id)
        if not el_info:
            print(f"  {prefix}  Element '{ELEMENT_KEYWORD}' nicht gefunden — übersprungen")
            await st.log(code, region_name, 0, "skip:no_element")
            return

        locked_marker = f" [Schloss→copy={el_info['copy_id']}]" if el_info["locked"] else ""
        print(f"  {prefix}  page={page_id}  sect={section_id}  "
              f"el={el_info['element_id']!r}{locked_marker}")

        # Aktuellen Inhalt lesen (ohne Schreiben — für SKIP_FILLED-Check).
        old_content, _ = await read_and_fill(
            page, st, code, page_id, section_id, el_info, html="")

        if SKIP_FILLED and old_content:
            name_lower = region_name.lower().split()[0]  # erstes Wort (z.B. "aachen")
            if name_lower in old_content.lower():
                print(f"  {prefix}  bereits regionalisiert — übersprungen")
                await st.log(code, region_name, len(old_content), "skip:already_filled")
                return

        # Text generieren (in Thread, nicht blockierend).
        print(f"  {prefix}  generiere Text …")
        html = await asyncio.to_thread(
            generate_seo_text, st.cfg.openai_key, region_name)

        # Befüllen + Speichern.
        _, save_btn = await read_and_fill(
            page, st, code, page_id, section_id, el_info, html=html)

        status = "filled" if AUTO_SAVE else "dry_run"
        locked_note = "+entsperrt" if el_info["locked"] else ""
        preview = html[:120].replace("\n", " ")
        print(f"  {prefix}  {status}{locked_note}  btn={save_btn}  {len(html)} Z.")
        print(f"  {prefix}  Vorschau: {preview!r}")
        await st.log(code, region_name, len(html), status + locked_note)

    except Exception as exc:
        print(f"  {prefix}  FEHLER: {type(exc).__name__}: {str(exc)[:120]}")
        await st.log(code, region_name, 0, f"error:{type(exc).__name__}")


# ── Hauptprogramm ────────────────────────────────────────────────────────────

async def main() -> None:
    cfg = load_config()
    st = State(cfg)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        pages = [await ctx.new_page() for _ in range(WORKERS)]
        for pg in pages:
            pg.on("dialog", lambda d: asyncio.create_task(d.accept()))

        st.sess = await do_login(pages[0], cfg)
        print(f"Login ok (sess={st.sess[:8]}…)  {WORKERS} Worker")
        if not AUTO_SAVE:
            print("AUTO_SAVE=0 — Probelauf, kein Speichern.")

        # Alle Regionen aus der Config-Seite lesen.
        await open_backend(pages[0], st, "/adm/individuell/regionen/config/?")
        await pages[0].wait_for_timeout(800)
        rows = await pages[0].eval_on_selector_all(
            "tr", "els => els.map(r => r.innerText.replace(/\\s+/g,' ').trim())")

        all_codes: list[str] = []
        for row in rows:
            m = re.match(r"^([a-z]+24)\s", row)
            if m:
                all_codes.append(m.group(1))

        if not all_codes:
            print("Keine Regionen gefunden.")
            await browser.close()
            return

        # Das Vatermodell hat keine Regionskennung (kein xxx24-Code) und
        # erscheint daher nicht in all_codes — alle gefundenen Codes sind echte Regionen.
        work_codes = all_codes
        print(f"Regionen gefunden: {len(work_codes)}")

        # Filter anwenden.
        if ONLY_REGION:
            work_codes = [c for c in work_codes if c == ONLY_REGION]
        elif ONLY_REGIONS:
            work_codes = [c for c in work_codes if c in ONLY_REGIONS]
        if EXCLUDE_REGIONS:
            work_codes = [c for c in work_codes if c not in EXCLUDE_REGIONS]
            print(f"Ausgeschlossen:  {sorted(EXCLUDE_REGIONS)}")

        if not work_codes:
            print("Keine passenden Regionen nach Filter — Abbruch.")
            await browser.close()
            return

        print(f"Nach Filter:     {len(work_codes)}\n")

        # Queue befüllen.
        queue: asyncio.Queue = asyncio.Queue()
        for code in work_codes:
            region_name = cfg.region_mapping.get(code, code)
            queue.put_nowait((code, region_name))

        done = 0
        total = len(work_codes)

        async def worker(pg):
            nonlocal done
            while True:
                try:
                    code, region_name = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                await process_region(pg, st, code, region_name)
                done += 1
                print(f"  → {done}/{total} abgeschlossen")

        await asyncio.gather(*(worker(pg) for pg in pages))
        await browser.close()

    print(f"\n{'='*60}")
    print(f"Fertig.  Log: {LOG_PATH}")
    print('='*60)


if __name__ == "__main__":
    asyncio.run(main())
