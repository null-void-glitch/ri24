"""Generates index.html: the real 'Makler bearbeiten' edit screen
(/adm/individuell/master/makler/edit/?maklerid=r24srn74skk — opened by
clicking a realtor's name in the Übersicht Makler list), rebuilt on the
Inspinia theme using real field data captured from the live backend.

Security note: the real Login-Backend/FTP "Passwort" fields are genuinely
displayed in plaintext in the live UI (admins read/copy them to hand to the
makler). To show that exact field pattern without publishing this makler's
real working credential in a static handoff file, the password VALUES here
are fabricated placeholders — everything else (name, IDs, region, profile
text, checkbox/select state) is the real captured data.

"neue Objekte im ADM anlegen" and "Baufi anhand Immo-Ort" are dropped — both
are now always-on defaults for every Makler going forward, no longer a
per-Makler configurable option.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "27-makler-edit-data.json").read_text(encoding="utf-8"))
inputs = data["inputs"]
selects = data["selects"]
makler_text = data["makler_text_clean"]

FAKE_PASSWORD = "x7k2mQ9p"  # placeholder — see docstring


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


def ibox_save(title, body_html):
    """Like c.ibox(), but for panels holding editable data: adds a small
    floppy-disk save button bottom-right instead of relying on one general
    "Speichern" button for the whole page."""
    save_button = (
        '<div class="text-right m-t-md">'
        '<button type="button" class="btn btn-primary btn-sm" title="Speichern">'
        '<i class="fa fa-floppy-o"></i></button>'
        '</div>'
    )
    return c.ibox(title, body_html + save_button)


def field_row(label, control_html, note=""):
    note_html = f'<div><small class="text-muted">{note}</small></div>' if note else ""
    return f"""
    <div class="form-group row">
        <label class="col-sm-3 control-label">{label}</label>
        <div class="col-sm-9">{control_html}{note_html}</div>
    </div>"""


# --- Maklerdaten --------------------------------------------------------------

maklerdaten_body = "".join([
    field_row("Firmenname", f'<input type="text" class="form-control" value="{inputs["name"]["value"]}">'),
    field_row("Makler-ID", f'<input type="text" class="form-control" value="{inputs["makler_id"]["value"]}" disabled>'),
    field_row("Region", (
        '<span class="badge badge-inverse" style="font-size:13px;">brei24</span> '
        '<a href="#" class="btn btn-success btn-sm"><i class="fa fa-retweet"></i> umhängen</a>'
    )),
    field_row("Profil-Verzeichnis", (
        f'<div class="input-group"><input type="text" class="form-control" value="{inputs["profil_uri_name"]["value"]}" disabled>'
        '<span class="input-group-btn"><button class="btn btn-default" type="button" title="URL-Segment umschalten"><i class="fa fa-pencil"></i></button></span></div>'
    )),
    field_row("E-Mail bei keinen Immobilie", select_html("info_no_immo", selects["info_no_immo"])),
    field_row("Makler-Stufe/Modell", select_html("makler_stufe", selects["makler_stufe"])),
    field_row("Angebote zusammenfassen", checkbox("merge_offers")),
    field_row("für Gemeinschaftsgeschäft freischalten (Multimakler)", checkbox("multimakler") + ' <small class="text-muted">(nur Premium)</small>'),
    field_row("Freischaltung Immosolve", checkbox("kontakt_has_immosolve")),
])

# --- Makler-Profil -------------------------------------------------------------

makler_profil_body = "".join([
    field_row("E-Mail", f'<input type="text" class="form-control" placeholder="{inputs["maklerprofil_email"]["placeholder"]}">',
              "Anzeige auf Profil-Seite und für Info-Versand bei keinen aktiven Immobilien"),
    field_row("ext. Homepage", f'<input type="text" class="form-control" placeholder="{inputs["maklerprofil_homepage"]["placeholder"]}">',
              "URLS immer mit <code>http(s)://</code> beginnend"),
])

# --- Login Backend / FTP -------------------------------------------------------

def login_pair_body(login_id, login_val):
    return "".join([
        field_row("Login-Name" if "ftp" not in login_id else "Benutzername", (
            f'<div class="input-group"><input type="text" class="form-control" value="{login_val}">'
            '<span class="input-group-btn"><button class="btn btn-default" type="button" title="neu generieren"><i class="fa fa-refresh"></i></button></span></div>'
        )),
        field_row("Passwort", (
            f'<div class="input-group"><input type="text" class="form-control" value="{FAKE_PASSWORD}">'
            '<span class="input-group-btn"><button class="btn btn-default" type="button" title="neu generieren"><i class="fa fa-refresh"></i></button></span></div>'
        )),
    ])


login_backend_body = login_pair_body("login", inputs["login"]["value"])
login_ftp_body = login_pair_body("ftp_user", inputs["ftp_user"]["value"])

# --- techn. Ansprechpartner -----------------------------------------------------

ansprechpartner_body = field_row("Immobilienfinanzierung", select_html("ansprechpartner_baufi", selects["ansprechpartner_baufi"]))

# --- Webapp-Einstellungen -------------------------------------------------------

webapp_body = "".join([
    field_row("Webapp-Nutzung für Makler aktivieren", checkbox("use_webapp")),
    field_row("alternativer Name", f'<input type="text" class="form-control" placeholder="{inputs["webapp_titel"]["placeholder"]}">', "ansonsten Firmenname"),
])

main_column = f"""
{ibox_save("Maklerdaten", maklerdaten_body)}
{ibox_save("Makler-Profil", makler_profil_body)}
{ibox_save("Login Backend", login_backend_body)}
{ibox_save("Login FTP", login_ftp_body)}
{ibox_save("techn. Ansprechpartner", ansprechpartner_body)}
{ibox_save("Webapp-Einstellungen", webapp_body)}
"""

# --- Right sidebar: Aktionen / Makler Text / Makler löschen ------------------
# No general "Daten speichern" button — each editable box above/below saves
# itself via its own floppy-disk button (see ibox_save()).

makler_text_body = f'<textarea class="form-control" rows="10" readonly>{makler_text}</textarea>'
loeschen_body = '<button class="btn btn-danger btn-block">Löschen</button>'

# Ported from the row-action icons on Übersicht Makler / Kurzliste Makler
# ("als Makler anmelden" and "Zugangsdaten ausdrucken") — those only exist as
# small icon buttons in the list rows today; added here as real buttons so
# they're reachable directly from the edit screen too.
aktionen_body = """
<button class="btn btn-success btn-block"><i class="fa fa-sign-in"></i> Einloggen</button>
<button class="btn btn-default btn-block"><i class="fa fa-download"></i> Zugangsdaten Download</button>
"""

sidebar_column = f"""
{c.ibox("Aktionen", aktionen_body)}
{ibox_save("Makler Text", makler_text_body)}
{c.ibox("Makler löschen", loeschen_body)}
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
    title="Makler 1980 Real Estate GmbH bearbeiten - RI24 SEO",
    banner_html=c.prototype_banner(
        "Makler bearbeiten (/adm/.../makler/edit/?maklerid=r24srn74skk) — opened from a realtor's name in Übersicht Makler",
        "Login-Backend/FTP Passwort values are fabricated placeholders, not the real credential — see build.py docstring. Everything else is real captured data. \"Einloggen\" / \"Zugangsdaten Download\" are ported from the row-action icons on Übersicht Makler / Kurzliste Makler. The single \"Daten speichern\" button is replaced with a floppy-disk save action on each editable box. \"neue Objekte im ADM anlegen\" and \"Baufi anhand Immo-Ort\" are dropped — both are now always-on defaults for every Makler going forward, no longer a per-Makler option.",
    ),
    content_html=c.page_heading("Makler 1980 Real Estate GmbH bearbeiten", ["Home", "Konfiguration"]) + content,
    active_makler_item="Übersicht Makler",
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
