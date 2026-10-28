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
 *     "conversation_id": "<clientseitig erzeugte UUID pro Chat-Instanz>",
 *     "berater_url":     "<optional: URL des dem Nutzer aktuell angezeigten Finanzierungsberaters>",
 *     "team_id":         "<optional: Team-ID des zuständigen Finanzierungsberater-Teams>"
 *   }
 *
 * `berater_url` (siehe embed-snippet.html) identifiziert den Finanzierungsberater,
 * der dem Nutzer konkret in seiner Sitzung angezeigt wird (aus dem `href` des
 * Berater-Links im Exposé-DOM). Ist der Wert gesetzt, werden dessen Kontaktdaten
 * live über den MCP-Server nachgeladen (siehe berater-fetch.php) und in die
 * Instructions eingespeist — das stellt sicher, dass der Assistent denselben
 * Berater nennt, den der Nutzer auch auf der Seite sieht, selbst wenn der über
 * `getExposeData` serverseitig gescrapte Berater-Block (ohne Nutzer-Session)
 * einen anderen Berater ergeben würde.
 *
 * `team_id` (siehe embed-snippet.html) wird direkt aus dem `data-team-id`-Attribut
 * am Team-Logo/-Foto im selben Berater-Block gelesen (`a.baufi-berater-label
 * [data-team-id]`) und unverändert an das MCP-Tool `submitFinancingInquiry`
 * durchgereicht. Fällt der Live-Fetch des Beraters (`berater_url`) fehl, wird
 * ersatzweise `team_id` aus der Live-Antwort verwendet, falls dort vorhanden.
 *
 * Antwort: text/event-stream mit `data: {"text":"<delta>"}` Chunks.
 */

require __DIR__ . '/config.php';
require __DIR__ . '/berater-fetch.php';

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
$beraterUrlInput = trim((string)($body['berater_url'] ?? ''));
$teamIdInput = preg_replace('/[^0-9]/', '', (string)($body['team_id'] ?? ''));

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

// ─── Finanzierungsberater: dem Nutzer angezeigten Berater live nachladen ────────
// Ersetzt bei Erfolg den ggf. abweichenden Berater aus dem "Finanzierungsberater
// Details"-Abschnitt von getExposeData (siehe Docblock oben) durch den, den der
// Nutzer tatsächlich auf der Seite sieht.
if ($beraterUrlInput !== '') {
    $berater = fetch_berater_from_mcp($beraterUrlInput);
    if ($berater !== null) {
        if ($teamIdInput === '' && !empty($berater['team_id'])) {
            $teamIdInput = $berater['team_id'];
        }
        $instructions .= "\n\n---\nZUSTÄNDIGER FINANZIERUNGSBERATER (vom System übergeben, hat VORRANG vor "
            . "eventuell abweichenden Angaben im Abschnitt \"Finanzierungsberater Details\" aus getExposeData):\n"
            . "Name: " . $berater['name'] . "\n"
            . "Telefon: " . $berater['phone'] . "\n"
            . (!empty($berater['mobile']) ? "Mobil: " . $berater['mobile'] . "\n" : "")
            . "E-Mail: " . $berater['email'] . "\n"
            . (!empty($berater['calendly']) ? "Calendly-Buchungslink: " . $berater['calendly'] . "\n" : "")
            . "Verwende ausschließlich diese Kontaktdaten für den Finanzierungsberater. "
            . "Erfinde niemals andere Namen oder Kontaktdaten.";
    }
}

// team_id (aus dem `data-team-id`-Attribut im Berater-Block des Nutzer-DOMs, siehe
// embed-snippet.html) wird 1:1 an das MCP-Tool `submitFinancingInquiry` durchgereicht.
// Ohne diesen Block müsste das Modell raten oder aus dem Fließtext von getExposeData
// ableiten, was bei falscher/erfundener team_id zu Anfragen beim falschen Team führt.
if ($teamIdInput !== '') {
    $instructions .= "\n\n---\nteam_id (vom System übergeben, für das Tool `submitFinancingInquiry`): " . $teamIdInput
        . "\nVerwende exakt diesen Wert als `team_id`-Parameter, sobald der Nutzer eine Finanzierungsanfrage "
        . "stellt. Frage den Nutzer NIEMALS nach der team_id und erfinde NIEMALS einen eigenen Wert.";
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
