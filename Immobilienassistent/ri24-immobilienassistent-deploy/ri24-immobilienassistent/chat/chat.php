<?php
/**
 * DeepChat-Proxy für den RI24-Immobilienassistenten.
 *
 * Aufgabe:
 *   - Kapselt den OpenAI-API-Key (liegt NIE im Frontend/DeepChat).
 *   - Ruft die OpenAI **Responses API** im Streaming-Modus auf.
 *   - Bindet den bestehenden MCP-Server als Remote-MCP-Tool ein.
 *   - Hält den Konversationsverlauf über `previous_response_id`
 *     (serverseitig in der PHP-Session, pro conversation_id).
 *   - Injiziert die aktuelle Exposé-URL in die Instructions.
 *   - Reicht den SSE-Stream im von DeepChat erwarteten Format weiter.
 *
 * Erwarteter Request-Body (JSON, von DeepChat + requestInterceptor):
 *   {
 *     "messages":        [{ "role": "user", "text": "..." }, ...],
 *     "expose_url":      "https://www.regionalimmobilien24.de/immobilien/expose/?id=...",
 *     "conversation_id": "<clientseitig erzeugte UUID pro Chat-Instanz>"
 *   }
 *
 * Antwort: text/event-stream mit `data: {"text":"<delta>"}` Chunks.
 */

require __DIR__ . '/config.php';

// ─── CORS (nur relevant, wenn Endpoint auf anderer Origin liegt, z.B. Dev) ──────
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

// ─── Kleiner Helfer: eine SSE-Nachricht an DeepChat senden ──────────────────────
function sse_send(array $payload): void
{
    echo 'data: ' . json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n\n";
    if (function_exists('ob_get_level')) {
        while (ob_get_level() > 0) {
            @ob_end_flush();
        }
    }
    @flush();
}

// ─── SSE-Header setzen ──────────────────────────────────────────────────────────
header('Content-Type: text/event-stream; charset=utf-8');
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Connection: keep-alive');
header('X-Accel-Buffering: no'); // nginx: Buffering für diesen Response abschalten
@ini_set('zlib.output_compression', '0');
@ini_set('output_buffering', 'off');
@ini_set('implicit_flush', '1');
set_time_limit(0);
ignore_user_abort(false);

// ─── Konfiguration prüfen ───────────────────────────────────────────────────────
if (OPENAI_API_KEY === '' || MCP_SERVER_URL === '') {
    sse_send(['text' => '⚠️ Der Assistent ist momentan nicht konfiguriert. Bitte kontaktiere uns direkt.']);
    error_log('[chat.php] Fehlende Konfiguration: OPENAI_API_KEY oder MCP_SERVER_URL nicht gesetzt.');
    exit;
}

// ─── Request-Body lesen ─────────────────────────────────────────────────────────
$raw  = file_get_contents('php://input');
$body = json_decode($raw, true);
if (!is_array($body)) {
    sse_send(['text' => 'Ungültige Anfrage.']);
    exit;
}

$messages      = $body['messages'] ?? [];
$exposeUrl     = trim((string)($body['expose_url'] ?? ''));
$conversationId = preg_replace('/[^A-Za-z0-9_\-]/', '', (string)($body['conversation_id'] ?? ''));

// Letzte Nutzernachricht extrahieren (DeepChat schickt den Verlauf; da wir
// previous_response_id nutzen, brauchen wir nur die neue Nachricht).
$userText = '';
for ($i = count($messages) - 1; $i >= 0; $i--) {
    $m = $messages[$i];
    if (($m['role'] ?? '') === 'user' && isset($m['text'])) {
        $userText = (string)$m['text'];
        break;
    }
}
if ($userText === '') {
    sse_send(['text' => 'Bitte gib eine Nachricht ein.']);
    exit;
}

// ─── Verlauf: previous_response_id aus serverseitigem Store holen ───────────────
// Gespeichert wird pro conversation_id (die der Client bei JEDEM Request mitsendet)
// in einer Datei – bewusst NICHT über die PHP-Session/Cookie. Grund: Bei
// cross-origin-Einbindung (lokaler Prototyp per file://, andere (Sub-)Domain,
// Cookie-Blocking im Browser) wird die PHPSESSID nicht mitgeschickt; die
// Konversation würde sonst jeden Turn ihr Gedächtnis verlieren. Für horizontale
// Skalierung in Produktion diesen Store durch Redis o.ä. ersetzen.
$convKey   = $conversationId !== '' ? $conversationId : 'default';
$storeDir  = sys_get_temp_dir() . '/ri24-chat-sessions';
@mkdir($storeDir, 0700, true);
$storeFile = $storeDir . '/' . md5($convKey) . '.json';

$state = is_file($storeFile)
    ? (json_decode((string)file_get_contents($storeFile), true) ?: [])
    : [];
$previousResponseId = $state['response_id'] ?? null;

// Wechselt die Exposé-URL innerhalb derselben conversation_id, starten wir eine
// frische Konversation (kein Kontext-Bleed zwischen verschiedenen Objekten).
if ($exposeUrl !== '' && ($state['expose_url'] ?? null) !== $exposeUrl) {
    $previousResponseId  = null;
    $state['response_id'] = null;
    $state['expose_url']  = $exposeUrl;
    @file_put_contents($storeFile, json_encode($state), LOCK_EX);
}

// ─── Instructions (System-Prompt) laden + Exposé-URL injizieren ─────────────────
$instructions = '';
if (is_file(INSTRUCTIONS_FILE)) {
    $file = file_get_contents(INSTRUCTIONS_FILE);
    // Markdown-Präambel bis zur ersten horizontalen Linie (---) entfernen.
    $parts = preg_split('/^\s*---\s*$/m', $file, 2);
    $instructions = trim($parts[1] ?? $file);
}
if ($exposeUrl !== '') {
    $instructions .= "\n\n---\nAKTUELLE EXPOSÉ-URL (vom System übergeben): " . $exposeUrl
        . "\nBeziehe dich ausschließlich auf dieses Exposé. Falls die strukturierten Objektdaten "
        . "noch nicht geladen wurden, rufe zuerst `getExposeData` mit genau dieser URL auf.";
}

// ─── Payload für die Responses API bauen ────────────────────────────────────────
$payload = [
    'model'        => OPENAI_MODEL,
    'instructions' => $instructions,
    'input'        => $userText,
    'stream'       => true,
    'store'        => true, // nötig, damit previous_response_id funktioniert
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
if ($previousResponseId) {
    $payload['previous_response_id'] = $previousResponseId;
}

// ─── OpenAI-Streaming per cURL, Chunks nach DeepChat durchreichen ───────────────
$sseBuffer = '';
$newResponseId = null;
$gotAnyText = false;

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

        // Vollständige Zeilen verarbeiten, unvollständigen Rest im Buffer belassen.
        while (($nl = strpos($sseBuffer, "\n")) !== false) {
            $line = rtrim(substr($sseBuffer, 0, $nl), "\r");
            $sseBuffer = substr($sseBuffer, $nl + 1);

            if (strncmp($line, 'data:', 5) !== 0) {
                continue; // "event:"-Zeilen etc. ignorieren
            }
            $data = trim(substr($line, 5));
            if ($data === '' || $data === '[DONE]') {
                continue;
            }
            $event = json_decode($data, true);
            if (!is_array($event) || !isset($event['type'])) {
                continue;
            }

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
                    $msg = $event['response']['error']['message']
                        ?? $event['message']
                        ?? 'Unbekannter Fehler.';
                    error_log('[chat.php] OpenAI-Fehler: ' . $msg);
                    sse_send(['text' => "\n\n⚠️ Es ist ein Fehler aufgetreten. Bitte versuche es erneut."]);
                    break;
            }
        }
        return strlen($chunk);
    },
]);

$ok = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlErr  = curl_error($ch);
curl_close($ch);

// ─── Neue response_id für den nächsten Turn merken ──────────────────────────────
if ($newResponseId) {
    $state['response_id'] = $newResponseId;
    if ($exposeUrl !== '') { $state['expose_url'] = $exposeUrl; }
    @file_put_contents($storeFile, json_encode($state), LOCK_EX);
}

// ─── Fehlerbehandlung, falls gar nichts kam ─────────────────────────────────────
if (!$gotAnyText && ($httpCode >= 400 || $ok === false)) {
    error_log("[chat.php] Request fehlgeschlagen (HTTP $httpCode): $curlErr");
    sse_send(['text' => 'Der Assistent ist momentan nicht erreichbar. Bitte versuche es später erneut.']);
}

// Stream sauber beenden (DeepChat erkennt das Ende am Verbindungsschluss).
echo "data: [DONE]\n\n";
@flush();
