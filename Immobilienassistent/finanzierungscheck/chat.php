<?php
/**
 * DeepChat-Proxy für den personalisierten Finanzierungscheck-Chatbot.
 *
 * Analog zu chat-baufinanzierung/chat.php, aber:
 * - Lädt die Session-Daten anhand des im Request mitgeschickten Tokens.
 * - Injiziert Kundendaten + Berater- und Finanzierer-Info in die Instructions.
 * - Nutzt den Finanzierungscheck-System-Prompt (system-prompt-finanzierungscheck.md).
 *
 * Erwarteter Request-Body (JSON):
 * {
 *   "messages":        [{ "role": "user", "text": "..." }, ...],
 *   "conversation_id": "<clientseitige UUID>",
 *   "session_token":   "<Token aus der URL>",
 *   "berater_url":     "<optional — Fallback-URL für Berater-Lookup>"
 * }
 */

require __DIR__ . '/config.php';
require __DIR__ . '/../chat-baufinanzierung/advisor-resolver.php';

// ─── CORS ────────────────────────────────────────────────────────────────────────
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '') {
    $allowed = array_map('trim', explode(',', ALLOWED_ORIGINS));
    if (in_array('*', $allowed, true) || in_array($origin, $allowed, true)) {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Vary: Origin');
        header('Access-Control-Allow-Methods: POST, OPTIONS');
        header('Access-Control-Allow-Headers: Content-Type');
        header('Access-Control-Allow-Credentials: true');
    }
}
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

function sse_send(array $payload): void
{
    echo 'data: ' . json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n\n";
    while (ob_get_level() > 0) {
        @ob_end_flush();
    }
    @flush();
}

// ─── SSE-Header ──────────────────────────────────────────────────────────────────
header('Content-Type: text/event-stream; charset=utf-8');
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Connection: keep-alive');
header('X-Accel-Buffering: no');
@ini_set('zlib.output_compression', '0');
@ini_set('output_buffering', 'off');
@ini_set('implicit_flush', '1');
set_time_limit(0);
ignore_user_abort(false);

// ─── Konfiguration prüfen ────────────────────────────────────────────────────────
if (OPENAI_API_KEY === '' || MCP_SERVER_URL === '') {
    sse_send(['text' => '⚠️ Der Assistent ist momentan nicht konfiguriert.']);
    error_log('[finanzierungscheck/chat.php] Fehlende Konfiguration');
    exit;
}

// ─── Request lesen ───────────────────────────────────────────────────────────────
$raw  = file_get_contents('php://input');
$body = json_decode($raw, true);
if (!is_array($body)) {
    sse_send(['text' => 'Ungültige Anfrage.']);
    exit;
}

$messages       = $body['messages'] ?? [];
$conversationId = preg_replace('/[^A-Za-z0-9_\-]/', '', (string)($body['conversation_id'] ?? ''));
$sessionToken   = preg_replace('/[^A-Za-z0-9]/', '', (string)($body['session_token'] ?? ''));
$beraterUrlFallback = trim((string)($body['berater_url'] ?? ''));

// Letzte Nutzernachricht
$userText = '';
for ($i = count($messages) - 1; $i >= 0; $i--) {
    $m = $messages[$i];
    if (($m['role'] ?? '') === 'user' && isset($m['text'])) {
        $userText = trim((string)$m['text']);
        break;
    }
}
if ($userText === '') {
    sse_send(['text' => 'Bitte gib eine Nachricht ein.']);
    exit;
}

// ─── Session laden ───────────────────────────────────────────────────────────────
$session = [];
if ($sessionToken !== '') {
    $sessionFile = SESSIONS_DIR . '/' . $sessionToken . '.json';
    if (is_file($sessionFile)) {
        $session = json_decode((string)file_get_contents($sessionFile), true) ?: [];
    }
}

// ─── Gesprächsverlauf (previous_response_id) ─────────────────────────────────────
$convKey   = $conversationId !== '' ? $conversationId : ($sessionToken ?: 'default');
$storeDir  = sys_get_temp_dir() . '/ri24-finanzcheck-sessions';
@mkdir($storeDir, 0700, true);
$storeFile = $storeDir . '/' . md5($convKey) . '.json';

$state              = is_file($storeFile) ? (json_decode((string)file_get_contents($storeFile), true) ?: []) : [];
$previousResponseId = $state['response_id'] ?? null;

// ─── System-Prompt laden ─────────────────────────────────────────────────────────
$instructions = '';
if (is_file(INSTRUCTIONS_FILE)) {
    $file  = file_get_contents(INSTRUCTIONS_FILE);
    $parts = preg_split('/^\s*---\s*$/m', $file, 2);
    $instructions = trim($parts[1] ?? $file);
}

// ─── Kundendaten in Instructions injizieren ───────────────────────────────────────
$vorname  = $session['vorname']  ?? '';
$nachname = $session['nachname'] ?? '';
$exposeUrl = trim((string)($session['expose_url'] ?? ''));

$kundenBlock = "\n\n---\nKUNDENDATEN (vom System übergeben — diese Daten sind bekannt und müssen NICHT erneut abgefragt werden):\n"
    . "Name: " . $vorname . " " . $nachname . "\n"
    . "E-Mail: " . ($session['email'] ?? '') . "\n"
    . "Telefon: " . ($session['telefon'] ?? '') . "\n"
    . "session_token: " . $sessionToken . "\n"
    . "case_id: " . ($session['case_id'] ?? '') . "\n";

if ($exposeUrl !== '') {
    $kundenBlock .= "\nEXPOSÉ-URL (vorhanden — rufe getExposeData mit dieser URL auf, um Kaufpreis, PLZ und Objektart zu laden):\n"
        . $exposeUrl . "\n";
} else {
    $kundenBlock .= "\nKEINE Exposé-URL bekannt — Schritt 2 (Objektsituation) mit dem Kunden durchgehen.\n";
}

if (is_array($session['finanzierer'] ?? null)) {
    $fi = $session['finanzierer'];
    $kundenBlock .= "\nZUGEWIESENER FINANZIERER (vom System übergeben):\n";
    if (!empty($fi['name'])) $kundenBlock .= "Name: " . $fi['name'] . "\n";
    if (!empty($fi['id']))   $kundenBlock .= "Europace-ID: " . $fi['id'] . "\n";
}

$instructions .= $kundenBlock;

// ─── Berater auflösen ─────────────────────────────────────────────────────────────
$beraterId  = $session['berater_id']  ?? '';
$beraterUrl = $session['berater_url'] ?? $beraterUrlFallback;

$advisor = resolve_advisor(
    $beraterId  !== '' ? $beraterId  : null,
    null,
    $beraterUrl !== '' ? $beraterUrl : null
);
if ($advisor !== null) {
    $instructions .= "\n\n---\nBERATER (vom System übergeben — Kontaktdaten für Schritt 6 verwenden):\n"
        . "Name: " . $advisor['name'] . "\n"
        . "Telefon: " . $advisor['phone'] . "\n"
        . (!empty($advisor['mobile']) ? "Mobil: " . $advisor['mobile'] . "\n" : "")
        . "E-Mail: " . $advisor['email'] . "\n"
        . "Calendly-Buchungslink: " . $advisor['calendly'] . "\n"
        . "Verwende ausschließlich diese Kontaktdaten. Erfinde niemals andere.";
}

// ─── Payload ─────────────────────────────────────────────────────────────────────
$payload = [
    'model'        => OPENAI_MODEL,
    'instructions' => $instructions,
    'input'        => $userText,
    'stream'       => true,
    'store'        => true,
    'tools'        => [[
        'type'             => 'mcp',
        'server_label'     => MCP_SERVER_LABEL,
        'server_url'       => MCP_SERVER_URL,
        'require_approval' => 'never',
    ]],
];
if (MCP_AUTHORIZATION !== '') {
    $payload['tools'][0]['headers'] = ['Authorization' => MCP_AUTHORIZATION];
}
if (FILE_SEARCH_VECTOR_STORE_ID !== '') {
    $payload['tools'][] = [
        'type'             => 'file_search',
        'vector_store_ids' => [FILE_SEARCH_VECTOR_STORE_ID],
    ];
}
if ($previousResponseId) {
    $payload['previous_response_id'] = $previousResponseId;
}

// ─── Streaming ───────────────────────────────────────────────────────────────────
$sseBuffer     = '';
$newResponseId = null;
$gotAnyText    = false;

$ch = curl_init('https://api.openai.com/v1/responses');
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
    CURLOPT_HTTPHEADER     => [
        'Authorization: Bearer ' . OPENAI_API_KEY,
        'Content-Type: application/json',
        'Accept: text/event-stream',
    ],
    CURLOPT_RETURNTRANSFER => false,
    CURLOPT_WRITEFUNCTION  => function ($ch, $chunk) use (&$sseBuffer, &$newResponseId, &$gotAnyText) {
        $sseBuffer .= $chunk;
        while (($nl = strpos($sseBuffer, "\n")) !== false) {
            $line      = rtrim(substr($sseBuffer, 0, $nl), "\r");
            $sseBuffer = substr($sseBuffer, $nl + 1);

            if (strncmp($line, 'data:', 5) !== 0) continue;
            $data = trim(substr($line, 5));
            if ($data === '' || $data === '[DONE]') continue;

            $event = json_decode($data, true);
            if (!is_array($event) || !isset($event['type'])) continue;

            switch ($event['type']) {
                case 'response.output_text.delta':
                    if (isset($event['delta']) && $event['delta'] !== '') {
                        $gotAnyText = true;
                        sse_send(['text' => $event['delta']]);
                    }
                    break;

                case 'response.created':
                case 'response.completed':
                    if (isset($event['response']['id'])) {
                        $newResponseId = $event['response']['id'];
                    }
                    break;

                case 'response.failed':
                case 'error':
                    $msg = $event['response']['error']['message'] ?? $event['message'] ?? 'Unbekannter Fehler.';
                    error_log('[finanzierungscheck/chat.php] OpenAI-Fehler: ' . $msg);
                    sse_send(['text' => "\n\n⚠️ Ein Fehler ist aufgetreten. Bitte versuche es erneut."]);
                    break;
            }
        }
        return strlen($chunk);
    },
]);

$ok       = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlErr  = curl_error($ch);
curl_close($ch);

if ($newResponseId) {
    $state['response_id'] = $newResponseId;
    @file_put_contents($storeFile, json_encode($state), LOCK_EX);
}

if (!$gotAnyText && ($httpCode >= 400 || $ok === false)) {
    error_log("[finanzierungscheck/chat.php] Request fehlgeschlagen (HTTP $httpCode): $curlErr");
    sse_send(['text' => 'Der Assistent ist momentan nicht erreichbar. Bitte versuche es später erneut.']);
}

echo "data: [DONE]\n\n";
@flush();
