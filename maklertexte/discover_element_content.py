"""Liest den CKEditor-Inhalt von Element 56gbzo (Partnerseiten-Inhalt) aus.

Aufruf:
    REGIO=aai24 .venv/bin/python discover_element_content.py
    REGIO=aai24 ELEMENT_ID=56gbzo .venv/bin/python discover_element_content.py
"""

from __future__ import annotations

import asyncio
import os

from playwright.async_api import async_playwright

from config import load_config
from generate_texts import BASE_URL
from rollout_parallel import do_login, open_backend

REGIO      = os.environ.get("REGIO", "aai24")
PAGE_ID    = os.environ.get("PAGE_ID", "mbgttnf8")
SECTION_ID = os.environ.get("SECTION_ID", "zh8pew2p")
ELEMENT_ID = os.environ.get("ELEMENT_ID", "56gbzo")


class _St:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sess = ""
        self.login_lock = asyncio.Lock()


async def main() -> None:
    cfg = load_config()
    st = _St(cfg)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        st.sess = await do_login(page, cfg)
        print(f"Login ok (sess={st.sess[:8]}…)")

        path = (
            f"/adm/individuell/regionen/edit_region_element.php"
            f"?regio={REGIO}&page_id={PAGE_ID}"
            f"&section_id={SECTION_ID}&element_id={ELEMENT_ID}&"
        )
        await open_backend(page, st, path)
        await page.wait_for_timeout(2000)
        print(f"URL: {page.url}\n")

        # ── Alle Formularfelder (auch versteckte) ─────────────────────────────
        fields = await page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('input, textarea, select').forEach(el => {
                results.push({
                    tag: el.tagName.toLowerCase(),
                    type: el.type || '',
                    id: el.id || '',
                    name: el.name || '',
                    value: (el.value || '').slice(0, 200),
                    class: el.className.slice(0, 80),
                    disabled: el.disabled,
                });
            });
            return results;
        }""")
        print("=== Alle Formularfelder ===")
        for f in fields:
            dis = " [disabled]" if f['disabled'] else ""
            print(f"  {f['tag']:10} id={f['id']!r:35} name={f['name']!r:35} "
                  f"val={f['value']!r:.60}{dis}")

        # ── CKEditor-Instanzen ────────────────────────────────────────────────
        editors = await page.evaluate("""() => {
            if (!window.CKEDITOR) return 'no-CKEDITOR';
            return Object.keys(CKEDITOR.instances).map(id => ({
                id: id,
                status: CKEDITOR.instances[id].status,
                content_len: CKEDITOR.instances[id].getData().length,
                content: CKEDITOR.instances[id].getData(),
            }));
        }""")
        print("\n=== CKEditor-Instanzen ===")
        if editors == 'no-CKEDITOR':
            print("  CKEDITOR nicht gefunden auf dieser Seite.")
        elif not editors:
            print("  (keine CKEditor-Instanzen)")
        else:
            for e in editors:
                print(f"\n  id={e['id']!r}  status={e['status']!r}  len={e['content_len']}")
                print(f"  --- Inhalt ---")
                print(e['content'] or "(leer)")

        # ── Alle Textarea-Inhalte (direkter DOM-Zugriff als Fallback) ─────────
        textareas = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('textarea')).map(ta => ({
                id: ta.id,
                name: ta.name,
                value_len: ta.value.length,
                value: ta.value.slice(0, 500),
                class: ta.className.slice(0, 60),
            }));
        }""")
        print("\n=== Textareas (DOM) ===")
        for ta in textareas:
            print(f"  id={ta['id']!r}  name={ta['name']!r}  "
                  f"len={ta['value_len']}  val={ta['value']!r:.80}")

        # ── Sektion-Seite: prüfe ob Element gesperrt oder frei ───────────────
        print("\n=== Elementstatus in Sektion (gesperrt vs. editierbar) ===")
        await open_backend(
            page, st,
            f"/adm/individuell/regionen/edit_region_section.php"
            f"?regio={REGIO}&page_id={PAGE_ID}&section_id={SECTION_ID}&"
        )
        await page.wait_for_timeout(1000)

        all_links = await page.eval_on_selector_all(
            "a[href*='edit_region_element'], a[href*='old_element_id']",
            "els => els.map(a => ({ href: a.href, title: a.title || '', "
            "label: (a.closest('tr') || a).innerText.replace(/\\s+/g,' ').trim().slice(0,120) }))"
        )
        # Kategorisiere: hat element_id= → editierbar; nur old_element_id= → gesperrt
        import re
        editable, locked = [], []
        seen = set()
        for lnk in all_links:
            if 'element_id' in lnk['href'] and 'old_element_id' not in lnk['href']:
                m = re.search(r'element_id=([a-z0-9]+)', lnk['href'])
                eid = m.group(1) if m else '?'
                if eid not in seen:
                    seen.add(eid)
                    editable.append((eid, lnk['label']))
            elif 'old_element_id' in lnk['href']:
                m = re.search(r'old_element_id=([a-z0-9]+)', lnk['href'])
                nm = re.search(r'new_element_id=([a-z0-9]+)', lnk['href'])
                eid = m.group(1) if m else '?'
                nid = nm.group(1) if nm else '?'
                if eid not in seen:
                    seen.add(eid)
                    locked.append((eid, nid, lnk['label']))

        print("  EDITIERBAR (bereits individualisiert):")
        for eid, label in editable:
            marker = " ← ZIEL" if eid == ELEMENT_ID else ""
            print(f"    element_id={eid!r:15}  {label[:80]}{marker}")
        print("  GESPERRT (noch Vatermodell — braucht Entsperren):")
        for eid, nid, label in locked:
            print(f"    old={eid!r}  new={nid!r}  {label[:70]}")

        await browser.close()
        print("\nDiscovery abgeschlossen.")


if __name__ == "__main__":
    asyncio.run(main())
