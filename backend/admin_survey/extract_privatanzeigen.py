"""Offline extraction of the real 'alle Privatanzeigen' table from the saved
33-privatanzeigen-list.html (443 real rows) into a compact JSON for the
prototype build.py — capped at 250 rows, same practice as the other
prototypes."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
CAP = 250

soup = BeautifulSoup((BASE / "33-privatanzeigen-list.html").read_text(encoding="utf-8"), "lxml")
table = soup.find_all("table")[0]
tbody = table.find("tbody")
all_rows = tbody.find_all("tr", recursive=False)
print("total real rows:", len(all_rows))

rows_out = []
for r in all_rows[:CAP]:
    tds = r.find_all("td", recursive=False)
    if len(tds) < 10:
        continue

    region = tds[0].get_text(strip=True)

    verkaeufer_lines = [s.strip() for s in tds[1].stripped_strings]

    objektanschrift_lines = [s.strip() for s in tds[2].stripped_strings]
    objekttyp = tds[3].get_text(" ", strip=True)
    objekttitel = tds[4].get_text(strip=True)

    id_a = tds[5].find("a")
    objekt_id = id_a.get_text(strip=True) if id_a else tds[5].get_text(strip=True)
    objekt_href = id_a["href"] if id_a else ""

    beginn = tds[6].get_text(strip=True)
    status = tds[7].find("span")
    status_text = status.get_text(strip=True) if status else tds[7].get_text(strip=True)

    ende_input = tds[8].find("input")
    ende_value = ende_input["value"] if ende_input else ""

    ops_links = tds[9].find_all("a")
    ausblenden_href = ops_links[0]["href"] if len(ops_links) > 0 else ""
    loeschen_href = ops_links[1]["href"] if len(ops_links) > 1 else ""

    rows_out.append({
        "region": region,
        "verkaeufer_lines": verkaeufer_lines,
        "objektanschrift_lines": objektanschrift_lines,
        "objekttyp": objekttyp,
        "objekttitel": objekttitel,
        "objekt_id": objekt_id,
        "objekt_href": objekt_href,
        "beginn": beginn,
        "status": status_text,
        "ende": ende_value,
        "row_bg": r.get("style") or "",
        "ausblenden_href": ausblenden_href,
        "loeschen_href": loeschen_href,
    })

out = {"total_real_rows": len(all_rows), "rows": rows_out}
(BASE / "33-privatanzeigen-rows.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "33-privatanzeigen-rows.json", "with", len(rows_out), "rows")
