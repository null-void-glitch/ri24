<?php
/**
 * Konfiguration für den personalisierten Finanzierungscheck-Chatbot.
 *
 * Kunden erhalten nach einer Finanzierungsanfrage einen eindeutigen Link
 * (session.php?t={token}) mit einem vollflächigen Chat-Widget, das ihre
 * Anfragedaten bereits kennt und gezielt durch den Vorbereitungsprozess führt.
 */

if (is_file(__DIR__ . '/config.local.php')) {
    require __DIR__ . '/config.local.php';
}

/** OpenAI API-Key */
if (!defined('OPENAI_API_KEY')) {
    define('OPENAI_API_KEY', getenv('OPENAI_API_KEY') ?: '');
}

/** Modell für die Responses API */
if (!defined('OPENAI_MODEL')) {
    define('OPENAI_MODEL', getenv('OPENAI_MODEL') ?: 'gpt-4.1');
}

/** URL des Remote-MCP-Servers */
if (!defined('MCP_SERVER_URL')) {
    define('MCP_SERVER_URL', getenv('MCP_SERVER_URL') ?: '');
}

if (!defined('MCP_SERVER_LABEL')) {
    define('MCP_SERVER_LABEL', getenv('MCP_SERVER_LABEL') ?: 'ri24-baufi');
}

if (!defined('MCP_AUTHORIZATION')) {
    define('MCP_AUTHORIZATION', getenv('MCP_AUTHORIZATION') ?: '');
}

/** CORS — erlaubte Origins */
if (!defined('ALLOWED_ORIGINS')) {
    define('ALLOWED_ORIGINS', getenv('FINANZCHECK_ALLOWED_ORIGINS') ?: 'https://www.regionalimmobilien24.de');
}

/**
 * Basis-URL der Landingpage — wird an den Token angehängt, um den
 * verschickbaren Link zu erzeugen. Mit abschließendem /.
 */
if (!defined('LANDINGPAGE_BASE_URL')) {
    define('LANDINGPAGE_BASE_URL', getenv('FINANZCHECK_BASE_URL') ?: 'https://www.regionalimmobilien24.de/finanzierungscheck/session.php?t=');
}

/** Verzeichnis für die Session-JSONs (Flat-File-Speicher) */
if (!defined('SESSIONS_DIR')) {
    define('SESSIONS_DIR', __DIR__ . '/sessions');
}

/** System-Prompt für den Finanzierungscheck-Chatbot */
if (!defined('INSTRUCTIONS_FILE')) {
    define('INSTRUCTIONS_FILE', getenv('FINANZCHECK_INSTRUCTIONS_FILE') ?: __DIR__ . '/../system-prompt-finanzierungscheck.md');
}

/**
 * WhatsApp Business API (Meta Cloud API)
 * Benötigt: Phone Number ID + permanentes Access Token aus dem Meta Developer Portal.
 */
if (!defined('WA_PHONE_NUMBER_ID')) {
    define('WA_PHONE_NUMBER_ID', getenv('WA_PHONE_NUMBER_ID') ?: '');
}

if (!defined('WA_ACCESS_TOKEN')) {
    define('WA_ACCESS_TOKEN', getenv('WA_ACCESS_TOKEN') ?: '');
}

/**
 * Name des Meta-genehmigten Message Templates für den ersten Kundenkontakt.
 * Muss im Meta Business Manager erstellt und genehmigt sein.
 * Template-Variablen: {{1}} = Vorname, {{2}} = Landing-Page-URL
 */
if (!defined('WA_TEMPLATE_NAME')) {
    define('WA_TEMPLATE_NAME', getenv('WA_TEMPLATE_NAME') ?: 'finanzierungscheck_einladung');
}

if (!defined('WA_TEMPLATE_LANG')) {
    define('WA_TEMPLATE_LANG', getenv('WA_TEMPLATE_LANG') ?: 'de');
}

/**
 * Interner E-Mail-Endpoint (bereits vorhandener Versanddienst).
 * POST mit JSON: { to, subject, body_html }
 */
if (!defined('EMAIL_ENDPOINT')) {
    define('EMAIL_ENDPOINT', getenv('FINANZCHECK_EMAIL_ENDPOINT') ?: '');
}

if (!defined('EMAIL_ENDPOINT_SECRET')) {
    define('EMAIL_ENDPOINT_SECRET', getenv('FINANZCHECK_EMAIL_ENDPOINT_SECRET') ?: '');
}

/**
 * Geheimer Schlüssel zum Absichern der create-session.php API.
 * Muss im Authorization-Header der anfragenden Anwendung mitgeschickt werden:
 *   Authorization: Bearer {CREATE_SESSION_SECRET}
 */
if (!defined('CREATE_SESSION_SECRET')) {
    define('CREATE_SESSION_SECRET', getenv('FINANZCHECK_CREATE_SESSION_SECRET') ?: '');
}

/** Optionale OpenAI Vector-Store-ID (Wissensdatenbank, wie bei chat-baufinanzierung) */
if (!defined('FILE_SEARCH_VECTOR_STORE_ID')) {
    define('FILE_SEARCH_VECTOR_STORE_ID', getenv('FINANZCHECK_VECTOR_STORE_ID') ?: '');
}

/**
 * Pitcom Backend API Basis-URL — wird für Datei-Relay und CRM-Notizen verwendet.
 * Pfadformat: {PITCOM_API_BASE}/add/files/{pitcom_session_id}.json
 *             {PITCOM_API_BASE}/add/chatverlauf/{pitcom_session_id}.json
 * Bearer je Request: strtoupper(md5($pitcomSessionId))
 */
if (!defined('PITCOM_API_BASE')) {
    define('PITCOM_API_BASE', getenv('PITCOM_API_BASE') ?: 'https://backend.regionalimmobilien24.de/api/finanzierungscheck');
}
