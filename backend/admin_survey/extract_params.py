"""Offline extraction of the real 'Parameter individualisieren' page
(35-regionen-params.html) — ~12 ibox panels, each with several fields laid
out as (label+input) / Platzhalter / Beispiel-Hinweis triplets — into a
compact JSON for the prototype build.py."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent

soup = BeautifulSoup((BASE / "35-regionen-params.html").read_text(encoding="utf-8"), "lxml")

GROUP_TITLES = ["Startseite", "Baufinanzierung, Strom & Gas", "Impressum"]


def extract_field(cg):
    """One .control-group div -> a field dict, or None if not a recognizable
    label/input/platzhalter/hinweis triplet (e.g. a lone checkbox row)."""
    rows = cg.find_all("tr", recursive=True)
    if not rows:
        return None
    label_row = rows[0]
    label_th = label_row.find("th")

    # Standalone checkbox rows have no <th> label — the label is a <label>
    # tag sharing the single <td> with the checkbox itself.
    if label_th is None:
        label_tag = label_row.find("label")
        checkbox = label_row.find("input", {"type": "checkbox"})
        if label_tag is not None and checkbox is not None:
            return {
                "label": label_tag.get_text(strip=True),
                "type": "checkbox",
                "value": checkbox.has_attr("checked"),
                "options": [],
                "platzhalter": "",
                "hinweis": "",
            }
        return None

    label = label_th.get_text(" ", strip=True)

    control_td = label_row.find_all("td")
    control_html = control_td[0] if control_td else None

    field_type = "text"
    value = ""
    options = []
    if control_html is not None:
        inp = control_html.find("input")
        sel = control_html.find("select")
        ta = control_html.find("textarea")
        if sel is not None:
            field_type = "select"
            options = [(o.get("value", ""), o.get_text(strip=True), o.has_attr("selected")) for o in sel.find_all("option")]
        elif ta is not None:
            field_type = "textarea"
            value = ta.get_text(strip=True)
        elif inp is not None:
            itype = inp.get("type", "text")
            if itype == "checkbox":
                field_type = "checkbox"
                value = inp.has_attr("checked")
            elif itype == "file":
                field_type = "file"
            else:
                field_type = "text"
                value = inp.get("value", "")

    platzhalter = ""
    hinweis = ""
    for r in rows[1:]:
        th = r.find("th")
        td = r.find("td")
        if not th or not td:
            continue
        key = th.get_text(strip=True)
        if key.startswith("Platzhalter"):
            platzhalter = td.get_text(strip=True)
        elif key.startswith("Beispiel"):
            hinweis = td.get_text(" ", strip=True)

    return {
        "label": label,
        "type": field_type,
        "value": value,
        "options": options,
        "platzhalter": platzhalter,
        "hinweis": hinweis,
    }


panels = []
for h2 in soup.find_all("h2"):
    group_title = h2.get_text(strip=True)
    if group_title not in GROUP_TITLES:
        continue
    # Panels for this group sit between this h2 and the next h2 in document order.
    for sib in h2.find_all_next():
        if sib.name == "h2":
            break
        if sib.name == "h5" and sib.find_parent("div", class_="widget-title"):
            box = sib.find_parent("div", class_="widget-box")
            if box is None:
                continue
            panel_title = sib.get_text(strip=True)
            fields = []
            for cg in box.find_all("div", class_="control-group"):
                f = extract_field(cg)
                if f:
                    fields.append(f)
            # Fields without a recognizable 3-row shape (e.g. plain checkbox
            # rows, selects outside control-group) handled separately below.
            panels.append({
                "group": group_title,
                "title": panel_title,
                "fields": fields,
            })

out = {"panels": panels}
(BASE / "35-regionen-params-data.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "35-regionen-params-data.json")
for p in panels:
    print(f"  [{p['group']}] {p['title']}: {len(p['fields'])} fields")
