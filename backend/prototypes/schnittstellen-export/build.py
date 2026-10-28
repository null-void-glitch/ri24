"""Generates index.html: Schnittstellen › Statischer Immobilien Export
(/adm/individuell/master/interface/immo/static/), rebuilt on Inspinia.

28 real API accounts. Passwords are real plaintext credentials from the live
backend and are replaced with placeholder bullets. Login usernames are shown
(they are the same as the account names, used only for HTTP basic auth on the
static XML export endpoint — not personal login credentials).

UI: table with Name / Login / Passwort (masked) / delete-button.
    Add-form row at the bottom: just a "Bezeichnung" field (the backend
    auto-generates login+password from the name).
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE   = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data  = json.loads((SURVEY / "49-immo-static-rows.json").read_text(encoding="utf-8"))
rows  = data["rows"]
total = data["total_real_rows"]

# Generate a plausible masked password length per row (8–12 bullets, random-looking)
import hashlib
def mask_pw(login):
    n = 8 + (int(hashlib.md5(login.encode()).hexdigest(), 16) % 5)
    return "•" * n

FEED_URLS = [
    ("JSON",                 "https://zbv.regionalimmobilien24.de/webapi/json/export.json"),
    ("XML",                  "https://zbv.regionalimmobilien24.de/webapi/xml/export.xml"),
    ("OpenImmo-XML (v1.2.7b)", "https://zbv.regionalimmobilien24.de/webapi/openimmo/export.xml"),
]

feed_alerts = "".join(
    f'<div class="alert alert-info" style="margin-bottom:8px;">'
    f'<strong>{label}:</strong> '
    f'<a href="{url}" target="_blank" style="color:#31708f;">{url}</a>'
    f'</div>'
    for label, url in FEED_URLS
)

thead = """<tr>
    <th>Name</th>
    <th>Login</th>
    <th>Passwort</th>
    <th style="width:60px;"></th>
</tr>"""

add_row = """
<tr class="warning" id="add-row">
    <td colspan="3">
        <input type="text" class="form-control input-sm" name="bez"
               placeholder="Bezeichnung (Name des neuen Accounts)" style="width:100%;">
    </td>
    <td class="text-center" style="vertical-align:middle;">
        <button type="button" class="btn btn-success btn-sm" title="hinzufügen">
            <i class="fa fa-plus"></i> hinzufügen
        </button>
    </td>
</tr>"""

tbody_rows = []
for r in rows:
    pw_display = mask_pw(r["login"])
    del_btn = (
        '<button type="button" class="btn btn-danger btn-xs" title="löschen">'
        '<i class="fa fa-times"></i></button>'
        if r["has_delete"] else ""
    )
    cells = [
        r["name"],
        f'<code>{r["login"]}</code>',
        f'<code class="text-muted">{pw_display}</code>',
        del_btn,
    ]
    tbody_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")

tbody_rows.append(add_row)

table_html = f"""
<div class="table-responsive">
    <table id="static-export-table" class="table table-striped table-bordered table-hover">
        <thead>{thead}</thead>
        <tbody>{''.join(tbody_rows)}</tbody>
    </table>
</div>"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-12">
            {c.ibox("Export-Endpunkte", feed_alerts)}
            {c.ibox(
                f'Accounts &nbsp;<span class="badge" style="background:#5b9bd5">{total}</span>',
                table_html
            )}
        </div>
    </div>
</div>"""

html = c.page_shell(
    title="Statischer Immobilien Export - Schnittstellen - RI24 Admin",
    banner_html=c.prototype_banner(
        "Schnittstellen › Statischer Immobilien Export (/adm/.../master/interface/immo/static/)",
        f"{total} real API accounts. Passwords replaced with placeholders (real credentials masked). "
        "Login names are HTTP basic-auth usernames for the static XML export endpoint.",
    ),
    content_html=c.page_heading(
        "Statischer Immobilien Export",
        ["Home", "Schnittstellen", "Statischer Immobilien Export"]
    ) + content,
    extra_head=(
        "<style>\n"
        "  #static-export-table thead th { background-color: #333333 !important; font-size: 12px; }\n"
        "  #static-export-table td { vertical-align: middle; font-size: 13px; }\n"
        "  #static-export-table tr.warning td { background: #fcf8e3; }\n"
        "</style>"
    ),
    active_schnittstellen_item="Statischer Immobilien Export",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
