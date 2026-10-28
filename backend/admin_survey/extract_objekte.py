"""Offline extraction of the real 'alle Objekte' table from the saved
32-objekte-list.html into a compact JSON for the prototype build.py.
The live page shows 100 real rows per legacy ID-range page (no cap needed
here — this already is one real page of the live UI)."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent

soup = BeautifulSoup((BASE / "32-objekte-list.html").read_text(encoding="utf-8"), "lxml")
table = soup.find_all("table")[0]
tbody = table.find("tbody")
all_rows = tbody.find_all("tr", recursive=False)
print("total real rows:", len(all_rows))

rows_out = []
for r in all_rows:
    tds = r.find_all("td", recursive=False)
    if len(tds) < 14:
        continue

    thumb_a = tds[2].find("a")
    thumb_img = tds[2].find("img")
    thumb_href = thumb_a["href"] if thumb_a else ""
    thumb_src = thumb_img["src"] if thumb_img else ""

    id_a = tds[3].find("a")
    objekt_id = id_a.get_text(strip=True) if id_a else tds[3].get_text(strip=True)
    objekt_href = id_a["href"] if id_a else ""

    adresse_lines = [s.strip() for s in tds[9].stripped_strings]

    rows_out.append({
        "checkbox_value": (tds[1].find("input") or {}).get("value", "") if tds[1].find("input") else "",
        "thumb_href": thumb_href,
        "thumb_src": thumb_src,
        "objekt_id": objekt_id,
        "objekt_href": objekt_href,
        "ext_objekt_nr": tds[4].get_text(strip=True),
        "makler": tds[5].get_text(strip=True),
        "objektart": tds[6].get_text(strip=True),
        "nutzungsart": tds[7].get_text(strip=True),
        "vermarktung": tds[8].get_text(strip=True),
        "adresse_lines": adresse_lines,
        "preis": tds[10].get_text(strip=True),
        "flaeche": tds[11].get_text(strip=True),
        "zimmer": tds[12].get_text(strip=True),
        "geaendert": tds[13].get_text(strip=True),
    })

out = {"total_real_rows": len(all_rows), "rows": rows_out}
(BASE / "32-objekte-rows.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "32-objekte-rows.json", "with", len(rows_out), "rows")
