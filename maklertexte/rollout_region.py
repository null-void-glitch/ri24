"""Regionaler Makler-Text-Lauf mit Duplikat-Erkennung und -Bereinigung.

Ablauf für eine Region:
  Phase 1 — Einlesen  : Alle Makler-Texte der Region parallel lesen.
  Phase 2 — Analyse   : Leere Felder und Duplikate erkennen
                        (erste 5 Wörter identisch → Duplikat).
  Phase 3 — Bereinigen: Duplikat-Texte löschen (einen nach dem anderen).
  Phase 4 — Befüllen  : Alle leeren Felder befüllen
                        (Text-Generierung parallel, Speichern serialisiert).

Aufruf:
    ROLLOUT_REGION=ami24 .venv/bin/python rollout_region.py
    ROLLOUT_REGION=ami24 WORKERS=3 .venv/bin/python rollout_region.py
    ROLLOUT_REGION=ami24 AUTO_SAVE=0 .venv/bin/python rollout_region.py  # Probelauf
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
from rollout_parallel import (
    FILL_JS, do_login, fetch_impressum, list_region, open_backend,
)
from text_generator import generate_makler_text

WORKERS = int(os.environ.get("WORKERS", "4"))
AUTO_SAVE = os.environ.get("AUTO_SAVE", "1") != "0"
REGION = os.environ.get("ROLLOUT_REGION", "")
LOG_PATH = Path(os.environ.get("ROLLOUT_LOG", "rollout_region_log.csv"))

# Anzahl der Anfangswörter, die als Duplikat-Fingerprint dienen.
DUP_WORDS = int(os.environ.get("DUP_WORDS", "5"))

CLEAR_JS = """() => {
    const ed = window.tinyMCE && tinyMCE.get('maklerprofil_dyn_profil_text_tiny');
    if (!ed) return 'no-editor';
    ed.setContent('');
    document.getElementById('maklerprofil_dyn_profil_text').value = '';
    return 'ok';
}"""

READ_TEXT_JS = """() => {
    const ed = window.tinyMCE && tinyMCE.get('maklerprofil_dyn_profil_text_tiny');
    if (ed) {
        const html = ed.getContent();
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        return tmp.innerText.trim();
    }
    return document.getElementById('maklerprofil_dyn_profil_text')?.value?.trim() || '';
}"""


# --- Zustand ----------------------------------------------------------------

class State:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sess = ""
        self.log_lock = asyncio.Lock()
        self.login_lock = asyncio.Lock()
        # Serialisiert ALLE Zugriffe auf Backend-Editierseiten (Lesen UND
        # Schreiben). Verhindert, dass parallele Workers gleichzeitig
        # verschiedene Makler-Editierseiten öffnen und dadurch den
        # serverseitigen Session-Zustand des Backends durcheinander bringen
        # (sowohl beim Lesen der profil_uri als auch beim Speichern).
        self.backend_lock = asyncio.Lock()

    async def log(self, maklerid: str, name: str, region: str, words: int, status: str):
        async with self.log_lock:
            new = not LOG_PATH.exists()
            with LOG_PATH.open("a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if new:
                    w.writerow(["maklerid", "name", "region", "words", "status"])
                w.writerow([maklerid, name, region, words, status])


# --- Backend-Operationen ----------------------------------------------------

async def read_info(page, st: State, maklerid: str) -> dict:
    """Liest Name, Profil-URI und Plaintext-Inhalt eines Maklers (serialisiert)."""
    async with st.backend_lock:
        await open_backend(page, st, f"/adm/individuell/master/makler/edit/?maklerid={maklerid}&")
        await page.wait_for_timeout(700)
        if f"maklerid={maklerid}" not in page.url:
            raise RuntimeError(
                f"Backend lud falsche Seite (erwartet maklerid={maklerid}, URL={page.url[:120]})")
        text = await page.evaluate(READ_TEXT_JS)
        return {
            "name": await page.input_value("#name"),
            "profil_uri": (await page.input_value("#profil_uri_name")).strip(),
            "text": text,
        }


async def clear_and_save(page, st: State, maklerid: str) -> None:
    """Löscht den TinyMCE-Inhalt eines Maklers und speichert (serialisiert)."""
    async with st.backend_lock:
        await open_backend(page, st, f"/adm/individuell/master/makler/edit/?maklerid={maklerid}&")
        await page.wait_for_timeout(700)
        if f"maklerid={maklerid}" not in page.url:
            raise RuntimeError(
                f"Backend lud falsche Seite beim Löschen (maklerid={maklerid}, URL={page.url[:120]})")
        result = await page.evaluate(CLEAR_JS)
        if result != "ok":
            raise RuntimeError(f"TinyMCE nicht bereit beim Löschen: {result}")
        if AUTO_SAVE:
            await page.click("span.btn.pitsafe:has-text('Speichern')")
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                await page.wait_for_timeout(3000)
            await page.wait_for_timeout(500)


async def fill_and_save(page, st: State, maklerid: str, text: str) -> None:
    """Befüllt TinyMCE mit dem generierten Text und speichert (serialisiert)."""
    async with st.backend_lock:
        await open_backend(page, st, f"/adm/individuell/master/makler/edit/?maklerid={maklerid}&")
        await page.wait_for_timeout(700)
        if f"maklerid={maklerid}" not in page.url:
            raise RuntimeError(
                f"Backend lud falsche Seite beim Befüllen (maklerid={maklerid}, URL={page.url[:120]})")
        html = "".join(f"<p>{p.strip()}</p>" for p in text.split("\n\n") if p.strip())
        result = await page.evaluate(FILL_JS, html)
        if result != "ok":
            raise RuntimeError(f"TinyMCE nicht bereit: {result}")
        if AUTO_SAVE:
            await page.click("span.btn.pitsafe:has-text('Speichern')")
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                await page.wait_for_timeout(3000)
            await page.wait_for_timeout(500)


# --- Hilfsfunktionen --------------------------------------------------------

# Generische Begriffe, die bei der Name-Erkennung ignoriert werden.
_GENERIC = frozenset({
    "gmbh", "immobilien", "invest", "estate", "wohnen", "makler", "gruppe",
    "service", "beratung", "management", "vermietung", "verwaltung", "haus",
    "consulting", "partner", "handel", "realty", "homes", "house", "wohn",
    "immobilien", "immo", "projekt", "gesellschaft", "mbh", "ohg", "kgaa",
    # Kurzformen / Rechtsformen die als Abkürzungen erkannt würden
    "ag", "ev", "eg", "se", "kg", "ek",
})


def prefix(text: str, n: int = DUP_WORDS) -> str:
    """Gibt die ersten n Wörter in Kleinschreibung zurück (Duplikat-Fingerprint)."""
    words = text.split()
    return " ".join(words[:n]).lower() if len(words) >= n else ""


def name_keywords(name: str, min_len: int = 6, fallback_len: int = 0) -> list[str]:
    """Extrahiert unterscheidende Wörter aus einem Makler-Namen.

    Stufen (nur für Eigenname-/Post-Gen-Checks mit fallback_len gesetzt):
      1. Wörter ≥ min_len Zeichen, nicht in _GENERIC
      2. Wörter ≥ fallback_len Zeichen, nicht in _GENERIC
      3. Abkürzungen (komplett Großbuchstaben, ≥ 2 Zeichen, nicht in _GENERIC)
    Stufen 2+3 nur bei fallback_len > 0 — nie für Fremdname-Checks verwenden,
    da kurze/generische Tokens dort zu Falsch-Positiven führen würden.
    """
    words = [w for w in re.split(r"\W+", name) if w]
    kws = [w.lower() for w in words if len(w) >= min_len and w.lower() not in _GENERIC]
    if not kws and fallback_len:
        kws = [w.lower() for w in words if len(w) >= fallback_len and w.lower() not in _GENERIC]
        if not kws:
            # Abkürzungen wie "IW", "KH", "RE" als letzter Fallback
            kws = [w.lower() for w in words if len(w) >= 2 and w.isupper() and w.lower() not in _GENERIC]
    return kws


def kw_in_text(kw: str, text: str) -> bool:
    """Prüft ob kw als ganzes Wort im Text vorkommt (Wortgrenzen)."""
    return bool(re.search(r"\b" + re.escape(kw) + r"\b", text))


# --- Orchestrierung ---------------------------------------------------------

async def main() -> None:
    if not REGION:
        raise SystemExit(
            "Bitte ROLLOUT_REGION setzen, z. B.:\n"
            "  ROLLOUT_REGION=ami24 .venv/bin/python rollout_region.py")

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

        # Region-Slug und -Name über die Regionen-Config ermitteln.
        await open_backend(pages[0], st, "/adm/individuell/regionen/config/?")
        rows = await pages[0].eval_on_selector_all(
            "tr", "els => els.map(r => r.innerText.replace(/\\s+/g,' ').trim())")
        slugs: dict[str, str] = {}
        for row in rows:
            m = re.match(r"^([a-z]+24)\s+/([a-z0-9äöü.\-]+)/\s", row)
            if m:
                slugs[m.group(1)] = m.group(2)

        if REGION not in slugs:
            await browser.close()
            raise SystemExit(
                f"Region {REGION!r} nicht in der Regionen-Config.\n"
                f"Verfügbar: {sorted(slugs)}")

        slug = slugs[REGION]
        region_name = cfg.region_mapping.get(REGION, REGION)
        print(f"Region: {REGION} ({region_name}), Slug: /{slug}/")
        if not AUTO_SAVE:
            print("AUTO_SAVE=0 — Speichern deaktiviert (Probelauf).")

        # ── Phase 1: Alle Makler-Texte parallel einlesen ──────────────────────
        print(f"\n{'='*60}")
        print("Phase 1: Texte einlesen")
        print('='*60)

        ids = await list_region(pages[0], st, REGION)
        if not ids:
            print("Keine Makler gefunden — Abbruch.")
            await browser.close()
            return
        print(f"{len(ids)} Makler gefunden.\n")

        read_q: asyncio.Queue = asyncio.Queue()
        for mid in ids:
            read_q.put_nowait(mid)

        infos: dict[str, dict | None] = {}
        info_lock = asyncio.Lock()

        async def reader(pg):
            while True:
                try:
                    mid = read_q.get_nowait()
                except asyncio.QueueEmpty:
                    return
                try:
                    info = await read_info(pg, st, mid)
                    async with info_lock:
                        infos[mid] = info
                    wc = len(info["text"].split()) if info["text"] else 0
                    label = "leer" if not info["text"] else f"{wc} W."
                    print(f"  [lesen] {info['name']}: {label}"
                          f"  (profil_uri: {info['profil_uri']!r})")
                except Exception as e:
                    async with info_lock:
                        infos[mid] = None
                    print(f"  [ERR lesen] {mid}: {type(e).__name__}: {str(e)[:80]}")

        await asyncio.gather(*(reader(pg) for pg in pages))

        # ── Phase 2: Duplikate und Leerstellen erkennen ───────────────────────
        print(f"\n{'='*60}")
        print("Phase 2: Analyse")
        print('='*60)

        by_prefix: dict[str, list[str]] = {}
        for mid, info in infos.items():
            if not info or not info["text"]:
                continue
            fp = prefix(info["text"])
            if fp:  # nur wenn mindestens DUP_WORDS Wörter vorhanden
                by_prefix.setdefault(fp, []).append(mid)

        dup_groups = {fp: mids for fp, mids in by_prefix.items() if len(mids) > 1}
        to_clear: set[str] = {mid for mids in dup_groups.values() for mid in mids}
        to_fill: set[str] = {mid for mid, info in infos.items() if info and not info["text"]}

        # Fremdname-Erkennung: Text eines Maklers enthält den Namen eines
        # ANDEREN Maklers aus der Region → Text ist falsch zugeordnet.
        # Erkennt Fälle, bei denen die KI leicht unterschiedliche Texte über
        # denselben Fremd-Makler generiert hat (sodass der 5-Wort-Fingerprint
        # nicht greift).
        broker_kws: dict[str, list[str]] = {
            mid: name_keywords(info["name"])
            for mid, info in infos.items()
            if info and info["name"]
        }
        wrong_name: set[str] = set()
        for mid, info in infos.items():
            if not info or not info["text"] or mid in to_clear:
                continue
            text_lower = info["text"].lower()
            for other_mid, kws in broker_kws.items():
                if other_mid == mid or not kws:
                    continue
                matched = [kw for kw in kws if kw_in_text(kw, text_lower)]
                if matched:
                    other_name = (infos[other_mid] or {}).get("name", other_mid)
                    print(f"  [Fremdname] {info['name']!r} → "
                          f"Text nennt '{other_name}' ({matched[0]!r})")
                    wrong_name.add(mid)
                    break
        to_clear |= wrong_name

        # Eigenname-Prüfung: Das eigene Namens-Keyword muss im eigenen Text
        # vorkommen. Fehlt es, wurde der Text für einen ANDEREN Makler erzeugt
        # (auch wenn dieser in einer anderen Region liegt und daher im
        # Fremdname-Check nicht auftaucht, z.B. Asgard-Text in Havelland).
        missing_own: set[str] = set()
        for mid, info in infos.items():
            if not info or not info["text"] or mid in to_clear:
                continue
            own_kws = name_keywords(info["name"], fallback_len=4)
            text_lower = info["text"].lower()
            if own_kws and not any(kw_in_text(kw, text_lower) for kw in own_kws):
                print(f"  [Eigenname fehlt] {info['name']!r} — "
                      f"Keywords {own_kws!r} nicht im Text")
                missing_own.add(mid)
        to_clear |= missing_own

        read_ok = sum(1 for i in infos.values() if i is not None)
        read_err = len(ids) - read_ok

        print(f"Erfolgreich gelesen:   {read_ok}/{len(ids)}"
              + (f"  ({read_err} Fehler)" if read_err else ""))
        print(f"Leere Felder:          {len(to_fill)}")
        print(f"Duplikat-Gruppen:      {len(dup_groups)}")
        print(f"Fremdname-Treffer:     {len(wrong_name)}")
        print(f"Eigenname fehlt:       {len(missing_own)}")
        print(f"Zu löschende Texte:    {len(to_clear)}")

        if dup_groups:
            print()
            for fp, mids in dup_groups.items():
                print(f"  Duplikat [{fp!r}]:")
                for m in mids:
                    print(f"    → {infos[m]['name'] if infos.get(m) else m}")

        # ── Phase 3: Duplikate löschen ────────────────────────────────────────
        cleared = 0
        clear_errors = 0

        if to_clear:
            print(f"\n{'='*60}")
            print(f"Phase 3: {len(to_clear)} Duplikat-Texte löschen")
            print('='*60)

            for mid in sorted(to_clear):
                info = infos.get(mid) or {}
                name = info.get("name", mid)
                try:
                    await clear_and_save(pages[0], st, mid)
                    to_fill.add(mid)
                    cleared += 1
                    print(f"  [gelöscht] {name}")
                    await st.log(mid, name, REGION, 0, "cleared_duplicate")
                except Exception as e:
                    clear_errors += 1
                    print(f"  [ERR löschen] {name}: {type(e).__name__}: {str(e)[:80]}")
                    await st.log(mid, name, REGION, 0, f"error_clear:{type(e).__name__}")

        # ── Phase 4: Leere Felder befüllen ────────────────────────────────────
        filled = 0
        fill_errors = 0

        if to_fill:
            print(f"\n{'='*60}")
            print(f"Phase 4: {len(to_fill)} Felder befüllen")
            print('='*60)

            fill_q: asyncio.Queue = asyncio.Queue()
            for mid in to_fill:
                info = infos.get(mid)
                if info is None:
                    continue  # Lesen hatte Fehler — überspringen
                fill_q.put_nowait({
                    "maklerid": mid,
                    "name": info["name"],
                    "profil_uri": info["profil_uri"],
                    "region_name": region_name,
                    "slug": slug,
                })

            async def filler(pg):
                nonlocal filled, fill_errors
                while True:
                    try:
                        task = fill_q.get_nowait()
                    except asyncio.QueueEmpty:
                        return
                    mid = task["maklerid"]
                    name = task["name"]
                    try:
                        path = build_profile_path(task["profil_uri"], task["slug"])
                        try:
                            impressum = await fetch_impressum(pg, path)
                        except Exception as imp_err:
                            print(f"  [Warnung] Impressum-Abruf für '{name}' fehlgeschlagen "
                                  f"({type(imp_err).__name__}) — fahre ohne Impressum fort")
                            impressum = ""

                        # Impressum-Validierung: Prüfe ob mindestens ein
                        # signifikantes Wort des Makler-Namens im Impressum
                        # vorkommt. Falls nicht, ist das Impressum vermutlich
                        # von einem anderen Makler (falsche profil_uri).
                        if impressum and name:
                            name_words = [
                                w for w in name.lower().split() if len(w) > 3
                                and w not in {"gmbh", "immobilien", "haus"}
                            ]
                            if name_words and not any(
                                w in impressum.lower() for w in name_words
                            ):
                                print(f"  [Warnung] Impressum für '{name}' "
                                      f"enthält keinen Namensteil — wird "
                                      f"ignoriert (profil_uri={task['profil_uri']!r})")
                                impressum = ""

                        text = await asyncio.to_thread(
                            generate_makler_text, st.cfg.openai_key, impressum,
                            task["region_name"], name)

                        # Post-Generierungs-Prüfung: mind. ein eigenes
                        # Namens-Keyword muss im generierten Text vorkommen.
                        # Fehlt es → einmaliger Retry ohne Impressum (nur mit
                        # Name), damit die KI nicht erneut das falsche Impressum
                        # verwendet.
                        own_kws = name_keywords(name, fallback_len=4)
                        tl = text.lower()
                        if own_kws and not any(kw_in_text(kw, tl) for kw in own_kws):
                            print(f"  [Retry] '{name}' — kein Namensteil im Text"
                                  f" {own_kws} — nochmal (ohne Impressum)")
                            text = await asyncio.to_thread(
                                generate_makler_text, st.cfg.openai_key, "",
                                task["region_name"], name)
                            tl = text.lower()
                            if own_kws and not any(kw_in_text(kw, tl) for kw in own_kws):
                                print(f"  [Warnung] '{name}' — nach Retry "
                                      f"noch kein Namensteil im Text")

                        await fill_and_save(pg, st, mid, text)
                        words = len(text.split())
                        filled += 1
                        status = "filled" if impressum else "filled_no_impressum"
                        note = "" if impressum else " (kein Impressum)"
                        print(f"  [befüllt {filled}] {name} — {words} W.{note}")
                        await st.log(mid, name, REGION, words, status)
                    except Exception as e:
                        fill_errors += 1
                        print(f"  [ERR befüllen] {name}: {type(e).__name__}: {str(e)[:100]}")
                        await st.log(mid, name, REGION, 0, f"error_fill:{type(e).__name__}")

            await asyncio.gather(*(filler(pg) for pg in pages))

        await browser.close()

    # ── Zusammenfassung ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Zusammenfassung  Region {REGION} ({region_name})")
    print('='*60)
    print(f"  Gelesen:        {read_ok}/{len(ids)}"
          + (f"  ({read_err} Lesefehler)" if read_err else ""))
    print(f"  Gelöscht:       {cleared}"
          + (f"  ({clear_errors} Fehler)" if clear_errors else ""))
    print(f"  Befüllt:        {filled}"
          + (f"  ({fill_errors} Fehler)" if fill_errors else ""))
    print(f"  Log:            {LOG_PATH.name}")


if __name__ == "__main__":
    asyncio.run(main())
