# RI24 Admin Backend – Migrationsspezifikation

**Projekt:** Regionalimmobilien24 CMS Admin Backend  
**Theme:** Inspinia Bootstrap Admin (Bootstrap 3 / jQuery)  
**Stand:** Oktober 2026  

---

## 1. Überblick

Das bestehende RI24-Backend wird auf das **Inspinia Bootstrap Admin Theme** migriert. Ziel ist eine moderne, konsistente Benutzeroberfläche mit einheitlichem Navigations- und Designsystem. Im Zuge der Migration werden redundante Menüpunkte entfernt, inhaltlich verwandte Bereiche konsolidiert und die Navigationsstruktur vereinfacht.

---

## 2. Navigationsstruktur: Alt vs. Neu

### 2.1 Alte Struktur (Auszug)

```
Dashboard
  ├─ Makler
  ├─ Baufinanzierung
  ├─ Nutzer
  ├─ reCaptcha          ← entfernt (in Nutzer integriert)
  ├─ Sitzungen          ← entfernt (in Nutzer integriert)
  ├─ Mails              ← entfernt (in Nutzer integriert)
  ├─ OID Recherche      ← verschoben → Objekte
  └─ Dubletten Check    ← verschoben → Objekte

Makler
  ├─ Übersicht Makler   ┐
  ├─ Kurzliste Makler   ┘ zusammengeführt
  ├─ Anfragen
  ├─ neuen Makler anlegen
  ├─ Kooperationen      ← verschoben → eigener Hauptmenüpunkt
  └─ Makler umhängen    ← entfernt

Kundenlogin             ← umbenannt → "Nutzer"

Objekte
  └─ alle Objekte

Privatanzeigen

Baufi/Immo-Orte         ← entfernt
statische Seiten        ← entfernt

alle Regionen
  ├─ alle Regionen
  ├─ Parameter individualisieren  ← Untermenü entfernt
  ├─ Geodaten anpassen            ← Untermenü entfernt
  ├─ Mailings anpassen            ← Untermenü entfernt
  ├─ Immo Werbebanner & PopUp     ← Untermenü entfernt
  └─ Seiten individualisieren     ← Untermenü entfernt

Kontaktanfragen
  ├─ alle Kontaktanfragen
  ├─ E-Mail Liste
  └─ Blacklist

Team
Whitelabel-Lizenzen
Suchaufträge            ← entfernt
Schnittstellen
SEO                     ← entfernt
Immobilienassistent     ← entfernt
Hilfe                   ← entfernt
```

### 2.2 Neue Struktur

```
Dashboard
  ├─ Makler
  ├─ Baufinanzierung
  └─ Nutzer

Makler
  ├─ Übersicht Makler  (zusammengeführt)
  ├─ Anfragen
  └─ neuen Makler anlegen

Kooperationen           (neuer Hauptmenüpunkt)
  ├─ Übersicht
  └─ neue Kooperation

Nutzer                  (ehemals "Kundenlogin")

Objekte
  ├─ alle Objekte
  └─ OID / Dubletten Check  (zusammengeführt)

Privatanzeigen

alle Regionen           (direkter Link, kein Untermenü)

Kontaktanfragen
  ├─ alle Kontaktanfragen
  ├─ E-Mail Liste
  └─ Blacklist

Team
Whitelabel-Lizenzen

Schnittstellen
  ├─ Sitemaps (Mitula)
  └─ Statischer Immobilien Export
```

---

## 3. Entfernte Menüpunkte

| Menüpunkt               | Grund                                                                 |
|-------------------------|-----------------------------------------------------------------------|
| **reCaptcha**           | Inhalte in Dashboard → Nutzer integriert                              |
| **Sitzungen**           | Alle 3 Panels in Dashboard → Nutzer integriert                        |
| **Mails**               | Suchauftrag-Mails und Follow-Up-Mails in Dashboard → Nutzer integriert |
| **Baufi/Immo-Orte**     | Nicht mehr benötigt                                                   |
| **statische Seiten**    | Nicht mehr benötigt                                                   |
| **Suchaufträge**        | Nicht mehr benötigt                                                   |
| **SEO**                 | Nicht mehr benötigt                                                   |
| **Immobilienassistent** | Nicht mehr benötigt                                                   |
| **Hilfe**               | Nicht mehr benötigt                                                   |
| **Makler umhängen**     | Nicht mehr benötigt                                                   |
| **Alle-Regionen-Untermenüs** | Direktlink auf Übersicht reicht; Unterpunkte nur über Zeilenaktionen erreichbar |

---

## 4. Konsolidierungen und Umbenennungen

| Alt                                          | Neu                                     | Art der Änderung     |
|----------------------------------------------|-----------------------------------------|----------------------|
| Übersicht Makler + Kurzliste Makler          | Übersicht Makler                        | Zusammengeführt      |
| OID Recherche + Dubletten Check (Dashboard)  | Objekte › OID / Dubletten Check         | Zusammengeführt + verschoben |
| reCaptcha, Sitzungen, Mails (Dashboard)      | Dashboard › Nutzer (zusätzliche Panels) | Integriert           |
| Kundenlogin                                  | Nutzer                                  | Umbenannt            |
| Kooperationen (unter Makler)                 | Kooperationen (eigener Hauptmenüpunkt)  | Verschoben + erweitert |

---

## 5. Menüpunkte im Detail

### 5.1 Dashboard → Makler

**Pfad (alt):** `/adm/individuell/master/dashboard/`  
**Inhalt:** Statistische Übersicht der Makler-Kennzahlen mit Zeitreihen-Diagrammen.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` (Panel)  | Jeder Kennzahlenbereich in eigenem Panel |
| Flot.js Liniendiagramm | Zeitreihen (Anzahl Makler, Kontaktanfragen, Anfragen nach Quelle) |
| Flot.js Kreisdiagramm | Verteilung nach Kategorien |
| `form-control input-sm` | Region- und Quellenfilter-Dropdowns |
| `input-group` + Datepicker | Von-/Bis-Datumsfilter |
| `label` (farbig) | Kennzahl-Badges (z. B. Organisch, Google Ads) |

---

### 5.2 Dashboard → Baufinanzierung

**Pfad (alt):** `/adm/individuell/master/dashboard/baufi/`  
**Inhalt:** Statistiken zu Baufinanzierungsanfragen.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Jeder Panel-Bereich |
| Flot.js Multi-Series Liniendiagramm | Mehrteilige Zeitreihen nach Quelle |
| Flot.js Kreisdiagramm | Anteilsverteilung |
| `form-control input-sm` | Filterleisten |
| `input-group` + Datepicker | Zeitraumfilter |

---

### 5.3 Dashboard → Nutzer

**Pfad (alt):** `/adm/individuell/master/dashboard/user/`  
**Inhalt:** Konsolidierter Dashboard mit Nutzerkonten, Logins, Suchaufträgen, Sitzungen, Telefon-Klicks, Referrern und reCaptcha-Fehlern. Die früheren eigenständigen Bereiche **Mails**, **Sitzungen** und **reCaptcha** wurden als zusätzliche Panels integriert.

**Panels (gesamt 9):**
1. Anzahl Nutzerkonten
2. Anzahl eingeloggter / aktiver Nutzer am Tag
3. Anzahl aktiver Suchaufträge
4. Anzahl Suchauftrag Mails *(ehemals: Dashboard → Mails)*
5. Anzahl Kaufobjekt Follow-Up Mails *(ehemals: Dashboard → Mails)*
6. Sitzungen (gruppiert) *(ehemals: Dashboard → Sitzungen)*
7. Klick auf Telefonnummern *(ehemals: Dashboard → Sitzungen)*
8. Referrer (komplett) *(ehemals: Dashboard → Sitzungen)*
9. fehlergeschlagene reCaptcha *(ehemals: Dashboard → reCaptcha)*

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Jeder der 9 Panels |
| Flot.js Liniendiagramm | Zeitreihen für Panels 1–5, 9 |
| Flot.js Kreisdiagramm | reCaptcha-Fehlerverteilung (Panel 9) |
| Flot.js Multi-Series | Sitzungen, Referrer (Panels 6–8) |
| `label` (farbig, inline) | Zählbadges (Organisch, Google Ads, Referral, Facebook) |
| `form-control input-sm` | Regioncode-, Quell- und Aktionsfilter |
| `input-group` + Datepicker | Von-/Bis-Datumsfilter |

---

### 5.4 Makler → Übersicht Makler

**Pfad (alt):** `/adm/individuell/master/makler/list/` + `/list-short/`  
**Änderung:** „Übersicht Makler" und „Kurzliste Makler" wurden zu einer einzigen Tabelle zusammengeführt (ca. 9 überlappende Spalten; 250 von 2.636 Zeilen dargestellt).

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables (`datatables.min.js` + Bootstrap-4-Adapter) | Sortierung, Paginierung, Suche; deutsche Sprachkonfiguration |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `btn btn-default btn-xs` | Zeilen-Aktionsschaltflächen (Bearbeiten, Sitzungen, etc.) |
| `badge` | Farbliche Statusmarkierungen |
| CDN-Thumbnails (50×50) | Firmenlogos hotlinked vom RI24-CDN |

---

### 5.5 Makler → Anfragen

**Pfad (alt):** `/adm/individuell/master/makler/anfragen/`  
**Änderung:** Die verschachtelte 3-zeilige `<thead>`-Struktur (rowspan/colspan) wurde auf eine flache Kopfzeile vereinfacht; Spaltenbezeichnungen beibehalten.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `btn btn-default btn-xs` | Bearbeiten-Schaltfläche je Zeile |

---

### 5.6 Makler → neuen Makler anlegen / bearbeiten

**Pfad (alt):** `/adm/individuell/master/makler/new/` / `/edit/`

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Formularcontainer |
| `form-horizontal` | Zweispaltiges Label-/Feldlayout |
| `form-group` + `col-sm-3` / `col-sm-9` | Feldraster |
| `form-control` | Texteingaben |
| `btn btn-primary` / `btn btn-default` | Speichern / Abbrechen |
| `text-danger` | Pflichtfeldmarkierung (`*`) |

---

### 5.7 Kooperationen → Übersicht

**Pfad (alt):** `/adm/individuell/master/makler/kooperation/`  
**Änderung:** Aus dem Makler-Untermenü als eigenständiger Hauptmenüpunkt herausgelöst; eigenes Untermenü (Übersicht / neue Kooperation). Bearbeiten-Funktion neu hinzugefügt.  
**Daten:** 24 reale Partnereinträge.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer mit Zähler-Badge im Titel |
| DataTables | Sortierung und Paginierung; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `badge` | Gesamtanzahl-Anzeige im Panel-Titel |
| `img` (CDN-Hotlink) | 50×50 Logos vom `bilder.regionalimmobilien24.de`-CDN |
| `btn btn-default btn-xs` | Aktionsschaltflächen: Bearbeiten (Bleistift), Sortierung, Löschen |
| `btn btn-success btn-sm` | „Neue Kooperation"-Button |

---

### 5.8 Kooperationen → neue Kooperation / bearbeiten

**Pfad (alt):** `/adm/.../makler/kooperation/new/` / `/edit/?id=…`  
**Neu:** Bearbeiten-Funktion erstmals als Prototyp umgesetzt.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Formularcontainer (Stammdaten) |
| `ibox` | Logo-Bereich (separates Panel) |
| `form-horizontal` | Label-/Feldlayout |
| `form-group` | Feldraster |
| `form-control` | Text-, URL- und Textarea-Felder |
| `select form-control` | CRM-Auswahl (nein / ja) |
| `input[type=file]` | Neues Logo hochladen |
| `img` (CDN, 120×60) | Vorschau des aktuellen Logos |
| `btn btn-primary` / `btn btn-default` | Speichern / Abbrechen |
| `btn btn-danger btn-sm` | Logo löschen |

---

### 5.9 Nutzer (ehemals: Kundenlogin)

**Pfad (alt):** `/adm/individuell/master/tools/kundenlogin/`  
**Änderung:** Menübezeichnung von „Kundenlogin" auf „Nutzer" geändert; Inhalt unverändert. 5.142 Zeilen (250 dargestellt).

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `btn btn-default btn-xs` | Zeilen-Aktionen (Bearbeiten, Umhängen, Löschen) |
| Tooltip (`title`-Attribut) | Feldinfos in der Kopfzeile |

---

### 5.10 Objekte → alle Objekte

**Pfad (alt):** `/adm/individuell/master/immo/list/`  
**Inhalt:** 100 Objekte (Live-Seite paginiert in 100er-Blöcken über den gesamten OID-Raum).

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche |
| `table-striped table-bordered table-hover` | Tabellenstil |
| CDN-Thumbnails (50×50) | Objektbilder hotlinked |
| `badge` | Statusmarkierungen |
| `btn btn-default btn-xs` | Zeilen-Aktionen |

---

### 5.11 Objekte → OID / Dubletten Check

**Pfad (alt):** `/adm/individuell/master/tools/oid-recherche/` + `/tools/immo-dubletten-check/`  
**Änderung:** Zwei ehemals separate Dashboard-Untermenüpunkte (OID Immo-Recherche und Immo Dubletten-Check) wurden zu einem einzigen Screen unter Objekte zusammengeführt.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` (2×) | Eines je Tool, nebeneinander (`col-lg-6`) |
| `form-horizontal` | Eingabeformulare |
| `form-control` | Lookup-Felder |
| `btn btn-primary` | Suche / Prüfung ausführen |

---

### 5.12 Privatanzeigen

**Pfad (alt):** `/adm/individuell/master/privatanzeige/`  
**Inhalt:** 443 Zeilen (250 dargestellt).

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `btn btn-default btn-xs` | Zeilen-Aktionen |

---

### 5.13 alle Regionen

**Pfad (alt):** `/adm/individuell/regionen/config/`  
**Änderung:** Das Untermenü (ehemals 6 Unterpunkte: alle Regionen, Parameter individualisieren, Geodaten anpassen, Mailings anpassen, Immo Werbebanner & PopUp anpassen, Seiten individualisieren) wurde vollständig entfernt. Der Menüpunkt ist jetzt ein direkter Link auf die Übersichtstabelle. Unterpunkte bleiben über die Zeilenaktionsschaltflächen in der Tabelle erreichbar. 105 Zeilen (104 Regionen + Vorlagezeile).

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `btn btn-default btn-xs` | Zeilen-Aktionen (W / P / G / M / S – je Unterbereich) |
| `badge` | Region-Status (aktiv/inaktiv) |

---

### 5.14 alle Regionen → Seiten individualisieren

**Pfad (alt):** `/adm/individuell/regionen/edit_region_sites.php?regio=aai24`  
**Neu:** Zusätzliche **Städte-Tabelle** mit 24 Städten der Beispielregion Aachen-Eifel sowie pro Stadt aufklappbare Untermenüs mit drei Seiten-Tabellen.

**Tabellen auf der Seite:**
1. Hauptnavigation (23 Einträge)
2. Servicenavigation (3 Einträge)
3. Seiten ohne Zuordnung (10 Einträge)
4. **Städte** (24 Einträge) – *neu*
   - Klick auf Bleistift → Bootstrap-Collapse mit 3 Unter-Tabellen:
     - **Kaufobjekte** (15 Seitentypen)
     - **Mietobjekte** (14 Seitentypen)
     - **Baufinanzierung** (1 Eintrag)

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` (4× äußere + 3× je Stadt) | Panels für jede Tabellengruppe |
| DataTables | Hauptnavigation, Servicenavigation, Seiten ohne Zuordnung |
| `table-striped table-bordered table-hover` | Alle Tabellen einheitlich |
| Bootstrap Collapse (`data-toggle="collapse"`) | Aufklappbare Städte-Untermenüs |
| `btn btn-default btn-xs` | Bleistift (Zeile bearbeiten / Collapse umschalten) + externer Link |
| `col-lg-4` × 3 | Dreispaltiges Layout der Unter-Tabellen im Collapse |

---

### 5.15 alle Regionen → Seite bearbeiten

**Pfad (alt):** `/adm/individuell/regionen/edit_region_page.php?regio=aai24&page_id=…`  
**Erreichbar über:** Bleistift-Button in Hauptnavigation / Servicenavigation / Seiten ohne Zuordnung / Städte-Untermenüs.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` (mehrere) | Getrennte Panels für Stammdaten, SEO-Konfiguration, Sektionen |
| `form-horizontal` | Formularstruktur |
| Bootstrap Tabs (`nav-tabs`) | Trennung SEO-Einstellungen (z. B. Titel, Beschreibung, OG-Tags) |
| `form-control` | Texteingaben, Textareas |
| `input[type=file]` | Bild-Upload |
| TinyMCE-Platzhalter | Richtext-Editor (auf Live-Seite aktiv) |
| `btn btn-primary` / `btn btn-default` | Speichern / Abbrechen je Panel |

---

### 5.16 Kontaktanfragen → alle Kontaktanfragen

**Pfad (alt):** `/adm/individuell/master/statistik/kontaktanfragen/`

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `btn btn-default btn-xs` | Zeilen-Aktionen |

---

### 5.17 Kontaktanfragen → E-Mail Liste

**Pfad (alt):** `/adm/individuell/master/mails/list/`  
**Neu:** Zusätzliche Filter (Region, Monat) und CSV-Export-Schaltflächen. Zwei getrennte Tabellen für Kauf- und Mietinteressenten.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` (2×) | Kaufinteressenten / Mietinteressenten je Panel |
| DataTables | Beide Tabellen; deutsche Lokalisierung |
| `form-control input-sm` | Region- und Monats-Dropdown-Filter |
| `btn btn-default btn-sm` | CSV-Export-Schaltflächen |
| `table-striped table-bordered table-hover` | Tabellenstil |

---

### 5.18 Kontaktanfragen → Blacklist

**Pfad (alt):** `/adm/individuell/master/mails/blacklist/`  
**Hinweis:** Bewusst **keine** DataTables — die Live-Seite verwendet eine einfache sortierbare Tabelle mit eigenen A-Z/Z-A-Schaltflächen.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| `table table-bordered table-hover` | Tabellenstil (kein DataTables, kein Striping) |
| `btn btn-default btn-sm` | A-Z / Z-A Sortierung, CSV-Export |
| `btn btn-danger btn-xs` | Eintrag entfernen (rotes „−") |
| `badge` | Gesamtanzahl der gesperrten Adressen |
| Inline-Formularzeile (`<tr>`) | Neuen Eintrag direkt in der Tabelle hinzufügen |

---

### 5.19 Team

**Pfad (alt):** `/adm/individuell/master/team/list/`  
**Inhalt:** 124 Team-Mitglieder.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| CDN-Fotos (50×50) | Profilbilder hotlinked vom RI24-CDN |
| `btn btn-default btn-xs` | Zeilen-Aktionen (Bearbeiten) |

---

### 5.20 Team → Mitglied bearbeiten

**Pfad (alt):** `/adm/individuell/master/team/edit/?id=…`  
**Layout:** Zweispaltig (`col-md-6`) mit mehreren `ibox`-Panels, jedes mit eigenem Speichern-Button (analog Live-Site mit separaten AJAX-Speicherungen).

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` (mehrere) | Persönliche Daten, Unternehmensdaten, EUROPACE, Partner-Status, Partner-Links, MobiBox, SMS |
| `form-horizontal` | Label-/Feldlayout |
| `form-control` | Texteingaben |
| `input[type=file]` | Foto, QR-Code, Logo (separate Upload-Formulare) |
| `btn btn-primary` | Speichern je Panel |
| `btn btn-default` | Abbrechen |

---

### 5.21 Team → Partner-Status bearbeiten

**Pfad (alt):** Unterebene von Team-Edit  
**Inhalt:** Partner-Status-Schicht mit eigenem Formular.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Formularcontainer |
| `form-horizontal` | Feldlayout |
| `form-control` | Eingabefelder |
| `btn btn-primary` / `btn btn-default` | Speichern / Abbrechen |

---

### 5.22 Whitelabel-Lizenzen

**Pfad (alt):** `/adm/individuell/master/whitelabel/list/`  
**Inhalt:** 44 Lizenzen; filterbar nach Portal und Mandant.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `form-control input-sm` | Portal- und Mandant-Filter |
| CDN-Bilder (50×50) | Partner-Logos hotlinked |
| `btn btn-default btn-xs` | Bearbeiten |

---

### 5.23 Whitelabel-Lizenzen → bearbeiten

**Pfad (alt):** `/adm/individuell/master/whitelabel/edit/?id=…`  
**Hinweis:** Passwörter aus dem Live-System wurden durch Platzhalter ersetzt.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Formularcontainer |
| `form-horizontal` | Dreispaltiges Feldlayout |
| `form-control` | Eingabefelder; Passwortfeld mit maskiertem Wert |
| `btn btn-primary` / `btn btn-default` | Speichern / Abbrechen |

---

### 5.24 Schnittstellen → Sitemaps (Mitula)

**Pfad (alt):** `/adm/individuell/master/interface/mitula/`  
**Inhalt:** 103 Regionen mit Sitemap-Konfiguration.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` | Tabellencontainer |
| DataTables | Sortierung, Paginierung, Suche; deutsche Lokalisierung |
| `table-striped table-bordered table-hover` | Tabellenstil |
| `btn btn-default btn-xs` | Zeilen-Aktionen |

---

### 5.25 Schnittstellen → Statischer Immobilien Export

**Pfad (alt):** `/adm/individuell/master/interface/immo/static/`  
**Inhalt:** 28 API-Konten. Klartextpasswörter aus dem Live-System wurden durch Platzhalter-Punkte ersetzt.

| Inspinia-Element | Verwendung |
|-----------------|------------|
| `ibox` (2×) | Tabellen- und Endpunkte-Container |
| `table table-striped table-bordered` | Tabellenstil (kein DataTables) |
| `btn btn-danger btn-xs` | Konto löschen |
| Inline-Formularzeile | Neues Konto anlegen (Bezeichnung-Feld am Tabellenende) |
| `ibox` (Export-Endpunkte) | Direktlinks auf JSON / XML / OpenImmo-XML Feeds |

---

## 6. Globale Inspinia-Komponenten

| Komponente | Einsatz im gesamten Backend |
|-----------|----------------------------|
| **MetisMenu** (`jquery.metisMenu.js`) | Sidebar-Navigation mit Akkordeon-Verhalten |
| **SlimScroll** (`jquery.slimscroll.min.js`) | Scrollbarer Sidebar-Bereich |
| **Pace.js** | Seitenladefortschrittsanzeige |
| **ibox** | Universeller Panel-Container mit Collapse- und Close-Option |
| `prototype-banner` | Hinweisleiste oben (nur Prototypen; entfällt in Produktion) |
| `page-heading` + `breadcrumb` | Einheitliche Seitenüberschrift mit Breadcrumb-Navigation |
| Bootstrap 3 Grid (`col-lg-*`) | Responsive Spaltenlayout auf allen Seiten |
| Font Awesome 4 (`fa fa-*`) | Alle Icons (Menü, Schaltflächen, Aktionen) |
| `btn btn-primary/default/danger/success` | Einheitliche Schaltflächenstile |
| `form-horizontal` + `form-group` | Standardlayout für alle Formulare |

---

## 7. Technische Umsetzung der Prototypen

- **Buildpipeline:** Python 3 (`build.py` je Prototype) generiert statische `index.html`
- **Gemeinsame Komponenten:** `_common.py` stellt `sidebar()`, `page_shell()`, `ibox()`, `page_heading()`, `prototype_banner()` und `DATATABLES_DE_JS` bereit
- **Echtdaten:** Alle Prototypen verwenden echte, aus dem Live-Backend gescrapte Daten (via Playwright); Klartextpasswörter wurden durch Platzhalter ersetzt
- **`complete/`-Ordner:** Vollständig verlinkte Prototypen-Suite (32 Seiten) mit funktionierender Sidebar-Navigation, Untermenüs und Vorwärts-/Rückwärtsnavigation; Einstiegspunkt: `complete/index.html`
- **Daten-Cap:** Tabellen mit mehr als 250 Zeilen werden auf 250 Zeilen begrenzt (ausreichend für die Layoutprüfung)
- **Sicherheit:** CDN-Thumbnails (öffentlich zugängliche kleine Crops) werden direkt eingebunden; Klartext-Passwörter und Sitzungstoken werden nie in statische Dateien übernommen
