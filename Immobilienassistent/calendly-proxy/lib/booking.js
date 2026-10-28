/**
 * Calendly Booking Service
 *
 * Führt eine vollständige Terminbuchung auf der Calendly-Seite durch:
 * 1. Tag auswählen
 * 2. Zeitslot auswählen
 * 3. "Bestätigen"-Button klicken (nach Zeitauswahl erscheint ein Confirm-Button)
 * 4. Ort auswählen (Anruf / vor Ort / Google Meet)
 * 5. Kontaktdaten eingeben (Vorname, Nachname, E-Mail, Telefon)
 * 6. "Termin buchen" absenden
 *
 * Calendly-UI-Elemente (Stand Mai 2026):
 * - Zeitslot-Button: <button data-container="time-button" data-start-time="09:00">
 * - Bestätigen nach Zeitwahl: <button data-container="confirm-button"> oder ähnlich
 * - Ort-Auswahl: <input name="location" type="radio" value="outbound_call|physical|google_conference">
 * - Vorname: <input name="first_name" autocomplete="given-name">
 * - Nachname: <input name="last_name" autocomplete="family-name">
 * - E-Mail: <input id="email_input" name="email">
 * - Telefon: <input name="question_0" type="tel">
 * - Absenden: <button type="submit"> mit Text "Termin buchen"
 */

const { chromium } = require('playwright');

/** Maximale Wartezeit für Seitenelemente (ms) */
const TIMEOUT = 15000;

/**
 * Bucht einen Termin auf der Calendly-Seite eines Beraters.
 *
 * @param {Object} params
 * @param {string} params.calendly_url – Calendly-Buchungsseite
 * @param {string} params.date – Gewünschtes Datum (YYYY-MM-DD)
 * @param {string} params.time – Gewünschte Uhrzeit (HH:MM, z.B. "09:30")
 * @param {string} params.location – Terminort: "outbound_call" | "physical" | "google_conference"
 * @param {string} params.first_name – Vorname des Nutzers
 * @param {string} params.last_name – Nachname des Nutzers
 * @param {string} params.email – E-Mail-Adresse des Nutzers
 * @param {string} [params.phone] – Telefonnummer des Nutzers (optional, aber empfohlen)
 * @returns {Object} – { success, message, booked_date, booked_time, booked_location }
 */
async function createBooking(params) {
  const {
    calendly_url, date, time, location,
    first_name, last_name, email, phone
  } = params;

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    locale: 'de-DE',
    timezoneId: 'Europe/Berlin',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
  });

  const page = await context.newPage();

  try {
    // ── Schritt 1: Seite laden ───────────────────────────────────────────
    console.log(`[booking] Öffne ${calendly_url}`);
    await page.goto(calendly_url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // ── Schritt 2: Zum richtigen Monat navigieren ────────────────────────
    await navigateToTargetMonth(page, date);

    // ── Schritt 3: Tag auswählen ─────────────────────────────────────────
    const dayOfMonth = new Date(date).getDate();
    console.log(`[booking] Wähle Tag ${dayOfMonth}`);

    const dayClicked = await clickAvailableDay(page, dayOfMonth);
    if (!dayClicked) {
      throw new Error(`Der ${date} ist nicht verfügbar. Bitte einen anderen Tag wählen.`);
    }

    await page.waitForTimeout(1500);

    // ── Schritt 4: Zeitslot auswählen ────────────────────────────────────
    console.log(`[booking] Wähle Zeitslot ${time}`);
    const timeClicked = await clickTimeSlot(page, time);
    if (!timeClicked) {
      throw new Error(`Die Uhrzeit ${time} ist nicht verfügbar am ${date}. Bitte eine andere Uhrzeit wählen.`);
    }

    await page.waitForTimeout(1000);

    // ── Schritt 5: Confirm-Button klicken (falls vorhanden) ──────────────
    console.log('[booking] Bestätige Zeitauswahl');
    await clickConfirmButton(page);
    await page.waitForTimeout(2000);

    // ── Schritt 6: Ort auswählen ─────────────────────────────────────────
    console.log(`[booking] Wähle Ort: ${location}`);
    await selectLocation(page, location);
    await page.waitForTimeout(500);

    // ── Schritt 7: Kontaktdaten eingeben ─────────────────────────────────
    console.log('[booking] Fülle Kontaktdaten aus');
    await fillContactForm(page, { first_name, last_name, email, phone });
    await page.waitForTimeout(500);

    // ── Schritt 8: Termin buchen (Submit) ────────────────────────────────
    console.log('[booking] Sende Buchung ab');
    await submitBooking(page);

    // ── Schritt 9: Auf Bestätigung warten ────────────────────────────────
    console.log('[booking] Warte auf Bestätigung');
    const confirmation = await waitForConfirmation(page);

    return {
      success: true,
      message: confirmation || 'Termin wurde erfolgreich gebucht!',
      booked_date: date,
      booked_time: time,
      booked_location: locationLabel(location)
    };

  } catch (err) {
    // Screenshot für Debugging speichern (optional)
    try {
      await page.screenshot({ path: '/tmp/calendly-booking-error.png', fullPage: true });
      console.error('[booking] Fehler-Screenshot gespeichert unter /tmp/calendly-booking-error.png');
    } catch { /* ignore screenshot error */ }

    throw err;

  } finally {
    await browser.close();
  }
}

/**
 * Navigiert zum Monat des Zieldatums.
 */
async function navigateToTargetMonth(page, targetDate) {
  const target = new Date(targetDate);
  const targetMonth = target.getMonth();
  const targetYear = target.getFullYear();

  for (let i = 0; i < 12; i++) {
    const titleEl = page.locator('[aria-live="polite"], [data-component="calendar-title"], h2').first();
    const titleText = await titleEl.textContent().catch(() => '');

    const currentInfo = parseMonthFromTitle(titleText);
    if (currentInfo.month === targetMonth && currentInfo.year === targetYear) {
      return; // Richtiger Monat erreicht
    }

    const currentDate = new Date(currentInfo.year, currentInfo.month, 1);
    const targetMonthDate = new Date(targetYear, targetMonth, 1);

    if (targetMonthDate > currentDate) {
      const nextBtn = page.locator('button[aria-label*="Nächster"], button[aria-label*="Next"]').first();
      await nextBtn.click().catch(() => {});
    } else {
      const prevBtn = page.locator('button[aria-label*="Vormonat"], button[aria-label*="Previous"], button[aria-label*="Vorheriger"]').first();
      await prevBtn.click().catch(() => {});
    }
    await page.waitForTimeout(1000);
  }
}

/**
 * Parst Monat und Jahr aus dem Kalender-Header-Text.
 */
function parseMonthFromTitle(title) {
  const months = {
    'januar': 0, 'february': 1, 'februar': 1, 'march': 2, 'märz': 2,
    'april': 3, 'mai': 4, 'may': 4, 'juni': 5, 'june': 5,
    'juli': 6, 'july': 6, 'august': 7, 'september': 8,
    'oktober': 9, 'october': 9, 'november': 10, 'dezember': 11, 'december': 11,
    'january': 0
  };

  const lower = (title || '').toLowerCase();
  for (const [name, idx] of Object.entries(months)) {
    if (lower.includes(name)) {
      const yearMatch = title.match(/(\d{4})/);
      return { month: idx, year: yearMatch ? parseInt(yearMatch[1]) : new Date().getFullYear() };
    }
  }
  return { month: new Date().getMonth(), year: new Date().getFullYear() };
}

/**
 * Klickt auf einen verfügbaren Tag.
 */
async function clickAvailableDay(page, dayOfMonth) {
  const dayStr = String(dayOfMonth);

  // Primäre Strategie: Button mit aria-label "verfügbar" und dem richtigen Tag
  const availableButton = page.locator(
    `button[aria-label*="verfügbar"]:has(span:text-is("${dayStr}")), ` +
    `button[aria-label*="available"]:has(span:text-is("${dayStr}"))`
  ).first();

  try {
    if (await availableButton.isVisible({ timeout: 3000 })) {
      await availableButton.click();
      return true;
    }
  } catch { /* nicht gefunden */ }

  // Fallback: Versuche Buttons mit der bookable-Klasse
  const bookableButton = page.locator(
    `button[class*="bookable"]:has(span:text-is("${dayStr}"))`
  ).first();

  try {
    if (await bookableButton.isVisible({ timeout: 2000 })) {
      await bookableButton.click();
      return true;
    }
  } catch { /* nicht gefunden */ }

  return false;
}

/**
 * Klickt auf einen Zeitslot.
 */
async function clickTimeSlot(page, time) {
  // Normalisiere Zeit-Format (z.B. "9:00" → "09:00")
  const normalizedTime = time.padStart(5, '0');

  // Primäre Strategie: data-start-time Attribut
  const timeButton = page.locator(
    `button[data-start-time="${normalizedTime}"]`
  ).first();

  try {
    if (await timeButton.isVisible({ timeout: 5000 })) {
      await timeButton.click();
      return true;
    }
  } catch { /* nicht gefunden */ }

  // Fallback: Button mit dem Zeittext
  const textButton = page.locator(
    `[data-container="time-button"]:has-text("${normalizedTime}")`
  ).first();

  try {
    if (await textButton.isVisible({ timeout: 3000 })) {
      await textButton.click();
      return true;
    }
  } catch { /* nicht gefunden */ }

  return false;
}

/**
 * Klickt auf den "Bestätigen/Confirm"-Button nach der Zeitauswahl.
 * In Calendly erscheint nach der Zeitauswahl oft ein weiterer Bestätigungs-Button.
 */
async function clickConfirmButton(page) {
  const confirmSelectors = [
    'button[data-container="confirm-button"]',
    'button:has-text("Bestätigen")',
    'button:has-text("Confirm")',
    'button:has-text("Next")',
    'button:has-text("Weiter")'
  ];

  for (const sel of confirmSelectors) {
    const btn = page.locator(sel).first();
    try {
      if (await btn.isVisible({ timeout: 2000 })) {
        await btn.click();
        return;
      }
    } catch { /* nicht gefunden */ }
  }

  // Manchmal geht Calendly direkt zum Formular, kein Confirm nötig
  console.log('[booking] Kein Bestätigungs-Button gefunden, fahre fort...');
}

/**
 * Wählt den Terminort per Radio-Button aus.
 */
async function selectLocation(page, locationValue) {
  // Warten bis die Ortsauswahl sichtbar ist
  const locationRadio = page.locator(`input[name="location"][value="${locationValue}"]`).first();

  try {
    await locationRadio.waitFor({ state: 'attached', timeout: 5000 });

    // Playwright kann versteckte Radio-Buttons nicht direkt klicken,
    // daher klicken wir auf das zugehörige Label
    const label = page.locator(
      `[data-component="location-choice"]:has(input[value="${locationValue}"]) label`
    ).first();

    if (await label.isVisible({ timeout: 3000 })) {
      await label.click();
      return;
    }

    // Fallback: Radio-Button direkt per JavaScript setzen
    await page.evaluate((val) => {
      const radio = document.querySelector(`input[name="location"][value="${val}"]`);
      if (radio) {
        radio.checked = true;
        radio.dispatchEvent(new Event('change', { bubbles: true }));
        radio.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }, locationValue);

  } catch (err) {
    console.warn(`[booking] Ortsauswahl "${locationValue}" nicht gefunden:`, err.message);
    // Manche Event-Types haben keine Ortswahl – dann weitermachen
  }
}

/**
 * Füllt das Kontaktformular aus.
 */
async function fillContactForm(page, { first_name, last_name, email, phone }) {
  // ── Vorname ────────────────────────────────────────────────────────────
  const firstNameInput = page.locator('input[name="first_name"]').first();
  await firstNameInput.waitFor({ state: 'visible', timeout: TIMEOUT });
  await firstNameInput.fill(first_name);

  // ── Nachname ───────────────────────────────────────────────────────────
  const lastNameInput = page.locator('input[name="last_name"]').first();
  await lastNameInput.fill(last_name);

  // ── E-Mail ─────────────────────────────────────────────────────────────
  const emailInput = page.locator('input[name="email"], input#email_input').first();
  await emailInput.fill(email);

  // ── Telefon (falls vorhanden) ──────────────────────────────────────────
  if (phone) {
    // Calendly hat oft ein intl-tel-input für Telefonnummern
    const phoneInput = page.locator(
      'input[type="tel"], input[name="question_0"], input[autocomplete="tel"]'
    ).first();

    try {
      if (await phoneInput.isVisible({ timeout: 3000 })) {
        await phoneInput.fill(phone);
      }
    } catch {
      console.warn('[booking] Telefon-Eingabefeld nicht gefunden');
    }
  }
}

/**
 * Klickt den "Termin buchen" / "Schedule Event" Submit-Button.
 */
async function submitBooking(page) {
  const submitSelectors = [
    'button[type="submit"]',
    'button:has-text("Termin buchen")',
    'button:has-text("Schedule Event")',
    'button:has-text("Confirm")'
  ];

  for (const sel of submitSelectors) {
    const btn = page.locator(sel).first();
    try {
      if (await btn.isVisible({ timeout: 3000 })) {
        await btn.click();
        return;
      }
    } catch { /* nicht gefunden */ }
  }

  throw new Error('Submit-Button ("Termin buchen") nicht gefunden.');
}

/**
 * Wartet auf die Buchungsbestätigung.
 */
async function waitForConfirmation(page) {
  // Calendly zeigt nach erfolgreicher Buchung eine Bestätigungsseite
  const confirmSelectors = [
    'h1:has-text("Bestätigt")',
    'h1:has-text("Confirmed")',
    'h1:has-text("You are scheduled")',
    '[data-component="confirmation"]',
    'text=Bestätigt',
    'text=Confirmed',
    'text=erfolgreich'
  ];

  for (const sel of confirmSelectors) {
    try {
      await page.waitForSelector(sel, { timeout: 15000 });
      const text = await page.locator(sel).first().textContent().catch(() => '');
      return text || 'Termin erfolgreich gebucht!';
    } catch { /* nächsten Selektor probieren */ }
  }

  // Prüfe ob die URL auf eine Bestätigungsseite weist
  const currentUrl = page.url();
  if (currentUrl.includes('invitee') || currentUrl.includes('confirmed') || currentUrl.includes('scheduled')) {
    return 'Termin erfolgreich gebucht!';
  }

  // Letzte Chance: Prüfe den Seiteninhalt
  const bodyText = await page.textContent('body').catch(() => '');
  if (bodyText.includes('bestätigt') || bodyText.includes('confirmed') || bodyText.includes('scheduled')) {
    return 'Termin erfolgreich gebucht!';
  }

  throw new Error(
    'Buchungsbestätigung konnte nicht verifiziert werden. ' +
    'Bitte prüfe den Termin direkt in Calendly oder im E-Mail-Postfach.'
  );
}

/**
 * Gibt einen lesbaren Label-Text für den Terminort zurück.
 */
function locationLabel(location) {
  const labels = {
    'outbound_call': 'Telefonisch (Anruf)',
    'physical': 'Vor Ort beim Berater',
    'google_conference': 'Online (Google Meet)'
  };
  return labels[location] || location;
}

module.exports = { createBooking };
