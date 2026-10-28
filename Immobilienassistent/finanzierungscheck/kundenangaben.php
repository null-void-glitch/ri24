<?php
/**
 * Kundenangaben-Relay für den Finanzierungscheck.
 *
 * Nimmt persönliche und finanzielle Kundendaten entgegen und leitet sie
 * über den Pitcom update-case-Endpoint an Europace weiter.
 *
 * POST ?t={sessionToken}
 *   Content-Type: application/json
 *   Body: {
 *     "geburtsdatum":            "1985-06-15",   // ISO-Datum oder "01.01.1985"
 *     "beschaeftigungsArt":      "ANGESTELLTER", // ANGESTELLTER|SELBSTSTAENDIGER|BEAMTER|RENTNER
 *     "einkommenNetto":          3500,
 *     "eigenKapital":            40000,
 *     "kaufpreis":               320000,         // optional
 *     "objektArt":               "EIGENTUMSWOHNUNG", // optional
 *     "plz":                     "08056",        // optional
 *     "ort":                     "Zwickau",      // optional
 *     "wunschRate":              1200,           // optional
 *     "wunschZinsbindung":       15,             // optional
 *     "ratenKrediteRestschuld":  0               // optional
 *   }
 *
 * Antwort: { ok: bool, http_code: int }
 */

require __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');

// ─── CORS ────────────────────────────────────────────────────────────────────────
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '') {
    $allowed = array_map('trim', explode(',', ALLOWED_ORIGINS));
    if (in_array('*', $allowed, true) || in_array($origin, $allowed, true)) {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Vary: Origin');
        header('Access-Control-Allow-Methods: POST, OPTIONS');
        header('Access-Control-Allow-Headers: Content-Type');
    }
}
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Method not allowed']);
    exit;
}

// ─── Token & Session laden ───────────────────────────────────────────────────────
$token = preg_replace('/[^A-Za-z0-9]/', '', (string)($_GET['t'] ?? ''));
if ($token === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Kein Token angegeben.']);
    exit;
}

$sessionFile = SESSIONS_DIR . '/' . $token . '.json';
if (!is_file($sessionFile)) {
    http_response_code(404);
    echo json_encode(['ok' => false, 'error' => 'Ungültiger oder abgelaufener Link.']);
    exit;
}

require_once __DIR__ . '/pitcom.php';
$session         = json_decode((string)file_get_contents($sessionFile), true) ?: [];
$pitcomSessionId = pitcom_ensure_session_id($sessionFile, $session);

// ─── Payload lesen ───────────────────────────────────────────────────────────────
$raw     = file_get_contents('php://input');
$payload = json_decode($raw, true);
if (!is_array($payload) || empty($payload)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Leerer oder ungültiger JSON-Body.']);
    exit;
}

// ─── Ohne Pitcom-Session: lokal protokollieren ───────────────────────────────────
if ($pitcomSessionId === '') {
    error_log('[kundenangaben.php] pitcom_session_id nicht ermittelbar — Daten nicht weitergeleitet.');
    echo json_encode(['ok' => true, 'relayed' => false]);
    exit;
}

// ─── Human-Handshake (Spam-Detection-Bypass) ─────────────────────────────────────
$browserUa   = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
$humanCookie = '';
$hsCh = curl_init('https://www.regionalimmobilien24.de/ressource/set/user/human/');
curl_setopt_array($hsCh, [
    CURLOPT_HTTPGET        => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HEADER         => true,
    CURLOPT_TIMEOUT        => 8,
    CURLOPT_HTTPHEADER     => [
        'User-Agent: ' . $browserUa,
        'X-Requested-With: XMLHttpRequest',
        'Accept: application/json, text/javascript, */*; q=0.01',
    ],
]);
$hsResp = curl_exec($hsCh);
curl_close($hsCh);
if ($hsResp && preg_match_all('/^Set-Cookie:\s*([^;]+)/mi', $hsResp, $cm)) {
    $humanCookie = implode('; ', $cm[1]);
}

// ─── Relay zu Pitcom update-case ─────────────────────────────────────────────────
$ep        = pitcom_endpoint($session, 'update-case');
$pitcomUrl = $ep['url'];
$bearer    = $ep['bearer'];

// Feldnamen-Mapping: MCP-Interface → Pitcom-API
$beschMap = [
    'ANGESTELLTER'     => 'Angestellter',
    'SELBSTSTAENDIGER' => 'Selbststaendiger',
    'BEAMTER'          => 'Beamter',
    'RENTNER'          => 'Rentner',
    'FREIBERUFLER'     => 'Freiberufler',
    'ARBEITER'         => 'Arbeiter',
];
$objektartMap = [
    'BAUGRUNDSTUECK'     => 'Baugrundstueck',
    'DOPPELHAUSHAELFTE'  => 'Doppelhaushaelfte',
    'EIGENTUMSWOHNUNG'   => 'Eigentumswohnung',
    'EINFAMILIENHAUS'    => 'Einfamilienhaus',
    'MEHRFAMILIENHAUS'   => 'Mehrfamilienhaus',
    'REIHENHAUS'         => 'Reihenhaus',
    'ZWEIFAMILIENHAUS'   => 'Zweifamilienhaus',
];
$pitcomPayload = [
    'bday'          => $payload['geburtsdatum']       ?? null,
    'nhek'          => isset($payload['einkommenNetto'])       ? (int)$payload['einkommenNetto']       : null,
    'ek'            => isset($payload['eigenKapital'])         ? (int)$payload['eigenKapital']         : null,
    'beschaeftigung'=> $beschMap[$payload['beschaeftigungsArt'] ?? ''] ?? ($payload['beschaeftigungsArt'] ?? null),
    // Objektdaten (optional)
    'object_price'  => isset($payload['kaufpreis'])            ? (int)$payload['kaufpreis']            : null,
    'object_zip'    => $payload['plz']                ?? null,
    'object_city'   => $payload['ort']                ?? null,
    'objektart'     => $objektartMap[$payload['objektArt'] ?? ''] ?? ($payload['objektArt'] ?? null),
    'wunschrate'    => isset($payload['wunschRate'])           ? (int)$payload['wunschRate']           : null,
    'zinsbindung'   => isset($payload['wunschZinsbindung'])    ? (int)$payload['wunschZinsbindung']    : null,
    'restschuld'    => isset($payload['ratenKrediteRestschuld'])? (int)$payload['ratenKrediteRestschuld']: null,
    // Kontaktdaten aus Session
    'vorname'       => $session['vorname']  ?? null,
    'nachname'      => $session['nachname'] ?? null,
    'email'         => $session['email']    ?? null,
    'telefon'       => $session['telefon']  ?? null,
];
$pitcomPayload = array_filter($pitcomPayload, fn($v) => $v !== null);
error_log('[kundenangaben.php] Pitcom-Payload: ' . json_encode($pitcomPayload, JSON_UNESCAPED_UNICODE));

$jsonBody = json_encode($pitcomPayload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

$headers = [
    'Authorization: Bearer ' . $bearer,
    'Content-Type: application/json',
    'User-Agent: ' . $browserUa,
];
if ($humanCookie !== '') {
    $headers[] = 'Cookie: ' . $humanCookie;
}

$ch = curl_init($pitcomUrl);
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => $jsonBody,
    CURLOPT_HTTPHEADER     => $headers,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => 15,
]);
$pitcomRes  = curl_exec($ch);
$pitcomCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlErr    = curl_error($ch);
curl_close($ch);

$ok = $pitcomCode >= 200 && $pitcomCode < 300;
if (!$ok) {
    error_log("[kundenangaben.php] Pitcom-Fehler ($pitcomCode): $curlErr | Response: " . substr((string)$pitcomRes, 0, 300));
}

echo json_encode(['ok' => $ok, 'http_code' => $pitcomCode, 'relayed' => true], JSON_UNESCAPED_UNICODE);
