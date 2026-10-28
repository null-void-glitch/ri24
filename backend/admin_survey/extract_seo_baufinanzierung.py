"""Offline extraction of the real 'Daten der Seite: /aachen-eifel/baufinanzierung/'
SEO tabbed editor (41f-seo-baufinanzierung.html) into a compact JSON for the
prototype build.py. Reached via SEO -> SEO-Auswahl: Aachen-Eifelimmobilien24
-> Seitenbaum -> Startseite -> Baufinanzierung.
"""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent

soup = BeautifulSoup((BASE / "41f-seo-baufinanzierung.html").read_text(encoding="utf-8"), "lxml")

f_head = soup.find("form", id="form-seohead")
f_sitemap = soup.find("form", id="form-seositemap")
f_textblock = soup.find("form", id="form-seotextblock")


def val(form, name):
    el = form.find(["input", "textarea"], {"name": name})
    if el is None:
        return ""
    return el.get_text() if el.name == "textarea" else el.get("value", "")


def select_options(form, name, selected_value):
    sel = form.find("select", {"name": name})
    return [[o.get("value", ""), o.get_text(strip=True), o.get("value") == selected_value] for o in sel.find_all("option")]


out = {
    "url_path": "/aachen-eifel/baufinanzierung/",
    "kopf_daten": {
        "name": val(f_head, "name"),
        "location": val(f_head, "location"),
        "title": val(f_head, "title"),
        "header": val(f_head, "header"),
        "keywords": val(f_head, "keywords"),
        "description": val(f_head, "description"),
        "robots_options": select_options(f_head, "robots", "index, follow"),
        "revisit_options": select_options(f_head, "revisit-after", "7"),
    },
    "sitemap": {
        "prio_options": select_options(f_sitemap, "prio", "0.1"),
        "update_options": select_options(f_sitemap, "update", "daily"),
    },
    "textblock": {
        "text": val(f_textblock, "block_text"),
        "text2": val(f_textblock, "block_text2"),
    },
}

(BASE / "41-seo-baufinanzierung-data.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "41-seo-baufinanzierung-data.json")
print("description:", out["kopf_daten"]["description"][:50])
print("text len:", len(out["textblock"]["text"]))
