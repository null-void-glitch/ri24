<?php
/**
 * JSON-Endpoint für die Berater-Seite: liefert die Kontaktdaten des
 * Finanzierungsberaters, auf dessen Seite das Widget eingebettet ist (siehe
 * advisor-resolver.php), und setzt dabei ggf. das Sticky-Cookie (nur im
 * Dummy-Fallback relevant).
 *
 * Die Seite ruft diesen Endpoint beim Laden per fetch() auf — mit `url` =
 * der eigenen Seiten-URL (`window.location.href`) — um die
 * Finanzierungsberater-Card zu befüllen, und übernimmt dieselbe URL
 * anschließend als `berater_url` in jeden Chat-Request (analog dazu, wie der
 * Exposé-Chat `expose_url` mitschickt). Primärquelle sind die Live-Daten der
 * Seite selbst (`GET /gpt/berater` auf dem MCP-Server); nur wenn das
 * fehlschlägt (z.B. lokale Testumgebung), greift der Dummy-Fallback aus
 * `advisors.php` inkl. `?berater=`-Parameter.
 *
 * Antwort: { "id": "...", "name": "...", "title": "...", "phone": "...",
 *            "mobile": "...", "email": "...", "calendly": "...",
 *            "avatarInitials": "...", "photo": "..." }
 *            oder 404 mit { "error": "..." }, falls weder Live-Daten noch
 *            Dummy-Berater verfügbar sind. "mobile", "photo" (und im
 *            Dummy-Fallback "rating") sind optional.
 */

require __DIR__ . '/config.php';
require __DIR__ . '/advisor-resolver.php';

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '') {
    $allowed = array_map('trim', explode(',', ALLOWED_ORIGINS));
    if (in_array('*', $allowed, true) || in_array($origin, $allowed, true)) {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Vary: Origin');
        header('Access-Control-Allow-Methods: GET, OPTIONS');
        header('Access-Control-Allow-Credentials: true');
    }
}
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

header('Content-Type: application/json; charset=utf-8');

$advisor = resolve_advisor(
    trim((string)($_GET['berater'] ?? '')) ?: null,
    null,
    trim((string)($_GET['url'] ?? '')) ?: null
);
if ($advisor === null) {
    http_response_code(404);
    echo json_encode(['error' => 'Kein Finanzierungsberater konfiguriert.'], JSON_UNESCAPED_UNICODE);
    exit;
}

echo json_encode($advisor, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
