"""Generates index.html: the real 'Anfragen' screen
(/adm/individuell/master/makler/anfragen/), rebuilt on the Inspinia theme
(real DataTables) with 250 real makler rows captured from the live backend
(the full list has 2,638 real makler — capped here for a reviewable file,
same practice used for the Übersicht Makler table).

The live screen's "Anfragen" group header spans 5 real sub-columns (Klicks
auf Telefonnummer / Mietanfragen / Kaufanfragen / unbekannte / Gesamt) via a
3-row nested <thead> (rowspan/colspan). That's flattened to a single header
row here for a robust DataTables setup — the column meaning is unchanged,
just not nested. The month picker (a real dropdown in the live header,
currently on 9/2026) is ported as its own filter above the table, alongside
the Region filter — but since this is a static capture, switching the month
does not re-fetch different real numbers; only 9/2026 data is real here.

"Paket" is dropped (obsolete, per the same decision already made for
Übersicht Makler / Makler bearbeiten).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "30-makler-anfragen-rows.json").read_text(encoding="utf-8"))
rows = data["rows"]
# The scraped monthLinks list mixes in the (unrelated) region-filter link
# labels from the same page — keep only real mm/yyyy month entries.
MONTH_RE = re.compile(r"^\d{1,2}/\d{4}$")
month_options = sorted(
    (m for m in data["monthLinks"] if MONTH_RE.match(m)),
    key=lambda m: (int(m.split("/")[1]), int(m.split("/")[0])),
    reverse=True,
)
current_month = "9/2026"

region_opts = json.loads((SURVEY / "16-dashboard-nutzer-forms.json").read_text(encoding="utf-8"))[0]["selects"]["regioncode"]

region_filter_options = "".join(
    f'<option value="{value}">{text}</option>' for value, text, _sel in region_opts
)
month_filter_options = "".join(
    f'<option value="{m}"{" selected" if m == current_month else ""}>{m}</option>'
    for m in [current_month] + [m for m in month_options if m != current_month]
)

filter_bar = f"""
<div class="row m-b-md">
    <div class="col-sm-4">
        <label for="portal-filter">Region (Portal)</label>
        <select id="portal-filter" class="form-control input-sm">
            {region_filter_options}
        </select>
    </div>
    <div class="col-sm-4">
        <label for="month-filter">Monat</label>
        <select id="month-filter" class="form-control input-sm">
            {month_filter_options}
        </select>
    </div>
</div>
"""

# Real totals across all 2,638 makler for the current month (from the live
# header's per-column badges) — the 250-row sample below won't sum to these.
totals_bar = f"""
<div class="row m-b-md">
    <div class="col-sm-2"><h2 class="no-margins">1.751</h2><small>Gesamt ({current_month})</small></div>
    <div class="col-sm-10">
        <div class="row">
            <div class="col-sm-3 text-center"><span class="label label-default">Klicks auf Telefonnummer: 182</span></div>
            <div class="col-sm-3 text-center"><span class="label label-default">Mietanfragen: 935</span></div>
            <div class="col-sm-3 text-center"><span class="label label-default">Kaufanfragen: 816</span></div>
            <div class="col-sm-3 text-center"><span class="label label-default">unbekannte: 0</span></div>
        </div>
    </div>
</div>
"""

thead = """
<tr>
    <th>Firmenname</th>
    <th>Portal</th>
    <th>Makler-ID</th>
    <th>Stufe</th>
    <th>Klicks auf Telefonnummer</th>
    <th>Mietanfragen</th>
    <th>Kaufanfragen</th>
    <th>unbekannte</th>
    <th>Gesamt</th>
</tr>"""

body_rows = []
for r in rows:
    makler_id_cell = r["makler_id"]
    if r["makler_id_badge"]:
        makler_id_cell += f' <span class="badge badge-info">{r["makler_id_badge"]}</span>'
    cells = [
        f'<a href="#" title="Makler bearbeiten">{r["firmenname"]}</a>',
        f'<span class="badge badge-inverse">{r["portal"]}</span>',
        makler_id_cell,
        f'<span class="badge badge-default">{r["stufe"]}</span>',
        r["klicks_telefon"],
        r["mietanfragen"],
        r["kaufanfragen"],
        r["unbekannte"],
        f'<strong>{r["gesamt"]}</strong>',
    ]
    body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-anfragen">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>
"""

panel_body = f"""
<p class="text-muted">
    Anfragen je Makler für den gewählten Monat — Klicks auf Telefonnummer, Mietanfragen,
    Kaufanfragen, unbekannte und Gesamt (die live Seite zeigt diese 5 Spalten unter einer
    gemeinsamen "Anfragen"-Kopfzeile). Paket (obsolet) wurde entfernt.
</p>
{totals_bar}
{filter_bar}
{table_html}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("Anfragen", panel_body)}</div></div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    var table = $('.data-table-anfragen').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [4, 5, 6, 7, 8], width: '80px' }
        ]
    });

    $('#portal-filter').on('change', function () {
        var value = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(1).search(value ? '^' + value + '$' : '', true, false).draw();
    });

    // The month filter is real (matches the live dropdown's options), but this
    // static capture only has real row data for the current month (9/2026) —
    // switching it here does not re-fetch different numbers.
    $('#month-filter').on('change', function () {
        console.log('Month filter changed to', $(this).val(), '— static prototype, no live data behind other months.');
    });
});
</script>
"""

html = c.page_shell(
    title="Anfragen - RI24 SEO",
    banner_html=c.prototype_banner(
        "Makler &rarr; Anfragen (/adm/.../makler/anfragen/)",
        "250 of 2,638 real makler shown (capped for a reviewable file); Paket column dropped (obsolete). "
        "Month filter is real, but only 9/2026 has real row data behind it in this static capture.",
    ),
    content_html=c.page_heading("Anfragen", ["Home", "Makler", "Anfragen"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-anfragen thead th { background-color: #333333 !important; text-align: left !important; }\n"
        "  .data-table-anfragen a { color: #333333 !important; }\n"
        "  .data-table-anfragen a:hover, .data-table-anfragen a:focus { color: #A4C735 !important; }\n"
        "  .data-table-anfragen .badge-info { background-color: #A4C735 !important; color: #fff !important; }\n"
        "  .data-table-anfragen td:nth-child(5), .data-table-anfragen td:nth-child(6), .data-table-anfragen td:nth-child(7), .data-table-anfragen td:nth-child(8), .data-table-anfragen td:nth-child(9) { text-align: center; }\n"
        "  .data-table-anfragen thead th.sorting, .data-table-anfragen thead th.sorting_asc, .data-table-anfragen thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-anfragen thead .sorting:after, .data-table-anfragen thead .sorting_asc:after, .data-table-anfragen thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_makler_item="Anfragen",
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
