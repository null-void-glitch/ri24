"""Generates index.html: the real 'Privatanzeigen (alle Regionen)' screen
(/adm/individuell/master/privatanzeige/), rebuilt on the Inspinia theme (real
DataTables) with 250 real listing rows captured from the live backend (the
full list has 443 real rows — capped here for a reviewable file, same
practice used for the oversized tables in the other prototypes).

Security/privacy note: unlike the Makler tables (business entities), the
"Verkäufer" column here is a private individual's real name, home address,
personal e-mail and phone number — the seller behind a classified ad, not a
company. Kept real and disclosed transparently (same stance already taken
for Kundenlogin's customer names/e-mails), since this is an internal
migration review of the live admin backend's own data, not a public
publication. The live table's own commented-out "Passwort"/"Tarif" columns
(visible in the raw source, already disabled on the real site) are not
reproduced — they're dead code on the live page too.

The real per-row "Ende" date field + "speichern" submit is kept, restyled
to the floppy-disk save-icon pattern already used on Makler bearbeiten. The
real "ausblenden" / "löschen" row-action icons are kept as labeled buttons,
same pattern as Kundenlogin's "umhängen" / "löschen". Some rows carry a real
light-red background color from the live data (inline style, cause unclear
from the markup alone — possibly a soon-to-expire flag) — preserved as-is
rather than guessed at or dropped.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "33-privatanzeigen-rows.json").read_text(encoding="utf-8"))
rows = data["rows"]
total_real_rows = data["total_real_rows"]

region_opts = json.loads((SURVEY / "16-dashboard-nutzer-forms.json").read_text(encoding="utf-8"))[0]["selects"]["regioncode"]

region_filter_options = "".join(
    f'<option value="{value}">{text}</option>' for value, text, _sel in region_opts
)
region_filter_bar = f"""
<div class="row m-b-md">
    <div class="col-sm-4">
        <label for="region-filter">Region</label>
        <select id="region-filter" class="form-control input-sm">
            {region_filter_options}
        </select>
    </div>
</div>"""

thead = """
<tr>
    <th>Region</th>
    <th>Verkäufer</th>
    <th>Objektanschrift</th>
    <th>Objekttyp</th>
    <th>Objekttitel</th>
    <th>Objekt-ID</th>
    <th>Beginn</th>
    <th>Status</th>
    <th>Ende</th>
    <th>Operationen</th>
</tr>"""


def verkaeufer_cell(lines):
    if not lines:
        return ""
    name = lines[0]
    rest = "<br>".join(lines[1:])
    return f'{name}<br><small class="text-muted">{rest}</small>'


def status_badge(status):
    if status == "freigeschaltet":
        return f'<span class="badge badge-success">{status}</span>'
    return f'<span class="badge badge-default">{status}</span>'


def ende_cell(value):
    # Stacked (date above save button) rather than side-by-side — an
    # inline input-group here got crushed down to a few px wide whenever
    # the table's other columns (esp. the two Aktionen buttons) needed the
    # space, making the date unreadable/unusable at normal viewport widths.
    return (
        f'<input type="text" class="form-control input-sm" value="{value}">'
        '<button type="button" class="btn btn-primary btn-xs btn-block" title="Speichern"><i class="fa fa-floppy-o"></i> Speichern</button>'
    )


def aktionen_cell():
    return (
        '<a href="#" class="btn btn-default btn-xs btn-block" title="Anzeige ausblenden"><i class="fa fa-eye-slash"></i> Ausblenden</a>'
        '<a href="#" class="btn btn-danger btn-xs btn-block" title="Anzeige löschen"><i class="fa fa-trash-o"></i> Löschen</a>'
    )


body_rows = []
for r in rows:
    cells = [
        f'<span class="badge badge-inverse">{r["region"]}</span>',
        verkaeufer_cell(r["verkaeufer_lines"]),
        "<br>".join(r["objektanschrift_lines"]),
        r["objekttyp"],
        r["objekttitel"],
        f'<a href="{r["objekt_href"]}" target="_blank" title="Exposé ansehen">{r["objekt_id"]}</a>',
        r["beginn"],
        status_badge(r["status"]),
        ende_cell(r["ende"]),
        aktionen_cell(),
    ]
    row_attr = f' style="{r["row_bg"]}"' if r["row_bg"] else ""
    body_rows.append(f"<tr{row_attr}>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-privatanzeigen">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>
"""

panel_body = f"""
<p class="text-muted">
    {len(rows)} of {total_real_rows} real Privatanzeigen shown (capped for a reviewable file).
    Some rows keep a real light-red highlight carried over from the live data — see build.py docstring.
</p>
{region_filter_bar}
{table_html}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("alle Privatanzeigen (alle Regionen)", panel_body)}</div></div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    var table = $('.data-table-privatanzeigen').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [8, 9], orderable: false },
            { targets: [8], width: '130px' },
            { targets: [9], width: '110px' }
        ]
    });

    $('#region-filter').on('change', function () {
        var value = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(0).search(value ? '^' + value + '$' : '', true, false).draw();
    });
});
</script>
"""

html = c.page_shell(
    title="Privatanzeigen - RI24 SEO",
    banner_html=c.prototype_banner(
        "Privatanzeigen (/adm/.../master/privatanzeige/)",
        f"{len(rows)} of {total_real_rows} real listings shown (capped for a reviewable file). "
        "Verkäufer contact details are real (private sellers) — see build.py docstring for the privacy note.",
    ),
    content_html=c.page_heading("Privatanzeigen (alle Regionen)", ["Home", "Privatanzeigen"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-privatanzeigen thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-privatanzeigen a:not(.btn) { color: #333333 !important; }\n"
        "  .data-table-privatanzeigen a:not(.btn):hover, .data-table-privatanzeigen a:not(.btn):focus { color: #A4C735 !important; }\n"
        "  .data-table-privatanzeigen .badge-success { background-color: #A4C735 !important; }\n"
        "  .data-table-privatanzeigen .badge-inverse { background-color: #333333 !important; }\n"
        "  .data-table-privatanzeigen .btn-primary { background-color: #A4C735 !important; border-color: #8fae2d !important; }\n"
        "  .data-table-privatanzeigen .btn-primary:hover { background-color: #8fae2d !important; }\n"
        "  .data-table-privatanzeigen td:nth-child(9) input { margin-bottom: 4px; min-width: 110px; }\n"
        "  .data-table-privatanzeigen td:nth-child(10) .btn:first-child { margin-bottom: 4px; }\n"
        "  .data-table-privatanzeigen thead th.sorting, .data-table-privatanzeigen thead th.sorting_asc, .data-table-privatanzeigen thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-privatanzeigen thead .sorting:after, .data-table-privatanzeigen thead .sorting_asc:after, .data-table-privatanzeigen thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_top_item="Privatanzeigen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
