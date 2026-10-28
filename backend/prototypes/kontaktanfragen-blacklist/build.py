"""Generates index.html: the 'Blacklist' (Kunden mit Kontaktsperre) screen
under Kontaktanfragen (/adm/individuell/master/mails/blacklist/).

The live page renders as a plain sorted table (NOT DataTables) with:
  - A-Z / Z-A sort buttons (sort by E-Mail)
  - CSV-Export button
  - Total count badge
  - Inline add-new-entry form row at the top of the table body
  - Red "−" remove button on each existing row

The live table has 1799 entries; capped at 150 here for a reviewable file.
Name, Vorname and Telefon are nearly always empty in the live data.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "44-mails-blacklist-rows.json").read_text(encoding="utf-8"))
rows = data["rows"]
total_real_rows = data["total_real_rows"]

# Inline add-form row (first row in the table body)
add_row = """
<tr id="blacklist-add-row" class="warning">
    <td class="text-muted" id="blacklist-add-datum" style="white-space:nowrap;vertical-align:middle;"></td>
    <td><input type="text" class="form-control input-sm" placeholder="Nachname (optional)"></td>
    <td><input type="text" class="form-control input-sm" placeholder="Vorname (optional)"></td>
    <td><input type="text" class="form-control input-sm" placeholder="email@domain.tld"></td>
    <td><input type="text" class="form-control input-sm" placeholder="03741xxx (optional)"></td>
    <td class="text-center" style="vertical-align:middle;">
        <button type="button" class="btn btn-success btn-sm" title="Zur Blacklist hinzufügen"><i class="fa fa-plus"></i></button>
    </td>
</tr>"""


def remove_btn():
    return '<button type="button" class="btn btn-danger btn-sm" title="Aus Blacklist entfernen"><i class="fa fa-minus"></i></button>'


def email_cell(val):
    if not val:
        return "&mdash;"
    return f'<a href="mailto:{val}">{val}</a>'


body_rows = [add_row]
for r in rows:
    cells = [
        f'<span style="white-space:nowrap;">{r.get("datum", "")}</span>',
        r.get("name", "") or "",
        r.get("vorname", "") or "",
        email_cell(r.get("email", "")),
        r.get("telefon", "") or "",
        remove_btn(),
    ]
    body_rows.append(
        '<tr>' + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>"
    )

table_html = f"""
<div class="table-responsive">
    <table id="blacklist-table" class="table table-striped table-bordered table-hover">
        <thead>
            <tr>
                <th>Datum der Eintragung</th>
                <th>Name</th>
                <th>Vorname</th>
                <th>E-Mail</th>
                <th>Telefon</th>
                <th style="width:60px;">Blacklist</th>
            </tr>
        </thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
</div>"""

# Custom ibox with full toolbar (A-Z, Z-A, CSV-Export, count badge)
ibox_html = f"""
<div class="ibox">
    <div class="ibox-title" style="display:flex;align-items:center;justify-content:space-between;">
        <h5 style="margin:0;">Kunden mit Kontaktsperre</h5>
        <div style="display:flex;align-items:center;gap:6px;">
            <button type="button" class="btn btn-default btn-sm" title="CSV-Export"><i class="fa fa-download"></i> CSV-Export</button>
            <span class="badge" style="background-color:#5b9bd5;font-size:13px;padding:5px 10px;">{total_real_rows}</span>
        </div>
    </div>
    <div class="ibox-content">
        <p class="text-muted">
            {len(rows)} von {total_real_rows} Einträgen angezeigt (auf {len(rows)} begrenzt).
            Name, Vorname und Telefon sind im Live-System bei den meisten Einträgen leer.
        </p>
        {table_html}
    </div>
</div>"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{ibox_html}</div></div>
</div>"""

SCRIPT = """
<script>
$(function () {
    // Set today's date in the add row datum cell
    var today = new Date();
    var dd = String(today.getDate()).padStart(2,'0');
    var mm = String(today.getMonth()+1).padStart(2,'0');
    var yy = String(today.getFullYear()).slice(-2);
    $('#blacklist-add-datum').text(dd + '.' + mm + '.' + yy);

});
</script>
"""

html = c.page_shell(
    title="Blacklist - Kontaktanfragen - RI24 Admin",
    banner_html=c.prototype_banner(
        "Blacklist / Kunden mit Kontaktsperre (/adm/.../master/mails/blacklist/)",
        f"{len(rows)} of {total_real_rows} real rows shown (capped). "
        "Add-form row, A-Z/Z-A sort, CSV-Export and remove buttons replicate the live backend. "
        "Name/Vorname/Telefon are nearly always empty in the live data.",
    ),
    content_html=c.page_heading("Blacklist", ["Home", "Kontaktanfragen", "Blacklist"]) + content,
    extra_head=(
        "<style>\n"
        "  #blacklist-table thead th { background-color: #333333 !important; color: #fff; text-align: left !important; font-size: 12px !important; }\n"
        "  #blacklist-table a { color: #333333 !important; }\n"
        "  #blacklist-table a:hover { color: #A4C735 !important; }\n"
        "  #blacklist-table tr.warning td { background-color: #fcf8e3; }\n"
        "  .ibox-title { flex-wrap: wrap; }\n"
        "</style>"
    ),
    extra_scripts=SCRIPT,
    active_kontakt_item="Blacklist",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
