"""Generates index.html: the real 'Werbebanner und PopUps' screen
(/adm/individuell/regionen/edit/immo-werbebanner/?regio=aai24), rebuilt on
the Inspinia theme with real data captured for the example region
Aachen-Eifel (aai24): the Pop-Up Kontaktanfrage section (2 cards) and 4
banner categories (Wohnen/Mieten, Wohnen/Kaufen, Gewerbe/Mieten,
Gewerbe/Kaufen) with 4 banner slots each. Banner images hotlink to the live
image CDN (bilder.regionalimmobilien24.de) — small, already-public crops.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "38-regionen-werbebanner-data.json").read_text(encoding="utf-8"))


def meta_table(rows):
    trs = "".join(
        f'<tr><td><strong>{r["label"]}</strong></td>'
        f'<td class="text-center"><span class="label {"label-success" if r["is_set"] else ""}">{r["value"]}</span></td></tr>'
        for r in rows
    )
    return f'<table class="table table-bordered table-condensed m-b-none"><tbody>{trs}</tbody></table>'


def popup_card(card):
    header = f"""
        <div class="ibox-title">
            <h5>{card["title"]}</h5>
            <div class="ibox-tools"><a class="btn btn-warning btn-xs" title="Banner für Region individualisieren"><i class="fa fa-download"></i></a></div>
        </div>"""
    return f'<div class="ibox"><div style="background:#f7e2c4;">{header}</div><div class="ibox-content">{meta_table(card["rows"])}</div></div>'


def banner_card(banner):
    if banner["has_content"]:
        tools = (
            '<a class="btn btn-success btn-xs" title="Banner bearbeiten"><i class="fa fa-pencil"></i></a> '
            '<a class="btn btn-danger btn-xs" title="Banner löschen und zentralen Stand wieder herstellen"><i class="fa fa-trash-o"></i></a>'
        )
        header_bg = "background:#333333;"
        img_html = f'<img src="{banner["img_src"]}" style="max-width:100%;" alt="">'
    else:
        tools = '<a class="btn btn-warning btn-xs" title="Banner für Region individualisieren"><i class="fa fa-download"></i></a>'
        header_bg = ""
        img_html = '<div class="text-center text-muted" style="padding:20px 0;"><i class="fa fa-image fa-2x"></i></div>'
    return f"""
<div class="ibox">
    <div class="ibox-title" style="{header_bg}">
        <h5 style="{'color:#fff;' if banner['has_content'] else ''}">{banner["title"]}</h5>
        <div class="ibox-tools">{tools}</div>
    </div>
    <div class="ibox-content">{img_html}</div>
    <div class="ibox-content">{meta_table(banner["rows"])}</div>
</div>"""


popup_html = "".join(f'<div class="col-sm-6">{popup_card(card)}</div>' for card in data["popup_cards"])

category_sections = []
for cat in data["categories"]:
    cards = "".join(f'<div class="col-sm-3">{banner_card(b)}</div>' for b in cat["banners"])
    category_sections.append(f"""
<div class="ibox">
    <div class="ibox-title"><h5>{cat["title"]}</h5></div>
</div>
<div class="row">{cards}</div>
""")

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="ibox">
        <div class="ibox-title"><h5>Pop-Up Kontaktanfrage</h5></div>
    </div>
    <div class="row">{popup_html}</div>
    {''.join(category_sections)}
</div>
"""

html = c.page_shell(
    title="Werbebanner und PopUps für AAI24 - RI24 SEO",
    banner_html=c.prototype_banner(
        "Werbebanner und PopUps (/adm/.../regionen/edit/immo-werbebanner/?regio=aai24)",
        "Real banner/PopUp data for the example region Aachen-Eifel (aai24). Banner images hotlink to the live image CDN.",
    ),
    content_html=c.page_heading("Werbebanner und PopUps für AAI24", ["Home", "alle Regionen", "Immobilien Werbebanner", "AAI24"]) + content,
    active_top_item="alle Regionen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
