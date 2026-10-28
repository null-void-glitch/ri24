"""Generates index.html: Makler › Kooperationen
(/adm/individuell/master/makler/kooperation/), rebuilt on Inspinia.

24 real partner cooperation entries. Each row: Sortierung, Name, Logo (50×50
CDN crop), Beschreibung (full text), Link (anonym), and 3 operation buttons
(bearbeiten / sort / löschen).
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE   = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data  = json.loads((SURVEY / "50-kooperationen-rows.json").read_text(encoding="utf-8"))
rows  = data["rows"]
total = data["total"]

thead = """<tr>
    <th style="width:60px;">Sortierung</th>
    <th style="width:220px;">Name</th>
    <th style="width:70px;">Logo</th>
    <th>Beschreibung</th>
    <th style="width:120px;">Link</th>
    <th style="width:120px;"></th>
</tr>"""

tbody_rows = []
for r in rows:
    logo_cell = (
        f'<img src="{r["logo_src"]}" alt="{r["name"]}" '
        f'style="max-width:50px;max-height:50px;object-fit:contain;">'
        if r["logo_src"] else '<span class="text-muted">—</span>'
    )
    link_cell = (
        f'<a href="{r["link_href"]}" target="_blank" class="btn btn-default btn-xs">'
        f'<i class="fa fa-external-link"></i> {r["link_text"] or "Link"}</a>'
        if r["link_href"] else ""
    )
    ops_cell = (
        '<a href="../makler-kooperationen-edit/index.html" class="btn btn-default btn-xs" title="bearbeiten">'
        '<i class="fa fa-pencil"></i></a> '
        '<a href="#" class="btn btn-default btn-xs" title="Sortierung ändern">'
        '<i class="fa fa-sort"></i></a> '
        '<a href="#" class="btn btn-danger btn-xs" title="löschen">'
        '<i class="fa fa-trash"></i></a>'
    )
    cells = [
        f'<span class="badge badge-default">{r["sortierung"]}</span>',
        f'<strong>{r["name"]}</strong>',
        logo_cell,
        f'<small>{r["beschreibung"]}</small>',
        link_cell,
        ops_cell,
    ]
    tbody_rows.append("<tr>" + "".join(f"<td style='vertical-align:middle;'>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table id="koop-table" class="table table-striped table-bordered table-hover">
        <thead>{thead}</thead>
        <tbody>{''.join(tbody_rows)}</tbody>
    </table>
</div>"""

new_btn = (
    '<a href="../makler-kooperationen-new/index.html" class="btn btn-success btn-sm pull-right" style="margin-bottom:10px;">'
    '<i class="fa fa-plus"></i> Neue Kooperation</a>'
    '<div class="clearfix"></div>'
)

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-12">
            {c.ibox(
                f'Kooperationen &nbsp;<span class="badge" style="background:#5b9bd5">{total}</span>',
                new_btn + table_html
            )}
        </div>
    </div>
</div>"""

dt_init = f"""
<script>
$(function () {{
    {c.DATATABLES_DE_JS}
    $('#koop-table').DataTable({{
        autoWidth: false,
        pageLength: 25,
        columnDefs: [
            {{ width: '60px',  targets: 0 }},
            {{ width: '200px', targets: 1 }},
            {{ width: '70px',  targets: 2, orderable: false }},
            {{ width: '110px', targets: 4, orderable: false }},
            {{ width: '110px', targets: 5, orderable: false }},
        ]
    }});
}});
</script>"""

html = c.page_shell(
    title="Kooperationen - Makler - RI24 Admin",
    banner_html=c.prototype_banner(
        "Makler › Kooperationen (/adm/individuell/master/makler/kooperation/)",
        f"{total} real cooperation entries. Logos hotlinked from bilder.regionalimmobilien24.de CDN. "
        "Operation buttons (bearbeiten/sort/löschen) are decorative in the prototype.",
    ),
    content_html=c.page_heading(
        "Kooperationen",
        ["Home", "Makler", "Kooperationen"]
    ) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  #koop-table thead th { background-color: #333333 !important; font-size: 12px; }\n"
        "  #koop-table td small { color: #555; font-size: 11px; line-height: 1.4; display: block; max-width: 420px; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n' + dt_init
    ),
    active_kooperationen_item="Übersicht",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
