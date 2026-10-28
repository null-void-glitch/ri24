# RI24 Baufinanzierungs-Assistent – eigenständiger DeepChat + PHP-Proxy

Eigenständiger Chatbot für die persönlichen Finanzierungsberater-Seiten (kein
Exposé-Bezug) — eingebunden analog zum Exposé-Assistenten: nicht auf einer
einzelnen generischen Landingpage, sondern auf JEDER Berater-Seite einzeln, die
Seite selbst identifiziert per `berater_url` den zuständigen Berater. Nutzt
denselben MCP-Server und dasselbe Muster wie der Exposé-Assistent (`../chat/`),
aber:

- **kein** `expose_url` / `getExposeData` — Kaufpreis, PLZ und Objektart erfragt
  der Agent direkt im Gespräch,
- eigener System-Prompt (`../system-prompt-baufinanzierung.md`), fokussiert auf
  `createVorschlaege` / `getVorschlaege` (Berechnung & Optimierung),
- eigene Wissensdatenbank über das OpenAI `file_search`-Tool (Vector Store),
  zusätzlich zum MCP-Tool: `wissensbasis_baufinanzierung_chatbot_v1_4.json`
  (Stiftung-Warentest-Grundlagenwissen) ist bereits hochgeladen und als
  Vector Store `vs_6a6860fef3988191ab2a5c9015556e27` verknüpft (in
  `config.local.php`, s.u.).

```
Berater-Seite (DeepChat)  ──GET  /api/chat-baufinanzierung/resolve-advisor.php?url=<eigene Seite>──▶  advisor-resolver.php
     │                                                                                                       │
     │                                                                                                       └─◀ MCP-Server GET /gpt/berater?url=... (scrapeBeraterPage())
     │
     └──POST /api/chat-baufinanzierung/chat.php { berater_url: <eigene Seite>, … }──▶  chat.php
                                                                             │
                                                                             ├─ resolve_advisor() → dieselbe Live-Quelle wie oben
                                                                             ├─ OpenAI Responses API (Streaming)
                                                                             │     tools: [{ type: "mcp", … }, { type: "file_search", … }?]
                                                                             │
                                                                             └─◀ MCP-Server (createVorschlaege, getVorschlaege,
                                                                                   getCurrentDate — getExposeData/searchNearby/
                                                                                   submitContactInquiry werden per Prompt NICHT genutzt)
```

## Warum ein eigener Ordner statt eines gemeinsamen Endpoints?

`chat/chat.php` ist zwar generisch genug (Instructions-Datei und `expose_url`
sind optional), aber ein eigener Ordner hält die beiden Assistenten sauber
getrennt: eigener System-Prompt, eigener Session-Store
(`/tmp/ri24-chat-baufi-sessions`), eigene CORS-/Vector-Store-Konfiguration —
ohne den bestehenden, produktiv laufenden Exposé-Chat anzufassen.

## Bestandteile

| Datei | Zweck |
|---|---|
| `chat.php` | Streaming-Proxy: kapselt API-Key, ruft Responses API + MCP (+ optional file_search), hält Verlauf per `previous_response_id`, speist Berater-Kontaktdaten in die Instructions ein |
| `advisor-resolver.php` | `resolve_advisor()` — liest die Kontaktdaten primär LIVE von der Berater-Seite (`berater_url` → MCP `GET /gpt/berater`); Fallback: Dummy-Zuweisung aus `advisors.php` (URL-Parameter → Cookie → Zufall) |
| `advisors.php` | Dummy-Datenbasis für den Fallback (nur relevant, wenn `berater_url` fehlt oder der Live-Scrape fehlschlägt, z.B. lokale Testumgebung ohne Netzzugriff auf den MCP-Server) |
| `resolve-advisor.php` | JSON-Endpoint für die Berater-Seite: liefert die (Live- oder Fallback-)Kontaktdaten, setzt im Fallback-Fall das Sticky-Cookie |
| `config.php` | Konfiguration (Env-Variablen, optional `config.local.php`) |
| `config.local.php.example` | Vorlage für lokale Dev-Konfiguration |
| `embed-snippet.html` | Einbettungs-Snippet für die persönliche Berater-Seite (sendet `berater_url` = eigene Seiten-URL) — inkl. Finanzierungsrechner-Panel (zweiseitig mit dem Chat verknüpft, Position über `CALC_POSITION` konfigurierbar) |
| `partner-widget.js` | Widget-Engine für EXTERNE Berater-Webseiten (siehe „Externe Partner-Webseiten" unten) — feste `beraterId` statt Live-Scrape, Modi `bubble`/`inline`, inkl. Rechner-Panel |
| `partner-widget-snippet-{inline,bubble}-{rechner-oben,rechner-unten,nur-chat}.example.html` | 6 fertige Kopiervorlagen für externe Berater (Modus × Rechner-Layout) — pro Berater nur `teamDir` anpassen |
| `index.html` | Lokale Demo-Seite zum Testen (mit Feld für die zu testende Berater-URL, Layout-Umschalter Rechner oben/unten/nur Chat) |

### Woher kommen die Berater-Daten?

Das Widget wird — analog zur Einbindung des Exposé-Chats auf Exposé-Seiten —
direkt auf der **persönlichen Berater-Seite** eingebettet (z.B.
`.../vogtland/baufinanzierung/philipp-steppohn/`). Die Seite selbst ist damit
die Objekt-Referenz: `embed-snippet.html` schickt `window.location.href` als
`berater_url` mit jedem Chat-Request sowie beim initialen Abruf von
`resolve-advisor.php`. `advisor-resolver.php` liest daraus live Name, Titel,
Telefon/Mobil, E-Mail, Foto und Calendly-Link über den MCP-Server
(`GET /gpt/berater?url=...` → `scrapeBeraterPage()` in
`mcp-server/server/src/index.ts`, dieselbe `[data-xdata]`-Auswertung wie beim
Berater-Block des Exposé-Chats). Nur wenn das fehlschlägt, greift die
Dummy-Datenbasis `advisors.php` als Fallback.

## Konfiguration

Per Umgebungsvariablen **oder** `config.local.php` (siehe `*.example`):

| Variable | Bedeutung |
|---|---|
| `OPENAI_API_KEY` | OpenAI-Key (Pflicht) |
| `OPENAI_MODEL` | Modell, Default `gpt-4.1` |
| `MCP_SERVER_URL` | MCP-SSE-URL — derselbe Server wie beim Exposé-Chat (Pflicht) |
| `MCP_SERVER_LABEL` | Label, Default `ri24-baufi` |
| `MCP_AUTHORIZATION` | optionaler Auth-Header für den MCP |
| `CHAT_BAUFI_ALLOWED_ORIGINS` | CORS-Origins (kommagetrennt oder `*`) |
| `CHAT_BAUFI_INSTRUCTIONS_FILE` | Pfad zum System-Prompt, Default `../system-prompt-baufinanzierung.md` |
| `CHAT_BAUFI_VECTOR_STORE_ID` | OpenAI Vector-Store-ID für die custom Knowledge Base (optional, leer = kein `file_search`-Tool) |

## Vor dem Go-Live noch zu erledigen

1. **Widget auf den echten Berater-Seiten einbinden:** `embed-snippet.html`
   muss auf JEDER persönlichen Berater-Seite eingebunden sein (nicht auf einer
   einzelnen generischen Landingpage) — die Kontaktdaten werden pro Seite live
   über `berater_url` ermittelt (siehe „Woher kommen die Berater-Daten?" oben).
   Die Kontaktdaten werden **nicht mehr** fest im System-Prompt hinterlegt,
   sondern von `chat.php` dynamisch in die Instructions eingespeist (siehe
   `../system-prompt-baufinanzierung.md`, Abschnitt 6).
   `advisors.php` bleibt als **Fallback für Testumgebungen** (kein
   `berater_url` verfügbar, oder MCP-Server nicht erreichbar) — enthält
   weiterhin nur Dummy-Berater; für den Fallback-Fall in Produktion (sollte
   idealerweise nie eintreten) ggf. durch reale Platzhalter ersetzen.
2. **Produktions-`config.local.php` bzw. Env-Vars anlegen:** `OPENAI_API_KEY`,
   `MCP_SERVER_URL` und `CHAT_BAUFI_VECTOR_STORE_ID=vs_6a6860fef3988191ab2a5c9015556e27`
   setzen (lokal bereits in `config.local.php` hinterlegt, die Datei wird
   nicht eingecheckt).
3. **MCP-Server:** keine Änderung nötig — `createVorschlaege`/`getVorschlaege`
   sind bereits registriert und benötigen keine Objekt-ID.

### Knowledge Base — Stand & wichtiger Hinweis zur Nutzung

Die Wissensdatenbank (`wissensbasis_baufinanzierung_chatbot_v1_4.json`, Quelle:
Stiftung Warentest, Stand 2026-07-27) wurde als OpenAI-File hochgeladen und in
den Vector Store `vs_6a6860fef3988191ab2a5c9015556e27` eingebunden (Upload +
Verknüpfung erfolgten direkt über die OpenAI-API, nicht über den MCP-Server).

**Getestet und wichtig:** Mit `tools: [{type: "file_search", ...}]` allein
(ohne erzwungenen `tool_choice`) hat `gpt-4.1` die Dateisuche bei einer klar
einschlägigen Wissensfrage im ersten Test **nicht** aufgerufen und stattdessen
aus eigenem Vorwissen geantwortet. Deshalb wurde Abschnitt 7 des System-Prompts
so verschärft, dass die Dateisuche für Wissensfragen **zwingend zuerst**
aufgerufen werden muss ("MUSST du zuerst die Dateisuche aufrufen, bevor du
antwortest"). Mit dieser Formulierung hat das Modell im Test zuverlässig
`file_search_call` ausgelöst und die Antwort korrekt auf die in der
Wissensdatenbank hinterlegten Inhalte (inkl. `chatbot_instruction`/
`safety_rules`) gestützt. **Bei künftigen Prompt-Änderungen an Abschnitt 7
darauf achten, diese Formulierung nicht abzuschwächen**, sonst sinkt die
Trefferquote der Dateisuche wieder.

**Beim Aktualisieren der Wissensdatenbank** (neue Version der JSON-Datei):
1. Neue Datei hochladen: `POST https://api.openai.com/v1/files` mit
   `purpose=assistants`.
2. Neue `file_id` zum Vector Store hinzufügen:
   `POST https://api.openai.com/v1/vector_stores/vs_6a6860fef3988191ab2a5c9015556e27/files`.
3. Alte Datei-Version aus dem Vector Store entfernen (sonst überlagern sich
   alte und neue Inhalte in der Suche).
4. Kein Code-/Prompt-Change nötig — die Vector-Store-ID bleibt gleich.

## Lokal testen

```bash
cd chat-baufinanzierung
cp config.local.php.example config.local.php   # Werte eintragen (Key + ngrok-MCP-URL)
php -S localhost:8001                            # anderer Port als chat/ (8000)
```

Dann `index.html` öffnen und den Endpoint auf `http://localhost:8001/chat.php`
zeigen lassen.

## In Produktion einbinden

1. `chat-baufinanzierung/` auf den Server legen, sodass `chat.php` unter z.B.
   `https://www.regionalimmobilien24.de/api/chat-baufinanzierung/chat.php`
   erreichbar ist (gleiche Domain wie die Unterseite → kein CORS nötig).
2. `OPENAI_API_KEY` und `MCP_SERVER_URL` (Backend-MCP) als Umgebungsvariablen
   setzen — dieselben Werte wie beim Exposé-Chat sind hier ebenfalls gültig.
3. Inhalt aus `embed-snippet.html` in JEDE persönliche Berater-Seite
   übernehmen (nicht nur eine einzelne generische Landingpage — die Seite
   selbst identifiziert per `berater_url` den zuständigen Berater) und
   `ENDPOINT`/`RESOLVE_ADVISOR_ENDPOINT` auf die Produktionspfade setzen.

## Externe Partner-Webseiten (Berater mit eigener Domain)

Für Berater, die eine eigene, nicht auf regionalimmobilien24.de laufende
Webseite betreiben, gibt es zusätzlich `partner-widget.js`: Anders als
`embed-snippet.html` (Live-Scrape der eigenen RI24-Seite per `berater_url`)
wird hier die Berater-Zuordnung **vorab fest hinterlegt** — jede externe Seite
bekommt eine feste `beraterId`. Die Kontaktdaten selbst bleiben zentral in
`advisors.php` gepflegt; `resolve_advisor()` löst die ID genauso auf wie beim
`?berater=`-Deep-Link der Landingpage, nur dass hier nie ein Cookie/Zufall
zum Zug kommt, weil die ID bei jedem Request explizit mitgeschickt wird.

Zwei Darstellungsmodi, beide über dasselbe Skript, nur `mode` unterscheidet
sich:

- **`bubble`** (Floating-Launcher unten rechts, klappt beim Klick ein
  Chat-Panel auf) — die Partnerseite muss dafür nichts vorbereiten, das
  Skript baut Button + Panel selbst.
- **`inline`** (offenes Widget direkt im Seitenfluss, wie `embed-snippet.html`)
  — der Chat wird genau an der Stelle eingefügt, an der das `<script>`-Tag im
  HTML steht.

Einbindung: passende Kopiervorlage aussuchen — je eine Datei pro Kombination aus
Einbindungsmodus (`inline`/`bubble`) und Rechner-Layout (`rechner-oben`/`rechner-unten`/
`nur-chat`), insgesamt 6 fertige, sofort einsatzbereite Dateien:

- `partner-widget-snippet-inline-rechner-oben.example.html`
- `partner-widget-snippet-inline-rechner-unten.example.html`
- `partner-widget-snippet-inline-nur-chat.example.html`
- `partner-widget-snippet-bubble-rechner-oben.example.html`
- `partner-widget-snippet-bubble-rechner-unten.example.html`
- `partner-widget-snippet-bubble-nur-chat.example.html`

Die passende Datei an den Berater/die Partneragentur geben, nur `teamDir` anpassen (bei
`inline` zusätzlich die `id` des Ziel-`<div>` übernehmen):

```html
<div id="ri24_baufi_widget"></div> <!-- nur nötig bei layout: 'inline' -->
<script>
  window.RI24_BAUFI_PARTNER_WIDGET = {
    teamDir:   'philipp-steppohn',
    elementID: 'ri24_baufi_widget', // nur layout: 'inline' — Ziel-<div> für den Chat
    layout:    'bubble',
    color:     '#c0392b' // optional: Marken-Farbe des Partners statt RI24-Grün
  };
</script>
<script async defer src="https://www.regionalimmobilien24.de/api/chat-baufinanzierung/partner-widget.js"></script>
```

**Feldnamen:** Jede Option existiert unter zwei Namen — dem ursprünglichen (`beraterId`/
`mode`/`accentColor`) und dem Namen aus dem älteren Widget-Baukasten (`teamDir`/`layout`/
`color`), damit Backend-generierte Snippets für alle RI24-Partner-Widgets dieselben Feldnamen
verwenden können. Beide funktionieren (auch gemischt); ist ein Feld doppelt gesetzt, gewinnt
der neue Name. `elementID` und `open` gibt es nur unter dem neuen Namen (kein Alias).

`elementID` (optional, nur `layout: 'inline'`) benennt ein `<div>` auf der Partnerseite, in das
der Chat eingefügt wird — nötig, wenn das Skript mit `async`/`defer` geladen wird (empfohlen,
siehe Snippet oben), da `document.currentScript` beim Ausführen sonst bereits wieder `null`
ist. Ohne `elementID` fällt das Skript ersatzweise auf die Position direkt hinter dem eigenen
`<script>`-Tag zurück (setzt synchrones Laden voraus). Bei `layout: 'bubble'` ohne Wirkung.

`open` (optional, nur `layout: 'bubble'`, Default `false`) klappt das Chat-Panel direkt beim
Laden auf, statt auf den ersten Klick auf den Launcher-Button zu warten.

`color`/`accentColor` (optional, 6-stelliger Hex-Code) färbt alle Bedienelemente (Buttons,
Header, Launcher, Nutzer-Bubble, Rechner-Panel) in der Marken-Farbe des Partners. Der helle
Hintergrundton für die KI-Bubble und die Hinweis-Leiste wird automatisch als aufgehellte
Variante davon berechnet — Partner müssen nur eine Farbe angeben. Die Textfarbe AUF der
Akzentfarbe (Header, Buttons, Nutzer-Bubble) wird automatisch bestimmt (Anthrazit oder Weiß, je
nachdem was mehr Kontrast liefert), da manche Partnerfarben (und auch der RI24-Standardton) zu
hell für weißen Text sein können — `textcolor` überschreibt das optional fest. Fehlt `color`/
`accentColor` oder ist kein gültiger Hex-Code, bleibt es beim RI24-Standardgrün (`#BDE04F`).

`calcPosition` (optional, `'above'`/`'below'`/`'none'`, Default `'above'`) legt fest, ob das
Rechner-Panel über oder unter dem Chat erscheint (bei `layout: 'bubble'` innerhalb des
Popup-Panels) — oder mit `'none'` ganz entfällt (reine Chat-Variante ohne Rechner-Panel, für
Partner, die nur den Assistenten einbinden möchten). Kein Live-Umschalter für Endnutzer — pro
Partner/Integration fest gewählt.

**Vor dem Rollout an Partner:**

1. Externe Berater als neue Einträge in `advisors.php` anlegen (echte Daten,
   Struktur/Keys beibehalten).
2. `CHAT_BAUFI_ALLOWED_ORIGINS` um die jeweilige Partner-Domain erweitern
   (kommagetrennt) — oder `*` setzen. Da `chat.php`/`resolve-advisor.php` den
   `Access-Control-Allow-Origin`-Header immer mit der konkreten anfragenden
   Origin befüllen (nicht mit dem Literal `*`), funktioniert das auch mit
   `Access-Control-Allow-Credentials: true` zuverlässig für viele
   verschiedene Partner-Domains.
3. `partner-widget.js` unter der in den Snippets hinterlegten Produktions-URL
   erreichbar machen (Default: `/api/chat-baufinanzierung/partner-widget.js`
   auf `www.regionalimmobilien24.de`) — die URLs in `partner-widget.js` sind
   bewusst absolut, da das Skript im Kontext der fremden Partnerseite läuft.
4. Bekannte Grenze: kein Shadow DOM — global gesetzte CSS-Resets auf der
   Partnerseite können das Widget verformen. Für den ersten Rollout bewusst
   einfach gehalten; bei Problemen auf einzelnen Partnerseiten ggf. später
   nachrüsten.

## Hinweise

- **Server-Buffering aus:** wie bei `chat/chat.php` — bei nginx ggf.
  `proxy_buffering off;` für diesen Pfad setzen.
- **Terminbuchung:** analog zum aktuellen Exposé-Prompt bewusst nur als
  Selbstbuchungs-Link (kein automatisiertes `createCalendlyBooking` im
  Prompt) — siehe Projekt-Notiz zur Entfernung der Playwright/Calendly-
  Automatisierung wegen Zuverlässigkeitsproblemen.
