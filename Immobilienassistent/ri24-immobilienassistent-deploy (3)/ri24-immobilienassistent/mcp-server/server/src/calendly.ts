/**
 * Calendly Service – Playwright-basiertes Scraping & Booking
 *
 * Stellt zwei Funktionen bereit:
 *   - getAvailability(): Verfügbare Tage & Zeitslots
 *   - createBooking(): Termin buchen
 *
 * Wird als MCP-Tool im bestehenden Server registriert.
 * Nutzt playwright-extra mit Stealth-Plugin und gespeicherte Cookies
 * um reCAPTCHA zu umgehen.
 */

import { chromium } from 'playwright-extra';
import type { Page, Browser } from 'playwright';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import path from 'node:path';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

// Stealth-Plugin aktivieren (maskiert Bot-Erkennungsmerkmale)
chromium.use(StealthPlugin());

// Debug-Ordner für Screenshots
const DEBUG_DIR = path.resolve(process.cwd(), '..', 'calendly-debug');
try { mkdirSync(DEBUG_DIR, { recursive: true }); } catch {}

// Cookie-Datei – wird geladen und nach jeder Session aktualisiert
const COOKIE_FILE = path.resolve(process.cwd(), '..', 'calendly-cookies.json');

async function debugScreenshot(page: Page, name: string): Promise<void> {
  try {
    const filepath = path.join(DEBUG_DIR, `${name}_${Date.now()}.png`);
    await page.screenshot({ path: filepath, fullPage: true });
    console.log(`[calendly] 📸 Screenshot: ${filepath}`);
  } catch (e) {
    console.warn(`[calendly] Screenshot fehlgeschlagen: ${e}`);
  }
}

const TIMEOUT = 15000;

// Persistentes Browser-Profil
const BROWSER_PROFILE_DIR = path.resolve(process.cwd(), '..', 'calendly-browser-profile');
try { mkdirSync(BROWSER_PROFILE_DIR, { recursive: true }); } catch {}

const BROWSER_ARGS = [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-blink-features=AutomationControlled',
  '--disable-infobars',
  '--window-size=1920,1080'
];

/**
 * Lädt gespeicherte Cookies und filtert Admin-Cookies heraus.
 * Admin-Cookies (authenticated, login_email etc.) verursachen Sicherheitsblockaden,
 * weil Calendly erkennt, dass ein Admin seinen eigenen Kalender bucht.
 * Nur Tracking-/Consent-Cookies werden behalten.
 */
function loadGuestCookies(): any[] {
  // Admin-Cookie-Namen, die NICHT geladen werden dürfen
  const ADMIN_COOKIE_NAMES = new Set([
    'authenticated',
    'CALENDLY_AUTHENTICATED_USER_STATUS',
    'login_email',
    'referrer_user_id',
    '_calendly_session',
  ]);

  try {
    const raw = readFileSync(COOKIE_FILE, 'utf-8');
    const allCookies = JSON.parse(raw);
    const guestCookies = allCookies.filter((c: any) =>
      !ADMIN_COOKIE_NAMES.has(c.name) &&
      !c.name.startsWith('calendly_idd_id_')
    );
    console.log(`[calendly] ${guestCookies.length}/${allCookies.length} Gast-Cookies geladen (Admin-Cookies gefiltert)`);
    return guestCookies;
  } catch (e) {
    console.warn(`[calendly] Keine Cookies geladen: ${e}`);
    return [];
  }
}

/**
 * Speichert aktuelle Browser-Cookies zurück in die JSON-Datei (nur Gast-Cookies).
 */
async function saveCookies(context: any): Promise<void> {
  try {
    const cookies = await context.cookies('https://calendly.com');
    if (cookies.length > 0) {
      writeFileSync(COOKIE_FILE, JSON.stringify(cookies, null, 2));
      console.log(`[calendly] ${cookies.length} Cookies gespeichert`);
    }
  } catch (e) {
    console.warn(`[calendly] Cookies konnten nicht gespeichert werden: ${e}`);
  }
}

/**
 * Startet einen sauberen Browser OHNE Admin-Cookies.
 * Nutzt persistentes Profil für Browser-Fingerprint-Konsistenz.
 */
async function launchBrowser(): Promise<{ context: any; page: Page; close: () => Promise<void> }> {
  const context = await chromium.launchPersistentContext(BROWSER_PROFILE_DIR, {
    headless: true,
    args: BROWSER_ARGS,
    locale: 'de-DE',
    timezoneId: 'Europe/Berlin',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    viewport: { width: 1920, height: 1080 },
    screen: { width: 1920, height: 1080 }
  });

  // KEINE Admin-Cookies injizieren! Nur saubere Gast-Session verwenden.
  console.log('[calendly] Browser gestartet (saubere Gast-Session)');

  const page = context.pages()[0] || await context.newPage();

  return {
    context,
    page,
    close: async () => {
      await saveCookies(context);
      await context.close();
    }
  };
}

// ─── Types ───────────────────────────────────────────────────────────────────

interface AvailableDay {
  day: number;
  label: string;
}

interface TimeSlot {
  time: string;
  display: string;
}

interface AvailabilityResult {
  month: string;
  available_days: AvailableDay[];
  requested_date?: string;
  time_slots?: TimeSlot[];
  message?: string;
  alternative_days?: AvailableDay[];
}

interface BookingParams {
  calendly_url: string;
  date: string;
  time: string;
  location: 'outbound_call' | 'physical' | 'google_conference';
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
}

interface BookingResult {
  success: boolean;
  message: string;
  booked_date: string;
  booked_time: string;
  booked_location: string;
}

// ─── Cookie-Banner ───────────────────────────────────────────────────────────

async function dismissCookieBanner(page: Page): Promise<void> {
  const cookieSelectors = [
    'button:has-text("Alle akzeptieren")',
    'button:has-text("Accept all")',
    'button:has-text("Akzeptieren")',
    'button:has-text("Accept")',
    'button[data-testid="cookie-accept"]',
    '#onetrust-accept-btn-handler'
  ];

  for (const sel of cookieSelectors) {
    try {
      const btn = page.locator(sel).first();
      if (await btn.isVisible({ timeout: 2000 })) {
        await btn.click();
        console.log(`[calendly] Cookie-Banner geschlossen mit: ${sel}`);
        await page.waitForTimeout(500);
        return;
      }
    } catch { /* kein Cookie-Banner */ }
  }
}

// ─── Availability ────────────────────────────────────────────────────────────

export async function getAvailability(calendlyUrl: string, targetDate: string | null): Promise<AvailabilityResult> {
  const { page, close } = await launchBrowser();

  try {
    await page.goto(calendlyUrl, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await dismissCookieBanner(page);

    // Falls ein bestimmtes Datum gewünscht: zum richtigen Monat navigieren
    if (targetDate) {
      await navigateToMonth(page, targetDate);
    }

    const monthTitle = await extractMonthTitle(page);
    const availableDays = await extractAvailableDays(page);

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

      await page.waitForTimeout(1500);
      const timeSlots = await extractTimeSlots(page);

      return {
        month: monthTitle,
        available_days: availableDays,
        requested_date: targetDate,
        time_slots: timeSlots
      };
    }

    return { month: monthTitle, available_days: availableDays };
  } finally {
    await close();
  }
}

// ─── Booking ─────────────────────────────────────────────────────────────────

/**
 * Mapping für Ort-Konfiguration.
 */
function locationConfig(loc: string): { kind: string; location?: string } {
  switch (loc) {
    case 'physical':
      return { kind: 'physical', location: 'Kirchstraße 2, 08523 Plauen' };
    case 'phone':
    case 'outbound_call':
      return { kind: 'outbound_call' };
    case 'online':
    case 'google_conference':
    default:
      return { kind: 'google_meet' };
  }
}

// ─── Pre-filled Booking URL ──────────────────────────────────────────────────

/**
 * Generiert eine vorausgefüllte Calendly-URL.
 * Der Endnutzer kann diese URL öffnen und den Termin mit einem Klick bestätigen.
 */
function generatePrefilledUrl(params: BookingParams): string {
  const { calendly_url, date, time, first_name, last_name, email, phone, location } = params;

  const baseUrl = calendly_url.replace(/\/$/, '');

  // Telefonnummer normalisieren:
  //   0176...   → 49176...  (Calendly setzt selbst ein + davor)
  //   +49176... → 49176...
  let normalizedPhone = (phone || '').replace(/\s+/g, '');
  if (normalizedPhone.startsWith('+')) {
    normalizedPhone = normalizedPhone.substring(1);
  } else if (normalizedPhone.startsWith('00')) {
    normalizedPhone = normalizedPhone.substring(2);
  } else if (normalizedPhone.startsWith('0')) {
    normalizedPhone = '49' + normalizedPhone.substring(1);
  }

  // URL-Parameter zusammenbauen
  // Hinweis: Calendly unterstützt KEINE Vorauswahl der Location-Radiobuttons
  // per URL-Parameter bei Multi-Location Events.
  const queryParams = new URLSearchParams({
    month: date.substring(0, 7),
    date: date,
    name: `${first_name} ${last_name}`,
    email: email,
    ...(normalizedPhone ? { a1: normalizedPhone } : {})
  });

  // Zeitslot-basierte URL
  const dateTimeUrl = `${baseUrl}/${date}T${time}:00+02:00`;
  return `${dateTimeUrl}?${queryParams.toString()}`;
}

// ─── createBooking ───────────────────────────────────────────────────────────

export async function createBooking(params: BookingParams): Promise<BookingResult> {
  const { calendly_url, date, time, location, first_name, last_name, email, phone } = params;


  // ── Strategie B: Pre-filled URL generieren ──
  console.log('[calendly] Generiere vorausgefüllte Buchungs-URL...');

  // Zuerst prüfen ob der Zeitslot verfügbar ist
  const { page, close } = await launchBrowser();

  try {
    console.log(`[calendly] Öffne ${calendly_url}`);
    await page.goto(calendly_url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await dismissCookieBanner(page);

    // Zum richtigen Monat navigieren
    await navigateToMonth(page, date);

    // Tag prüfen
    const dayOfMonth = new Date(date).getDate();
    console.log(`[calendly] Prüfe Verfügbarkeit Tag ${dayOfMonth}`);
    if (!await clickDay(page, dayOfMonth)) {
      throw new Error(`Der ${date} ist nicht verfügbar. Bitte einen anderen Tag wählen.`);
    }
    await page.waitForTimeout(1500);

    // Zeitslot prüfen
    console.log(`[calendly] Prüfe Zeitslot ${time}`);
    if (!await clickTimeSlot(page, time)) {
      throw new Error(`Die Uhrzeit ${time} ist nicht verfügbar am ${date}.`);
    }

    // Vorausgefüllte URL generieren
    const prefilledUrl = generatePrefilledUrl(params);
    console.log(`[calendly] ✅ Vorausgefüllte URL: ${prefilledUrl}`);

    return {
      success: true,
      message: `Der Zeitslot am ${date} um ${time} Uhr ist verfügbar! ` +
               `Da eine automatische Buchung aus Sicherheitsgründen nicht möglich ist, ` +
               `wurde ein vorausgefüllter Buchungslink erstellt. ` +
               `Bitte öffnen Sie den folgenden Link, um die Buchung abzuschließen:\n\n` +
               `👉 ${prefilledUrl}\n\n` +
               `Ihre Daten (${first_name} ${last_name}, ${email}) sind bereits vorausgefüllt.\n` +
               `📋 Bitte wählen Sie auf der Buchungsseite noch die gewünschte Terminart aus (Telefonisch, Vor Ort oder Online per Google Meet).`,
      booked_date: date,
      booked_time: time,
      booked_location: ''
    };
  } finally {
    await close();
  }
}

// ─── Helper Functions ────────────────────────────────────────────────────────

async function navigateToMonth(page: Page, targetDate: string): Promise<void> {
  const target = new Date(targetDate);
  const targetMonth = target.getMonth();
  const targetYear = target.getFullYear();

  for (let i = 0; i < 12; i++) {
    const currentMonthTitle = await extractMonthTitle(page);
    const { month: currentMonth, year: currentYear } = parseMonthTitle(currentMonthTitle);

    if (currentMonth === targetMonth && currentYear === targetYear) return;

    const currentDate = new Date(currentYear, currentMonth, 1);
    const targetMonthDate = new Date(targetYear, targetMonth, 1);

    if (targetMonthDate > currentDate) {
      const nextBtn = page.locator('button[aria-label*="Nächster"], button[aria-label*="Next"], button[aria-label*="nächster"]').first();
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click();
        await page.waitForTimeout(1000);
      }
    } else {
      const prevBtn = page.locator('button[aria-label*="Vormonat"], button[aria-label*="Previous"], button[aria-label*="Vorheriger"]').first();
      if (await prevBtn.isVisible().catch(() => false)) {
        await prevBtn.click();
        await page.waitForTimeout(1000);
      }
    }
  }
}

async function extractMonthTitle(page: Page): Promise<string> {
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
      if (text && text.trim().length > 0) return text.trim();
    }
  }
  return 'Unbekannt';
}

function parseMonthTitle(title: string): { month: number; year: number } {
  const months: Record<string, number> = {
    'januar': 0, 'january': 0, 'februar': 1, 'february': 1, 'märz': 2, 'march': 2,
    'april': 3, 'mai': 4, 'may': 4, 'juni': 5, 'june': 5,
    'juli': 6, 'july': 6, 'august': 7, 'september': 8,
    'oktober': 9, 'october': 9, 'november': 10, 'dezember': 11, 'december': 11
  };

  const lower = title.toLowerCase();
  for (const [name, idx] of Object.entries(months)) {
    if (lower.includes(name)) {
      const yearMatch = title.match(/(\d{4})/);
      return { month: idx, year: yearMatch ? parseInt(yearMatch[1]) : new Date().getFullYear() };
    }
  }
  return { month: new Date().getMonth(), year: new Date().getFullYear() };
}

async function extractAvailableDays(page: Page): Promise<AvailableDay[]> {
  return page.evaluate(() => {
    const buttons = document.querySelectorAll('button[aria-label]');
    const available: { day: number; label: string }[] = [];
    const seen = new Set<string>();

    for (const btn of buttons) {
      const label = btn.getAttribute('aria-label') || '';

      const isAvailable =
        (label.includes('Zeiten verfügbar') && !label.includes('Keine Zeiten')) ||
        (label.includes('Times available') && !label.includes('No times'));

      if (!isAvailable) continue;

      const dayText = btn.textContent?.trim();
      const dayNum = parseInt(dayText || '0') || 0;
      const key = `${dayNum}-${label}`;
      if (seen.has(key)) continue;
      seen.add(key);

      available.push({ day: dayNum, label });
    }

    return available.sort((a, b) => a.day - b.day);
  });
}

async function clickDay(page: Page, dayOfMonth: number): Promise<boolean> {
  const dayStr = String(dayOfMonth);

  const availableButton = page.locator(
    `button[aria-label*="Zeiten verfügbar"]:has(span:text-is("${dayStr}")), ` +
    `button[aria-label*="Times available"]:has(span:text-is("${dayStr}"))`
  ).first();

  try {
    if (await availableButton.isVisible({ timeout: 3000 })) {
      await availableButton.click();
      return true;
    }
  } catch { /* nicht verfügbar */ }

  // Fallback: bookable-Klasse
  const bookableButton = page.locator(`button[class*="bookable"]:has(span:text-is("${dayStr}"))`).first();
  try {
    if (await bookableButton.isVisible({ timeout: 2000 })) {
      await bookableButton.click();
      return true;
    }
  } catch { /* nicht verfügbar */ }

  return false;
}

async function extractTimeSlots(page: Page): Promise<TimeSlot[]> {
  await page.waitForSelector('[data-container="time-button"], button[data-start-time]', { timeout: TIMEOUT }).catch(() => {});

  return page.evaluate(() => {
    const buttons = document.querySelectorAll('[data-container="time-button"], button[data-start-time]');
    const times: { time: string; display: string }[] = [];

    for (const btn of buttons) {
      const startTime = btn.getAttribute('data-start-time');
      const timeText = btn.textContent?.trim();
      if (startTime || timeText) {
        times.push({ time: startTime || timeText || '', display: timeText || startTime || '' });
      }
    }
    return times;
  });
}

async function clickTimeSlot(page: Page, time: string): Promise<boolean> {
  const normalizedTime = time.padStart(5, '0');

  const timeButton = page.locator(`button[data-start-time="${normalizedTime}"]`).first();
  try {
    if (await timeButton.isVisible({ timeout: 5000 })) {
      await timeButton.click();
      return true;
    }
  } catch { /* nicht gefunden */ }

  const textButton = page.locator(`[data-container="time-button"]:has-text("${normalizedTime}")`).first();
  try {
    if (await textButton.isVisible({ timeout: 3000 })) {
      await textButton.click();
      return true;
    }
  } catch { /* nicht gefunden */ }

  return false;
}

/**
 * Klickt den "Weiter"-Button, der nach Zeitslot-Auswahl neben dem Slot erscheint.
 * Calendly zeigt auf deutschen Seiten "Weiter" statt "Next"/"Confirm".
 */
async function clickWeiterButton(page: Page): Promise<void> {
  const selectors = [
    // Priorität: Deutsche Selektoren zuerst
    'button[aria-label^="Weiter"]',
    'button:has-text("Weiter")',
    'button[data-container="confirm-button"]',
    'button:has-text("Bestätigen")',
    'button:has-text("Confirm")',
    'button:has-text("Next")'
  ];

  for (const sel of selectors) {
    const btn = page.locator(sel).first();
    try {
      if (await btn.isVisible({ timeout: 3000 })) {
        console.log(`[calendly] "Weiter"-Button gefunden mit: ${sel}`);
        await btn.click();
        return;
      }
    } catch { /* nicht gefunden */ }
  }
  console.warn('[calendly] Kein "Weiter"-Button gefunden, fahre fort...');
}

/**
 * Wählt den Terminort per Klick auf das Radio-Label im Formular.
 * Calendly zeigt die Optionen als Radio-Buttons in einer fieldset[role="radiogroup"].
 * Die Labels enthalten Klartext wie "Anruf", "Google Meet", oder die physische Adresse.
 */
async function selectLocation(page: Page, locationValue: string): Promise<void> {
  // Mapping von API-Werten auf Calendly-Seitentext
  const locationTexts: Record<string, string[]> = {
    'outbound_call': ['Anruf', 'Phone call', 'Call', 'Telefon'],
    'physical': ['Kirchstraße', 'Vor Ort', 'In person', 'Office'],
    'google_conference': ['Google Meet', 'Google Conference', 'Online']
  };

  const searchTexts = locationTexts[locationValue] || [locationValue];

  // Versuche jedes mögliche Label zu finden
  for (const text of searchTexts) {
    try {
      // Suche in der radiogroup nach Labels die den Text enthalten
      const radioLabel = page.locator(`fieldset[role="radiogroup"] label:has-text("${text}")`).first();
      if (await radioLabel.isVisible({ timeout: 2000 }).catch(() => false)) {
        await radioLabel.click();
        console.log(`[calendly] Ort gewählt per Label-Text: "${text}"`);
        return;
      }

      // Fallback: beliebiges Label mit dem Text
      const anyLabel = page.locator(`label:has-text("${text}")`).first();
      if (await anyLabel.isVisible({ timeout: 1000 }).catch(() => false)) {
        await anyLabel.click();
        console.log(`[calendly] Ort gewählt per Label-Fallback: "${text}"`);
        return;
      }
    } catch { /* nächsten Text probieren */ }
  }

  // Letzter Fallback: Erstes Radio-Element anklicken
  try {
    const firstRadio = page.locator('fieldset[role="radiogroup"] label').first();
    if (await firstRadio.isVisible({ timeout: 2000 }).catch(() => false)) {
      await firstRadio.click();
      console.warn(`[calendly] Kein passender Ort gefunden, erste Option gewählt.`);
    }
  } catch {
    console.warn(`[calendly] Ortsauswahl komplett fehlgeschlagen für "${locationValue}"`);
  }
}

/**
 * Füllt das Kontaktformular aus.
 * Calendly verwendet teilweise dynamische IDs, daher nutzen wir stabile Selektoren:
 * - name="full_name" (Vor- + Nachname) oder name="first_name" / name="last_name"
 * - id="email_input" (stabil)
 * - input[type="tel"] für Telefon
 */
async function fillContactForm(page: Page, data: { first_name: string; last_name: string; email: string; phone?: string }): Promise<void> {
  // Warten bis das Formular sichtbar ist
  await page.waitForSelector('input[name="full_name"], input[name="first_name"], input#email_input', {
    state: 'visible',
    timeout: TIMEOUT
  }).catch(() => {});

  // Vorname + Nachname: Calendly kann ein kombiniertes Feld oder getrennte Felder haben
  const fullNameInput = page.locator('input[name="full_name"]').first();
  const firstNameInput = page.locator('input[name="first_name"]').first();
  const lastNameInput = page.locator('input[name="last_name"]').first();

  if (await fullNameInput.isVisible({ timeout: 2000 }).catch(() => false)) {
    await fullNameInput.fill(`${data.first_name} ${data.last_name}`);
    console.log('[calendly] Volles Namensfeld ausgefüllt');
  } else if (await firstNameInput.isVisible({ timeout: 2000 }).catch(() => false)) {
    await firstNameInput.fill(data.first_name);
    if (await lastNameInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      await lastNameInput.fill(data.last_name);
    }
    console.log('[calendly] Getrennte Namensfelder ausgefüllt');
  } else {
    // Fallback: Suche nach aria-label oder placeholder
    const nameInputs = page.locator('input[type="text"]');
    const count = await nameInputs.count();
    if (count >= 2) {
      await nameInputs.nth(0).fill(data.first_name);
      await nameInputs.nth(1).fill(data.last_name);
      console.log('[calendly] Namensfelder per Positionsindex ausgefüllt');
    }
  }

  // E-Mail: id="email_input" ist stabil bei Calendly
  const emailInput = page.locator('input#email_input, input[name="email"], input[type="email"]').first();
  if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
    await emailInput.fill(data.email);
    console.log('[calendly] E-Mail ausgefüllt');
  }

  // Telefon
  if (data.phone) {
    const phoneInput = page.locator('input[type="tel"]').first();
    try {
      if (await phoneInput.isVisible({ timeout: 3000 })) {
        await phoneInput.fill(data.phone);
        console.log('[calendly] Telefonnummer ausgefüllt');
      }
    } catch {
      console.warn('[calendly] Telefon-Eingabefeld nicht gefunden');
    }
  }
}

/**
 * Klickt den "Termin buchen" / "Schedule Event" Button.
 */
async function submitBooking(page: Page): Promise<void> {
  const selectors = [
    // Deutsche Varianten zuerst
    'button:has-text("Termin buchen")',
    'button:has-text("Termin planen")',
    'button[type="submit"]',
    'button:has-text("Schedule Event")',
    'button:has-text("Confirm")',
    'button:has-text("Buchen")'
  ];

  for (const sel of selectors) {
    const btn = page.locator(sel).first();
    try {
      if (await btn.isVisible({ timeout: 3000 })) {
        console.log(`[calendly] Submit-Button gefunden: ${sel}`);
        await btn.click();
        return;
      }
    } catch { /* nicht gefunden */ }
  }

  throw new Error('Submit-Button ("Termin buchen") nicht gefunden.');
}

/**
 * Prüft ob ein reCAPTCHA-Dialog sichtbar ist und versucht ihn zu lösen.
 * Muss NACH dem Submit-Klick UND nach ausreichender Wartezeit aufgerufen werden.
 *
 * Calendly-Struktur:
 *   div[role="dialog"][aria-modal="true"]
 *     h2 "Bestätigen Sie, dass Sie ein Mensch sind."
 *     div#recaptcha-challenge
 *       iframe[title="reCAPTCHA"]   ← Checkbox liegt hier drin
 *     button "Fortfahren"           ← im Hauptdokument, NICHT im iframe
 */
async function handleRecaptcha(page: Page): Promise<void> {
  // Mehrere Selektoren für den Dialog probieren
  const dialogSelectors = [
    '[role="dialog"]:has-text("Mensch")',
    '[role="dialog"]:has-text("Roboter")',
    '[aria-modal="true"]:has-text("Mensch")',
    '#recaptcha-challenge',
    'text="Bestätigen Sie, dass Sie ein Mensch sind"'
  ];

  let dialogFound = false;
  for (const sel of dialogSelectors) {
    try {
      const el = page.locator(sel).first();
      if (await el.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log(`[calendly] ⚠️ reCAPTCHA-Dialog erkannt mit: ${sel}`);
        dialogFound = true;
        break;
      }
    } catch { /* nächsten probieren */ }
  }

  if (!dialogFound) {
    // Auch auf den "Fortfahren"-Button prüfen (der ist nur im reCAPTCHA-Dialog)
    const fortfahrenBtn = page.locator('button:has-text("Fortfahren")').first();
    if (await fortfahrenBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      console.log('[calendly] ⚠️ reCAPTCHA erkannt via "Fortfahren"-Button');
      dialogFound = true;
    }
  }

  if (!dialogFound) {
    console.log('[calendly] Kein reCAPTCHA-Dialog erkannt – Buchung geht direkt durch');
    return;
  }

  await debugScreenshot(page, '08a_recaptcha_dialog');

  // Die reCAPTCHA-Checkbox liegt in einem iframe
  // Versuche mehrere iframe-Selektoren
  const iframeSelectors = [
    'iframe[title="reCAPTCHA"]',
    'iframe[title*="recaptcha" i]',
    'iframe[src*="recaptcha"]',
    '#recaptcha-challenge iframe'
  ];

  for (const iframeSel of iframeSelectors) {
    try {
      const recaptchaFrame = page.frameLocator(iframeSel).first();
      const checkbox = recaptchaFrame.locator('#recaptcha-anchor, .recaptcha-checkbox, [role="checkbox"]').first();

      if (await checkbox.isVisible({ timeout: 5000 }).catch(() => false)) {
        console.log(`[calendly] reCAPTCHA-Checkbox gefunden in: ${iframeSel}`);
        await checkbox.click();

        // Warte auf reCAPTCHA-Verarbeitung
        await page.waitForTimeout(5000);
        await debugScreenshot(page, '08b_nach_recaptcha_click');

        // Prüfe ob die Checkbox jetzt checked ist
        const isChecked = await recaptchaFrame.locator('[aria-checked="true"]').first().isVisible({ timeout: 5000 }).catch(() => false);
        console.log(`[calendly] reCAPTCHA Checkbox checked: ${isChecked}`);

        if (!isChecked) {
          console.warn('[calendly] reCAPTCHA-Checkbox wurde nicht als checked erkannt – evtl. Bildrätsel erforderlich');
          await debugScreenshot(page, '08b2_recaptcha_challenge');
        }

        // "Fortfahren"-Button im Hauptdokument klicken
        const continueBtn = page.locator('button:has-text("Fortfahren")').first();
        if (await continueBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
          console.log('[calendly] "Fortfahren"-Button gefunden, klicke...');
          await continueBtn.click();
          await page.waitForTimeout(5000);
          await debugScreenshot(page, '08c_nach_fortfahren');
        } else {
          console.warn('[calendly] "Fortfahren"-Button nicht sichtbar');
        }
        return; // Fertig
      }
    } catch {
      console.log(`[calendly] iframe ${iframeSel} nicht gefunden`);
    }
  }

  console.warn('[calendly] reCAPTCHA-Dialog gefunden, aber Checkbox konnte nicht angeklickt werden');
  await debugScreenshot(page, '08d_recaptcha_fehler');
}

/**
 * Wartet auf die Buchungsbestätigung.
 * Calendly leitet nach dem Submit auf eine Bestätigungsseite weiter.
 * Die URL ändert sich (enthält "invitee" oder ähnliches) und die Seite zeigt "Bestätigt" o.ä.
 */
async function waitForConfirmation(page: Page, urlBeforeSubmit: string): Promise<string> {
  const currentUrl = page.url();
  console.log(`[calendly] Bestätigungsprüfung – aktuelle URL: ${currentUrl}`);

  // Strategie 1: URL hat sich bereits geändert (Submit hat schon redirected)
  if (currentUrl !== urlBeforeSubmit) {
    console.log(`[calendly] URL hat sich geändert von ${urlBeforeSubmit} zu ${currentUrl}`);
    if (currentUrl.includes('invitee') || currentUrl.includes('confirmed') || currentUrl.includes('scheduled')) {
      return 'Termin erfolgreich gebucht!';
    }
    // Auch wenn die URL nicht die typischen Keywords enthält, hat sich etwas getan
    return 'Termin wurde gebucht. Bitte Bestätigungs-E-Mail prüfen.';
  }

  // Strategie 2: Warte auf URL-Änderung (noch nicht passiert, evtl. langsam)
  try {
    await page.waitForURL((url: URL) => url.toString() !== urlBeforeSubmit, { timeout: 15000 });
    console.log(`[calendly] URL geändert nach Warten: ${page.url()}`);
    await page.waitForTimeout(2000);
    await debugScreenshot(page, '09_bestaetigung');
    return 'Termin erfolgreich gebucht!';
  } catch {
    console.log('[calendly] Keine URL-Änderung erkannt');
  }

  // Strategie 3: Text-basierte Erkennung
  const bodyText = await page.textContent('body').catch(() => '') || '';
  const confirmTexts = [
    'Bestätigt', 'bestätigt', 'Confirmed', 'confirmed',
    'You are scheduled', 'erfolgreich', 'Termin ist gebucht',
    'wurde gebucht', 'Vielen Dank', 'E-Mail-Einladung',
    'Kalender hinzugefügt', 'calendar invitation'
  ];

  for (const text of confirmTexts) {
    if (bodyText.includes(text)) {
      console.log(`[calendly] Bestätigung per Text erkannt: "${text}"`);
      return 'Termin erfolgreich gebucht!';
    }
  }

  // Strategie 4: Prüfe ob echte Formular-Validierungsfehler auf der Seite angezeigt werden
  // NICHT den Cookie-Banner-Text als Fehler werten!
  const formErrors = await page.evaluate(() => {
    // Suche nach typischen Fehler-Elementen (rot markierte Felder, Fehlermeldungen)
    const errorElements = document.querySelectorAll(
      '[role="alert"], .error, .field-error, [data-error], [aria-invalid="true"], .validation-error'
    );
    const errors: string[] = [];
    for (const el of errorElements) {
      const text = el.textContent?.trim();
      if (text && text.length > 0 && text.length < 200) {
        errors.push(text);
      }
    }
    return errors;
  });

  // Debug: Seiten-Body loggen (erste 500 Zeichen)
  const bodyPreview = bodyText.replace(/\s+/g, ' ').trim().substring(0, 500);
  console.log(`[calendly] Seitentext (Preview): ${bodyPreview}`);
  await debugScreenshot(page, '09_fehler_oder_timeout');

  if (formErrors.length > 0) {
    console.log(`[calendly] Formular-Fehler erkannt: ${formErrors.join(', ')}`);
    throw new Error(
      'Formularfehler auf der Calendly-Seite: ' + formErrors.join('; ')
    );
  }

  // Kein Fehler erkannt, aber auch keine Bestätigung → wahrscheinlich Submit-Problem
  // Anstatt zu werfen, geben wir eine Warnung zurück
  console.warn('[calendly] Keine eindeutige Bestätigung oder Fehler erkannt.');
  throw new Error(
    'Buchungsbestätigung konnte nicht verifiziert werden. ' +
    'Debug-Screenshots wurden gespeichert unter: ' + DEBUG_DIR + '. ' +
    'Bitte prüfe den Termin direkt in Calendly oder im E-Mail-Postfach.'
  );
}

function locationLabel(location: string): string {
  const labels: Record<string, string> = {
    'outbound_call': 'Telefonisch (Anruf)',
    'physical': 'Vor Ort beim Berater',
    'google_conference': 'Online (Google Meet)'
  };
  return labels[location] || location;
}
