"""Offline extraction of the real 'Werbebanner und PopUps' page
(38-regionen-werbebanner.html) into a compact JSON for the prototype
build.py."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent

soup = BeautifulSoup((BASE / "38-regionen-werbebanner.html").read_text(encoding="utf-8"), "lxml")
boxes = soup.find_all("div", class_="widget-box")


def meta_rows(box):
    table = box.find_all("div", class_="widget-content")[-1]
    out = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) != 2:
            continue
        label = tds[0].get_text(strip=True)
        span = tds[1].find("span")
        value = span.get_text(strip=True) if span else tds[1].get_text(strip=True)
        is_set = bool(span and "label-success" in (span.get("class") or []))
        out.append({"label": label, "value": value, "is_set": is_set})
    return out


# boxes[0] = Pop-Up Kontaktanfrage section header (just a heading, no own content)
# boxes[1], boxes[2] = the two Pop-Up cards (Wohnen/Kaufen, Gewerbe/Kaufen)
popup_cards = []
for b in boxes[1:3]:
    h5 = b.find("h5")
    popup_cards.append({
        "title": h5.get_text(strip=True),
        "rows": meta_rows(b),
    })

# Remaining boxes: 4 category sections, each = 1 header box + 4 banner boxes.
CATEGORY_TITLES = ["Wohnen / Mieten", "Wohnen / Kaufen", "Gewerbe / Mieten", "Gewerbe / Kaufen"]
categories = []
idx = 3
for cat_title in CATEGORY_TITLES:
    header_box = boxes[idx]
    assert header_box.find("h5").get_text(strip=True) == cat_title, (idx, header_box.find("h5").get_text(strip=True))
    idx += 1
    banners = []
    for _ in range(4):
        b = boxes[idx]
        idx += 1
        title = b.find("h5").get_text(strip=True)
        edit_a = b.find("a", class_="btn-success")
        delete_a = b.find("a", class_="btn-danger")
        has_content = edit_a is not None
        img = b.find("img")
        img_src = img["src"] if img else ""
        banners.append({
            "title": title,
            "has_content": has_content,
            "img_src": img_src,
            "rows": meta_rows(b),
        })
    categories.append({"title": cat_title, "banners": banners})

out = {"popup_cards": popup_cards, "categories": categories}
(BASE / "38-regionen-werbebanner-data.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote", BASE / "38-regionen-werbebanner-data.json")
print("popup cards:", len(popup_cards), "categories:", len(categories))
