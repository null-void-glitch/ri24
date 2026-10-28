<?php
/**
 * Konfiguration für den DeepChat-Proxy (chat.php).
 *
 * Werte werden aus Umgebungsvariablen gelesen. Für die lokale Entwicklung kann
 * eine Datei `config.local.php` (nicht eingecheckt) daneben liegen, die diese
 * Konstanten überschreibt bzw. vorab setzt (z.B. die ngrok-MCP-URL).
 */

// Lokale Overrides für die Entwicklung (API-Key, ngrok-MCP-URL etc.).
if (is_file(__DIR__ . '/config.local.php')) {
    require __DIR__ . '/config.local.php';
}

/** OpenAI API-Key — NIEMALS ins Frontend! Nur hier serverseitig. */
if (!defined('OPENAI_API_KEY')) {
    define('OPENAI_API_KEY', getenv('OPENAI_API_KEY') ?: '');
}

/** Modell für die Responses API. */
if (!defined('OPENAI_MODEL')) {
    define('OPENAI_MODEL', getenv('OPENAI_MODEL') ?: 'gpt-4.1');
}

/**
 * URL des Remote-MCP-Servers.
 *  - Dev:  ngrok-URL des lokalen MCP, z.B. https://xxxx.ngrok-free.app/mcp/sse
 *  - Prod: interne/öffentliche URL des Backend-MCP.
 */
if (!defined('MCP_SERVER_URL')) {
    define('MCP_SERVER_URL', getenv('MCP_SERVER_URL') ?: '');
}

/** Label, unter dem der MCP-Server dem Modell bekannt gemacht wird. */
if (!defined('MCP_SERVER_LABEL')) {
    define('MCP_SERVER_LABEL', getenv('MCP_SERVER_LABEL') ?: 'ri24');
}

/**
 * Optionaler Authorization-Header-Wert für den MCP-Server (z.B. "Bearer xyz").
 * Leer lassen, wenn der MCP keine Auth benötigt.
 */
if (!defined('MCP_AUTHORIZATION')) {
    define('MCP_AUTHORIZATION', getenv('MCP_AUTHORIZATION') ?: '');
}

/**
 * Erlaubte Origins für CORS. In Produktion steht der Endpoint auf derselben
 * Domain wie das Exposé (kein CORS nötig). Für Dev (ngrok/localhost) hier die
 * Origins eintragen, kommagetrennt, oder '*' für alle.
 */
if (!defined('ALLOWED_ORIGINS')) {
    define('ALLOWED_ORIGINS', getenv('CHAT_ALLOWED_ORIGINS') ?: 'https://www.regionalimmobilien24.de');
}

/**
 * Pfad zur Datei mit den Agent-Instructions (System-Prompt).
 * Standard: der gepflegte system-prompt.md eine Ebene höher.
 */
if (!defined('INSTRUCTIONS_FILE')) {
    define('INSTRUCTIONS_FILE', getenv('CHAT_INSTRUCTIONS_FILE') ?: __DIR__ . '/../system-prompt.md');
}
