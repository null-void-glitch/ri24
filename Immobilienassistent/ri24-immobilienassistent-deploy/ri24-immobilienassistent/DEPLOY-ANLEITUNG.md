# RI24 Immobilienassistent – Deploy-Anleitung für Backend

Dieses Paket bringt den **bereits laufenden MCP-Server auf den vollen aktuellen
Funktionsstand** und liefert den dazugehörigen **Chat-Proxy** (PHP) für die
Einbindung in die Exposé-Seiten.

> **Kurzfassung für Eilige**
> 1. MCP-Server: `mcp-server/server/src/` in das bestehende Server-Repo
>    übernehmen, `npm install && npm run build`, Dienst neu starten.
> 2. Chat-Proxy: Ordner `chat/` unter `…/api/chat/` ablegen, `config.local.php`
>    (oder Env-Vars) mit OpenAI-Key + `MCP_SERVER_URL` befüllen.
> 3. Im Exposé-Template den Inhalt aus `chat/embed-snippet.html` einbinden.

---

## 1. Architektur

```
 Browser (Exposé-Seite)
   │  DeepChat-Widget (embed-snippet.html)
   │  POST /api/chat/chat.php   { text, expose_url, conversation_id }
   ▼
 chat.php  (PHP-Proxy, kapselt den OpenAI-Key)
   │  OpenAI Responses API (stream:true)
   │  tools:[{ type:"mcp", server_url: MCP_SERVER_URL }]
   ▼
 MCP-Server  (Node/Express, SSE unter /mcp/sse, Port 3000)
   │  getExposeData, searchNearby, Finanzierung, Vorschläge,
   │  Calendly, Kontaktanfrage …
   ▼
 regionalimmobilien24.de  (OpenImmo-Feed, Europace, Kontakt-Endpoint)
   + Google Places + Calendly
```

Der **OpenAI-API-Key liegt ausschließlich im PHP-Proxy** – niemals im Frontend.
Der MCP-Server wird von OpenAI als **Remote-MCP-Tool** angesprochen, muss also
öffentlich per **HTTPS** erreichbar sein.

---

## 2. Paketinhalt

```
ri24-immobilienassistent/
├── DEPLOY-ANLEITUNG.md              ← dieses Dokument
├── system-prompt.md                 ← Agent-Instructions (von chat.php gelesen)
├── chat/                            ← PHP-Proxy + Frontend-Einbindung
│   ├── chat.php                     ← Streaming-Proxy (Responses API + MCP)
│   ├── config.php                   ← liest Env-Vars / config.local.php
│   ├── config.local.php.example     ← Vorlage für lokale Konfiguration
│   ├── embed-snippet.html           ← Einbettungs-Snippet fürs Exposé-Template
│   ├── index.html                   ← Standalone-Demo
│   ├── test-expose.html             ← Test-Exposé
│   ├── beispiel-expose-prototyp.html← Referenz: Inline- + Popup-Einbindung
│   ├── heyregio.svg                 ← Branding-Logo
│   └── README.md                    ← Detail-Doku zum Proxy
└── mcp-server/                      ← erweiterter MCP-Server (Monorepo: server + web)
    ├── package.json                 ← npm-Workspaces-Root (baut server + web)
    ├── CHATGPT-APP-DEPLOYMENT.md    ← erprobte Deploy-Anleitung der ChatGPT-App (FreeBSD/nginx/SSL)
    ├── server/                      ← MCP-Server (Node/Express)
    │   ├── src/{index,db,calendly,contact}.ts
    │   ├── package.json
    │   ├── tsconfig.json
    │   └── .env.example
    ├── web/                         ← React-Widget der ChatGPT-App (real-estate-board)
    │   ├── src/…, index.html, vite.config.ts, tailwind.config.js …   ← Quelle (neu baubar)
    │   └── dist/                    ← vorgebautes Widget-Bundle, PFLICHT für `search_real_estate`
    ├── calendly-cookies.json        ← ⚠️ sensibel: Calendly-Admin-Session
    └── deploy/
        ├── nginx-ri24-mcp.conf      ← nginx-Reverse-Proxy (SSE-tauglich)
        └── ri24_mcp.rc              ← FreeBSD-rc.d-Service-Script
```

---

## 3. Teil A – MCP-Server aktualisieren

### 3.1 Was ist neu ggü. dem aktuell deployten Stand

Der aktuell laufende Server hat einen **älteren Funktionsstand**. Dieses Paket
enthält den **kompletten aktuellen Umfang**. Am einfachsten und sichersten:
`server/src/` **vollständig ersetzen** und neu bauen – dann ist garantiert alles
enthalten. Die wesentlichen Ergänzungen gegenüber dem alten Stand:

- **Kontaktanfrage** (`submitContactInquiry`) – sendet an den internen
  Chatbot-Kontakt-Endpoint.
- **Personalisierte Finanzierungs-Vorschläge** (`createVorschlaege` /
  `getVorschlaege`) über die Europace-Vorschläge-API.
- **428/451-Bot-Wall-Bypass** für `regionalimmobilien24.de` (pitcom „Bin ich ein
  Roboter?"): der Server holt sich per Handshake ein `human`-Cookie und
  wiederholt geblockte Requests automatisch (siehe `index.ts`, Abschnitt
  „pitcom … Bypass").
- **Calendly-Verfügbarkeit + Buchung** und der komplette **Finanzierungs-Flow**
  (`createProcessCode` / `getFinanzierung` / `updateFinanzierung`).

> ✅ **Die ChatGPT-App bleibt vollständig erhalten.** Die aktuelle Quelle ist ein
> **Superset** des deployten Builds: Die grafische Immobiliensuche `search_real_estate`
> samt Widget (`real-estate-board`) und Domain-Verifizierung ist unverändert enthalten
> (siehe 3.8) – es kommen nur die oben genannten Funktionen hinzu. Beim Ersetzen von
> `server/src/` gehen die ChatGPT-App-Funktionen **nicht** verloren; `web/dist/`
> ebenfalls beibehalten.

### 3.2 Vollständiger Funktionsumfang (registrierte MCP-Tools)

| Tool | Zweck |
|---|---|
| `ping` | Health-Check |
| `search_real_estate` | **ChatGPT-App:** Immobiliensuche über den OpenImmo-Bestand (Ort, Preis, Zimmer, Ausstattung/Soft-Filter). Liefert die Treffer als **grafisches Widget** (`ui://widget/real-estate-board.html`) im ChatGPT-Client. Siehe Abschnitt 3.8. |
| `getExposeData` | Exposé-Daten (Preis, Makler, Finanzberater) per URL laden |
| `searchNearby` | POIs in der Umgebung via Google Places (Schulen, ÖPNV …) |
| `getCurrentDate` | Heutiges Datum + nächste 30 Tage (für relative Zeitangaben) |
| `createProcessCode` | Finanzierungsberechnung starten (ProcessCode) |
| `getFinanzierung` | Finanzierungsangebote zum ProcessCode abrufen |
| `updateFinanzierung` | Finanzierungsparameter anpassen |
| `createVorschlaege` | Personalisierte Vorschläge-Berechnung starten (anfrageId) |
| `getVorschlaege` | Personalisierte Vorschläge abrufen |
| `getCalendlyAvailability` | Freie Termine eines Finanzierungsberaters (Calendly) |
| `createCalendlyBooking` | Beratungstermin über Calendly buchen/vorbefüllen |
| `submitContactInquiry` | Kontaktanfrage über das Exposé-Kontaktformular senden |

### 3.3 Voraussetzungen

- **Node.js ≥ 18** (empfohlen 20). `fetch` wird nativ genutzt.
- Für die **Calendly-Tools**: Playwright-Chromium (headless Browser-Automation):
  ```bash
  npx playwright install chromium
  # ggf. Systempakete für Chromium (Linux: npx playwright install-deps)
  ```
- Ausgehende HTTPS-Verbindungen zu `regionalimmobilien24.de`,
  `zbv.regionalimmobilien24.de`, Google Places und `calendly.com`.

### 3.4 Environment-Variablen (`.env`)

Aus `mcp-server/server/.env.example` (die Werte sind bereits die produktiven
Feed-Zugangsdaten – bitte im Team verifizieren):

| Variable | Bedeutung |
|---|---|
| `OPENIMMO_URL` | OpenImmo-Export-URL (Objektdatenbank) |
| `OPENIMMO_USER` / `OPENIMMO_PASS` | Basic-Auth für den Feed |
| `REFRESH_INTERVAL_HOURS` | (optional) XML-Refresh-Intervall, Default `24` |

Der Server lädt den OpenImmo-Feed **beim Start** herunter (mehrere hundert MB) und
danach periodisch.

> ⚠️ **Google-Places-Key ist aktuell hardcodiert** in `index.ts` (im `searchNearby`-
> Tool, ca. Z. 506 und 1147). Empfehlung: den Key per **API-/IP-Restriction**
> absichern und mittelfristig in eine Env-Variable auslagern. Wird die Umgebungs-
> suche nicht benötigt, kann `searchNearby` deaktiviert werden.

### 3.5 Build & lokaler Start

**Empfohlen – kompletter Workspace-Build (Server + ChatGPT-App-Widget):**

```bash
cd mcp-server
npm install                   # installiert server- und web-Workspace
npm run build                 # baut server (tsc → server/dist) UND web (vite → web/dist)
cd server
cp .env.example .env          # Werte prüfen/eintragen
node dist/index.js            # lauscht auf http://0.0.0.0:3000  →  /mcp/sse
```

Alternativ nur den Server bauen (das vorgebaute `web/dist/` bleibt erhalten):

```bash
cd mcp-server/server && cp .env.example .env && npm install && npm run build && node dist/index.js
```

> **Wichtig:** Das `web/dist/`-Bundle nicht löschen – es wird für die grafische
> ChatGPT-App-Immobiliensuche gebraucht (Abschnitt 3.8).

> Für Entwicklung ohne Build: `npm run dev` (nutzt `tsx`).

**Wichtig zu den relativen Pfaden:** Der Server erwartet als Arbeitsverzeichnis
den Ordner `server/`. Er greift auf **Geschwister-Ordner** zu:
`../web/dist/assets` (React-Widget-Bundle der ChatGPT-App, siehe 3.8) und `../calendly-cookies.json`
(Calendly-Session). Die Ordnerstruktur dieses Pakets bitte **so beibehalten**
(`mcp-server/server`, `mcp-server/web`, `mcp-server/calendly-cookies.json`).

### 3.6 Als Dienst betreiben

- **FreeBSD:** `deploy/ri24_mcp.rc` nach `/usr/local/etc/rc.d/ri24_mcp` kopieren,
  Server nach `/opt/ri24-mcp/server` legen (`web/` + `calendly-cookies.json` als
  Geschwister), in `/etc/rc.conf` aktivieren:
  ```
  ri24_mcp_enable="YES"
  ri24_mcp_dir="/opt/ri24-mcp/server"
  ri24_mcp_user="www"
  ```
  `service ri24_mcp start`. (Auf Linux analog per **systemd**-Unit: `WorkingDirectory`
  = server-Ordner, `ExecStart=/usr/bin/node dist/index.js`, `EnvironmentFile=.env`.)

- **nginx** (Reverse-Proxy, TLS, SSE-tauglich): `deploy/nginx-ri24-mcp.conf`
  anpassen (Server-Name + Zertifikatspfade). Entscheidend für Streaming:
  `proxy_buffering off;` und lange `proxy_read_timeout`. Der öffentliche
  MCP-Endpoint ist dann `https://<mcp-domain>/mcp/sse`.

### 3.7 ⚠️ Calendly-Session (sensibel)

`calendly-cookies.json` enthält eine **Admin-Session für calendly.com**. Sie ist
nötig, damit `getCalendlyAvailability` / `createCalendlyBooking` funktionieren.
Diese Cookies **laufen ab** – bei Fehlern in den Calendly-Tools muss die Datei
erneuert werden (frische Cookies eines eingeloggten Calendly-Admins). Datei
**vertraulich behandeln**, nicht in öffentliche Repos einchecken.

Funktionieren die Calendly-Tools nicht (fehlende Cookies / kein Chromium), bleibt
der Rest des Assistenten voll nutzbar – lediglich Terminabruf/-buchung entfällt.

### 3.8 ChatGPT-App (grafische Immobiliensuche) — NICHT verlieren!

Derselbe MCP-Server bedient **zwei** Szenarien. Beim Update den ChatGPT-App-Teil
unbedingt erhalten:

1. **DeepChat-Exposé-Assistent** (Teil B): Chat im Exposé, Text/JSON-Antworten.
2. **ChatGPT-App / Connector**: Der Server ist als Connector in ChatGPT einbindbar.
   Das Tool **`search_real_estate`** durchsucht den OpenImmo-Bestand und gibt die
   Treffer als **grafisches React-Widget** (`ui://widget/real-estate-board.html`)
   direkt im ChatGPT-Client aus (Immobilien-Board mit Bildern, Preis, Eckdaten).

Damit die ChatGPT-App funktioniert, sind zwingend nötig:

- **`web/dist/`** – das gebaute React-Widget-Bundle. Der Server liest es beim
  Tool-Aufruf aus `../web/dist/assets/` (relativ zum `server/`-Verzeichnis). Fehlt
  es, zeigt ChatGPT statt des Boards nur einen Platzhalter. **Beim Rebuild also die
  `web`-Workspace mitbauen** (`npm run build` im Root baut `server` **und** `web`)
  bzw. das mitgelieferte `web/dist/` beibehalten.
- **Domain-Verifizierung:** Der Server beantwortet `GET /.well-known/openai-apps-challenge`.
  ChatGPT nutzt das zur Verifizierung der MCP-Domain.
- **HTTPS** (siehe nginx-Config) – ChatGPT verbindet sich ausschließlich per HTTPS.

**MCP-Server-URL für den ChatGPT-Connector:** `https://<mcp-domain>/mcp/sse`

> Eine ausführliche, erprobte Schritt-für-Schritt-Anleitung speziell für dieses
> ChatGPT-App-Deployment (FreeBSD, nginx, SSL, ChatGPT-Connector) liegt dem Paket
> als **`mcp-server/CHATGPT-APP-DEPLOYMENT.md`** bei.

> **Hinweis zur Tool-Sichtbarkeit:** `search_real_estate` wird über `registerAppTool`
> (Apps SDK) registriert, die übrigen Tools über `registerTool`. Alle sind Teil
> desselben Servers und werden gemeinsam über `/mcp/sse` ausgeliefert.

---

## 4. Teil B – Chat-Proxy (PHP) einbinden

### 4.1 Voraussetzungen

- **PHP ≥ 8.0** mit **cURL**-Extension.
- Erreichbar unter derselben Domain wie das Exposé (dann **kein CORS** nötig),
  z. B. `https://www.regionalimmobilien24.de/api/chat/chat.php`.

### 4.2 Konfiguration

Konfiguration per **Umgebungsvariablen** *oder* per `config.local.php`
(Kopie von `config.local.php.example`, wird von `config.php` automatisch geladen):

| Variable / Konstante | Bedeutung |
|---|---|
| `OPENAI_API_KEY` | OpenAI-Key (**Pflicht**, nur serverseitig!) |
| `OPENAI_MODEL` | Modell, Default `gpt-4.1` |
| `MCP_SERVER_URL` | **öffentliche** MCP-SSE-URL → `https://<mcp-domain>/mcp/sse` (**Pflicht**) |
| `MCP_SERVER_LABEL` | Label, Default `ri24` |
| `MCP_AUTHORIZATION` | optionaler Auth-Header für den MCP (leer, wenn keiner) |
| `CHAT_ALLOWED_ORIGINS` | CORS-Origins (kommagetrennt oder `*`); prod: die Exposé-Domain |
| `CHAT_INSTRUCTIONS_FILE` | Pfad zum System-Prompt, Default `../system-prompt.md` |

> `system-prompt.md` muss **eine Ebene über** `chat/` liegen (wie in diesem Paket),
> sonst `CHAT_INSTRUCTIONS_FILE` explizit setzen.

Empfehlung für Produktion: Key & URL als **Env-Vars** setzen, **nicht** als Datei.

### 4.3 Frontend einbinden

1. Inhalt aus `chat/embed-snippet.html` ins Exposé-Template übernehmen.
2. Im Snippet die Konstante `ENDPOINT` auf den Produktionspfad setzen
   (z. B. `/api/chat/chat.php`) und `EXPOSE_URL` auf `window.location.href`.
3. `beispiel-expose-prototyp.html` zeigt eine vollständige Referenz mit **Inline-**
   *und* **Popup-Einbindung** des Widgets inkl. heyRegio-Branding.

Hinweis: `chat.php` setzt `X-Accel-Buffering: no`. Falls ein nginx davor steht,
für diesen Pfad zusätzlich `proxy_buffering off;` setzen, damit das Streaming
token-weise ankommt.

---

## 5. Verdrahtung & Test

1. MCP-Server läuft und ist öffentlich erreichbar – Smoke-Test:
   ```bash
   curl -N https://<mcp-domain>/mcp/sse
   # erwartet:  event: endpoint  /  data: /mcp/sse?sessionId=…
   ```
2. `MCP_SERVER_URL` im PHP-Proxy auf genau diese `…/mcp/sse`-URL setzen.
3. Exposé-Seite öffnen, Frage stellen (z. B. „Was bietet diese Immobilie?").
   Der Agent ruft `getExposeData` auf und antwortet gestreamt.
4. Golden-Prompts durchspielen: Umgebung (`searchNearby`), Finanzierung
   (`createProcessCode`→`getFinanzierung`), Termin (`getCalendlyAvailability`),
   Kontakt (`submitContactInquiry`).

---

## 6. Sicherheit & Betrieb

- **OpenAI-Key** nur im PHP-Proxy / als Server-Env – nie im Frontend, nie im Repo.
- **`calendly-cookies.json`** und **`.env`** enthalten Geheimnisse → aus
  öffentlichen Repos ausschließen, restriktive Dateirechte.
- **Gesprächsverlauf:** `chat.php` hält den Verlauf per `previous_response_id` in
  einem serverseitigen **Datei-Store**, gekeyt auf die vom Client gesendete
  `conversation_id` (`sys_get_temp_dir()/ri24-chat-sessions/`). Bewusst **nicht**
  über die PHP-Session/Cookie – sonst geht der Verlauf bei cross-origin-Einbindung
  oder Cookie-Blocking verloren (Agent verliert sein Gedächtnis). Für horizontale
  Skalierung (mehrere Server) den Store durch einen gemeinsamen Speicher (z. B.
  Redis) ersetzen; der Store-Verzeichnispfad muss beschreibbar sein.
- **UI-Widgets / zwei Ausgabewege:** `search_real_estate` liefert ein
  Apps-SDK-Widget (`openai/outputTemplate`, `ui://widget/real-estate-board.html`),
  das **im ChatGPT-Client grafisch** rendert (dafür ist `web/dist/` **erforderlich**,
  siehe 3.8). In DeepChat (Exposé-Assistent) rendern diese Widgets nicht – dort
  kommt Text/JSON an. **Der Server bedient beide Wege gleichzeitig**; `web/dist/`
  ist nur dann verzichtbar, wenn die ChatGPT-App **nicht** genutzt wird.
- **Logging:** Tool-Call-IDs, Latenzen und Fehlerpayloads mitschreiben; der Server
  loggt bereits ausführlich nach stdout (bei rc/systemd ins Logfile).
