<?php

declare(strict_types=1);

/**
 * Public AJAX endpoint called by handwerker-box.js to populate the
 * Handwerkerart dropdown. Keeps client_id/client_secret server-side and
 * proxies GET /v2/partners/categories.
 *
 * Categories barely ever change, so the cache TTL is much longer than
 * craftsmen.php's.
 */

header('Content-Type: application/json; charset=utf-8');

require __DIR__ . '/BlauarbeitClient.php';

const CACHE_TTL_SECONDS = 86400;

$configFile = __DIR__ . '/blauarbeit-config.php';
if (!is_file($configFile)) {
    http_response_code(500);
    echo json_encode(['code' => 'not_configured', 'message' => 'blauarbeit-config.php is missing. Copy blauarbeit-config.example.php and fill in your credentials.']);
    exit;
}

$cacheFile = sys_get_temp_dir() . '/blauarbeit_categories.json';

if (is_file($cacheFile) && (filemtime($cacheFile) + CACHE_TTL_SECONDS) > time()) {
    echo file_get_contents($cacheFile);
    exit;
}

try {
    $config = require $configFile;
    $client = new BlauarbeitClient($config);
    $result = $client->categories();

    $body = json_encode($result);
    file_put_contents($cacheFile, $body);
    echo $body;
} catch (Throwable $e) {
    error_log('Blauarbeit categories proxy error: ' . $e->getMessage());

    if (is_file($cacheFile)) {
        echo file_get_contents($cacheFile);
        exit;
    }

    http_response_code(502);
    echo json_encode(['code' => 'upstream_error', 'message' => 'Kategorien konnten nicht geladen werden.']);
}
