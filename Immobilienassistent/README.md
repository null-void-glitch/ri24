# Regionalimmobilien24 – Immobilienassistent (CustomGPT)

Ein CustomGPT-basierter Chatbot für Immobilien-Exposéseiten von Regionalimmobilien24.

## 🏠 Funktionen

| Funktion | Umsetzung |
|---|---|
| **Exposé-Informationen** | ChatGPT browst die Exposé-Seite direkt (gewhitelistet) |
| **Umgebungssuche** | ChatGPT nutzt seine eingebaute Websuche |
| **Finanzierungsberechnung** | Action → bestehender RI24-Endpunkt → Europace API |
| **Terminbuchung** | Action → Calendly-Proxy (Playwright) → Calendly-Widget |

## 📁 Projektstruktur

```
Immobilienassistent/
├── system-prompt.md                          # Instructions für den GPT-Builder
├── conversation-starters.md                  # Vorgeschlagene Gesprächseinstiege
├── angebote-api.md                           # Europace API-Dokumentation (Referenz)
├── actions/
│   ├── finanzierung-action.yaml              # OpenAPI-Schema (RI24-Endpunkt)
│   ├── finanzierung-action-direkt.yaml       # Alternative: Direkt gegen Europace
│   ├── umgebung-action-google.yaml           # Google Places Umgebungssuche
│   ├── calendly-action.yaml                  # Calendly Terminbuchung (Proxy)
│   └── kontakt-action.yaml                   # Kontaktanfrage (direkte POST-API)
└── calendly-proxy/                           # Playwright-basierter Proxy-Service
    ├── package.json
    ├── server.js                              # Express-Server (Port 3100)
    └── lib/
        ├── availability.js                    # Verfügbare Termine scrapen
        └── booking.js                         # Terminbuchung durchführen
```

## 🚀 Setup

### 1. GPT erstellen

1. Öffne [chat.openai.com](https://chat.openai.com) → **Explore GPTs** → **Create**
2. **Name:** Immobilienassistent
3. **Instructions:** Inhalt von `system-prompt.md` einfügen
4. **Conversation Starters:** Aus `conversation-starters.md` übernehmen
5. **Capabilities:** "Web Browsing" aktivieren

### 2. Finanzierungs-Action konfigurieren

1. Im GPT-Builder auf **Create new Action** klicken
2. Den YAML-Inhalt von `actions/finanzierung-action.yaml` einfügen
3. **Authentication:** None (öffentlicher Endpunkt auf eurer Domain)
4. **Privacy Policy URL** hinterlegen

### 3. Calendly-Buchungs-Action konfigurieren

1. Zusätzliche Action erstellen: YAML-Inhalt von `actions/calendly-action.yaml` einfügen
2. **Authentication:** None (der Proxy läuft auf eurer Domain)

### 4. Calendly-Proxy-Service deployen

```bash
cd calendly-proxy
npm install
npx playwright install chromium
npm start   # Startet auf Port 3100
```

**Auf dem Produktionsserver:**
- Der Service muss unter `https://www.regionalimmobilien24.de/ressource/get/calendly/` bzw. `/ressource/set/calendly/` erreichbar sein.
- Entweder per Reverse-Proxy (nginx/Apache) auf den Node.js-Service weiterleiten oder direkt in den bestehenden Server integrieren.

### 5. Testen

Starte eine Konversation mit einer Exposé-URL, z.B.:
```
https://www.regionalimmobilien24.de/immobilien/expose/?id=644525992
```

Für den Terminbuchungstest sage im Chat z.B.:
```
Ich möchte einen Beratungstermin beim Finanzierungsexperten buchen.
```

## 🔑 Kein Server nötig!

Der GPT nutzt ausschließlich:
- **Browse-Funktion** → Exposé-Seite lesen (gewhitelistet)
- **Websuche** → Umgebungsfragen beantworten
- **Bestehender RI24-Endpunkt** → `GET /ressource/get/europace/zins/{OID}.json` für Finanzierung

Kein eigener Middleware-Server, keine zusätzlichen API-Keys erforderlich.

## 📄 Dateien

| Datei | Zweck |
|---|---|
| `system-prompt.md` | In GPT-Builder unter "Instructions" einfügen |
| `conversation-starters.md` | Gesprächseinstiege für den GPT |
| `actions/finanzierung-action.yaml` | Action-Schema: nutzt euren bestehenden RI24-Europace-Endpunkt |
| `actions/finanzierung-action-direkt.yaml` | Alternative: geht direkt gegen die Europace API (OAuth2 nötig) |
| `actions/calendly-action.yaml` | Action-Schema: Calendly-Terminbuchung über Proxy |
| `actions/kontakt-action.yaml` | Action-Schema: Kontaktanfrage direkt per POST (ohne ReCaptcha/Playwright) |
| `calendly-proxy/` | Playwright-basierter Proxy-Service für Calendly |
| `angebote-api.md` | Europace API-Dokumentation als Referenz |
