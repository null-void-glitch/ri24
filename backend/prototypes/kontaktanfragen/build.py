"""Generates index.html: the real 'alle Kontaktanfragen' screen
(/adm/individuell/master/statistik/kontaktanfragen/), rebuilt on the
Inspinia theme (real DataTables) with all 50 real inquiry rows scraped
from the live backend.

The old CMS rendered each row as a large inline email card (entire HTML
email template embedded per row), making the page extremely tall and
slow. In this prototype the email body is replaced with a short plain-text
preview — much more usable in a table context.

The old 'Vermarktung/Nutzung' column contained broken icon glyphs that
did not render meaningfully even on the live site — omitted here.

The old 'Löschen' row action was commented-out on the live site — not
reproduced here (no actions were active).

Privacy note: "Anfragender" contact data (name, email, phone) are private
individuals making real estate enquiries — same internal-review stance as
Privatanzeigen (see that prototype's docstring).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "42-kontaktanfragen-rows.json").read_text(encoding="utf-8"))
rows = data["rows"]
total_real_rows = data["total_real_rows"]


def parse_kontakt(antwort_an):
    m_mail = re.search(r"Mail:\s*(\S+)", antwort_an)
    m_tel = re.search(r"Tel\.:\s*(\S+)", antwort_an)
    email = m_mail.group(1) if m_mail else ""
    tel = m_tel.group(1) if m_tel else ""
    return email, tel


thead = """
<tr>
    <th>Zeit</th>
    <th>Objekt</th>
    <th>Anfragender</th>
    <th>Kontakt</th>
    <th>Empfänger</th>
    <th>E-Mail Vorschau</th>
</tr>"""


def zeit_cell(r):
    return f'{r["zeitId"]}<br><small class="text-muted">{r["zeitDatum"]}</small>'


def objekt_cell(r):
    oid = r["objektId"]
    href = r["objektHref"]
    anschrift = r["objektanschrift"]
    link = f'<a href="{href}" target="_blank" title="Exposé ansehen">{oid}</a>' if href else oid
    if anschrift:
        return f'{link}<br><small class="text-muted">{anschrift}</small>'
    return link


def anfragender_cell(r):
    return r["name"]


def kontakt_cell(r):
    email, tel = parse_kontakt(r["antwortAn"])
    parts = []
    if email:
        parts.append(f'<a href="mailto:{email}">{email}</a>')
    if tel:
        parts.append(f'<small class="text-muted"><i class="fa fa-phone"></i> {tel}</small>')
    return "<br>".join(parts) if parts else "&mdash;"


def empfaenger_cell(r):
    e = r["empfaenger"]
    return f'<a href="mailto:{e}">{e}</a>' if e else "&mdash;"


def email_preview_cell(r):
    text = r["emailText"]
    # Strip the boilerplate prefix common to all rows
    text = re.sub(r"^Neue Anfrage zu Ihrem Objekt\s*", "", text).strip()
    preview = text[:160].rstrip()
    if len(text) > 160:
        preview += " …"
    return f'<small>{preview}</small>'


body_rows = []
for r in rows:
    cells = [
        zeit_cell(r),
        objekt_cell(r),
        anfragender_cell(r),
        kontakt_cell(r),
        empfaenger_cell(r),
        email_preview_cell(r),
    ]
    body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

table_html = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover data-table-kontaktanfragen">
        <thead>{thead}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>
"""

panel_body = f"""
<p class="text-muted">
    {total_real_rows} Kontaktanfragen (alle Regionen, aktuelle Seite der Live-Daten).
    Die E-Mail-Vorschau zeigt den Anfrage-Text als Kurztext; auf dem Live-System ist die vollständige E-Mail-HTML inline eingebettet.
</p>
{table_html}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("alle Kontaktanfragen", panel_body)}</div></div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    $('.data-table-kontaktanfragen').DataTable({
        order: [[0, 'desc']],
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [0], width: '110px' },
            { targets: [1], width: '130px' },
            { targets: [2], width: '130px' },
            { targets: [5], orderable: false }
        ]
    });
});
</script>
"""

html = c.page_shell(
    title="Kontaktanfragen - RI24 Admin",
    banner_html=c.prototype_banner(
        "Kontaktanfragen (/adm/.../master/statistik/kontaktanfragen/)",
        f"{total_real_rows} real rows (all pages). Vermarktung/Nutzung column omitted (broken icon glyphs on live site). "
        "Email body rendered as plain-text preview (live site embeds full HTML email template per row). "
        "Anfragender contact details are real private individuals — internal review only.",
    ),
    content_html=c.page_heading("Kontaktanfragen (alle Regionen)", ["Home", "Kontaktanfragen"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-kontaktanfragen thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-kontaktanfragen a:not(.btn) { color: #333333 !important; }\n"
        "  .data-table-kontaktanfragen a:not(.btn):hover, .data-table-kontaktanfragen a:not(.btn):focus { color: #A4C735 !important; }\n"
        "  .data-table-kontaktanfragen thead th.sorting, .data-table-kontaktanfragen thead th.sorting_asc, .data-table-kontaktanfragen thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-kontaktanfragen thead .sorting:after, .data-table-kontaktanfragen thead .sorting_asc:after, .data-table-kontaktanfragen thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "  .data-table-kontaktanfragen td { vertical-align: top; }\n"
        "  .data-table-kontaktanfragen td:last-child small { color: #555; line-height: 1.4; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_kontakt_item="alle Kontaktanfragen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
