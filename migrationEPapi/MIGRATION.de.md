# Migration: Angebote v2 `ermittlung` → Vorschläge API

Migration des abzuschaltenden Aufrufs **`POST /v2/ergebnisliste/ermittlung`** (mit
`ErfassteDaten`-Body und **ohne** `vorgangsNummer`) auf die **Vorschläge API**.

- **Frist:** Der v2-Endpunkt wird **Ende November 2026** abgeschaltet.
- **Warum Vorschläge (und nicht Angebote v3):** Der Migrationsleitfaden besagt, dass
  `POST /v2/ergebnisliste/ermittlung` mit `ErfassteDaten`-Body und ohne `vorgangsNummer`
  **kein Äquivalent in der Angebote API v3** hat (v3 erfordert immer `{vorgangsnummer}` im
  Pfad). Für Berechnungen ohne bestehenden Vorgang ist die dokumentierte Ablösung die
  **Vorschläge API**.
- **Scope-Entscheidungen für diese Migration:**
  - Nur Berechnen & Anzeigen — **kein API-Merken** (`gemerkteAngebote` / gespeicherte Angebote).
  - Daher wird nur der OAuth-Scope **`baufinanzierung:angebote:ermitteln`** benötigt
    (nicht `baufinanzierung:vorgaenge:schreiben`), und es wird keine `vorgangsnummer` persistiert.

---

## 1. Änderung auf Endpunkt-Ebene

| Aspekt | Alt (v2 ermittlung) | Neu (Vorschläge API) |
|---|---|---|
| Host | Angebote-v2-Host (`Configuration::getHost(2)`) | `baufinanzierung.api.europace.de` |
| Aufrufmuster | **1 synchroner** POST | **2-stufig asynchron**: POST, dann GET pollen |
| Endpunkt(e) | `POST /v2/ergebnisliste/ermittlung` | `POST /v1/vorschlaege` → `GET /v1/vorschlaege/{anfrageId}` |
| Request-Body | `ErfassteDaten` | `{ metadaten, kundenangaben }` |
| Berechnungs-Optionen | Query-Parameter: `alternativen`, `produktAnbieter`, `excludierteProduktAnbieter`, `provisionsAusgabe` | `metadaten.gewuenschteAnzahlVorschlaege` + (optional) `finanzierungsbedarf.praeferenzen` |
| Erfolgs-Antwort | `ErmittlungResponce` (`ermittlungsId` + `ergebnisse[]`) | POST → `{ anfrageId }`; Poll → `202` (erneut versuchen) oder `200` `{ vorschlaege[], leadRating }` |
| Ergebnis-IDs | `ermittlungsId` / `ergebnisNummer` | `anfrageId` / `finanzierungsVorschlagId` |
| OAuth-Scope | (bestehend) | **`baufinanzierung:angebote:ermitteln`** |
| Anbietername für UI | Ergebnisfeld | `vorschlaege[].finanzierungsbausteine[].produktAnbieter` (in der `200`-Antwort) |

**Asynchroner Ablauf:**
```
POST /v1/vorschlaege            → 200 { "anfrageId": "passende-vorschlaege-..." }
GET  /v1/vorschlaege/{anfrageId} → 202  (Ermittlung läuft → erneut versuchen)
                                 → 200  { "vorschlaege": [...], "leadRating": {...} }
```

---

## 2. Erledigte Schritte

1. **Geprüft**: den Migrationsleitfaden, die Vorschläge-API-Dokumentation und den
   bestehenden PHP-Client (`EliV2RestControllerApi.php`).
2. **Ziel bestätigt**: Vorschläge API (kein Angebote-v3-Äquivalent für den Fall ohne Vorgang).
3. **Scope reduziert**: kein Merken → nur ein Scope, keine Vorgangs-Persistierung.
4. **Quell-Datenmodell inspiziert** (`ErfassteDaten` und alle verschachtelten Leaf-Modelle),
   um ein exaktes Feld-Mapping zu erstellen.
5. **Request-Body-Mapper gebaut**: [`VorschlaegeRequestMapper.php`](./VorschlaegeRequestMapper.php)
   — bildet `ErfassteDaten` → `{ metadaten, kundenangaben }` als einfaches Array für `json_encode()` ab.

Verwendung:
```php
$body = (new VorschlaegeRequestMapper())->map($erfassteDaten, 3); // 3 = gewuenschteAnzahlVorschlaege
$json = json_encode($body); // Request-Body für /v1/vorschlaege
```

---

## 3. Feld-Mapping (alt `ErfassteDaten` → neu `kundenangaben`)

Legende: ✅ implementiert & gegen das Modell verifiziert · ⚠️ implementiert, Wert muss
verifiziert werden · 🔵 bewusst zurückgestellt · 🟠 noch nicht gemappt (benötigt weitere Angaben)

### 3.1 `metadaten`
| Neues Feld | Quelle (alt) | Status | Hinweise |
|---|---|---|---|
| `datenkontext` | `ErfassteDaten.datenKontext` | ⚠️ | Quell-Enum `TEST_MODUS` / `ECHT_GESCHAEFT`; Produktiv-Literal im Vorschläge-YAML verifizieren. |
| `extKundenId` | `ErfassteDaten.externeVorgangsNummer` | ⚠️ | Bestätigen, dass dies die beabsichtigte Quelle ist. |
| `extClientId` | — | 🟠 | Aktuell `null`; aus `getLeadTracking()` befüllen, falls eine Client-ID getrackt wird. |
| `gewuenschteAnzahlVorschlaege` | Methoden-Parameter | ✅ | Ersetzt den alten Query-Parameter `alternativen`. |

### 3.2 `kundenangaben.haushalte[]` ← `ErfassteDaten.haushalte[]` (`Haushalt[]`)

**`kunden[]` ← `Haushalt.antragsteller[]` (`Antragsteller[]`)**

| Neues Feld | Quellpfad | Status | Hinweise |
|---|---|---|---|
| `geburtsdatum` | `Antragsteller.geburtsdatum` | ✅ | `DateTime` → `Y-m-d`. |
| `einkommenNetto` | `Antragsteller.beschaeftigung.einkommenNettoMonatlich` | ✅ | Monatliches Netto — genau das, was Vorschläge erwartet (Nettoeinkommen liegt an `Beschaeftigung`, **nicht** an `Antragsteller`). |
| `beschaeftigungsArt` | `Antragsteller.beschaeftigung.art` | ⚠️ | Enum-gemappt (`BESCHAEFTIGUNGS_ART_MAP`); `HAUSFRAU`/`ARBEITSLOSER` verifizieren. |
| `beschaeftigtSeit` | `Antragsteller.beschaeftigung.beschaeftigtSeit` | ✅ | `DateTime` → `Y-m-d`. |
| `arbeitBefristet` | `Antragsteller.beschaeftigung.befristungsStatus` | ✅ | Abgeleitet: `=== 'BEFRISTET'`. |

**`finanzielleSituation` ← `Haushalt.positionen` (`HaushaltsPositionen`) + Formel**

| Neues Feld | Quelle / Regel | Status | Hinweise |
|---|---|---|---|
| `eigenKapital` | **berechnet**: `10% × Finanzbedarf.kaufpreis + Kaufnebenkosten` | ✅ | Laut Entscheidung. Kaufnebenkosten = `grunderwerbsteuer + maklergebuehr + notargebuehr`. Wird **nur dem Haupthaushalt** zugewiesen (übrige `null`), um Doppelzählung zu vermeiden. |
| `sonstigeEinnahmen` | Σ `positionen.sonstigeEinnahmen[].einnahmenMonatlich` | ✅ | |
| `gesamtRatenkrediteRestschuld` | Σ `positionen.ratenkredite[].restschuld` | ✅ | Alle Ratenkredite. |
| `verbleibendeRatenkrediteRestschuld` | Σ `ratenkredite[].restschuld`, wobei `wirdAbgeloest !== true` | ✅ | Schließt abzulösende Kredite aus. |
| `verbleibendeRatenkrediteRateMonatlich` | Σ `ratenkredite[].rateMonatlich`, wobei `wirdAbgeloest !== true` | ✅ | |
| `gesamtPrivateDarlehenRestschuld` | Σ `positionen.privateDarlehen[].restschuld` | ✅ | |

### 3.3 `kundenangaben.finanzierungsbedarf` ← `ErfassteDaten.vorhaben` (`Vorhaben`)
| Neues Feld | Quellpfad | Status | Hinweise |
|---|---|---|---|
| `finanzierungszweck` | `Vorhaben.verwendungszweck` | ⚠️ | Enum-gemappt (`VERWENDUNGSZWECK_MAP`); Ziel-Literale verifizieren. |
| `kaufpreis` | `Vorhaben.finanzbedarf.kaufpreis` | ✅ | |
| `grundstueckKaufpreis` | `Vorhaben.finanzbedarf.grundstuecksKaufpreis` | ✅ | |
| `modernisierungsKostenInklEigenleistungen` | `Vorhaben.finanzbedarf.modernisierung` | ✅ | |
| `modernisierungEigenleistung` | `Vorhaben.eigenleistungWennNeubauOderModernisierungsmassnahmen` | ✅ | |
| `praeferenzen` | `Vorhaben.finanzierungswunsch.darlehensWuensche[]` | 🟠 | **Nicht gemappt.** Optional. Benötigt das `DarlehensWunsch`-Modell + eine Regel, welcher Wunsch `rate`/`laufzeit`/Datumswerte bestimmt. Wird `null` gesendet. |

### 3.4 `kundenangaben.finanzierungsobjekt` ← `ErfassteDaten.finanzierungsObjekt` (`FinanzierungsObjekt`)
| Neues Feld | Quellpfad | Status | Hinweise |
|---|---|---|---|
| `objektArt` | `FinanzierungsObjekt.objektArt` | ⚠️ | Enum-gemappt (`OBJEKT_ART_MAP`, z. B. `HAUS → EINFAMILIENHAUS`); **Ziel-Literale verifizieren** — die Vokabulare unterscheiden sich. |
| `wohnflaeche` | `FinanzierungsObjekt.gebaeude.wohnflaeche.gesamtGroesse` | ✅ | `wohnflaeche` ist ein `GebaeudeFlaeche`-Objekt, kein Skalar. |
| `baujahr` | `FinanzierungsObjekt.gebaeude.baujahr` | ✅ | `string` → `int`. |
| `gewerblicheNutzung` | abgeleitet aus `gebaeude.anzahlDerGewerbeeinheiten > 0` oder `gebaeude.gewerbeflaeche != null` | ✅ | Kein direktes Flag in der Quelle. |
| `vermietet` | (`gebaeude.wohnflaeche.vermietungsInformationen`) | 🔵 | **Bewusst zurückgestellt** → `null`. Echte Quelle für später notiert. Beeinflusst nur die LeadRating-Qualität. |
| `anschrift.plz` | `FinanzierungsObjekt.adresse.postleitzahl` | ✅ | Quellfeld heißt `postleitzahl`, nicht `plz`. |
| `anschrift.ort` | `FinanzierungsObjekt.adresse.ort` | ✅ | |
| `anschrift.strasse` | `FinanzierungsObjekt.adresse.strasse` | ✅ | |
| `anschrift.hausnummer` | `FinanzierungsObjekt.adresse.hausnummer` | ✅ | |

> **Tolerant-Reader-Vertrag:** Unbekannte Leaf-Werte werden als explizites `null` gesendet
> (= „kein Wert bekannt"), niemals weggelassen.

---

## 4. Enum-Mapping-Tabellen (im Mapper)

```
VERWENDUNGSZWECK_MAP   (Vorhaben.verwendungszweck → finanzierungszweck)
  KAUF, NEUBAU, KAUF_NEUBAU_VOM_BAUTRAEGER, MODERNISIERUNG_UMBAU_ANBAU,
  ANSCHLUSSFINANZIERUNG, KAPITALBESCHAFFUNG   (Identität — jeweils verifizieren)

OBJEKT_ART_MAP         (FinanzierungsObjekt.objektArt → objektArt)
  HAUS             → EINFAMILIENHAUS     ⚠️ verifizieren
  EIGENTUMSWOHNUNG → EIGENTUMSWOHNUNG
  GRUNDSTUECK      → GRUNDSTUECK         ⚠️ verifizieren, ob reines Grundstück unterstützt wird

BESCHAEFTIGUNGS_ART_MAP (Beschaeftigung.art → beschaeftigungsArt)
  ANGESTELLTER, ARBEITER, BEAMTER, FREIBERUFLER, SELBSTAENDIGER,
  RENTNER, HAUSFRAU ⚠️, ARBEITSLOSER ⚠️   (Identität — die beiden markierten verifizieren)
```

---

## 5. Was noch zu tun ist

### 5.1 Mapper — verifizieren / fertigstellen
- [ ] **Enum-Literale verifizieren** gegen das Vorschläge-YAML (`#/components/schemas/Kundenangaben`):
      `objektArt` (insbesondere `HAUS → ?`), `finanzierungszweck`, `beschaeftigungsArt`.
- [ ] **`datenkontext`** Produktiv-Literal verifizieren (`ECHT_GESCHAEFT` vs. anderes).
- [ ] **`metadaten.extKundenId`**-Quelle bestätigen (`externeVorgangsNummer`?) und ob
      `extClientId` aus `leadTracking` kommen soll.
- [ ] **Kaufnebenkosten-Komponenten** für die `eigenKapital`-Formel bestätigen (aktuell
      Grunderwerbsteuer + Maklergebühr + Notargebühr).
- [ ] *(Optional)* **`praeferenzen`** mappen — benötigt das `DarlehensWunsch`-Modell + eine Regel
      „welcher Wunsch gewinnt".
- [ ] *(Optional)* **`vermietet`** aus `GebaeudeFlaeche.vermietungsInformationen` mappen.

### 5.2 Client / Transport (noch nicht begonnen)
- [ ] **Neue asynchrone Client-Methode** `findeVorschlaege()`:
      `POST /v1/vorschlaege` (Body aus dem Mapper) → `anfrageId` lesen →
      `GET /v1/vorschlaege/{anfrageId}` pollen bis `200` (`202` als erneuten Versuch behandeln;
      Poll-Obergrenze + Backoff ergänzen; `X-TraceId`-Header mitsenden).
- [ ] Requests auf den Host **`baufinanzierung.api.europace.de`** richten.
- [ ] OAuth-Scope **`baufinanzierung:angebote:ermitteln`** zum Token-Request hinzufügen.

### 5.3 Antwort-Verarbeitung (noch nicht begonnen)
- [ ] Nachgelagerte Leser von `ErmittlungResponce` (`ermittlungsId`, `ergebnisse[]`) auf die
      neue Struktur umstellen (`vorschlaege[]`, je mit `finanzierungsVorschlagId`,
      `finanzierungsbausteine[]`, `darlehensSumme`, `sollZins`, `effektivZins`, `rank`,
      `gesamtRateProMonat`; zzgl. `leadRating`).
- [ ] **Anbietername für das Frontend** (z. B. „Sparkasse Vogtland") wird jetzt aus
      `vorschlaege[].finanzierungsbausteine[].produktAnbieter` in der Antwort gelesen — kein
      Eingabe-Filter nötig. Die alte `produktAnbieter`-Query-Param-Logik entfernen.
- [ ] Berücksichtigen, dass `leadRating` in der ersten `200` fehlen kann (ggf. erneut abfragen).

### 5.4 Aufräumen
- [ ] Übrig gebliebenen Debug-Code in `EliV2RestControllerApi::ermittleErgebnisse()` entfernen
      (`var_dump(...); var_dump(...); die();`, ca. Zeilen 137–139) — er bricht die Methode vor
      ihrem `return` ab.
- [ ] Alte v2-Methode / Host (Index 2) außer Betrieb nehmen, sobald nichts mehr darauf zugreift.

### 5.5 Test & Umstellung
- [ ] In `datenkontext = TEST_MODUS` gegen die Testumgebung testen; den Zyklus
      POST → Poll → 200 und das Feld-Mapping mit den Beispiel-Requests der API validieren.
- [ ] Alt vs. neu parallel laufen lassen und vergleichen, bevor Produktiv-Traffic umgestellt wird.
- [ ] Umstellung vor der Abschaltung **Ende November 2026** abschließen.

---

## 6. Referenzen

- Quell-Datenmodell (alt): `ErfassteDaten` → `Haushalt` (`antragsteller`/`positionen`),
  `Antragsteller` → `Beschaeftigung`, `HaushaltsPositionen`, `Vorhaben`
  (`finanzbedarf`/`finanzierungswunsch`), `FinanzierungsObjekt`
  (`gebaeude`/`adresse`).
- Vorschläge OpenAPI-YAML:
  `https://github.com/europace/baufi-passende-vorschlaege-api/blob/main/api/baufi-passende-vorschlaege-api.yaml`
- Swagger UI:
  `https://europace.github.io/baufi-passende-vorschlaege-api/docs/swaggerui.html`
- Beispiel-Requests:
  `https://github.com/europace/baufi-passende-vorschlaege-api/tree/main/docs/requests`
- Mapper-Implementierung: [`VorschlaegeRequestMapper.php`](./VorschlaegeRequestMapper.php)
