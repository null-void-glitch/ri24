# Makler-Texte (Regionalimmobilien24)

Automatisiert das Befüllen des Feldes **„Makler Text"** in den Anbieterprofilen
des RI24-Backends per Playwright + OpenAI (Web-Suche).

## Ablauf

1. Login ins Backend (`/adm/`), Session-Token (`admsess`) wird aus der URL gelesen.
2. **Übersicht Makler** öffnen, ersten Makler (`makler/edit?maklerid=…`) wählen.
3. Auf der Edit-Seite **Region-Code** (Badge, z. B. `bsi24`) und
   **Profil-Verzeichnis** (`profil_uri_name`, Template `{region}/anbieter/<slug>/`) auslesen.
4. Öffentliches Anbieter-**Impressum** laden:
   `https://www.regionalimmobilien24.de/<region-slug>/anbieter/<slug>/impressum/`
   (`{region}` → Regionsname aus dem Mapping, klein geschrieben).
5. 300-Wörter-Vorstellungstext per OpenAI **Responses-API + Web-Search** erzeugen
   (Impressum + Region gehen in den Prompt zur Identifikation).
6. Text in den **TinyMCE**-Editor `maklerprofil_dyn_profil_text_tiny` schreiben,
   ins versteckte Datenfeld synchronisieren und über den **Speichern**-Button
   (`span.btn.pitsafe`) speichern.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

`.env` enthält `USERNAME`, `PASSWORD`, `OPENAI_KEY` und `region_mapping`
(Kürzel → Regionsname). **Nicht** einchecken (siehe `.gitignore`).

## Ausführen (Vollausbau über alle Makler)

```bash
.venv/bin/python generate_texts.py
```

Iteriert regionsweise über alle Makler. Fortschritt landet in `rollout_log.csv`
(Spalten: maklerid, name, region, words, status). Der Lauf ist **resümierbar**:
bei erneutem Start werden bereits befüllte Makler übersprungen.

Schalter oben in `generate_texts.py`:
- `HEADLESS` — `False` zum Zuschauen im Browser.
- `AUTO_SAVE` — `True` speichert automatisch (klickt „Speichern").
- `SKIP_FILLED` — `True` überspringt Makler mit bereits vorhandenem Text (resümierbar).
- `LIMIT` — max. Anzahl zu befüllender Makler (`None` = alle; z. B. `2` zum Testen).
- `ONLY_REGIONS` — Liste von Region-Codes, z. B. `["bsi24"]`, sonst alle.

Eigenschaften:
- **Region-Slugs** (auch Umlaute: München→`muenchen`, Köln→`koeln`) werden
  autoritativ aus `regionen/config/` gelesen.
- **Fehlertoleranz:** ein Fehler bei einem Makler bricht den Lauf nicht ab, er
  wird als `error:*` geloggt.
- **Session:** läuft die Backend-Session ab, wird automatisch neu eingeloggt.
- **Inhalt:** Der Finanzdienstleistungs-Bereich der Makler wird NICHT beworben
  (Erkennung + neutrale Umschreibung); Fokus rein auf Immobilien.

Hinweis Kosten/Dauer: je Makler 1–3 OpenAI-Calls mit Web-Suche → bei mehreren
tausend Maklern erheblicher Zeit-/Kostenaufwand. Ggf. in Batches über `LIMIT`
oder `ONLY_REGIONS` laufen lassen.

## Parallel (schneller): `rollout_parallel.py`

```bash
.venv/bin/python rollout_parallel.py
WORKERS=6 .venv/bin/python rollout_parallel.py
```

Nutzt **einen** Login und mehrere Browser-Seiten gleichzeitig (async); die
OpenAI-Generierung läuft nebenläufig in Threads. Wall-Clock ≈ serielle Dauer /
WORKERS (bei ~2.645 Maklern und WORKERS=5 grob **~4 h**).

Wichtig — Backend-Eigenheit: pro Account ist nur **eine** aktive Login-Session
für die Makler-Listen gültig (ein zweiter Login entwertet die erste). Daher
NICHT mehrere Prozesse/Logins parallel starten — `rollout_parallel.py` löst das
über mehrere Seiten unter einer Session. Gleiche Steuerung per Env-Variablen
(`WORKERS`, `SKIP_FILLED`, `AUTO_SAVE`, `ROLLOUT_LIMIT`, `ROLLOUT_REGIONS`,
`ROLLOUT_LOG`), gleiches resümierbares `rollout_log.csv`.
