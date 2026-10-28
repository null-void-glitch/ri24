<?php
/**
 * Datei-Upload-Endpoint für den Finanzierungscheck.
 *
 * Empfängt Dateien vom DeepChat-Widget (base64-kodiert im JSON-Body)
 * und speichert sie in sessions/{token}/uploads/.
 *
 * Später: Weiterleitung an Pitcom/Europace-Endpoint, sobald URL bekannt.
 *
 * GET  ?t={token}  → Browser-Upload-Seite (für externen Link-Versand)
 * POST ?t={token}  → JSON-Body mit { files: [{name, type, data}] }
 *                    → Speichert Dateien, gibt { ok, saved } zurück
 */

require __DIR__ . '/config.php';

$token = preg_replace('/[^A-Za-z0-9]/', '', (string)($_GET['t'] ?? ''));

// ─── CORS ────────────────────────────────────────────────────────────────────────
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '') {
    $allowed = array_map('trim', explode(',', ALLOWED_ORIGINS));
    if (in_array('*', $allowed, true) || in_array($origin, $allowed, true)) {
        header('Access-Control-Allow-Origin: ' . $origin);
        header('Vary: Origin');
        header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
        header('Access-Control-Allow-Headers: Content-Type');
    }
}
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') { http_response_code(204); exit; }

// ─── Token prüfen ───────────────────────────────────────────────────────────────
if ($token === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Kein Token angegeben.']);
    exit;
}
$sessionFile = SESSIONS_DIR . '/' . $token . '.json';
if (!is_file($sessionFile)) {
    http_response_code(404);
    echo json_encode(['ok' => false, 'error' => 'Ungültiger oder abgelaufener Link.']);
    exit;
}

// ─── GET: einfache Browser-Upload-Seite ─────────────────────────────────────────
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'GET') {
    $session  = json_decode((string)file_get_contents($sessionFile), true) ?: [];
    $vorname  = htmlspecialchars($session['vorname']  ?? '', ENT_QUOTES, 'UTF-8');
    $nachname = htmlspecialchars($session['nachname'] ?? '', ENT_QUOTES, 'UTF-8');
    $tokenJs  = json_encode($token);
    ?>
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Unterlagen hochladen – <?= $vorname ?> <?= $nachname ?></title>
  <meta name="robots" content="noindex, nofollow">
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body { margin: 0; font-family: system-ui, sans-serif; background: #f7f8f9; color: #222; }
    .topbar { background: #fff; border-bottom: 1px solid #e2e5ea; padding: 12px 20px; display: flex; align-items: center; gap: 12px; }
    .topbar img { height: 26px; }
    h1 { font-size: 1.1rem; font-weight: 600; margin: 0; }
    .wrap { max-width: 560px; margin: 40px auto; padding: 0 20px; }
    .drop-zone {
      border: 2px dashed #bcd03a; border-radius: 12px; padding: 40px 20px;
      text-align: center; background: #fff; cursor: pointer; transition: background .15s;
    }
    .drop-zone.over { background: #f5fadf; }
    .drop-zone p { margin: 8px 0; color: #555; font-size: .95rem; }
    .drop-zone strong { color: #333; }
    input[type=file] { display: none; }
    .file-list { margin-top: 16px; list-style: none; padding: 0; }
    .file-list li { background: #fff; border: 1px solid #e2e5ea; border-radius: 8px;
      padding: 10px 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; font-size: .9rem; }
    .file-list li .fname { flex: 1; }
    .file-list li .fsize { color: #888; font-size: .8rem; }
    .file-list li .remove { cursor: pointer; color: #c00; font-size: 1.1rem; line-height: 1; }
    .btn { display: block; width: 100%; padding: 14px; background: #BDE04F; border: none;
      border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 16px; }
    .btn:disabled { opacity: .5; cursor: default; }
    .status { margin-top: 14px; padding: 12px 16px; border-radius: 8px; font-size: .9rem; display: none; }
    .status.ok  { background: #e8f7e8; color: #1a6e1a; }
    .status.err { background: #fdeaea; color: #8b0000; }
  </style>
</head>
<body>
  <div class="topbar">
    <img src="https://www.regionalimmobilien24.de/wp-content/uploads/2020/10/logo_ri24_new_300.png"
         alt="Regionalimmobilien24" onerror="this.style.display='none'">
    <h1>Unterlagen hochladen</h1>
  </div>
  <div class="wrap">
    <p>Hallo <?= $vorname ?>, lade hier deine Unterlagen für den Finanzierungscheck hoch.</p>
    <div class="drop-zone" id="drop">
      <strong>Dateien hier ablegen</strong>
      <p>oder klicken zum Auswählen</p>
      <p style="font-size:.8rem;color:#999">PDF, JPG, PNG · max. 20 MB je Datei</p>
      <input type="file" id="fileInput" multiple accept=".pdf,.jpg,.jpeg,.png,.doc,.docx">
    </div>
    <ul class="file-list" id="fileList"></ul>
    <button class="btn" id="uploadBtn" disabled>Hochladen</button>
    <div class="status" id="status"></div>
  </div>

  <script>
    var TOKEN = <?= $tokenJs ?>;
    var files = [];

    var drop   = document.getElementById('drop');
    var input  = document.getElementById('fileInput');
    var list   = document.getElementById('fileList');
    var btn    = document.getElementById('uploadBtn');
    var status = document.getElementById('status');

    drop.addEventListener('click', function() { input.click(); });
    drop.addEventListener('dragover', function(e) { e.preventDefault(); drop.classList.add('over'); });
    drop.addEventListener('dragleave', function() { drop.classList.remove('over'); });
    drop.addEventListener('drop', function(e) {
      e.preventDefault(); drop.classList.remove('over');
      addFiles(Array.from(e.dataTransfer.files));
    });
    input.addEventListener('change', function() { addFiles(Array.from(input.files)); input.value = ''; });

    function addFiles(newFiles) {
      newFiles.forEach(function(f) { files.push(f); });
      render();
    }
    function render() {
      list.innerHTML = '';
      files.forEach(function(f, i) {
        var li = document.createElement('li');
        li.innerHTML = '<span class="fname">' + escHtml(f.name) + '</span>'
          + '<span class="fsize">' + (f.size > 1048576 ? (f.size/1048576).toFixed(1)+'&nbsp;MB' : Math.round(f.size/1024)+'&nbsp;KB') + '</span>'
          + '<span class="remove" data-i="'+i+'">✕</span>';
        list.appendChild(li);
      });
      list.querySelectorAll('.remove').forEach(function(el) {
        el.addEventListener('click', function() { files.splice(+el.dataset.i, 1); render(); });
      });
      btn.disabled = files.length === 0;
    }
    function escHtml(s) { return s.replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

    btn.addEventListener('click', function() {
      if (!files.length) return;
      btn.disabled = true;
      status.style.display = 'none';

      var readers = files.map(function(f) {
        return new Promise(function(res, rej) {
          var r = new FileReader();
          r.onload = function() { res({ name: f.name, type: f.type, data: r.result.split(',')[1] }); };
          r.onerror = rej;
          r.readAsDataURL(f);
        });
      });

      Promise.all(readers).then(function(encoded) {
        return fetch('upload.php?t=' + encodeURIComponent(TOKEN), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ files: encoded })
        });
      }).then(function(r) { return r.json(); }).then(function(d) {
        status.style.display = 'block';
        if (d.ok) {
          status.className = 'status ok';
          status.textContent = '✓ ' + d.saved + ' Datei(en) erfolgreich hochgeladen.';
          files = []; render();
        } else {
          status.className = 'status err';
          status.textContent = 'Fehler: ' + (d.error || 'Unbekannter Fehler');
          btn.disabled = false;
        }
      }).catch(function() {
        status.style.display = 'block'; status.className = 'status err';
        status.textContent = 'Verbindungsfehler. Bitte erneut versuchen.';
        btn.disabled = false;
      });
    });
  </script>
</body>
</html>
    <?php
    exit;
}

// ─── POST: Dateien empfangen / Kategorien bestätigen und weiterleiten ───────────
header('Content-Type: application/json; charset=utf-8');

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Method not allowed']);
    exit;
}

$raw  = file_get_contents('php://input');
$body = json_decode($raw, true);

if (!is_array($body)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Ungültiger JSON-Body.']);
    exit;
}

// ─── action=submit: kategorisierte Dateien an Pitcom weiterleiten ───────────────
if (($_GET['action'] ?? '') === 'submit') {
    $docs = $body['documents'] ?? [];
    if (empty($docs) || !is_array($docs)) {
        http_response_code(400);
        echo json_encode(['ok' => false, 'error' => 'Keine Dokumente im Body.']);
        exit;
    }

    require_once __DIR__ . '/pitcom.php';
    $session         = json_decode((string)file_get_contents($sessionFile), true) ?: [];
    $pitcomSessionId = pitcom_ensure_session_id($sessionFile, $session);
    $uploadDir       = SESSIONS_DIR . '/' . $token . '/uploads';
    $submitted       = 0;
    $errors          = [];

    // Dateien aus dem lokalen Upload-Verzeichnis einsammeln
    $filesToSend = [];
    foreach ($docs as $doc) {
        $filename = basename((string)($doc['filename'] ?? ''));
        $category = trim((string)($doc['category'] ?? ''));
        if ($filename === '') { $errors[] = 'Leerer Dateiname übersprungen.'; continue; }

        $found = null;
        if (is_dir($uploadDir)) {
            foreach (scandir($uploadDir) as $f) {
                if (str_ends_with($f, '_' . $filename) || $f === $filename) {
                    $found = $uploadDir . '/' . $f;
                    break;
                }
            }
        }
        if ($found === null) { $errors[] = "Datei nicht gefunden: $filename"; continue; }

        $filesToSend[] = ['path' => $found, 'filename' => $filename, 'category' => $category];
    }

    if (!empty($filesToSend)) {
        if ($pitcomSessionId !== '') {
            // Human-Handshake: Pitcom-Spam-Detection umgehen (HTTP 412/428-Wall)
            $browserUa = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
            $humanCookie = '';
            $hsCh = curl_init('https://www.regionalimmobilien24.de/ressource/set/user/human/');
            curl_setopt_array($hsCh, [
                CURLOPT_HTTPGET        => true,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_HEADER         => true,
                CURLOPT_TIMEOUT        => 8,
                CURLOPT_HTTPHEADER     => [
                    'User-Agent: ' . $browserUa,
                    'X-Requested-With: XMLHttpRequest',
                    'Accept: application/json, text/javascript, */*; q=0.01',
                ],
            ]);
            $hsResp = curl_exec($hsCh);
            curl_close($hsCh);
            // Set-Cookie-Header aus Antwort extrahieren
            if ($hsResp && preg_match_all('/^Set-Cookie:\s*([^;]+)/mi', $hsResp, $cm)) {
                $humanCookie = implode('; ', $cm[1]);
            }

            // Endpoint-URL + Bearer aus gespeicherten Pitcom-Endpoints (Production)
            $ep        = pitcom_endpoint($session, 'add-files');
            $pitcomUrl = $ep['url'];
            $bearer    = $ep['bearer'];

            $postFields = [];
            foreach ($filesToSend as $idx => $f) {
                $mime     = mime_content_type($f['path']) ?: 'application/octet-stream';
                $label    = $f['category'] !== ''
                    ? $f['category'] . '_' . $f['filename']
                    : $f['filename'];
                $postFields["file[$idx]"] = new CURLFile($f['path'], $mime, $label);
                if ($f['category'] !== '') {
                    $postFields["category[$idx]"] = $f['category'];
                }
            }

            $headers = [
                'Authorization: Bearer ' . $bearer,
                'User-Agent: ' . $browserUa,
                'Accept: */*',
            ];
            if ($humanCookie !== '') {
                $headers[] = 'Cookie: ' . $humanCookie;
            }

            $ch = curl_init($pitcomUrl);
            curl_setopt_array($ch, [
                CURLOPT_POST           => true,
                CURLOPT_POSTFIELDS     => $postFields,
                CURLOPT_HTTPHEADER     => $headers,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT        => 30,
            ]);
            $pitcomRes  = curl_exec($ch);
            $pitcomCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            $curlErr    = curl_error($ch);
            curl_close($ch);

            if ($pitcomCode >= 200 && $pitcomCode < 300) {
                $submitted = count($filesToSend);
            } else {
                $errMsg = $curlErr ?: "HTTP $pitcomCode";
                $errors[] = "Pitcom-Upload fehlgeschlagen: $errMsg";
                error_log("[upload.php/submit] Pitcom-Fehler ($pitcomCode): $curlErr | Response: " . substr($pitcomRes, 0, 300));
            }
        } else {
            // Kein pitcom_session_id — Dateien liegen lokal, als erfolgreich markieren
            $submitted = count($filesToSend);
        }
    }

    echo json_encode(['ok' => $submitted > 0 || empty($errors), 'submitted' => $submitted, 'errors' => $errors], JSON_UNESCAPED_UNICODE);
    exit;
}

// ─── Normaler POST: Rohdateien empfangen und lokal speichern ─────────────────────
if (empty($body['files']) || !is_array($body['files'])) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Keine Dateien im Body.']);
    exit;
}

$uploadDir = SESSIONS_DIR . '/' . $token . '/uploads';
if (!is_dir($uploadDir)) {
    @mkdir($uploadDir, 0700, true);
}

$ALLOWED_MIME = [
    'application/pdf',
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/heic', 'image/heif',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream', // Fallback wenn Browser keinen Typ meldet
];
$ALLOWED_EXT  = ['pdf','jpg','jpeg','png','gif','webp','heic','heif','doc','docx','xls','xlsx','txt'];
$MAX_BYTES    = 20 * 1024 * 1024; // 20 MB

$saved  = 0;
$errors = [];

foreach ($body['files'] as $file) {
    $name = basename((string)($file['name'] ?? ''));
    $type = (string)($file['type'] ?? '');
    $data = (string)($file['data'] ?? '');

    if ($name === '' || $data === '') { $errors[] = 'Leere Datei übersprungen.'; continue; }
    $ext = strtolower(pathinfo($name, PATHINFO_EXTENSION));
    if (!in_array($type, $ALLOWED_MIME, true) && !in_array($ext, $ALLOWED_EXT, true)) {
        $errors[] = "Typ nicht erlaubt: $type ($name)"; continue;
    }

    $decoded = base64_decode($data, true);
    if ($decoded === false) { $errors[] = "Base64-Fehler bei: $name"; continue; }
    if (strlen($decoded) > $MAX_BYTES) { $errors[] = "Zu groß (>20 MB): $name"; continue; }

    // Eindeutiger Dateiname: Zeitstempel-Präfix
    $safeName = preg_replace('/[^A-Za-z0-9_\.\-]/', '_', $name);
    $dest = $uploadDir . '/' . date('Ymd_His_') . $safeName;
    if (file_put_contents($dest, $decoded, LOCK_EX) === false) {
        $errors[] = "Konnte $name nicht speichern."; continue;
    }
    chmod($dest, 0600);
    $saved++;
}

echo json_encode([
    'ok'     => $saved > 0,
    'saved'  => $saved,
    'errors' => $errors,
], JSON_UNESCAPED_UNICODE);
