"""Generates index.html: Whitelabel-Lizenz edit form
(/adm/individuell/master/whitelabel/edit/?id=265), rebuilt on Inspinia.

3-column layout (col-md-4 each, mirrors original span4):
  Left:   persönliche Daten (Region, Mandant, E-Mail, Sortierung, Name, Position,
                              Telefon, Fax, Mobil, Whatsapp, Website)
  Middle: Unternehmensdaten (Firmenbezeichnung, Straße/Nr, PLZ, Ort)
          + Europace (EUROPACE Partner ID)
  Right:  Backend-Login (Login, Passwort — real credential masked)
          + Whitelabel-Lizenz löschen

Sample values from id=265 (Tester Whitelabel Pitcom — a test/demo account).
Password from live backend is replaced with a placeholder.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent

STYLE = """
<style>
  .ibox .form-group { margin-bottom: 10px; }
  .ibox .col-form-label { font-weight: 600; font-size: 12px; padding-top: 7px; }
  .ibox .form-control { font-size: 13px; }
  .ibox-footer { padding: 10px 15px; background: #f7f7f7; border-top: 1px solid #e7eaec; }
</style>
"""

def save_btn():
    return '<button type="button" class="btn btn-primary btn-sm"><i class="fa fa-floppy-o"></i> Speichern</button>'

def fg(label, ctrl, col_l=4, col_r=8):
    return (
        f'<div class="form-group row">'
        f'<label class="col-sm-{col_l} col-form-label">{label}</label>'
        f'<div class="col-sm-{col_r}">{ctrl}</div></div>'
    )

def txt(name, value='', placeholder='', type_='text', extra=''):
    return f'<input type="{type_}" class="form-control form-control-sm" name="{name}" value="{value}" placeholder="{placeholder}" {extra}>'

def sel(name, options, selected_val=''):
    opts = ''.join(
        f'<option value="{v}"{" selected" if v == selected_val else ""}>{t}</option>'
        for v, t in options
    )
    return f'<select name="{name}" class="form-control form-control-sm">{opts}</select>'

def section(title, body):
    return (
        f'<div class="ibox">'
        f'<div class="ibox-title"><h5>{title}</h5></div>'
        f'<div class="ibox-content">{body}</div>'
        f'</div>'
    )

mandant_opts = [
    ('', '--- bitte wählen ---'),
    ('3', 'Qualitypool (activ)'),
    ('4', 'Finanzierungsassistent24 (activ)'),
    ('5', 'Regionalimmobilien24 - DEMO (activ)'),
]

# ── persönliche Daten ────────────────────────────────────────────────────────
pers_body = f"""<form class="form-horizontal">
{fg("Region", '<select name="regioncode" class="form-control form-control-sm"><option value="vi24" selected>Regionalimmobilien24 - Vogtland (vi24)</option></select>')}
{fg("Whitelabel-Mandant", sel("whitelabel_mid", mandant_opts, "4"))}
{fg("E-Mail<br><small class='text-muted'>(Login-Benutzername)</small>", txt("email", "66d30a28@pitcom.de", type_="email"))}
{fg("Sortierung", txt("sorting", "0", type_="number", extra='style="max-width:90px;"'))}
{fg("Vorname", txt("firstname", "Tester Whitelabel"))}
{fg("Nachname", txt("lastname", "Pitcom"))}
{fg("Titel", txt("title"))}
{fg("Position", txt("position", "Finanzierungsberater"))}
{fg("Telefon", txt("phone"))}
{fg("Fax", txt("fax"))}
{fg("Mobiltelefon", txt("mobile"))}
{fg("Whatsapp", txt("whatsapp"))}
{fg("Website", txt("website", "https://www.regionalimmobilien24.de"))}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── Unternehmensdaten ─────────────────────────────────────────────────────────
unternehmens_body = f"""<form class="form-horizontal">
{fg("Firmenbezeichnung", txt("firmenbezeichnung", "Regionalimmobilien24 GmbH"))}
{fg("Straße, Nr", txt("street", "Test-Straße"))}
{fg("PLZ / Ort",
    '<div class="row">'
    '<div class="col-5"><input type="text" class="form-control form-control-sm" name="zip" value="08523"></div>'
    '<div class="col-7"><input type="text" class="form-control form-control-sm" name="city" value="Plauen"></div>'
    '</div>'
)}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── Europace ──────────────────────────────────────────────────────────────────
europace_body = f"""<form class="form-horizontal">
{fg("EUROPACE Partner ID", txt("baufi_dir"))}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── Backend-Login ─────────────────────────────────────────────────────────────
login_body = f"""<form class="form-horizontal">
{fg("Login", txt("login", "66d30a28@pitcom.de"))}
{fg("Passwort", txt("pw", "••••••••••••••••••••••••••"))}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── Löschen ───────────────────────────────────────────────────────────────────
loeschen_body = """
<p class="text-muted">Diese Whitelabel-Lizenz und alle zugehörigen Daten unwiderruflich löschen.</p>
<a href="#" class="btn btn-danger"><i class="fa fa-trash-o"></i> Löschen</a>"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
  <div class="row">
    <div class="col-md-4">
      {section("persönliche Daten", pers_body)}
    </div>
    <div class="col-md-4">
      {section("Unternehmensdaten", unternehmens_body)}
      {section("Europace", europace_body)}
    </div>
    <div class="col-md-4">
      {section("Backend-Login Whitelabel", login_body)}
      {section("Whitelabel-Lizenz löschen", loeschen_body)}
    </div>
  </div>
</div>"""

html = c.page_shell(
    title="Whitelabel-Lizenz bearbeiten - RI24 Admin",
    banner_html=c.prototype_banner(
        "Whitelabel-Lizenz bearbeiten (/adm/.../master/whitelabel/edit/?id=265)",
        "Edit form for id=265 (Tester Whitelabel Pitcom — demo account). "
        "Backend-Login password replaced with placeholder (real credential masked). "
        "3-column layout: persönliche Daten | Unternehmensdaten + Europace | Backend-Login + Löschen.",
    ),
    content_html=(
        c.page_heading("Whitelabel-Lizenz bearbeiten", ["Home", "Whitelabel-Lizenzen", "bearbeiten"])
        + '<div style="margin:-10px 0 10px 20px;">'
          '<a href="../whitelabel-lizenzen/index.html" class="btn btn-default btn-sm">'
          '<i class="fa fa-arrow-left"></i> Zurück zur Liste</a></div>'
        + content
    ),
    extra_head=STYLE,
    active_top_item="Whitelabel-Lizenzen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
