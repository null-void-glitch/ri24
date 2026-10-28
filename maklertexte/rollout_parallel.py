"""Paralleler Makler-Text-Vollausbau — EIN Login, mehrere Browser-Seiten.

Das Backend erlaubt pro Account nur eine aktive Login-Session (ein zweiter
Login entwertet die erste). Mehrere Seiten unter DERSELBEN Session sind aber
unproblematisch. Daher: einmal einloggen, dann N Worker-Seiten parallel
arbeiten lassen; die OpenAI-Generierung läuft nebenläufig in Threads.

Wall-Clock ≈ serielle Dauer / WORKERS. Aufruf:
    .venv/bin/python rollout_parallel.py
    WORKERS=6 .venv/bin/python rollout_parallel.py
"""

from __future__ import annotations

import asyncio
import csv
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright

from config import load_config
from generate_texts import BASE_URL, PUBLIC_BASE, build_profile_path
from text_generator import generate_makler_text

WORKERS = int(os.environ.get("WORKERS", "5"))
SKIP_FILLED = os.environ.get("SKIP_FILLED", "1") != "0"
AUTO_SAVE = os.environ.get("AUTO_SAVE", "1") != "0"
LIMIT = int(os.environ["ROLLOUT_LIMIT"]) if os.environ.get("ROLLOUT_LIMIT") else None
ONLY_REGIONS = (
    [c.strip() for c in os.environ["ROLLOUT_REGIONS"].split(",") if c.strip()]
    if os.environ.get("ROLLOUT_REGIONS") else None
)
LOG_PATH = Path(os.environ.get("ROLLOUT_LOG", "rollout_log.csv"))

FILL_JS = """(html) => {
    const ed = window.tinyMCE && tinyMCE.get('maklerprofil_dyn_profil_text_tiny');
    if (!ed) return 'no-editor';
    ed.setContent(html);
    const out = (typeof transcode4tiny === 'function')
        ? transcode4tiny(ed.getContent(), 'out') : ed.getContent();
    document.getElementById('maklerprofil_dyn_profil_text').value = out;
    return 'ok';
}"""


# --- gemeinsamer Zustand ----------------------------------------------------

class State:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sess = ""
        self.done = 0
        self.skipped = 0
        self.errors = 0
        self.log_lock = asyncio.Lock()
        self.login_lock = asyncio.Lock()
        # Serialisiert das Laden der Edit-Seite + Befüllen + Speichern.
        # Verhindert, dass parallele Workers gleichzeitig verschiedene Makler-
        # Editierseiten öffnen und dadurch den serverseitigen Session-Zustand
        # des Backends gegenseitig überschreiben (falscher Text landet bei
        # falschem Makler). Text-Generierung läuft weiterhin parallel.
        self.save_lock = asyncio.Lock()

    async def log(self, maklerid, name, region, words, status):
        async with self.log_lock:
            new = not LOG_PATH.exists()
            with LOG_PATH.open("a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if new:
                    w.writerow(["maklerid", "name", "region", "words", "status"])
                w.writerow([maklerid, name, region, words, status])


# --- Backend-Helfer (async) -------------------------------------------------

async def do_login(page, cfg, attempts=5) -> str:
    # Jeder Versuch ist gekapselt: ein transienter Fehler (Timeout/Netz-Blip)
    # führt zu einem erneuten Versuch statt zu einer Exception, die sonst den
    # Re-Login-Sturm auslösen würde. domcontentloaded statt networkidle, damit
    # hängende Sub-Requests den Login nicht blockieren.
    last = ""
    for _ in range(attempts):
        try:
            await page.goto(f"{BASE_URL}/adm/", wait_until="domcontentloaded",
                            timeout=30000)
            await page.fill("#adm_user", cfg.username)
            await page.fill("#adm_pw", cfg.password)
            await page.click("#adm_login_submit")
            try:
                await page.wait_for_url(re.compile(r"admsess=[a-z0-9]+"), timeout=15000)
            except Exception:
                pass
            await page.wait_for_timeout(800)
            m = re.search(r"admsess=([a-z0-9]+)", page.url)
            if m:
                return m.group(1)
            href = await page.eval_on_selector_all(
                "a[href*='admsess=']", "els => (els[0] && els[0].href) || ''")
            m = re.search(r"admsess=([a-z0-9]+)", href or "")
            if m:
                return m.group(1)
            last = page.url
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:80]}"
        await page.wait_for_timeout(1500)
    raise RuntimeError(f"Login fehlgeschlagen ({last}).")


async def open_backend(page, st: State, path_with_query: str) -> None:
    """Öffnet eine Backend-Seite; re-login bei Session-Verlust.

    Wichtig: Das Backend erlaubt nur EINE aktive Session pro Account — ein
    zweiter Login entwertet den ersten. Bei Ablauf laufen alle Worker
    gleichzeitig auf die Login-Seite; es darf aber nur EINER neu einloggen,
    die anderen übernehmen die erneuerte Session. Der Guard prüft daher, ob
    sich st.sess seit dem eigenen letzten Stand geändert hat (nicht bloß, ob
    die Login-Maske sichtbar ist) — sonst entwerten sich die Logins gegenseitig
    (Login-Sturm, der nie konvergiert)."""
    used = st.sess
    await page.goto(f"{BASE_URL}{path_with_query}admsess={st.sess}",
                    wait_until="domcontentloaded")
    if await page.query_selector("#adm_user") is not None:
        async with st.login_lock:
            if st.sess == used:      # noch kein anderer Worker hat erneuert
                st.sess = await do_login(page, st.cfg)
        await page.goto(f"{BASE_URL}{path_with_query}admsess={st.sess}",
                        wait_until="domcontentloaded")


async def list_region(page, st: State, code: str) -> list[str]:
    # Unter paralleler Last liefert die Liste-Seite gelegentlich (noch) keine
    # Makler-Links zurück (networkidle feuert vor dem Rendern der Tabelle).
    # Daher: explizit auf einen Makler-Link warten und bei 0 Treffern erneut
    # laden. Genuin leere Regionen laufen in den Timeout und liefern [].
    ids: list[str] = []
    for attempt in range(3):
        await open_backend(page, st, f"/adm/individuell/master/makler/list/?portal={code}&")
        try:
            await page.wait_for_selector("a[href*='makler/edit']", timeout=8000)
        except Exception:
            await page.wait_for_timeout(800)
        hrefs = await page.eval_on_selector_all(
            "a", "els => els.map(a => a.href).filter(h => h.includes('makler/edit'))")
        ids = []
        for h in hrefs:
            m = re.search(r"maklerid=([a-zA-Z0-9]+)", h)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
        if ids:
            break
        await page.wait_for_timeout(800)
    return ids


async def read_info(page, st: State, maklerid: str) -> dict:
    await open_backend(page, st, f"/adm/individuell/master/makler/edit/?maklerid={maklerid}&")
    await page.wait_for_timeout(700)
    if f"maklerid={maklerid}" not in page.url:
        raise RuntimeError(
            f"Backend lud falsche Seite (erwartet maklerid={maklerid}, URL={page.url[:120]})")
    # TinyMCE leert das hidden-Input beim Laden — daher Inhalt direkt über den
    # Editor lesen; Fallback auf das Hidden-Input falls TinyMCE noch nicht bereit.
    current = await page.evaluate("""() => {
        const ed = window.tinyMCE && tinyMCE.get('maklerprofil_dyn_profil_text_tiny');
        if (ed) {
            const html = ed.getContent();
            const tmp = document.createElement('div');
            tmp.innerHTML = html;
            return tmp.innerText.trim();
        }
        return document.getElementById('maklerprofil_dyn_profil_text')?.value?.trim() || '';
    }""")
    return {
        "name": await page.input_value("#name"),
        "profil_uri": (await page.input_value("#profil_uri_name")).strip(),
        "current": current,
    }


async def fetch_impressum(page, profile_path: str) -> str:
    url = f"{PUBLIC_BASE}/{profile_path}impressum/"
    resp = await page.goto(url, wait_until="networkidle")
    if not resp or resp.status >= 400:
        return ""
    await page.wait_for_timeout(250)
    text = await page.inner_text("body")
    start = text.find("Impressum:")
    start = start + len("Impressum:") if start >= 0 else 0
    end = text.find("©", start)
    return text[start:end if end > 0 else None].strip()


async def fill_and_save(page, st: State, maklerid: str, text: str) -> None:
    # save_lock: Editierseite laden + befüllen + speichern als atomare Sequenz.
    # Kein anderer Worker darf zwischen dem Laden dieser Seite und dem Speichern
    # eine andere Makler-Editierseite öffnen (verhindert Session-State-Überschneidung).
    async with st.save_lock:
        await open_backend(page, st, f"/adm/individuell/master/makler/edit/?maklerid={maklerid}&")
        await page.wait_for_timeout(700)
        if f"maklerid={maklerid}" not in page.url:
            raise RuntimeError(
                f"Backend lud falsche Seite (erwartet maklerid={maklerid}, URL={page.url[:120]})")
        html = "".join(f"<p>{p.strip()}</p>" for p in text.split("\n\n") if p.strip())
        result = await page.evaluate(FILL_JS, html)
        if result != "ok":
            raise RuntimeError(f"TinyMCE nicht bereit: {result}")
        if AUTO_SAVE:
            await page.click("span.btn.pitsafe:has-text('Speichern')")
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            await page.wait_for_timeout(800)


# --- Verarbeitung eines Maklers ---------------------------------------------

async def process(page, st: State, task: dict) -> None:
    mid = task["maklerid"]
    try:
        info = await read_info(page, st, mid)
        if SKIP_FILLED and info["current"]:
            st.skipped += 1
            await st.log(mid, info["name"], task["region_code"], 0, "skipped_filled")
            return
        path = build_profile_path(info["profil_uri"], task["slug"])
        impressum = await fetch_impressum(page, path)
        text = await asyncio.to_thread(
            generate_makler_text, st.cfg.openai_key, impressum,
            task["region_name"], info["name"])
        await fill_and_save(page, st, mid, text)
        st.done += 1
        words = len(text.split())
        await st.log(mid, info["name"], task["region_code"], words,
                     "ok" if impressum else "ok_no_impressum")
        print(f"  [ok {st.done}] {info['name']} ({task['region_code']}) — {words} W."
              f"{'' if impressum else ' (kein Impressum)'}")
    except Exception as e:
        st.errors += 1
        await st.log(mid, "", task["region_code"], 0, f"error:{type(e).__name__}")
        print(f"  [ERR] {mid} ({task['region_code']}): {type(e).__name__}: {str(e)[:100]}")


# --- Orchestrierung ---------------------------------------------------------

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
        print(f"Login ok (Session {st.sess}), {WORKERS} Worker-Seiten.")

        # Region-Slugs (autoritativ) über Seite 0 laden.
        await open_backend(pages[0], st, "/adm/individuell/regionen/config/?")
        rows = await pages[0].eval_on_selector_all(
            "tr", "els => els.map(r => r.innerText.replace(/\\s+/g,' ').trim())")
        slugs = {}
        for row in rows:
            m = re.match(r"^([a-z]+24)\s+/([a-z0-9äöü.\-]+)/\s", row)
            if m:
                slugs[m.group(1)] = m.group(2)
        codes = ONLY_REGIONS or list(slugs.keys())
        print(f"{len(slugs)} Regionen; verarbeite {len(codes)}.")

        # Phase 1: Worklist parallel aufbauen (Regionen auf Seiten verteilen).
        region_q: asyncio.Queue = asyncio.Queue()
        for c in codes:
            region_q.put_nowait(c)
        worklist: list[dict] = []

        async def lister(page):
            while not region_q.empty():
                try:
                    code = region_q.get_nowait()
                except asyncio.QueueEmpty:
                    return
                try:
                    for mid in await list_region(page, st, code):
                        worklist.append({
                            "maklerid": mid, "region_code": code,
                            "slug": slugs.get(code, ""),
                            "region_name": cfg.region_mapping.get(code, code),
                        })
                except Exception as e:
                    print(f"  [ERR list {code}] {type(e).__name__}: {str(e)[:80]}")

        await asyncio.gather(*(lister(pg) for pg in pages))
        print(f"Worklist: {len(worklist)} Makler.")

        # Phase 2: Makler parallel verarbeiten.
        task_q: asyncio.Queue = asyncio.Queue()
        for t in worklist:
            task_q.put_nowait(t)

        async def worker(page):
            while True:
                if LIMIT is not None and st.done >= LIMIT:
                    return
                try:
                    task = task_q.get_nowait()
                except asyncio.QueueEmpty:
                    return
                await process(page, st, task)

        await asyncio.gather(*(worker(pg) for pg in pages))
        await browser.close()

    print(f"\nFertig. befüllt={st.done} übersprungen={st.skipped} fehler={st.errors}. "
          f"Log: {LOG_PATH.name}")


if __name__ == "__main__":
    asyncio.run(main())
