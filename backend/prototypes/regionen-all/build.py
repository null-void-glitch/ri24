"""Generates index.html: ALL 6 'alle Regionen' screens combined into one
self-contained file, so the sidebar sub-menu (and the main list's row
action buttons) can be clicked straight through without leaving the file —
unlike the separate prototypes/regionen*/ folders, which link to sibling
index.html files on disk.

Same real data as the separate prototypes (see their build.py docstrings
for full sourcing notes): all 105 real region rows on the list, and the
full real capture for the example region Aachen-Eifel (aai24) on the other
5 screens. Only the navigation wiring differs here — plain-link hrefs are
replaced with a small show/hide script that swaps which section is visible
and keeps the sidebar's active-item highlight in sync, since there's only
one HTML document to navigate within.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

regionen_data = json.loads((SURVEY / "34-regionen-rows.json").read_text(encoding="utf-8"))
params_data = json.loads((SURVEY / "35-regionen-params-data.json").read_text(encoding="utf-8"))
werbebanner_data = json.loads((SURVEY / "38-regionen-werbebanner-data.json").read_text(encoding="utf-8"))
seiten_data = json.loads((SURVEY / "39-regionen-seiten-data.json").read_text(encoding="utf-8"))
seite_bearbeiten_data = json.loads((SURVEY / "40-regionen-page-edit-data.json").read_text(encoding="utf-8"))
seo_baufinanzierung_data = json.loads((SURVEY / "41-seo-baufinanzierung-data.json").read_text(encoding="utf-8"))

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

# PAGE_IDS maps the internal section id -> the exact sidebar label text (so
# the generic sidebar HTML from _common.sidebar() can be rewired below).
PAGE_IDS = [
    ("list", "alle Regionen"),
    ("params", "Parameter individualisieren"),
    ("geodaten", "Geodaten anpassen"),
    ("mailings", "Mailings anpassen"),
    ("werbebanner", "Immo Werbebanner & PopUp anpassen"),
    ("seiten", "Seiten individualisieren"),
]


def nav_link(page_id, label, active=False):
    """A sidebar sub-item that swaps the visible section instead of
    following an href to a sibling file."""
    cls = ' class="active"' if active else ""
    return (
        f'<li{cls} id="regionen-nav-{page_id}">'
        f'<a href="#" data-page="{page_id}" onclick="showRegionPage(\'{page_id}\');return false;">{label}</a></li>'
    )


def row_action_link(page_id, label, title):
    return f'<a href="#" class="btn btn-default btn-xs" data-page="{page_id}" onclick="showRegionPage(\'{page_id}\');return false;" title="{title}">{label}</a>'


# --- Section 1: alle Regionen (list) ---------------------------------------

def build_list_section():
    rows = regionen_data["rows"]
    total_real_rows = regionen_data["total_real_rows"]

    thead = """
    <tr>
        <th>Code</th>
        <th>Verzeichnis</th>
        <th>Name</th>
        <th>aktiv</th>
        <th>individuell</th>
        <th>Parameter</th>
        <th>Geodaten</th>
        <th>Mailings</th>
        <th>Werbebanner &amp; PopUp</th>
        <th>Seiten</th>
    </tr>"""

    def bool_checkbox(value):
        if value is None:
            return ""
        checked = " checked" if value else ""
        return f'<input type="checkbox" disabled{checked}>'

    body_rows = []
    for r in rows:
        if r["is_vatermodell"]:
            row_html = (
                "<tr>"
                "<td></td>"
                f'<td><strong>{r["name"]}</strong></td>'
                "<td></td><td></td><td></td>"
                f'<td>{row_action_link("params", "anpassen", "Parameter anpassen")}</td>'
                "<td></td>"
                f'<td>{row_action_link("mailings", "anpassen", "Mailings anpassen")}</td>'
                f'<td>{row_action_link("werbebanner", "anpassen", "Werbung anpassen")}</td>'
                f'<td>{row_action_link("seiten", "anpassen", "Seiten anpassen")}</td>'
                "</tr>"
            )
            body_rows.append(row_html)
            continue

        cells = [
            f'<span class="badge badge-inverse">{r["code"]}</span>',
            f'<a href="https://www.regionalimmobilien24.de{r["verzeichnis"]}" target="_blank">{r["verzeichnis"]}</a>',
            r["name"],
            bool_checkbox(r["aktiv"]),
            bool_checkbox(r["individuell"]),
            row_action_link("params", "anpassen", "Parameter anpassen"),
            row_action_link("geodaten", "anpassen", "Geodaten anpassen"),
            row_action_link("mailings", "anpassen", "Mailings anpassen"),
            row_action_link("werbebanner", "anpassen", "Werbung anpassen"),
            row_action_link("seiten", "anpassen", "Seiten anpassen"),
        ]
        body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

    table_html = f"""
    <div class="table-responsive">
        <table class="table table-striped table-bordered table-hover data-table-regionen">
            <thead>{thead}</thead>
            <tbody>{''.join(body_rows)}</tbody>
        </table>
    </div>"""

    panel_body = f"""
    <p class="text-muted">
        All {total_real_rows} real rows shown (104 regions + the "Seiten des Vatermodells" template row).
        Every row's action buttons jump to the same 5 example sections (captured in full for one
        region, Aachen-Eifel / aai24) regardless of which region's row they're on.
    </p>
    {table_html}"""

    heading = c.page_heading("alle Regionen", ["Home", "alle Regionen"])
    content = f"""
    <div class="wrapper wrapper-content animated fadeInRight">
        <div class="row"><div class="col-lg-12">{c.ibox("alle Regionen", panel_body)}</div></div>
    </div>"""
    return heading + content


# --- Section 2: Parameter individualisieren --------------------------------

def build_params_section():
    panels = {p["title"]: p for p in params_data["panels"]}

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
        return "".join(render_field(f) for f in panels[title]["fields"])

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

    baufi_row = f"""
    <div class="row">
        <div class="col-lg-6">{ibox_save("Baufi Opener-Box (nur Mail,Share-Link und Tel. wird benutzt)", panel_body("Baufi Opener-Box (nur Mail,Share-Link und Tel. wird benutzt)"))}</div>
        <div class="col-lg-6">
            {ibox_save("Strom- und Gas-Links", panel_body("Strom- und Gas-Links"))}
            {ibox_save("Ansprechpartner Baufinanzierung", panel_body("Ansprechpartner Baufinanzierung"))}
            {ibox_save("Adresse Baufinanzierung (auf Baufi-Seiten)", panel_body("Adresse Baufinanzierung (auf Baufi-Seiten)"))}
        </div>
    </div>"""

    impressum_row = f"""
    <div class="row">
        <div class="col-lg-6">{ibox_save("Adresse", panel_body("Adresse"))}</div>
        <div class="col-lg-6">{ibox_save("Impressum", panel_body("Impressum"))}</div>
    </div>
    <div class="row">
        <div class="col-lg-12">{ibox_save("Öffnungszeiten", oeffnungszeiten_body)}</div>
    </div>"""

    heading = c.page_heading("Regionalimmobilien24 - Aachen-Eifel", ["Home", "alle Regionen", "Parameter - Regionalimmobilien24 - Aachen-Eifel"])
    content = f"""
    <div class="wrapper wrapper-content animated fadeInRight">
        <h2>Startseite</h2>
        {startseite_row1}
        {startseite_row2}
        <h2>Baufinanzierung, Strom &amp; Gas</h2>
        {baufi_row}
        <h2>Impressum</h2>
        {impressum_row}
    </div>"""
    return heading + content


# --- Section 3: Geodaten anpassen ------------------------------------------

def build_geodaten_section():
    zoom_select = "".join(
        f'<option value="{z}"{" selected" if z == "10" else ""}>{z}</option>' for z in (str(z) for z in range(4, 18))
    )

    def field_row(label, control_html, required=True):
        star = ' <span class="text-danger">*</span>' if required else ""
        return f"""
        <div class="form-group row">
            <label class="col-sm-4 control-label">{label}{star}</label>
            <div class="col-sm-8">{control_html}</div>
        </div>"""

    mittelpunkt_body = "".join([
        field_row("lat", '<input type="text" class="form-control" value="50.75">'),
        field_row("lon", '<input type="text" class="form-control" value="6.46">'),
        field_row("ZOOM-Stufe", f'<select class="form-control">{zoom_select}</select>'),
    ])

    bbox_body = "".join([
        field_row("lat (min)", '<input type="text" class="form-control" value="50.3361">'),
        field_row("lat (max)", '<input type="text" class="form-control" value="50.9795">'),
        field_row("lon (min)", '<input type="text" class="form-control" value="5.9749">'),
        field_row("lon (max)", '<input type="text" class="form-control" value="6.9081">'),
        (
            '<div class="text-center m-t-md" style="background:#f3f3f4;border:1px dashed #d7d7d7;padding:30px 10px;color:#999;">'
            '<i class="fa fa-map-o fa-2x"></i><br><small>Kartenvorschau (Platzhalter) — Bounding Box lat/lon</small>'
            '</div>'
        ),
    ])

    speichern_body = '<button class="btn btn-primary btn-block">Speichern</button><p class="text-muted m-t-sm">* Pflichtfeld</p>'

    heading = c.page_heading("Geodaten für Aachen-Eifelimmobilien24 (AAI24) bearbeiten", ["Home", "alle Regionen", "AAI24", "Geodaten bearbeiten"])
    content = f"""
    <div class="wrapper wrapper-content animated fadeInRight">
        <div class="row">
            <div class="col-lg-4">{c.ibox("Mittelpunkt / Zoomstufe", mittelpunkt_body)}</div>
            <div class="col-lg-4">{c.ibox("Bounding Box", bbox_body)}</div>
            <div class="col-lg-4">{c.ibox("Daten speichern", speichern_body)}</div>
        </div>
    </div>"""
    return heading + content


# --- Section 4: Mailings anpassen ------------------------------------------

def build_mailings_section():
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
    </div>"""

    panel_body = f"""
    <p class="text-muted">
        All {len(MAIL_TEMPLATES)} real mail templates shown for the example region Aachen-Eifel (aai24) —
        all 22 are "nicht regionalisiert" for this region in the live data.
    </p>
    {table_html}"""

    heading = c.page_heading("Mailing-Konfiguration für AAI24", ["Home", "alle Regionen", "Mailings", "AAI24"])
    content = f"""
    <div class="wrapper wrapper-content animated fadeInRight">
        <div class="row"><div class="col-lg-12">{c.ibox("Mail-Templates", panel_body)}</div></div>
    </div>"""
    return heading + content


# --- Section 5: Immo Werbebanner & PopUp anpassen ---------------------------

def build_werbebanner_section():
    def meta_table(rows):
        trs = "".join(
            f'<tr><td><strong>{r["label"]}</strong></td>'
            f'<td class="text-center"><span class="label {"label-success" if r["is_set"] else ""}">{r["value"]}</span></td></tr>'
            for r in rows
        )
        return f'<table class="table table-bordered table-condensed m-b-none"><tbody>{trs}</tbody></table>'

    def popup_card(card):
        header = f"""
            <div class="ibox-title">
                <h5>{card["title"]}</h5>
                <div class="ibox-tools"><a class="btn btn-warning btn-xs" title="Banner für Region individualisieren"><i class="fa fa-download"></i></a></div>
            </div>"""
        return f'<div class="ibox"><div style="background:#f7e2c4;">{header}</div><div class="ibox-content">{meta_table(card["rows"])}</div></div>'

    def banner_card(banner):
        if banner["has_content"]:
            tools = (
                '<a class="btn btn-success btn-xs" title="Banner bearbeiten"><i class="fa fa-pencil"></i></a> '
                '<a class="btn btn-danger btn-xs" title="Banner löschen und zentralen Stand wieder herstellen"><i class="fa fa-trash-o"></i></a>'
            )
            header_bg = "background:#333333;"
            img_html = f'<img src="{banner["img_src"]}" style="max-width:100%;" alt="">'
        else:
            tools = '<a class="btn btn-warning btn-xs" title="Banner für Region individualisieren"><i class="fa fa-download"></i></a>'
            header_bg = ""
            img_html = '<div class="text-center text-muted" style="padding:20px 0;"><i class="fa fa-image fa-2x"></i></div>'
        return f"""
    <div class="ibox">
        <div class="ibox-title" style="{header_bg}">
            <h5 style="{'color:#fff;' if banner['has_content'] else ''}">{banner["title"]}</h5>
            <div class="ibox-tools">{tools}</div>
        </div>
        <div class="ibox-content">{img_html}</div>
        <div class="ibox-content">{meta_table(banner["rows"])}</div>
    </div>"""

    popup_html = "".join(f'<div class="col-sm-6">{popup_card(card)}</div>' for card in werbebanner_data["popup_cards"])

    category_sections = []
    for cat in werbebanner_data["categories"]:
        cards = "".join(f'<div class="col-sm-3">{banner_card(b)}</div>' for b in cat["banners"])
        category_sections.append(f"""
    <div class="ibox">
        <div class="ibox-title"><h5>{cat["title"]}</h5></div>
    </div>
    <div class="row">{cards}</div>
    """)

    heading = c.page_heading("Werbebanner und PopUps für AAI24", ["Home", "alle Regionen", "Immobilien Werbebanner", "AAI24"])
    content = f"""
    <div class="wrapper wrapper-content animated fadeInRight">
        <div class="ibox">
            <div class="ibox-title"><h5>Pop-Up Kontaktanfrage</h5></div>
        </div>
        <div class="row">{popup_html}</div>
        {''.join(category_sections)}
    </div>"""
    return heading + content


# --- Section 6: Seiten individualisieren ------------------------------------

def build_seiten_section():
    def name_cell(entry):
        pfad = entry["pfad"] or "&mdash;"
        return f'{entry["name"]}<br><small class="text-muted">{pfad}</small>'

    def rows_html(entries, has_sortierung):
        out = []
        for e in entries:
            cells = [
                f'<a href="{e["view_href"]}" target="_blank" class="btn btn-default btn-xs" title="Seite aufrufen"><i class="fa fa-external-link"></i></a>',
                name_cell(e),
            ]
            if has_sortierung:
                cells.append(e["sortierung"])
            cells.append(e["sektionen"])
            cells.append(row_action_link("seite-bearbeiten", '<i class="fa fa-pencil"></i>', "bearbeiten"))
            out.append("<tr>" + "".join(f"<td>{c_}</td>" for c_ in cells) + "</tr>")
        return "".join(out)

    def table_html(entries, has_sortierung, css_class):
        cols = ["Seite aufrufen", "Ebene / Bezeichnung &middot; Pfad"]
        if has_sortierung:
            cols.append("Sortierung")
        cols += ["Sektionen / Elemente", "bearbeiten"]
        thead = "<tr>" + "".join(f"<th>{h}</th>" for h in cols) + "</tr>"
        return f"""
    <div class="table-responsive">
        <table class="table table-striped table-bordered table-hover {css_class}">
            <thead>{thead}</thead>
            <tbody>{rows_html(entries, has_sortierung)}</tbody>
        </table>
    </div>"""

    hauptnav_html = table_html(seiten_data["hauptnavigation"], True, "data-table-hauptnav")
    servicenav_html = table_html(seiten_data["servicenavigation"], True, "data-table-servicenav")
    ohne_zuordnung_html = table_html(seiten_data["seiten_ohne_zuordnung"], False, "data-table-ohne-zuordnung")

    heading = c.page_heading("Seiten - Aachen-Eifelimmobilien24", ["Home", "alle Regionen", "regionale Seiten - Aachen-Eifelimmobilien24"])
    content = f"""
    <div class="wrapper wrapper-content animated fadeInRight">
        <div class="row">
            <div class="col-lg-6">{c.ibox("Hauptnavigation", hauptnav_html)}</div>
            <div class="col-lg-6">
                {c.ibox("Servicenavigation", servicenav_html)}
                {c.ibox("Seiten ohne Zuordnung", ohne_zuordnung_html)}
            </div>
        </div>
    </div>"""
    return heading + content


# --- Section 7: Seite '<X>' bearbeiten (reached from a Seiten row's pencil,
# not from the sidebar sub-menu) ---------------------------------------------

def build_seite_bearbeiten_section():
    d = seite_bearbeiten_data

    grund_thead = """
    <tr>
        <th>Bezeichnung &middot; Pfad</th>
        <th>Sortierung</th>
        <th>Sektionen / Elemente</th>
    </tr>"""
    grund_row = (
        "<tr>"
        f'<td>{d["page_name"]}<br><small class="text-muted">{d["pfad"]}</small></td>'
        f'<td class="text-center">{d["sortierung"]}</td>'
        f'<td class="text-center">{d["sektionen"]}</td>'
        "</tr>"
    )
    grund_table = f"""
    <div class="table-responsive">
        <table class="table table-bordered">
            <thead>{grund_thead}</thead>
            <tbody>{grund_row}</tbody>
        </table>
    </div>"""

    sektionen_thead = """
    <tr>
        <th>Bezeichnung</th>
        <th>Sortierung</th>
        <th>bearbeiten</th>
    </tr>"""
    sektionen_rows = "".join(
        "<tr>"
        f'<td>{s["bezeichnung"]}</td>'
        f'<td class="text-center">{s["sortierung"]}</td>'
        '<td class="text-center"><a href="#" class="btn btn-default btn-xs" title="Sektion bearbeiten"><i class="fa fa-pencil"></i></a></td>'
        "</tr>"
        for s in d["sections"]
    )
    sektionen_table = f"""
    <div class="table-responsive">
        <table class="table table-striped table-bordered table-hover">
            <thead>{sektionen_thead}</thead>
            <tbody>{sektionen_rows}</tbody>
        </table>
    </div>"""

    # The real "Daten der Seite: /aachen-eifel/baufinanzierung/" 5-tab SEO
    # editor — reached from the separate "SEO" top-level menu on the live
    # site, folded in here next to Grundeinstellungen per instruction (see
    # build.py docstring / prototypes/regionen-seite-bearbeiten).
    def seo_field_row(label, control_html, help_text=""):
        help_html = f' <i class="fa fa-question-circle text-muted" title="{help_text}"></i>' if help_text else ""
        return f"""
        <div class="form-group row">
            <label class="col-sm-3 control-label">{label}{help_html}</label>
            <div class="col-sm-9">{control_html}</div>
        </div>"""

    def seo_select(name, options):
        opts = "".join(
            f'<option value="{v}"{" selected" if sel else ""}>{t}</option>' for v, t, sel in options
        )
        return f'<select class="form-control" name="{name}">{opts}</select>'

    def seo_save_button():
        return '<div class="text-right m-t-md"><button type="button" class="btn btn-primary btn-sm" title="Speichern"><i class="fa fa-floppy-o"></i></button></div>'

    kd = seo_baufinanzierung_data["kopf_daten"]
    kopfdaten_body = "".join([
        seo_field_row("Bezeichnung (intern)", f'<input type="text" class="form-control" value="{kd["name"]}">', "interner Name, erscheint nicht auf der Seite"),
        seo_field_row("URL", f'<input type="text" class="form-control" value="{kd["location"]}" disabled> <span class="text-danger">*</span>'),
        seo_field_row("Page-Titel", f'<input type="text" class="form-control" value="{kd["title"]}">'),
        seo_field_row("H1-SEO-Überschrift", f'<input type="text" class="form-control" value="{kd["header"]}">', "überschreibt die H1 nur für Suchmaschinen"),
        seo_field_row("Schlüsselwörter (Keywords)", f'<input type="text" class="form-control" value="{kd["keywords"]}">'),
        seo_field_row("Beschreibungstext", f'<textarea class="form-control" rows="3">{kd["description"]}</textarea>'),
        seo_field_row("Robots", seo_select("robots", kd["robots_options"])),
        seo_field_row("wieder indizieren", seo_select("revisit-after", kd["revisit_options"])),
        seo_save_button(),
    ])

    sm = seo_baufinanzierung_data["sitemap"]
    sitemap_body = "".join([
        seo_field_row("Priorität", seo_select("prio", sm["prio_options"])),
        seo_field_row("Update-Rate", seo_select("update", sm["update_options"])),
        seo_save_button(),
    ])

    tb = seo_baufinanzierung_data["textblock"]
    textblock_body = "".join([
        seo_field_row("Text", f'<textarea class="form-control" rows="10">{tb["text"]}</textarea>'),
        seo_field_row("Text 2", f'<textarea class="form-control" rows="4">{tb["text2"]}</textarea>'),
        '<p class="text-muted"><small>Die Live-Seite zeigt hier zusätzlich eine bebilderte Anleitung, wo Text/Text 2 auf der öffentlichen Seite erscheinen — ein statisches Hilfsbild, keine Daten, daher hier nicht reproduziert.</small></p>',
        seo_save_button(),
    ])

    bild_body = """
    <div class="text-center m-b-md">
        <div style="display:inline-block;background:#f3f3f4;border:1px dashed #d7d7d7;padding:20px 30px;color:#999;">
            <i class="fa fa-image fa-2x"></i><br><small>Vorschaubild (kein Bild hinterlegt)</small>
        </div>
    </div>
    <input type="file" class="form-control">
    <div class="text-right m-t-md"><button type="button" class="btn btn-primary btn-sm">Hochladen</button></div>
    """

    faq_body = '<button type="button" class="btn btn-primary btn-sm">Neue Frage</button>'

    seo_tabs = f"""
    <ul class="nav nav-tabs">
        <li class="active"><a data-toggle="tab" href="#seo-tab-kopfdaten">Kopf-Daten</a></li>
        <li><a data-toggle="tab" href="#seo-tab-sitemap">Infos f&uuml;r Sitemap</a></li>
        <li><a data-toggle="tab" href="#seo-tab-textblock">SEO-Textblock</a></li>
        <li><a data-toggle="tab" href="#seo-tab-bild">Bild f&uuml;r SEO-Textblock</a></li>
        <li><a data-toggle="tab" href="#seo-tab-faq">H&auml;ufige Fragen</a></li>
    </ul>
    <div class="tab-content">
        <div class="tab-pane active" id="seo-tab-kopfdaten">{kopfdaten_body}</div>
        <div class="tab-pane" id="seo-tab-sitemap">{sitemap_body}</div>
        <div class="tab-pane" id="seo-tab-textblock">{textblock_body}</div>
        <div class="tab-pane" id="seo-tab-bild">{bild_body}</div>
        <div class="tab-pane" id="seo-tab-faq">{faq_body}</div>
    </div>
    """

    heading = c.page_heading(f"Seite '{d['page_name']}' bearbeiten - Aachen-Eifelimmobilien24", ["Home", "alle Regionen", "regionale Seiten - Aachen-Eifelimmobilien24", "Seite bearbeiten - Aachen-Eifelimmobilien24"])
    content = f"""
    <div class="wrapper wrapper-content animated fadeInRight">
        <div class="row">
            <div class="col-lg-6">{c.ibox("Grundeinstellungen", grund_table)}</div>
            <div class="col-lg-6">{c.ibox("zugeordnete Sektionen", sektionen_table)}</div>
        </div>
        <div class="row">
            <div class="col-lg-12">{c.ibox(f"Daten der Seite: {seo_baufinanzierung_data['url_path']}", seo_tabs)}</div>
        </div>
    </div>"""
    return heading + content


SECTION_BUILDERS = {
    "list": build_list_section,
    "params": build_params_section,
    "geodaten": build_geodaten_section,
    "mailings": build_mailings_section,
    "werbebanner": build_werbebanner_section,
    "seiten": build_seiten_section,
    "seite-bearbeiten": build_seite_bearbeiten_section,
}

# "seite-bearbeiten" isn't in PAGE_IDS — it has no sidebar sub-menu entry,
# same as on the live site, only reachable via a Seiten row's pencil icon.
ALL_PAGE_IDS = [pid for pid, _ in PAGE_IDS] + ["seite-bearbeiten"]

sections_html = []
for page_id in ALL_PAGE_IDS:
    inner = SECTION_BUILDERS[page_id]()
    display = "block" if page_id == "list" else "none"
    sections_html.append(f'<div class="region-page" id="region-page-{page_id}" style="display:{display};">{inner}</div>')

all_sections_html = "\n".join(sections_html)

sidebar_html = c.sidebar(active_top_item="alle Regionen", breadcrumb_under_dashboard=False)

SCRIPT = """
<script>
function showRegionPage(id) {
    $('.region-page').hide();
    $('#region-page-' + id).show();
    $('#region-page-' + id + ' table.dataTable').each(function () {
        $(this).DataTable().columns.adjust().draw(false);
    });
    $('#side-menu li[id^="regionen-nav-"]').removeClass('active');
    var li = $('a[data-page="' + id + '"]').closest('li');
    li.addClass('active');
    $('html, body').scrollTop(0);
}

$(function () {
    $('.data-table-regionen').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [
            { targets: [3, 4], orderable: false, className: 'text-center', width: '60px' },
            { targets: [5, 6, 7, 8, 9], orderable: false }
        ]
    });
    $('.data-table-mailings').DataTable({
        pageLength: 25,
        autoWidth: false,
        columnDefs: [ { targets: [1, 2], orderable: false, width: '160px' } ]
    });
    ['.data-table-hauptnav', '.data-table-servicenav', '.data-table-ohne-zuordnung'].forEach(function (sel) {
        $(sel).DataTable({
            pageLength: 10,
            autoWidth: false,
            columnDefs: [ { targets: [0, -1], orderable: false, width: '40px' } ]
        });
    });
});
</script>
"""

EXTRA_HEAD = (
    '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
    "<style>\n"
    "  .data-table-regionen thead th, .data-table-mailings thead th,\n"
    "  .data-table-hauptnav thead th, .data-table-servicenav thead th, .data-table-ohne-zuordnung thead th\n"
    "  { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
    "  .data-table-regionen a:not(.btn) { color: #333333 !important; }\n"
    "  .data-table-regionen a:not(.btn):hover, .data-table-regionen a:not(.btn):focus { color: #A4C735 !important; }\n"
    "  .data-table-regionen .badge-inverse { background-color: #333333 !important; }\n"
    "  table.dataTable thead th.sorting, table.dataTable thead th.sorting_asc, table.dataTable thead th.sorting_desc\n"
    "  { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
    "  table.dataTable thead .sorting:after, table.dataTable thead .sorting_asc:after, table.dataTable thead .sorting_desc:after\n"
    "  { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
    "  .region-page { }\n"
    "</style>"
)

banner_html = c.prototype_banner(
    "alle Regionen — all 6 screens combined into one file",
    "Click through the sidebar's \"alle Regionen\" sub-menu (or a row's \"anpassen\" buttons on the list) to "
    "jump between sections without leaving this file. Same real data as the separate prototypes/regionen*/ folders.",
)

html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>alle Regionen (combined) - RI24 SEO</title>
<link href="assets/css/bootstrap.min.css" rel="stylesheet">
<link href="assets/font-awesome/css/font-awesome.css" rel="stylesheet">
{EXTRA_HEAD}
<link href="assets/css/animate.css" rel="stylesheet">
<link href="assets/css/style.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-adaptation.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-colors.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-icons.css" rel="stylesheet">
<style>{c.PROTOTYPE_CSS}</style>
</head>
<body class="pitcom">
{banner_html}
<div id="wrapper">
    {sidebar_html}
    <div id="page-wrapper" class="gray-bg dashbard-1">
        {c.TOPBAR}
        {all_sections_html}
        {c.FOOTER}
    </div>
</div>

<script src="assets/js/jquery-3.1.1.min.js"></script>
<script src="assets/js/popper.min.js"></script>
<script src="assets/js/bootstrap.js"></script>
<script src="assets/js/plugins/metisMenu/jquery.metisMenu.js"></script>
<script src="assets/js/plugins/slimscroll/jquery.slimscroll.min.js"></script>
<script src="assets/js/plugins/flot/jquery.flot.js"></script>
<script src="assets/js/plugins/flot/jquery.flot.tooltip.min.js"></script>
<script src="assets/js/plugins/flot/jquery.flot.resize.js"></script>
<script src="assets/js/plugins/flot/jquery.flot.pie.js"></script>
<script src="assets/js/plugins/flot/jquery.flot.time.js"></script>
<script src="assets/js/inspinia.js"></script>
<script src="assets/js/plugins/pace/pace.min.js"></script>
<script src="assets/js/plugins/dataTables/datatables.min.js"></script>
<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>
<script>{c.DATATABLES_DE_JS}</script>
{SCRIPT}
</body>
</html>
"""

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
