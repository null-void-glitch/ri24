"""Generates index.html: the real 'Mailing-Konfiguration' screen
(/adm/individuell/regionen/edit/mailings/?regio=aai24), rebuilt on the
Inspinia theme (real DataTable) with all 22 real mail templates captured
for the example region Aachen-Eifel (aai24) — all 22 show "nicht
regionalisiert" for this region in the live data, which is reproduced as-is
(not a simplification on our part).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent

MAIL_TEMPLATES = [
    "Endkunde: Suchagent",
    "Endkunde: Suchagent Whitelabel",
    "Endkunde: Follow Up Mail Kaufobjekte Anfrage",
    "Endkunde: Follow Up Mail Kaufobjekte Anfrage Objektspezifisch",
    "Endkunde: Bestätigungsmail bei Kontaktanfragen - Version KAUF",
    "Endkunde: Bestätigungsmail bei Kontaktanfragen - Version MIET",
    "Endkunde: Bestätigungsmail bei Kontaktanfragen (Privatanzeigen) - Version KAUF",
    "Endkunde: Bestätigungsmail bei Kontaktanfragen (Privatanzeigen) - Version MIET",
    "Endkunde: Bestätigung Maklersuche / Bewertung",
    "Endkunde: Bestätigungsmail Einstellung Privatanzeige",
    "Makler: Kontaktanfragen an Makler",
    "Makler: Import-Fehler XML",
    "Makler: Import-Fehler XML-AnbieterNr",
    "Makler: Import-Fehler ZIP",
    "Makler: Import-Fehler Energieausweis",
    "Makler: Erinnerung 6 Monate keine Immobilien (Wiedergewinnungsmail)",
    "Makler: Erinnerung 14 Tage keine Immobilien (Hinweismail)",
    "Suchagent: Erinnerungs-Mail",
    "Finanzierer: Benachrichtigung bei Verifizierung eines Interessenten-Suchauftrages",
    "Finanzierer: Benachrichtigung bei Kontaktanfragen via BaufinanzierungPrime.de",
    "Vertrieb: Information über OptOut eines neuen Maklers für 6 Monate Inaktivität",
    "Vertrieb: Information über OptOut eines neuen Maklers für 14 Tage kein Immobilien",
]

thead = """
<tr>
    <th>Mail Template</th>
    <th>Regionalisierung</th>
    <th>Aktion</th>
</tr>"""

body_rows = []
for name in MAIL_TEMPLATES:
    cells = [
        name,
        '<span class="badge badge-default">nicht regionalisiert</span>',
        '<a href="#" class="btn btn-default btn-xs" title="Regionalisieren"><i class="fa fa-unlock-alt"></i> Regionalisieren</a>',
    ]
    body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-mailings">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>
"""

panel_body = f"""
<p class="text-muted">
    All {len(MAIL_TEMPLATES)} real mail templates shown for the example region Aachen-Eifel (aai24) —
    all 22 are "nicht regionalisiert" for this region in the live data.
</p>
{table_html}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("Mail-Templates", panel_body)}</div></div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    $('.data-table-mailings').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [1, 2], orderable: false, width: '160px' }
        ]
    });
});
</script>
"""

html = c.page_shell(
    title="Mailing-Konfiguration für AAI24 - RI24 SEO",
    banner_html=c.prototype_banner(
        "Mailing-Konfiguration (/adm/.../regionen/edit/mailings/?regio=aai24)",
        f"All {len(MAIL_TEMPLATES)} real mail templates shown for the example region Aachen-Eifel (aai24).",
    ),
    content_html=c.page_heading("Mailing-Konfiguration für AAI24", ["Home", "alle Regionen", "Mailings", "AAI24"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-mailings thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-mailings thead th.sorting, .data-table-mailings thead th.sorting_asc, .data-table-mailings thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-mailings thead .sorting:after, .data-table-mailings thead .sorting_asc:after, .data-table-mailings thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
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
