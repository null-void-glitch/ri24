"""Generates index.html: the 'E-Mail Liste' screen under Kontaktanfragen
(/adm/individuell/master/mails/list/), rebuilt on the Inspinia theme.

The original backend splits the list into two separate tables:
  - Kaufinteressenten (tagged 'data-table-kauf' on live site)
  - Mietinteressenten (separate table, empty for the current month Oct 2026)

Filters added (matching the live CSV export URL parameters y/m/t):
  - Region dropdown (global, filters both tables)
  - Monat dropdown (global, last 12 months; static prototype — no live data
    behind other months)

CSV Export buttons replicate the live URL pattern:
  .../mails/list/csv/?y=YYYY&m=MM&t=kauf|miete
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "43-mails-list-rows.json").read_text(encoding="utf-8"))
rows_kauf = data["rows"]          # all 50 scraped rows are Kaufinteressenten
total_kauf = data["total_real_rows"]
rows_miet = []                    # Mietinteressenten: 0 for current month (matches live)
total_miet = 0

# --- Region filter (same source as other prototypes) ---
region_opts = json.loads((SURVEY / "16-dashboard-nutzer-forms.json").read_text(encoding="utf-8"))[0]["selects"]["regioncode"]
region_filter_options = "".join(
    f'<option value="{value}">{text}</option>' for value, text, _sel in region_opts
)

# --- Month filter: last 12 months ---
today = date(2026, 10, 6)
months = []
d = today.replace(day=1)
for _ in range(12):
    months.append(d)
    d = (d - timedelta(days=1)).replace(day=1)
current_month_label = today.strftime("%-m/%Y")
month_options = "".join(
    f'<option value="{m.strftime("%-m/%Y")}"{" selected" if m.year == today.year and m.month == today.month else ""}>{m.strftime("%-m/%Y")}</option>'
    for m in months
)

filter_bar = f"""
<div class="row m-b-md">
    <div class="col-sm-4">
        <label for="region-filter">Region</label>
        <select id="region-filter" class="form-control input-sm">
            {region_filter_options}
        </select>
    </div>
    <div class="col-sm-3">
        <label for="month-filter">Monat</label>
        <select id="month-filter" class="form-control input-sm">
            {month_options}
        </select>
    </div>
</div>"""

# --- Table building ---
thead = """
<tr>
    <th>Region</th>
    <th>Newsletter</th>
    <th>Kontaktdatum</th>
    <th>Name</th>
    <th>Vorname</th>
    <th>E-Mail</th>
    <th>Telefon</th>
    <th>Objekte</th>
    <th>Blacklist</th>
</tr>"""


def blacklist_cell(val):
    if val and val.strip():
        return f'<span class="badge badge-danger">{val}</span>'
    return '<a href="#" class="btn btn-default btn-xs" title="Zur Blacklist hinzufügen"><i class="fa fa-ban"></i> hinzufügen</a>'


def objekte_cell(val):
    if not val:
        return "&mdash;"
    return f'<a href="https://www.regionalimmobilien24.de/immobilien/expose/?id={val}" target="_blank">{val}</a>'


def email_cell(val):
    if not val:
        return "&mdash;"
    return f'<a href="mailto:{val}">{val}</a>'


def build_rows(rows):
    out = []
    for r in rows:
        region, newsletter, kontaktdatum, name, vorname, email, telefon, objekte, blacklist = (
            r + [""] * 9
        )[:9]
        cells = [
            f'<span class="badge badge-inverse">{region}</span>' if region else "",
            newsletter,
            kontaktdatum,
            name,
            vorname,
            email_cell(email),
            telefon,
            objekte_cell(objekte),
            blacklist_cell(blacklist),
        ]
        out.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    return "".join(out)


def table_section(css_class, rows):
    body = build_rows(rows)
    if not body:
        body = f'<tr><td colspan="9" class="text-center text-muted">Keine Einträge für diesen Monat.</td></tr>'
    return f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover {css_class}">
        <thead>{thead}</thead>
        <tbody>{body}</tbody>
    </table>
</div>"""


def csv_button(t):
    return f'<a href="#" class="btn btn-sm btn-default" title="CSV-Export für {t}"><i class="fa fa-download"></i> CSV-Export</a>'


kauf_panel_body = f"""
<p class="text-muted">{total_kauf} Kaufinteressenten (aktueller Monat, alle Seiten zusammengeführt).</p>
{table_section("data-table-kauf", rows_kauf)}"""

miet_panel_body = f"""
<p class="text-muted">{total_miet} Mietinteressenten (aktueller Monat — entspricht dem Live-Stand).</p>
{table_section("data-table-miet", rows_miet)}"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">
        <div class="ibox">
            <div class="ibox-title">
                <h5>E-Mail Liste</h5>
                <div class="ibox-tools">
                    <a class="collapse-link"><i class="fa fa-chevron-up"></i></a>
                    <a class="close-link"><i class="fa fa-times"></i></a>
                </div>
            </div>
            <div class="ibox-content">
                {filter_bar}
            </div>
        </div>
    </div></div>
    <div class="row">
        <div class="col-lg-12">
            <div class="ibox">
                <div class="ibox-title">
                    <h5>Kaufinteressenten</h5>
                    <div class="ibox-tools">
                        {csv_button("Kaufinteressenten")}
                        <a class="collapse-link m-l-sm"><i class="fa fa-chevron-up"></i></a>
                        <a class="close-link"><i class="fa fa-times"></i></a>
                    </div>
                </div>
                <div class="ibox-content">{kauf_panel_body}</div>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">
            <div class="ibox">
                <div class="ibox-title">
                    <h5>Mietinteressenten</h5>
                    <div class="ibox-tools">
                        {csv_button("Mietinteressenten")}
                        <a class="collapse-link m-l-sm"><i class="fa fa-chevron-up"></i></a>
                        <a class="close-link"><i class="fa fa-times"></i></a>
                    </div>
                </div>
                <div class="ibox-content">{miet_panel_body}</div>
            </div>
        </div>
    </div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    var kaufTable = $('.data-table-kauf').DataTable({
        order: [[2, 'desc']],
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [0], width: '70px' },
            { targets: [1, 2], width: '100px' },
            { targets: [8], width: '130px', orderable: false }
        ]
    });

    var mietTable = $('.data-table-miet').DataTable({
        order: [[2, 'desc']],
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [0], width: '70px' },
            { targets: [1, 2], width: '100px' },
            { targets: [8], width: '130px', orderable: false }
        ]
    });

    // Region filter — applies to both tables via column(0) regex search
    $('#region-filter').on('change', function () {
        var val = $.fn.dataTable.util.escapeRegex($(this).val());
        var search = val ? '^' + val + '$' : '';
        kaufTable.column(0).search(search, true, false).draw();
        mietTable.column(0).search(search, true, false).draw();
    });

    // Month filter — static prototype, no live data behind other months
    $('#month-filter').on('change', function () {
        console.log('Month filter changed to', $(this).val(), '— static prototype, real data only for 10/2026.');
    });
});
</script>
"""

html = c.page_shell(
    title="E-Mail Liste - Kontaktanfragen - RI24 Admin",
    banner_html=c.prototype_banner(
        "E-Mail Liste (/adm/.../master/mails/list/)",
        f"{total_kauf} Kaufinteressenten, {total_miet} Mietinteressenten (Oct 2026, matches live). "
        "Region filter applies to both tables. Month filter is UI-only (static prototype). "
        "Contact data are real private individuals — internal review only.",
    ),
    content_html=c.page_heading("E-Mail Liste", ["Home", "Kontaktanfragen", "E-Mail Liste"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-kauf thead th, .data-table-miet thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-kauf a:not(.btn), .data-table-miet a:not(.btn) { color: #333333 !important; }\n"
        "  .data-table-kauf a:not(.btn):hover, .data-table-miet a:not(.btn):hover { color: #A4C735 !important; }\n"
        "  .data-table-kauf .badge-inverse, .data-table-miet .badge-inverse { background-color: #333333 !important; }\n"
        "  .data-table-kauf .badge-danger, .data-table-miet .badge-danger { background-color: #c0392b !important; }\n"
        "  .data-table-kauf thead th.sorting, .data-table-kauf thead th.sorting_asc, .data-table-kauf thead th.sorting_desc,\n"
        "  .data-table-miet thead th.sorting, .data-table-miet thead th.sorting_asc, .data-table-miet thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-kauf thead .sorting:after, .data-table-kauf thead .sorting_asc:after, .data-table-kauf thead .sorting_desc:after,\n"
        "  .data-table-miet thead .sorting:after, .data-table-miet thead .sorting_asc:after, .data-table-miet thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "  .ibox-tools .btn { margin-top: -2px; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_kontakt_item="E-Mail Liste",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
