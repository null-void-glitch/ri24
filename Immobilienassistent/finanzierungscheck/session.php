<?php
/**
 * Personalisierte Finanzierungscheck-Landingpage.
 *
 * URL: session.php?t={token}
 *
 * Zeigt lediglich das vollflächige DeepChat-Widget. Keine Navigation,
 * kein Rechner — der Chatbot führt den Kunden allein durch den Prozess.
 *
 * Das Session-JSON wird serverseitig geladen, um:
 *   1. Den Kundennamen für den <title> zu nutzen.
 *   2. Den Token sicher an das Frontend zu übergeben (nicht den vollen JSON-Inhalt!).
 *      Das chat.php-Backend liest den vollen JSON erst serverseitig.
 *   3. Eine 404-Seite auszuliefern, wenn der Token unbekannt ist.
 */

require __DIR__ . '/config.php';

$token = preg_replace('/[^A-Za-z0-9]/', '', (string)($_GET['t'] ?? ''));

$session = null;
if ($token !== '') {
    $sessionFile = SESSIONS_DIR . '/' . $token . '.json';
    if (is_file($sessionFile)) {
        $session = json_decode((string)file_get_contents($sessionFile), true) ?: null;
    }
}

if ($session === null) {
    http_response_code(404);
    echo '<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><title>Nicht gefunden</title></head>'
        . '<body style="font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">'
        . '<p style="color:#555">Dieser Link ist ungültig oder abgelaufen.</p></body></html>';
    exit;
}

$vorname  = htmlspecialchars($session['vorname']  ?? '', ENT_QUOTES, 'UTF-8');
$nachname = htmlspecialchars($session['nachname'] ?? '', ENT_QUOTES, 'UTF-8');
$tokenJs  = json_encode($token); // für JavaScript-Ausgabe

// Basis-URL desselben Verzeichnisses für den Chat-Endpoint (relativ)
$chatEndpoint = 'chat.php';
?>
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Finanzierungsassistent – <?= $vorname ?> <?= $nachname ?></title>
  <!-- Kein Indexieren durch Suchmaschinen -->
  <meta name="robots" content="noindex, nofollow">
  <style>
    *, *::before, *::after { box-sizing: border-box; }

    html, body {
      margin: 0; padding: 0;
      height: 100%; width: 100%;
      background: #f7f8f9;
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      /* Verhindert Overscroll-Bounce auf iOS außerhalb des Chat-Widgets */
      overflow: hidden;
    }

    /* Minimale Kopfzeile mit Logo — bleibt am oberen Rand fixiert */
    .topbar {
      position: fixed; top: 0; left: 0; right: 0;
      height: 48px;
      background: #fff;
      border-bottom: 1px solid #e2e5ea;
      display: flex; align-items: center; padding: 0 16px;
      z-index: 10;
    }
    .topbar img { height: 26px; }
    .topbar-spacer { flex: 1; }
    .ai-badge {
      font-size: .72rem; color: #667; white-space: nowrap;
    }

    /* EU AI Act Art. 50: dauerhafter KI-Hinweis, sitzt zwischen Topbar und Chat */
    .ai-notice {
      position: fixed; top: 48px; left: 0; right: 0;
      background: #f1f4f2; border-bottom: 1px solid #e2e5ea;
      font-size: .74rem; color: #555; padding: 5px 16px;
      z-index: 9;
    }

    /* Chat-Widget füllt den gesamten verbleibenden Viewport */
    .chat-wrap {
      position: fixed;
      top: calc(48px + 28px); /* topbar + ai-notice */
      left: 0; right: 0; bottom: 0;
    }

    deep-chat {
      width: 100%; height: 100%;
      display: block;
      border: none !important;
      border-radius: 0 !important;
    }
  </style>
</head>
<body>

  <div class="topbar">
    <img src="https://www.regionalimmobilien24.de/wp-content/uploads/2020/10/logo_ri24_new_300.png"
         alt="Regionalimmobilien24" onerror="this.style.display='none'">
    <div class="topbar-spacer"></div>
    <span class="ai-badge">🤖 KI-gestützter Assistent</span>
  </div>

  <div class="ai-notice">
    KI-generierter Inhalt · Dieser Assistent ist eine künstliche Intelligenz, kein Mensch
  </div>

  <div class="chat-wrap">
    <script type="module"
      src="https://cdn.jsdelivr.net/npm/deep-chat@2/dist/deepChat.bundle.js"></script>
    <deep-chat id="fc-chat"></deep-chat>
  </div>

  <script>
    (function () {
      var SESSION_TOKEN = <?= $tokenJs ?>;
      var ENDPOINT      = '<?= htmlspecialchars($chatEndpoint, ENT_QUOTES, 'UTF-8') ?>';

      var chat = document.getElementById('fc-chat');

      var conversationId = (window.crypto && crypto.randomUUID)
        ? crypto.randomUUID()
        : 'c' + Date.now() + Math.random().toString(36).slice(2);

      customElements.whenDefined('deep-chat').then(function () {

        chat.connect = {
          stream: true,
          handler: function (body, signals) {
            var controller = new AbortController();
            signals.stopClicked.listener = function () { controller.abort(); };

            // ─── SSE-Pump ────────────────────────────────────────────────────
            function pump(reader, decoder, buf) {
              return reader.read().then(function (chunk) {
                if (chunk.done) { signals.onClose(); return; }
                buf += decoder.decode(chunk.value, { stream: true });
                var lines = buf.split('\n');
                buf = lines.pop();
                lines.forEach(function (line) {
                  if (line.indexOf('data:') !== 0) return;
                  var raw = line.slice(5).trim();
                  if (raw === '' || raw === '[DONE]') return;
                  var pl;
                  try { pl = JSON.parse(raw); } catch (e) { return; }
                  if (pl.text) signals.onResponse({ text: pl.text });
                });
                return pump(reader, decoder, buf);
              });
            }

            // ─── Chat senden (nach optionalem Upload) ────────────────────────
            function dispatchChat(jsonBody, uploadedFiles) {
              var msgs = (jsonBody.messages || []).map(function (m) {
                if (m.files && m.files.length) {
                  var c = { role: m.role };
                  if (m.text && m.text.trim()) c.text = m.text;
                  return c;
                }
                return m;
              });

              function doFetch(note) {
                if (note) {
                  var appended = false;
                  for (var i = msgs.length - 1; i >= 0; i--) {
                    if (msgs[i].role === 'user') {
                      msgs[i].text = (msgs[i].text || '') + note;
                      appended = true;
                      break;
                    }
                  }
                  if (!appended) msgs.push({ role: 'user', text: note.trim() });
                }
                jsonBody.messages = msgs;
                fetch(ENDPOINT, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(jsonBody),
                  signal: controller.signal
                }).then(function (res) {
                  if (!res.ok || !res.body) {
                    signals.onResponse({ error: 'Der Assistent ist momentan nicht erreichbar.' });
                    signals.onClose();
                    return;
                  }
                  signals.onOpen();
                  return pump(res.body.getReader(), new TextDecoder(), '');
                }).catch(function (err) {
                  if (err && err.name === 'AbortError') { signals.onClose(); return; }
                  signals.onResponse({ error: 'Verbindung fehlgeschlagen. Bitte Seite neu laden.' });
                  signals.onClose();
                });
              }

              if (uploadedFiles && uploadedFiles.length > 0) {
                fetch('upload.php?t=' + encodeURIComponent(SESSION_TOKEN), {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ files: uploadedFiles }),
                  signal: controller.signal
                }).then(function (r) { return r.json(); }).then(function (d) {
                  var names = uploadedFiles.map(function (f) { return f.name; }).join(', ');
                  doFetch(d.ok
                    ? '\n\n[SYSTEM: Der Nutzer hat ' + d.saved + ' Datei(en) erfolgreich hochgeladen: ' + names + ']'
                    : '\n\n[SYSTEM: Datei-Upload fehlgeschlagen (' + (d.error || 'Fehler') + '). Bitte Nutzer informieren.]');
                }).catch(function () {
                  doFetch('\n\n[SYSTEM: Datei-Upload konnte nicht gesendet werden. Bitte Nutzer informieren.]');
                });
              } else {
                doFetch(null);
              }
            }

            // ─── Body normalisieren ──────────────────────────────────────────
            if (typeof FormData !== 'undefined' && body instanceof FormData) {
              // DeepChat schickt FormData wenn Dateien angehängt sind.
              // Nachrichten aus message1, message2, … rekonstruieren.
              var msgs = [];
              var idx = 1;
              var entry;
              while ((entry = body.get('message' + idx)) !== null) {
                try { msgs.push(JSON.parse(entry)); } catch (ignore) {}
                idx++;
              }

              // DeepChat fügt die aktuelle Nutzernachricht nur ein, wenn sie Text hat.
              // Ohne Text (reine Datei-Nachricht) fehlt sie → Platzhalter einfügen.
              var lastMsg = msgs[msgs.length - 1];
              if (!lastMsg || lastMsg.role !== 'user' || !(lastMsg.text && lastMsg.text.trim())) {
                msgs.push({ role: 'user', text: '' });
              }

              var jsonBody = { messages: msgs, conversation_id: conversationId, session_token: SESSION_TOKEN };

              // Dateien direkt aus FormData lesen (File-Objekte → Base64 via FileReader)
              var rawFiles = body.getAll('files');
              if (!rawFiles.length) {
                dispatchChat(jsonBody, []);
                return;
              }
              Promise.all(rawFiles.map(function (file) {
                return new Promise(function (resolve) {
                  var reader = new FileReader();
                  reader.onload  = function (e) {
                    resolve({ name: file.name || 'datei', type: file.type || 'application/octet-stream', data: e.target.result.split(',')[1] });
                  };
                  reader.onerror = function () { resolve(null); };
                  reader.readAsDataURL(file);
                });
              })).then(function (results) {
                dispatchChat(jsonBody, results.filter(Boolean));
              });

            } else {
              // Normaler JSON-Pfad (kein Datei-Upload)
              body.conversation_id = conversationId;
              body.session_token   = SESSION_TOKEN;
              dispatchChat(body, []);
            }
          }
        };

        // ─── Datei-Upload im Chat aktivieren ────────────────────────────────
        chat.mixedFiles = true;

        // ─── Styling (identisch mit chat-baufinanzierung, aber ohne Rechner-Panel) ──
        var fix = document.createElement('style');
        fix.textContent =
          /* overflow-x nur auf spezifische Scrollcontainer, nicht global —
             * { overflow-x: hidden } blockiert Drop-Events auf manchen Systemen.
             * #input-container bekommt overflow-x:clip statt hidden: clip löst die
             * CSS-Spec-Coercion nicht aus (hidden würde overflow-y:visible→auto machen,
             * was den absolut positionierten #file-attachment-container wegclippt). */
          '#messages-container { overflow-x: hidden; } ' +
          '#input-container { overflow-x: clip; } ' +
          '.input-button-container { overflow: visible !important; } ' +
          '.inside-end, .inside-start, .outside-end, .outside-start { ' +
          'inset-block-end: 50% !important; transform: translateY(50%) !important; margin: 0 !important; } ' +
          '.input-button { display: flex !important; align-items: center !important; justify-content: center !important; } ' +
          '.input-button.loading-button, .input-button:has(#stop-icon) { background-color: transparent !important; } ' +
          '.loading-submit-button { inset-block-end: 0 !important; } ' +
          '#stop-icon { position: relative !important; inset-inline-start: calc(-9990px + 0.275em) !important; ' +
          'inset-block-end: 0 !important; width: 0.22em !important; height: 0.22em !important; border-radius: 5px !important; ' +
          'background-color: #848484 !important; box-shadow: 9990px 0 0 0 #848484, calc(9990px + 0.44em) 0 0 0 #848484, ' +
          'calc(9990px + 0.8em) 0 0 0 #848484 !important; animation: loading-submit-button 1.5s infinite linear !important; }';
        chat.shadowRoot.appendChild(fix);

        chat.textInput = { placeholder: { text: 'Schreib mir …' } };
        chat.submitButtonStyles = {
          submit: {
            container: { default: { backgroundColor: '#BDE04F', width: '2rem', height: '2rem', borderRadius: '50%' } },
            svg: { styles: { default: { width: '45%', height: '45%', fill: '#333' } } }
          }
        };
        chat.messageStyles = {
          default: {
            ai:   { bubble: { backgroundColor: '#f1f4f2', color: '#111' } },
            user: { bubble: { backgroundColor: '#BDE04F', color: '#333' } }
          }
        };
        // Mikrofon-Button im Eingabefeld; nach kurzer Sprechpause wird automatisch
        // abgesendet (hands-free). Sprachbefehle „stopp"/„absenden" möglich. Analog
        // zum Exposé-Chat/Baufinanzierungs-Chat (chat/test-expose.html,
        // chat-baufinanzierung/embed-snippet.html).
        chat.speechToText = {
          webSpeech: { language: 'de-DE' },
          // Zwischenergebnisse (interim) deaktiviert: auf Android/Chrome werden sie
          // teils nicht ersetzt, sondern an den bestehenden Text angehängt – das
          // führt zu vervielfachtem/wiederholtem Text ("Ichichich möchteich…").
          // Nur finale Segmente einfügen vermeidet das zuverlässig.
          displayInterimResults: false,
          submitAfterSilence: 2500,
          commands: { stop: 'stopp', submit: 'absenden' },
          textColor: { final: '#333333' },
          button: { active: { container: { default: { backgroundColor: '#BDE04F' } } } }
        };

        // Intro-Nachricht ist leer — der Chatbot selbst schickt die personalisierte
        // Begrüßung (Schritt 1 des System-Prompts) als erste Antwort.
        // Dafür senden wir beim Laden eine stille Startnachricht.
        chat.introMessage = { html: '' };

        // Erste Nachricht automatisch senden (triggert die personalisierte Begrüßung).
        // Kurze Verzögerung, damit das Widget vollständig initialisiert ist.
        setTimeout(function () {
          chat.submitUserMessage({ text: 'Hallo' });
        }, 400);

      }); // customElements.whenDefined
    })();
  </script>
</body>
</html>
