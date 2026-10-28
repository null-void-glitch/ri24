"""Offline extraction of the real Kundenlogin table from the saved
31-kundenlogin.html (5,142 real rows) into a compact JSON for the prototype
build.py — capped at 250 rows, same practice as the other prototypes."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
CAP = 250

soup = BeautifulSoup((BASE / "31-kundenlogin.html").read_text(encoding="utf-8"), "lxml")
main = soup.find_all("table")[0]
tbody = main.find("tbody")
all_rows = tbody.find_all("tr", recursive=False)
print("total real rows:", len(all_rows))

rows_out = []
for r in all_rows[:CAP]:
    tds = r.find_all("td", recursive=False)
    if len(tds) < 11:
        continue

    portal = tds[0].get_text(strip=True)

    kunde_td = tds[2]
    small = kunde_td.find("small")
    name = kunde_td.contents[0].strip() if kunde_td.contents else ""
    detail_lines = [s.strip() for s in small.stripped_strings] if small else []

    login_badges = [b.get_text(strip=True) for b in tds[3].find_all("span", class_="badge")]
    status_badges = [b.get_text(strip=True) for b in tds[4].find_all("span", class_="badge")]

    registriert = tds[5].get_text(strip=True)
    letzter_besuch = tds[6].get_text(strip=True)

    umhaengen_a = tds[8].find("a")
    umhaengen_href = umhaengen_a["href"] if umhaengen_a else ""

    # Suchauftrag: nested mini-table of saved search-agent codes; keep just a
    # compact summary (count) plus the first few codes + their "gültig bis".
    suchauftrag = []
    inner_table = tds[9].find("table")
    if inner_table:
        for inner_tr in inner_table.find("tbody").find_all("tr", recursive=False):
            inner_tds = inner_tr.find_all("td", recursive=False)
            if len(inner_tds) < 3:
                continue
            code_a = inner_tds[1].find("a")
            code = code_a.get_text(strip=True) if code_a else ""
            detail = inner_tds[3]
            gueltig = ""
            g_span = detail.find("span", title="gültig bis")
            if g_span:
                gueltig = g_span.get_text(strip=True)
            suchauftrag.append({"code": code, "gueltig_bis": gueltig})

    loeschen_a = tds[10].find("a")
    loeschen_href = loeschen_a["href"] if loeschen_a else ""

    rows_out.append({
        "portal": portal,
        "name": name,
        "detail_lines": detail_lines,
        "login_badges": login_badges,
        "status_badges": status_badges,
        "registriert": registriert,
        "letzter_besuch": letzter_besuch,
        "umhaengen_href": umhaengen_href,
        "suchauftrag": suchauftrag,
        "loeschen_href": loeschen_href,
    })

out = {"total_real_rows": len(all_rows), "rows": rows_out}
(BASE / "31-kundenlogin-rows.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "31-kundenlogin-rows.json", "with", len(rows_out), "rows")
