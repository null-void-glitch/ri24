"""Offline extraction of the real 'Seiten - <Region>' page
(39-regionen-seiten.html) into a compact JSON for the prototype build.py."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent

soup = BeautifulSoup((BASE / "39-regionen-seiten.html").read_text(encoding="utf-8"), "lxml")
tables = soup.find_all("table")


def extract_table(t, has_sortierung):
    rows = t.find_all("tr")[1:]
    out = []
    for r in rows:
        tds = r.find_all("td")
        if not tds:
            continue
        view_a = tds[0].find("a")
        view_href = view_a["href"] if view_a else ""

        name_inputs = tds[1].find_all("input", {"name": "page_name"})
        dir_inputs = tds[1].find_all("input", {"name": "dir"})
        name = name_inputs[0]["value"] if name_inputs else ""
        pfad = dir_inputs[0]["value"] if dir_inputs else ""

        idx = 2
        sortierung = ""
        if has_sortierung:
            sortierung = tds[idx].get_text(strip=True)
            idx += 1

        sektionen = tds[idx].get_text(strip=True)
        idx += 1

        edit_a = tds[idx].find("a") if idx < len(tds) else None
        edit_href = edit_a["href"] if edit_a else ""

        out.append({
            "name": name,
            "pfad": pfad,
            "sortierung": sortierung,
            "sektionen": sektionen,
            "view_href": view_href,
            "edit_href": edit_href,
        })
    return out


hauptnav = extract_table(tables[0], has_sortierung=True)
servicenav = extract_table(tables[1], has_sortierung=True)
ohne_zuordnung = extract_table(tables[2], has_sortierung=False)

out = {
    "hauptnavigation": hauptnav,
    "servicenavigation": servicenav,
    "seiten_ohne_zuordnung": ohne_zuordnung,
}
(BASE / "39-regionen-seiten-data.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "39-regionen-seiten-data.json")
print("hauptnav:", len(hauptnav), "servicenav:", len(servicenav), "ohne_zuordnung:", len(ohne_zuordnung))
