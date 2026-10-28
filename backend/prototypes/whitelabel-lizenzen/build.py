"""Generates index.html: Whitelabel-Lizenzen list
(/adm/individuell/master/whitelabel/list/), rebuilt on Inspinia.

44 real rows. Columns: Portal, Partner-Bereich (Mandant), Sortierung,
Bild (50×50 CDN hotlink), Name/Position, Telefon/E-Mail, Operationen.

Portal filter via DataTables column(0) regex, same pattern as Team.
Partner-Bereich filter via column(1).
Photos: public CDN crops at bilder.regionalimmobilien24.de/get-file/.../partner/...
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE   = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data  = json.loads((SURVEY / "48-whitelabel-rows.json").read_text(encoding="utf-8"))
rows  = data["rows"]
total = data["total_real_rows"]

# Portal filter options
portals = sorted(set(r["portal"] for r in rows if r["portal"]))
portal_opts = '<option value="">Alle Portale</option>' + "".join(
    f'<option value="{p}">{p}</option>' for p in portals
)

# Partner (Mandant) filter options
partners = sorted(set(r["partner"] for r in rows if r["partner"]))
partner_opts = '<option value="">Alle Mandanten</option>' + "".join(
    f'<option value="{p}">{p}</option>' for p in partners
)

filter_bar = f"""
<div class="row m-b-md">
    <div class="col-sm-3">
        <label for="portal-filter">Portal</label>
        <select id="portal-filter" class="form-control input-sm">{portal_opts}</select>
    </div>
    <div class="col-sm-3">
        <label for="partner-filter">Mandant</label>
        <select id="partner-filter" class="form-control input-sm">{partner_opts}</select>
    </div>
</div>"""

thead = """<tr>
    <th>Portal</th>
    <th>Mandant</th>
    <th>Sort.</th>
    <th>Bild</th>
    <th>Name / Position</th>
    <th>Telefon / E-Mail</th>
    <th>Operationen</th>
</tr>"""

KONTAKT_RE = re.compile(
    r'Telefon:\s*(?P<tel>[^\n]*?)\s*Mobil:\s*(?P<mob>[^\n]*?)\s*E-Mail:\s*(?P<mail>[^\n]*)',
    re.S
)


def bild_cell(src):
    if not src:
        return '<i class="fa fa-user-circle fa-2x text-muted"></i>'
    return f'<img src="{src}" width="50" height="50" style="border-radius:4px;object-fit:cover;" alt="">'


def name_cell(raw):
    # raw = "Vorname Nachname Position" — no reliable separator
    # show as-is; first line vs rest not available from scraped text
    return raw if raw else ""


def kontakt_cell(raw):
    m = KONTAKT_RE.search(raw)
    if not m:
        return raw
    tel  = m.group("tel").strip()
    mob  = m.group("mob").strip()
    mail = m.group("mail").strip()
    parts = []
    if tel:
        parts.append(f'<i class="fa fa-phone text-muted"></i> {tel}')
    if mob:
        parts.append(f'<i class="fa fa-mobile text-muted"></i> {mob}')
    if mail:
        parts.append(f'<a href="mailto:{mail}" class="text-muted"><i class="fa fa-envelope-o"></i> {mail}</a>')
    return "<br>".join(parts) if parts else "&mdash;"


def portal_cell(p):
    return f'<span class="badge badge-inverse" style="background:#333;font-size:10px;">{p}</span>' if p else ""


def partner_cell(p):
    colors = {
        "Finanzierungsassistent24": "#A4C735",
        "Qualitypool":              "#5b9bd5",
    }
    bg = colors.get(p, "#888")
    return f'<span class="badge" style="background:{bg};font-size:10px;white-space:normal;">{p}</span>' if p else ""


def ops_cell(row_id):
    return (
        f'<a href="../whitelabel-lizenzen-edit/index.html" class="btn btn-default btn-xs" title="bearbeiten"><i class="fa fa-pencil"></i></a> '
        f'<a href="#" class="btn btn-default btn-xs" title="Freigabe"><i class="fa fa-unlock-alt"></i></a> '
        f'<a href="#" class="btn btn-danger btn-xs" title="löschen"><i class="fa fa-trash-o"></i></a>'
    )


tbody_rows = []
for r in rows:
    cells = [
        portal_cell(r["portal"]),
        partner_cell(r["partner"]),
        r["sortierung"],
        bild_cell(r["bild_src"]),
        name_cell(r["name_pos"]),
        kontakt_cell(r["kontakt"]),
        ops_cell(r.get("id", "")),
    ]
    tbody_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-wl">
        <thead>{thead}</thead>
        <tbody>{''.join(tbody_rows)}</tbody>
    </table>
</div>"""

new_btn = '<a href="#" class="btn btn-primary btn-sm"><i class="fa fa-plus"></i> Neue Whitelabel-Lizenz</a>'

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
            {c.ibox(
                f'alle Whitelabel-Lizenzen (alle Regionen) &nbsp;'
                f'<span class="badge" style="background:#5b9bd5">{total}</span>',
                panel_body
            )}
        </div>
    </div>
</div>"""

SCRIPT = """
<script>
$(function () {
    var table = $('.data-table-wl').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [0], width: '65px' },
            { targets: [1], width: '120px' },
            { targets: [2], width: '50px' },
            { targets: [3], width: '60px', orderable: false },
            { targets: [6], width: '110px', orderable: false }
        ]
    });

    $('#portal-filter').on('change', function () {
        var val = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(0).search(val ? '^' + val + '$' : '', true, false).draw();
    });

    $('#partner-filter').on('change', function () {
        var val = $.fn.dataTable.util.escapeRegex($(this).val());
        table.column(1).search(val ? '^' + val + '$' : '', true, false).draw();
    });
});
</script>
"""

html = c.page_shell(
    title="Whitelabel-Lizenzen - RI24 Admin",
    banner_html=c.prototype_banner(
        "Whitelabel-Lizenzen (/adm/.../master/whitelabel/list/)",
        f"All {total} real whitelabel licence rows. Photos hotlinked from public RI24 CDN. "
        "Portal and Mandant dropdowns filter via DataTables column regex.",
    ),
    content_html=c.page_heading("Whitelabel-Lizenzen", ["Home", "Whitelabel-Lizenzen"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-wl thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-wl a:not(.btn) { color: #333333 !important; }\n"
        "  .data-table-wl a:not(.btn):hover { color: #A4C735 !important; }\n"
        "  .data-table-wl td { vertical-align: middle; }\n"
        "  .data-table-wl thead th.sorting, .data-table-wl thead th.sorting_asc, .data-table-wl thead th.sorting_desc { padding: 12px 8px 22px !important; }\n"
        "  .data-table-wl thead .sorting:after, .data-table-wl thead .sorting_asc:after, .data-table-wl thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_top_item="Whitelabel-Lizenzen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
