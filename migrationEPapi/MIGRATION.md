# Migration: Angebote v2 `ermittlung` → Vorschläge API

Migrating the sunset call **`POST /v2/ergebnisliste/ermittlung`** (with an `ErfassteDaten`
body and **no** `vorgangsNummer`) to the **Vorschläge API**.

- **Deadline:** the v2 endpoint is shut down **end of November 2026**.
- **Why Vorschläge (not Angebote v3):** the migration guide states that
  `POST /v2/ergebnisliste/ermittlung` with an `ErfassteDaten` body and no `vorgangsNummer`
  has **no equivalent in Angebote API v3** (v3 always requires `{vorgangsnummer}` in the
  path). For calculations without an existing Vorgang, the documented replacement is the
  **Vorschläge API**.
- **Scope decisions for this migration:**
  - Calculate & display only — **no API bookmarking** (`gemerkteAngebote` / saved offers).
  - Therefore only the OAuth scope **`baufinanzierung:angebote:ermitteln`** is required
    (not `baufinanzierung:vorgaenge:schreiben`), and no `vorgangsnummer` is persisted.

---

## 1. Endpoint-level change

| Aspect | Old (v2 ermittlung) | New (Vorschläge API) |
|---|---|---|
| Host | Angebote v2 host (`Configuration::getHost(2)`) | `baufinanzierung.api.europace.de` |
| Call shape | **1 synchronous** POST | **2-step async**: POST then poll GET |
| Endpoint(s) | `POST /v2/ergebnisliste/ermittlung` | `POST /v1/vorschlaege` → `GET /v1/vorschlaege/{anfrageId}` |
| Request body | `ErfassteDaten` | `{ metadaten, kundenangaben }` |
| Calc options | query params: `alternativen`, `produktAnbieter`, `excludierteProduktAnbieter`, `provisionsAusgabe` | `metadaten.gewuenschteAnzahlVorschlaege` + (optional) `finanzierungsbedarf.praeferenzen` |
| Success response | `ErmittlungResponce` (`ermittlungsId` + `ergebnisse[]`) | POST → `{ anfrageId }`; poll → `202` (retry) or `200` `{ vorschlaege[], leadRating }` |
| Result IDs | `ermittlungsId` / `ergebnisNummer` | `anfrageId` / `finanzierungsVorschlagId` |
| OAuth scope | (existing) | **`baufinanzierung:angebote:ermitteln`** |
| Provider name for UI | result field | `vorschlaege[].finanzierungsbausteine[].produktAnbieter` (in the `200` response) |

**Async flow:**
```
POST /v1/vorschlaege            → 200 { "anfrageId": "passende-vorschlaege-..." }
GET  /v1/vorschlaege/{anfrageId} → 202  (determination in progress → retry)
                                 → 200  { "vorschlaege": [...], "leadRating": {...} }
```

---

## 2. Steps completed

1. **Reviewed** the migration guide, the Vorschläge API doc, and the existing PHP client
   (`EliV2RestControllerApi.php`).
2. **Confirmed the target**: Vorschläge API (no Angebote v3 equivalent for the no-Vorgang case).
3. **Reduced scope**: no bookmarking → single scope, no Vorgang persistence.
4. **Inspected the source data model** (`ErfassteDaten` and all nested leaf models) to build an
   exact field mapping.
5. **Built the request-body mapper**: [`VorschlaegeRequestMapper.php`](./VorschlaegeRequestMapper.php)
   — maps `ErfassteDaten` → `{ metadaten, kundenangaben }` as a plain array for `json_encode()`.

Usage:
```php
$body = (new VorschlaegeRequestMapper())->map($erfassteDaten, 3); // 3 = gewuenschteAnzahlVorschlaege
$json = json_encode($body); // POST body for /v1/vorschlaege
```

---

## 3. Field mapping (old `ErfassteDaten` → new `kundenangaben`)

Legend: ✅ implemented & verified against the model · ⚠️ implemented, value needs verification ·
🔵 deferred by decision · 🟠 not yet mapped (needs more input)

### 3.1 `metadaten`
| New field | Source (old) | Status | Notes |
|---|---|---|---|
| `datenkontext` | `ErfassteDaten.datenKontext` | ⚠️ | Source enum `TEST_MODUS` / `ECHT_GESCHAEFT`; verify productive literal in Vorschläge YAML. |
| `extKundenId` | `ErfassteDaten.externeVorgangsNummer` | ⚠️ | Confirm this is the intended source. |
| `extClientId` | — | 🟠 | Currently `null`; wire from `getLeadTracking()` if a client id is tracked. |
| `gewuenschteAnzahlVorschlaege` | method param | ✅ | Replaces the old `alternativen` query param. |

### 3.2 `kundenangaben.haushalte[]` ← `ErfassteDaten.haushalte[]` (`Haushalt[]`)

**`kunden[]` ← `Haushalt.antragsteller[]` (`Antragsteller[]`)**

| New field | Source path | Status | Notes |
|---|---|---|---|
| `geburtsdatum` | `Antragsteller.geburtsdatum` | ✅ | `DateTime` → `Y-m-d`. |
| `einkommenNetto` | `Antragsteller.beschaeftigung.einkommenNettoMonatlich` | ✅ | Monthly net — exactly what Vorschläge expects (net income is on `Beschaeftigung`, **not** on `Antragsteller`). |
| `beschaeftigungsArt` | `Antragsteller.beschaeftigung.art` | ⚠️ | Enum-mapped (`BESCHAEFTIGUNGS_ART_MAP`); verify `HAUSFRAU`/`ARBEITSLOSER` accepted. |
| `beschaeftigtSeit` | `Antragsteller.beschaeftigung.beschaeftigtSeit` | ✅ | `DateTime` → `Y-m-d`. |
| `arbeitBefristet` | `Antragsteller.beschaeftigung.befristungsStatus` | ✅ | Derived: `=== 'BEFRISTET'`. |

**`finanzielleSituation` ← `Haushalt.positionen` (`HaushaltsPositionen`) + formula**

| New field | Source / rule | Status | Notes |
|---|---|---|---|
| `eigenKapital` | **computed**: `10% × Finanzbedarf.kaufpreis + Kaufnebenkosten` | ✅ | Per decision. Kaufnebenkosten = `grunderwerbsteuer + maklergebuehr + notargebuehr`. Assigned to the **primary household only** (others `null`) to avoid double-counting. |
| `sonstigeEinnahmen` | Σ `positionen.sonstigeEinnahmen[].einnahmenMonatlich` | ✅ | |
| `gesamtRatenkrediteRestschuld` | Σ `positionen.ratenkredite[].restschuld` | ✅ | All credits. |
| `verbleibendeRatenkrediteRestschuld` | Σ `ratenkredite[].restschuld` where `wirdAbgeloest !== true` | ✅ | Excludes credits being paid off. |
| `verbleibendeRatenkrediteRateMonatlich` | Σ `ratenkredite[].rateMonatlich` where `wirdAbgeloest !== true` | ✅ | |
| `gesamtPrivateDarlehenRestschuld` | Σ `positionen.privateDarlehen[].restschuld` | ✅ | |

### 3.3 `kundenangaben.finanzierungsbedarf` ← `ErfassteDaten.vorhaben` (`Vorhaben`)
| New field | Source path | Status | Notes |
|---|---|---|---|
| `finanzierungszweck` | `Vorhaben.verwendungszweck` | ⚠️ | Enum-mapped (`VERWENDUNGSZWECK_MAP`); verify target literals. |
| `kaufpreis` | `Vorhaben.finanzbedarf.kaufpreis` | ✅ | |
| `grundstueckKaufpreis` | `Vorhaben.finanzbedarf.grundstuecksKaufpreis` | ✅ | |
| `modernisierungsKostenInklEigenleistungen` | `Vorhaben.finanzbedarf.modernisierung` | ✅ | |
| `modernisierungEigenleistung` | `Vorhaben.eigenleistungWennNeubauOderModernisierungsmassnahmen` | ✅ | |
| `praeferenzen` | `Vorhaben.finanzierungswunsch.darlehensWuensche[]` | 🟠 | **Not mapped.** Optional. Needs `DarlehensWunsch` model + a rule for which wish drives `rate`/`laufzeit`/dates. Sent `null`. |

### 3.4 `kundenangaben.finanzierungsobjekt` ← `ErfassteDaten.finanzierungsObjekt` (`FinanzierungsObjekt`)
| New field | Source path | Status | Notes |
|---|---|---|---|
| `objektArt` | `FinanzierungsObjekt.objektArt` | ⚠️ | Enum-mapped (`OBJEKT_ART_MAP`, e.g. `HAUS → EINFAMILIENHAUS`); **verify target literals** — vocabularies differ. |
| `wohnflaeche` | `FinanzierungsObjekt.gebaeude.wohnflaeche.gesamtGroesse` | ✅ | `wohnflaeche` is a `GebaeudeFlaeche` object, not a scalar. |
| `baujahr` | `FinanzierungsObjekt.gebaeude.baujahr` | ✅ | `string` → `int`. |
| `gewerblicheNutzung` | derived from `gebaeude.anzahlDerGewerbeeinheiten > 0` or `gebaeude.gewerbeflaeche != null` | ✅ | No direct flag in the source. |
| `vermietet` | (`gebaeude.wohnflaeche.vermietungsInformationen`) | 🔵 | **Deferred by decision** → `null`. Real source noted for later. Only affects LeadRating quality. |
| `anschrift.plz` | `FinanzierungsObjekt.adresse.postleitzahl` | ✅ | Source field is `postleitzahl`, not `plz`. |
| `anschrift.ort` | `FinanzierungsObjekt.adresse.ort` | ✅ | |
| `anschrift.strasse` | `FinanzierungsObjekt.adresse.strasse` | ✅ | |
| `anschrift.hausnummer` | `FinanzierungsObjekt.adresse.hausnummer` | ✅ | |

> **Tolerant Reader contract:** unknown leaf values are sent as explicit `null` (= "no data
> known"), never omitted.

---

## 4. Enum mapping tables (in the mapper)

```
VERWENDUNGSZWECK_MAP   (Vorhaben.verwendungszweck → finanzierungszweck)
  KAUF, NEUBAU, KAUF_NEUBAU_VOM_BAUTRAEGER, MODERNISIERUNG_UMBAU_ANBAU,
  ANSCHLUSSFINANZIERUNG, KAPITALBESCHAFFUNG   (identity — verify each accepted)

OBJEKT_ART_MAP         (FinanzierungsObjekt.objektArt → objektArt)
  HAUS             → EINFAMILIENHAUS     ⚠️ verify
  EIGENTUMSWOHNUNG → EIGENTUMSWOHNUNG
  GRUNDSTUECK      → GRUNDSTUECK         ⚠️ verify a bare plot is supported

BESCHAEFTIGUNGS_ART_MAP (Beschaeftigung.art → beschaeftigungsArt)
  ANGESTELLTER, ARBEITER, BEAMTER, FREIBERUFLER, SELBSTAENDIGER,
  RENTNER, HAUSFRAU ⚠️, ARBEITSLOSER ⚠️   (identity — verify the flagged two)
```

---

## 5. What's left to do

### 5.1 Mapper — verify / finish
- [ ] **Verify enum literals** against the Vorschläge YAML (`#/components/schemas/Kundenangaben`):
      `objektArt` (esp. `HAUS → ?`), `finanzierungszweck`, `beschaeftigungsArt`.
- [ ] **Verify `datenkontext`** productive literal (`ECHT_GESCHAEFT` vs. other).
- [ ] **Confirm `metadaten.extKundenId`** source (`externeVorgangsNummer`?) and whether
      `extClientId` should come from `leadTracking`.
- [ ] **Confirm Kaufnebenkosten** components for the `eigenKapital` formula (currently
      Grunderwerbsteuer + Maklergebühr + Notargebühr).
- [ ] *(Optional)* Map **`praeferenzen`** — needs `DarlehensWunsch` model + a "which wish wins" rule.
- [ ] *(Optional)* Map **`vermietet`** from `GebaeudeFlaeche.vermietungsInformationen`.

### 5.2 Client / transport (not started)
- [ ] **New async client method** `findeVorschlaege()`:
      `POST /v1/vorschlaege` (body from the mapper) → read `anfrageId` →
      poll `GET /v1/vorschlaege/{anfrageId}` until `200` (treat `202` as retry; add a poll
      cap + backoff; keep an `X-TraceId` header).
- [ ] Point requests at host **`baufinanzierung.api.europace.de`**.
- [ ] Add OAuth scope **`baufinanzierung:angebote:ermitteln`** to the token request.

### 5.3 Response consumers (not started)
- [ ] Remap downstream readers from `ErmittlungResponce` (`ermittlungsId`, `ergebnisse[]`)
      to the new shape (`vorschlaege[]`, each with `finanzierungsVorschlagId`,
      `finanzierungsbausteine[]`, `darlehensSumme`, `sollZins`, `effektivZins`, `rank`,
      `gesamtRateProMonat`; plus `leadRating`).
- [ ] **Provider name for the frontend** (e.g. "Sparkasse Vogtland") now reads from
      `vorschlaege[].finanzierungsbausteine[].produktAnbieter` in the response — no input
      filter needed. Drop the old `produktAnbieter` query-param plumbing.
- [ ] Handle `leadRating` possibly being absent in the first `200` (re-query if needed).

### 5.4 Cleanup
- [ ] Remove the leftover debug code in `EliV2RestControllerApi::ermittleErgebnisse()`
      (`var_dump(...); var_dump(...); die();`, around lines 137–139) — it short-circuits the
      method before its `return`.
- [ ] Retire the old v2 method / host (index 2) once nothing calls it.

### 5.5 Testing & cutover
- [ ] Test in `datenkontext = TEST_MODUS` against the test environment; validate the
      POST → poll → 200 cycle and the field mapping with the API's example requests.
- [ ] Run old vs. new side by side and compare before switching production traffic.
- [ ] Cut over before the **end-of-November-2026** shutdown.

---

## 6. Reference

- Source data model (old): `ErfassteDaten` → `Haushalt` (`antragsteller`/`positionen`),
  `Antragsteller` → `Beschaeftigung`, `HaushaltsPositionen`, `Vorhaben`
  (`finanzbedarf`/`finanzierungswunsch`), `FinanzierungsObjekt`
  (`gebaeude`/`adresse`).
- Vorschläge OpenAPI YAML:
  `https://github.com/europace/baufi-passende-vorschlaege-api/blob/main/api/baufi-passende-vorschlaege-api.yaml`
- Swagger UI:
  `https://europace.github.io/baufi-passende-vorschlaege-api/docs/swaggerui.html`
- Example requests:
  `https://github.com/europace/baufi-passende-vorschlaege-api/tree/main/docs/requests`
- Mapper implementation: [`VorschlaegeRequestMapper.php`](./VorschlaegeRequestMapper.php)
