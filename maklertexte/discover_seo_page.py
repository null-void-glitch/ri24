"""Gibt die vollständige Formularstruktur der Makler-Landingpage für eine Region aus.

Navigationspfad:
  edit_region_sites     → Seitenübersicht (findet "immobilienportal-partner-werden")
  edit_region_page      → Sektionen der Seite
  edit_region_section   → Elemente jeder Sektion
  edit_region_element   → Formularfelder (nach "Entsperren")

Aufruf:
    .venv/bin/python discover_seo_page.py
    REGIO=aai24 .venv/bin/python discover_seo_page.py
    PAGE_DIR=immobilienportal-partner-werden .venv/bin/python discover_seo_page.py
"""

from __future__ import annotations

import asyncio
import os
import re

from playwright.async_api import async_playwright

from config import load_config
from generate_texts import BASE_URL
from rollout_parallel import do_login, open_backend


PAGE_DIR = os.environ.get("PAGE_DIR", "immobilienportal-partner-werden")


class _St:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sess = ""
        self.login_lock = asyncio.Lock()


def sep(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


async def main() -> None:
    cfg = load_config()
    st = _St(cfg)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # sichtbar für Debugging
        page = await browser.new_page()

        st.sess = await do_login(page, cfg)
        print(f"Login ok (sess={st.sess[:8]}…)")

        # ── Schritt 1: Regionen-Liste, Vatermodell überspringen ───────────────
        sep("Schritt 1: Regionen-Liste")
        await open_backend(page, st, "/adm/individuell/regionen/config/?")
        await page.wait_for_timeout(800)

        # Alle "anpassen"-Links sammeln (edit_region_sites.php?regio=CODE)
        site_links = await page.eval_on_selector_all(
            "a[href*='edit_region_sites.php']",
            "els => els.map(a => ({ href: a.href, text: a.closest('tr') "
            "? a.closest('tr').innerText.replace(/\\s+/g,' ').trim().slice(0,80) : '' }))"
        )
        print(f"Regionen mit 'Seiten anpassen'-Link: {len(site_links)}")
        if len(site_links) < 2:
            print("Nicht genug Regionen — Abbruch.")
            await browser.close()
            return

        # Ersten überspringen (Vatermodell), zweiten nehmen (oder REGIO-Env)
        regio_env = os.environ.get("REGIO", "")
        target_link = None
        for lnk in site_links:
            m = re.search(r"regio=([a-z0-9]+)", lnk["href"])
            if not m:
                continue
            code = m.group(1)
            if regio_env:
                if code == regio_env:
                    target_link = lnk
                    break
            else:
                # Ersten überspringen (index 0 = Vatermodell)
                if lnk is not site_links[0]:
                    target_link = lnk
                    break

        if not target_link:
            print("Kein passender Regions-Link gefunden.")
            await browser.close()
            return

        regio_code = re.search(r"regio=([a-z0-9]+)", target_link["href"]).group(1)
        print(f"Gewählte Region: {regio_code}")
        print(f"Zeile: {target_link['text']}")

        # ── Schritt 2: Seiten der Region — findet PAGE_DIR ────────────────────
        sep(f"Schritt 2: edit_region_sites (regio={regio_code})")
        await open_backend(
            page, st,
            f"/adm/individuell/regionen/edit_region_sites.php?regio={regio_code}&")
        await page.wait_for_timeout(1000)
        print(f"URL: {page.url}")

        # Alle Seiten-Zeilen einlesen
        page_rows = await page.evaluate(f"""() => {{
            const rows = [];
            document.querySelectorAll('tr.form_inline').forEach(tr => {{
                const dirInput = tr.querySelector('input[name="dir"]');
                const nameInput = tr.querySelector('input[name="page_name"]');
                const editLink = tr.querySelector('a[href*="edit_region_page"]');
                if (dirInput) {{
                    rows.push({{
                        dir: dirInput.value,
                        page_name: nameInput ? nameInput.value : '',
                        edit_href: editLink ? editLink.href : '',
                    }});
                }}
            }});
            return rows;
        }}""")

        print(f"Seiten gefunden: {len(page_rows)}")
        for r in page_rows:
            marker = " ← ZIEL" if PAGE_DIR in r["dir"] else ""
            print(f"  dir={r['dir']!r:50}  name={r['page_name']!r}{marker}")

        target_page = next((r for r in page_rows if PAGE_DIR in r["dir"]), None)
        if not target_page:
            print(f"\nSeite mit dir='{PAGE_DIR}' nicht gefunden.")
            await browser.close()
            return

        page_id_m = re.search(r"page_id=([a-z0-9]+)", target_page["edit_href"])
        page_id = page_id_m.group(1) if page_id_m else ""
        print(f"\nZielseite: page_id={page_id!r}  dir={target_page['dir']!r}")

        # ── Schritt 3: Sektionen der Seite ────────────────────────────────────
        sep(f"Schritt 3: edit_region_page (page_id={page_id})")
        await open_backend(
            page, st,
            f"/adm/individuell/regionen/edit_region_page.php"
            f"?regio={regio_code}&page_id={page_id}&")
        await page.wait_for_timeout(1000)
        print(f"URL: {page.url}")

        section_rows = await page.evaluate("""() => {
            const rows = [];
            document.querySelectorAll('tr.form_inline').forEach(tr => {
                const bezInput = tr.querySelector('input[name="section_bez"]');
                const idInput = tr.querySelector('input[name="section_id"]');
                const editLink = tr.querySelector('a[href*="edit_region_section"]');
                if (bezInput) {
                    rows.push({
                        section_id: idInput ? idInput.value : '',
                        section_bez: bezInput.value,
                        edit_href: editLink ? editLink.href : '',
                    });
                }
            });
            return rows;
        }""")

        print(f"Sektionen gefunden: {len(section_rows)}")
        for s in section_rows:
            print(f"  section_id={s['section_id']!r:15}  bez={s['section_bez']!r}")

        # ── Schritt 4: Alle Sektionen → Elemente ──────────────────────────────
        for sec in section_rows:
            sep(f"Schritt 4: Sektion '{sec['section_bez']}' (id={sec['section_id']})")

            path = (
                f"/adm/individuell/regionen/edit_region_section.php"
                f"?regio={regio_code}&page_id={page_id}&section_id={sec['section_id']}&"
            )
            await open_backend(page, st, path)
            await page.wait_for_timeout(1000)
            print(f"URL: {page.url}")

            # Alle Element-Edit-Links sammeln
            element_links = await page.eval_on_selector_all(
                "a[href*='edit_region_element']",
                "els => els.map(a => ({ href: a.href, "
                "label: a.closest('tr') ? "
                "a.closest('tr').innerText.replace(/\\s+/g,' ').trim().slice(0,100) "
                ": a.title || '' }))"
            )
            print(f"Elemente: {len(element_links)}")
            for el in element_links:
                print(f"  href={el['href'][-80:]!r}")
                print(f"  label={el['label']!r}")

            # Erstes Element öffnen und Formular zeigen
            if element_links:
                el0 = element_links[0]
                el_m = re.search(r"element_id=([a-z0-9]+)", el0["href"])
                element_id = el_m.group(1) if el_m else ""
                sep(f"  Element {element_id} — Formular")

                el_path = (
                    f"/adm/individuell/regionen/edit_region_element.php"
                    f"?regio={regio_code}&page_id={page_id}"
                    f"&section_id={sec['section_id']}&element_id={element_id}&"
                )
                await open_backend(page, st, el_path)
                await page.wait_for_timeout(1500)
                print(f"URL: {page.url}")

                # Entsperren-Button suchen
                unlock_btn = await page.query_selector(
                    "button:has-text('entsperren'), "
                    "a:has-text('entsperren'), "
                    "input[value*='entsperren'], "
                    "button:has-text('Entsperren'), "
                    "a:has-text('Entsperren'), "
                    "[class*='unlock'], [class*='loesen'], [class*='loslösen']"
                )
                print(f"Entsperren-Element gefunden: {unlock_btn is not None}")
                if unlock_btn:
                    tag = await unlock_btn.evaluate("el => el.tagName")
                    txt = await unlock_btn.evaluate("el => el.innerText || el.value || ''")
                    cls = await unlock_btn.evaluate("el => el.className")
                    print(f"  Tag={tag}  text={txt!r}  class={cls!r}")

                # Seiteninhalt vor Entsperren ausgeben
                body_before = await page.evaluate(
                    "() => document.body.innerText.replace(/\\s{3,}/g,'\\n').slice(0,2000)")
                print("\n--- Seiteninhalt VOR Entsperren ---")
                print(body_before)

                # Alle klickbaren Elemente mit Text ausgeben (für Entsperren-Suche)
                clickables = await page.evaluate("""() => {
                    const els = [];
                    document.querySelectorAll('button, a, input[type=submit], input[type=button]').forEach(el => {
                        const txt = (el.innerText || el.value || el.title || '').trim().slice(0, 80);
                        if (txt) els.push({
                            tag: el.tagName,
                            text: txt,
                            class: el.className.slice(0,60),
                            href: el.href || '',
                        });
                    });
                    return els;
                }""")
                print("\n--- Klickbare Elemente ---")
                for c in clickables:
                    print(f"  {c['tag']:8} text={c['text']!r:50} class={c['class']!r}")

                if unlock_btn:
                    print("\n--- Klicke Entsperren ---")
                    await unlock_btn.click()
                    await page.wait_for_timeout(2000)

                    body_after = await page.evaluate(
                        "() => document.body.innerText.replace(/\\s{3,}/g,'\\n').slice(0,2000)")
                    print("\n--- Seiteninhalt NACH Entsperren ---")
                    print(body_after)

                    # Formularfelder nach Entsperren
                    fields = await page.evaluate("""() => {
                        const results = [];
                        document.querySelectorAll('input, textarea, select').forEach(el => {
                            results.push({
                                tag: el.tagName.toLowerCase(),
                                type: el.type || '',
                                id: el.id || '',
                                name: el.name || '',
                                value_preview: (el.value || '').slice(0, 100),
                                class: el.className.slice(0, 60),
                            });
                        });
                        return results;
                    }""")
                    print("\n--- Formularfelder nach Entsperren ---")
                    for f in fields:
                        print(f"  {f['tag']:10} id={f['id']!r:35} name={f['name']!r:35} "
                              f"val={f['value_preview']!r}")

                    editors = await page.evaluate("""() => {
                        if (!window.tinyMCE) return [];
                        return tinyMCE.editors.map(e => ({
                            id: e.id,
                            content_len: e.getContent().length,
                            content_preview: e.getContent().replace(/<[^>]+>/g,'').slice(0, 200),
                        }));
                    }""")
                    print("\n--- TinyMCE nach Entsperren ---")
                    if editors:
                        for e in editors:
                            print(f"  id={e['id']!r}  len={e['content_len']}  "
                                  f"preview={e['content_preview']!r}")
                    else:
                        print("  (keine TinyMCE-Editoren)")

        print("\n\nDiscovery abgeschlossen.")
        input("Enter drücken um Browser zu schließen…")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
