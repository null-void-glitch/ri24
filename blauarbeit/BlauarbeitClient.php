<?php

declare(strict_types=1);

/**
 * Minimal client for the Blauarbeit Partner API (see openapi.json).
 * Holds the OAuth2 client-credentials exchange and caches the resulting
 * Bearer token on disk so we don't re-authenticate on every request.
 */
class BlauarbeitClient
{
    private const BASE_URLS = [
        'production' => 'https://api-prod.blauarbeit.de',
        'staging' => 'https://api-stag.blauarbeit.de',
    ];

    private string $baseUrl;
    private string $clientId;
    private string $clientSecret;
    private string $tokenCacheFile;

    public function __construct(array $config)
    {
        $environment = $config['environment'] ?? 'production';
        if (!isset(self::BASE_URLS[$environment])) {
            throw new InvalidArgumentException("Unknown Blauarbeit environment: {$environment}");
        }

        $this->baseUrl = self::BASE_URLS[$environment];
        $this->clientId = $config['client_id'];
        $this->clientSecret = $config['client_secret'];
        $this->tokenCacheFile = sys_get_temp_dir() . '/blauarbeit_token_' . md5($this->clientId . $environment) . '.json';
    }

    /**
     * GET /v2/partners/users/craftsmen — up to 3 craftsmen near a zipcode,
     * ordered by distance. Rate limited to 30 requests/minute by Blauarbeit.
     */
    public function nearbyCraftsmen(string $zipcode, ?int $category = null): array
    {
        $query = ['zipcode' => $zipcode];
        if ($category !== null) {
            $query['category'] = $category;
        }

        return $this->request('GET', '/v2/partners/users/craftsmen?' . http_build_query($query));
    }

    /**
     * GET /v2/partners/categories — the trade categories craftsmen can be filtered by.
     */
    public function categories(): array
    {
        return $this->request('GET', '/v2/partners/categories');
    }

    private function request(string $method, string $path): array
    {
        $token = $this->getAccessToken();

        $ch = curl_init($this->baseUrl . $path);
        curl_setopt_array($ch, [
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10,
            CURLOPT_HTTPHEADER => [
                'Authorization: Bearer ' . $token,
                'Accept: application/json',
            ],
        ]);
        $body = curl_exec($ch);
        if ($body === false) {
            $error = curl_error($ch);
            curl_close($ch);
            throw new RuntimeException("Blauarbeit API request failed: {$error}");
        }
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        $decoded = json_decode($body, true);
        if ($status >= 400) {
            throw new RuntimeException('Blauarbeit API error (HTTP ' . $status . '): ' . ($decoded['message'] ?? $body));
        }

        return $decoded;
    }

    private function getAccessToken(): string
    {
        if (is_file($this->tokenCacheFile)) {
            $cached = json_decode((string) file_get_contents($this->tokenCacheFile), true);
            if (is_array($cached) && ($cached['expires_at'] ?? 0) > time() + 30) {
                return $cached['access_token'];
            }
        }

        $ch = curl_init($this->baseUrl . '/oauth/token');
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode([
                'grant_type' => 'client_credentials',
                'client_id' => $this->clientId,
                'client_secret' => $this->clientSecret,
            ]),
        ]);
        $body = curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($body === false || $status >= 400) {
            throw new RuntimeException('Failed to obtain Blauarbeit access token (HTTP ' . $status . ')');
        }

        $decoded = json_decode($body, true);

        file_put_contents($this->tokenCacheFile, json_encode([
            'access_token' => $decoded['access_token'],
            'expires_at' => time() + (int) $decoded['expires_in'],
        ]));

        return $decoded['access_token'];
    }
}
