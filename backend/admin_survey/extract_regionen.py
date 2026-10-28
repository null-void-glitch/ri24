"""Offline extraction of the real 'alle Regionen' table from the saved
34-regionen-config.html (105 real rows: 1 Vatermodell template row + 104
regions) into a compact JSON for the prototype build.py."""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent

soup = BeautifulSoup((BASE / "34-regionen-config.html").read_text(encoding="utf-8"), "lxml")
table = soup.find_all("table")[0]
all_rows = table.find_all("tr")[1:]
print("total real rows:", len(all_rows))


def strip_sess(href):
    return re.sub(r"[?&]admsess=[a-z0-9]+", "", href or "")


rows_out = []
for r in all_rows:
    tds = r.find_all("td", recursive=False)
    if len(tds) == 7:
        # Vatermodell template row
        links = {}
        for td, key in zip([tds[2], tds[4], tds[5], tds[6]], ["params", "mailings", "werbebanner", "seiten"]):
            a = td.find("a")
            if a:
                links[key] = strip_sess(a["href"])
        rows_out.append({
            "is_vatermodell": True,
            "code": "",
            "verzeichnis": "",
            "name": "Seiten des Vatermodells",
            "aktiv": None,
            "individuell": None,
            "links": links,
        })
        continue

    if len(tds) != 10:
        continue

    code = tds[0].get_text(strip=True)
    verzeichnis_a = tds[1].find("a")
    verzeichnis = verzeichnis_a.get_text(" ", strip=True).replace(" ", " ").strip() if verzeichnis_a else ""
    verzeichnis = " ".join(verzeichnis.split())
    name = tds[2].get_text(strip=True)
    aktiv = tds[3].find("input", {"type": "checkbox"}) is not None and tds[3].find("input", {"type": "checkbox"}).has_attr("checked")
    individuell = tds[4].find("input", {"type": "checkbox"}) is not None and tds[4].find("input", {"type": "checkbox"}).has_attr("checked")

    links = {}
    for td, key in zip(tds[5:10], ["params", "geodaten", "mailings", "werbebanner", "seiten"]):
        a = td.find("a")
        if a:
            links[key] = strip_sess(a["href"])

    rows_out.append({
        "is_vatermodell": False,
        "code": code,
        "verzeichnis": verzeichnis,
        "name": name,
        "aktiv": aktiv,
        "individuell": individuell,
        "links": links,
    })

out = {"total_real_rows": len(rows_out), "rows": rows_out}
(BASE / "34-regionen-rows.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "34-regionen-rows.json", "with", len(rows_out), "rows")
