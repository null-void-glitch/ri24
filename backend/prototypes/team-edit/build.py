"""Generates index.html: the Team member edit form
(/adm/individuell/master/team/edit/?id=123), rebuilt on the Inspinia theme.

The original is a multi-section form where each ibox has its own Speichern
button (saved individually via AJAX/pitsafe). File-upload sections (Foto,
QR-Code, Logo) have separate POST forms.

Layout (mirrors the original Bootstrap 2 span grid → Bootstrap 4 col):
  Row 1: col-md-6 (persönliche Daten + EUROPACE + Partner-Status + Partner Links
                    + MobiBox) | col-md-6 (Unternehmensdaten + SMS)
  Row 2: 4 × col-md-3 (Foto | Foto Widget Pose | QR-Code | Logo Baufi)
  Row 3: col-md-9 (Webapp-Einstellungen) | col-md-3 (Logo Webapp)
  Row 4: col-md-4 (Teammitglied löschen)
  Row 5: col-md-12 (zugeordnete Makler)

Sample data comes from member id=123 as scraped (the customer-service
placeholder account). Real member names are used as-is since the edit form
is an internal admin screen.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent

PHOTO_URL = "https://bilder.regionalimmobilien24.de/get-file/img/images/system_ri24/team/v/200x200/max/b22a9339_customersupport.png"

FORM_STYLE = """
<style>
  .ibox .form-group { margin-bottom: 10px; }
  .ibox .col-form-label { font-weight: 600; font-size: 12px; padding-top: 7px; }
  .ibox .form-control { font-size: 13px; }
  .ibox-footer { padding: 10px 15px; background: #f7f7f7; border-top: 1px solid #e7eaec; }
  .upload-preview { border: 1px solid #e7eaec; padding: 8px; border-radius: 4px; background: #fafafa; text-align: center; }
  .upload-preview img { max-width: 100%; max-height: 180px; object-fit: contain; }
  .checkrow { padding: 4px 0; }
</style>
"""

def save_btn():
    return '<button type="button" class="btn btn-primary btn-sm"><i class="fa fa-floppy-o"></i> Speichern</button>'

def fg(label, control_html, col_label=4, col_input=8):
    return f"""
<div class="form-group row">
  <label class="col-sm-{col_label} col-form-label">{label}</label>
  <div class="col-sm-{col_input}">{control_html}</div>
</div>"""

def txt(name, value='', placeholder='', type_='text', extra=''):
    return f'<input type="{type_}" class="form-control form-control-sm" name="{name}" value="{value}" placeholder="{placeholder}" {extra}>'

def chk(name, label, value='1', checked=False):
    ch = ' checked' if checked else ''
    return f"""
<div class="checkrow">
  <label class="font-normal">
    <input type="checkbox" name="{name}" value="{value}"{ch}> {label}
  </label>
</div>"""

def upload_box(field_name, action_param, img_url=None, has_delete=False, delete_id=''):
    img_html = f'<img src="{img_url}" alt="" class="m-b-sm">' if img_url else '<p class="text-muted small">Kein Bild vorhanden</p>'
    delete_btn = f' <button type="button" id="{delete_id}" class="btn btn-danger btn-sm"><i class="fa fa-trash-o"></i> Löschen</button>' if has_delete else ''
    return f"""
<div class="upload-preview">{img_html}</div>
<div class="m-t-sm">
  <input type="file" name="{field_name}" class="form-control-file m-b-xs">
  <button type="button" class="btn btn-default btn-sm"><i class="fa fa-upload"></i> Hochladen</button>{delete_btn}
</div>"""


# ── persönliche Daten ────────────────────────────────────────────────────────
pers_fields = (
    fg("Region", '<select name="regioncode" class="form-control form-control-sm"><option value="">--- keine Region ---</option></select>') +
    fg("Vorname", txt("firstname")) +
    fg("Nachname", txt("lastname", "Immobilienanfragen")) +
    fg("Titel", txt("title")) +
    fg("Position", txt("position", "bei Fragen zu Immobilien wende Dich bitte direkt an den entsprechenden Anbieter aus dem Exposé.")) +
    fg("Bezeichnung im<br>Partner-Login-Bereich", txt("partnerlogin_label")) +
    fg("Telefon", txt("phone")) +
    fg("Fax", txt("fax")) +
    fg("Mobiltelefon", txt("mobile")) +
    fg("Whatsapp", txt("whatsapp")) +
    fg("E-Mail", txt("email", type_="email")) +
    fg("Calendly-Link",
       '<div class="input-group input-group-sm">'
       '<div class="input-group-prepend"><span class="input-group-text">https://calendly.com/</span></div>'
       '<input type="text" class="form-control form-control-sm" name="calendly" placeholder="ihr-name">'
       '<input type="text" class="form-control form-control-sm" name="calendly_zusatz" value="/60min" style="max-width:80px;">'
       '</div>') +
    fg("Website", txt("website")) +
    fg("Sortierung", txt("sorting", "-31", type_="number", extra='style="max-width:100px;"')) +
    '<hr class="m-t-xs m-b-xs">' +
    chk("is_baufi", "Teammitglied ist ein Baufinanzierer") +
    chk("is_finpartner", "Finanzierungspartner") +
    chk("show_on_mlp", 'auf der Landingpage <em>/immobilienportal-partner-werden/</em> (MLP) anzeigen')
)
pers_html = f'<form class="form-horizontal">{pers_fields}<div class="ibox-footer">{save_btn()}</div></form>'

# ── EUROPACE Partner IDs ─────────────────────────────────────────────────────
europace_html = f"""<form class="form-horizontal">
{fg("Qualitypool (Haupt-ID)", txt("europace_partner_id"))}
{fg("Forum", txt("europace_partner_id_forum"))}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── Partner-Status ───────────────────────────────────────────────────────────
partner_status_html = """
<div class="form-actions">
  <span class="badge badge-secondary m-r-sm">nicht gesetzt</span>
  <a href="../team-partner-edit/index.html" class="btn btn-success btn-sm"><i class="fa fa-pencil"></i> bearbeiten</a>
</div>"""

# ── Partner Links ────────────────────────────────────────────────────────────
partner_links_html = f"""<form class="form-horizontal">
{fg("finCrm", txt("link_uri_fincrm", "https://www.fincrm.de/login"))}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── MobiBox Login ────────────────────────────────────────────────────────────
mobibox_html = f"""<form class="form-horizontal">
{fg("Login", txt("texte_mobibox_login"))}
{fg("Passwort", '<input type="password" class="form-control form-control-sm" name="texte_mobibox_pw">')
}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── Unternehmensdaten ────────────────────────────────────────────────────────
unternehmens_html = f"""<form class="form-horizontal">
{fg("Firmenbezeichnung", txt("firmenbezeichnung"))}
{fg("Straße, Nr", txt("street"))}
{fg("PLZ / Ort",
    '<div class="row">'
    '<div class="col-4"><input type="text" class="form-control form-control-sm" name="zip" placeholder="PLZ"></div>'
    '<div class="col-8"><input type="text" class="form-control form-control-sm" name="city" placeholder="Ort"></div>'
    '</div>'
)}
{fg("Öffnungszeiten",
    '<textarea name="opening_hours" class="form-control form-control-sm" rows="4"></textarea>'
    '<small class="text-muted">HTML erlaubt</small>'
)}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── SMS Erinnerung ───────────────────────────────────────────────────────────
sms_html = f"""<form class="form-horizontal">
{chk("use_sms", "SMS bei BaufiLead versenden")}
{fg("Nummer für SMS", txt("phonenumber"))}
{fg("BaufiLead SMS",
    '<textarea name="sms_baufilead" class="form-control form-control-sm" rows="4">Ein neuer Finanzierungsinteressent wartet auf Dich. Nimm den Lead innerhalb von 30 Minuten an.</textarea>'
)}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── Webapp-Einstellungen ─────────────────────────────────────────────────────
webapp_html = f"""<form class="form-horizontal">
{chk("use_webapp", "persönliche Webapp-Nutzung für Finanzierer aktivieren")}
{fg("Titel", txt("webapp_titel", "Immobilienanfragen - Baufinanzierung"))}
{fg("Untertitel", txt("webapp_description", "BaufinanzierungPrime"))}
<div class="ibox-footer">{save_btn()}</div>
</form>"""

# ── Fotosections ─────────────────────────────────────────────────────────────
foto_html       = upload_box("image",             "image",              PHOTO_URL,  has_delete=True,  delete_id="delimage")
pose_html       = upload_box("image_widget_pose", "image_widget_pose",  None,       has_delete=False)
qr_html         = upload_box("qrcode",            "qrcode",             None,       has_delete=False)
logo_baufi_html = upload_box("logo_baufi",        "logo_baufi",         None,       has_delete=False)
logo_webapp_html= upload_box("webapp_logo",       "webapp_logo",        PHOTO_URL,  has_delete=True,  delete_id="delwebapp_logo")

# ── Löschen ──────────────────────────────────────────────────────────────────
loeschen_html = """
<p class="text-muted">Dieses Teammitglied und alle zugehörigen Daten unwiderruflich löschen.</p>
<a href="#" class="btn btn-danger"><i class="fa fa-trash-o"></i> Löschen</a>"""

# ── Makler ───────────────────────────────────────────────────────────────────
makler_html = '<p class="text-muted">Aktuell sind keine Makler diesem Berater zugeordnet.</p>'


def section(title, body, css_class=""):
    return f"""
<div class="ibox {css_class}">
  <div class="ibox-title"><h5>{title}</h5></div>
  <div class="ibox-content">{body}</div>
</div>"""


content = f"""
<div class="wrapper wrapper-content animated fadeInRight">

  <!-- Row 1 -->
  <div class="row">
    <div class="col-md-6">
      {section("persönliche Daten", pers_html)}
      {section("EUROPACE Partner IDs", europace_html)}
      {section("Partner-Status: nicht gesetzt", partner_status_html)}
      {section("Partner Links", partner_links_html)}
      {section("MobiBox Login", mobibox_html)}
    </div>
    <div class="col-md-6">
      {section("Unternehmensdaten", unternehmens_html)}
      {section("SMS Erinnerung", sms_html)}
    </div>
  </div>

  <!-- Row 2: Foto uploads -->
  <div class="row">
    <div class="col-md-3">{section("Foto", foto_html)}</div>
    <div class="col-md-3">{section("Foto Widget Pose", pose_html)}</div>
    <div class="col-md-3">{section("QR-Code", qr_html)}</div>
    <div class="col-md-3">{section("Logo Baufi", logo_baufi_html)}</div>
  </div>

  <!-- Row 3: Webapp -->
  <div class="row">
    <div class="col-md-9">{section("Webapp-Einstellungen", webapp_html)}</div>
    <div class="col-md-3">{section("Logo Webapp", logo_webapp_html)}</div>
  </div>

  <!-- Row 4: Löschen -->
  <div class="row">
    <div class="col-md-4">{section("Teammitglied löschen", loeschen_html)}</div>
  </div>

  <!-- Row 5: Makler -->
  <div class="row">
    <div class="col-md-12">{section("zugeordnete Makler (0)", makler_html)}</div>
  </div>

</div>"""

html = c.page_shell(
    title="Teammitglied bearbeiten - RI24 Admin",
    banner_html=c.prototype_banner(
        "Team › bearbeiten (/adm/.../master/team/edit/?id=123)",
        "Edit form for team member id=123. Each section has its own Speichern button "
        "(original uses per-section AJAX saves). File uploads are separate POST forms. "
        "Photo hotlinked from public RI24 CDN (200×200 max).",
    ),
    content_html=(
        c.page_heading("Teammitglied bearbeiten", ["Home", "Team", "bearbeiten"])
        + '<div style="margin:-10px 0 10px 20px;">'
          '<a href="../team/index.html" class="btn btn-default btn-sm">'
          '<i class="fa fa-arrow-left"></i> Zurück zur Liste</a></div>'
        + content
    ),
    extra_head=FORM_STYLE,
    active_top_item="Team",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
