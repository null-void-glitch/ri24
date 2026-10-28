"""Generates index.html: the real 'Kundenlogin' screen
(/adm/individuell/master/tools/kundenlogin/), rebuilt on the Inspinia theme
(real DataTables) with 250 real customer-account rows captured from the live
backend (the full list has 5,142 real rows — capped here for a reviewable
file, same practice used for Übersicht Makler / Anfragen).

Per instruction, three real columns are dropped from the live screen:
"ermitteltes Portal" (a secondary/derived portal guess, redundant next to the
real "Portal" column) and the "Bewerbermappe Miete" / "Bewerbermappe Kauf"
buttons (a separate feature, not part of this migration). The real "Kunde
umhängen" and "löschen" row actions are kept, restyled to the green/gray CI
and consolidated into one "Aktionen" column (was two separate blank-header
columns on the live site). "Suchauftrag" is kept as a compact badge list
(code + "gültig bis" tooltip) — the live site's click-to-expand dialog isn't
reproduced since this is a static capture.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "31-kundenlogin-rows.json").read_text(encoding="utf-8"))
rows = data["rows"]
total_real_rows = data["total_real_rows"]

# Same real regioncode list used across the other prototypes' Region filters.
region_opts = json.loads((SURVEY / "16-dashboard-nutzer-forms.json").read_text(encoding="utf-8"))[0]["selects"]["regioncode"]


# The real backend's Bootstrap-2-era ".badge-important" class isn't part of
# this Inspinia theme (it only ships primary/success/warning/danger/info/
# inverse/white/disable) — remapped to the closest available equivalent
# (badge-danger) so the red/gray distinction the live site conveys survives.
LOGIN_BADGE_CLASS = {
    "google": "badge-danger",
    "facebook": "badge-info",
    "apple": "",
    "ri24": "badge-success",
}
STATUS_BADGE_CLASS = {
    "aktiv": "badge-success",
    "inaktiv": "badge-danger",
    "verifiziert": "badge-success",
    "nicht verifiziert": "badge-danger",
}

region_filter_options = "".join(
    f'<option value="{value}">{text}</option>' for value, text, _sel in region_opts
)
region_filter_bar = f"""
<div class="row m-b-md">
    <div class="col-sm-4">
        <label for="portal-filter">Portal</label>
        <select id="portal-filter" class="form-control input-sm">
            {region_filter_options}
        </select>
    </div>
</div>"""

thead = """
<tr>
    <th>Portal</th>
    <th>Kunde</th>
    <th>Login</th>
    <th>Status</th>
    <th>Registriert seit</th>
    <th>letzter Besuch</th>
    <th>Suchaufträge</th>
    <th>Aktionen</th>
</tr>"""


def login_badges(codes):
    return " ".join(
        f'<span class="badge {LOGIN_BADGE_CLASS.get(code, "")}">{code}</span>' for code in codes
    )


def status_badges(codes):
    return " ".join(
        f'<span class="badge {STATUS_BADGE_CLASS.get(code, "")}">{code}</span>' for code in codes
    )


def kunde_cell(r):
    detail = "<br>".join(l for l in r["detail_lines"][1:] if l)
    return f'{r["name"]}<br><small class="text-muted">{detail}</small>'


def suchauftrag_cell(entries):
    if not entries:
        return '<span class="text-muted">&mdash;</span>'
    shown = entries[:4]
    badges = "".join(
        f'<span class="label label-default" title="gültig bis: {e["gueltig_bis"]}">'
        f'<i class="fa fa-search"></i> {e["code"]}</span> '
        for e in shown
    )
    more = f'<span class="text-muted">+{len(entries) - 4} weitere</span>' if len(entries) > 4 else ""
    return badges + more


def aktionen_cell():
    return (
        '<a href="#" class="btn btn-success btn-xs" title="Kunde umhängen">'
        '<i class="fa fa-exchange"></i> umhängen</a> '
        '<a href="#" class="btn btn-danger btn-xs" title="Kundenkonto löschen">'
        '<i class="fa fa-trash-o"></i> löschen</a>'
    )


body_rows = []
for r in rows:
    cells = [
        r["portal"] or '<span class="text-muted">&mdash;</span>',
        kunde_cell(r),
        login_badges(r["login_badges"]),
        status_badges(r["status_badges"]),
        r["registriert"],
        r["letzter_besuch"],
        suchauftrag_cell(r["suchauftrag"]),
        aktionen_cell(),
    ]
    body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-kundenlogin">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>
"""

panel_body = f"""
<p class="text-muted">
    {len(rows)} of {total_real_rows} real customer accounts shown (capped for a reviewable file).
    "ermitteltes Portal" and the "Bewerbermappe Miete"/"Bewerbermappe Kauf" buttons are dropped
    per instruction; "Kunde umhängen" and "löschen" are kept, consolidated into one Aktionen column.
</p>
{region_filter_bar}
{table_html}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("Kundenlogin", panel_body)}</div></div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    var table = $('.data-table-kundenlogin').DataTable({
        pageLength: 25,
        autoWidth: false
    });

    $('#portal-filter').on('change', function () {
        var value = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(0).search(value ? '^' + value + '$' : '', true, false).draw();
    });
});
</script>
"""

html = c.page_shell(
    title="Kundenlogin - RI24 SEO",
    banner_html=c.prototype_banner(
        "Kundenlogin (/adm/.../tools/kundenlogin/)",
        f"{len(rows)} of {total_real_rows} real customer accounts shown (capped for a reviewable file). "
        "\"ermitteltes Portal\" and the Bewerbermappe Miete/Kauf buttons dropped per instruction.",
    ),
    content_html=c.page_heading("Übersicht", ["Home", "Kundenlogin"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-kundenlogin thead th { background-color: #333333 !important; text-align: left !important; }\n"
        "  .data-table-kundenlogin a { color: #333333 !important; }\n"
        "  .data-table-kundenlogin a:hover, .data-table-kundenlogin a:focus { color: #A4C735 !important; }\n"
        "  .data-table-kundenlogin .btn-success { background-color: #A4C735 !important; border-color: #8fae2d !important; }\n"
        "  .data-table-kundenlogin .btn-success:hover { background-color: #8fae2d !important; }\n"
        "  .data-table-kundenlogin .label-default { background-color: #7a7a7a !important; }\n"
        "  .data-table-kundenlogin thead th.sorting, .data-table-kundenlogin thead th.sorting_asc, .data-table-kundenlogin thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; }\n"
        "  .data-table-kundenlogin thead .sorting:after, .data-table-kundenlogin thead .sorting_asc:after, .data-table-kundenlogin thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 4px !important; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_top_item="Nutzer",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
