# Regionalimmobilien24 — Landingpages · Projekt-Handoff

> Hand this file to Claude at the start of a new session in this folder to restore full context.
> Last updated: 2026-06-30.

## What this project is
Standalone, **self-contained HTML landing pages** for **regionalimmobilien24.de** (German regional real-estate platform). No build system — each page is one `.html` file with inline CSS/JS, fonts via Google Fonts CDN, and local image assets in `assets/`. Drop-in deployable.

**Single conversion goal:** every page drives clicks to the Maklersuche click-funnel → `https://www.regionalimmobilien24.de/maklersuche/`

## Files in this folder
- `grundstueck-verkaufen.html` — **the blueprint page** ("Grundstück verkaufen oder bewerten lassen")
- `haus-verkaufen.html` — "Haus verkaufen oder bewerten lassen"
- `wohnung-verkaufen.html` — "Wohnung verkaufen oder bewerten lassen"
- `assets/` — `doppellogo.webp` (+ `.png` fallback), `google-partner.svg`, `instagram.webp`, `facebook.webp`, `pinterest.webp`, `app.webp`, `eu-kofinanziert.webp`
- `*.md` — the SEO source content for each page (note caveat below)
- `Doppellogo-2023.png` — original logo, 1.8 MB, **no longer referenced** (safe to delete; pages use `assets/doppellogo.webp`)
- `header.PNG` — reference screenshot of the desired desktop header

**⚠ Content-file naming caveat:** `content-haus-verkaufen.md` actually contains *Grundstück* (land) content — it is the source for `grundstueck-verkaufen.html`, NOT the house page. The real house content is `haus-verkaufen.md`. Don't be misled by the filename.

## CI / brand colors (authoritative — NO blue; the blue on the live site is not a brand color)
- **Main brand: lime green `#BDE04F`.** Other CI colors: gray `#565656`, darkgray `#333333`, black, white, plus lighter/darker shades of the lime.
- Working shades used: `#a6cf33` (darker lime — hover, visible green lines on white), `#5f7d12` (dark green — the only green legible as small text/icons on white), `#eef6d6` (light lime wash).
- **Usage rule:** lime is LIGHT → use it as **fills with dark text** (buttons, pills, badges, hero marker-highlight, the solid Bodenrichtwert/callout block, SVG fills + dots) and as **bright accents on charcoal**. NEVER small text or thin hairlines on white. Buttons = lime bg + `#1f1f1f` text.
- Ink `#333333` · muted `#565656` · strong `#1f1f1f` · dark sections `#2e2e2e` · footer `#161616`/`#1c1c1c`.

## Typography
- Display: **Space Grotesk** · Body: **Inter** · Labels/data/eyebrows: **Space Mono** (the "data readout" voice).

## Header (identical on all pages)
- `assets/doppellogo.webp` logo (PNG fallback via `<picture>`).
- **Desktop (≥760px):** white logo row, logo centered, over a sticky dark-gray (`#565656`) nav bar. Links: Immobilien · Baufinanzierung · Immobilien inserieren · Unser Team · Blog · Login. Hover → lime.
- **Mobile (≤760px):** sticky bar = burger ☰ (left) · logo centered · login user-icon (right). Burger → ✕ toggles a dark dropdown with the nav stacked; Login `<li>` hidden (icon covers it). JS toggles `.nav-open`, manages `aria-expanded`, closes on link click / Esc.
- Logo on mobile uses `height:auto; max-height:36px; max-width:100%` so it never gets squished by the global `img{max-width:100%}`.

## Footer (identical on all pages)
Dark `#161616`. Order: *Wichtiger Hinweis* disclaimer (page-specific text) → `#footer-head` "Regionalimmobilien24" → legal nav (AGB / Impressum / Datenschutz, absolute URLs) → social nav (Google Partner badge, Instagram, Facebook, Pinterest, "App herunterladen" PWA span `#ri24_pwa_install_cmd` (inert on standalone page), EU "Kofinanziert" logo) → `© 2017–2026 Regionalimmobilien24 GmbH`. All images are local in `assets/`. (Site blocks `/get-file/` hotlinking with HTTP 451; assets were downloaded with a browser UA + Referer.)

## Page section structure (shared blueprint)
hero + signature card · Vorteile strip (charcoal) · 5 Schritte (numbered) · Wertfaktoren grid (6) · Arten/Zielgruppen cards (6) · solid-lime callout · privat-vs-Makler compare · Unterlagen `<details>` chips · FAQ (`<details>` + `FAQPage` JSON-LD) · final CTA · footer. Each page ships `FAQPage` + `Service` + `BreadcrumbList` JSON-LD.

### Hero signature cards (subject-specific, same ink-line + lime-fill + Space-Mono-data language)
- Grundstück = cadastral **Liegenschaftskarte** (parcel polygon, survey points, "Bodenrichtwert?")
- Haus = **house elevation** ("Hauswert?")
- Wohnung = **floor plan / Grundriss** (rooms, "Wohnungswert?")
- **Important:** animated SVG strokes carry `pathLength="1"` — without it the draw-on animation renders as a dotted outline on motion-enabled browsers.

## How to build another page
Copy `grundstueck-verkaufen.html` to the new slug, then swap ONLY: `<head>` (title, description, canonical, og:*), the hero (`<h1>`, lead, CTA label, signature SVG + tag), the content sections, the footer `Wichtiger Hinweis` text, the skip-link text, and the FAQ JSON-LD (+ Service name + BreadcrumbList). Leave CSS, header, footer markup, and JS untouched.

## How to preview locally
```
python3 -m http.server 8755    # run in this folder
# then open:
#   http://localhost:8755/grundstueck-verkaufen.html
#   http://localhost:8755/haus-verkaufen.html
#   http://localhost:8755/wohnung-verkaufen.html
```
Quality bar already met: responsive to mobile, visible keyboard focus, reduced-motion respected, JSON-LD validated, tags balanced.

## OPEN TODOs (confirm/decide next session)
1. **Nav-bar URLs are GUESSED slugs** (`/baufinanzierung/`, `/immobilie-inserieren/`, `/unser-team/`, `/blog/`, `/login/`). The homepage is JS-rendered so they couldn't be scraped — confirm the real paths and update all three pages.
2. **Canonical slugs assumed**: `/grundstueck-verkaufen/`, `/haus-verkaufen/`, `/wohnung-verkaufen/`. Adjust if they'll live elsewhere.
3. **Delete `Doppellogo-2023.png`** (1.8 MB, unused) once confirmed.
4. Optional: cross-link the three pages (e.g. a "weitere Immobilie verkaufen" row) if desired.

## Installed tooling note
The `frontend-design` plugin (from the `anthropics/claude-code` marketplace) is installed and was used as the design lead for these pages.
