"""Generates index.html: Kooperationen › bearbeiten
(/adm/individuell/master/makler/kooperation/edit/?id=25), rebuilt on Inspinia.

Pre-filled with the real "onOffice" entry (id=25) as the example row.
Edit form fields: sort, name, link_anonym, link, beschreibung, is_partner_crm, login_uri.
Logo section: current logo preview + upload-new (file input) + delete button.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent

# Example data: onOffice (first real row, id=25, sort=-1)
EXAMPLE = {
    "name": "onOffice",
    "sort": "-1",
    "link_anonym": "",
    "link": "https://onoffice.com/immobiliensoftware/?utm_source=pr&utm_medium=organic&utm_campaign=ri24",
    "beschreibung": (
        "Immobiliensoftware, WP-Websites, App und Online-Marketing-Produkte\n"
        "Zusammenarbeit mit Maklern und Immobilienprofis seit 2000\n"
        "All-in-one Plattform für die Immobilienbranche"
    ),
    "is_partner_crm": "0",
    "login_uri": "",
    "logo_src": (
        "https://bilder.regionalimmobilien24.de/get-file/img/images/system_ri24"
        "/kooperation/v/50x50/crop/658987be_onOffice_Logo2024_blue-black_RGB.png"
    ),
}


def txt(name, placeholder="", value="", input_type="text"):
    return (
        f'<input type="{input_type}" class="form-control" id="{name}" name="{name}" '
        f'placeholder="{placeholder}" value="{value}">'
    )


def fg(label, name, input_html, hint="", required=False):
    req = ' <span class="text-danger">*</span>' if required else ""
    hint_row = f'<p class="help-block">{hint}</p>' if hint else ""
    return (
        f'<div class="form-group">'
        f'<label for="{name}" class="col-sm-3 control-label">{label}{req}</label>'
        f'<div class="col-sm-9">{input_html}{hint_row}</div>'
        f'</div>'
    )


f_sort = fg(
    "Sortierung", "sort",
    txt("sort", value=EXAMPLE["sort"], input_type="number"),
    hint="Niedrigere Zahl = weiter oben. -1 = ganz oben."
)

f_name = fg("Name", "name", txt("name", value=EXAMPLE["name"]), required=True)

f_link_anonym = fg(
    "Link (anonym)", "link_anonym",
    txt("link_anonym", "https://www.was-auch-immer.intern", EXAMPLE["link_anonym"]),
    hint=(
        "Wenn ein Link hinterlegt ist, wird der Eintrag mit Link auf der anonymen Seite "
        "<a href='https://www.regionalimmobilien24.de/kooperation/' target='_blank'>/kooperation/</a> angezeigt."
    )
)

f_link = fg(
    "Link mit Ri24-Rabatt", "link",
    txt("link", "https://www.was-auch-immer.intern/ri24rabatt", EXAMPLE["link"]),
    required=True,
)

desc_val = EXAMPLE["beschreibung"].replace("<", "&lt;").replace(">", "&gt;")
f_beschreibung = fg(
    "Beschreibung", "beschreibung",
    f'<textarea class="form-control" id="beschreibung" name="beschreibung" rows="5">{desc_val}</textarea>',
    required=True,
)

crm_nein = ' selected' if EXAMPLE["is_partner_crm"] == "0" else ""
crm_ja   = ' selected' if EXAMPLE["is_partner_crm"] == "1" else ""
crm_select = (
    f'<select class="form-control" id="is_partner_crm" name="is_partner_crm">'
    f'<option value="0"{crm_nein}>nein</option>'
    f'<option value="1"{crm_ja}>ja</option>'
    f'</select>'
)
f_crm = fg(
    "CRM mit Login im Partnerbereich", "is_partner_crm",
    crm_select,
    hint="Wenn „ja“: wird im Partnerbereich des Maklers ein Login-Link eingeblendet.",
)

f_login_uri = fg(
    "Login-Link für Partner-Bereich", "login_uri",
    txt("login_uri", "https://www.was-auch-immer.intern/login", EXAMPLE["login_uri"]),
    hint="Nur relevant wenn „CRM mit Login“ = ja.",
)

f_buttons = (
    '<div class="form-group">'
    '<div class="col-sm-offset-3 col-sm-9">'
    '<button type="submit" class="btn btn-primary">'
    '<i class="fa fa-save"></i> Speichern</button>'
    ' <a href="../makler-kooperationen/index.html" class="btn btn-default">'
    '<i class="fa fa-arrow-left"></i> Abbrechen</a>'
    ' <span class="text-muted m-l-md" style="font-size:12px;">'
    '<span class="text-danger">*</span> Pflichtfeld</span>'
    '</div></div>'
)

main_form = (
    '<form class="form-horizontal" method="post" action="#">'
    + f_sort + f_name + f_link_anonym + f_link + f_beschreibung + f_crm + f_login_uri + f_buttons
    + '</form>'
)

# Logo section — separate ibox
logo_section = (
    '<div class="row m-b-sm">'
    '<div class="col-sm-3 text-right"><strong>Aktuelles Logo</strong></div>'
    '<div class="col-sm-9">'
    f'<img src="{EXAMPLE["logo_src"]}" alt="Logo" '
    'style="max-width:120px;max-height:60px;object-fit:contain;border:1px solid #e7eaec;padding:6px;">'
    '</div></div>'
    '<form class="form-horizontal" method="post" enctype="multipart/form-data" action="#" style="margin-top:12px;">'
    '<div class="form-group">'
    '<label class="col-sm-3 control-label">Neues Logo hochladen</label>'
    '<div class="col-sm-9">'
    '<input type="file" name="logo" accept="image/*" class="form-control-file">'
    '<p class="help-block">PNG, JPG oder WebP empfohlen. Wird auf 50×50 px zugeschnitten.</p>'
    '</div></div>'
    '<div class="form-group"><div class="col-sm-offset-3 col-sm-9">'
    '<button type="submit" class="btn btn-default btn-sm"><i class="fa fa-upload"></i> Hochladen</button>'
    ' <button type="button" class="btn btn-danger btn-sm m-l-sm">'
    '<i class="fa fa-trash"></i> Logo löschen</button>'
    '</div></div>'
    '</form>'
)

back_btn = (
    '<a href="../makler-kooperationen/index.html" class="btn btn-default btn-sm m-b-md">'
    '<i class="fa fa-arrow-left"></i> zurück zur Übersicht</a>'
)

content = (
    '<div class="wrapper wrapper-content animated fadeInRight">'
    '<div class="row"><div class="col-lg-8 col-lg-offset-2">'
    + back_btn
    + c.ibox("Kooperation bearbeiten — onOffice", main_form)
    + c.ibox("Logo", logo_section)
    + '</div></div></div>'
)

html = c.page_shell(
    title="Kooperation bearbeiten - RI24 Admin",
    banner_html=c.prototype_banner(
        "Kooperationen › bearbeiten (/adm/.../makler/kooperation/edit/?id=25)",
        "Pre-filled with real onOffice entry (id=25). "
        "Beschreibung uses plain textarea (TinyMCE on live site). "
        "Speichern / Logo-Upload / Löschen are decorative.",
    ),
    content_html=c.page_heading(
        "Kooperation bearbeiten",
        ["Home", "Kooperationen", "bearbeiten"]
    ) + content,
    active_top_item="Kooperationen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
