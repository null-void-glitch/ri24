"""Generates index.html: the real 'alle Regionen' screen
(/adm/individuell/regionen/config/), rebuilt on the Inspinia theme (real
DataTables) with all 105 real rows captured from the live backend (104
regions + the special "Seiten des Vatermodells" template row, which has no
Geodaten/aktiv/individuell of its own — kept as a distinct header-like row,
same as on the live site).

Each region row's 5 "anpassen"/"setzen" buttons on the live site open a
per-region edit screen (Parameter, Geodaten, Mailings, Immo Werbebanner &
PopUp, Seiten) pre-filled with that region's data. This migration captured
one example region (Aachen-Eifel / aai24) in full for each of those 5
screens — see prototypes/regionen-params, regionen-geodaten,
regionen-mailings, regionen-werbebanner, regionen-seiten. Every row's
action buttons here link to those same 5 example pages regardless of which
region's row they're on (disclosed below) — this list itself has no
"submenu" on the live site, so those 5 destinations are also added as a
sidebar sub-menu under "alle Regionen" for direct access.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "34-regionen-rows.json").read_text(encoding="utf-8"))
rows = data["rows"]
total_real_rows = data["total_real_rows"]

SUB_PAGES = {
    "params": ("../regionen-params/index.html", "T", "Parameter individualisieren"),
    "geodaten": ("../regionen-geodaten/index.html", "G", "Geodaten anpassen"),
    "mailings": ("../regionen-mailings/index.html", "M", "Mailings anpassen"),
    "werbebanner": ("../regionen-werbebanner/index.html", "W", "Immo Werbebanner & PopUp anpassen"),
    "seiten": ("../regionen-seiten/index.html", "S", "Seiten individualisieren"),
}

thead = """
<tr>
    <th>Code</th>
    <th>Verzeichnis</th>
    <th>Name</th>
    <th>aktiv</th>
    <th>individuell</th>
    <th>Parameter</th>
    <th>Geodaten</th>
    <th>Mailings</th>
    <th>Werbebanner &amp; PopUp</th>
    <th>Seiten</th>
</tr>"""


def bool_checkbox(value):
    if value is None:
        return ""
    checked = " checked" if value else ""
    return f'<input type="checkbox" disabled{checked}>'


def action_btn(key):
    href, letter, title = SUB_PAGES[key]
    return f'<a href="{href}" class="btn btn-default btn-xs" title="{title}">anpassen</a>'


body_rows = []
for r in rows:
    if r["is_vatermodell"]:
        # Same 10 <td> count as every other row (no colspan) — DataTables
        # requires a consistent cell count per row to index columns safely.
        row_html = (
            "<tr>"
            '<td></td>'
            f'<td><strong>{r["name"]}</strong></td>'
            '<td></td><td></td><td></td>'
            f'<td>{action_btn("params")}</td>'
            '<td></td>'
            f'<td>{action_btn("mailings")}</td>'
            f'<td>{action_btn("werbebanner")}</td>'
            f'<td>{action_btn("seiten")}</td>'
            "</tr>"
        )
        body_rows.append(row_html)
        continue

    cells = [
        f'<span class="badge badge-inverse">{r["code"]}</span>',
        f'<a href="https://www.regionalimmobilien24.de{r["verzeichnis"]}" target="_blank">{r["verzeichnis"]}</a>',
        r["name"],
        bool_checkbox(r["aktiv"]),
        bool_checkbox(r["individuell"]),
        action_btn("params"),
        action_btn("geodaten"),
        action_btn("mailings"),
        action_btn("werbebanner"),
        action_btn("seiten"),
    ]
    body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-regionen">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>
"""

panel_body = f"""
<p class="text-muted">
    All {total_real_rows} real rows shown (104 regions + the "Seiten des Vatermodells" template row).
    Every row's action buttons link to the same 5 example sub-pages (captured in full for one
    region, Aachen-Eifel / aai24) regardless of which region's row they're on — see build.py docstring.
</p>
{table_html}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("alle Regionen", panel_body)}</div></div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    $('.data-table-regionen').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [3, 4], orderable: false, className: 'text-center', width: '60px' },
            { targets: [5, 6, 7, 8, 9], orderable: false }
        ]
    });
});
</script>
"""

html = c.page_shell(
    title="alle Regionen - RI24 SEO",
    banner_html=c.prototype_banner(
        "alle Regionen (/adm/individuell/regionen/config/)",
        f"All {total_real_rows} real rows shown. Action buttons link to one example region's sub-pages — see build.py docstring.",
    ),
    content_html=c.page_heading("alle Regionen", ["Home", "alle Regionen"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-regionen thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-regionen a:not(.btn) { color: #333333 !important; }\n"
        "  .data-table-regionen a:not(.btn):hover, .data-table-regionen a:not(.btn):focus { color: #A4C735 !important; }\n"
        "  .data-table-regionen .badge-inverse { background-color: #333333 !important; }\n"
        "  .data-table-regionen thead th.sorting, .data-table-regionen thead th.sorting_asc, .data-table-regionen thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-regionen thead .sorting:after, .data-table-regionen thead .sorting_asc:after, .data-table-regionen thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_top_item="alle Regionen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
