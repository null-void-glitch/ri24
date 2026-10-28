# RI24 Admin Backend → Inspinia: Visual Layout Migration Map

Scope: **visual/layout migration only**. No backend logic, data, routes, field names, or IDs change —
this document tells the frontend/template layer which Inspinia page pattern and plugin to reuse for
each existing `/adm/` screen. Data/DB migration is handled separately by the dev team.

Source material:
- Current backend: screenshots in `admin_survey/00-*.png` … `13-*.png`, captured live via a logged-in
  session against `backend.regionalimmobilien24.de/adm/`.
- Target theme: [Inspinia](https://www.v-start.de/inspinia/) demo pages, screenshots in
  `admin_survey/i-*.png`. Stack confirmed from the demo source: Bootstrap 3, jQuery, **metisMenu**
  (collapsible sidebar), **Font Awesome** icons.

Current stack observation: the existing backend already uses a dark fixed sidebar + white content
panels with dark title bars — structurally this is very close to Inspinia's "ibox" panel pattern, so
most sections are a **reskin**, not a rebuild. The exceptions are the big listing tables (custom
number-pagination, no client-side search/sort) and the SEO/static-pages trees, which should pick up
real Inspinia plugins (DataTables, jsTree) to gain functionality, not just a new coat of paint.

---

## 1. Global chrome

| Element | Current | Screenshot | Inspinia target | Notes |
|---|---|---|---|---|
| Sidebar nav | Fixed dark sidebar, icon + label, `+` expandable submenus | `00-dashboard.png` | Inspinia left nav w/ **metisMenu** (`index.html`) | Same interaction model already (expand/collapse). Map each top-level item 1:1 to a metisMenu `<li>`; keep current icon meaning, swap icon set for Font Awesome equivalents. |
| Topbar | Plain dark bar, only "Logout" button | `00-dashboard.png` | Inspinia top navbar (`index.html`) | Current has no search/notifications — don't invent fake ones; keep topbar minimal (logout + maybe session timer "480 Minuten" as a text item), just restyle to Inspinia's navbar classes. |
| Breadcrumb | `Home > Dashboard` gray bar under header | all screens | Inspinia breadcrumb row (`.breadcrumb`, same pattern site-wide) | Direct swap, same structure. |
| Content sections | Dark-header white panel ("Maklerdaten", "Server-Infos", etc.) | all screens | Inspinia **ibox** (`.ibox`, `.ibox-title`, `.ibox-content`) | This is the biggest win: current custom panel = Inspinia ibox almost 1:1. Title bar gets the ibox collapse/close icons for free. |

---

## 2. Dashboard (`00-dashboard.png`)

- **Current**: "Server-Infos" and "Anzahl Objekte" as 3-column stat panels (status pairs: label + value).
- **Target**: Inspinia `index.html` (Dashboard v.1) — small stat widgets + ibox panels.
  Screenshot: `i-01-index.png`.
- Use Inspinia's small stat-box widgets for single-number metrics (Wohnen/Gewerbe counts,
  Multilisting/Offmarket/inaktiv), and a plain 3-column ibox row (like current) for the
  status/latency/load panels since those are label-value pairs, not chart widgets.
- No charts exist in the current dashboard — don't add graph widgets from the demo, keep it flat data.

## 3. Big listing tables — Objekte / Makler / Privatanzeigen

- **Current**: `01-objekte-list.png`, `02-makler-list.png`, `09-privatanzeigen.png`. Dense table with
  thumbnail column, custom letter/number jump-pagination grid at top, no visible search or sort.
- **Target**: Inspinia **Data Tables** page — `table_data_tables.html`, screenshot `i-03-table-datatables.png`.
- Functional upgrade to call out to devs: swap the custom pagination grid for the **DataTables**
  plugin (search box, column sort, page-length selector, Copy/CSV/Excel/Print export buttons already
  built into the Inspinia demo). This directly replaces the hand-rolled number grid — a real UX
  improvement, not just a skin change.
- Keep the thumbnail-image column (DataTables supports arbitrary cell HTML, incl. `<img>`).

## 4. Simple/short lists — Team, Baufi/Immo-Orte

- **Current**: `12-baufi-orte.png` (single ibox, plain list), Team list (not captured but same class of
  screen as Whitelabel minus avatar/contact detail).
- **Target**: Inspinia **Static Tables** — `table_basic.html`, screenshot `i-04-table-basic.png`.
  Use the plain "Basic Table" or "Border Table" variant — no DataTables needed here, these lists are
  short and don't need search/sort/export.

## 5. Whitelabel-Lizenzen (avatar + contact card list)

- **Current**: `06-whitelabel-list.png` — table row per license holder: avatar photo, name/position,
  phone/mobile/email, edit/delete/status icons.
- **Target option A (recommended, keeps table density)**: Inspinia Static/Data Table with an avatar
  `<img>` cell, same as today — lower migration effort, preserves the current scan-a-list workflow.
- **Target option B (nicer visually, more rework)**: Inspinia **Contacts v.2** card grid —
  `contacts_2.html`, screenshot `i-07-contacts2.png`. One card per license/partner with avatar, name,
  role, contact block, and action buttons (Call/Email/Follow → repurpose as Edit/Deactivate/Delete).
- Flag this as a decision point for the team — A is a straight reskin, B is a UX change (grid instead
  of list) that needs sign-off since it changes information density on a page with 200+ rows.

## 6. Makler edit / neuen Makler anlegen (multi-section form)

- **Current**: `03-makler-new.png`, `13-makler-edit.png` — main column with stacked panels
  ("Maklerdaten", "Makler-Profil", "Login Backend", "Login FTP", "techn. Ansprechpartner",
  "Webapp-Einstellungen"), each a dark-header box with label/input rows; separate **right-hand sidebar
  column** with standalone action boxes ("Daten speichern" → Speichern button, "Makler Text" preview,
  "Makler löschen" → red Löschen button).
- **Target**: Inspinia ibox-based two-column form layout, same structure as
  `form_advanced.html` (screenshot `i-05-form-advanced.png`) for the field groups, combined with the
  **right sidebar action-panel pattern** used throughout Inspinia's detail views
  (e.g. `invoice.html`, `profile.html`) for the Speichern/Löschen/preview boxes.
- Keep the two-column split exactly as-is: main content left, sticky action ibox(es) right — this
  already matches Inspinia's own convention for edit/detail screens, so it's a direct reskin.
- Form controls to reuse from Inspinia's form component set: standard text inputs, `<select>`
  (Region, Makler-Stufe/Modell, Angebotspaket), checkboxes (iCheck-styled in Inspinia — "neue Objekte
  im ADM anlegen" etc.), and the TinyMCE-based "Makler Text" box — Inspinia's
  `form_editors.html` demonstrates the same TinyMCE integration pattern, so the existing
  `#maklerprofil_dyn_profil_text_tiny` editor wiring does not need to change, only its chrome.
- The read-only/generated fields (Makler-ID, generated Login-Name/Passwort with the refresh icon) map
  to Inspinia's plain disabled-input style — no special component needed.

## 7. alle Regionen (config matrix)

- **Current**: `04-regionen-config.png` — wide table, one row per region, colored pill badges per
  column (aktiv/individuell/Parameter/Geodaten/Mailings/Immo Werbebanner/Seiten), each with its own
  "anpassen" action button.
- **Target**: Inspinia **Data Tables** (`table_data_tables.html`) for the base grid (sortable, and a
  search box would actually help here — 80+ regions in one table today with no filter), combined with
  Inspinia's **Badges & Labels** component (`badges_labels.html`) for the colored pill states
  (green/red/blue/orange → Inspinia's `label-success`/`label-danger`/`label-info`/`label-warning`).
- This is a genuine usability gap in the current screen (no search across 80+ rows) — worth flagging
  to devs as a "free" improvement from adopting DataTables here, not just cosmetic.

## 8. SEO-Konfiguration & statische Seiten (nested/tree lists)

- **Current**: `08-seo-config.png` (simple 2-level "Seitenbaum" list) and `11-static-sites.png`
  (three parallel ibox panels — Hauptnavigation / Servicenavigation / Seiten ohne Zuordnung — each a
  table with expand/edit per row, representing a page tree flattened into per-panel tables).
- **Target**: Inspinia **Tree View** — `tree_view.html`, screenshot `i-09-tree-view.png` (jsTree
  plugin, supports nested folders/pages with icons, matches "Seitenbaum" naming in the current UI
  almost exactly).
- Recommendation: use jsTree for the actual page-tree screens (SEO Seitenbaum, and ideally collapse
  the three `statische Seiten` panels into one tree if the underlying data is hierarchical — flag this
  as a question for the dev team, since right now it's presented as 3 flat tables, not a real tree).
- If preserving the current three-panel flat-table layout is preferred (lower risk), keep them as
  three side-by-side Inspinia ibox + Static/Data Tables instead of introducing jsTree — this is the
  safer, lower-effort option and should be the fallback if tree semantics turn out not to match the
  data model.

## 9. Kontaktanfragen / Suchaufträge

Both re-captured with a longer timeout — they are **not** the flat-table pattern from §3, each needs
its own mapping:

### 9a. Kontaktanfragen (`07-kontaktanfragen.png`)

- A filter bar at top, then a **repeating card feed**: one block per inquiry with a property
  thumbnail, sender info with small colored status/portal-source flag icons, a message/note preview,
  and an assigned-agent avatar row underneath — much closer to an activity/social feed than a data
  grid.
- **Target**: Inspinia's **Activity Stream** (`activity_stream.html`) or **Social Feed** pattern (seen
  in the "Your daily feed" ibox on the dashboard demo, `i-01-index.png`) — repeating item blocks with
  avatar + timestamp + content + action row. Keep the filter bar as a plain ibox form row above the
  feed.
- Do not force this into DataTables — the content per row (thumbnail + message body) doesn't fit a
  tabular cell model well; the feed pattern preserves the current scan experience better.

### 9b. Suchaufträge (`10-suchauftraege-viewport.png`, top of page only — see note below)

- **Important finding**: this screen renders **5,317 active search-order records with zero
  pagination** — one key-value detail table per record (code, email, gültig-bis/last-mail dates, then
  a full attribute list: `geo`, `vaoa`, `oa`, `va`, `p`, `f`, `z`, `rd`, `pa`, `bt`, `gw`, `gs`, …),
  stacked vertically. Full page height measured at **~1.9 million pixels** — this is large enough that
  a headless browser can no longer even screenshot it in one shot (`Page.captureScreenshot` protocol
  error), which is a strong signal the current page is already past a usable/renderable size for a
  browser, regardless of theme.
- **Target**: don't reproduce this as one giant page. Two Inspinia-native options for devs to choose
  between:
  - Reflow each record's attribute block as a compact **ibox** (title = Suchauftrag-Code + dates,
    body = a small 2-column key-value table for the search criteria) and paginate the collection with
    **Data Tables**-style server-side pagination (or at minimum a page-length control) — same DataTables
    plugin as §3/§7, just applied to a card collection instead of flat rows.
  - Alternatively, flatten to one real row per search order in a Data Table (columns: Code, E-Mail,
    gültig bis, letzte Mail, + an "Details" expand toggle for the full attribute list) — lower rework,
    but loses the at-a-glance attribute view.
  - Either way: **flag the missing pagination as a pre-existing bug/risk to the dev team**, independent
    of the theme migration — 5000+ un-paginated records is a real performance problem today.

---

## Summary table

| Current screen | Screenshot | Inspinia target page | Key plugin |
|---|---|---|---|
| Dashboard | `00-dashboard.png` | `index.html` | ibox + stat widgets |
| Objekte / Makler / Privatanzeigen lists | `01,02,09-*.png` | `table_data_tables.html` | DataTables |
| Team / Baufi-Orte | `12-baufi-orte.png` | `table_basic.html` | none (static) |
| Whitelabel-Lizenzen | `06-whitelabel-list.png` | `table_basic.html` **or** `contacts_2.html` | DataTables / card grid |
| Makler new/edit | `03,13-*.png` | `form_advanced.html` + sidebar action ibox pattern | iCheck, TinyMCE |
| alle Regionen | `04-regionen-config.png` | `table_data_tables.html` | DataTables + Badges |
| SEO / statische Seiten | `08,11-*.png` | `tree_view.html` (or ibox tables as fallback) | jsTree |
| Kontaktanfragen | `07-kontaktanfragen.png` | `activity_stream.html` (feed pattern) | none (plain ibox feed) |
| Suchaufträge | `10-suchauftraege-viewport.png` | ibox cards + DataTables pagination **or** flat Data Table w/ expand | DataTables — also flags a pre-existing no-pagination issue (5,317 rows, ~1.9M px page) |

All screenshots referenced above live in `admin_survey/` next to this file for side-by-side review.
