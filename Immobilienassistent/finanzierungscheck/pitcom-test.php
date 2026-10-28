<?php
/**
 * Proxy für den Pitcom-Testendpunkt.
 * Wird von demo.html aufgerufen — umgeht Browser-CORS-Beschränkungen.
 *
 * GET  → ruft session/test.php auf Pitcom auf, gibt JSON zurück
 * POST → ruft add/chatverlauf/test.php auf (Notiz-Test), body = plain text
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

$action = $_GET['action'] ?? 'session';

if ($action === 'session') {
    // Pitcom-Testformular benötigt POST mit: vorname, nachname, email, telefon, berater_id, case_id
    $raw  = file_get_contents('php://input');
    $req  = json_decode($raw, true) ?: [];

    $postFields = http_build_query([
        'vorname'    => $req['vorname']    ?? 'Max',
        'nachname'   => $req['nachname']   ?? 'Mustermann',
        'email'      => $req['email']      ?? 'max@example.com',
        'telefon'    => $req['telefon']    ?? '+491761234567',
        'berater_id' => $req['berater_id'] ?? '',
        'case_id'    => $req['case_id']    ?? '',
    ]);

    $ch = curl_init('https://backend.regionalimmobilien24.de/api/finanzierungscheck/session/test.php');
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $postFields,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_HTTPHEADER     => ['Accept: application/json', 'User-Agent: Mozilla/5.0 (compatible)'],
    ]);
    $body = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);

    if ($err || $code < 200 || $code >= 300) {
        http_response_code(502);
        echo json_encode(['error' => "Pitcom nicht erreichbar ($code): $err", 'response' => $body]);
        exit;
    }

    // Pitcom antwortet manchmal HTML mit JSON im <pre>-Block — extrahieren
    $json = json_decode($body, true);
    if ($json !== null) {
        echo $body;
    } elseif (preg_match('/<pre>\s*(\{.+?\})\s*<\/pre>/s', $body, $m)) {
        $inner = json_decode($m[1], true);
        if ($inner !== null) {
            echo json_encode($inner);
        } else {
            echo json_encode(['raw_response' => $body, 'http_code' => $code]);
        }
    } else {
        echo json_encode(['raw_response' => $body, 'http_code' => $code]);
    }
    exit;
}

if ($action === 'notice') {
    $pitcomSessionId = trim($_GET['session_id'] ?? '');
    if ($pitcomSessionId === '') {
        http_response_code(400);
        echo json_encode(['error' => 'session_id fehlt']);
        exit;
    }
    $text   = file_get_contents('php://input') ?: 'Test-Notiz vom Demo-Panel — ' . date('Y-m-d H:i:s');
    $url    = 'https://backend.regionalimmobilien24.de/api/finanzierungscheck/add/chatverlauf/' . rawurlencode($pitcomSessionId) . '.json';
    $bearer = strtoupper(md5($pitcomSessionId));

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $text,
        CURLOPT_HTTPHEADER     => ['Authorization: Bearer ' . $bearer, 'Content-Type: text/plain'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
    ]);
    $body = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);

    $responseJson = json_decode($body, true);
    if ($responseJson === null && preg_match('/<pre>\s*(\{.+?\})\s*<\/pre>/s', $body, $m)) {
        $responseJson = json_decode($m[1], true);
    }

    echo json_encode([
        'ok'       => $code >= 200 && $code < 300,
        'http_code'=> $code,
        'response' => $responseJson ?? $body,
        'error'    => $err ?: null,
    ]);
    exit;
}

http_response_code(400);
echo json_encode(['error' => 'Unbekannte action']);
