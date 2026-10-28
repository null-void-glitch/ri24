"""Offline extraction of the real 'Seite <X> bearbeiten' screen
(40-regionen-page-edit.html) into a compact JSON for the prototype
build.py. Captured for page_id=bfo2 (Baufinanzierung), region aai24."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent

soup = BeautifulSoup((BASE / "40-regionen-page-edit.html").read_text(encoding="utf-8"), "lxml")
tables = soup.find_all("table")

grund_tds = tables[0].find_all("tr")[1:][0].find_all("td")
name = grund_tds[0].find("input", {"name": "page_name"})["value"]
dir_ = grund_tds[0].find("input", {"name": "dir"})["value"]
sortierung = grund_tds[1].get_text(strip=True)
sektionen = " ".join(grund_tds[2].get_text(" ", strip=True).split())

sections = []
for r in tables[1].find_all("tr")[1:]:
    tds = r.find_all("td")
    bez = tds[1].find("input", {"name": "section_bez"})["value"]
    sort_inp = tds[2].find("input", {"name": "sort"})
    sort_val = sort_inp.get("value", "") if sort_inp else ""
    sections.append({"bezeichnung": bez, "sortierung": sort_val})

out = {
    "page_name": name,
    "pfad": dir_,
    "sortierung": sortierung,
    "sektionen": sektionen,
    "sections": sections,
}
(BASE / "40-regionen-page-edit-data.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "40-regionen-page-edit-data.json")
print(json.dumps(out, ensure_ascii=False, indent=2))
