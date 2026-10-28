/**
 * Calendly Proxy Service
 * 
 * Playwright-basierter Proxy für Calendly-Terminbuchungen.
 * Da die Berater nur kostenlose Calendly-Accounts haben, nutzt dieser Service
 * einen Headless-Browser, um die Calendly-Oberfläche programmatisch zu bedienen.
 *
 * Endpunkte:
 *   GET  /ressource/get/calendly/availability.json  → Verfügbare Termine abrufen
 *   POST /ressource/set/calendly/booking.json       → Termin buchen
 */

const express = require('express');
const { getAvailability } = require('./lib/availability');
const { createBooking } = require('./lib/booking');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3100;

// ─── Health-Check ────────────────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'calendly-proxy' });
});

// ─── Verfügbare Termine abrufen ──────────────────────────────────────────────
app.get('/ressource/get/calendly/availability.json', async (req, res) => {
  const { url, date } = req.query;

  if (!url) {
    return res.status(400).json({
      status: false,
      error: 'Parameter "url" (Calendly-URL des Beraters) ist erforderlich.'
    });
  }

  try {
    const result = await getAvailability(url, date || null);
    res.json({ status: true, data: result });
  } catch (err) {
    console.error('[availability] Fehler:', err.message);
    res.status(500).json({
      status: false,
      error: `Verfügbarkeit konnte nicht abgerufen werden: ${err.message}`
    });
  }
});

// ─── Termin buchen ───────────────────────────────────────────────────────────
app.post('/ressource/set/calendly/booking.json', async (req, res) => {
  const { calendly_url, date, time, location, first_name, last_name, email, phone } = req.body;

  // Pflichtfelder prüfen
  const missing = [];
  if (!calendly_url) missing.push('calendly_url');
  if (!date) missing.push('date');
  if (!time) missing.push('time');
  if (!location) missing.push('location');
  if (!first_name) missing.push('first_name');
  if (!last_name) missing.push('last_name');
  if (!email) missing.push('email');

  if (missing.length > 0) {
    return res.status(400).json({
      status: false,
      error: `Fehlende Pflichtfelder: ${missing.join(', ')}`
    });
  }

  // Location validieren
  const validLocations = ['outbound_call', 'physical', 'google_conference'];
  if (!validLocations.includes(location)) {
    return res.status(400).json({
      status: false,
      error: `Ungültiger Ort. Erlaubt: ${validLocations.join(', ')}`
    });
  }

  try {
    const result = await createBooking({
      calendly_url,
      date,
      time,
      location,
      first_name,
      last_name,
      email,
      phone: phone || ''
    });
    res.json({ status: true, data: result });
  } catch (err) {
    console.error('[booking] Fehler:', err.message);
    res.status(500).json({
      status: false,
      error: `Buchung fehlgeschlagen: ${err.message}`
    });
  }
});

// ─── Server starten ──────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`✅ Calendly-Proxy läuft auf Port ${PORT}`);
});
