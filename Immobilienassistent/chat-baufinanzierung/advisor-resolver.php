<?php
/**
 * Ermittlung des Finanzierungsberaters für das eingebettete Widget.
 *
 * Primärquelle: Das Widget wird auf der PERSÖNLICHEN Berater-Seite eingebettet
 * (z.B. https://www.regionalimmobilien24.de/vogtland/baufinanzierung/
 * philipp-steppohn/) — analog dazu, wie der Exposé-Chat seine Kontaktdaten aus
 * der Exposé-Seite selbst liest. Die aktuelle Seiten-URL wird daher vom
 * Frontend mitgeschickt (`berater_url`, siehe embed-snippet.html) und live über
 * den MCP-Server ausgelesen (`GET /gpt/berater?url=...`, siehe
 * `scrapeBeraterPage()` in `mcp-server/server/src/index.ts`) — dieselbe Seite
 * liefert damit sowohl die Anzeige-Daten (Name, Foto, Kontakt) als auch die
 * Instructions-Grundlage für `chat.php`.
 *
 * Fallback (kein `berater_url` übergeben, oder Live-Scrape schlägt fehl — z.B.
 * lokale Dev-/Testumgebung ohne Netzzugriff auf den MCP-Server): Zuweisung aus
 * der statischen Dummy-Datenbasis `advisors.php`, wie zuvor:
 *   1. Expliziter Parameter `berater` (Kampagnen-/Deep-Link-Fall).
 *   2. Letztes URL-Segment von `berater_url` (z.B. .../baufinanzierung/
 *      philipp-steppohn/ → 'philipp-steppohn') — greift, wenn die URL zwar
 *      klar auf einen Dummy-Berater verweist, der Live-Scrape aber fehlschlägt.
 *   3. Bestehendes Cookie `ri24_baufi_berater` (Session-Stickiness).
 *   4. Zufällige Zuweisung, anschließend im Cookie festgehalten.
 */

// config.php wird i.d.R. bereits vom Aufrufer (chat.php / resolve-advisor.php)
// geladen; nur nachladen, wenn MCP_SERVER_URL noch fehlt (z.B. Standalone-Tests),
// um doppelte define()-Aufrufe aus config.local.php zu vermeiden.
if (!defined('MCP_SERVER_URL')) {
    require __DIR__ . '/config.php';
}
require __DIR__ . '/advisors.php';

const RI24_BAUFI_BERATER_COOKIE = 'ri24_baufi_berater';

/**
 * Liest die Kontaktdaten live von der Berater-Seite über den MCP-Server.
 *
 * @return array{name:string, title:string, phone:string, mobile:string, email:string, calendly:string, avatarInitials:string, photo:string}|null
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
        error_log("[advisor-resolver] /gpt/berater fehlgeschlagen (HTTP $httpCode, $curlErr) für: $pageUrl");
        return null;
    }
    $data = json_decode($response, true);
    if (!is_array($data) || empty($data['name'])) {
        error_log("[advisor-resolver] /gpt/berater lieferte keine verwertbaren Daten für: $pageUrl");
        return null;
    }

    $nameParts = preg_split('/\s+/', trim($data['name'])) ?: [];
    $initials  = strtoupper(mb_substr($nameParts[0] ?? '', 0, 1) . mb_substr(end($nameParts) ?: '', 0, 1));

    return [
        'name'           => $data['name'],
        'title'          => $data['title'] ?: 'Finanzierungsspezialist',
        'phone'          => $data['phone'] ?? '',
        'mobile'         => $data['mobile'] ?? '',
        'email'          => $data['email'] ?? '',
        'calendly'       => $data['calendly'] ?? '',
        'avatarInitials' => $initials,
        'photo'          => $data['photo'] ?? '',
    ];
}

/**
 * @param string|null $requestedId Explizit gewünschte Berater-ID für den Dummy-Fallback
 *        (z.B. aus dem JSON-Body von chat.php). Fällt auf $_GET['berater'] zurück.
 * @param array<string, array<string, string>>|null $advisors Für Tests injizierbar; Default: advisors.php
 * @param string|null $pageUrl URL der Berater-Seite, auf der das Widget eingebettet ist
 *        (Primärquelle, siehe Docblock oben). Fällt auf $_GET['url'] / $_POST['url'] zurück.
 * @return array{id:string, name:string, title:string, phone:string, mobile?:string, email:string, calendly:string, avatarInitials:string, photo?:string}|null
 *         null, wenn weder Live-Daten noch Dummy-Berater verfügbar sind.
 */
function resolve_advisor(?string $requestedId = null, ?array $advisors = null, ?string $pageUrl = null): ?array
{
    // 0. Primärquelle: live von der Berater-Seite selbst lesen.
    $pageUrl ??= trim((string)($_GET['url'] ?? $_POST['url'] ?? ''));
    if ($pageUrl !== '') {
        $live = fetch_berater_from_mcp($pageUrl);
        if ($live !== null) {
            return ['id' => substr(md5($pageUrl), 0, 12)] + $live;
        }
        error_log('[advisor-resolver] Fallback auf Dummy-Zuweisung für: ' . $pageUrl);
    }

    // Fallback: Dummy-Datenbasis (Dev/Testumgebung oder Live-Scrape fehlgeschlagen).
    $advisors ??= require __DIR__ . '/advisors.php';
    if (empty($advisors)) {
        return null;
    }

    $sanitize = static fn($v) => preg_replace('/[^a-z0-9\-]/', '', strtolower((string)$v));

    // 1. Expliziter Parameter: Funktionsargument (chat.php-JSON-Body) oder
    //    GET ?berater=... (Landingpage/Kampagnen-Deep-Link).
    $requested = $sanitize($requestedId ?? $_GET['berater'] ?? '');
    if ($requested !== '' && isset($advisors[$requested])) {
        $id = $requested;
    } else {
        // 2. Letztes Segment der Berater-URL als Slug interpretieren (greift z.B.
        //    in der lokalen Demo, wenn die URL zwar eindeutig auf einen Dummy-
        //    Berater verweist, der Live-Scrape aber mangels Netzzugriff fehlschlägt).
        $urlSlug = $pageUrl !== null && $pageUrl !== ''
            ? $sanitize(basename(rtrim((string)parse_url($pageUrl, PHP_URL_PATH), '/')))
            : '';
        if ($urlSlug !== '' && isset($advisors[$urlSlug])) {
            $id = $urlSlug;
        } else {
            // 3. Bestehendes Cookie wiederverwenden.
            $cookieId = $sanitize($_COOKIE[RI24_BAUFI_BERATER_COOKIE] ?? '');
            if ($cookieId !== '' && isset($advisors[$cookieId])) {
                $id = $cookieId;
            } else {
                // 4. Zufällige Zuweisung (Platzhalter-Regel, siehe Docblock oben).
                $ids = array_keys($advisors);
                $id  = $ids[array_rand($ids)];
            }
        }
    }

    if (($_COOKIE[RI24_BAUFI_BERATER_COOKIE] ?? null) !== $id && !headers_sent()) {
        setcookie(RI24_BAUFI_BERATER_COOKIE, $id, [
            'expires'  => time() + 60 * 60 * 24 * 180,
            'path'     => '/',
            'secure'   => true,
            'httponly' => true,
            'samesite' => 'Lax',
        ]);
    }

    return ['id' => $id] + $advisors[$id];
}
