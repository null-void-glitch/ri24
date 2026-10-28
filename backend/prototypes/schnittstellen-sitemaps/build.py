"""Generates index.html: Schnittstellen › Sitemaps (Mitula)
(/adm/individuell/master/interface/mitula/), rebuilt on Inspinia.

103 real rows. Each row = one region with:
  - Region code (e.g. VI24)
  - Link to the full XML sitemap
  - 4 toggle-status indicators (Miete/Wohnung, Kauf/Wohnung, Kauf/Haus, Kauf/Grundstück)
  - Individual sub-feed links

On the live backend the toggles are per-row mini-POST-forms (submit = toggle).
In the prototype they are rendered as green check / grey dash badges.
Sub-feed links are real clickable URLs.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE   = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data  = json.loads((SURVEY / "49-mitula-rows.json").read_text(encoding="utf-8"))
rows  = data["rows"]
total = data["total_real_rows"]

FEED_LABELS = ["Miete / Wohnung", "Kauf / Wohnung", "Kauf / Haus", "Kauf / Grundstück"]

thead = """<tr>
    <th rowspan="2" style="vertical-align:middle;">Region</th>
    <th rowspan="2" style="vertical-align:middle;">Gesamt-Sitemap</th>
    <th colspan="2" class="text-center">Miete</th>
    <th colspan="2" class="text-center">Kauf</th>
    <th rowspan="2" style="vertical-align:middle;">Einzel-Links</th>
</tr>
<tr>
    <th class="text-center">Wohnung</th>
    <th class="text-center">Wohnung</th>
    <th class="text-center">Haus</th>
    <th class="text-center">Grundstück</th>
</tr>"""


def toggle_cell(active):
    if active:
        return '<span class="badge" style="background:#A4C735;cursor:pointer;" title="aktiv — klicken zum Deaktivieren"><i class="fa fa-check"></i></span>'
    return '<span class="badge badge-default" style="cursor:pointer;color:#888;" title="inaktiv — klicken zum Aktivieren"><i class="fa fa-minus"></i></span>'


def sub_links_cell(links):
    parts = []
    for lnk in links:
        label = lnk["text"].split("https://")[0].strip() or lnk["text"][:30]
        href  = lnk["href"]
        parts.append(f'<a href="{href}" target="_blank" class="label label-default m-r-xs">{label}</a>')
    return " ".join(parts)


tbody_rows = []
for r in rows:
    chks = r.get("checkboxes", [True, True, True, True])
    while len(chks) < 4:
        chks.append(True)
    code = r["region"].lower()
    main_href = r.get("main_link", f"https://www.regionalimmobilien24.de/objects.{code}.xml")
    cells = [
        f'<strong>{r["region"]}</strong>',
        f'<a href="{main_href}" target="_blank" class="text-muted"><i class="fa fa-rss"></i> {code}</a>',
        toggle_cell(chks[0]),
        toggle_cell(chks[1]),
        toggle_cell(chks[2]),
        toggle_cell(chks[3]),
        sub_links_cell(r.get("sub_links", [])),
    ]
    td_aligns = ["", "", ' class="text-center"', ' class="text-center"',
                 ' class="text-center"', ' class="text-center"', ""]
    tbody_rows.append(
        "<tr>" + "".join(f"<td{a}>{cell}</td>" for a, cell in zip(td_aligns, cells)) + "</tr>"
    )

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover table-sitemaps">
        <thead>{thead}</thead>
        <tbody>{''.join(tbody_rows)}</tbody>
    </table>
</div>"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-12">
            {c.ibox(
                f'Übersicht &nbsp;<span class="badge" style="background:#5b9bd5">{total}</span>',
                table_html
            )}
        </div>
    </div>
</div>"""

html = c.page_shell(
    title="Sitemaps (Mitula) - Schnittstellen - RI24 Admin",
    banner_html=c.prototype_banner(
        "Schnittstellen › Sitemaps (Mitula) (/adm/.../master/interface/mitula/)",
        f"All {total} real region rows. Aktivieren/Deaktivieren toggles are decorative in the prototype "
        "(live backend uses per-row mini-POST forms). Sub-feed links are real clickable XML URLs.",
    ),
    content_html=c.page_heading("Sitemaps (Mitula)", ["Home", "Schnittstellen", "Sitemaps (Mitula)"]) + content,
    extra_head=(
        "<style>\n"
        "  .table-sitemaps thead th { background-color: #333333 !important; color: #fff; font-size: 12px; text-align: center; }\n"
        "  .table-sitemaps td { vertical-align: middle; font-size: 12px; }\n"
        "  .table-sitemaps a { color: #555; }\n"
        "  .table-sitemaps a:hover { color: #A4C735; }\n"
        "  .label-default { background-color: #5b9bd5; color: #fff; font-size: 11px; padding: 3px 6px; border-radius: 3px; white-space: nowrap; }\n"
        "</style>"
    ),
    active_schnittstellen_item="Sitemaps (Mitula)",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
