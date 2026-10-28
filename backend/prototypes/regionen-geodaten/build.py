"""Generates index.html: the real 'Geodaten bearbeiten' screen
(/adm/individuell/regionen/config/geodaten/?regio=aai24), rebuilt on the
Inspinia theme with real field data captured for the example region
Aachen-Eifel (aai24). Reached from alle Regionen's "Geodaten anpassen"
button, now also in the sidebar sub-menu directly.

The live page's bounding-box preview is a static theme illustration image
(ressource/img/adm/latlon.jpg, a generic lat/lon diagram, not an actual map
tied to these coordinates) — not bundled with this prototype's asset set,
replaced with an equivalent text placeholder rather than a broken image.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent

ZOOM_OPTIONS = [str(z) for z in range(4, 18)]
zoom_select = "".join(
    f'<option value="{z}"{" selected" if z == "10" else ""}>{z}</option>' for z in ZOOM_OPTIONS
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

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-4">{c.ibox("Mittelpunkt / Zoomstufe", mittelpunkt_body)}</div>
        <div class="col-lg-4">{c.ibox("Bounding Box", bbox_body)}</div>
        <div class="col-lg-4">{c.ibox("Daten speichern", speichern_body)}</div>
    </div>
</div>
"""

html = c.page_shell(
    title="Geodaten für Aachen-Eifelimmobilien24 (AAI24) bearbeiten - RI24 SEO",
    banner_html=c.prototype_banner(
        "Geodaten bearbeiten (/adm/.../regionen/config/geodaten/?regio=aai24)",
        "Real field data for the example region Aachen-Eifel (aai24). The live bounding-box preview image is replaced with a text placeholder — see build.py docstring.",
    ),
    content_html=c.page_heading("Geodaten für Aachen-Eifelimmobilien24 (AAI24) bearbeiten", ["Home", "alle Regionen", "AAI24", "Geodaten bearbeiten"]) + content,
    active_top_item="alle Regionen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
