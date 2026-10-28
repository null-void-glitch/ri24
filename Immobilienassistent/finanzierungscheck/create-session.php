<?php
/**
 * Session-Endpoint für den personalisierten Finanzierungscheck.
 *
 * Wird vom Portal (oder manuell via demo.html) aufgerufen, wenn eine
 * Finanzierungsanfrage eingeht. Speichert die Kundendaten als JSON-Datei
 * und gibt den fertig zusammengebauten Landingpage-Link zurück.
 *
 * Erwarteter Request (JSON POST):
 * {
 *   "vorname":    "Max",
 *   "nachname":   "Mustermann",
 *   "telefon":    "+491761234567",     // international, mit +
 *   "email":      "max@example.com",
 *   "berater_id": "12345",             // optional – Pitcom-Berater-ID
 *   "berater_url": "https://...",      // optional – Berater-Seiten-URL
 *   "case_id":    "A23WYC",           // optional – Europace-Vorgangs-ID (von Pitcom)
 *   "expose_url": "https://www.regionalimmobilien24.de/expose/12345678/",  // optional
 *   "finanzierer": {                   // Daten des zugeschlüsselten Finanzierers
 *     "name": "Musterbank AG",
 *     "id":   "EP-XXXXXX"             // Europace Finanzierer-ID (optional)
 *   }
 * }
 *
 * Antwort (JSON):
 * {
 *   "token":                "abc123...",
 *   "url":                  "https://...?t=abc123...",
 *   "is_mobile":            true,
 *   "whatsapp_recommended": true
 * }
 *
 * Absicherung: CREATE_SESSION_SECRET muss als Bearer-Token im Authorization-Header
 * mitgeschickt werden (konfigurierbar in config.php).
 */

require __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');

// ─── CORS ───────────────────────────────────────────────────────────────────────
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '') {
    $allowed = array_map('trim', explode(',', ALLOWED_ORIGINS));
    if (in_array('*', $allowed, true) || in_array($origin, $allowed, true)) {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Vary: Origin');
        header('Access-Control-Allow-Methods: POST, OPTIONS');
        header('Access-Control-Allow-Headers: Content-Type, Authorization');
    }
}
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

function json_error(int $code, string $message): never
{
    http_response_code($code);
    echo json_encode(['error' => $message], JSON_UNESCAPED_UNICODE);
    exit;
}

// ─── Authentifizierung ───────────────────────────────────────────────────────────
if (CREATE_SESSION_SECRET !== '') {
    $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $provided   = '';
    if (str_starts_with($authHeader, 'Bearer ')) {
        $provided = substr($authHeader, 7);
    }
    if (!hash_equals(CREATE_SESSION_SECRET, $provided)) {
        json_error(401, 'Unauthorized');
    }
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    json_error(405, 'Method not allowed');
}

// ─── Request lesen ───────────────────────────────────────────────────────────────
$raw  = file_get_contents('php://input');
$body = json_decode($raw, true);

if (!is_array($body)) {
    json_error(400, 'Ungültiger JSON-Body');
}

$vorname  = trim((string)($body['vorname']  ?? ''));
$nachname = trim((string)($body['nachname'] ?? ''));
$telefon  = trim((string)($body['telefon']  ?? ''));
$email    = trim((string)($body['email']    ?? ''));

if ($vorname === '' || $nachname === '') {
    json_error(400, 'vorname und nachname sind Pflichtfelder');
}

// ─── Telefonnummer-Analyse ───────────────────────────────────────────────────────
// Erkennt deutsche Mobilnummern anhand ihrer Vorwahl (015x, 016x, 017x).
// Eine exakte WhatsApp-Prüfung über die Meta-API ist serverseitig ohne aktiven
// Konversationsfluss nicht möglich; WhatsApp wird daher für alle Mobilnummern
// empfohlen und der Zustellstatus der Nachricht gibt Aufschluss.
function is_german_mobile(string $number): bool
{
    $cleaned = preg_replace('/[\s\-\(\)]/', '', $number);
    // Normalisieren: +49 oder 0049 → 0
    $cleaned = preg_replace('/^\+49/', '0', $cleaned);
    $cleaned = preg_replace('/^0049/', '0', $cleaned);
    return (bool)preg_match('/^0(15[0-9]|16[0-9]|17[0-9])/', $cleaned);
}

$isMobile            = $telefon !== '' && is_german_mobile($telefon);
$whatsappRecommended = $isMobile;

// ─── Session-Token erzeugen ─────────────────────────────────────────────────────
$token = bin2hex(random_bytes(20)); // 40-stelliger Hex-String

// ─── Zusätzliche Felder aus dem Body übernehmen ─────────────────────────────────
$finanzierer     = is_array($body['finanzierer'] ?? null) ? $body['finanzierer'] : null;
$beraterId       = trim((string)($body['berater_id']        ?? ''));
$beraterUrl      = trim((string)($body['berater_url']       ?? ''));
$caseId          = trim((string)($body['case_id']           ?? ''));
$exposeUrl       = trim((string)($body['expose_url']        ?? ''));
$pitcomSessionId = trim((string)($body['pitcom_session_id'] ?? ''));

// ─── Session speichern ───────────────────────────────────────────────────────────
@mkdir(SESSIONS_DIR, 0700, true);

$session = [
    'token'             => $token,
    'created_at'        => date('c'),
    'vorname'           => $vorname,
    'nachname'          => $nachname,
    'telefon'           => $telefon,
    'email'             => $email,
    'berater_id'        => $beraterId,
    'berater_url'       => $beraterUrl,
    'case_id'           => $caseId,
    'expose_url'        => $exposeUrl,
    'finanzierer'       => $finanzierer,
    'pitcom_session_id' => $pitcomSessionId,  // Pitcom-interner Bezeichner für Callback-Endpunkte
    'sent'              => [],   // wird von send.php befüllt
];

$sessionFile = SESSIONS_DIR . '/' . $token . '.json';
if (file_put_contents($sessionFile, json_encode($session, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX) === false) {
    json_error(500, 'Session konnte nicht gespeichert werden');
}
chmod($sessionFile, 0600);

// ─── Antwort ─────────────────────────────────────────────────────────────────────
// Für Dev/Tunnel-Umgebungen URL aus dem Request ableiten; LANDINGPAGE_BASE_URL
// nur für Produktions-URLs verwenden (nicht localhost, IP, lhr.life, ngrok).
$configBase = defined('LANDINGPAGE_BASE_URL') ? LANDINGPAGE_BASE_URL : '';
$isProd     = $configBase !== ''
    && !preg_match('/localhost|127\.0\.0\.|lhr\.life|ngrok|\.run/', $configBase);

if ($isProd) {
    $sessionBase = $configBase;
} else {
    $proto = 'http';
    if (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') {
        $proto = 'https';
    } elseif (strtolower($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https') {
        $proto = 'https';
    }
    $host        = $_SERVER['HTTP_HOST'] ?? 'localhost:8002';
    $sessionBase = $proto . '://' . $host . '/session.php?t=';
}
$url = $sessionBase . urlencode($token);

echo json_encode([
    'token'                => $token,
    'url'                  => $url,
    'is_mobile'            => $isMobile,
    'whatsapp_recommended' => $whatsappRecommended,
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
