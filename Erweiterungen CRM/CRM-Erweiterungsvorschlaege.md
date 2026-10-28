# CRM-Erweiterungsvorschläge — Partnerbereich Baufinanzierung
**Regionalimmobilien24 GmbH** · Stand: Oktober 2026

---

## Überblick

Auf Basis einer vollständigen Analyse des Partner-CRM (`/be-admin/`) wurden die folgenden 13 Erweiterungsvorschläge erarbeitet. Die Analyse umfasste alle Hauptbereiche: Kundenverwaltung, Europace-Integration, Profil, Landingpages, Empfehlungsseite, Unterlagen sowie die bestehenden API- und Datenbankfelder.

Die Vorschläge sind nach Umsetzungsaufwand und strategischem Hebel priorisiert. Die drei stärksten Quick-Wins sind **#2, #1 und #3**.

---

## 1. Bankenwissen direkt in der Kundenverwaltung

**Bereich:** Kundenverwaltung · **Aufwand:** Mittel · **Hebel:** Sehr hoch

### Ist-Zustand
Der Bankenwissen-Bot (132 Kriterien × 487 Banken, Qualitypool-Datenbasis, Stand 2026-05-07) existiert als separater Typebot. Berater müssen bei der Kundenberatung zwischen CRM und Typebot wechseln, um Bankanforderungen nachzuschlagen.

### Vorschlag
Ein Bankenwissen-Abfrage-Panel direkt in der Kundendetailansicht einbetten. Das Panel wird automatisch mit den Kreditparametern des Kunden vorbelegt (Darlehenssumme, Vorhaben, Beleihungsauslauf) und fragt die bestehende Vektordatenbank ab.

### Nutzen
- Kein Kontextwechsel mehr während der Beratung
- Berater sieht Bankanforderungen und Kundendaten parallel
- Basis: bestehende `/bankenwissen/combined/*.json` Datenbasis + OpenAI file_search

---

## 2. Automatischer Lead-Import aus dem Finanzierungscheck-Chatbot

**Bereich:** Kundenverwaltung · **Aufwand:** Gering–Mittel · **Hebel:** Sehr hoch

### Ist-Zustand
Der Finanzierungscheck-Chatbot (MCP → Pitcom → Europace) erstellt Europace-Vorgänge, schreibt aber nichts in die Kundenverwaltung des CRM. Berater müssen Leads manuell doppelt erfassen.

### Vorschlag
Webhook-Bridge: Wenn der Chatbot einen Fall bei Pitcom/Europace speichert, wird gleichzeitig ein POST an den CRM-Backend gesendet, der einen neuen Eintrag im Status „Leadeingang" erzeugt — vollständig vorausgefüllt mit Name, Darlehenssumme, Vorhaben, Telefon, E-Mail und EP-Vorgangsnummer.

### Nutzen
- Eliminiert doppelte Dateneingabe vollständig
- Kein Lead fällt mehr durchs Raster
- Umsetzbar mit bestehendem MCP-Stack (saveKundenangaben-Endpoint)

---

## 3. Kanban-Board statt Tabellen-Pipeline

**Bereich:** Kundenverwaltung · **Aufwand:** Mittel · **Hebel:** Hoch

### Ist-Zustand
Die Pipeline-Stufen (Leadeingang: 2, Angebot: 1, Aufbereitung: 1, Fall bei Bank: 0, Abschluss: 0) werden als kleine Stat-Karten über einer flachen Tabelle angezeigt. Die Gesamtübersicht fehlt.

### Vorschlag
Drag-and-Drop Kanban-Board als zweite Ansicht (Toggle: Tabelle / Kanban). Jede Spalte entspricht einer Pipeline-Stufe. Kunden-Karten zeigen: Name, Darlehenssumme, letztes Aktivitätsdatum und einen farbigen Indikator für überfällige Aufgaben. Verschieben einer Karte aktualisiert die Phase via AJAX.

### Nutzen
- Berater sieht auf einen Blick, wo jeder Kunde steht
- Priorisierung wird intuitiv
- Stellt dar, wo Deals hängen bleiben

---

## 4. Automatisierte Follow-up-Erinnerungen

**Bereich:** Kundenverwaltung · **Aufwand:** Mittel · **Hebel:** Hoch

### Ist-Zustand
Aufgaben existieren als manuell erstellte Tabelle (Fällig / Erledigt / Aufgabe / Kunde). Es gibt keine Automatisierungsregeln.

### Vorschlag
Regelbasierte Aufgaben-Automatisierung:
- „Wenn ein Lead >3 Tage in ‚Leadeingang' ohne Aktivität → Aufgabe ‚Anrufen' erstellen"
- „Wenn ein Angebot >7 Tage ohne Rückmeldung → Erinnerung per E-Mail"
- „Wenn ein Termin gebucht wurde (Calendly-Webhook) → Aufgabe ‚Termin vorbereiten' erstellen"

Browser- und E-Mail-Push-Benachrichtigungen für überfällige Aufgaben.

### Nutzen
- Kein Lead fällt mehr durch das Raster
- Berater braucht kein eigenes Erinnerungssystem
- Kombiniert sich direkt mit Feature #13 (Kalender-Integration)

---

## 5. Dashboard-Upgrade: Conversion-Funnel und Lead-Source-Tracking

**Bereich:** Dashboard · **Aufwand:** Mittel–Hoch · **Hebel:** Hoch

### Ist-Zustand
Das Dashboard zeigt monatliche Rohdaten seit 2023 sowie vier KPIs (Exposé-Anzeigen, Logo-Anzeigen, Landingpage-Aufrufe, Anfragen), die für den Test-Account alle auf 0 stehen. Es gibt keine Trichtervisualisierung und keine Lead-Quellen-Zuordnung.

### Vorschlag
- **Conversion-Funnel:** Visualisierung der Abfallraten zwischen den Pipeline-Stufen (z. B. Leadeingang→Angebot: 65 %) inkl. durchschnittlicher Verweildauer je Stufe
- **Lead-Source-Tracking:** Herkunftslabels pro Kunde (Chatbot / IS24 / Manuell / Empfehlung / Calendly)
- **Umsatz-Trend:** Darlehenssummen über Zeit mit 12-Monats-Linie und Vorjahresvergleich
- **Rolling-Window-Ansicht:** 7-Tage / 30-Tage / Quartal als Filteroption

### Nutzen
- Berater erkennt seinen eigenen Bottleneck
- Basis für Coaching-Gespräche mit Partnerbetreuer
- Macht den Wert des Partnerbereichs messbar

---

## 6. KI-Profiltext-Generator für „Meine Texte"

**Bereich:** Meine Texte / Landingpages · **Aufwand:** Gering · **Hebel:** Mittel–Hoch

### Ist-Zustand
Der Bereich „Meine Texte" enthält bearbeitbare Felder für Zitat, Kurzbeschreibung, Ausführliche Beschreibung, Leistungen und Orte — alle manuell befüllt. In der Praxis lassen viele Berater diese Felder leer, was Landingpage-SEO und Conversion verschlechtert.

### Vorschlag
„Mit KI generieren"-Button je Textfeld. Die KI (Claude) erhält Name, Region (Orte-Feld), Europace-Partnernummer und Spezialisierung und generiert alle Texte im richtigen Umfang und Ton. Der Berater kann vor dem Speichern editieren.

### Nutzen
- Befüllungsrate der Profilfelder steigt deutlich
- Bessere Landingpage-Rankings ohne Mehraufwand für Berater
- Minimaler Backend-Aufwand (API-Call auf bestehende OpenAI/Claude-Infrastruktur)

---

## 7. Onboarding-Wizard für externe Plattformen

**Bereich:** Administration (Europace-Config) · **Aufwand:** Gering · **Hebel:** Mittel

### Ist-Zustand
Die Administrations-Seite zeigt 7 externe Plattformen (Abakus24, Baufinex, Fondsfinanz, Forum extern, Qualitypool extern, Starpool, Forum) alle mit Status „nicht hinterlegt / Freischalten". Es gibt keine Anleitung, wie die Verbindung hergestellt wird.

### Vorschlag
Schrittweiser Einrichtungs-Wizard pro Plattform:
1. Welche Zugangsdaten werden benötigt (und wo findet man sie)?
2. Eingabeformular mit Live-Verbindungstest
3. Berechtigungsübersicht nach erfolgreicher Verbindung
4. Status-Ampel auf der Übersichtsseite

### Nutzen
- Aktivierungsrate der Drittplattformen steigt
- Weniger Support-Anfragen bei Partnerbetreuer
- Direkter Umsatzhebel (mehr Abschlusskanäle = mehr Provisionen)

---

## 8. Empfehlungsseite: Tracking und ROI-Dashboard

**Bereich:** Empfehlungsseite · **Aufwand:** Mittel · **Hebel:** Mittel

### Ist-Zustand
Die Empfehlungsseite erlaubt das Hochladen und Versenden eines Empfehlungsvideos sowie die optionale Hinterlegung einer Empfehlungsvergütung. Eine Tabelle zeigt Status / Zeit / Video — aber keine Konversionsrate.

### Vorschlag
- Tracking: Wie viele Empfänger haben den Link geöffnet? Wie viele haben das Formular ausgefüllt? Wie viele wurden ein Kunde?
- Optionale Provisionsabrechnung: Automatische Berechnung der Empfehlungsvergütung je konvertiertem Lead
- Mini-Dashboard auf der Seite: Gesendete Empfehlungen / Öffnungsrate / Abschlussrate

### Nutzen
- Empfehlungskanal wird erstmals messbar
- Berater erkennt, ob sich die Empfehlungsvergütung lohnt
- Anreiz, mehr Empfehlungen aktiv zu versenden

---

## 9. Dokumenten-Management pro Kunde

**Bereich:** Kundenverwaltung · **Aufwand:** Mittel–Hoch · **Hebel:** Mittel–Hoch

### Ist-Zustand
Das Unterlagen-Center ist eine generelle Ablage (Logos, Unterlagen, Videos) für alle Berater. Es gibt keine Möglichkeit, Dokumente einem einzelnen Kunden zuzuordnen.

### Vorschlag
Dokumenten-Reiter in der Kundendetailansicht mit Kategorien:
- Einkommensnachweis
- SCHUFA-Auskunft
- Objektunterlagen
- Angebote / Konditionenvergleiche
- Sonstiges

Jedes Dokument bekommt einen Status (ausstehend / eingereicht / geprüft) und ein Upload-Datum. Optional: Benachrichtigung an den Berater, wenn ein Dokument noch fehlt.

### Nutzen
- Vollständige Kundenakte an einem Ort
- Weniger E-Mail-Ping-Pong mit Kunden
- Basis für spätere Europace-Dokument-Upload-Integration (API-Rechte `unterlagen:dokument:schreiben` bereits vorhanden)

---

## 10. IS24-Lead-Integration

**Bereich:** Kundenverwaltung · **Aufwand:** Mittel · **Hebel:** Mittel

### Ist-Zustand
ImmoScout24-Leads liegen als separate Datenquelle vor, fließen aber nicht automatisch in die Kundenverwaltung ein.

### Vorschlag
IS24-Leads mit Finanzierungsinteresse (erkennbar an Nachrichteninhalt oder IS24-Finanzierungsanfrage-Flag) werden automatisch als „Leadeingang" in der Kundenverwaltung angelegt — mit Lead-Quelle „IS24" getaggt und dem zuständigen Berater zugewiesen.

### Nutzen
- Neuer Leadkanal ohne manuelle Übertragung
- Vollständige Übersicht aller Leads in einem System
- IS24-Leads bekommen denselben Follow-up-Automatismus wie Chatbot-Leads

---

## 11. WhatsApp-Follow-up aus der Kundenverwaltung

**Bereich:** Kundenverwaltung · **Aufwand:** Gering · **Hebel:** Mittel

### Ist-Zustand
Kundenzeilen in der Tabelle zeigen Telefon und E-Mail, bieten aber keine direkten Messaging-Aktionen.

### Vorschlag
WhatsApp-Icon-Button auf jeder Kundenzeile. Klick öffnet `wa.me/{Telefon}?text=...` mit vorausgefüllter Nachricht (Vorname des Kunden + individuelle Berater-Signatur). Alternativ: Einfache Twilio-API-Integration für programmatischen Versand mit Bestätigung im CRM.

### Nutzen
- 5-Schritte-Prozess auf 1 Klick reduziert
- Höhere Follow-up-Quote
- Ergänzt Feature #13 (Calendly-Link per WhatsApp senden)

---

## 12. Qualitypool-Zertifikats-Tracker

**Bereich:** Dashboard / Weiterbildung · **Aufwand:** Gering–Mittel · **Hebel:** Mittel

### Ist-Zustand
„Weiterbildung" verlinkt auf Qpedia/Makler-Wiki. Es gibt keinen Überblick über den Status laufender oder auslaufender Zertifizierungen.

### Vorschlag
Zertifikats-Dashboard mit:
- Liste aller Pflicht-Zertifizierungen (Qualitypool, IHK § 34i)
- Ablaufdatum und Countdown
- Direktlink zur Verlängerung
- Automatische Erinnerung 60 / 30 / 7 Tage vor Ablauf

Die Qualitypool-API-Verbindung ist bereits vollständig eingerichtet (`baufinanzierung:ereignis:lesen` berechtigt) — Abruf der Zertifikatsdaten sollte ohne neue Authentifizierung möglich sein.

### Nutzen
- Keine abgelaufenen Zertifikate mehr
- Berater bleibt konform ohne eigenes Tracking
- Niedrigschwellig: Qualitypool-API bereits verbunden

---

## 13. Eingebaute Kalender-Funktion mit Calendly-Integration

**Bereich:** Kundenverwaltung / Profil · **Aufwand:** Gering (A+B) bis Mittel (C) · **Hebel:** Hoch

### Ist-Zustand
- Das Datenmodell enthält bereits die Felder `calendly` und `calendly_zusatz` für jeden Berater — beide sind aktuell `null` und im Profil-Formular nicht sichtbar
- Calendly wird auf dem Dashboard bereits für den „Individuelle Finanzierungsunterstützung"-Termin von Philipp Steppohn verwendet
- Kunden erhalten Terminlinks nur, wenn Berater manuell kopieren und per WhatsApp/E-Mail senden

### Vorschlag — drei aufbauende Ausbaustufen

**A. Profil: Calendly-URL hinterlegen (Kleinstaufwand)**
Das bestehende `calendly`-Datenbankfeld im Profil-Formular sichtbar machen und speicherbar machen. Das Feld `calendly_zusatz` kann für eine persönliche Einladungsnotiz genutzt werden (z. B. „Bitte wählen Sie einen 30-Minuten-Termin für unser Erstgespräch").
- Reine Frontend-Änderung, kein neues Backend erforderlich

**B. Kundenverwaltung: „Termin senden"-Button (Geringer Aufwand)**
Kalender-Icon-Button auf jeder Kunden-Karte / -Zeile. Klick öffnet ein Modal mit drei Versandoptionen:
- **WhatsApp:** `wa.me/{Telefon}?text=Hallo+{Vorname}%2C+...+{calendly_url}` — öffnet vorausgefüllte Nachricht in WhatsApp Web
- **E-Mail:** `mailto:{Email}?subject=Terminvorschlag+Baufinanzierung&body=...` mit eingebettetem Calendly-Link
- **Link kopieren:** Kopiert den personalisierten Booking-Link in die Zwischenablage

Die Nachricht ist vorausgefüllt (Kundenvorname wird automatisch eingesetzt) und vor dem Versand editierbar. Vollständig client-seitig umsetzbar — kein Backend erforderlich.

**C. Terminübersicht und Pipeline-Automatisierung (Mittlerer Aufwand)**
Calendly bietet kostenlose Webhooks (`invitee.created`, `invitee.canceled`). Wenn ein Kunde über den Berater-Link bucht:
- CRM empfängt den Webhook und findet den passenden Kundeneintrag (E-Mail-Abgleich)
- Pipeline-Stufe wird automatisch aktualisiert (z. B. Leadeingang → Angebot)
- Aufgabe „Termin vorbereiten: {Datum, Uhrzeit}" wird automatisch angelegt
- Bevorstehende Termine erscheinen als Widget auf dem Dashboard

**Fallback für Berater ohne Calendly:**
Der „Termin per E-Mail anfragen"-Button sendet eine einfache Terminanfrage-Mail. Als plattformweiter Fallback kann der bestehende RI24-Calendly-Link (Philipp Steppohn) angezeigt werden.

### Nutzen
- Terminvereinbarung von 5 manuellen Schritten auf 1 Klick reduziert
- Höhere Terminquote = mehr Abschlüsse
- Stufe A+B in einem Sprint umsetzbar, da Datenbankfeld bereits vorhanden
- Stufe C schließt den Kreislauf: Termin gebucht → CRM reagiert automatisch

---

## Prioritätsmatrix

| # | Feature | Aufwand | Hebel | Empfehlung |
|---|---------|---------|-------|------------|
| 2 | Chatbot → CRM Lead-Bridge | Gering–Mittel | Sehr hoch | **Sprint 1** |
| 13 | Calendly-Integration (A+B) | Gering | Hoch | **Sprint 1** |
| 1 | Bankenwissen in Kundenprofil | Mittel | Sehr hoch | **Sprint 1** |
| 3 | Kanban-Board | Mittel | Hoch | Sprint 2 |
| 4 | Follow-up-Automatisierung | Mittel | Hoch | Sprint 2 |
| 11 | WhatsApp-Button | Gering | Mittel | Sprint 2 |
| 6 | KI-Profiltext-Generator | Gering | Mittel–Hoch | Sprint 2 |
| 7 | Onboarding-Wizard Plattformen | Gering | Mittel | Sprint 2 |
| 5 | Dashboard Funnel-Analytics | Mittel–Hoch | Hoch | Sprint 3 |
| 9 | Dokumente pro Kunde | Mittel–Hoch | Mittel–Hoch | Sprint 3 |
| 8 | Empfehlungsseite Tracking | Mittel | Mittel | Sprint 3 |
| 10 | IS24-Lead-Integration | Mittel | Mittel | Sprint 3 |
| 12 | Zertifikats-Tracker | Gering–Mittel | Mittel | Sprint 3 |
| 13C | Calendly Webhook/Dashboard | Mittel | Hoch | Sprint 3 |

---

*Erstellt auf Basis einer automatisierten CRM-Analyse · Regionalimmobilien24 GmbH · Oktober 2026*
