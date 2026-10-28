# RI24 Immobilienassistent – DeepChat + PHP-Proxy

Eingebetteter Chatbot für die Exposé-Seiten. Der Chat läuft über **DeepChat**
(Frontend) und einen schlanken **PHP-Proxy** (`chat.php`), der den OpenAI-API-Key
kapselt und die **OpenAI Responses API** mit dem bestehenden **MCP-Server** als
Remote-Tool anspricht.

```
Exposé-Seite (DeepChat)  ──POST /api/chat/chat.php──▶  chat.php
                                                         │
                                                         ├─ OpenAI Responses API (Streaming)
                                                         │     tools: [{ type: "mcp", server_url: … }]
                                                         │
                                                         └─◀ MCP-Server (getExposeData, searchNearby,
                                                               Finanzierung, Vorschläge, Calendly, Kontakt)
```

## Bestandteile

| Datei | Zweck |
|---|---|
| `chat.php` | Streaming-Proxy: kapselt API-Key, ruft Responses API + MCP, hält Verlauf per `previous_response_id`, injiziert Exposé-URL |
| `config.php` | Konfiguration (Env-Variablen, optional `config.local.php`) |
| `config.local.php.example` | Vorlage für lokale Dev-Konfiguration |
| `embed-snippet.html` | Einbettungs-Snippet fürs Exposé-Template |
| `index.html` | Lokale Demo-Seite zum Testen |

## Funktionsweise

- **Streaming (SSE):** `chat.php` reicht die Antwort Token für Token an DeepChat
  durch (`data: {"text":"…"}`).
- **Verlauf:** über `previous_response_id`, serverseitig in der PHP-Session je
  `conversation_id` gehalten. DeepChat muss den Verlauf nicht selbst mitschicken.
  Wechselt die Exposé-URL, startet automatisch eine frische Konversation.
- **Exposé-Kontext:** DeepChat sendet `expose_url` versteckt mit; `chat.php`
  injiziert sie in die Instructions, der Agent ruft daraufhin `getExposeData` auf.
- **Instructions:** werden aus `../system-prompt.md` gelesen (Teil nach der ersten
  `---`-Linie). Anpassbar über `CHAT_INSTRUCTIONS_FILE`.

## Konfiguration

Per Umgebungsvariablen **oder** `config.local.php` (siehe `*.example`):

| Variable | Bedeutung |
|---|---|
| `OPENAI_API_KEY` | OpenAI-Key (Pflicht) |
| `OPENAI_MODEL` | Modell, Default `gpt-4.1` |
| `MCP_SERVER_URL` | MCP-SSE-URL. Dev: ngrok, Prod: Backend-MCP (Pflicht) |
| `MCP_SERVER_LABEL` | Label, Default `ri24` |
| `MCP_AUTHORIZATION` | optionaler Auth-Header für den MCP |
| `CHAT_ALLOWED_ORIGINS` | CORS-Origins (kommagetrennt oder `*`) |
| `CHAT_INSTRUCTIONS_FILE` | Pfad zum System-Prompt |

## Lokal testen

```bash
cd chat
cp config.local.php.example config.local.php   # Werte eintragen (Key + ngrok-MCP-URL)
php -S localhost:8000                            # PHP-Built-in-Server
```

Dann `index.html` öffnen (z.B. über denselben Server `http://localhost:8000/`
oder per Datei) und den in der Demo eingetragenen Endpoint auf
`http://localhost:8000/chat.php` zeigen lassen.

## In Produktion einbinden

1. `chat/` auf den Server legen, sodass `chat.php` unter z.B.
   `https://www.regionalimmobilien24.de/api/chat/chat.php` erreichbar ist
   (gleiche Domain wie das Exposé → kein CORS nötig).
2. `OPENAI_API_KEY` und `MCP_SERVER_URL` (Backend-MCP) als Umgebungsvariablen setzen.
3. Inhalt aus `embed-snippet.html` ins Exposé-Template übernehmen und `ENDPOINT`
   auf den Produktionspfad setzen.

## Hinweise

- **Server-Buffering aus:** `chat.php` setzt `X-Accel-Buffering: no`. Bei nginx
  ggf. zusätzlich `proxy_buffering off;` für diesen Pfad, damit das Streaming
  wirklich Token für Token ankommt.
- **UI-Widgets:** Einige MCP-Tools liefern OpenAI-Apps-SDK-Widgets
  (`openai/outputTemplate`). Die rendern nur im ChatGPT-Client, **nicht** in
  DeepChat – dort kommt der Text-/JSON-Output an.
- **PHP-Sessions:** Der Verlauf hängt an der PHP-Session (Cookie). Für horizontale
  Skalierung (mehrere Server) einen gemeinsamen Session-Store (Redis o.ä.)
  verwenden oder auf ein zustandsloses Verfahren wechseln.
