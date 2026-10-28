<?php
/**
 * DeepChat-Proxy für den eigenständigen RI24-Baufinanzierungs-Assistenten.
 *
 * Unterschied zum Exposé-Chat (chat/chat.php): Es gibt KEINEN Objektbezug —
 * kein expose_url, kein getExposeData. Der Nutzer gibt Kaufpreis/PLZ/Objektart
 * direkt im Gespräch an; die Optimierung läuft über createVorschlaege/getVorschlaege
 * auf demselben MCP-Server.
 *
 * Aufgabe:
 *   - Kapselt den OpenAI-API-Key (liegt NIE im Frontend/DeepChat).
 *   - Ruft die OpenAI **Responses API** im Streaming-Modus auf.
 *   - Bindet den bestehenden MCP-Server als Remote-MCP-Tool ein.
 *   - Hält den Konversationsverlauf über `previous_response_id`
 *     (serverseitig, pro conversation_id in einer Datei).
 *   - Reicht den SSE-Stream im von DeepChat erwarteten Format weiter.
 *
 * Erwarteter Request-Body (JSON, von DeepChat + requestInterceptor):
 *   {
 *     "messages":        [{ "role": "user", "text": "..." }, ...],
 *     "conversation_id": "<clientseitig erzeugte UUID pro Chat-Instanz>",
 *     "berater_url":     "<URL der Berater-Seite, auf der das Widget eingebettet ist>",
 *     "berater_id":      "<optional: Dummy-Fallback-ID, siehe advisor-resolver.php>"
 *   }
 *
 * `berater_url`/`berater_id` ersetzen den früher statisch im System-Prompt
 * hinterlegten Finanzierungsberater-Platzhalter (siehe
 * system-prompt-baufinanzierung.md, Abschnitt 6): Statt eines fest
 * eincodierten Namens erhält das Modell die tatsächlichen Kontaktdaten des
 * Beraters, auf dessen Seite das Widget läuft (live gescraped über
 * advisor-resolver.php → MCP `/gpt/berater`), als zusätzlichen
 * Instructions-Block — analog dazu, wie chat/chat.php dem Exposé-Chat die
 * `expose_url` mitgibt.
 *
 * Antwort: text/event-stream mit `data: {"text":"<delta>"}` Chunks.
 */

require __DIR__ . '/config.php';
require __DIR__ . '/advisor-resolver.php';

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

// ─── Rechner-Panel (Demo): Tool-Call-Argumente/-Ergebnisse für den Client aufbereiten ───
// Wird nur von 'response.output_item.done' (mcp_call) weiter unten genutzt. Rein additiv –
// ändert nichts am bestehenden Text-Stream, siehe chat-baufinanzierung/index.html.
function extract_calc_input(array $args): array
{
    $out = [];
    if (isset($args['kaufpreis'])) {
        $out['kaufpreis'] = number_format((float)$args['kaufpreis'], 0, ',', '.') . ' €';
    }
    if (isset($args['eigenKapital'])) {
        $out['eigenKapital'] = number_format((float)$args['eigenKapital'], 0, ',', '.') . ' €';
    }
    if (isset($args['plz'])) {
        $out['plz'] = (string)$args['plz'];
    }
    if (isset($args['objektArt'])) {
        $out['objektArt'] = (string)$args['objektArt'];
    }
    if (isset($args['wunschRate'])) {
        $out['wunschRate'] = number_format((float)$args['wunschRate'], 0, ',', '.') . ' €';
    }
    if (isset($args['wunschZinsbindung'])) {
        $out['wunschZinsbindung'] = (string)$args['wunschZinsbindung'] . ' Jahre';
    }
    return $out;
}

function extract_first_vorschlag(string $output): ?array
{
    // Defensiv: falls der MCP-Output doch als JSON-Content-Array ankommt statt als
    // reiner Klartext, die 'text'-Teile zusammensetzen.
    $text = $output;
    $decoded = json_decode($output, true);
    if (is_array($decoded)) {
        $parts = [];
        foreach ($decoded as $part) {
            if (is_array($part) && isset($part['text'])) {
                $parts[] = (string)$part['text'];
            }
        }
        if ($parts !== []) {
            $text = implode("\n", $parts);
        }
    }

    // Ersten "### Vorschlag ..."-Block bis zum nächsten "###" oder Textende isolieren.
    if (!preg_match('/###\s*Vorschlag.*?(?=\n###|\z)/su', $text, $blockMatch)) {
        return null;
    }
    $block = $blockMatch[0];

    $field = static function (string $label) use ($block): ?string {
        if (preg_match('/\*\*' . preg_quote($label, '/') . '\*\*:\s*(.+)/u', $block, $m)) {
            return trim($m[1]);
        }
        return null;
    };

    $result = array_filter([
        'darlehenssumme' => $field('Darlehenssumme'),
        'rate'           => $field('Monatliche Rate'),
        'sollzins'       => $field('Sollzins'),
        'effektivzins'   => $field('Effektivzins'),
        'zinsbindung'    => $field('Zinsbindung'),
        'machbarkeit'    => $field('Machbarkeit'),
    ], static fn ($v) => $v !== null);

    return $result !== [] ? $result : null;
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
    error_log('[chat-baufinanzierung/chat.php] Fehlende Konfiguration: OPENAI_API_KEY oder MCP_SERVER_URL nicht gesetzt.');
    exit;
}

// ─── Request-Body lesen ─────────────────────────────────────────────────────────
$raw  = file_get_contents('php://input');
$body = json_decode($raw, true);
if (!is_array($body)) {
    sse_send(['text' => 'Ungültige Anfrage.']);
    exit;
}

$messages        = $body['messages'] ?? [];
$conversationId  = preg_replace('/[^A-Za-z0-9_\-]/', '', (string)($body['conversation_id'] ?? ''));
$beraterIdInput  = trim((string)($body['berater_id'] ?? ''));
$beraterUrlInput = trim((string)($body['berater_url'] ?? ''));

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
// in einer Datei – bewusst NICHT über die PHP-Session/Cookie (cross-origin/Cookie-
// Blocking siehe chat/chat.php). Eigener Store-Ordner, damit die Sessions des
// Baufinanzierungs-Assistenten nicht mit denen des Exposé-Chats vermischt werden.
$convKey   = $conversationId !== '' ? $conversationId : 'default';
$storeDir  = sys_get_temp_dir() . '/ri24-chat-baufi-sessions';
@mkdir($storeDir, 0700, true);
$storeFile = $storeDir . '/' . md5($convKey) . '.json';

$state = is_file($storeFile)
    ? (json_decode((string)file_get_contents($storeFile), true) ?: [])
    : [];
$previousResponseId = $state['response_id'] ?? null;

// ─── Instructions (System-Prompt) laden ─────────────────────────────────────────
$instructions = '';
if (is_file(INSTRUCTIONS_FILE)) {
    $file = file_get_contents(INSTRUCTIONS_FILE);
    // Markdown-Präambel bis zur ersten horizontalen Linie (---) entfernen.
    $parts = preg_split('/^\s*---\s*$/m', $file, 2);
    $instructions = trim($parts[1] ?? $file);
}

// ─── Finanzierungsberater auflösen + in die Instructions einspeisen ─────────────
// Ersetzt den früheren Platzhalter in Abschnitt 6 des System-Prompts: Statt eines
// fest eincodierten Namens bekommt das Modell die echten Kontaktdaten des Beraters,
// auf dessen Seite das Widget eingebettet ist (live über berater_url gescraped;
// berater_id ist nur der Dummy-Fallback, siehe advisor-resolver.php).
$advisor = resolve_advisor(
    $beraterIdInput !== '' ? $beraterIdInput : null,
    null,
    $beraterUrlInput !== '' ? $beraterUrlInput : null
);
if ($advisor !== null) {
    $instructions .= "\n\n---\nZUSTÄNDIGER FINANZIERUNGSBERATER (vom System übergeben, für Abschnitt 6 verwenden):\n"
        . "Name: " . $advisor['name'] . "\n"
        . "Telefon: " . $advisor['phone'] . "\n"
        . (!empty($advisor['mobile']) ? "Mobil: " . $advisor['mobile'] . "\n" : "")
        . "E-Mail: " . $advisor['email'] . "\n"
        . "Calendly-Buchungslink: " . $advisor['calendly'] . "\n"
        . "Verwende ausschließlich diese Kontaktdaten, wenn du in Abschnitt 6 auf den "
        . "Finanzierungsberater verweist. Erfinde niemals andere Namen oder Kontaktdaten.";
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
if (defined('FILE_SEARCH_VECTOR_STORE_ID') && FILE_SEARCH_VECTOR_STORE_ID !== '') {
    $payload['tools'][] = [
        'type'             => 'file_search',
        'vector_store_ids' => [FILE_SEARCH_VECTOR_STORE_ID],
    ];
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
                    error_log('[chat-baufinanzierung/chat.php] OpenAI-Fehler: ' . $msg);
                    sse_send(['text' => "\n\n⚠️ Es ist ein Fehler aufgetreten. Bitte versuche es erneut."]);
                    break;

                // ── Rechner-Panel (Demo): Argumente/Ergebnisse von createVorschlaege/
                // getVorschlaege zusätzlich zum Text als eigenes Event ausliefern, damit
                // die Demo-Seite ein Live-Rechner-Panel füllen kann (siehe index.html).
                case 'response.output_item.done':
                    $item = $event['item'] ?? null;
                    if (is_array($item) && ($item['type'] ?? '') === 'mcp_call' && empty($item['error'])) {
                        $toolName = $item['name'] ?? '';
                        if ($toolName === 'createVorschlaege') {
                            $args = json_decode((string)($item['arguments'] ?? ''), true);
                            if (is_array($args)) {
                                sse_send(['calc_input' => extract_calc_input($args)]);
                            }
                        } elseif ($toolName === 'getVorschlaege') {
                            $result = extract_first_vorschlag((string)($item['output'] ?? ''));
                            if ($result !== null) {
                                sse_send(['calc_result' => $result]);
                            }
                        }
                    }
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
    @file_put_contents($storeFile, json_encode($state), LOCK_EX);
}

// ─── Fehlerbehandlung, falls gar nichts kam ─────────────────────────────────────
if (!$gotAnyText && ($httpCode >= 400 || $ok === false)) {
    error_log("[chat-baufinanzierung/chat.php] Request fehlgeschlagen (HTTP $httpCode): $curlErr");
    sse_send(['text' => 'Der Assistent ist momentan nicht erreichbar. Bitte versuche es später erneut.']);
}

// Stream sauber beenden (DeepChat erkennt das Ende am Verbindungsschluss).
echo "data: [DONE]\n\n";
@flush();
