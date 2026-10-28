<?php
/**
 * Live-Abruf der Finanzierungsberater-Kontaktdaten über den MCP-Server.
 *
 * Hintergrund: `getExposeData` (MCP `scrapeExpose()`) liest den Berater-Block
 * bereits aus der Exposé-Seite, ABER der MCP-Server ruft die Seite dafür per
 * serverseitigem HTTP-Request ohne die Session/Cookies des Nutzers ab. Ist der
 * Nutzer sitzungsübergreifend einem bestimmten Finanzierungsberater zugewiesen
 * (Konsistenz über die Webseite hinweg), kann der so ermittelte Berater vom
 * tatsächlich im Browser des Nutzers angezeigten abweichen.
 *
 * `berater_url` (siehe embed-snippet.html: gelesen aus dem `href` von
 * `a.baufi-berater-label` im DOM der Exposé-Seite, also demselben Element, das
 * der Nutzer selbst sieht) macht diesen Live-Abruf hier explizit und deckungs-
 * gleich mit der Anzeige — analog zu `chat-baufinanzierung/advisor-resolver.php`,
 * das denselben MCP-Endpoint (`GET /gpt/berater?url=...`) für den eigenständigen
 * Baufinanzierungs-Assistenten nutzt.
 */

/**
 * @return array{name:string, title:string, phone:string, mobile:string, email:string, calendly:string, photo:string, team_id:string}|null
 */
function fetch_berater_from_mcp(string $pageUrl): ?array
{
    if (!defined('MCP_SERVER_URL') || MCP_SERVER_URL === '') {
        return null;
    }
    // MCP_SERVER_URL zeigt auf den SSE-Endpoint (".../mcp/sse"); der einfache
    // JSON-Scrape-Endpoint liegt auf demselben Host unter "/gpt/berater".
    $base = preg_replace('#/mcp/sse/?$#', '', MCP_SERVER_URL);
    $endpoint = rtrim((string)$base, '/') . '/gpt/berater?' . http_build_query(['url' => $pageUrl]);

    $ch = curl_init($endpoint);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
        CURLOPT_HTTPHEADER     => ['Accept: application/json'],
    ]);
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlErr  = curl_error($ch);
    curl_close($ch);

    if ($response === false || $httpCode >= 400) {
        error_log("[berater-fetch] /gpt/berater fehlgeschlagen (HTTP $httpCode, $curlErr) für: $pageUrl");
        return null;
    }
    $data = json_decode($response, true);
    if (!is_array($data) || empty($data['name'])) {
        error_log("[berater-fetch] /gpt/berater lieferte keine verwertbaren Daten für: $pageUrl");
        return null;
    }

    return [
        'name'     => $data['name'],
        'title'    => $data['title'] ?: 'Finanzierungsspezialist',
        'phone'    => $data['phone'] ?? '',
        'mobile'   => $data['mobile'] ?? '',
        'email'    => $data['email'] ?? '',
        'calendly' => $data['calendly'] ?? '',
        'photo'    => $data['photo'] ?? '',
        'team_id'  => $data['teamId'] ?? '',
    ];
}
