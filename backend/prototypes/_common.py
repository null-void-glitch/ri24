"""Shared chrome (sidebar/topbar/heading/footer) + small helpers reused across
the RI24 -> Inspinia dashboard prototypes. Import from a sibling build.py via:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import _common as c
"""
import json

# Standard German DataTables translation (datatables.net/plug-ins/i18n/German).
# Set once as the plugin default so every $(...).DataTable() call on the page
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

DASHBOARD_SUBITEMS = [
    ("Makler", None),
    ("Baufinanzierung", None),
    ("Nutzer", None),
]

# "Übersicht Makler" + "Kurzliste Makler" consolidated into one item — see
# prototypes/makler-uebersicht/build.py for the merged screen.
MAKLER_SUBITEMS = [
    "Übersicht Makler",
    "Anfragen",
    "neuen Makler anlegen",
]

KOOPERATIONEN_SUBITEMS = [
    ("Übersicht", "../makler-kooperationen/index.html"),
    ("neue Kooperation", "../makler-kooperationen-new/index.html"),
]

# "OID Immo-Recherche" + "Immo Dubletten-Check" moved here from the Dashboard
# submenu and consolidated into one page — see
# prototypes/tools-oid-dubletten/build.py.
OBJEKTE_SUBITEMS = [
    "alle Objekte",
    "OID / Dubletten Check",
]

# The real "alle Regionen" screen (/adm/individuell/regionen/config/) is a
# flat link with no sidebar submenu on the live site — each region row's 5
# "anpassen"/"setzen" action buttons lead to these sub-screens instead. A
# sidebar submenu is added here (same treatment as Objekte) so they're all
# reachable directly, not just via a specific region's row.

TOP_LEVEL_ITEMS = [
    ("fa-user", "Makler", None, True),
    ("fa-key", "Nutzer", None, False),
    ("fa-home", "Objekte", None, False),
    ("fa-font", "Privatanzeigen", None, False),
    ("fa-globe", "alle Regionen", None, False),
    ("fa-map-marker", "Baufi/Immo-Orte", None, False),
    ("fa-laptop", "statische Seiten (überregional)", None, False),
    ("fa-envelope", "Kontaktanfragen", None, True),
    ("fa-users", "Team", None, False),
    ("fa-users", "Whitelabel-Lizenzen", None, False),
    ("fa-search", "Suchaufträge", None, False),
    ("fa-globe", "Schnittstellen", None, False),
    ("fa-line-chart", "SEO", None, False),
    ("fa-microphone", "Immobilienassistent", None, False),
    ("fa-question-circle", "Hilfe", None, False),
]


def sidebar(active_dashboard_item=None, breadcrumb_under_dashboard=True, active_makler_item=None, active_top_item=None, active_objekte_item=None, active_kontakt_item=None, active_schnittstellen_item=None, active_kooperationen_item=None):
    """Sidebar with the real RI24 nav.
    `active_dashboard_item` is one of the labels in DASHBOARD_SUBITEMS.
    `active_makler_item` is one of the labels in MAKLER_SUBITEMS.
    `active_top_item` is a flat top-level nav label (e.g. "Nutzer", "alle Regionen").
    `active_objekte_item` is one of the labels in OBJEKTE_SUBITEMS.
    `active_kontakt_item` is one of the Kontaktanfragen sub-labels.
    Exactly one section is expanded/highlighted, based on whichever
    argument is set."""
    _dash_hrefs = {
        "Makler":         "../dashboard-makler/index.html",
        "Baufinanzierung":"../dashboard-baufi/index.html",
        "Nutzer":         "../dashboard-nutzer/index.html",
    }
    sub_items = []
    for label, _ in DASHBOARD_SUBITEMS:
        cls = ' class="active"' if label == active_dashboard_item else ""
        href = _dash_hrefs.get(label, "#")
        sub_items.append(f'<li{cls}><a href="{href}">{label}</a></li>')

    makler_active_section = active_makler_item is not None
    objekte_active_section = active_objekte_item is not None
    kontakt_active_section = active_kontakt_item is not None
    schnittstellen_active_section = active_schnittstellen_item is not None
    kooperationen_active_section = active_kooperationen_item is not None or active_top_item == "Kooperationen"
    other_section_active = makler_active_section or objekte_active_section or kontakt_active_section or schnittstellen_active_section or kooperationen_active_section
    dash_active = ' class="active"' if breadcrumb_under_dashboard and not other_section_active else ""

    kontakt_active = active_top_item == "Kontaktanfragen" or kontakt_active_section
    schnittstellen_active = active_top_item == "Schnittstellen" or schnittstellen_active_section
    _schnittstellen_items = [
        ("Sitemaps (Mitula)", "../schnittstellen-sitemaps/index.html"),
        ("Statischer Immobilien Export", "../schnittstellen-export/index.html"),
    ]
    _schnittstellen_lis = "".join(
        f'<li{" class=\"active\"" if label == active_schnittstellen_item else ""}><a href="{href}">{label}</a></li>'
        for label, href in _schnittstellen_items
    )
    schnittstellen_sub = f"""
                <ul class="nav nav-second-level collapse{' in' if schnittstellen_active else ''}">
                    {_schnittstellen_lis}
                </ul>"""

    _kontakt_items = [
        ("alle Kontaktanfragen", "../kontaktanfragen/index.html"),
        ("E-Mail Liste", "../kontaktanfragen-maillist/index.html"),
        ("Blacklist", "../kontaktanfragen-blacklist/index.html"),
    ]
    _kontakt_lis = "".join(
        f'<li{" class=\"active\"" if label == active_kontakt_item else ""}><a href="{href}">{label}</a></li>'
        for label, href in _kontakt_items
    )
    kontakt_sub = f"""
                <ul class="nav nav-second-level collapse{' in' if kontakt_active else ''}">
                    {_kontakt_lis}
                </ul>"""
    _makler_hrefs = {
        "Übersicht Makler":    "../makler-uebersicht/index.html",
        "Anfragen":            "../makler-anfragen/index.html",
        "neuen Makler anlegen":"../makler-new/index.html",
    }
    makler_items = []
    for label in MAKLER_SUBITEMS:
        cls = ' class="active"' if label == active_makler_item else ""
        href = _makler_hrefs.get(label, "#")
        makler_items.append(f'<li{cls}><a href="{href}">{label}</a></li>')
    makler_sub = f"""
                <ul class="nav nav-second-level collapse{' in' if makler_active_section else ''}">
                    {''.join(makler_items)}
                </ul>"""

    _objekte_hrefs = {
        "alle Objekte":       "../objekte/index.html",
        "OID / Dubletten Check": "../tools-oid-dubletten/index.html",
    }
    objekte_items = []
    for label in OBJEKTE_SUBITEMS:
        cls = ' class="active"' if label == active_objekte_item else ""
        href = _objekte_hrefs.get(label, "#")
        objekte_items.append(f'<li{cls}><a href="{href}">{label}</a></li>')
    objekte_sub = f"""
                <ul class="nav nav-second-level collapse{' in' if objekte_active_section else ''}">
                    {''.join(objekte_items)}
                </ul>"""

    _koop_lis = "".join(
        f'<li{" class=\"active\"" if label == active_kooperationen_item else ""}><a href="{href}">{label}</a></li>'
        for label, href in KOOPERATIONEN_SUBITEMS
    )
    koop_sub = f"""
                <ul class="nav nav-second-level collapse{' in' if kooperationen_active_section else ''}">
                    {_koop_lis}
                </ul>"""

    return f"""
<nav class="navbar-default navbar-static-side" role="navigation">
    <div class="sidebar-collapse">
        <ul class="nav metismenu" id="side-menu">
            <li class="nav-header">
                <div class="dropdown profile-element">
                    <span class="block m-t-xs font-bold">Regionalimmobilien24</span>
                    <span class="text-muted text-xs block">RI24 SEO Backend</span>
                </div>
            </li>
            <li{dash_active}>
                <a href="../dashboard-makler/index.html"><i class="fa fa-th-large"></i> <span class="nav-label">Dashboard</span> <span class="fa arrow"></span></a>
                <ul class="nav nav-second-level collapse in">
                    {''.join(sub_items)}
                </ul>
            </li>
            <li{' class="active"' if makler_active_section else ''}>
                <a href="#"><i class="fa fa-user"></i> <span class="nav-label">Makler</span> <span class="fa arrow"></span></a>
                {makler_sub}
            </li>
            <li{' class="active"' if active_top_item == 'Nutzer' else ''}><a href="../kundenlogin/index.html"><i class="fa fa-key"></i> <span class="nav-label">Nutzer</span></a></li>
            <li{' class="active"' if objekte_active_section else ''}>
                <a href="#"><i class="fa fa-home"></i> <span class="nav-label">Objekte</span> <span class="fa arrow"></span></a>
                {objekte_sub}
            </li>
            <li{' class="active"' if active_top_item == 'Privatanzeigen' else ''}><a href="../privatanzeigen/index.html"><i class="fa fa-font"></i> <span class="nav-label">Privatanzeigen</span></a></li>
            <li{' class="active"' if active_top_item == 'alle Regionen' else ''}><a href="../regionen/index.html"><i class="fa fa-globe"></i> <span class="nav-label">alle Regionen</span></a></li>
            <li{' class="active"' if kontakt_active else ''}>
                <a href="#"><i class="fa fa-envelope"></i> <span class="nav-label">Kontaktanfragen</span> <span class="fa arrow"></span></a>
                {kontakt_sub}
            </li>
            <li{' class="active"' if active_top_item == 'Team' else ''}><a href="../team/index.html"><i class="fa fa-users"></i> <span class="nav-label">Team</span></a></li>
            <li{' class="active"' if active_top_item == 'Whitelabel-Lizenzen' else ''}><a href="../whitelabel-lizenzen/index.html"><i class="fa fa-users"></i> <span class="nav-label">Whitelabel-Lizenzen</span></a></li>
            <li{' class="active"' if kooperationen_active_section else ''}>
                <a href="../makler-kooperationen/index.html"><i class="fa fa-handshake-o"></i> <span class="nav-label">Kooperationen</span> <span class="fa arrow"></span></a>
                {koop_sub}
            </li>
            <li{' class="active"' if schnittstellen_active else ''}>
                <a href="#"><i class="fa fa-globe"></i> <span class="nav-label">Schnittstellen</span> <span class="fa arrow"></span></a>
                {schnittstellen_sub}
            </li>
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

FOOTER = """
<div class="footer">
    <div><strong>&copy; 2014 - 2026</strong> Regionalimmobilien24 GmbH</div>
</div>
"""


def page_heading(title, crumbs):
    """crumbs: list of breadcrumb label strings; the last one is marked active."""
    items = []
    for i, label in enumerate(crumbs):
        if i == len(crumbs) - 1:
            items.append(f'<li class="breadcrumb-item active"><strong>{label}</strong></li>')
        else:
            items.append(f'<li class="breadcrumb-item"><a href="#">{label}</a></li>')
    return f"""
<div class="row wrapper border-bottom white-bg page-heading">
    <div class="col-lg-10">
        <h2>{title}</h2>
        <ol class="breadcrumb">{''.join(items)}</ol>
    </div>
</div>
"""


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


def prototype_banner(source_path, note=""):
    extra = f" {note}" if note else ""
    return f"""
<div class="prototype-banner">
    <strong>Prototype</strong> — {source_path} rebuilt on the Inspinia theme, using real data captured from the live backend on 2026-09-10.{extra}
</div>
"""


PROTOTYPE_CSS = """
  .prototype-banner { background:#2f4050; color:#fff; text-align:center; padding:6px 10px; font-size:12px; }
  .prototype-banner strong { color:#1ab394; }
"""


def page_shell(title, banner_html, content_html, extra_head="", extra_scripts="", active_dashboard_item=None, breadcrumb_under_dashboard=True, active_makler_item=None, active_top_item=None, active_objekte_item=None, active_kontakt_item=None, active_schnittstellen_item=None, active_kooperationen_item=None):
    side = sidebar(active_dashboard_item, breadcrumb_under_dashboard, active_makler_item, active_top_item, active_objekte_item, active_kontakt_item, active_schnittstellen_item, active_kooperationen_item)
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link href="assets/css/bootstrap.min.css" rel="stylesheet">
<link href="assets/font-awesome/css/font-awesome.css" rel="stylesheet">
{extra_head}
<link href="assets/css/animate.css" rel="stylesheet">
<link href="assets/css/style.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-adaptation.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-colors.css" rel="stylesheet">
<link href="assets/css/pitcom/pitcom-icons.css" rel="stylesheet">
<style>{PROTOTYPE_CSS}</style>
</head>
<body class="pitcom">
{banner_html}
<div id="wrapper">
    {side}
    <div id="page-wrapper" class="gray-bg dashbard-1">
        {TOPBAR}
        {content_html}
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
{extra_scripts}
</body>
</html>
"""
