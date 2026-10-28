"""Generates index.html: the real 'Dashboard -> Baufi' backend screen,
rebuilt with the actual Inspinia theme assets (in assets/) and populated
with real data captured from the live backend (admin_survey/15-dashboard-baufi-*.json).
"""
import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs

# Standard German DataTables translation (datatables.net/plug-ins/i18n/German).
# Set once as the plugin default so every $(...).DataTable() call on this page
# picks it up without repeating it per table.
DATATABLES_DE_JS = """
$.extend(true, $.fn.dataTable.defaults, {
    language: {
        emptyTable: "Keine Daten in der Tabelle vorhanden",
        info: "_START_ bis _END_ von _TOTAL_ Einträgen",
        infoEmpty: "0 bis 0 von 0 Einträgen",
        infoFiltered: "(gefiltert von _MAX_ Einträgen)",
        lengthMenu: "_MENU_ Einträge anzeigen",
        loadingRecords: "Wird geladen...",
        processing: "Bitte warten...",
        search: "Suchen:",
        zeroRecords: "Keine Einträge vorhanden.",
        paginate: {
            first: "Erste",
            previous: "Zurück",
            next: "Nächste",
            last: "Letzte"
        },
        aria: {
            sortAscending: ": aktivieren, um Spalte aufsteigend zu sortieren",
            sortDescending: ": aktivieren, um Spalte absteigend zu sortieren"
        }
    }
});
"""


def preview_text(raw, max_len=60):
    """Some 'E-Mail-Text' values are full HTML email templates (with <style>
    blocks etc.) rather than short codes. Strip markup and truncate so the
    table stays a compact list instead of one giant cell per templated email."""
    text = re.sub(r"(?is)<(style|script)[^>]*>.*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    # Some source emails ship the <style> ruleset without its wrapping tag —
    # collapse innermost {...} blocks repeatedly until none remain, which
    # also clears @media wrappers.
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"[\w.#,\s\-:()%@]*\{[^{}]*\}", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + "…"
    return text

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

ajax = json.loads((SURVEY / "15-dashboard-baufi-ajax.json").read_text(encoding="utf-8"))
forms = json.loads((SURVEY / "15-dashboard-baufi-forms.json").read_text(encoding="utf-8"))


def find_body(url_suffix, table=None):
    for c in ajax:
        if not c["url"].endswith(url_suffix):
            continue
        pd = c.get("postData") or ""
        params = parse_qs(pd)
        if table is not None and params.get("table", [""])[0] != table:
            continue
        return c["body"]
    raise KeyError((url_suffix, table))


anfragen = find_body("/adm/helper/ajax/dashboard/")
leads = find_body("/adm/helper/ajax/dashboard/baufileads/")

# Folded in from the (not-migrated) Dashboard -> Finanzzertifikate / Terminvereinbarungen
# screens: both are really Baufinanzierung-Anfragen, so their charts+tables live here now.
finanzzert = json.loads((SURVEY / "22-finanzzert-body.json").read_text(encoding="utf-8"))
terminvb = json.loads((SURVEY / "23-terminvb-body.json").read_text(encoding="utf-8"))
finanzzert_forms = json.loads((SURVEY / "22-dashboard-finanzzert-forms.json").read_text(encoding="utf-8"))
terminvb_forms = json.loads((SURVEY / "23-dashboard-terminvb-forms.json").read_text(encoding="utf-8"))

FLOT_COLOR = "#1ab394"

f0 = forms[0]["selects"]
f1 = forms[1]["selects"]

FROM_DATE = "10.08.2026"
TO_DATE = "10.09.2026"


def select_html(name, options, selected_value=""):
    opts = []
    for value, label, _sel in options:
        sel = " selected" if value == selected_value else ""
        opts.append(f'<option value="{value}"{sel}>{label}</option>')
    return f'<select name="{name}" class="form-control input-sm">' + "".join(opts) + "</select>"


def ibox(title, body_html):
    return f"""
        <div class="ibox">
            <div class="ibox-title">
                <h5>{title}</h5>
                <div class="ibox-tools">
                    <a class="collapse-link"><i class="fa fa-chevron-up"></i></a>
                    <a class="close-link"><i class="fa fa-times"></i></a>
                </div>
            </div>
            <div class="ibox-content">
                {body_html}
            </div>
        </div>"""


# --- Panel 1: Anzahl Baufi-Anfragen ------------------------------------------

a_counts = anfragen["data1"]["counts"]
a_count = anfragen["data1"]["count"]

panel1_filters = f"""
    <div class="row m-b-sm">
        <div class="col-sm-3">{select_html("regioncode", f0["regioncode"])}</div>
        <div class="col-sm-3">{select_html("source", f0["source"])}</div>
        <div class="col-sm-2">
            <div class="input-group"><span class="input-group-addon">von</span>
                <input type="text" class="form-control input-sm datepicker" value="{FROM_DATE}"></div>
        </div>
        <div class="col-sm-2">
            <div class="input-group"><span class="input-group-addon">bis</span>
                <input type="text" class="form-control input-sm datepicker" value="{TO_DATE}"></div>
        </div>
    </div>
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("origin", f0["origin"])}</div>
    </div>
"""

# The raw per-lead rows (data3) -> a real DataTable, sourced from the live payload.
leads_rows = anfragen["data3"]["data"]
leads_rows = [row[:6] + [preview_text(row[6])] for row in leads_rows]
leads_thead = "<tr><th>Zeit</th><th>ID</th><th>Name Vorname</th><th>Empfänger</th><th>Sender</th><th>Antwort an</th><th>E-Mail-Text</th></tr>"
leads_tbody = "".join(
    "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in leads_rows
)

panel1_body = f"""
    <div class="row m-b-md">
        <div class="col-sm-2"><h2 class="no-margins">{a_count}</h2><small>gesamt</small></div>
        <div class="col-sm-2"><span class="label label-default">Organisch: {a_counts["none"]}</span></div>
        <div class="col-sm-2"><span class="label label-info">Google Ads: {a_counts["gads"]}</span></div>
        <div class="col-sm-2"><span class="label label-primary">Facebook: {a_counts["fb"]}</span></div>
        <div class="col-sm-2"><span class="label label-default" style="background:#000">Referral: {a_counts["referral"]}</span></div>
    </div>
    {panel1_filters}
    <div class="flot-chart" style="height: 300px;">
        <div class="flot-chart-content" id="chart-anfragen"></div>
    </div>
    <div class="table-responsive m-t-md">
        <table class="table table-striped table-bordered table-hover data-table-anfragen">
            <thead>{leads_thead}</thead>
            <tbody>{leads_tbody}</tbody>
        </table>
    </div>
"""

# --- Panel 2: Anzahl Baufileads ----------------------------------------------

l_counts = leads["counts"]
panel2_filters = f"""
    <div class="row m-b-sm">
        <div class="col-sm-3">{select_html("blcode", f1["blcode"])}</div>
        <div class="col-sm-3">{select_html("regioncode", f1["regioncode"])}</div>
        <div class="col-sm-3">{select_html("team_id", f1["team_id"])}</div>
        <div class="col-sm-1">
            <div class="input-group"><span class="input-group-addon">von</span>
                <input type="text" class="form-control input-sm datepicker" value="{FROM_DATE}"></div>
        </div>
        <div class="col-sm-2">
            <div class="input-group"><span class="input-group-addon">bis</span>
                <input type="text" class="form-control input-sm datepicker" value="{TO_DATE}"></div>
        </div>
    </div>
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("first", f1["first"])}</div>
    </div>
"""

panel2_body = f"""
    <div class="row m-b-md">
        <div class="col-sm-2"><h2 class="no-margins">{l_counts["all"]}</h2><small>gesamt</small></div>
        <div class="col-sm-2"><span class="label label-info">Erstzuw.: {l_counts["first1"]}</span></div>
        <div class="col-sm-3"><span class="label label-primary">Transfer (in): {l_counts["first0-in"]}</span></div>
        <div class="col-sm-3"><span class="label label-danger">Transfer (out): {l_counts["first0-out"]}</span></div>
    </div>
    {panel2_filters}
    <div class="flot-chart" style="height: 300px;">
        <div class="flot-chart-content" id="chart-leads"></div>
    </div>
    <div class="row m-t-md">
        <div class="col-lg-6">
            <div class="table-responsive">{leads["table"]["mails"]}</div>
        </div>
        <div class="col-lg-6">
            <div class="table-responsive">{leads["table"]["stat"]}</div>
        </div>
    </div>
"""

# --- Panels 3 & 4: Finanzzertifikate / Terminvereinbarungen (folded in) ------
# Same shape as panel 1: data1 = count + chart data, data3 = the raw lead rows.

def simple_leads_panel(body, forms, chart_id, table_class):
    d1 = body["data1"]
    thead = "<tr><th>Zeit</th><th>ID</th><th>Name Vorname</th><th>Empfänger</th><th>Sender</th><th>Antwort an</th><th>E-Mail-Text</th></tr>"
    rows = [row[:6] + [preview_text(row[6])] for row in body["data3"]["data"]]
    tbody = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    fsel = forms[0]["selects"]
    filters = f"""
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("regioncode", fsel["regioncode"])}</div>
        <div class="col-sm-3">{select_html("source", fsel["source"])}</div>
        <div class="col-sm-2">
            <div class="input-group"><span class="input-group-addon">von</span>
                <input type="text" class="form-control input-sm datepicker" value="{FROM_DATE}"></div>
        </div>
        <div class="col-sm-2">
            <div class="input-group"><span class="input-group-addon">bis</span>
                <input type="text" class="form-control input-sm datepicker" value="{TO_DATE}"></div>
        </div>
    </div>"""
    body_html = f"""
    <div class="row m-b-sm">
        <div class="col-sm-2"><h2 class="no-margins">{d1["count"]}</h2><small>gesamt</small></div>
    </div>
    {filters}
    <div class="flot-chart" style="height: 250px;">
        <div class="flot-chart-content" id="{chart_id}"></div>
    </div>
    <div class="table-responsive m-t-md">
        <table class="table table-striped table-bordered table-hover {table_class}">
            <thead>{thead}</thead>
            <tbody>{tbody}</tbody>
        </table>
    </div>
    """
    return body_html, d1["data"], d1["data"][-1][0]


panel3_body, finanzzert_data, finanzzert_last_t = simple_leads_panel(
    finanzzert, finanzzert_forms, "chart-finanzzert", "data-table-finanzzert"
)
panel4_body, terminvb_data, terminvb_last_t = simple_leads_panel(
    terminvb, terminvb_forms, "chart-terminvb", "data-table-terminvb"
)

# --- Sidebar / topbar / heading / footer (shared RI24 chrome) ----------------

SIDEBAR = """
<nav class="navbar-default navbar-static-side" role="navigation">
    <div class="sidebar-collapse">
        <ul class="nav metismenu" id="side-menu">
            <li class="nav-header">
                <div class="dropdown profile-element">
                    <span class="block m-t-xs font-bold">Regionalimmobilien24</span>
                    <span class="text-muted text-xs block">RI24 SEO Backend</span>
                </div>
            </li>
            <li class="active">
                <a href="#"><i class="fa fa-th-large"></i> <span class="nav-label">Dashboard</span> <span class="fa arrow"></span></a>
                <ul class="nav nav-second-level collapse in">
                    <li><a href="#">Makler</a></li>
                    <li class="active"><a href="#">Baufinanzierung</a></li>
                    <li><a href="#">Nutzer</a></li>
                    <li><a href="#">reCaptcha</a></li>
                </ul>
            </li>
            <li>
                <a href="#"><i class="fa fa-user"></i> <span class="nav-label">Makler</span> <span class="fa arrow"></span></a>
                <ul class="nav nav-second-level collapse">
                    <li><a href="#">Übersicht Makler</a></li>
                    <li><a href="#">Anfragen</a></li>
                    <li><a href="#">neuen Makler anlegen</a></li>
                    <li><a href="#">Kooperationen</a></li>
                    <li><a href="#">Makler umhängen</a></li>
                </ul>
            </li>
            <li><a href="#"><i class="fa fa-key"></i> <span class="nav-label">Nutzer</span></a></li>
            <li>
                <a href="#"><i class="fa fa-home"></i> <span class="nav-label">Objekte</span> <span class="fa arrow"></span></a>
                <ul class="nav nav-second-level collapse">
                    <li><a href="#">alle Objekte</a></li>
                    <li><a href="#">OID / Dubletten Check</a></li>
                </ul>
            </li>
            <li><a href="#"><i class="fa fa-font"></i> <span class="nav-label">Privatanzeigen</span></a></li>
            <li><a href="#"><i class="fa fa-globe"></i> <span class="nav-label">alle Regionen</span></a></li>
            <li>
                <a href="#"><i class="fa fa-envelope"></i> <span class="nav-label">Kontaktanfragen</span> <span class="fa arrow"></span></a>
                <ul class="nav nav-second-level collapse">
                    <li><a href="#">alle Kontaktanfragen</a></li>
                    <li><a href="#">E-Mail Liste</a></li>
                    <li><a href="#">Blacklist</a></li>
                </ul>
            </li>
            <li><a href="#"><i class="fa fa-users"></i> <span class="nav-label">Team</span></a></li>
            <li><a href="#"><i class="fa fa-users"></i> <span class="nav-label">Whitelabel-Lizenzen</span></a></li>
            <li><a href="#"><i class="fa fa-globe"></i> <span class="nav-label">Schnittstellen</span></a></li>
        </ul>
    </div>
</nav>
"""

TOPBAR = """
<div class="row border-bottom">
<nav class="navbar navbar-static-top" role="navigation" style="margin-bottom: 0">
    <div class="navbar-header">
        <a class="navbar-minimalize minimalize-styl-2 btn btn-primary" href="#"><i class="fa fa-bars"></i></a>
    </div>
    <ul class="nav navbar-top-links navbar-right">
        <li><a href="#"><i class="fa fa-sign-out"></i> Logout</a></li>
    </ul>
</nav>
</div>
"""

PAGE_HEADING = """
<div class="row wrapper border-bottom white-bg page-heading">
    <div class="col-lg-10">
        <h2>Dashboard - RI24 SEO</h2>
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="#">Home</a></li>
            <li class="breadcrumb-item"><a href="#">Dashboard</a></li>
            <li class="breadcrumb-item active"><strong>Baufi</strong></li>
        </ol>
    </div>
</div>
"""

FOOTER = """
<div class="footer">
    <div><strong>&copy; 2014 - 2026</strong> Regionalimmobilien24 GmbH</div>
</div>
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Baufi-Anfragen", panel1_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Baufileads", panel2_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Finanzzertifikate-Anfragen", panel3_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Terminvereinbarungen (calendly)", panel4_body)}</div></div>
</div>
"""

# --- Chart scripts ------------------------------------------------------------

anfragen_data = json.dumps(anfragen["data1"]["data"])
anfragen_last_t = anfragen["data1"]["data"][-1][0]

leads_times = leads["times"]
leads_series = leads["data"]
leads_colors = leads["colors"]
leads_series_js = json.dumps([
    {"label": s["label"], "data": s["data"], "color": leads_colors[i % len(leads_colors)]}
    for i, s in enumerate(leads_series)
])
leads_last_t = leads_series[0]["data"][-1][0]

SCRIPT = f"""
<script>
$(function () {{
    var anfragenData = {anfragen_data};
    $.plot('#chart-anfragen', [{{ data: anfragenData, color: '{FLOT_COLOR}', lines: {{ show: true, fill: 0.05 }}, points: {{ show: false }} }}], {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        grid: {{
            color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {anfragen_last_t}, to: {anfragen_last_t} }}, color: '#ED5565', lineWidth: 2 }}]
        }},
        tooltip: true
    }});

    var leadsSeries = {leads_series_js};
    $.plot('#chart-leads', leadsSeries, {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        legend: {{ position: 'nw' }},
        grid: {{
            color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {leads_last_t}, to: {leads_last_t} }}, color: '#ED5565', lineWidth: 2 }}]
        }},
        tooltip: true
    }});

    var finanzzertData = {json.dumps(finanzzert_data)};
    $.plot('#chart-finanzzert', [{{ data: finanzzertData, color: '{FLOT_COLOR}', lines: {{ show: true, fill: 0.05 }}, points: {{ show: false }} }}], {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        grid: {{
            color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {finanzzert_last_t}, to: {finanzzert_last_t} }}, color: '#ED5565', lineWidth: 2 }}]
        }},
        tooltip: true
    }});

    var terminvbData = {json.dumps(terminvb_data)};
    $.plot('#chart-terminvb', [{{ data: terminvbData, color: '{FLOT_COLOR}', lines: {{ show: true, fill: 0.05 }}, points: {{ show: false }} }}], {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        grid: {{
            color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {terminvb_last_t}, to: {terminvb_last_t} }}, color: '#ED5565', lineWidth: 2 }}]
        }},
        tooltip: true
    }});

    $('.data-table-anfragen').DataTable({{ pageLength: 10 }});
    $('.data-table-finanzzert').DataTable({{ pageLength: 10 }});
    $('.data-table-terminvb').DataTable({{ pageLength: 10 }});
    var sideBySideOpts = {{
        pageLength: 10,
        lengthChange: false,
        dom: 'ftip',
        language: {{ search: '', searchPlaceholder: 'Suchen…' }}
    }};
    $('.data-table-leads').DataTable(sideBySideOpts);
    $('.data-table-leads-stat').DataTable(sideBySideOpts);
}});
</script>
"""

HTML = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard - RI24 SEO</title>
<link href="assets/css/bootstrap.min.css" rel="stylesheet">
<link href="assets/font-awesome/css/font-awesome.css" rel="stylesheet">
<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">
<link href="assets/css/animate.css" rel="stylesheet">
<link href="assets/css/style.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-adaptation.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-colors.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-icons.css" rel="stylesheet">
<style>
  .prototype-banner {{ background:#2f4050; color:#fff; text-align:center; padding:6px 10px; font-size:12px; }}
  .prototype-banner strong {{ color:#1ab394; }}
  .data-table-leads, .data-table-leads-stat {{ font-size: 12px; }}
  .data-table-leads_wrapper .dataTables_paginate, .data-table-leads-stat_wrapper .dataTables_paginate {{ font-size: 12px; }}
  .data-table-leads_wrapper .paginate_button, .data-table-leads-stat_wrapper .paginate_button {{ padding: 0.3em 0.5em !important; }}
</style>
</head>
<body class="pitcom">
<div class="prototype-banner">
    <strong>Prototype</strong> — Dashboard &rarr; Baufi (/adm/individuell/master/dashboard/baufi/) rebuilt on the Inspinia theme, using real data captured from the live backend on 2026-09-10. "Anzahl Finanzzertifikate-Anfragen" and "Anzahl Terminvereinbarungen" folded in from Dashboard &rarr; Finanzzertifikate / Terminvereinbarungen, which are otherwise not being migrated as separate menu items.
</div>
<div id="wrapper">
    {SIDEBAR}
    <div id="page-wrapper" class="gray-bg dashbard-1">
        {TOPBAR}
        {PAGE_HEADING}
        {content}
        {FOOTER}
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
<script src="assets/js/plugins/dataTables/datatables.min.js"></script>
<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>
<script src="assets/js/inspinia.js"></script>
<script src="assets/js/plugins/pace/pace.min.js"></script>
<script>{DATATABLES_DE_JS}</script>
{SCRIPT}
</body>
</html>
"""

(BASE / "index.html").write_text(HTML, encoding="utf-8")
print("wrote", BASE / "index.html", len(HTML), "bytes")
