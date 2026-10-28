<?php
/**
 * Versand-Endpoint: Schickt den Landingpage-Link an den Kunden per WhatsApp oder E-Mail.
 *
 * POST mit JSON:
 * {
 *   "token":   "abc123...",
 *   "channel": "whatsapp" | "email"
 * }
 *
 * WhatsApp: Nutzt die Meta Cloud API mit einem vorher genehmigten Template.
 *   Template-Variablen: {{1}} = Vorname, {{2}} = Landingpage-URL
 *
 * E-Mail: Ruft den internen E-Mail-Endpoint auf (bereits vorhanden).
 *
 * Absicherung: CREATE_SESSION_SECRET als Bearer-Token im Authorization-Header.
 */

require __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');

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

// ─── Auth ────────────────────────────────────────────────────────────────────────
if (CREATE_SESSION_SECRET !== '') {
    $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $provided   = str_starts_with($authHeader, 'Bearer ') ? substr($authHeader, 7) : '';
    if (!hash_equals(CREATE_SESSION_SECRET, $provided)) {
        json_error(401, 'Unauthorized');
    }
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    json_error(405, 'Method not allowed');
}

$raw  = file_get_contents('php://input');
$body = json_decode($raw, true);

$token   = preg_replace('/[^A-Za-z0-9]/', '', (string)($body['token']   ?? ''));
$channel = strtolower(trim((string)($body['channel'] ?? '')));

if ($token === '') {
    json_error(400, 'token fehlt');
}
if (!in_array($channel, ['whatsapp', 'email'], true)) {
    json_error(400, 'channel muss "whatsapp" oder "email" sein');
}

// ─── Session laden ───────────────────────────────────────────────────────────────
$sessionFile = SESSIONS_DIR . '/' . $token . '.json';
if (!is_file($sessionFile)) {
    json_error(404, 'Session nicht gefunden');
}
$session = json_decode((string)file_get_contents($sessionFile), true);
if (!is_array($session)) {
    json_error(500, 'Session beschädigt');
}

$vorname = $session['vorname'] ?? '';
$nachname = $session['nachname'] ?? '';
$url      = LANDINGPAGE_BASE_URL . urlencode($token);

// ─── WhatsApp-Versand (Meta Cloud API) ──────────────────────────────────────────
function send_whatsapp(array $session, string $url): array
{
    if (WA_PHONE_NUMBER_ID === '' || WA_ACCESS_TOKEN === '') {
        return ['ok' => false, 'error' => 'WhatsApp nicht konfiguriert (WA_PHONE_NUMBER_ID/WA_ACCESS_TOKEN fehlt)'];
    }

    $telefon = $session['telefon'] ?? '';
    if ($telefon === '') {
        return ['ok' => false, 'error' => 'Keine Telefonnummer in der Session'];
    }

    // Telefonnummer normalisieren: führende 0 → +49
    $to = preg_replace('/[\s\-\(\)]/', '', $telefon);
    if (str_starts_with($to, '00')) {
        $to = '+' . substr($to, 2);
    } elseif (str_starts_with($to, '0') && !str_starts_with($to, '+')) {
        $to = '+49' . substr($to, 1);
    }
    // Nur Ziffern und führendes + behalten
    $to = preg_replace('/[^\d+]/', '', $to);

    // Template-Nachricht: Variablen {{1}} = Vorname, {{2}} = URL
    $payload = json_encode([
        'messaging_product' => 'whatsapp',
        'to'                => $to,
        'type'              => 'template',
        'template'          => [
            'name'     => WA_TEMPLATE_NAME,
            'language' => ['code' => WA_TEMPLATE_LANG],
            'components' => [
                [
                    'type'       => 'body',
                    'parameters' => [
                        ['type' => 'text', 'text' => $session['vorname'] ?? ''],
                        ['type' => 'text', 'text' => $url],
                    ],
                ],
            ],
        ],
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    $apiUrl = 'https://graph.facebook.com/v21.0/' . WA_PHONE_NUMBER_ID . '/messages';

    $ch = curl_init($apiUrl);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => [
            'Authorization: Bearer ' . WA_ACCESS_TOKEN,
            'Content-Type: application/json',
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
    ]);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlErr  = curl_error($ch);
    curl_close($ch);

    if ($curlErr !== '') {
        return ['ok' => false, 'error' => 'cURL-Fehler: ' . $curlErr];
    }

    $result = json_decode((string)$response, true);

    if ($httpCode >= 400) {
        $errMsg = $result['error']['message'] ?? $response;
        error_log('[finanzierungscheck/send.php] WA-Fehler HTTP ' . $httpCode . ': ' . $errMsg);
        return ['ok' => false, 'error' => 'WhatsApp API Fehler: ' . $errMsg];
    }

    return ['ok' => true, 'message_id' => $result['messages'][0]['id'] ?? null];
}

// ─── E-Mail-Versand (interner Endpoint) ──────────────────────────────────────────
function send_email(array $session, string $url): array
{
    if (EMAIL_ENDPOINT === '') {
        return ['ok' => false, 'error' => 'E-Mail-Endpoint nicht konfiguriert'];
    }

    $email = $session['email'] ?? '';
    if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        return ['ok' => false, 'error' => 'Keine gültige E-Mail-Adresse in der Session'];
    }

    $vorname  = $session['vorname'] ?? '';
    $nachname = $session['nachname'] ?? '';

    $subject  = 'Ihre Baufinanzierung – persönlicher Beratungsassistent';
    $bodyHtml = '<p>Guten Tag ' . htmlspecialchars($vorname) . ' ' . htmlspecialchars($nachname) . ',</p>'
        . '<p>wir haben Ihnen Ihren persönlichen Finanzierungsassistenten vorbereitet. '
        . 'Öffnen Sie einfach den folgenden Link, um den Prozess zu starten:</p>'
        . '<p><a href="' . htmlspecialchars($url) . '">' . htmlspecialchars($url) . '</a></p>'
        . '<p>Der Assistent kennt bereits Ihre Anfrage und führt Sie Schritt für Schritt '
        . 'durch die Vorbereitung Ihres Beratungstermins.</p>'
        . '<p>Mit freundlichen Grüßen<br>Ihr Team von Regionalimmobilien24</p>';

    $payload = json_encode([
        'to'        => $email,
        'subject'   => $subject,
        'body_html' => $bodyHtml,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    $headers = [
        'Content-Type: application/json',
    ];
    if (EMAIL_ENDPOINT_SECRET !== '') {
        $headers[] = 'Authorization: Bearer ' . EMAIL_ENDPOINT_SECRET;
    }

    $ch = curl_init(EMAIL_ENDPOINT);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
    ]);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlErr  = curl_error($ch);
    curl_close($ch);

    if ($curlErr !== '') {
        return ['ok' => false, 'error' => 'cURL-Fehler: ' . $curlErr];
    }
    if ($httpCode >= 400) {
        error_log('[finanzierungscheck/send.php] E-Mail-Fehler HTTP ' . $httpCode . ': ' . $response);
        return ['ok' => false, 'error' => 'E-Mail-Endpoint Fehler (HTTP ' . $httpCode . ')'];
    }

    return ['ok' => true];
}

// ─── Versand ausführen ───────────────────────────────────────────────────────────
$result = $channel === 'whatsapp'
    ? send_whatsapp($session, $url)
    : send_email($session, $url);

// Versand-Zeitstempel in der Session speichern (für Protokollierung)
if ($result['ok']) {
    $session['sent'][] = [
        'channel'   => $channel,
        'sent_at'   => date('c'),
        'url'       => $url,
    ];
    @file_put_contents($sessionFile, json_encode($session, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);
}

if ($result['ok']) {
    echo json_encode(['ok' => true, 'channel' => $channel] + $result, JSON_UNESCAPED_UNICODE);
} else {
    http_response_code(502);
    echo json_encode(['ok' => false, 'channel' => $channel, 'error' => $result['error']], JSON_UNESCAPED_UNICODE);
}
