"""Generates index.html: the Partner-Status edit page
(/adm/individuell/master/team/edit/partner/?id=123), rebuilt on Inspinia.

Reached by clicking 'bearbeiten' in the Partner-Status ibox on the team-edit page.

Layout (mirrors original span6 grid → col-md-6):
  Row 1: Partner-Bereich | zugeordnete Ansprechpartner
  Row 2: Logos           | Dokumente
  Row 3: Videos          | Landingpages

Credentials scraped from the live page: password replaced with placeholder
(real plaintext credentials must never appear in prototype files).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent

BRONZE_IMG = "https://www.regionalimmobilien24.de/get-file/img/ressource/img/elements/franchise/v/h60/max/bronze.png.webp"

STYLE = """
<style>
  .ibox .form-group { margin-bottom: 10px; }
  .ibox .col-form-label { font-weight: 600; font-size: 12px; padding-top: 7px; }
  .ibox .form-control { font-size: 13px; }
  .ibox-footer { padding: 10px 15px; background: #f7f7f7; border-top: 1px solid #e7eaec; }
  .zentral-badge { color: #aaa; font-size: 11px; font-style: italic; }
  table.partner-table thead th { background: #333 !important; color: #fff; font-size: 12px; }
  table.partner-table td { vertical-align: middle; font-size: 13px; }
</style>
"""

def save_btn():
    return '<button type="button" class="btn btn-primary btn-sm"><i class="fa fa-floppy-o"></i> Speichern</button>'

def fg(label, ctrl, col_l=4, col_r=8):
    return (f'<div class="form-group row">'
            f'<label class="col-sm-{col_l} col-form-label">{label}</label>'
            f'<div class="col-sm-{col_r}">{ctrl}</div></div>')

def sel(name, options, selected_val=''):
    opts = ''.join(
        f'<option value="{v}"{" selected" if v == selected_val else ""}>{t}</option>'
        for v, t in options
    )
    return f'<select name="{name}" class="form-control form-control-sm">{opts}</select>'

def txt(name, value='', placeholder='', type_='text'):
    return f'<input type="{type_}" class="form-control form-control-sm" name="{name}" value="{value}" placeholder="{placeholder}">'

def section(title, body):
    return (f'<div class="ibox"><div class="ibox-title"><h5>{title}</h5></div>'
            f'<div class="ibox-content">{body}</div></div>')

def zentral_table(headers, rows, add_row_html=''):
    ths = ''.join(f'<th>{h}</th>' for h in headers)
    trs = ''
    for row in rows:
        tds = ''.join(f'<td>{cell}</td>' for cell in row)
        trs += f'<tr>{tds}</tr>'
    if add_row_html:
        trs += add_row_html
    return (f'<div class="table-responsive"><table class="table table-bordered table-hover partner-table">'
            f'<thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>')


# ── Partner-Bereich ──────────────────────────────────────────────────────────
stufe_opts = [
    ('', '--- bitte wählen ---'),
    ('2', 'Bronze'), ('3', 'Silber'), ('4', 'Gold'), ('5', 'Platin'), ('6', 'Platin+'),
]
status_opts = [('1', 'aktiv'), ('2', 'blockiert (zu viele falsche Logins)'), ('0', 'inaktiv / gesperrt')]
provision_opts = [('1', 'anzeigen'), ('0', 'nicht anzeigen')]

partner_body = f"""<form class="form-horizontal">
{fg("Partner-Stufe",
    f'<div class="d-flex align-items-center gap-2">'
    f'{sel("partnerstufe", stufe_opts, "2")}'
    f'<img src="{BRONZE_IMG}" alt="Bronze" title="Status: bronze" style="height:40px;margin-left:8px;">'
    f'</div>'
)}
{fg("Login", txt("email", placeholder="E-Mail Adresse"))}
{fg("Passwort", txt("pw", value="••••••••••"))}
{fg("Login-Status", sel("is_status", status_opts, "1"))}
{fg("Provision", sel("show_provision", provision_opts, "1"))}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── zugeordnete Ansprechpartner ──────────────────────────────────────────────
ansp_opts_sample = [
    ('', '--- bitte wählen ---'),
    ('63', 'Technikhotline'), ('62', 'Vertragshotline'),
    ('93', 'Stefanie Rupprecht'), ('1', 'Lars Rupprecht (VI24)'),
    ('56', 'Stefanie Rupprecht'), ('64', 'Alexander Stumm'),
    ('94', 'Sindy Popp'), ('4', 'Philipp Steppohn (VI24)'),
]
ansp_body = f"""
{zentral_table(
    ['Ansprechpartner', ''],
    [],  # no assigned contacts for id=123
)}
<form class="form-horizontal m-t-sm">
{fg("Ansprechpartner hinzufügen", sel("aid", ansp_opts_sample))}
<div class="ibox-footer">
  <button type="button" class="btn btn-success btn-sm"><i class="fa fa-plus"></i> Hinzufügen</button>
</div>
</form>"""

# ── Logos ────────────────────────────────────────────────────────────────────
logo_rows = [
    ['0', 'Doppellogo vom Header der Region', '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'Baufilogo',                         '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'a6005d8d_prime-einzeln.png',        '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'Finanzierungspartner Siegel',        '<span class="zentral-badge">(zentral)</span>'],
]
logos_add = (
    '<tr class="warning">'
    '<td style="width:70px;"><input type="number" class="form-control input-sm" name="sorting_logo" value="0" style="width:60px;"></td>'
    '<td><input type="file" name="image" class="form-control-file"></td>'
    '<td style="width:100px;"><button type="button" class="btn btn-success btn-sm"><i class="fa fa-upload"></i> Hochladen</button></td>'
    '</tr>'
)
logos_body = zentral_table(['Sort.', 'Datei', ''], logo_rows, logos_add)

# ── Dokumente ────────────────────────────────────────────────────────────────
doc_rows = [
    ['0', 'Beilagenblatt zum Immobilienkauf',    '<span class="zentral-badge">(zentral)</span>'],
    ['1', 'Finanzierungszertifikat',             '<span class="zentral-badge">(zentral)</span>'],
    ['2', 'Objektzertifikat',                    '<span class="zentral-badge">(zentral)</span>'],
    ['3', 'Auftrag Immobilienanbieter',          '<span class="zentral-badge">(zentral)</span>'],
    ['4', 'Anleitung Kalenderverbindung',        '<span class="zentral-badge">(zentral)</span>'],
    ['5', 'Einrichtung Mail Account',            '<span class="zentral-badge">(zentral)</span>'],
    ['6', 'Anleitung Europace einrichten',       '<span class="zentral-badge">(zentral)</span>'],
    ['7', 'Anleitung Finanzierungs-Widgets',     '<span class="zentral-badge">(zentral)</span>'],
]
docs_add = (
    '<tr class="warning">'
    '<td style="width:70px;"><input type="number" class="form-control input-sm" name="sorting_doc" value="0" style="width:60px;"></td>'
    '<td><input type="file" name="docfile" class="form-control-file"></td>'
    '<td style="width:100px;"><button type="button" class="btn btn-success btn-sm"><i class="fa fa-upload"></i> Hochladen</button></td>'
    '</tr>'
)
docs_body = zentral_table(['Sort.', 'Datei', ''], doc_rows, docs_add)

# ── Videos ──────────────────────────────────────────────────────────────────
video_rows = [
    ['0', 'Vorstellung Baufinanzierung<br><small class="text-muted">https://blog.regionalimmobilien24.de/dateien/RI24-Baufi-cut.mp4</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'Forwarddarlehen / Umschuldung<br><small class="text-muted">https://blog.regionalimmobilien24.de/dateien/Ri24-Forwarddarlehen-cut.mp4</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'Immobilienbewertung<br><small class="text-muted">https://blog.regionalimmobilien24.de/dateien/Immobilienbewertung-cut.mp4</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'Vorstellung Finanzierungsassistent<br><small class="text-muted">https://blog.regionalimmobilien24.de/dateien/Screencast-Finanzierungsassistent-Makler-komprimiert.m4v</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'Vorteile für Sichtbarkeitspartner<br><small class="text-muted">https://blog.regionalimmobilien24.de/dateien/Vorteile-Sichtbarkeitspartner.mp4</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'Portalvorstellung für Makler<br><small class="text-muted">https://blog.regionalimmobilien24.de/dateien/Portalvorstellung-Makler.mp4</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['0', 'Erklärvideo Empfehlungsmanagement<br><small class="text-muted">https://blog.regionalimmobilien24.de/dateien/Empfehlungsmanagment.mp4</small>', '<span class="zentral-badge">(zentral)</span>'],
]
videos_add = (
    '<tr class="warning">'
    '<td style="width:70px;"><input type="number" class="form-control input-sm" name="sorting_doc_videos" value="0" style="width:60px;"></td>'
    '<td><input type="text" class="form-control input-sm" name="label_doc_videos" placeholder="Bezeichnung">'
    '<input type="text" class="form-control input-sm m-t-xs" name="file_doc_videos" placeholder="URL"></td>'
    '<td style="width:100px;"><button type="button" class="btn btn-success btn-sm"><i class="fa fa-plus"></i> Hinzufügen</button></td>'
    '</tr>'
)
videos_body = zentral_table(['Sort.', 'URL', ''], video_rows, videos_add)

# ── Landingpages ─────────────────────────────────────────────────────────────
lp_rows = [
    ['10', 'Beraterlandingpage<br><small class="text-muted">https://www.regionalimmobilien24.de/#region#/baufinanzierung/#baufidir#/</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['20', 'Beraterlandingpage "Klickstrecke"<br><small class="text-muted">https://www.regionalimmobilien24.de/#region#/baufinanzierung/#baufidir#/angebot/</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['30', 'Beraterlandingpage "Suchauftrag"<br><small class="text-muted">https://www.regionalimmobilien24.de/#region#/baufinanzierung/#baufidir#/suchauftrag/</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['40', 'Beraterlandingpage "Unterlagenupload"<br><small class="text-muted">https://www.regionalimmobilien24.de/#region#/baufinanzierung/#baufidir#/unterlagen/</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['50', 'Beraterlandingpage "Umschuldung"<br><small class="text-muted">https://www.regionalimmobilien24.de/#region#/baufinanzierung/#baufidir#/umschuldung/</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['60', 'Beraterlandingpage "Immobilie bewerten"<br><small class="text-muted">https://www.regionalimmobilien24.de/#region#/baufinanzierung/#baufidir#/immobilienbewertung/</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['70', 'Beraterlandingpage "energetische Sanierung"<br><small class="text-muted">https://www.regionalimmobilien24.de/#region#/baufinanzierung/#baufidir#/energetische-sanierung/</small>', '<span class="zentral-badge">(zentral)</span>'],
    ['80', 'Makleranbindung<br><small class="text-muted">http://www.regionalimmobilien24.de/immobilienportal-partner-werden/</small>', '<span class="zentral-badge">(zentral)</span>'],
]
lp_add = (
    '<tr class="warning">'
    '<td style="width:70px;"><input type="number" class="form-control input-sm" name="sorting_doc_links" value="0" style="width:60px;"></td>'
    '<td><input type="text" class="form-control input-sm" name="label_doc_links" placeholder="Bezeichnung">'
    '<input type="text" class="form-control input-sm m-t-xs" name="file_doc_links" placeholder="URL"></td>'
    '<td style="width:100px;"><button type="button" class="btn btn-success btn-sm"><i class="fa fa-plus"></i> Hinzufügen</button></td>'
    '</tr>'
)
lp_body = zentral_table(['Sort.', 'URL', ''], lp_rows, lp_add)


content = f"""
<div class="wrapper wrapper-content animated fadeInRight">

  <!-- Row 1 -->
  <div class="row">
    <div class="col-md-6">{section("Partner-Bereich", partner_body)}</div>
    <div class="col-md-6">{section("zugeordnete Ansprechpartner", ansp_body)}</div>
  </div>

  <!-- Row 2 -->
  <div class="row">
    <div class="col-md-6">{section("Logos", logos_body)}</div>
    <div class="col-md-6">{section("Dokumente", docs_body)}</div>
  </div>

  <!-- Row 3 -->
  <div class="row">
    <div class="col-md-6">{section("Videos", videos_body)}</div>
    <div class="col-md-6">{section("Landingpages", lp_body)}</div>
  </div>

</div>"""

html = c.page_shell(
    title="Partner-Status bearbeiten - RI24 Admin",
    banner_html=c.prototype_banner(
        "Partner-Status (/adm/.../master/team/edit/partner/?id=123)",
        "Reached via Partner-Status › bearbeiten on the team-edit page. "
        "Login password replaced with placeholder (real credential masked). "
        "Table rows marked (zentral) are centrally managed; add-rows allow new entries.",
    ),
    content_html=(
        c.page_heading("Partner-Status bearbeiten", ["Home", "Team", "bearbeiten", "Partner-Status"])
        + '<div style="margin:-10px 0 10px 20px;">'
          '<a href="../team-edit/index.html" class="btn btn-default btn-sm">'
          '<i class="fa fa-arrow-left"></i> Zurück</a></div>'
        + content
    ),
    extra_head=STYLE,
    active_top_item="Team",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
