"""
Master build for the /complete/ demo suite.

Rebuilds all individual prototypes (picking up _common.py link updates),
then mirrors them into complete/[page]/ subdirectories. Each subdir gets:
  - assets symlink → ../../makler-uebersicht/assets
  - post-processed index.html (hardcoded-sidebar dashboard pages get
    their sidebar links wired to match what _common.py now produces)

Entry point: complete/index.html — meta-refresh redirect to dashboard-makler.

Usage:
    python3 build.py
"""
import subprocess, sys
from pathlib import Path

PROTO_DIR = Path(__file__).resolve().parent.parent   # prototypes/
COMPLETE  = Path(__file__).resolve().parent           # prototypes/complete/
ASSETS    = "../../makler-uebersicht/assets"

PAGES = [
    "dashboard-makler",
    "dashboard-baufi",
    "dashboard-nutzer",
    "makler-uebersicht",
    "makler-anfragen",
    "makler-edit",
    "makler-new",
    "makler-kooperationen",
    "makler-kooperationen-new",
    "makler-kooperationen-edit",
    "kundenlogin",
    "objekte",
    "tools-oid-dubletten",
    "privatanzeigen",
    "regionen",
    "regionen-params",
    "regionen-geodaten",
    "regionen-mailings",
    "regionen-werbebanner",
    "regionen-seiten",
    "regionen-seite-bearbeiten",
    "regionen-all",
    "kontaktanfragen",
    "kontaktanfragen-maillist",
    "kontaktanfragen-blacklist",
    "team",
    "team-edit",
    "team-partner-edit",
    "whitelabel-lizenzen",
    "whitelabel-lizenzen-edit",
    "schnittstellen-sitemaps",
    "schnittstellen-export",
]

# The 3 dashboard pages have fully hardcoded sidebars (predating _common.py).
# These rewrites apply _common.py's link decisions to their HTML output.
KOOPERATIONEN_TOP_LEVEL = (
    '<li>\n'
    '                <a href="../makler-kooperationen/index.html">'
    '<i class="fa fa-handshake-o"></i>'
    ' <span class="nav-label">Kooperationen</span>'
    ' <span class="fa arrow"></span></a>\n'
    '                <ul class="nav nav-second-level collapse">\n'
    '                    <li><a href="../makler-kooperationen/index.html">Übersicht</a></li>\n'
    '                    <li><a href="../makler-kooperationen-new/index.html">neue Kooperation</a></li>\n'
    '                </ul>\n'
    '            </li>\n'
    '            '
)

SCHNITTSTELLEN_DROPDOWN = (
    '<li>\n'
    '                <a href="#"><i class="fa fa-globe"></i>'
    ' <span class="nav-label">Schnittstellen</span>'
    ' <span class="fa arrow"></span></a>\n'
    '                <ul class="nav nav-second-level collapse">\n'
    '                    <li><a href="../schnittstellen-sitemaps/index.html">Sitemaps (Mitula)</a></li>\n'
    '                    <li><a href="../schnittstellen-export/index.html">Statischer Immobilien Export</a></li>\n'
    '                </ul>\n'
    '            </li>'
)

DASH_REWRITES = [
    # Dashboard top-level heading link
    ('<a href="#"><i class="fa fa-th-large"></i>',
     '<a href="../dashboard-makler/index.html"><i class="fa fa-th-large"></i>'),
    # Dashboard submenu
    ('<li class="active"><a href="#">Makler</a></li>',
     '<li class="active"><a href="../dashboard-makler/index.html">Makler</a></li>'),
    ('<li><a href="#">Makler</a></li>',
     '<li><a href="../dashboard-makler/index.html">Makler</a></li>'),
    ('<li class="active"><a href="#">Baufinanzierung</a></li>',
     '<li class="active"><a href="../dashboard-baufi/index.html">Baufinanzierung</a></li>'),
    ('<li><a href="#">Baufinanzierung</a></li>',
     '<li><a href="../dashboard-baufi/index.html">Baufinanzierung</a></li>'),
    ('<li class="active"><a href="#">Nutzer</a></li>',
     '<li class="active"><a href="../dashboard-nutzer/index.html">Nutzer</a></li>'),
    ('<li><a href="#">Nutzer</a></li>',
     '<li><a href="../dashboard-nutzer/index.html">Nutzer</a></li>'),
    ('<li class="active"><a href="#">reCaptcha</a></li>', ''),
    ('<li><a href="#">reCaptcha</a></li>', ''),
    # Makler submenu
    ('<li><a href="#">Übersicht Makler</a></li>',
     '<li><a href="../makler-uebersicht/index.html">Übersicht Makler</a></li>'),
    ('<li><a href="#">Anfragen</a></li>',
     '<li><a href="../makler-anfragen/index.html">Anfragen</a></li>'),
    ('<li><a href="#">neuen Makler anlegen</a></li>',
     '<li><a href="../makler-new/index.html">neuen Makler anlegen</a></li>'),
    ('<li><a href="#">Makler umhängen</a></li>', ''),
    ('<li><a href="#">Kooperationen</a></li>', ''),
    # Nutzer (formerly Kundenlogin) / Privatanzeigen
    ('<a href="#"><i class="fa fa-key"></i> <span class="nav-label">Nutzer</span></a>',
     '<a href="../kundenlogin/index.html"><i class="fa fa-key"></i> <span class="nav-label">Nutzer</span></a>'),
    ('<a href="#"><i class="fa fa-font"></i> <span class="nav-label">Privatanzeigen</span></a>',
     '<a href="../privatanzeigen/index.html"><i class="fa fa-font"></i> <span class="nav-label">Privatanzeigen</span></a>'),
    # Objekte submenu
    ('<li><a href="#">alle Objekte</a></li>',
     '<li><a href="../objekte/index.html">alle Objekte</a></li>'),
    ('<li><a href="#">OID / Dubletten Check</a></li>',
     '<li><a href="../tools-oid-dubletten/index.html">OID / Dubletten Check</a></li>'),
    # Regionen submenu
    ('<a href="#"><i class="fa fa-globe"></i> <span class="nav-label">alle Regionen</span></a>',
     '<a href="../regionen/index.html"><i class="fa fa-globe"></i> <span class="nav-label">alle Regionen</span></a>'),
    # Kontaktanfragen submenu
    ('<li><a href="#">alle Kontaktanfragen</a></li>',
     '<li><a href="../kontaktanfragen/index.html">alle Kontaktanfragen</a></li>'),
    ('<li><a href="#">E-Mail Liste</a></li>',
     '<li><a href="../kontaktanfragen-maillist/index.html">E-Mail Liste</a></li>'),
    ('<li><a href="#">Blacklist</a></li>',
     '<li><a href="../kontaktanfragen-blacklist/index.html">Blacklist</a></li>'),
    # Team / Whitelabel-Lizenzen
    ('<a href="#"><i class="fa fa-users"></i> <span class="nav-label">Team</span></a>',
     '<a href="../team/index.html"><i class="fa fa-users"></i> <span class="nav-label">Team</span></a>'),
    ('<a href="#"><i class="fa fa-users"></i> <span class="nav-label">Whitelabel-Lizenzen</span></a>',
     '<a href="../whitelabel-lizenzen/index.html"><i class="fa fa-users"></i> <span class="nav-label">Whitelabel-Lizenzen</span></a>'),
    # Schnittstellen flat → dropdown with real links; Kooperationen top-level injected before it
    ('<li><a href="#"><i class="fa fa-globe"></i> <span class="nav-label">Schnittstellen</span></a></li>',
     KOOPERATIONEN_TOP_LEVEL + SCHNITTSTELLEN_DROPDOWN),
]

DASHBOARD_PAGES = {"dashboard-makler", "dashboard-baufi", "dashboard-nutzer"}

# ── Step 1: rebuild all individual prototypes ────────────────────────────────
print("=== Rebuilding prototypes ===")
errors = []
for page in PAGES:
    build = PROTO_DIR / page / "build.py"
    if not build.exists():
        print(f"  SKIP (no build.py): {page}")
        continue
    r = subprocess.run(
        [sys.executable, "-I", str(build)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"  ERROR {page}: {r.stderr.strip()[:160]}")
        errors.append(page)
    else:
        print(f"  ok  {page}")

# ── Step 2: mirror into complete/ ────────────────────────────────────────────
print("\n=== Mirroring to complete/ ===")
for page in PAGES:
    dest = COMPLETE / page
    dest.mkdir(exist_ok=True)

    # Ensure assets symlink points to the shared assets tree
    assets_link = dest / "assets"
    if assets_link.exists() or assets_link.is_symlink():
        assets_link.unlink()
    assets_link.symlink_to(ASSETS)

    src = PROTO_DIR / page / "index.html"
    if not src.exists():
        print(f"  MISSING: {page}/index.html")
        continue

    html = src.read_text(encoding="utf-8")

    if page in DASHBOARD_PAGES:
        for old, new in DASH_REWRITES:
            html = html.replace(old, new)

    (dest / "index.html").write_text(html, encoding="utf-8")
    kb = len(html) // 1024
    print(f"  ok  {page}  ({kb} KB)")

# ── Step 3: landing-page redirect ────────────────────────────────────────────
landing = """\
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=dashboard-makler/index.html">
<title>RI24 Admin – Prototypen-Suite</title>
</head>
<body style="font-family:sans-serif;padding:2em;color:#333;">
<p>Weiterleitung zu
   <a href="dashboard-makler/index.html">Dashboard → Makler</a>&hellip;</p>
</body>
</html>
"""
(COMPLETE / "index.html").write_text(landing, encoding="utf-8")
print("\nwrote complete/index.html  (meta-refresh → dashboard-makler)")

if errors:
    print(f"\nWARNING: {len(errors)} build(s) failed: {', '.join(errors)}")
else:
    print(f"\nAll {len(PAGES)} pages built successfully.")

print("Open: file://" + str(COMPLETE / "index.html"))
