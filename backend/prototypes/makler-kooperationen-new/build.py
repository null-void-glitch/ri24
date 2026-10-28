"""Generates index.html: Makler › Kooperationen › neue Kooperation
(/adm/individuell/master/makler/kooperation/new/), rebuilt on Inspinia.

Form fields (real field names from live backend):
  name           — Name *
  link_anonym    — Link (anonym)  [shown on public /kooperation/ page]
  link           — Link mit Ri24-Rabatt *
  beschreibung   — Beschreibung * (textarea; TinyMCE on live site)
  is_partner_crm — ist ein CRM mit Login im Partnerbereich (select: nein / ja)
  login_uri      — Login-Link für Partner-Bereich
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent


def txt(name, placeholder=""):
    return (f'<input type="text" class="form-control" id="{name}" name="{name}" '
            f'placeholder="{placeholder}">')


def fg(label, name, input_html, hint="", required=False):
    req = ' <span class="text-danger">*</span>' if required else ""
    hint_row = f'<p class="help-block">{hint}</p>' if hint else ""
    return (
        f'<div class="form-group">'
        f'<label for="{name}" class="col-sm-3 control-label">{label}{req}</label>'
        f'<div class="col-sm-9">{input_html}{hint_row}</div>'
        f'</div>'
    )


f_name = fg("Name", "name", txt("name"), required=True)

f_link_anonym = fg(
    "Link (anonym)", "link_anonym",
    txt("link_anonym", "https://www.was-auch-immer.intern"),
    hint=(
        "Wenn ein Link hinterlegt ist, wird der Eintrag mit Link auf der anonymen Seite "
        "<a href='https://www.regionalimmobilien24.de/kooperation/' target='_blank'>/kooperation/</a> angezeigt."
    )
)

f_link = fg(
    "Link mit Ri24-Rabatt", "link",
    txt("link", "https://www.was-auch-immer.intern/ri24rabatt"),
    required=True,
)

f_beschreibung = fg(
    "Beschreibung", "beschreibung",
    '<textarea class="form-control" id="beschreibung" name="beschreibung" rows="5" '
    'placeholder="Kurzbeschreibung der Kooperation…"></textarea>',
    required=True,
)

crm_select = (
    '<select class="form-control" id="is_partner_crm" name="is_partner_crm">'
    '<option value="0">nein</option>'
    '<option value="1">ja</option>'
    '</select>'
)
f_crm = fg(
    "CRM mit Login im Partnerbereich", "is_partner_crm",
    crm_select,
    hint="Wenn „ja“: wird im Partnerbereich des Maklers ein Login-Link eingeblendet.",
)

f_login_uri = fg(
    "Login-Link für Partner-Bereich", "login_uri",
    txt("login_uri", "https://www.was-auch-immer.intern/login"),
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

form_html = (
    '<form class="form-horizontal" method="post" action="#">'
    + f_name + f_link_anonym + f_link + f_beschreibung + f_crm + f_login_uri + f_buttons
    + '</form>'
)

back_btn = (
    '<a href="../makler-kooperationen/index.html" class="btn btn-default btn-sm m-b-md">'
    '<i class="fa fa-arrow-left"></i> zurück zur Übersicht</a>'
)

content = (
    '<div class="wrapper wrapper-content animated fadeInRight">'
    '<div class="row"><div class="col-lg-8 col-lg-offset-2">'
    + back_btn
    + c.ibox("Neue Kooperation", form_html)
    + '</div></div></div>'
)

html = c.page_shell(
    title="Neue Kooperation - Makler - RI24 Admin",
    banner_html=c.prototype_banner(
        "Makler › Kooperationen › neue Kooperation (/adm/.../makler/kooperation/new/)",
        "Real field names and structure from the live backend. "
        "Beschreibung uses a plain textarea (TinyMCE on the live site). "
        "Speichern / Abbrechen are decorative.",
    ),
    content_html=c.page_heading(
        "neue Kooperation",
        ["Home", "Makler", "Kooperationen", "neue Kooperation"]
    ) + content,
    active_kooperationen_item="neue Kooperation",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
