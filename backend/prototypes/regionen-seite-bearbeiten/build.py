"""Generates index.html: the real 'Seite '<X>' bearbeiten' screen
(/adm/individuell/regionen/edit_region_page.php?regio=aai24&page_id=bfo2),
rebuilt on the Inspinia theme with real data captured for one example page
(Baufinanzierung) of the example region Aachen-Eifel (aai24). Reached from
Seiten individualisieren's "bearbeiten" pencil icon — on the live site,
every row in all 3 of that screen's tables (Hauptnavigation,
Servicenavigation, Seiten ohne Zuordnung) leads to this same screen type,
just for a different page_id; this prototype shows one example regardless
of which row's pencil was clicked (see prototypes/regionen-seiten).

The "zugeordnete Sektionen" table's own "bearbeiten" pencil icons go one
level deeper still (edit_region_section.php, editing one content section's
actual body) — not built out here to keep this migration's scope bounded;
those icons are inert placeholders.

Also added here: the real "Daten der Seite: /aachen-eifel/baufinanzierung/"
5-tab SEO editor (Kopf-Daten / Infos für Sitemap / SEO-Textblock / Bild für
SEO-Textblock / Häufige Fragen) — on the live site this is reached from the
separate "SEO" top-level menu (SEO-Auswahl: Aachen-Eifelimmobilien24 ->
Seitenbaum -> Baufinanzierung), not from this screen, but per instruction
it's folded in here next to Grundeinstellungen since it edits the same
page's data. The SEO-Textblock tab's live page also shows a large annotated
screenshot of where each field renders on the public site — that's a static
help graphic, not data, and isn't reproduced here.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _common as c

BASE = Path(__file__).resolve().parent
SURVEY = BASE.parent.parent / "admin_survey"

data = json.loads((SURVEY / "40-regionen-page-edit-data.json").read_text(encoding="utf-8"))
seo_data = json.loads((SURVEY / "41-seo-baufinanzierung-data.json").read_text(encoding="utf-8"))


def seo_field_row(label, control_html, help_text=""):
    help_html = f' <i class="fa fa-question-circle text-muted" title="{help_text}"></i>' if help_text else ""
    return f"""
    <div class="form-group row">
        <label class="col-sm-3 control-label">{label}{help_html}</label>
        <div class="col-sm-9">{control_html}</div>
    </div>"""


def seo_select(name, options):
    opts = "".join(
        f'<option value="{v}"{" selected" if sel else ""}>{t}</option>' for v, t, sel in options
    )
    return f'<select class="form-control" name="{name}">{opts}</select>'


def seo_save_button():
    return '<div class="text-right m-t-md"><button type="button" class="btn btn-primary btn-sm" title="Speichern"><i class="fa fa-floppy-o"></i></button></div>'


kd = seo_data["kopf_daten"]
kopfdaten_body = "".join([
    seo_field_row("Bezeichnung (intern)", f'<input type="text" class="form-control" value="{kd["name"]}">', "interner Name, erscheint nicht auf der Seite"),
    seo_field_row("URL", f'<input type="text" class="form-control" value="{kd["location"]}" disabled> <span class="text-danger">*</span>'),
    seo_field_row("Page-Titel", f'<input type="text" class="form-control" value="{kd["title"]}">'),
    seo_field_row("H1-SEO-Überschrift", f'<input type="text" class="form-control" value="{kd["header"]}">', "überschreibt die H1 nur für Suchmaschinen"),
    seo_field_row("Schlüsselwörter (Keywords)", f'<input type="text" class="form-control" value="{kd["keywords"]}">'),
    seo_field_row("Beschreibungstext", f'<textarea class="form-control" rows="3">{kd["description"]}</textarea>'),
    seo_field_row("Robots", seo_select("robots", kd["robots_options"])),
    seo_field_row("wieder indizieren", seo_select("revisit-after", kd["revisit_options"])),
    seo_save_button(),
])

sm = seo_data["sitemap"]
sitemap_body = "".join([
    seo_field_row("Priorität", seo_select("prio", sm["prio_options"])),
    seo_field_row("Update-Rate", seo_select("update", sm["update_options"])),
    seo_save_button(),
])

tb = seo_data["textblock"]
textblock_body = "".join([
    seo_field_row("Text", f'<textarea class="form-control" rows="10">{tb["text"]}</textarea>'),
    seo_field_row("Text 2", f'<textarea class="form-control" rows="4">{tb["text2"]}</textarea>'),
    '<p class="text-muted"><small>Die Live-Seite zeigt hier zusätzlich eine bebilderte Anleitung, wo Text/Text 2 auf der öffentlichen Seite erscheinen — ein statisches Hilfsbild, keine Daten, daher hier nicht reproduziert.</small></p>',
    seo_save_button(),
])

bild_body = """
<div class="text-center m-b-md">
    <div style="display:inline-block;background:#f3f3f4;border:1px dashed #d7d7d7;padding:20px 30px;color:#999;">
        <i class="fa fa-image fa-2x"></i><br><small>Vorschaubild (kein Bild hinterlegt)</small>
    </div>
</div>
<input type="file" class="form-control">
<div class="text-right m-t-md"><button type="button" class="btn btn-primary btn-sm">Hochladen</button></div>
"""

faq_body = '<button type="button" class="btn btn-primary btn-sm">Neue Frage</button>'

seo_tabs = f"""
<ul class="nav nav-tabs">
    <li class="active"><a data-toggle="tab" href="#seo-tab-kopfdaten">Kopf-Daten</a></li>
    <li><a data-toggle="tab" href="#seo-tab-sitemap">Infos f&uuml;r Sitemap</a></li>
    <li><a data-toggle="tab" href="#seo-tab-textblock">SEO-Textblock</a></li>
    <li><a data-toggle="tab" href="#seo-tab-bild">Bild f&uuml;r SEO-Textblock</a></li>
    <li><a data-toggle="tab" href="#seo-tab-faq">H&auml;ufige Fragen</a></li>
</ul>
<div class="tab-content">
    <div class="tab-pane active" id="seo-tab-kopfdaten">{kopfdaten_body}</div>
    <div class="tab-pane" id="seo-tab-sitemap">{sitemap_body}</div>
    <div class="tab-pane" id="seo-tab-textblock">{textblock_body}</div>
    <div class="tab-pane" id="seo-tab-bild">{bild_body}</div>
    <div class="tab-pane" id="seo-tab-faq">{faq_body}</div>
</div>
"""

grund_thead = """
<tr>
    <th>Bezeichnung &middot; Pfad</th>
    <th>Sortierung</th>
    <th>Sektionen / Elemente</th>
</tr>"""
grund_row = (
    "<tr>"
    f'<td>{data["page_name"]}<br><small class="text-muted">{data["pfad"]}</small></td>'
    f'<td class="text-center">{data["sortierung"]}</td>'
    f'<td class="text-center">{data["sektionen"]}</td>'
    "</tr>"
)
grund_table = f"""
<div class="table-responsive">
    <table class="table table-bordered">
        <thead>{grund_thead}</thead>
        <tbody>{grund_row}</tbody>
    </table>
</div>"""

sektionen_thead = """
<tr>
    <th>Bezeichnung</th>
    <th>Sortierung</th>
    <th>bearbeiten</th>
</tr>"""
sektionen_rows = "".join(
    "<tr>"
    f'<td>{s["bezeichnung"]}</td>'
    f'<td class="text-center">{s["sortierung"]}</td>'
    '<td class="text-center"><a href="#" class="btn btn-default btn-xs" title="Sektion bearbeiten"><i class="fa fa-pencil"></i></a></td>'
    "</tr>"
    for s in data["sections"]
)
sektionen_table = f"""
<div class="table-responsive">
    <table class="table table-striped table-bordered table-hover">
        <thead>{sektionen_thead}</thead>
        <tbody>{sektionen_rows}</tbody>
    </table>
</div>"""

content = f"""
<div class="wrapper wrapper-content animated fadeInRight">
    <div class="row">
        <div class="col-lg-6">{c.ibox("Grundeinstellungen", grund_table)}</div>
        <div class="col-lg-6">{c.ibox("zugeordnete Sektionen", sektionen_table)}</div>
    </div>
    <div class="row">
        <div class="col-lg-12">{c.ibox(f"Daten der Seite: {seo_data['url_path']}", seo_tabs)}</div>
    </div>
</div>
"""

html = c.page_shell(
    title=f"Seite '{data['page_name']}' bearbeiten - Aachen-Eifelimmobilien24 - RI24 SEO",
    banner_html=c.prototype_banner(
        "Seite bearbeiten (/adm/.../regionen/edit_region_page.php?regio=aai24&page_id=bfo2)",
        f"Real data for the example page \"{data['page_name']}\" of the example region Aachen-Eifel (aai24). "
        "The nested \"zugeordnete Sektionen\" bearbeiten icons go one level deeper still (editing a section's content) — not built out, see build.py docstring.",
    ),
    content_html=c.page_heading(f"Seite '{data['page_name']}' bearbeiten - Aachen-Eifelimmobilien24", ["Home", "alle Regionen", "regionale Seiten - Aachen-Eifelimmobilien24", "Seite bearbeiten - Aachen-Eifelimmobilien24"]) + content,
    active_top_item="alle Regionen",
    breadcrumb_under_dashboard=False,
)

(BASE / "index.html").write_text(html, encoding="utf-8")
print("wrote", BASE / "index.html", len(html), "bytes")
