"""Generates index.html: the real 'alle Objekte' screen
(/adm/individuell/master/immo/list/), rebuilt on the Inspinia theme (real
DataTables) with 100 real object rows captured from the live backend — the
live screen's default view already shows exactly this many rows per "page"
(it paginates through the full object-ID space in blocks of 100 via a large
grid of manually-clickable ID-range buttons, e.g. "1 - 100", "101 - 200", …
up to roughly 60,000). That legacy ID-range grid is replaced here by the
same real DataTables client-side search/sort/pagination used everywhere
else in this migration — the live "Suchen:" label above the table maps
directly onto DataTables' own (German) search box, so nothing is lost.

The real bulk "Alle wählen" checkbox + "Löschen" action is kept (wired up
client-side: the header checkbox toggles every row checkbox). Object
thumbnails hotlink to the live image CDN (bilder.regionalimmobilien24.de) —
these are small, already-public 75x75 crops, so viewing this file requires
network access to see them, same as any other page that embeds real image
URLs.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "32-objekte-rows.json").read_text(encoding="utf-8"))
rows = data["rows"]
total_real_rows = data["total_real_rows"]

thead = """
<tr>
    <th class="no-sort"><input type="checkbox" id="select-all" title="Alle wählen"></th>
    <th class="no-sort">Hauptbild</th>
    <th>Objekt-ID</th>
    <th>Ext.Objekt-Nr</th>
    <th>Makler</th>
    <th>Objektart</th>
    <th>Nutzungsart</th>
    <th>Vermarktung</th>
    <th>Adresse</th>
    <th>Preis</th>
    <th>Fläche</th>
    <th>Zimmer</th>
    <th>geändert</th>
</tr>"""

body_rows = []
for r in rows:
    adresse = "<br>".join(r["adresse_lines"])
    objektart = r["objektart"] or '<span class="text-muted">&mdash;</span>'
    cells = [
        f'<input type="checkbox" class="row-select" value="{r["checkbox_value"]}">',
        f'<a href="{r["thumb_href"]}" target="_blank" title="auf der Website ansehen"><img src="{r["thumb_src"]}" alt="" width="50" height="50"></a>',
        f'<a href="{r["objekt_href"]}" target="_blank" title="auf der Website ansehen">{r["objekt_id"]}</a>',
        r["ext_objekt_nr"] or '<span class="text-muted">&mdash;</span>',
        r["makler"],
        objektart,
        r["nutzungsart"],
        f'<span class="badge {"badge-success" if r["vermarktung"] == "mieten" else "badge-info"}">{r["vermarktung"]}</span>',
        adresse,
        r["preis"],
        r["flaeche"],
        r["zimmer"],
        r["geaendert"],
    ]
    body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-objekte">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>
<div class="m-t-sm">
    <button type="button" class="btn btn-danger btn-sm" id="delete-selected"><i class="fa fa-trash-o"></i> Auswahl löschen</button>
</div>
"""

panel_body = f"""
<p class="text-muted">
    {len(rows)} of {total_real_rows} real objects shown — this already is one full real
    page of the live "alle Objekte" screen (the live legacy ID-range pagination grid is
    replaced by the standard DataTable search/sort/pagination used across this migration).
</p>
{table_html}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("alle Objekte", panel_body)}</div></div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    $('.data-table-objekte').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [0, 1], orderable: false, width: '50px' },
            { targets: [9, 10, 11], className: 'text-right' }
        ]
    });

    $('#select-all').on('change', function () {
        $('.row-select').prop('checked', $(this).is(':checked'));
    });

    // Static prototype — the real bulk-delete posts to the backend; this
    // just clears the checkboxes to illustrate the interaction.
    $('#delete-selected').on('click', function () {
        $('.row-select, #select-all').prop('checked', false);
    });
});
</script>
"""

html = c.page_shell(
    title="Objekte bearbeiten - RI24 SEO",
    banner_html=c.prototype_banner(
        "alle Objekte (/adm/.../immo/list/)",
        f"{len(rows)} of {total_real_rows} real objects shown (already one full real page of the live screen — see build.py docstring). "
        "The legacy ID-range pagination grid is replaced by the standard DataTable search/sort/pagination.",
    ),
    content_html=c.page_heading("Objekte bearbeiten", ["Home", "Objekte"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-objekte thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-objekte a { color: #333333 !important; }\n"
        "  .data-table-objekte a:hover, .data-table-objekte a:focus { color: #A4C735 !important; }\n"
        "  .data-table-objekte .badge-success { background-color: #A4C735 !important; }\n"
        "  .data-table-objekte td img { border-radius: 3px; }\n"
        "  .data-table-objekte thead th.sorting, .data-table-objekte thead th.sorting_asc, .data-table-objekte thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-objekte thead .sorting:after, .data-table-objekte thead .sorting_asc:after, .data-table-objekte thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "  .data-table-objekte thead th.no-sort { padding-top: 12px !important; padding-bottom: 12px !important; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_objekte_item="alle Objekte",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
