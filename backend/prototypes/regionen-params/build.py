"""Generates index.html: the real 'Parameter individualisieren' screen
(/adm/individuell/regionen/edit/params/?regio=aai24), rebuilt on the
Inspinia theme with real field data captured for the example region
Aachen-Eifel (aai24) — 12 ibox panels across 3 groups (Startseite;
Baufinanzierung, Strom & Gas; Impressum), ~60 real fields total. Each
field's real "Platzhalter" (template variable) and "Beispiel / Hinweis"
text from the live page is kept as a note under the input, same role it
plays on the live site. Per-panel save action uses the floppy-disk icon
pattern already used on Makler bearbeiten, instead of the live page's
per-box plain "Speichern" button.

The two real file-upload panels (Portal-Logo hochladen / Portal-Logo für
Baufinanzierung hochladen) and the Öffnungszeiten textarea panel aren't
data-driven (file inputs + an empty textarea in the live data for this
region) — reproduced directly rather than templated from JSON.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "35-regionen-params-data.json").read_text(encoding="utf-8"))
PANELS = {p["title"]: p for p in data["panels"]}


def ibox_save(title, body_html):
    save_button = (
        '<div class="text-right m-t-md">'
        '<button type="button" class="btn btn-primary btn-sm" title="Speichern">'
        '<i class="fa fa-floppy-o"></i></button>'
        '</div>'
    )
    return c.ibox(title, body_html + save_button)


def render_field(f):
    label = f["label"]
    note_bits = []
    if f["platzhalter"]:
        note_bits.append(f'<code>{f["platzhalter"]}</code>')
    if f["hinweis"]:
        note_bits.append(f["hinweis"])
    note_html = f'<div><small class="text-muted">{" &mdash; ".join(note_bits)}</small></div>' if note_bits else ""

    if f["type"] == "checkbox":
        checked = " checked" if f["value"] else ""
        return f"""
        <div class="form-group row">
            <div class="col-sm-12"><label><input type="checkbox"{checked}> {label}</label></div>
        </div>"""

    if f["type"] == "select":
        opts = "".join(
            f'<option value="{v}"{" selected" if sel else ""}>{t}</option>' for v, t, sel in f["options"]
        )
        control = f'<select class="form-control">{opts}</select>'
    elif f["type"] == "textarea":
        control = f'<textarea class="form-control" rows="4">{f["value"]}</textarea>'
    elif f["type"] == "file":
        control = '<input type="file" class="form-control">'
    else:
        control = f'<input type="text" class="form-control" value="{f["value"]}">'

    return f"""
    <div class="form-group row">
        <label class="col-sm-4 control-label">{label}</label>
        <div class="col-sm-8">{control}{note_html}</div>
    </div>"""


def panel_body(title):
    fields = PANELS[title]["fields"]
    return "".join(render_field(f) for f in fields)


def logo_upload_body(preview_label):
    return f"""
    <div class="text-center m-b-md">
        <div style="display:inline-block;background:#f3f3f4;border:1px dashed #d7d7d7;padding:20px 30px;color:#999;">
            <i class="fa fa-image fa-2x"></i><br><small>{preview_label}</small>
        </div>
    </div>
    <input type="file" class="form-control">
    <p class="text-muted m-t-sm"><small>Bildgröße 60px (PNG/JPG verwenden)</small></p>
    """


oeffnungszeiten_body = '<textarea class="form-control" rows="6"></textarea>'

# --- Startseite -----------------------------------------------------------

startseite_row1 = f"""
<div class="row">
    <div class="col-lg-4">{ibox_save("Allgemein", panel_body("Allgemein"))}</div>
    <div class="col-lg-4">{ibox_save("wichtige Texte", panel_body("wichtige Texte"))}</div>
    <div class="col-lg-4">{ibox_save("Portal-Logo hochladen", logo_upload_body("aktuelles Portal-Logo"))}</div>
</div>"""

startseite_row2 = f"""
<div class="row">
    <div class="col-lg-4">{ibox_save("Portal-Logo für Baufinanzierung hochladen", logo_upload_body("aktuelles Baufi-Logo"))}</div>
    <div class="col-lg-4">{ibox_save("Jobangebote Drittportale", panel_body("Jobangebote Drittportale"))}</div>
</div>"""

# --- Baufinanzierung, Strom & Gas ------------------------------------------

baufi_row = f"""
<div class="row">
    <div class="col-lg-6">{ibox_save("Baufi Opener-Box (nur Mail,Share-Link und Tel. wird benutzt)", panel_body("Baufi Opener-Box (nur Mail,Share-Link und Tel. wird benutzt)"))}</div>
    <div class="col-lg-6">
        {ibox_save("Strom- und Gas-Links", panel_body("Strom- und Gas-Links"))}
        {ibox_save("Ansprechpartner Baufinanzierung", panel_body("Ansprechpartner Baufinanzierung"))}
        {ibox_save("Adresse Baufinanzierung (auf Baufi-Seiten)", panel_body("Adresse Baufinanzierung (auf Baufi-Seiten)"))}
    </div>
</div>"""

# --- Impressum --------------------------------------------------------------

impressum_row = f"""
<div class="row">
    <div class="col-lg-6">{ibox_save("Adresse", panel_body("Adresse"))}</div>
    <div class="col-lg-6">{ibox_save("Impressum", panel_body("Impressum"))}</div>
</div>
<div class="row">
    <div class="col-lg-12">{ibox_save("Öffnungszeiten", oeffnungszeiten_body)}</div>
</div>"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <h2>Startseite</h2>
    {startseite_row1}
    {startseite_row2}
    <h2>Baufinanzierung, Strom &amp; Gas</h2>
    {baufi_row}
    <h2>Impressum</h2>
    {impressum_row}
</div>
"""

html = c.page_shell(
    title="Regionalimmobilien24 - Aachen-Eifel - RI24 SEO",
    banner_html=c.prototype_banner(
        "Parameter individualisieren (/adm/.../regionen/edit/params/?regio=aai24)",
        "~60 real fields for the example region Aachen-Eifel (aai24), across 12 ibox panels. "
        "Each box's save action uses the floppy-disk icon pattern from Makler bearbeiten instead of the live page's per-box \"Speichern\" button.",
    ),
    content_html=c.page_heading("Regionalimmobilien24 - Aachen-Eifel", ["Home", "alle Regionen", "Parameter - Regionalimmobilien24 - Aachen-Eifel"]) + content,
    active_top_item="alle Regionen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
