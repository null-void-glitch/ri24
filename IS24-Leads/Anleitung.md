# IS24-Leads – Anleitung

Kleines Python-Tool, das Baufinanzierungs-Leads aus der ImmoScout24-API
abholt, vereinheitlicht und als JSON-Datei für den CRM-Import ablegt.

## Ablauf der Anwendung

1. **Authentifizierung** (`auth.py`) – OAuth 1.0a 3-Legged-Flow gegen die
   IS24-Sandbox. Beim ersten Lauf wird ein Autorisierungs-Link geöffnet,
   der Verifier in der Konsole eingegeben und das Access-Token in
   `tokens.json` zwischengespeichert. Folgeläufe nutzen das Token
   automatisch.
2. **Konfiguration laden** (`config.py` / `config.json`) – legt fest, für
   welche `scoutId`s Leads geholt werden: ein organisationsweiter Pool und
   beliebig viele Berater-Pools.
3. **Leads abrufen** (`client.py`) – ruft pro `scoutId` den Endpunkt
   `GET /financing/construction/v2/lead` mit Zeitfenster (`from` / `to`)
   bzw. `test=true` auf.
4. **Validieren & Verpacken** (`schema.py`) – Antwort wird via Pydantic
   geprüft, jeder Lead in ein `LeadEnvelope` mit Pool-Tag und Abrufzeit
   verpackt. Duplikate (gleiche Lead-ID in mehreren Pools) werden anhand
   der ID verworfen.
5. **Ausgabe** – die Sammelmenge wird nach
   `out/leads-<ISO-Timestamp>.json` geschrieben und kann vom CRM
   eingelesen werden.

## Voraussetzungen

- Python 3.10+
- Abhängigkeiten: `pip install requests requests_oauthlib pydantic`
- `credentials.txt` mit den Sandbox-Keys (Consumer Key / Consumer Secret)
- `config.json` mit den eigenen `scoutId`s

## Leads abholen

Aus dem Projektverzeichnis ausführen:

```bash
# Erstmaliger Lauf – führt den OAuth-Dialog durch
python3 sync.py --test

# Echte Leads der letzten 24 Stunden
python3 sync.py

# Explizites Zeitfenster
python3 sync.py --since 2026-05-20T00:00:00 --until 2026-05-27T00:00:00

# Anderes Config-File
python3 sync.py --config ./meine-config.json
```

Beim ersten Lauf:

1. Browser öffnet die IS24-Autorisierungsseite (Sandbox-Login wird in der
   Konsole angezeigt).
2. Nach Freigabe wird ein Verifier-Code angezeigt – diesen ins Terminal
   einfügen.
3. Das resultierende Access-Token landet in `tokens.json`; spätere Läufe
   benötigen keinen Browser mehr.

## Leads in das CRM einspielen

1. Nach dem Lauf liegt im Ordner `out/` eine Datei
   `leads-<Timestamp>.json` mit einer Liste von Envelope-Objekten:

   ```json
   {
     "pool": "advisor:alice",
     "fetched_at": "2026-06-01T08:36:01Z",
     "lead": { ... Original-Lead von IS24 ... }
   }
   ```

2. Diese Datei dem CRM zur Verfügung stellen (Upload, Shared Folder,
   o. Ä.). Das Feld `pool` steuert, in welchen Berater-Posteingang der
   Lead einsortiert wird (`organization` oder `advisor:<name>`).
3. Bereits importierte Leads erkennt das CRM anhand der `lead.id`; die
   Sync-Routine entfernt selbst nur Duplikate innerhalb eines Laufs.
4. Wiederholungslauf z. B. per Cron einplanen (typisch: stündlich oder
   täglich mit passendem `--since`-Fenster).

## Umstellung Sandbox → Production

Aktuell zeigt die App ausschließlich auf die IS24-Sandbox. Für den
Produktivbetrieb sind folgende Anpassungen nötig:

1. **Basis-URL umstellen** (`auth.py`)
   - `SANDBOX_BASE` durch die Live-URL ersetzen, z. B.
     `https://rest.immobilienscout24.de`.
   - Dadurch passen sich auch `REQUEST_TOKEN_URL`, `AUTHORIZE_URL`,
     `ACCESS_TOKEN_URL` und (über `client.py`) `LEAD_URL` automatisch an.
   - Sauberer wäre, die Basis-URL über eine Umgebungsvariable
     (`IS24_BASE_URL`) oder ein Feld in `config.json` steuerbar zu machen,
     damit Sandbox/Prod ohne Code-Änderung wechselbar sind.
2. **Produktiv-Credentials nutzen** (`credentials.txt`)
   - Statt `Sandbox API Secret / Consumer Secret` den produktiven
     `API Secret / Consumer Secret` verwenden (`System Key` bleibt gleich,
     sofern der Key für Prod freigeschaltet wurde).
   - Die Key-Auswahl in `auth.get_session()` entsprechend anpassen.
3. **Sandbox-Login aus dem OAuth-Dialog entfernen** (`auth.py`,
   `_oauth_dance`)
   - Den fest eingetragenen Testbenutzer (`is24_tuv_…@is24test.com`) aus
     der Konsolenausgabe streichen – in Prod loggt sich der echte
     IS24-Account des Kunden ein.
4. **Frisches Access-Token erzeugen**
   - `tokens.json` löschen, damit der OAuth-Dance einmalig gegen die
     Live-Umgebung läuft. Sandbox-Tokens sind in Prod ungültig.
5. **Produktive `scoutId`s eintragen** (`config.json`)
   - Die Sandbox-`scoutId` (`19003525`) durch die echten IDs der
     Organisation bzw. der Berater ersetzen.
6. **Freischaltung bei IS24 prüfen**
   - Der Consumer Key muss vom IS24-Partnerdienst für den Endpunkt
     `financing/construction/v2/lead` in Produktion freigeschaltet sein.
7. **Betriebliches Drumherum**
   - `credentials.txt` und `tokens.json` aus dem Repo halten
     (`.gitignore`) und über ein Secret-Management (z. B. Vault, KMS,
     `.env` mit restriktiven Rechten) bereitstellen.
   - Logging/Monitoring des Cron-Jobs einrichten, da Fehlläufe in Prod
     direkt zu verpassten Leads führen.

## Wichtige Dateien

| Datei              | Zweck                                            |
| ------------------ | ------------------------------------------------ |
| `sync.py`          | Einstiegspunkt, orchestriert den kompletten Lauf |
| `auth.py`          | OAuth-Handshake & Token-Cache                    |
| `client.py`        | HTTP-Aufruf des Lead-Endpoints                   |
| `schema.py`        | Pydantic-Modelle & Envelope                      |
| `config.py`        | Lade- und Pool-Logik                             |
| `config.json`      | scoutId-Konfiguration                            |
| `credentials.txt`  | Consumer Key/Secret (nicht einchecken)           |
| `tokens.json`      | Gecachtes Access-Token (nicht einchecken)        |
| `out/`             | Erzeugte Lead-JSON-Dateien                       |
