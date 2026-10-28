<?php
/**
 * Gesprächsverlauf-Relay für den Finanzierungscheck.
 *
 * Nimmt den Chatverlauf als plain-text POST-Body entgegen und leitet ihn
 * als CRM-Notiz an Pitcom weiter.
 *
 * POST ?t={sessionToken}
 *   Content-Type: text/plain
 *   Body: formatierten Gesprächsverlauf
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

// ─── Transcript aus Body lesen ───────────────────────────────────────────────────
$transcript = file_get_contents('php://input');
if ($transcript === false || trim($transcript) === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Leerer Gesprächsverlauf.']);
    exit;
}

// ─── Ohne pitcom_session_id: lokal protokollieren, OK zurückgeben ────────────────
if ($pitcomSessionId === '') {
    error_log('[transcript.php] pitcom_session_id nicht ermittelbar — Transkript nicht weitergeleitet.');
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

// ─── Relay zu Pitcom ─────────────────────────────────────────────────────────────
$ep        = pitcom_endpoint($session, 'add-notice');
$pitcomUrl = $ep['url'];
$bearer    = $ep['bearer'];

$headers = [
    'Authorization: Bearer ' . $bearer,
    'Content-Type: text/plain',
    'User-Agent: ' . $browserUa,
];
if ($humanCookie !== '') {
    $headers[] = 'Cookie: ' . $humanCookie;
}

$ch = curl_init($pitcomUrl);
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => $transcript,
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
    error_log("[transcript.php] Pitcom-Fehler ($pitcomCode): $curlErr | Response: " . substr($pitcomRes, 0, 300));
}

echo json_encode(['ok' => $ok, 'http_code' => $pitcomCode, 'relayed' => true], JSON_UNESCAPED_UNICODE);
