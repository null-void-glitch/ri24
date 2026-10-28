"""Generates index.html: the 'Team' list screen
(/adm/individuell/master/team/list/), rebuilt on the Inspinia theme with all
124 real team member rows scraped from the live backend.

Photos are hotlinked from the public RI24 CDN (already-public 50×50 crops,
same policy as object thumbnails in other prototypes).

The 'Portal Filter' header in the old CMS embeds all ~100 region names as a
dropdown directly inside the column header — replaced here with a cleaner
dropdown filter above the table, matching the pattern used in Makler and
Privatanzeigen.

Eigenschaften icon glyphs (private-use Unicode from the old icon font) are
stripped; only the plain-text badge labels (Baufi, MLP, SMS, WebApp) are kept.

Operations: 4 icon buttons per row — bearbeiten, CRM, Freigabe, löschen.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE   = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data  = json.loads((SURVEY / "45-team-rows.json").read_text(encoding="utf-8"))
rows  = data["rows"]
total = data["total_real_rows"]

# Portal filter options
portals = sorted(set(r["portal"] for r in rows if r["portal"]))
portal_opts = '<option value="">Alle Portale</option>' + "".join(
    f'<option value="{p}">{p}</option>' for p in portals
)
filter_bar = f"""
<div class="row m-b-md">
    <div class="col-sm-4">
        <label for="portal-filter">Portal</label>
        <select id="portal-filter" class="form-control input-sm">
            {portal_opts}
        </select>
    </div>
</div>"""

thead = """
<tr>
    <th>Portal</th>
    <th>Sort.</th>
    <th>Bild</th>
    <th>Name / Position</th>
    <th>Telefon / E-Mail</th>
    <th>Makler</th>
    <th>Eigenschaften</th>
    <th>Operationen</th>
</tr>"""

GLYPH_RE = re.compile(r'[-]')
EIGEN_BADGE_COLORS = {
    "Baufi":  "badge-primary",
    "MLP":    "badge-warning",
    "SMS":    "badge-info",
    "WebApp": "badge-default",
}


def eigen_cell(raw):
    cleaned = GLYPH_RE.sub("", raw).strip()
    badges = []
    for word in cleaned.split():
        color = EIGEN_BADGE_COLORS.get(word, "badge-default")
        badges.append(f'<span class="badge {color}">{word}</span>')
    return " ".join(badges)


def portal_cell(p):
    if not p:
        return ""
    return f'<span class="badge badge-inverse" style="font-size:10px;white-space:normal;">{p}</span>'


def bild_cell(src):
    if not src:
        return '<span class="text-muted"><i class="fa fa-user-circle fa-2x"></i></span>'
    return f'<img src="{src}" width="50" height="50" style="border-radius:4px;object-fit:cover;" alt="">'


def name_cell(lines):
    if not lines:
        return ""
    name = lines[0]
    rest = " ".join(lines[1:])
    if rest:
        return f'{name}<br><small class="text-muted">{rest}</small>'
    return name


def kontakt_cell(lines):
    out = []
    for line in lines:
        line = line.strip()
        if not line or line in ("Telefon:", "Mobil:", "E-Mail:"):
            continue
        if line.startswith("E-Mail:"):
            email = line[7:].strip()
            out.append(f'<a href="mailto:{email}" class="text-muted"><i class="fa fa-envelope-o"></i> {email}</a>')
        elif line.startswith("Telefon:"):
            out.append(f'<i class="fa fa-phone text-muted"></i> {line[8:].strip()}')
        elif line.startswith("Mobil:"):
            out.append(f'<i class="fa fa-mobile text-muted"></i> {line[6:].strip()}')
        else:
            out.append(f'<small class="text-muted">{line}</small>')
    return "<br>".join(out)


def ops_cell():
    return (
        '<a href="../team-edit/index.html" class="btn btn-default btn-xs" title="bearbeiten"><i class="fa fa-pencil"></i></a> '
        '<a href="#" class="btn btn-default btn-xs" title="CRM"><i class="fa fa-address-card-o"></i></a> '
        '<a href="#" class="btn btn-default btn-xs" title="Freigabe"><i class="fa fa-unlock-alt"></i></a> '
        '<a href="#" class="btn btn-danger btn-xs" title="löschen"><i class="fa fa-trash-o"></i></a>'
    )


body_rows = []
for r in rows:
    cells = [
        portal_cell(r["portal"]),
        r["sortierung"],
        bild_cell(r["bild_src"]),
        name_cell(r["name_lines"]),
        kontakt_cell(r["kontakt_lines"]),
        r["makler"],
        eigen_cell(r["eigenschaften"]),
        ops_cell(),
    ]
    body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-team">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>"""

new_btn = '<a href="#" class="btn btn-primary btn-sm"><i class="fa fa-plus"></i> Neues Teammitglied</a>'

panel_body = f"""
<div class="row m-b-sm">
    <div class="col-sm-12 text-right">{new_btn}</div>
</div>
{filter_bar}
{table_html}"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-12">
            {c.ibox(f"alle Teammitglieder (alle Regionen) &nbsp;<span class=\"badge\" style=\"background:#5b9bd5\">{total}</span>", panel_body)}
        </div>
    </div>
</div>"""

SCRIPT = """
<script>
$(function () {
    var table = $('.data-table-team').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [0], width: '90px' },
            { targets: [1], width: '45px' },
            { targets: [2], width: '60px', orderable: false },
            { targets: [7], width: '130px', orderable: false }
        ]
    });

    $('#portal-filter').on('change', function () {
        var val = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(0).search(val ? '^' + val + '$' : '', true, false).draw();
    });
});
</script>
"""

html = c.page_shell(
    title="Team - RI24 Admin",
    banner_html=c.prototype_banner(
        "Team (/adm/.../master/team/list/)",
        f"All {total} real team members. Photos hotlinked from the public RI24 CDN (50×50 crops). "
        "Eigenschaften icon glyphs stripped — text badges (Baufi/MLP/SMS/WebApp) preserved.",
    ),
    content_html=c.page_heading("Team", ["Home", "Team"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-team thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-team a:not(.btn) { color: #333333 !important; }\n"
        "  .data-table-team a:not(.btn):hover { color: #A4C735 !important; }\n"
        "  .data-table-team .badge-inverse { background-color: #333333 !important; }\n"
        "  .data-table-team .badge-primary { background-color: #A4C735 !important; }\n"
        "  .data-table-team .badge-warning { background-color: #f0ad4e !important; }\n"
        "  .data-table-team .badge-info    { background-color: #5bc0de !important; }\n"
        "  .data-table-team td { vertical-align: middle; }\n"
        "  .data-table-team thead th.sorting, .data-table-team thead th.sorting_asc, .data-table-team thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-team thead .sorting:after, .data-table-team thead .sorting_asc:after, .data-table-team thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_top_item="Team",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
