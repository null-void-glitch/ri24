"""Generates index.html: the real 'Dashboard -> Makler' backend screen,
rebuilt with the actual Inspinia theme assets (in assets/) and populated
with real data captured from the live backend (admin_survey/14-dashboard-makler-*.json).
"""
import json
import re
from pathlib import Path
from urllib.parse import parse_qs

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

ajax = json.loads((SURVEY / "14-dashboard-makler-ajax2.json").read_text(encoding="utf-8"))
forms = json.loads((SURVEY / "14-dashboard-makler-forms.json").read_text(encoding="utf-8"))

# --- Pull the real series out of the captured AJAX responses -----------------

def find_body(table, source=None):
    for c in ajax:
        pd = c.get("postData") or ""
        params = parse_qs(pd)
        if params.get("table", [""])[0] != table:
            continue
        if source is not None and params.get("source", [""])[0] != source:
            continue
        return c["body"]
    raise KeyError((table, source))

contact = find_body("statdashboard__contact")
makler = find_body("statdashboard__makler")
own_objects = find_body("statdashboard__makler_objects", "intern")
ext_objects = find_body("statdashboard__makler_objects", "extern")
multi_objects = find_body("statdashboard__makler_objects", "multimakler")
immocount = find_body("statdashboard__immocount")

FLOT_COLOR = "#1ab394"  # inspinia teal used throughout its flot demos


def series_js(body, color=FLOT_COLOR):
    data = body["data1"]["data"]
    last_t = data[-1][0]
    return json.dumps(data), last_t


def select_html(name, options, selected_value=""):
    opts = []
    for value, label, _sel in options:
        sel = " selected" if value == selected_value else ""
        opts.append(f'<option value="{value}"{sel}>{label}</option>')
    return f'<select name="{name}" class="form-control input-sm">' + "".join(opts) + "</select>"


f0 = forms[0]["selects"]
regioncode_opts = f0["regioncode"]
source_opts = f0["source"]
va_opts = f0["va"]
origin_opts = f0["origin"]
immo_origin_opts = forms[4]["selects"]["origin"]

FROM_DATE = "10.08.2026"
TO_DATE = "10.09.2026"


def filter_row(extra_selects=""):
    return f"""
    <div class="row m-b-sm">
        <div class="col-sm-8">
            {select_html("regioncode", regioncode_opts)}
            {extra_selects}
        </div>
        <div class="col-sm-2">
            <div class="input-group">
                <span class="input-group-addon">von</span>
                <input type="text" class="form-control input-sm datepicker" name="from" value="{FROM_DATE}">
            </div>
        </div>
        <div class="col-sm-2">
            <div class="input-group">
                <span class="input-group-addon">bis</span>
                <input type="text" class="form-control input-sm datepicker" name="to" value="{TO_DATE}">
            </div>
        </div>
    </div>"""


def ibox(title, tools_extra, body_html):
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


# --- Panel 1: Anzahl Kontaktanfragen (has counter badges) ---------------------

counts = contact["data1"]["counts"]
contact_filters = (
    select_html("source", source_opts)
    + select_html("va", va_opts)
    + '<div class="m-t-sm">'
    + select_html("origin", origin_opts)
    + "</div>"
)
panel1_body = f"""
    <div class="row m-b-sm">
        <div class="col-sm-2"><h2 class="no-margins">{contact["data1"]["count"]}</h2><small>gesamt</small></div>
    </div>
    {filter_row(contact_filters)}
    <div class="row m-b-md">
        <div class="col-sm-3"><span class="label label-success">Organisch: {counts["none"]}</span></div>
        <div class="col-sm-3"><span class="label label-info">Google Ads: {counts["gads"]}</span></div>
        <div class="col-sm-3"><span class="label label-primary">Facebook: {counts["fb"]}</span></div>
        <div class="col-sm-3"><span class="label label-warning">Referral: {counts["referral"]}</span></div>
    </div>
    <div class="flot-chart">
        <div class="flot-chart-content" id="chart-contact"></div>
    </div>
"""

# --- Panels 2-4, 6-7: plain regioncode filter + line chart --------------------

panel2_body = f"""
    {filter_row()}
    <div class="flot-chart"><div class="flot-chart-content" id="chart-makler"></div></div>
"""

panel3_body = f"""
    {filter_row()}
    <div class="flot-chart"><div class="flot-chart-content" id="chart-own"></div></div>
"""

panel4_body = f"""
    {filter_row()}
    <div class="flot-chart"><div class="flot-chart-content" id="chart-ext"></div></div>
"""

# --- Panel 5: Anzahl aktiver Immobilien (table + multi-series chart) ---------

SOURCE_LABELS = {
    "all": "gesamt",
    "intern": "Intern",
    "immode": "immobilien.de",
    "wohnungjetzt": "wohnung-jetzt.de",
    "classmarkets": "classmarkets",
    "immobilienpool": "immobilienpool",
    "versteigerungspool": "versteigerungspool",
    "wohnglueck": "Wohnglück",
    "spotahome": "Spot A Home",
}
c1, c2, c3 = immocount["counts"], immocount["counts2"], immocount["counts3"]
table_rows = []
for key in ["all", "intern", "immode", "wohnungjetzt", "classmarkets", "immobilienpool", "versteigerungspool", "wohnglueck", "spotahome"]:
    label = SOURCE_LABELS[key]
    online = c1.get(key, "")
    letzte = c2.get(key, "")
    rate = c3.get(key, "")
    style = ' style="font-weight:bold;"' if key == "all" else ""
    table_rows.append(
        f"<tr{style}><td>{label}</td><td>{online}</td><td>{letzte}</td><td>{rate}</td></tr>"
    )

panel5_body = f"""
    {filter_row()}
    <table class="table table-striped m-b-md">
        <thead><tr><th>Quelle</th><th>online</th><th>letzte Lieferung</th><th>Onlinerate</th></tr></thead>
        <tbody>{''.join(table_rows)}</tbody>
    </table>
    <div class="flot-chart" style="height: 350px;">
        <div class="flot-chart-content" id="chart-immocount"></div>
    </div>
"""

# --- Panel 6: Anzahl aktiver Multilisting Objekte -----------------------------

panel6_body = f"""
    {filter_row()}
    <div class="flot-chart"><div class="flot-chart-content" id="chart-multi"></div></div>
"""

# --- Sidebar (real RI24 nav, Inspinia metisMenu markup) -----------------------

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
                    <li class="active"><a href="#">Makler</a></li>
                    <li><a href="#">Baufinanzierung</a></li>
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
            <li class="breadcrumb-item active"><strong>Makler</strong></li>
        </ol>
    </div>
</div>
"""

FOOTER = """
<div class="footer">
    <div>
        <strong>&copy; 2014 - 2026</strong> Regionalimmobilien24 GmbH
    </div>
</div>
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Kontaktanfragen", "", panel1_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Makler", "", panel2_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl aktiver eigener Objekte", "", panel3_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl aktiver Fremdobjekte", "", panel4_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl aktiver Immobilien", "", panel5_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl aktiver Multilisting Objekte", "", panel6_body)}</div></div>
</div>
"""

# --- Chart data & flot init script --------------------------------------------

def chart_js(var, body, elem):
    data, last_t = series_js(body)
    return f"""
    var {var} = {data};
    $.plot('#{elem}', [{{ data: {var}, color: '{FLOT_COLOR}', lines: {{ show: true, fill: 0.05 }}, points: {{ show: false }} }}], {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        grid: {{
            color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {last_t}, to: {last_t} }}, color: '#ED5565', lineWidth: 2 }}]
        }},
        tooltip: true
    }});
"""

immo_times, immo_series = immocount["times"], immocount["data"]
immo_colors = immocount["colors"]
immo_series_js = json.dumps([
    {"label": s["label"], "data": s["data"], "color": immo_colors[i % len(immo_colors)]}
    for i, s in enumerate(immo_series)
])
last_immo_t = immo_series[0]["data"][-1][0]

SCRIPT = f"""
<script>
$(function () {{
    {chart_js("contactData", contact, "chart-contact")}
    {chart_js("maklerData", makler, "chart-makler")}
    {chart_js("ownData", own_objects, "chart-own")}
    {chart_js("extData", ext_objects, "chart-ext")}
    {chart_js("multiData", multi_objects, "chart-multi")}

    var immoSeries = {immo_series_js};
    $.plot('#chart-immocount', immoSeries, {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        legend: {{ position: 'nw', noColumns: 2 }},
        grid: {{
            color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {last_immo_t}, to: {last_immo_t} }}, color: '#ED5565', lineWidth: 2 }}]
        }},
        tooltip: true
    }});
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
<link href="assets/css/animate.css" rel="stylesheet">
<link href="assets/css/style.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-adaptation.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-colors.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-icons.css" rel="stylesheet">
<style>
  /* Prototype note banner — not part of the Inspinia theme itself */
  .prototype-banner {{ background:#2f4050; color:#fff; text-align:center; padding:6px 10px; font-size:12px; }}
  .prototype-banner strong {{ color:#1ab394; }}
</style>
</head>
<body class="pitcom">
<div class="prototype-banner">
    <strong>Prototype</strong> — Dashboard &rarr; Makler (/adm/individuell/master/dashboard/makler/) rebuilt on the Inspinia theme, using real data captured from the live backend on 2026-09-10.
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
<script src="assets/js/inspinia.js"></script>
<script src="assets/js/plugins/pace/pace.min.js"></script>
{SCRIPT}
</body>
</html>
"""

(BASE / "index.html").write_text(HTML, encoding="utf-8")
print("wrote", BASE / "index.html", len(HTML), "bytes")
