"""Generates index.html: the real 'Seiten - <Region>' screen
(/adm/individuell/regionen/edit_region_sites.php?regio=aai24), rebuilt on
the Inspinia theme with all real rows captured for the example region
Aachen-Eifel (aai24): 23 Hauptnavigation rows, 3 Servicenavigation rows,
10 "Seiten ohne Zuordnung" rows, and 24 Städte rows (with inline
Kaufobjekte / Mietobjekte / Baufinanzierung sub-tables per city).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "39-regionen-seiten-data.json").read_text(encoding="utf-8"))


def name_cell(entry):
    pfad = entry["pfad"] or "&mdash;"
    return f'{entry["name"]}<br><small class="text-muted">{pfad}</small>'


def rows_html(entries, has_sortierung):
    out = []
    for e in entries:
        cells = [
            f'<a href="{e["view_href"]}" target="_blank" class="btn btn-default btn-xs" title="Seite aufrufen"><i class="fa fa-external-link"></i></a>',
            name_cell(e),
        ]
        if has_sortierung:
            cells.append(e["sortierung"])
        cells.append(e["sektionen"])
        cells.append('<a href="../regionen-seite-bearbeiten/index.html" class="btn btn-default btn-xs" title="bearbeiten"><i class="fa fa-pencil"></i></a>')
        out.append("<tr>" + "".join(f"<td>{c_}</td>" for c_ in cells) + "</tr>")
    return "".join(out)


def table_html(entries, has_sortierung, css_class):
    cols = ["Seite aufrufen", "Ebene / Bezeichnung &middot; Pfad"]
    if has_sortierung:
        cols.append("Sortierung")
    cols += ["Sektionen / Elemente", "bearbeiten"]
    thead = "<tr>" + "".join(f"<th>{h}</th>" for h in cols) + "</tr>"
    return f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover {css_class}">
        <thead>{thead}</thead>
        <tbody>{rows_html(entries, has_sortierung)}</tbody>
    </table>
</div>
"""


# --- Städte data -------------------------------------------------------------

STAEDTE = [
    "Aachen", "Alsdorf", "Bad Münstereifel", "Baesweiler", "Dahlem",
    "Düren", "Eschweiler", "Euskirchen", "Heimbach", "Herzogenrath",
    "Hürtgenwald", "Jülich", "Kall", "Kreuzau", "Linnich",
    "Mechernich", "Monschau", "Netterheim", "Nideggen", "Schleiden",
    "Stolberg", "Weilerswist", "Würselen", "Zülpich",
]

KAUFOBJEKTE_ITEMS = [
    ("Eigentumswohnungen", "eigentumswohnungen"),
    ("Häuser kaufen", "haeuser-kaufen"),
    ("Grundstücke kaufen", "grundstuecke-kaufen"),
    ("Garagen / Stellplätze", "garagen-stellplaetze"),
    ("Anlageobjekte", "anlageobjekte"),
    ("Neubau", "neubau"),
    ("sonstige Wohnobjekte", "sonstige-wohnobjekte"),
    ("Zwangsversteigerungen", "zwangsversteigerungen"),
    ("Büro / Praxen", "buero-praxen"),
    ("Hallen / Produktion", "hallen-produktion"),
    ("Einzelhandel", "einzelhandel"),
    ("Gastronomie / Hotels", "gastronomie-hotels"),
    ("Gewerbegrundstücke", "gewerbegrundstüche"),
    ("sonstige Gewerbeobjekte", "sonstige-gewerbeobjekte"),
    ("gewerbliche Zwangsversteigerungen", "gewerbliche-zwangsversteigerungen"),
]

MIETOBJEKTE_ITEMS = [
    ("Mietwohnungen", "mietwohnungen"),
    ("Haus mieten", "haus-mieten"),
    ("Grundstück pachten", "grundstück-pachten"),
    ("Garage / Stellplätze", "garage-stellplaetze"),
    ("Seniorenwohnen", "seniorenwohnen"),
    ("Wohnen auf Zeit", "wohnen-auf-zeit"),
    ("WG-Zimmer", "wg-zimmer"),
    ("Sonstige Wohnobjekte", "sonstige-wohnobjekte"),
    ("Büros / Praxen", "bueros-praxen"),
    ("Hallen / Produktion", "hallen-produktion"),
    ("Einzelhandel", "einzelhandel"),
    ("Gastronomie / Hotels", "gastronomie-hotels"),
    ("Gewerbegrundstücke", "gewerbegrundstüche"),
    ("Sonstige Gewerbeobjekte", "sonstige-gewerbeobjekte"),
]

BAUFINANZIERUNG_ITEMS = [
    ("Baufinanzierung", "baufinanzierung"),
]


def _city_pfad(name):
    s = name.lower()
    for k, v in [("ä","ae"),("ö","oe"),("ü","ue"),("ß","ss")]:
        s = s.replace(k, v)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def sub_item_rows_html(items):
    out = []
    for i, (name, pfad) in enumerate(items, 1):
        out.append(
            "<tr>"
            '<td><a href="#" class="btn btn-default btn-xs" title="Seite aufrufen">'
            '<i class="fa fa-external-link"></i></a></td>'
            f"<td>{name}<br><small class=\"text-muted\">/{pfad}/</small></td>"
            f"<td>{i}</td>"
            "<td>3 / 4</td>"
            '<td><a href="../regionen-seite-bearbeiten/index.html" '
            'class="btn btn-default btn-xs" title="bearbeiten">'
            '<i class="fa fa-pencil"></i></a></td>'
            "</tr>"
        )
    return "".join(out)


def sub_table_html_inner(items):
    cols = ["Seite aufrufen", "Bezeichnung · Pfad", "Sortierung",
            "Sektionen / Elemente", "bearbeiten"]
    thead = "<tr>" + "".join(f"<th>{h}</th>" for h in cols) + "</tr>"
    return (
        '<div class="table-responsive">'
        '<table class="table table-striped table-bordered table-hover sub-seiten-table">'
        f"<thead>{thead}</thead>"
        f"<tbody>{sub_item_rows_html(items)}</tbody>"
        "</table></div>"
    )


# Pre-compute sub-iboxes (same content for all cities — prototype pattern)
_kauf_ibox = c.ibox("Kaufobjekte", sub_table_html_inner(KAUFOBJEKTE_ITEMS))
_miet_ibox = c.ibox("Mietobjekte", sub_table_html_inner(MIETOBJEKTE_ITEMS))
_baufi_ibox = c.ibox("Baufinanzierung", sub_table_html_inner(BAUFINANZIERUNG_ITEMS))

_staedte_rows = []
for _i, _stadt in enumerate(STAEDTE):
    _slug = f"stadt-{_i}"
    _pfad = _city_pfad(_stadt)
    _collapse_cls = "collapse in" if _i == 0 else "collapse"
    _staedte_rows.append(
        f"<tr>"
        f'<td><a href="#" class="btn btn-default btn-xs" title="Seite aufrufen">'
        f'<i class="fa fa-external-link"></i></a></td>'
        f"<td><strong>{_stadt}</strong><br>"
        f'<small class="text-muted">/{_pfad}/</small></td>'
        f"<td>{_i + 1}</td>"
        f"<td>3 / 5</td>"
        f'<td><a href="#{_slug}" data-toggle="collapse" '
        f'class="btn btn-default btn-xs" title="Seiten bearbeiten">'
        f'<i class="fa fa-pencil"></i></a></td>'
        f"</tr>"
        f'<tr class="staedte-sub-row">'
        f'<td colspan="5" class="staedte-sub-td">'
        f'<div id="{_slug}" class="{_collapse_cls}">'
        f'<div class="row" style="padding:10px 15px 0;">'
        f'<div class="col-lg-4">{_kauf_ibox}</div>'
        f'<div class="col-lg-4">{_miet_ibox}</div>'
        f'<div class="col-lg-4">{_baufi_ibox}</div>'
        f"</div></div></td></tr>"
    )

staedte_cols = ["Seite aufrufen", "Bezeichnung · Pfad", "Sortierung",
                "Sektionen / Elemente", "bearbeiten"]
staedte_thead = "<tr>" + "".join(f"<th>{h}</th>" for h in staedte_cols) + "</tr>"
staedte_html = (
    '<div class="table-responsive">'
    '<table class="table table-striped table-bordered table-hover" id="staedte-table">'
    f"<thead>{staedte_thead}</thead>"
    f"<tbody>{''.join(_staedte_rows)}</tbody>"
    "</table></div>"
)

# --- Build existing sections -------------------------------------------------

hauptnav_html = table_html(data["hauptnavigation"], True, "data-table-hauptnav")
servicenav_html = table_html(data["servicenavigation"], True, "data-table-servicenav")
ohne_zuordnung_html = table_html(data["seiten_ohne_zuordnung"], False, "data-table-ohne-zuordnung")

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-6">{c.ibox("Hauptnavigation", hauptnav_html)}</div>
        <div class="col-lg-6">
            {c.ibox("Servicenavigation", servicenav_html)}
            {c.ibox("Seiten ohne Zuordnung", ohne_zuordnung_html)}
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">{c.ibox("Städte", staedte_html)}</div>
    </div>
</div>
"""

SCRIPT = """
<script>
$(function () {
    ['.data-table-hauptnav', '.data-table-servicenav', '.data-table-ohne-zuordnung'].forEach(function (sel) {
        $(sel).DataTable({
            pageLength: 10,
            autoWidth: false,
            columnDefs: [ { targets: [0, -1], orderable: false, width: '40px' } ]
        });
    });
});
</script>
"""

html = c.page_shell(
    title="Seiten - Aachen-Eifelimmobilien24 - RI24 SEO",
    banner_html=c.prototype_banner(
        "Seiten (/adm/.../regionen/edit_region_sites.php?regio=aai24)",
        "All real rows for Aachen-Eifel (aai24): 23 Hauptnavigation, 3 Servicenavigation, 10 Seiten ohne Zuordnung, 24 Städte. "
        "Pencil icon on each city expands inline Kaufobjekte / Mietobjekte / Baufinanzierung sub-tables (Aachen pre-expanded). Sub-table content is illustrative.",
    ),
    content_html=c.page_heading("Seiten - Aachen-Eifelimmobilien24", ["Home", "alle Regionen", "regionale Seiten - Aachen-Eifelimmobilien24"]) + content,
    extra_head=(
        '<link href="assets/css/plugins/dataTables/datatables.min.css" rel="stylesheet">\n'
        "<style>\n"
        "  .data-table-hauptnav thead th, .data-table-servicenav thead th, .data-table-ohne-zuordnung thead th { background-color: #333333 !important; text-align: left !important; font-size: 12px !important; }\n"
        "  .data-table-hauptnav thead th.sorting, .data-table-servicenav thead th.sorting, .data-table-ohne-zuordnung thead th.sorting,\n"
        "  .data-table-hauptnav thead th.sorting_asc, .data-table-servicenav thead th.sorting_asc, .data-table-ohne-zuordnung thead th.sorting_asc,\n"
        "  .data-table-hauptnav thead th.sorting_desc, .data-table-servicenav thead th.sorting_desc, .data-table-ohne-zuordnung thead th.sorting_desc { padding-right: 8px !important; padding-left: 8px !important; padding-top: 12px !important; padding-bottom: 22px !important; }\n"
        "  .data-table-hauptnav thead .sorting:after, .data-table-servicenav thead .sorting:after, .data-table-ohne-zuordnung thead .sorting:after,\n"
        "  .data-table-hauptnav thead .sorting_asc:after, .data-table-servicenav thead .sorting_asc:after, .data-table-ohne-zuordnung thead .sorting_asc:after,\n"
        "  .data-table-hauptnav thead .sorting_desc:after, .data-table-servicenav thead .sorting_desc:after, .data-table-ohne-zuordnung thead .sorting_desc:after { left: 8px !important; right: auto !important; bottom: 6px !important; }\n"
        "  #staedte-table thead th { background-color: #333333 !important; font-size: 12px !important; }\n"
        "  #staedte-table > tbody > .staedte-sub-row > .staedte-sub-td { padding: 0 !important; border-top: 0 !important; background-color: #f8f8f8 !important; }\n"
        "  .sub-seiten-table thead th { background-color: #4a4a4a !important; font-size: 11px !important; }\n"
        "  .sub-seiten-table { font-size: 12px; }\n"
        "</style>"
    ),
    extra_scripts=(
        '<script src="assets/js/plugins/dataTables/datatables.min.js"></script>\n'
        '<script src="assets/js/plugins/dataTables/dataTables.bootstrap4.min.js"></script>\n'
        f'<script>{c.DATATABLES_DE_JS}</script>\n'
        + SCRIPT
    ),
    active_top_item="alle Regionen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
