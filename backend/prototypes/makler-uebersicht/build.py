"""Generates index.html: the consolidated 'Übersicht Makler' screen — a merge
of the current /adm/individuell/master/makler/list/ ("Übersicht Makler") and
/adm/individuell/master/makler/list-short/ ("Kurzliste Makler") screens, which
share ~9 of their columns. Rebuilt on the Inspinia theme (real DataTables) with
250 real makler rows captured from the live backend (the full lists have 2,636
real makler each — capped here for a reviewable file, same practice used for
the oversized dropdowns/tables in the other prototypes).

Security note: the source lists include a real plaintext "Passwort" column
per makler. That column is intentionally dropped in this consolidated view —
publishing ~250 live credential pairs into a static handoff file is not
something this prototype should do, and it isn't needed to review the layout.

"Objekte bearbeiten" and "Baufi anhand Immo-Ort" are also dropped — both are
now always-on defaults for every Makler going forward, no longer a
per-Makler configurable option (also dropped from Makler bearbeiten / neuen
Makler anlegen for the same reason).

With those columns gone there's room for a new "Aktionen" column — the real
"Zugangsdaten ausdrucken" / "als Makler anmelden" row-action icons, ported
the same way they were already added as labeled buttons on Makler
bearbeiten ("Zugangsdaten Download" / "Einloggen").
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

rows = json.loads((SURVEY / "26-makler-uebersicht-rows.json").read_text(encoding="utf-8"))
# Same real regioncode list used across the other prototypes' "Alle Regionen"
# filters — the live Übersicht Makler / Kurzliste Makler screens both have this
# exact filter embedded in the Portal column header.
region_opts = json.loads((SURVEY / "16-dashboard-nutzer-forms.json").read_text(encoding="utf-8"))[0]["selects"]["regioncode"]


def yn_label(value, true_val="ja"):
    value = (value or "").strip()
    if value == true_val:
        return '<span class="label label-info">ja</span>'
    if value in ("nein",):
        return '<span class="label">nein</span>'
    if value == "n.a.":
        return '<span class="label label-default">n.a.</span>'
    if value == "vorhanden":
        return '<span class="label label-info">vorhanden</span>'
    if value == "keine E-Mail":
        return '<span class="label label-default">keine E-Mail</span>'
    return value


def objekte_cell(raw):
    # raw looks like "6 | 2 | 0 | 2" (Wohnen | Gewerbe | Multi | Inaktiv)
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) != 4:
        return raw
    w, g, m, i = parts
    return (
        f'<span title="Wohnobjekte">W:{w}</span> '
        f'<span title="Gewerbeobjekte">G:{g}</span> '
        f'<span title="Multimakler-Objekte">M:{m}</span> '
        f'<span title="inaktive Objekte">I:{i}</span>'
    )


region_filter_options = "".join(
    f'<option value="{value}">{text}</option>' for value, text, _sel in region_opts
)
region_filter_bar = f"""
<div class="row m-b-md">
    <div class="col-sm-4">
        <label for="portal-filter">Region (Portal)</label>
        <select id="portal-filter" class="form-control input-sm">
            {region_filter_options}
        </select>
    </div>
</div>"""

thead = f"""
<tr>
    <th>Firmenname</th>
    <th>Portal</th>
    <th>Login</th>
    <th>Makler-ID</th>
    <th>Stufe</th>
    <th>E-Mail</th>
    <th title="Multimakler">Multilisting</th>
    <th title="Angebote zusammenfassen">Angebote zsgf.</th>
    <th>Webapp</th>
    <th>Anz. Objekte (W|G|M|I)</th>
    <th>Aktionen</th>
</tr>"""

# Ported from the "Zugangsdaten ausdrucken" / "als Makler anmelden" row-action
# icons on the real Übersicht Makler / Kurzliste Makler lists (same pair
# already added as real buttons on Makler bearbeiten) — labeled "Einloggen"
# here too, to avoid clashing with this table's own "Login" (login-name) column.
aktionen_cell = (
    '<a href="#" class="btn btn-default btn-xs btn-block" title="Zugangsdaten Download"><i class="fa fa-download"></i> Zugangsdaten</a>'
    '<a href="#" class="btn btn-success btn-xs btn-block" title="als Makler anmelden"><i class="fa fa-sign-in"></i> Einloggen</a>'
)

body_rows = []
for r in rows:
    makler_id_cell = r["makler_id"]
    if r["makler_id_badge"]:
        makler_id_cell += f' <span class="badge badge-info">{r["makler_id_badge"]}</span>'
    cells = [
        f'<a href="../makler-edit/index.html" title="Makler bearbeiten">{r["firmenname"]}</a>',
        f'<span class="badge badge-inverse">{r["portal"]}</span>',
        r["login"],
        makler_id_cell,
        f'<span class="badge badge-default">{r["stufe"]}</span>',
        yn_label(r["email"], true_val="vorhanden"),
        yn_label(r["multimakler"]),
        yn_label(r["angebote_zusammenfassen"]),
        yn_label(r["webapp"]),
        objekte_cell(r["anz_objekte"]),
        aktionen_cell,
    ]
    body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-makler">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>
"""

panel_body = f"""
<p class="text-muted">
    Consolidated from the current <strong>Übersicht Makler</strong> and <strong>Kurzliste Makler</strong>
    screens — those shared 9 of their columns (Firmenname, Portal, Login, Makler-ID, Stufe, Paket,
    Objekte bearbeiten, Multimakler) across two separate full-table pages. One real DataTable now covers
    both, with the union of their distinct columns; Paket, Passwort, Objekte bearbeiten and Baufilike
    extern are dropped (see note below).
</p>
{region_filter_bar}
{table_html}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("Übersicht Makler", panel_body)}</div></div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    var table = $('.data-table-makler').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            // Multimakler / Angebote zusammenfassen / Webapp only ever hold
            // "ja"/"nein"/"n.a." — no need for a wide column.
            { targets: [6, 7, 8], width: '70px' },
            { targets: [10], orderable: false, width: '130px' }
        ]
    });

    // Portal (region) filter — the real Übersicht Makler / Kurzliste Makler
    // screens have this embedded in the column header, but that widens the
    // Portal column; placed above the table instead to keep it narrow.
    $('#portal-filter').on('change', function () {
        var value = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(1).search(value ? '^' + value + '$' : '', true, false).draw();
    });
});
</script>
"""

html = c.page_shell(
    title="Übersicht Makler - RI24 SEO",
    banner_html=c.prototype_banner(
        "Makler &rarr; Übersicht Makler (merges /adm/.../makler/list/ + /adm/.../makler/list-short/)",
        "250 of 2,636 real makler shown (capped for a reviewable file); Paket and Passwort columns dropped — see build.py docstring. "
        "\"Objekte bearbeiten\" and \"Baufi anhand Immo-Ort\" are dropped too — both are now always-on defaults for every Makler going forward, no longer a per-Makler option.",
    ),
    content_html=c.page_heading("Übersicht Makler", ["Home", "Makler", "Übersicht Makler"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        # The base theme's table header (#495977 blue-gray) and .label-info/
        # .badge-info (#008495 teal) are leftovers from the old Hausfarbe —
        # this table's own accents are recolored to the green/gray CI here
        # rather than globally, since label-info/badge-info still needs to
        # read as a distinct category elsewhere (e.g. the Google Ads badges).
        "<style>\n"
        "  .data-table-makler thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-makler a:not(.btn) { color: #333333 !important; }\n"
        "  .data-table-makler a:not(.btn):hover, .data-table-makler a:not(.btn):focus { color: #A4C735 !important; }\n"
        "  .data-table-makler .label-info, .data-table-makler .badge-info { background-color: #A4C735 !important; color: #fff !important; }\n"
        "  .data-table-makler td:nth-child(7), .data-table-makler td:nth-child(8), .data-table-makler td:nth-child(9) { text-align: center; }\n"
        "  .data-table-makler td:nth-child(11) { white-space: nowrap; }\n"
        "  .data-table-makler td:nth-child(11) .btn { margin-bottom: 4px; }\n"
        "  .data-table-makler td:nth-child(11) .btn:last-child { margin-bottom: 0; }\n"
        "  .data-table-makler .btn-success { background-color: #A4C735 !important; border-color: #8fae2d !important; }\n"
        "  .data-table-makler .btn-success:hover { background-color: #8fae2d !important; }\n"
        # Taller rows — the Aktionen column now stacks two buttons per row, so
        # extra vertical breathing room reads better across every column too.
        "  .data-table-makler tbody td { padding-top: 16px !important; padding-bottom: 16px !important; vertical-align: middle !important; }\n"
        # DataTables' default sort icon reserves 30px on the RIGHT of every
        # sortable header (table.dataTable thead th.sorting { padding-right:
        # 30px }), which widens every column regardless of its own content.
        # Move it to the left, under the heading text, and reclaim that space.
        # Heading text, sort icon, and the data cells below all start flush
        # at the same 8px left edge (matches .table td's own padding-left).
        "  .data-table-makler thead th.sorting, .data-table-makler thead th.sorting_asc, .data-table-makler thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-makler thead .sorting:after, .data-table-makler thead .sorting_asc:after, .data-table-makler thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_makler_item="Übersicht Makler",
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
