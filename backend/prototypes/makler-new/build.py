"""Generates index.html: the real 'neuen Makler anlegen' create-form screen
(/adm/individuell/master/makler/new/), rebuilt on the Inspinia theme using
real field data/defaults captured from the live backend.

Unlike Makler bearbeiten, this is a single atomic create action (not several
independently-editable sections), so it keeps the one central "Daten
speichern" button rather than the per-box floppy-save pattern used on the
edit screen. "Angebotspaket" is dropped here too, for the same
now-obsolete reason it was dropped from Übersicht Makler / Makler bearbeiten.

"neue Objekte im ADM anlegen" and "Baufi anhand Immo-Ort" are also dropped —
both are now always-on defaults for every Makler going forward, no longer a
per-Makler configurable option.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "29-makler-new-data.json").read_text(encoding="utf-8"))
inputs = data["inputs"]
selects = data["selects"]

FAKE_PASSWORD = "b3n8Wq5t"  # placeholder, not a real generated credential — see makler-edit/build.py


def select_html(id_, options, name=None):
    name = name or id_
    opts = "".join(
        f'<option value="{o["value"]}"{" selected" if o["selected"] else ""}>{o["text"]}</option>'
        for o in options
    )
    return f'<select id="{id_}" name="{name}" class="form-control">{opts}</select>'


def checkbox(id_, help_text=""):
    checked = " checked" if inputs[id_]["checked"] else ""
    help_html = f' <i class="fa fa-question-circle text-muted" title="{help_text}"></i>' if help_text else ""
    return f'<input type="checkbox" id="{id_}"{checked}>{help_html}'


def field_row(label, control_html, note=""):
    note_html = f'<div><small class="text-muted">{note}</small></div>' if note else ""
    return f"""
    <div class="form-group row">
        <label class="col-sm-3 control-label">{label}</label>
        <div class="col-sm-9">{control_html}{note_html}</div>
    </div>"""


# --- Maklerdaten --------------------------------------------------------------

maklerdaten_body = "".join([
    field_row("Firmenname", f'<input type="text" class="form-control" placeholder="{inputs["name"]["placeholder"]}">'),
    field_row("Region", select_html("regioncode", selects["regioncode"])),
    field_row("E-Mail", f'<input type="text" class="form-control" placeholder="{inputs["email"]["placeholder"]}">'),
    field_row("Makler-ID", f'<input type="text" class="form-control" value="{inputs["makler_id"]["value"]}" disabled>'),
    field_row("Makler-Stufe/Modell", select_html("makler_stufe", selects["makler_stufe"])),
    field_row("Angebote zusammenfassen", checkbox("merge_offers")),
    field_row("für Gemeinschaftsgeschäft freischalten (Multimakler)", checkbox("multimakler") + ' <small class="text-muted">(nur Premium)</small>'),
    field_row("Freischaltung Immosolve", checkbox("kontakt_has_immosolve")),
])

# --- Login Backend / FTP -------------------------------------------------------

def login_pair_body(login_val, name_label="Login-Name"):
    return "".join([
        field_row(name_label, (
            f'<div class="input-group"><input type="text" class="form-control" value="{login_val}">'
            '<span class="input-group-btn"><button class="btn btn-default" type="button" title="neu generieren"><i class="fa fa-refresh"></i></button></span></div>'
        )),
        field_row("Passwort", (
            f'<div class="input-group"><input type="text" class="form-control" value="{FAKE_PASSWORD}">'
            '<span class="input-group-btn"><button class="btn btn-default" type="button" title="neu generieren"><i class="fa fa-refresh"></i></button></span></div>'
        )),
    ])


login_backend_body = login_pair_body(inputs["login"]["value"])
login_ftp_body = login_pair_body(inputs["ftp_user"]["value"], name_label="Benutzername")

main_column = f"""
{c.ibox("Maklerdaten", maklerdaten_body)}
{c.ibox("Login Backend", login_backend_body)}
{c.ibox("Login FTP", login_ftp_body)}
"""

speichern_body = '<button class="btn btn-primary btn-block">Speichern</button><p class="text-muted m-t-sm">* Pflichtfeld</p>'

sidebar_column = f"""
{c.ibox("Daten speichern", speichern_body)}
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-8">{main_column}</div>
        <div class="col-lg-4">{sidebar_column}</div>
    </div>
</div>
"""

html = c.page_shell(
    title="neuen Makler anlegen - RI24 SEO",
    banner_html=c.prototype_banner(
        "neuen Makler anlegen (/adm/.../makler/new/)",
        "Login-Backend/FTP Passwort value is a fabricated placeholder, not a real generated credential. "
        "Angebotspaket is dropped here too (obsolete, same reasoning as Übersicht Makler / Makler bearbeiten). "
        "\"neue Objekte im ADM anlegen\" and \"Baufi anhand Immo-Ort\" are dropped as well — both are now "
        "always-on defaults for every Makler going forward, no longer a per-Makler option.",
    ),
    content_html=c.page_heading("neuen Makler anlegen", ["Home", "Konfiguration"]) + content,
    active_makler_item="neuen Makler anlegen",
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
