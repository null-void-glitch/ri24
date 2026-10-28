"""Generates index.html: the real 'OID Immo-Recherche'
(/adm/individuell/master/tools/oid-recherche/) and 'Immo Dubletten-Check'
(/adm/individuell/master/tools/immo-dubletten-check/) tool screens,
consolidated onto one page under Objekte -> "OID / Dubletten Check" (both
were previously separate Dashboard sub-menu items — see prototypes/objekte/
for the new Objekte sub-menu that replaces those two entries). Neither tool
has chart/table data on the live site — both are single static lookup/
comparison forms, side by side here since together they fit comfortably on
one screen.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent

oid_body = """
    <label class="control-label" style="display:block; font-weight:600; margin-bottom:6px;">
        Objekt-ID Liste<br><small class="text-muted">(je Zeile eine OID)</small>
    </label>
    <textarea class="form-control" rows="6"></textarea>
    <div class="m-t-md">
        <button type="submit" class="btn btn-primary">suchen</button>
    </div>
"""

dubletten_body = """
    <div class="row">
        <div class="col-sm-6">
            <label class="control-label" style="display:block; font-weight:600; margin-bottom:6px;">Objekt-ID (1)</label>
            <input type="text" class="form-control">
        </div>
        <div class="col-sm-6">
            <label class="control-label" style="display:block; font-weight:600; margin-bottom:6px;">Objekt-ID (2)</label>
            <input type="text" class="form-control">
        </div>
    </div>
    <div class="m-t-md">
        <button type="submit" class="btn btn-primary">vergleichen</button>
    </div>
"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-6">{c.ibox("OID Immo-Recherche", oid_body)}</div>
        <div class="col-lg-6">{c.ibox("Dubletten-Check", dubletten_body)}</div>
    </div>
</div>
"""

html = c.page_shell(
    title="OID / Dubletten Check - RI24 SEO",
    banner_html=c.prototype_banner(
        "OID Immo-Recherche + Immo Dubletten-Check (previously separate Dashboard sub-menu items)",
        "Both tools consolidated onto one page under Objekte → \"OID / Dubletten Check\".",
    ),
    content_html=c.page_heading("OID / Dubletten Check", ["Home", "Objekte", "OID / Dubletten Check"]) + content,
    active_objekte_item="OID / Dubletten Check",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
