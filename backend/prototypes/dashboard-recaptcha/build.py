"""Generates index.html: the real 'Dashboard -> reCaptcha' backend screen
(/adm/individuell/master/dashboard/recaptcha/), rebuilt on the Inspinia theme
using real data captured from the live backend."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

forms = json.loads((SURVEY / "18-dashboard-recaptcha-forms.json").read_text(encoding="utf-8"))
failed = json.loads((SURVEY / "18-recaptcha-failed-body.json").read_text(encoding="utf-8"))

FLOT_COLOR = "#1ab394"
FROM_DATE = "10.08.2026"
TO_DATE = "10.09.2026"

regioncode_opts = forms[0]["selects"]["regioncode"]
source_opts = forms[0]["selects"]["source"]
action_opts = forms[1]["selects"]["action"]

# --- Panel 1: fehlergeschlagene reCaptcha (line chart + pie breakdown) -------

panel1_body = f"""
    <div class="row m-b-md">
        <div class="col-sm-3">{c.select_html("regioncode", regioncode_opts)}</div>
        <div class="col-sm-3">{c.select_html("source", source_opts)}</div>
        {c.date_range_cols(FROM_DATE, TO_DATE)}
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

# --- Panel 2: Fehlgeschlagene Mail-Anfragen durch reCaptcha (empty table) ----

panel2_body = f"""
    <div class="row m-b-sm">
        <div class="col-sm-2"><span class="label label-default">Anzahl: 0</span></div>
    </div>
    <div class="row m-b-md">
        <div class="col-sm-3">{c.select_html("regioncode", regioncode_opts)}</div>
        <div class="col-sm-3">{c.select_html("action", action_opts)}</div>
        {c.date_range_cols(FROM_DATE, TO_DATE)}
    </div>
    <div class="row m-b-md">
        <div class="col-sm-12">
            <label><input type="checkbox"> Alle anzeigen</label>
        </div>
    </div>
    <div class="table-responsive">
        <table class="table table-striped table-bordered">
            <thead>
                <tr>
                    <th>Regioncode</th><th>E-Mail</th><th>IP</th><th>Hostname</th>
                    <th>Aktion</th><th>Grund</th><th>Score</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row"><div class="col-lg-12">{c.ibox("fehlergeschlagene reCaptcha", panel1_body)}</div></div>
    <div class="row"><div class="col-lg-12">{c.ibox("Fehlgeschlagene Mail-Anfragen durch reCaptcha", panel2_body)}</div></div>
</div>
"""

# --- Charts -------------------------------------------------------------------

failed_data = json.dumps(failed["data1"]["data"])
failed_last_t = failed["data1"]["data"][-1][0]
pie_data = json.dumps([{"label": label, "data": int(count)} for label, count in failed["data3"]["data"]])

SCRIPT = f"""
<script>
$(function () {{
    var failedData = {failed_data};
    $.plot('#chart-recaptcha-failed', [{{ data: failedData, color: '{FLOT_COLOR}', lines: {{ show: true, fill: 0.05 }}, points: {{ show: false }} }}], {{
        xaxis: {{ mode: 'time', timeformat: '%d.%m.%y' }},
        yaxis: {{ tickDecimals: 0 }},
        grid: {{
            color: '#999999', hoverable: true, borderColor: '#f0f0f0', borderWidth: 1,
            markings: [{{ xaxis: {{ from: {failed_last_t}, to: {failed_last_t} }}, color: '#ED5565', lineWidth: 2 }}]
        }},
        tooltip: true
    }});

    var pieData = {pie_data};
    $.plot('#pie-recaptcha-failed', pieData, {{
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

html = c.page_shell(
    title="Dashboard - RI24 SEO",
    banner_html=c.prototype_banner("Dashboard &rarr; reCaptcha (/adm/individuell/master/dashboard/recaptcha/)"),
    content_html=c.page_heading("Dashboard - RI24 SEO", ["Home", "Dashboard", "Recaptcha"]) + content,
    active_dashboard_item="reCaptcha",
    extra_scripts=SCRIPT,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
