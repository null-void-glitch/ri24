<?php
/**
 * Pitcom-Hilfsroutinen für den Finanzierungscheck.
 *
 * pitcom_ensure_session_id($sessionFile, &$session): string
 *   Gibt den Pitcom-Session-Token zurück. Ruft bei fehlendem Token oder
 *   fehlenden Endpoint-URLs den Production-Session-Endpoint auf und speichert
 *   die zurückgegebenen Endpoints in der Session-Datei.
 *
 * pitcom_endpoint($session, string $key): array{url:string, bearer:string}
 *   Gibt URL und Bearer für 'add-files' oder 'add-notice' zurück.
 *   Bevorzugt die gespeicherten Pitcom-Endpoints; fällt auf md5(token) zurück.
 */

function pitcom_ensure_session_id(string $sessionFile, array &$session): string
{
    $id        = trim((string)($session['pitcom_session_id'] ?? ''));
    $endpoints = $session['pitcom_endpoints'] ?? [];

    // Wenn Session-Token UND Endpoints vorhanden → kein weiterer API-Call nötig
    if ($id !== '' && !empty($endpoints)) return $id;

    $beraterId = trim((string)($session['berater_id'] ?? ''));
    $caseId    = trim((string)($session['case_id']    ?? ''));

    if ($beraterId === '' || $caseId === '') {
        error_log('[pitcom.php] berater_id oder case_id fehlt — Pitcom-Session nicht möglich');
        return $id;
    }

    // Production Bearer: strtoupper(md5($beraterId . $caseId))
    $sessionBearer = strtoupper(md5($beraterId . $caseId));

    $jsonBody = json_encode([
        'vorname'    => $session['vorname']    ?? '',
        'nachname'   => $session['nachname']   ?? '',
        'email'      => $session['email']      ?? '',
        'telefon'    => $session['telefon']    ?? '',
        'berater_id' => $beraterId,
        'case_id'    => $caseId,
        'expose_url' => $session['expose_url'] ?? '',
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    $ch = curl_init('https://backend.regionalimmobilien24.de/api/finanzierungscheck/session/');
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $jsonBody,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Accept: application/json',
            'User-Agent: Mozilla/5.0 (compatible)',
            'Authorization: Bearer ' . $sessionBearer,
        ],
    ]);
    $body = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);

    if ($err || $code < 200 || $code >= 300) {
        error_log("[pitcom.php] Session-Endpoint Fehler ($code): $err | Body: " . substr((string)$body, 0, 300));
        return $id;
    }

    // Pitcom antwortet manchmal als HTML mit JSON im <pre>-Block
    $data = json_decode($body, true);
    if ($data === null && preg_match('/<pre>\s*(\{.+?\})\s*<\/pre>/s', $body, $m)) {
        $data = json_decode($m[1], true);
    }

    if (!is_array($data) || empty($data['status'])) {
        error_log('[pitcom.php] Pitcom-Session-Response ungültig: ' . substr((string)$body, 0, 300));
        return $id;
    }

    $newId = trim((string)($data['token'] ?? ''));
    if ($newId === '') {
        error_log('[pitcom.php] Kein Token in Pitcom-Antwort: ' . substr((string)$body, 0, 300));
        return $id;
    }

    $session['pitcom_session_id'] = $newId;
    if (!empty($data['endpoints']) && is_array($data['endpoints'])) {
        $session['pitcom_endpoints'] = $data['endpoints'];
    }
    file_put_contents(
        $sessionFile,
        json_encode($session, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES),
        LOCK_EX
    );

    return $newId;
}

/**
 * Gibt URL und Bearer für den angegebenen Pitcom-Endpoint zurück.
 *
 * @param array  $session  Session-Daten (muss 'pitcom_endpoints' enthalten)
 * @param string $key      'add-files' oder 'add-notice'
 * @return array{url:string, bearer:string}
 */
function pitcom_endpoint(array $session, string $key): array
{
    $ep = ($session['pitcom_endpoints'] ?? [])[$key] ?? [];

    if (!empty($ep['url']) && !empty($ep['bearer'])) {
        return ['url' => (string)$ep['url'], 'bearer' => (string)$ep['bearer']];
    }

    // Fallback: URL + Bearer aus pitcom_session_id berechnen (Test-Endpoint-Verhalten)
    $sessionId = (string)($session['pitcom_session_id'] ?? '');
    $base      = defined('PITCOM_API_BASE')
        ? PITCOM_API_BASE
        : 'https://backend.regionalimmobilien24.de/api/finanzierungscheck';

    $paths = [
        'add-files'   => '/add/files/',
        'add-notice'  => '/add/chatverlauf/',
        'update-case' => '/update/case/',
    ];
    $path = $paths[$key] ?? '/add/' . $key . '/';

    return [
        'url'    => $base . $path . rawurlencode($sessionId) . '.json',
        'bearer' => strtoupper(md5($sessionId)),
    ];
}
