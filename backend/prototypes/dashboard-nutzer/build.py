"""Generates index.html: the real 'Dashboard -> Nutzer' backend screen,
rebuilt with the actual Inspinia theme assets (in assets/) and populated
with real data captured from the live backend (admin_survey/16-dashboard-nutzer-*.json).
"""
import json
from pathlib import Path
from urllib.parse import parse_qs

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

ajax = json.loads((SURVEY / "16-dashboard-nutzer-ajax.json").read_text(encoding="utf-8"))
forms = json.loads((SURVEY / "16-dashboard-nutzer-forms.json").read_text(encoding="utf-8"))
recaptcha_forms = json.loads((SURVEY / "18-dashboard-recaptcha-forms.json").read_text(encoding="utf-8"))
recaptcha_failed = json.loads((SURVEY / "18-recaptcha-failed-body.json").read_text(encoding="utf-8"))


def find_body(table):
    for c in ajax:
        pd = c.get("postData") or ""
        params = parse_qs(pd)
        if params.get("table", [""])[0] == table:
            return c["body"]
    raise KeyError(table)


user_account = find_body("statdashboard__user_account")
user_login = find_body("statdashboard__user_login")
searchagent = find_body("statdashboard__user_searchagent")
mail_searchagent = json.loads((SURVEY / "17-mail-searchagent-body.json").read_text(encoding="utf-8"))
mail_follow = json.loads((SURVEY / "17-mail-follow-body.json").read_text(encoding="utf-8"))

# Folded in from the (not-migrated) Dashboard -> Sitzungen screen — all 3 of
# its panels, since "Sitzungen" is being retired as its own menu item.
sitzungen_forms = json.loads((SURVEY / "19-dashboard-sitzungen-forms.json").read_text(encoding="utf-8"))
sitzungen_panel1 = json.loads((SURVEY / "19-sitzungen-panel1.json").read_text(encoding="utf-8"))  # Sitzungen (gruppiert)
sitzungen_panel2 = json.loads((SURVEY / "19-sitzungen-panel2.json").read_text(encoding="utf-8"))  # Klick auf Telefonnummern
sitzungen_panel3 = json.loads((SURVEY / "19-sitzungen-panel3.json").read_text(encoding="utf-8"))  # Referrer (komplett)
sf0, sf1, sf2 = sitzungen_forms[0]["selects"], sitzungen_forms[1]["selects"], sitzungen_forms[2]["selects"]
# form2's "source" select has 1261 real referrer-domain options; capped here
# since the full list isn't needed to review the layout.
sitzungen_source_opts_capped = sf2["source"][:60]
SITZUNGEN_FROM_DATE = "11.08.2026"

FLOT_COLOR = "#1ab394"
regioncode_opts = forms[0]["selects"]["regioncode"]
recaptcha_regioncode_opts = recaptcha_forms[0]["selects"]["regioncode"]
recaptcha_source_opts = recaptcha_forms[0]["selects"]["source"]

FROM_DATE = "10.08.2026"
TO_DATE = "10.09.2026"


def select_html(name, options, selected_value=""):
    opts = []
    for value, label, _sel in options:
        sel = " selected" if value == selected_value else ""
        opts.append(f'<option value="{value}"{sel}>{label}</option>')
    return f'<select name="{name}" class="form-control input-sm">' + "".join(opts) + "</select>"


def date_range_cols(from_date, to_date, von_cls="col-sm-2", bis_cls="col-sm-2"):
    return f"""
        <div class="{von_cls}">
            <div class="input-group"><span class="input-group-addon">von</span>
                <input type="text" class="form-control input-sm datepicker" value="{from_date}"></div>
        </div>
        <div class="{bis_cls}">
            <div class="input-group"><span class="input-group-addon">bis</span>
                <input type="text" class="form-control input-sm datepicker" value="{to_date}"></div>
        </div>"""


def sitzungen_counts_badges(counts):
    return f"""
    <div class="row m-b-md">
        <div class="col-sm-2"><h2 class="no-margins">{counts["all"]}</h2><small>Anzahl gesamt</small></div>
        <div class="col-sm-2"><span class="label" style="background:#34A853;color:#fff">Organisch: {counts["none"]}</span></div>
        <div class="col-sm-2"><span class="label" style="background:#EA4335;color:#fff">Google Ads: {counts["gads"]}</span></div>
        <div class="col-sm-2"><span class="label" style="background:#000;color:#fff">Referral: {counts["referral"]}</span></div>
        <div class="col-sm-2"><span class="label" style="background:#0866ff;color:#fff">Facebook: {counts["fb"]}</span></div>
    </div>"""


def filter_row():
    return f"""
    <div class="row m-b-sm">
        <div class="col-sm-8">{select_html("regioncode", regioncode_opts)}</div>
        <div class="col-sm-2">
            <div class="input-group"><span class="input-group-addon">von</span>
                <input type="text" class="form-control input-sm datepicker" value="{FROM_DATE}"></div>
        </div>
        <div class="col-sm-2">
            <div class="input-group"><span class="input-group-addon">bis</span>
                <input type="text" class="form-control input-sm datepicker" value="{TO_DATE}"></div>
        </div>
    </div>"""


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


panel1_body = f"""
    {filter_row()}
    <div class="flot-chart" style="height: 300px;"><div class="flot-chart-content" id="chart-account"></div></div>
"""

panel2_body = f"""
    <div class="row m-b-sm">
        <div class="col-sm-2"><span class="label label-default">Anzahl: {user_login["data1"]["count"]}</span></div>
    </div>
    {filter_row()}
    <div class="flot-chart" style="height: 300px;"><div class="flot-chart-content" id="chart-login"></div></div>
"""

panel3_body = f"""
    {filter_row()}
    <div class="flot-chart" style="height: 300px;"><div class="flot-chart-content" id="chart-searchagent"></div></div>
"""

# Folded in from the (not-migrated) Dashboard -> Mails screen: this is the
# only panel from there that's being kept, since it's really a Nutzer metric.
panel4_body = f"""
    <div class="row m-b-sm">
        <div class="col-sm-2"><span class="label label-default">Anzahl: {mail_searchagent["data1"]["count"]}</span></div>
    </div>
    {filter_row()}
    <div class="flot-chart" style="height: 300px;"><div class="flot-chart-content" id="chart-mail-searchagent"></div></div>
"""

panel5_body = f"""
    <div class="row m-b-sm">
        <div class="col-sm-2"><span class="label label-default">Anzahl: {mail_follow["data1"]["count"]}</span></div>
    </div>
    {filter_row()}
    <div class="flot-chart" style="height: 300px;"><div class="flot-chart-content" id="chart-mail-follow"></div></div>
"""

# --- Panels 6-8: folded in from Dashboard -> Sitzungen -----------------------

panel6_body = f"""
    {sitzungen_counts_badges(sitzungen_panel1["counts"])}
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("origin", sf0["origin"])}</div>
        <div class="col-sm-3">{select_html("referral", sf0["referral"], "grouped")}</div>
        <div class="col-sm-2">{select_html("regioncode", sf0["regioncode"])}</div>
        {date_range_cols(SITZUNGEN_FROM_DATE, TO_DATE)}
    </div>
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("oid_type", sf0["oid_type"])}</div>
    </div>
    <div class="flot-chart" style="height: 350px;"><div class="flot-chart-content" id="chart-sitzungen"></div></div>
"""

panel7_counts = sitzungen_panel2["counts"]
panel7_body = f"""
    <div class="row m-b-md">
        <div class="col-sm-2"><h2 class="no-margins">{panel7_counts["all"]}</h2><small>Anzahl gesamt</small></div>
        <div class="col-sm-2"><span class="label" style="background:#34A853;color:#fff">Organisch: {panel7_counts["none"]}</span></div>
        <div class="col-sm-2"><span class="label" style="background:#EA4335;color:#fff">Google Ads: {panel7_counts["gads"]}</span></div>
        <div class="col-sm-2"><span class="label" style="background:#000;color:#fff">Referral: {panel7_counts["referral"]}</span></div>
    </div>
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("origin", sf1["origin"])}</div>
        <div class="col-sm-3">{select_html("referral", sf1["referral"], "grouped")}</div>
        <div class="col-sm-2">{select_html("regioncode", sf1["regioncode"])}</div>
        {date_range_cols(SITZUNGEN_FROM_DATE, TO_DATE)}
    </div>
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("oid_type", sf1["oid_type"])}</div>
    </div>
    <div class="flot-chart" style="height: 300px;"><div class="flot-chart-content" id="chart-telcontact"></div></div>
"""

panel8_body = f"""
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("source", sitzungen_source_opts_capped)}</div>
        <div class="col-sm-3">{select_html("referral", sf2["referral"])}</div>
        <div class="col-sm-2">{select_html("regioncode", sf2["regioncode"])}</div>
        <div class="col-sm-2">{select_html("action", sf2["action"])}</div>
        <div class="col-sm-2">
            <div class="input-group"><span class="input-group-addon">min. Aufrufe</span>
                <input type="text" class="form-control input-sm" value="5"></div>
        </div>
    </div>
    <div class="row m-b-md">
        {date_range_cols(SITZUNGEN_FROM_DATE, TO_DATE, "col-sm-2", "col-sm-2")}
    </div>
    <div class="flot-chart" style="height: 350px;"><div class="flot-chart-content" id="chart-referrer"></div></div>
    <div id="legend-referrer" class="m-t-sm"></div>
"""

recaptcha_failed_data = json.dumps(recaptcha_failed["data1"]["data"])
recaptcha_failed_last_t = recaptcha_failed["data1"]["data"][-1][0]
recaptcha_pie_data = json.dumps([{"label": label, "data": int(count)} for label, count in recaptcha_failed["data3"]["data"]])

panel9_body = f"""
    <div class="row m-b-md">
        <div class="col-sm-3">{select_html("regioncode", recaptcha_regioncode_opts)}</div>
        <div class="col-sm-3">{select_html("source", recaptcha_source_opts)}</div>
        {date_range_cols(FROM_DATE, TO_DATE)}
    </div>
    <div class="row">
        <div class="col-lg-8">
            <div class="flot-chart" style="height: 300px;"><div class="flot-chart-content" id="chart-recaptcha-failed"></div></div>
        </div>
        <div class="col-lg-4">
            <div class="flot-chart-pie-content" id="pie-recaptcha-failed" style="height:300px;"></div>
        </div>
    </div>
"""

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
                    <li><a href="#">Baufinanzierung</a></li>
                    <li class="active"><a href="#">Nutzer</a></li>
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
            <li class="breadcrumb-item active"><strong>Nutzer</strong></li>
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
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Nutzerkonten", panel1_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl eingeloggter / aktiver Nutzer am Tag", panel2_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl aktiver Suchaufträge", panel3_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Suchauftrag Mails", panel4_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Anzahl Kaufobjekt Follow-Up Mails", panel5_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Sitzungen (gruppiert)", panel6_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Klick auf Telefonnummern (gruppiert)", panel7_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("Referrer (komplett)", panel8_body)}</div></div>
    <div class="row"><div class="col-lg-12">{ibox("fehlergeschlagene reCaptcha", panel9_body)}</div></div>
</div>
"""

# --- Chart scripts ------------------------------------------------------------

def chart_js(var, body, elem):
    data = body["data1"]["data"]
    last_t = data[-1][0]
    return f"""
    var {var} = {json.dumps(data)};
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

def multi_series_js(panel):
    colors = panel["colors"]
    series = [
        {"label": s["label"], "data": s["data"], "color": colors[i % len(colors)]}
        for i, s in enumerate(panel["data"])
    ]
    last_t = series[0]["data"][-1][0]
    return json.dumps(series), last_t


p6_series, p6_last = multi_series_js(sitzungen_panel1)
p7_series, p7_last = multi_series_js(sitzungen_panel2)
p8_series, p8_last = multi_series_js(sitzungen_panel3)

SCRIPT = f"""
<script>
$(function () {{
    {chart_js("accountData", user_account, "chart-account")}
    {chart_js("loginData", user_login, "chart-login")}
    {chart_js("searchagentData", searchagent, "chart-searchagent")}
    {chart_js("mailSearchagentData", mail_searchagent, "chart-mail-searchagent")}
    {chart_js("mailFollowData", mail_follow, "chart-mail-follow")}

    $.plot('#chart-sitzungen', {p6_series}, {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        legend: {{ position: 'nw' }},
        grid: {{ color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {p6_last}, to: {p6_last} }}, color: '#ED5565', lineWidth: 2 }}] }},
        tooltip: true
    }});

    $.plot('#chart-telcontact', {p7_series}, {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        legend: {{ position: 'nw' }},
        grid: {{ color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {p7_last}, to: {p7_last} }}, color: '#ED5565', lineWidth: 2 }}] }},
        tooltip: true
    }});

    $.plot('#chart-referrer', {p8_series}, {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        legend: {{ noColumns: 4, container: $('#legend-referrer') }},
        grid: {{ color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {p8_last}, to: {p8_last} }}, color: '#ED5565', lineWidth: 2 }}] }},
        tooltip: true
    }});

    var recaptchaData = {recaptcha_failed_data};
    $.plot('#chart-recaptcha-failed', [{{ data: recaptchaData, color: '{FLOT_COLOR}', lines: {{ show: true, fill: 0.05 }}, points: {{ show: false }} }}], {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        grid: {{
            color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {recaptcha_failed_last_t}, to: {recaptcha_failed_last_t} }}, color: '#ED5565', lineWidth: 2 }}]
        }},
        tooltip: true
    }});

    var recaptchaPieData = {recaptcha_pie_data};
    $.plot('#pie-recaptcha-failed', recaptchaPieData, {{
        series: {{
            pie: {{
                show: true,
                radius: 1,
                label: {{
                    show: true,
                    radius: 3/4,
                    formatter: function (label, series) {{
                        return "<div style='font-size:11px; text-align:center; padding:2px; color:#fff;'>" + label + "<br/>" + Math.round(series.percent) + "%</div>";
                    }},
                    background: {{ opacity: 0.6 }}
                }}
            }}
        }},
        legend: {{ show: false }}
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
  .prototype-banner {{ background:#2f4050; color:#fff; text-align:center; padding:6px 10px; font-size:12px; }}
  .prototype-banner strong {{ color:#1ab394; }}
</style>
</head>
<body class="pitcom">
<div class="prototype-banner">
    <strong>Prototype</strong> — Dashboard &rarr; Nutzer (/adm/individuell/master/dashboard/user/) rebuilt on the Inspinia theme, using real data captured from the live backend on 2026-09-10. "Anzahl Suchauftrag Mails" and "Anzahl Kaufobjekt Follow-Up Mails" folded in from Dashboard &rarr; Mails; all 3 Sitzungen panels folded in from Dashboard &rarr; Sitzungen; "fehlergeschlagene reCaptcha" panel folded in from Dashboard &rarr; reCaptcha — none of these are being migrated as separate menu items.
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
