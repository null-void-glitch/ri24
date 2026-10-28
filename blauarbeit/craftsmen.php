<?php

declare(strict_types=1);

/**
 * Public AJAX endpoint called by handwerker-box.js. Keeps the Blauarbeit
 * client_id/client_secret server-side and proxies GET /v2/partners/users/craftsmen.
 *
 * Results are cached for a few minutes per zipcode/category, since the
 * upstream endpoint is rate limited to 30 requests/minute and craftsmen
 * near a given zipcode don't change from one page view to the next.
 */

header('Content-Type: application/json; charset=utf-8');

require __DIR__ . '/BlauarbeitClient.php';

const CACHE_TTL_SECONDS = 600;

$configFile = __DIR__ . '/blauarbeit-config.php';
if (!is_file($configFile)) {
    http_response_code(500);
    echo json_encode(['code' => 'not_configured', 'message' => 'blauarbeit-config.php is missing. Copy blauarbeit-config.example.php and fill in your credentials.']);
    exit;
}

$zipcode = (string) ($_GET['zipcode'] ?? '');
if (!preg_match('/^\d{5}$/', $zipcode)) {
    http_response_code(422);
    echo json_encode(['code' => 'invalid_zipcode', 'message' => 'zipcode must be exactly 5 digits.']);
    exit;
}

$category = null;
if (isset($_GET['category']) && $_GET['category'] !== '') {
    if (!ctype_digit((string) $_GET['category'])) {
        http_response_code(422);
        echo json_encode(['code' => 'invalid_category', 'message' => 'category must be an integer.']);
        exit;
    }
    $category = (int) $_GET['category'];
}

$cacheKey = 'blauarbeit_craftsmen_' . md5($zipcode . '|' . $category);
$cacheFile = sys_get_temp_dir() . '/' . $cacheKey . '.json';

if (is_file($cacheFile) && (filemtime($cacheFile) + CACHE_TTL_SECONDS) > time()) {
    echo file_get_contents($cacheFile);
    exit;
}

try {
    $config = require $configFile;
    $client = new BlauarbeitClient($config);
    $result = $client->nearbyCraftsmen($zipcode, $category);

    $body = json_encode($result);
    file_put_contents($cacheFile, $body);
    echo $body;
} catch (Throwable $e) {
    error_log('Blauarbeit craftsmen proxy error: ' . $e->getMessage());

    if (is_file($cacheFile)) {
        // Serve stale data rather than nothing if the upstream call failed.
        echo file_get_contents($cacheFile);
        exit;
    }

    http_response_code(502);
    echo json_encode(['code' => 'upstream_error', 'message' => 'Handwerker konnten nicht geladen werden.']);
}
