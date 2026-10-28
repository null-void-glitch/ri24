/**
 * Calendly Availability Scraper
 *
 * Öffnet die Calendly-Seite eines Beraters im Headless-Browser und extrahiert:
 * 1. Verfügbare Tage des angezeigten Monats
 * 2. Verfügbare Zeitslots für einen bestimmten Tag (falls Datum angegeben)
 *
 * Calendly-UI-Elemente (Stand Mai 2026):
 * - Verfügbare Tage: <button aria-label="Tuesday, May 5 – Zeiten verfügbar">
 * - Zeitslots: <button data-container="time-button" data-start-time="09:00">
 * - Monatsnavigation: button mit aria-label "Vormonat" / "Nächster Monat"
 * - Aktueller Monat: Element mit data-component="calendar-title" o.ä.
 */

const { chromium } = require('playwright');

/** Maximale Wartezeit für Seitenelemente (ms) */
const TIMEOUT = 15000;

/**
 * Verfügbare Termine von einer Calendly-Seite abrufen.
 *
 * @param {string} calendlyUrl – Die Calendly-Buchungsseite des Beraters
 * @param {string|null} targetDate – Optionales Datum (YYYY-MM-DD). 
 *   Wenn angegeben: navigiert zum richtigen Monat, klickt den Tag an und gibt Zeitslots zurück.
 *   Wenn null: gibt nur die verfügbaren Tage des aktuellen Monats zurück.
 * @returns {Object} – { month, available_days, time_slots? }
 */
async function getAvailability(calendlyUrl, targetDate) {
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
    // ── Seite laden ──────────────────────────────────────────────────────
    await page.goto(calendlyUrl, { waitUntil: 'networkidle', timeout: 30000 });

    // Warten bis der Kalender geladen ist (verfügbare oder nicht-verfügbare Tage)
    await page.waitForSelector('button[aria-label*="verfügbar"], button[aria-label*="available"]', {
      timeout: TIMEOUT
    }).catch(() => {
      // Fallback: vielleicht englische Locale
    });

    // Kurz warten, damit alle Elemente gerendert sind
    await page.waitForTimeout(1000);

    // ── Falls ein bestimmtes Datum gewünscht: zum richtigen Monat navigieren ──
    if (targetDate) {
      await navigateToMonth(page, targetDate);
    }

    // ── Aktuellen Monat/Jahr aus dem Kalender-Header extrahieren ─────────
    const monthTitle = await extractMonthTitle(page);

    // ── Verfügbare Tage extrahieren ──────────────────────────────────────
    const availableDays = await extractAvailableDays(page);

    // ── Falls ein Datum angegeben: Tag anklicken und Zeitslots extrahieren
    if (targetDate) {
      const dayOfMonth = new Date(targetDate).getDate();
      const dayClicked = await clickDay(page, dayOfMonth);

      if (!dayClicked) {
        return {
          month: monthTitle,
          available_days: availableDays,
          requested_date: targetDate,
          time_slots: [],
          message: `Der ${targetDate} ist leider nicht verfügbar.`,
          alternative_days: availableDays
        };
      }

      // Warten bis Zeitslots erscheinen
      await page.waitForTimeout(1500);
      const timeSlots = await extractTimeSlots(page);

      return {
        month: monthTitle,
        available_days: availableDays,
        requested_date: targetDate,
        time_slots: timeSlots
      };
    }

    return {
      month: monthTitle,
      available_days: availableDays
    };

  } finally {
    await browser.close();
  }
}

/**
 * Navigiert zum Monat, der das Zieldatum enthält.
 */
async function navigateToMonth(page, targetDate) {
  const target = new Date(targetDate);
  const targetMonth = target.getMonth(); // 0-basiert
  const targetYear = target.getFullYear();

  // Maximal 12 Monate vor/zurück navigieren
  for (let i = 0; i < 12; i++) {
    const currentMonthTitle = await extractMonthTitle(page);
    const { month: currentMonth, year: currentYear } = parseMonthTitle(currentMonthTitle);

    if (currentMonth === targetMonth && currentYear === targetYear) {
      return; // Richtiger Monat
    }

    // Bestimmen ob vor oder zurück navigiert werden muss
    const currentDate = new Date(currentYear, currentMonth, 1);
    const targetMonthDate = new Date(targetYear, targetMonth, 1);

    if (targetMonthDate > currentDate) {
      // Vorwärts navigieren
      const nextBtn = page.locator('button[aria-label*="Nächster"], button[aria-label*="Next"], button[aria-label*="nächster"]').first();
      if (await nextBtn.isVisible()) {
        await nextBtn.click();
        await page.waitForTimeout(1000);
      }
    } else {
      // Rückwärts navigieren
      const prevBtn = page.locator('button[aria-label*="Vormonat"], button[aria-label*="Previous"], button[aria-label*="Vorheriger"]').first();
      if (await prevBtn.isVisible()) {
        await prevBtn.click();
        await page.waitForTimeout(1000);
      }
    }
  }
}

/**
 * Extrahiert den Monatstitel aus dem Kalender-Header.
 * Calendly nutzt ein <div data-testid="title"> mit z.B. "Mai 2026".
 */
async function extractMonthTitle(page) {
  // Prioritätsreihenfolge der Selektoren
  const selectors = [
    '[data-testid="title"]',
    '[data-component="calendar-title"]',
    '[aria-live="polite"]',
    'h2',
    '.calendar-title'
  ];

  for (const sel of selectors) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) {
      const text = await el.textContent();
      if (text && text.trim().length > 0) {
        return text.trim();
      }
    }
  }

  return 'Unbekannt';
}

/**
 * Parst einen deutschen oder englischen Monatstitel in Monat (0-basiert) und Jahr.
 */
function parseMonthTitle(title) {
  const monthsDE = {
    'januar': 0, 'februar': 1, 'märz': 2, 'april': 3, 'mai': 4, 'juni': 5,
    'juli': 6, 'august': 7, 'september': 8, 'oktober': 9, 'november': 10, 'dezember': 11
  };
  const monthsEN = {
    'january': 0, 'february': 1, 'march': 2, 'april': 3, 'may': 4, 'june': 5,
    'july': 6, 'august': 7, 'september': 8, 'october': 9, 'november': 10, 'december': 11
  };

  const allMonths = { ...monthsDE, ...monthsEN };
  const lower = title.toLowerCase();

  for (const [name, idx] of Object.entries(allMonths)) {
    if (lower.includes(name)) {
      const yearMatch = title.match(/(\d{4})/);
      return {
        month: idx,
        year: yearMatch ? parseInt(yearMatch[1]) : new Date().getFullYear()
      };
    }
  }

  return { month: new Date().getMonth(), year: new Date().getFullYear() };
}

/**
 * Extrahiert alle verfügbaren Tage (mit Datum) aus dem Kalender.
 * Calendly-aria-labels:
 *   Verfügbar:     "Tuesday, May 5 – Zeiten verfügbar"
 *   Nicht verfügbar: "Monday, May 4 – Keine Zeiten verfügbar"
 * Wichtig: "Keine Zeiten verfügbar" muss ausgeschlossen werden!
 */
async function extractAvailableDays(page) {
  const days = await page.evaluate(() => {
    const buttons = document.querySelectorAll('button[aria-label]');
    const available = [];
    const seen = new Set();

    for (const btn of buttons) {
      const label = btn.getAttribute('aria-label') || '';

      // Nur Tage mit "Zeiten verfügbar" / "Times available" (NICHT "Keine")
      const isAvailable =
        (label.includes('Zeiten verfügbar') && !label.includes('Keine Zeiten')) ||
        (label.includes('Times available') && !label.includes('No times'));

      if (!isAvailable) continue;

      const dayText = btn.textContent?.trim();
      const dayNum = parseInt(dayText) || 0;

      // Deduplizierung: Tage vom Vormonat können gleiche Nummern haben
      const key = `${dayNum}-${label}`;
      if (seen.has(key)) continue;
      seen.add(key);

      available.push({
        day: dayNum,
        label: label
      });
    }

    return available.sort((a, b) => a.day - b.day);
  });

  return days;
}

/**
 * Klickt auf einen bestimmten Tag im Kalender.
 * @returns {boolean} – true wenn der Tag verfügbar war und geklickt wurde
 */
async function clickDay(page, dayOfMonth) {
  // Suche den Button für diesen Tag, der als verfügbar markiert ist
  const dayButton = page.locator(
    `button[aria-label*="verfügbar"] span:text-is("${dayOfMonth}"), ` +
    `button[aria-label*="available"] span:text-is("${dayOfMonth}")`
  ).first();

  // Fallback: Versuche den übergeordneten Button direkt
  const parentButton = page.locator(
    `button[aria-label*="verfügbar"]:has(span:text-is("${dayOfMonth}")), ` +
    `button[aria-label*="available"]:has(span:text-is("${dayOfMonth}"))`
  ).first();

  try {
    if (await parentButton.isVisible({ timeout: 3000 })) {
      await parentButton.click();
      return true;
    }
  } catch {
    // Tag nicht verfügbar
  }

  return false;
}

/**
 * Extrahiert alle verfügbaren Zeitslots nach dem Klick auf einen Tag.
 * Calendly zeigt Zeitslots als Buttons mit data-start-time Attribut.
 */
async function extractTimeSlots(page) {
  // Warten auf die Zeitslot-Liste
  await page.waitForSelector('[data-container="time-button"], [data-start-time]', {
    timeout: TIMEOUT
  }).catch(() => {});

  const slots = await page.evaluate(() => {
    const buttons = document.querySelectorAll('[data-container="time-button"], button[data-start-time]');
    const times = [];

    for (const btn of buttons) {
      const startTime = btn.getAttribute('data-start-time');
      const timeText = btn.textContent?.trim();
      if (startTime || timeText) {
        times.push({
          time: startTime || timeText,
          display: timeText || startTime
        });
      }
    }

    return times;
  });

  return slots;
}

module.exports = { getAvailability };
