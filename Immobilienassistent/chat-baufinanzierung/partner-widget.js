/**
 * RI24 Baufinanzierungs-Assistent – Partner-Widget-Engine
 * =========================================================
 * Für EXTERNE Berater-Webseiten (nicht auf regionalimmobilien24.de). Anders
 * als embed-snippet.html (das die eigene RI24-Berater-Seite per `berater_url`
 * live über den MCP-Server scraped, siehe advisor-resolver.php) ist die
 * Berater-Zuordnung hier vorab fest hinterlegt: Jede externe Partner-Seite
 * bekommt eine feste `beraterId`. Die eigentlichen Kontaktdaten bleiben
 * trotzdem zentral in advisors.php gepflegt — resolve_advisor() löst die ID
 * genauso auf wie beim `?berater=`-Deep-Link der Landingpage, nur dass hier
 * nie ein Cookie/Zufall zum Zug kommt, weil die ID bei jedem Request explizit
 * mitgeschickt wird.
 *
 * Einbindung auf der externen Berater-Seite:
 *
 *   <div id="ri24_baufi_widget"></div>  <!-- nur nötig für mode:'inline', siehe elementID -->
 *   <script>
 *     window.RI24_BAUFI_PARTNER_WIDGET = {
 *       teamDir:   'philipp-steppohn',   // ← pro Berater anpassen (Alias: beraterId)
 *       elementID: 'ri24_baufi_widget',  // ← nur mode:'inline' — Ziel-<div> für den Chat, siehe unten
 *       layout:    'bubble',             // 'bubble' (Floating-Launcher) oder 'inline' (Alias: mode)
 *       open:      false,                // nur mode:'bubble' — Panel direkt beim Laden aufgeklappt?
 *       color:     '#c0392b',            // optional: Marken-Farbe des Partners (Alias: accentColor)
 *       textcolor: '#ffffff',            // optional: Textfarbe AUF color; ohne Angabe automatisch
 *                                        // per Kontrastberechnung bestimmt (siehe unten)
 *       calcPosition: 'above'            // optional: 'above' (Default), 'below' oder 'none' — Rechner-
 *                                        // Panel relativ zum Chat (inline: im Seitenfluss; bubble: im
 *                                        // Popup); 'none' blendet das Panel komplett aus (nur Chat)
 *     };
 *   </script>
 *   <script async defer src="https://www.regionalimmobilien24.de/api/chat-baufinanzierung/partner-widget.js"></script>
 *
 * Jedes Feld existiert unter zwei Namen — dem ursprünglichen (beraterId/mode/
 * accentColor) und dem Namen aus dem älteren Widget-Baukasten (teamDir/
 * layout/color), damit Backend-generierte Snippets für alle RI24-Partner-
 * Widgets dieselben Feldnamen verwenden können. Beide funktionieren, auch
 * gemischt; bei beiden gesetzt gewinnt der neue Name (teamDir vor beraterId
 * usw.).
 *
 * layout/mode 'inline': der Chat wird in das per `elementID` referenzierte
 * <div> eingefügt. Ohne `elementID` fällt das Skript ersatzweise auf die
 * Position direkt hinter dem eigenen <script>-Tag zurück — das setzt aber
 * synchrones Laden voraus (kein async/defer), da sonst document.currentScript
 * beim Ausführen bereits wieder null ist. `elementID` ist daher der
 * empfohlene Weg, insbesondere für async/defer-geladene Snippets.
 * layout/mode 'bubble': das Skript baut selbst einen Floating-Launcher-Button
 * unten rechts + ein Chat-Panel, das beim Klick auf-/zuklappt (oder direkt
 * beim Laden, siehe `open`) — die Partnerseite muss dafür nichts vorbereiten,
 * `elementID` hat hier keine Wirkung.
 *
 * Rechner-Panel: zeigt/liest Kaufpreis, Eigenkapital, PLZ, Objektart,
 * Wunschrate, Zinsbindung — zweiseitig mit dem Chat verknüpft (Chat→Rechner
 * über calc_input/calc_result-Events aus dem SSE-Stream, Rechner→Chat über den
 * "Neu berechnen"-Button). In beiden Modi neben dem Chat gestapelt
 * (calcPosition steuert die Reihenfolge); im Bubble-Panel füllt der Chat den
 * verbleibenden Platz, da das Popup eine feste Gesamthöhe hat. Mit
 * `calcPosition: 'none'` entfällt das Panel komplett — reine Chat-Variante,
 * z.B. für Partner, die nur den Assistenten ohne Rechner einbinden möchten.
 *
 * color/accentColor (optional): färbt Buttons, Header, Launcher, Nutzer-Bubble
 * und Rechner-Bedienelemente in der Marken-Farbe des Partners statt im RI24-
 * Standardgrün. Helle Hintergrundtöne (KI-Bubble, Hinweis-Leiste) werden
 * automatisch als aufgehellte Variante davon berechnet. Die Textfarbe AUF der
 * Akzentfarbe (Header, Buttons, Nutzer-Bubble) wird automatisch bestimmt
 * (Anthrazit oder Weiß — je nachdem, was mehr Kontrast liefert), da Partner
 * auch sehr helle Farben wählen können, auf denen weißer Text unlesbar wäre —
 * `textcolor` überschreibt diese Automatik optional fest. Ungültige/fehlende
 * Werte fallen auf das RI24-Standardgrün (#BDE04F) zurück.
 *
 * Bekannte Grenze: läuft ohne Shadow-DOM-Isolation, d.h. global gesetzte CSS-
 * Resets auf der Partnerseite (z.B. `button { all: unset }`) können das
 * Widget verformen. Für die ersten Partner-Rollouts bewusst einfach gehalten;
 * bei Bedarf später auf Shadow DOM umstellen.
 */
(function () {
  'use strict';

  var cfg = window.RI24_BAUFI_PARTNER_WIDGET || {};
  // `teamDir` ist der Feldname aus dem älteren Widget-Baukasten (z.B.
  // baufi-suchauftrag/widget.js) — als Alias unterstützt, damit Backend-
  // generierte Snippets dasselbe Feld für alle RI24-Partner-Widgets verwenden
  // können. `beraterId` bleibt der ursprüngliche, weiterhin gültige Name.
  var BERATER_ID = cfg.teamDir || cfg.beraterId;
  if (!BERATER_ID) {
    console.error('[RI24 Baufi Widget] RI24_BAUFI_PARTNER_WIDGET.teamDir (bzw. beraterId) fehlt – Widget wird nicht geladen.');
    return;
  }

  // `layout` ist der Feldname des älteren Widget-Baukastens für dasselbe
  // Konzept wie unser `mode` — als Alias unterstützt (Werte bleiben aber
  // 'inline'/'bubble', nicht die Werte des älteren Systems).
  var MODE = (cfg.layout || cfg.mode) === 'inline' ? 'inline' : 'bubble';
  // Position des Rechner-Panels relativ zum Chat — 'above' (Default), 'below'
  // oder 'none' (kein Rechner-Panel, nur der reine Chat).
  var CALC_POSITION = cfg.calcPosition === 'below' ? 'below' : cfg.calcPosition === 'none' ? 'none' : 'above';
  // Absolute URLs nötig: dieses Skript läuft im Kontext der PARTNER-Seite,
  // relative Pfade würden gegen deren Origin statt gegen unsere API auflösen.
  var ENDPOINT = cfg.endpoint || 'https://www.regionalimmobilien24.de/api/chat-baufinanzierung/chat.php';
  var RESOLVE_ENDPOINT = cfg.resolveEndpoint || 'https://www.regionalimmobilien24.de/api/chat-baufinanzierung/resolve-advisor.php';
  // Startzustand für mode:'bubble' — 'open' (altes Widget-Feld) öffnet das
  // Panel direkt beim Laden statt auf den ersten Klick zu warten. Ohne
  // Wirkung im 'inline'-Modus (der hat keinen Auf-/Zu-Zustand).
  var START_OPEN = cfg.open === true;

  // Ziel-Element für mode:'inline', per ID (z.B. <div id="ri24_baufi_widget">
  // im HTML der Partnerseite, wie beim älteren Widget-Baukasten). Dieser Weg
  // ist NÖTIG, wenn das Script-Tag mit async/defer geladen wird — dann ist
  // document.currentScript beim Ausführen bereits wieder null (siehe
  // insertionPoint unten), das Widget wüsste also nicht, wohin es sich selbst
  // einfügen soll.
  var ELEMENT_ID = cfg.elementID || null;

  // Fallback-Einfügepunkt, falls kein elementID gesetzt ist: direkt neben dem
  // eigenen <script>-Tag (setzt synchrones Laden voraus, siehe oben — muss
  // synchron beim Laden erfasst werden, in einer async-Callback wäre
  // document.currentScript bereits wieder null).
  var insertionPoint = document.currentScript;

  // Farbe der Bedienelemente (Buttons, Header, Launcher, Nutzer-Bubble,
  // Rechner-Panel) an die Marke des externen Partners anpassbar via
  // `accentColor` (6-stelliger Hex-Code, z.B. '#c0392b') — `color` (Feldname
  // des älteren Widget-Baukastens) wird als Alias unterstützt. Fällt auf das
  // RI24-Standardgrün zurück, wenn nicht gesetzt oder ungültig.
  var GREEN = isValidHexColor(cfg.color) ? cfg.color : (isValidHexColor(cfg.accentColor) ? cfg.accentColor : '#BDE04F');
  // Heller Hintergrundton (KI-Bubble, Hinweis-Leiste) automatisch abgeleitet,
  // damit Partner nicht mehrere Farben pflegen müssen.
  var GREEN_BG = lighten(GREEN, 0.94);
  // Dunklerer Ton für Hover-/Fokus-Zustände (Rechner-Button, Eingabefelder).
  var GREEN_DARK = darken(GREEN, 0.15);
  // Textfarbe AUF der Akzentfarbe (Header, Buttons, Nutzer-Bubble): automatisch
  // bestimmt (Anthrazit oder Weiß — je nachdem, was mehr Kontrast liefert), da
  // Partner (und unser eigener Default #BDE04F) auch sehr helle Farben wählen
  // können, auf denen weißer Text unlesbar wäre. `textcolor` (Feldname des
  // älteren Widget-Baukastens) überschreibt das optional fest — nützlich, wenn
  // eine Backend-Generierung bereits eine geprüfte Textfarbe mitliefert.
  var TEXT_ON_ACCENT = isValidHexColor(cfg.textcolor) ? cfg.textcolor : readableOnAccent(GREEN);
  // Textfarbe, wenn GREEN selbst als Schrift auf WEISSEM Hintergrund verwendet
  // wird (z.B. Rechner-Vorschlags-Buttons): nur wenn GREEN dort genug Kontrast
  // liefert, sonst Anthrazit-Fallback (verhindert z.B. helles Limonengrün als
  // fast unsichtbaren Fließtext).
  var TEXT_ACCENT_ON_WHITE = readableAccentOnWhite(GREEN);

  function isValidHexColor(v) {
    return typeof v === 'string' && /^#[0-9a-f]{6}$/i.test(v);
  }

  function lighten(hex, amount) {
    var r = parseInt(hex.slice(1, 3), 16);
    var g = parseInt(hex.slice(3, 5), 16);
    var b = parseInt(hex.slice(5, 7), 16);
    var mix = function (c) { return Math.round(c + (255 - c) * amount); };
    return 'rgb(' + mix(r) + ',' + mix(g) + ',' + mix(b) + ')';
  }

  function darken(hex, amount) {
    var r = parseInt(hex.slice(1, 3), 16);
    var g = parseInt(hex.slice(3, 5), 16);
    var b = parseInt(hex.slice(5, 7), 16);
    var mix = function (c) { return Math.round(c * (1 - amount)); };
    return 'rgb(' + mix(r) + ',' + mix(g) + ',' + mix(b) + ')';
  }

  // WCAG-Relativluminanz + Kontrastverhältnis — Basis für die automatische
  // Textfarben-Wahl auf beliebigen Partnerfarben (siehe TEXT_ON_ACCENT oben).
  function relLuminance(hex) {
    var chan = function (c) {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    };
    var r = chan(parseInt(hex.slice(1, 3), 16));
    var g = chan(parseInt(hex.slice(3, 5), 16));
    var b = chan(parseInt(hex.slice(5, 7), 16));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  function contrastRatio(hexA, hexB) {
    var lA = relLuminance(hexA), lB = relLuminance(hexB);
    var lighter = Math.max(lA, lB), darker = Math.min(lA, lB);
    return (lighter + 0.05) / (darker + 0.05);
  }

  function readableOnAccent(accentHex) {
    return contrastRatio(accentHex, '#333333') >= contrastRatio(accentHex, '#ffffff') ? '#333333' : '#ffffff';
  }

  function readableAccentOnWhite(accentHex) {
    return contrastRatio(accentHex, '#ffffff') >= 3 ? accentHex : '#333333';
  }

  // EU AI Act Art. 50: Nutzer muss jederzeit erkennen können, dass er mit
  // einer KI statt einem Menschen interagiert — daher als dauerhaft
  // sichtbares Label, nicht nur einmalig in der Willkommensnachricht.
  var DISCLOSURE_TEXT = '🤖 KI-generierter Inhalt';

  var conversationId = (window.crypto && crypto.randomUUID)
    ? crypto.randomUUID()
    : 'c' + Date.now() + Math.random().toString(36).slice(2);

  // Wie in embed-snippet.html: DeepChat lädt als type="module" deferred; ohne
  // whenDefined() würde die Konfiguration vor dem "Upgrade" des Custom
  // Elements greifen und der Chat startet im Demo-Modus.
  function ensureDeepChat(cb) {
    if (window.customElements && customElements.get('deep-chat')) { cb(); return; }
    if (!document.querySelector('script[data-ri24-baufi-deepchat]')) {
      var s = document.createElement('script');
      s.type = 'module';
      s.src = 'https://cdn.jsdelivr.net/npm/deep-chat@2/dist/deepChat.bundle.js';
      s.setAttribute('data-ri24-baufi-deepchat', '1');
      document.head.appendChild(s);
    }
    customElements.whenDefined('deep-chat').then(cb);
  }

  function fetchAdvisor() {
    return fetch(RESOLVE_ENDPOINT + '?berater=' + encodeURIComponent(BERATER_ID))
      .then(function (res) { return res.ok ? res.json() : null; })
      .catch(function () { return null; });
  }

  // advisors.php pflegt `photo` bisher als Pfad relativ zur Landingpage (z.B.
  // "assets/philipp-steppohn.png") — auf einer fremden Partner-Domain (oder
  // hier lokal) kann das ins Leere zeigen. Statt eines kaputten Bild-Icons
  // fällt das Foto bei Ladefehler automatisch auf Initialen/Emoji zurück.
  function avatarMarkup(advisor, sizePx, fontSize, fallbackBg) {
    var fallback = (advisor && advisor.avatarInitials) ? advisor.avatarInitials : '💬';
    var hasPhoto = !!(advisor && advisor.photo);
    var fallbackSpan =
      '<span style="display:' + (hasPhoto ? 'none' : 'flex') + ';' +
        'position:absolute;inset:0;border-radius:50%;background:' + fallbackBg + ';' +
        'align-items:center;justify-content:center;font-size:' + fontSize + ';font-weight:600;">' +
        fallback + '</span>';
    var imgHtml = hasPhoto
      ? '<img src="' + advisor.photo + '" alt="" ' +
          'style="width:100%;height:100%;border-radius:50%;object-fit:cover;" ' +
          'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
      : '';
    return '<span style="position:relative;display:inline-flex;width:' + sizePx + 'px;height:' + sizePx + 'px;flex:0 0 auto;">' +
      imgHtml + fallbackSpan + '</span>';
  }

  // <deep-chat> ist per Default ein `display:table-cell`-Element und legt
  // intern (Shadow DOM) einen Nachrichten-Container mit `overflow-x:auto` an,
  // der bei manchen Zoom-/Font-Kombinationen 1px breiter ist als sein
  // sichtbarer Bereich — auf Systemen mit klassischen (nicht-Overlay-)
  // Scrollbars (Linux/Windows) erscheint dadurch ein sichtbarer horizontaler
  // Scrollbalken. Eine ins Shadow-DOM injizierte Regel unterdrückt das
  // zuverlässig, unabhängig von der genauen internen Struktur.
  function applyShadowDomStyleFixes(chat) {
    if (!chat.shadowRoot) return;
    var style = document.createElement('style');
    style.textContent =
      // Unterdrückt einen unerwünschten horizontalen Scrollbalken im Widget.
      '* { overflow-x: hidden !important; }' +
      // Der Sendebutton hängt (Position inside-end) absolut positioniert außerhalb
      // seines eigenen 0px breiten Containers (.input-button-container) — die
      // obige globale Regel würde ihn sonst unsichtbar clippen.
      '.input-button-container { overflow: visible !important; }' +
      // DeepChat positioniert den Sendebutton per festem inset-block-end (kein
      // echtes vertikales Zentrieren) und vererbt .input-button { margin-bottom }
      // auch an absolut positionierte Buttons — beides zusammen lässt ihn optisch
      // zu hoch sitzen. Bottom:50%+translateY(50%) zentriert ihn exakt unabhängig
      // von Button-/Zeilenhöhe; margin:0 entfernt den zusätzlichen Versatz.
      '.inside-end, .inside-start, .outside-end, .outside-start { ' +
      'inset-block-end: 50% !important; transform: translateY(50%) !important; margin: 0 !important; } ' +
      // .input-button ist standardmäßig display:block — das Icon-SVG darin
      // bleibt dadurch oben statt vertikal zu zentrieren.
      '.input-button { display: flex !important; align-items: center !important; justify-content: center !important; } ' +
      // Während des Wartens (loading-button) bzw. während die Antwort streamt
      // (Stop-Button, erkennbar am #stop-icon-Kind) zeigt DeepChat den grünen
      // Kreis mit grauem Quadrat/Punkt — hier durch die schon vorhandene,
      // aber unsichtbar positionierte "drei springende Punkte"-Animation
      // (.loading-submit-button) ersetzt, ohne grünen Hintergrund.
      '.input-button.loading-button, .input-button:has(#stop-icon) { background-color: transparent !important; } ' +
      '.loading-submit-button { inset-block-end: 0 !important; } ' +
      '#stop-icon { position: relative !important; inset-inline-start: calc(-9990px + 0.275em) !important; ' +
      'inset-block-end: 0 !important; width: 0.22em !important; height: 0.22em !important; border-radius: 5px !important; ' +
      'background-color: #848484 !important; box-shadow: 9990px 0 0 0 #848484, calc(9990px + 0.44em) 0 0 0 #848484, ' +
      'calc(9990px + 0.8em) 0 0 0 #848484 !important; animation: loading-submit-button 1.5s infinite linear !important; }';
    chat.shadowRoot.appendChild(style);
  }

  function buildChatElement(advisor, onCalcInput, onCalcResult, onTurnEnd) {
    var chat = document.createElement('deep-chat');
    applyShadowDomStyleFixes(chat);

    // Eigener Stream-Handler statt connect.url + requestInterceptor — nur so
    // lassen sich neben dem Chat-Text auch die zusätzlichen SSE-Felder
    // (calc_input/calc_result) aus chat.php für das Rechner-Panel auswerten.
    chat.connect = {
      stream: true,
      handler: function (body, signals) {
        body.conversation_id = conversationId;
        body.berater_id = BERATER_ID; // fest zugeordnet, kein Live-Scrape

        var controller = new AbortController();
        signals.stopClicked.listener = function () { controller.abort(); };

        fetch(ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
          signal: controller.signal
        }).then(function (res) {
          if (!res.ok || !res.body) {
            onTurnEnd();
            signals.onResponse({ error: 'Der Assistent ist momentan nicht erreichbar.' });
            signals.onClose();
            return;
          }
          signals.onOpen();
          var reader = res.body.getReader();
          var decoder = new TextDecoder();
          var buffer = '';

          function pump() {
            return reader.read().then(function (chunk) {
              if (chunk.done) { onTurnEnd(); signals.onClose(); return; }
              buffer += decoder.decode(chunk.value, { stream: true });
              var lines = buffer.split('\n');
              buffer = lines.pop();
              lines.forEach(function (line) {
                if (line.indexOf('data:') !== 0) return;
                var raw = line.slice(5).trim();
                if (raw === '' || raw === '[DONE]') return;
                var payload;
                try { payload = JSON.parse(raw); } catch (e) { return; }
                if (payload.text) signals.onResponse({ text: payload.text });
                else if (payload.calc_input) onCalcInput(payload.calc_input);
                else if (payload.calc_result) onCalcResult(payload.calc_result);
              });
              return pump();
            });
          }
          return pump();
        }).catch(function (err) {
          if (err && err.name === 'AbortError') { onTurnEnd(); signals.onClose(); return; }
          onTurnEnd();
          signals.onResponse({ error: 'Verbindung zum Assistenten fehlgeschlagen.' });
          signals.onClose();
        });
      }
    };

    chat.textInput = {
      placeholder: { text: 'Deine Frage zur Baufinanzierung …' },
      styles: { text: { color: '#111' } }
    };
    chat.submitButtonStyles = {
      submit: {
        container: { default: { backgroundColor: GREEN, color: TEXT_ON_ACCENT, width: '2rem', height: '2rem', borderRadius: '50%' } },
        svg: { styles: { default: { width: '45%', height: '45%' } } }
      }
    };
    chat.messageStyles = {
      default: {
        ai:   { bubble: { backgroundColor: GREEN_BG, color: '#111' } },
        user: { bubble: { backgroundColor: GREEN, color: TEXT_ON_ACCENT } }
      }
    };
    // Mikrofon-Button im Eingabefeld; nach kurzer Sprechpause wird automatisch
    // abgesendet (hands-free). Sprachbefehle „stopp"/„absenden" möglich. Analog
    // zum Exposé-Chat (chat/test-expose.html, Expose-Prototyp-P2-Chat.html).
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
      // Mikrofon leuchtet beim Zuhören in der Partner-Akzentfarbe (statt fest
      // RI24-Grün) — bleibt so konsistent mit submitButtonStyles/messageStyles.
      button: { active: { container: { default: { backgroundColor: GREEN } } } }
    };
    chat.htmlClassUtilities = {
      'ri24-starter': {
        events: {
          click: function (event) { chat.submitUserMessage({ text: event.target.textContent.trim() }); }
        },
        styles: {
          default: {
            display: 'block', width: '100%', textAlign: 'left', cursor: 'pointer',
            margin: '6px 0', padding: '10px 12px', borderRadius: '10px',
            border: '1px solid #d7ddd9', backgroundColor: '#fff', color: TEXT_ACCENT_ON_WHITE,
            fontSize: '0.9rem'
          },
          hover: { backgroundColor: GREEN_BG }
        }
      }
    };

    var greeting = advisor && advisor.name
      ? 'Ich bin der Baufinanzierungs-Assistent von <b>' + advisor.name + '</b>' +
        (advisor.title ? ' (' + advisor.title + ')' : '') + '.'
      : 'Ich bin dein Baufinanzierungs-Assistent.';

    chat.introMessage = {
      html:
        '<div style="line-height:1.5">' +
          '<b>👋 Willkommen!</b><br>' + greeting + ' ' +
          'Ich helfe dir, deine Finanzierung durchzurechnen und zu optimieren.' +
          '<div style="margin-top:10px">' +
            '<div class="ri24-starter">Ich möchte eine Immobilienfinanzierung berechnen 🧮</div>' +
            '<div class="ri24-starter">Wie kann ich meine Finanzierung optimieren? 📈</div>' +
            '<div class="ri24-starter">Was ist eine Anschlussfinanzierung? ❓</div>' +
            '<div class="ri24-starter">Ich möchte einen Beratungstermin buchen 📅</div>' +
          '</div>' +
        '</div>'
    };

    return chat;
  }

  function disclosureBar() {
    var bar = document.createElement('div');
    bar.style.cssText =
      'box-sizing:border-box;width:100%;max-width:420px;background:' + GREEN_BG + ';color:#333;' +
      'border:1px solid #e2e5ea;border-bottom:none;border-radius:14px 14px 0 0;' +
      'padding:7px 14px;font-size:.76rem;line-height:1.3;' +
      'font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;';
    bar.textContent = DISCLOSURE_TEXT;
    return bar;
  }

  // Exakte objektArt-Enum-Werte der Europace Vorschläge-API
  // (baufi-passende-vorschlaege-api.yaml, Finanzierungsobjekt.objektArt) — freie
  // Texteingabe würde sonst Werte erzeugen, die createVorschlaege 1:1 unverändert
  // an Europace weiterreicht (kein Mapping/Normalisierung im MCP-Server). GRUNDSTUECK
  // bewusst weggelassen, da in der API-Doku als "deprecated, use BAUGRUNDSTUECK" markiert.
  var OBJEKT_ART_OPTIONS = [
    { value: 'EINFAMILIENHAUS', label: 'Einfamilienhaus' },
    { value: 'ZWEIFAMILIENHAUS', label: 'Zweifamilienhaus' },
    { value: 'MEHRFAMILIENHAUS', label: 'Mehrfamilienhaus' },
    { value: 'REIHENHAUS', label: 'Reihenhaus' },
    { value: 'DOPPELHAUSHAELFTE', label: 'Doppelhaushälfte' },
    { value: 'EIGENTUMSWOHNUNG', label: 'Eigentumswohnung' },
    { value: 'BAUGRUNDSTUECK', label: 'Baugrundstück' }
  ];
  var CALC_INPUT_LABELS = {
    kaufpreis: 'Kaufpreis', kaufnebenkosten: 'Kaufnebenkosten', eigenKapital: 'Eigenkapital',
    plz: 'PLZ', objektArt: 'Objektart', wunschRate: 'Wunschrate', wunschZinsbindung: 'Zinsbindung'
  };
  var CALC_RESULT_LABELS = {
    darlehenssumme: 'Darlehenssumme', rate: 'Monatliche Rate', sollzins: 'Sollzins',
    effektivzins: 'Effektivzins', zinsbindung: 'Zinsbindung', machbarkeit: 'Machbarkeit'
  };
  // Parst einen de-DE-formatierten Geldbetrag ("44.000 €", "44.000,50") zurück
  // in eine Zahl — Punkt = Tausendertrennzeichen, Komma = Dezimaltrennzeichen.
  function parseGermanNumber(str) {
    if (!str) return NaN;
    return parseFloat(String(str).replace(/[€\s]/g, '').replace(/\./g, '').replace(',', '.'));
  }
  // Grobe Kaufnebenkosten-Schätzung (~11% vom Kaufpreis, analog zur nativen
  // Exposé-Seiten-Berechnung aus Grunderwerbsteuer+Notar+Maklerprovision), auf
  // 100 € gerundet. Nur ein Startpunkt — der Nutzer kann den Betrag im
  // Rechner-Panel jederzeit überschreiben (siehe inputTouched in buildCalcPanel),
  // da die tatsächliche Höhe je nach Maklervertrag/Region stark abweichen kann.
  function estimateKaufnebenkosten(kaufpreisStr) {
    var kp = parseGermanNumber(kaufpreisStr);
    if (!kp || isNaN(kp) || kp <= 0) return '';
    return (Math.round(kp * 0.11 / 100) * 100).toLocaleString('de-DE') + ' €';
  }
  // Beispielrechnung, mit der das Panel startet, damit der Rechner nie leer
  // ist, sondern immer eine plausible Berechnung zeigt, bis der Assistent
  // echte Nutzerdaten liefert.
  var DEFAULT_CALC_INPUT = {
    kaufpreis: '400.000 €', kaufnebenkosten: estimateKaufnebenkosten('400.000 €'), eigenKapital: '80.000 €',
    plz: '10115', objektArt: 'EINFAMILIENHAUS', wunschRate: '1.500 €', wunschZinsbindung: '10 Jahre'
  };
  var DEFAULT_CALC_RESULT = {
    darlehenssumme: '320.000 €', rate: '1.465 €', sollzins: '3,49 %',
    effektivzins: '3,55 %', zinsbindung: '10 Jahre', machbarkeit: '✅ Machbar (100/100)'
  };

  // Baut das Rechner-Panel komplett per createElement/closures statt fixer
  // IDs (anders als index.html/embed-snippet.html) — dieses Skript läuft auf
  // beliebigen Partnerseiten ohne Shadow-DOM-Isolation, feste IDs könnten dort
  // mit vorhandenen Elementen der Seite kollidieren.
  function buildCalcPanel(chat) {
    var state = {
      input: Object.assign({}, DEFAULT_CALC_INPUT),
      result: Object.assign({}, DEFAULT_CALC_RESULT)
    };
    var isLive = false;
    var inputFields = {};
    // Merkt sich pro Feld, ob der Nutzer es manuell bearbeitet hat — nur so lange
    // NICHT gesetzt, wird "kaufnebenkosten" bei neuen Kaufpreis-Werten aus dem
    // Chat automatisch neu geschätzt (siehe updateCalcInput weiter unten). Nach
    // der ersten manuellen Änderung hat der Nutzer-Wert immer Vorrang.
    var inputTouched = {};

    var root = document.createElement('div');
    root.style.cssText =
      'width:100%;max-width:420px;box-sizing:border-box;background:#fff;border:1px solid #e2e5ea;' +
      'border-radius:14px;padding:18px 20px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;';

    var heading = document.createElement('h2');
    heading.textContent = '💰 Finanzierungsrechner';
    heading.style.cssText = 'margin:0 0 4px;font-size:1rem;color:#333;';

    var placeholder = document.createElement('p');
    placeholder.textContent = 'Beispielrechnung – aktualisiert sich automatisch, sobald du dem Assistenten deine Daten nennst.';
    placeholder.style.cssText = 'font-size:.85rem;color:#667;margin:8px 0 0;';

    var inputHeading = document.createElement('h3');
    inputHeading.textContent = 'Deine Eingaben';
    var sectionHeadingCss = 'margin:0 0 8px;font-size:.78rem;text-transform:uppercase;letter-spacing:.03em;color:#667;font-weight:700;';
    inputHeading.style.cssText = sectionHeadingCss;
    var inputRows = document.createElement('div');
    var recalcBtn = document.createElement('button');
    recalcBtn.type = 'button';
    recalcBtn.textContent = 'Neu berechnen ↻';
    recalcBtn.style.cssText =
      'margin-top:10px;width:100%;padding:8px 10px;border:none;border-radius:8px;font-family:inherit;' +
      'background:' + GREEN + ';color:' + TEXT_ON_ACCENT + ';font-size:.85rem;font-weight:600;cursor:pointer;';
    recalcBtn.addEventListener('mouseenter', function () { recalcBtn.style.background = GREEN_DARK; });
    recalcBtn.addEventListener('mouseleave', function () { recalcBtn.style.background = GREEN; });

    var statusEl = document.createElement('p');
    statusEl.style.cssText = 'font-size:.78rem;color:#946200;margin:8px 0 0;display:none;';

    var inputSection = document.createElement('div');
    inputSection.style.cssText = 'margin-top:16px;';
    inputSection.appendChild(inputHeading);
    inputSection.appendChild(inputRows);
    inputSection.appendChild(recalcBtn);
    inputSection.appendChild(statusEl);

    var resultHeading = document.createElement('h3');
    resultHeading.textContent = 'Ergebnis';
    resultHeading.style.cssText = sectionHeadingCss;
    var resultRows = document.createElement('div');
    // Platzsparend: Ergebnis-Block bleibt eingeklappt, bis markLive() ihn
    // aufklappt (erster "Neu berechnen"-Klick ODER erste Chat-Berechnung).
    var resultSection = document.createElement('div');
    resultSection.style.cssText = 'margin-top:16px;display:none;';
    resultSection.appendChild(resultHeading);
    resultSection.appendChild(resultRows);

    root.appendChild(heading);
    root.appendChild(placeholder);
    root.appendChild(inputSection);
    root.appendChild(resultSection);

    function calcRow(label, value) {
      var row = document.createElement('div');
      row.style.cssText = 'display:flex;justify-content:space-between;gap:12px;padding:6px 0;border-bottom:1px solid #eef1f0;font-size:.88rem;';
      var labelSpan = document.createElement('span');
      labelSpan.textContent = label;
      labelSpan.style.cssText = 'font-weight:400;color:#555;';
      var valueSpan = document.createElement('span');
      valueSpan.textContent = value;
      valueSpan.style.cssText = 'font-weight:700;color:#111;text-align:right;';
      row.appendChild(labelSpan);
      row.appendChild(valueSpan);
      return row;
    }

    function renderResultRows() {
      resultRows.innerHTML = '';
      Object.keys(CALC_RESULT_LABELS).forEach(function (key) {
        if (!state.result[key]) return;
        resultRows.appendChild(calcRow(CALC_RESULT_LABELS[key], state.result[key]));
      });
      if (resultRows.lastElementChild) resultRows.lastElementChild.style.borderBottom = 'none';
    }

    function renderInputRows() {
      inputRows.innerHTML = '';
      inputFields = {};
      Object.keys(CALC_INPUT_LABELS).forEach(function (key) {
        var row = document.createElement('div');
        row.style.cssText = 'display:flex;justify-content:space-between;gap:12px;padding:6px 0;border-bottom:1px solid #eef1f0;font-size:.88rem;';
        var labelSpan = document.createElement('span');
        labelSpan.textContent = CALC_INPUT_LABELS[key];
        labelSpan.style.cssText = 'font-weight:400;color:#555;';

        var field;
        if (key === 'objektArt') {
          field = document.createElement('select');
          OBJEKT_ART_OPTIONS.forEach(function (opt) {
            var optEl = document.createElement('option');
            optEl.value = opt.value;
            optEl.textContent = opt.label;
            field.appendChild(optEl);
          });
        } else {
          field = document.createElement('input');
          field.type = 'text';
          field.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); submitCalcToChat(); }
          });
          field.addEventListener('input', function () { inputTouched[key] = true; });
        }
        field.style.cssText =
          'width:55%;padding:3px 6px;border:1px solid #ccd2cf;border-radius:6px;box-sizing:border-box;' +
          'font-size:inherit;font-weight:700;color:#111;text-align:right;font-family:inherit;';
        field.addEventListener('focus', function () { field.style.outline = '2px solid ' + GREEN_DARK; field.style.outlineOffset = '1px'; });
        field.addEventListener('blur', function () { field.style.outline = 'none'; });
        field.value = state.input[key] || '';
        inputFields[key] = field;

        row.appendChild(labelSpan);
        row.appendChild(field);
        inputRows.appendChild(row);
      });
      if (inputRows.lastElementChild) inputRows.lastElementChild.style.borderBottom = 'none';
    }

    // Aktualisiert nur die .value der bestehenden Felder (statt sie neu zu
    // erzeugen) — sonst würde ein Chat-Update mitten in der Eingabe den Fokus
    // und die Cursor-Position im Feld zerstören.
    function updateInputFieldValues() {
      Object.keys(CALC_INPUT_LABELS).forEach(function (key) {
        var field = inputFields[key];
        // inputTouched-Check verhindert insbesondere, dass ein manuell editiertes
        // Eigenkapital-Feld nach einer Kaufnebenkosten-Verrechnung durch den bereits
        // verrechneten (Netto-)Wert aus dem Tool-Aufruf überschrieben wird — das würde
        // bei einem zweiten "Neu berechnen"-Klick sonst zu einer doppelten Abzugsrechnung
        // führen (siehe system-prompt-baufinanzierung.md, Abschnitt "Kaufnebenkosten").
        if (!field || document.activeElement === field || inputTouched[key]) return;
        var value = state.input[key] || '';
        // Falls der Assistent (Chat → Rechner) einen objektArt-Wert liefert,
        // der nicht im Europace-Enum steckt, Wert trotzdem sichtbar machen
        // statt ihn stillschweigend auf die erste Option zu verwerfen.
        if (key === 'objektArt' && value && !OBJEKT_ART_OPTIONS.some(function (opt) { return opt.value === value; })) {
          var extra = document.createElement('option');
          extra.value = value;
          extra.textContent = value;
          field.appendChild(extra);
        }
        field.value = value;
      });
    }

    function markLive() {
      if (isLive) return;
      isLive = true;
      placeholder.textContent = 'Deine aktuelle Berechnung:';
      resultSection.style.display = '';
    }

    // Gesetzt zwischen einem "Neu berechnen"-Klick und dem Ende der Chat-Antwort
    // (siehe handleTurnWithoutCalc im zurückgegebenen Objekt) — hält fest, was vor
    // dem Versuch galt, damit ein Zurückrollen möglich ist, falls der Assistent
    // statt zu rechnen eine Rückfrage stellt (z.B. fehlende Pflichtangaben wie
    // Geburtsdatum/Einkommen) und daher NIE ein calc_result-Event eintrifft — ohne
    // dieses Tracking blieben die "…"-Platzhalter sonst für immer stehen.
    var pendingCalcSubmit = null;

    // Liest die aktuellen Eingabefelder aus und schickt sie als normale
    // Nutzer-Nachricht an den Chat (Rechner → Chat) — der Assistent berechnet
    // darüber via createVorschlaege/getVorschlaege neu, das Ergebnis kommt wie
    // gewohnt per SSE (calc_result) zurück in dieses Panel.
    function submitCalcToChat() {
      Object.keys(CALC_INPUT_LABELS).forEach(function (key) {
        var field = inputFields[key];
        if (field) state.input[key] = field.value.trim();
      });
      pendingCalcSubmit = { wasLiveBefore: isLive, previousResult: Object.assign({}, state.result) };
      statusEl.style.display = 'none';
      markLive();
      // Ergebnis-Felder sofort auf "wird berechnet…" zurücksetzen, statt das
      // alte (jetzt nicht mehr zu den neuen Eingaben passende) Ergebnis stehen
      // zu lassen, bis die Antwort (calc_result per SSE) eintrifft.
      Object.keys(CALC_RESULT_LABELS).forEach(function (key) { state.result[key] = '…'; });
      renderResultRows();
      var parts = Object.keys(CALC_INPUT_LABELS)
        .filter(function (key) { return state.input[key]; })
        .map(function (key) { return CALC_INPUT_LABELS[key] + ': ' + state.input[key]; });
      chat.submitUserMessage({
        text: 'Bitte neu berechnen mit diesen Angaben — ' + parts.join(', ') + '.'
      });
    }
    recalcBtn.addEventListener('click', submitCalcToChat);

    renderInputRows();
    renderResultRows();

    return {
      root: root,
      // Höhe im eingeklappten Zustand ("Deine Eingaben", Ergebnis noch
      // versteckt) — funktioniert nur, wenn root bereits im (sichtbaren) DOM
      // hängt, siehe mountInline/mountBubble.
      getCollapsedHeight: function () { return root.getBoundingClientRect().height; },
      updateCalcInput: function (data) {
        markLive();
        Object.assign(state.input, data);
        // Kaufnebenkosten-Schätzung nur nachziehen, solange der Nutzer das Feld
        // noch nicht selbst angefasst hat — danach hat sein manueller Wert Vorrang.
        if (data.kaufpreis && !inputTouched.kaufnebenkosten) {
          state.input.kaufnebenkosten = estimateKaufnebenkosten(data.kaufpreis);
        }
        updateInputFieldValues();
      },
      updateCalcResult: function (data) {
        // Bestätigtes Ergebnis eingetroffen — ein evtl. laufender "wartet-auf-
        // Ergebnis"-Zustand aus submitCalcToChat ist damit erledigt.
        pendingCalcSubmit = null;
        statusEl.style.display = 'none';
        markLive();
        Object.assign(state.result, data);
        renderResultRows();
      },
      // Wird aufgerufen, wenn die Chat-Antwort komplett durchgelaufen ist, OHNE
      // dass dabei ein calc_result-Event kam — z.B. weil der Assistent statt zu
      // rechnen nach fehlenden Pflichtangaben gefragt hat. Rollt die "wird
      // berechnet…"-Platzhalter zurück, statt sie dauerhaft stehen zu lassen.
      handleTurnWithoutCalc: function () {
        if (!pendingCalcSubmit) return;
        var pending = pendingCalcSubmit;
        pendingCalcSubmit = null;
        if (!pending.wasLiveBefore) {
          // Allererster Versuch war verfrüht — Aufklapp-Zustand wieder
          // zurücknehmen, statt Beispielwerte als "Deine aktuelle Berechnung"
          // auszugeben.
          isLive = false;
          placeholder.textContent = 'Beispielrechnung – aktualisiert sich automatisch, sobald du dem Assistenten deine Daten nennst.';
          resultSection.style.display = 'none';
        }
        state.result = pending.previousResult;
        renderResultRows();
        statusEl.textContent = 'ℹ️ Der Assistent hat noch eine Rückfrage — bitte im Chat antworten.';
        statusEl.style.display = '';
      }
    };
  }

  // Fügt den fertigen Widget-Wurzelknoten (Wrapper-Div) an EINER Stelle ein:
  // 1. explizites Ziel-Element per `elementID` (nötig für async/defer, siehe
  //    ELEMENT_ID oben), 2. direkt hinter dem eigenen <script>-Tag (nur bei
  //    synchronem Laden zuverlässig), 3. Fallback ans Ende von <body>.
  function insertWidgetRoot(node) {
    var container = ELEMENT_ID ? document.getElementById(ELEMENT_ID) : null;
    if (ELEMENT_ID && !container) {
      console.error('[RI24 Baufi Widget] elementID "' + ELEMENT_ID + '" nicht im DOM gefunden — falle auf Standard-Einfügepunkt zurück.');
    }
    if (container) {
      container.appendChild(node);
    } else if (insertionPoint && insertionPoint.parentNode) {
      insertionPoint.insertAdjacentElement('afterend', node);
    } else {
      document.body.appendChild(node);
    }
  }

  function mountInline(chat, calcController) {
    if (!calcController) {
      // Variante "nur Chat" (calcPosition: 'none') — einfache Einbindung ohne
      // Rechner-Panel/Stack, feste Standardhöhe wie vor Einführung des Panels.
      chat.style =
        'display:block;border-radius:0 0 14px 14px;border:1px solid #e2e5ea;border-top:none;' +
        'width:100%;max-width:420px;height:600px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;';
      var onlyChatWrap = document.createElement('div');
      onlyChatWrap.appendChild(disclosureBar());
      onlyChatWrap.appendChild(chat);
      insertWidgetRoot(onlyChatWrap);
      return;
    }

    // Chat + Rechner-Panel gestapelt (Reihenfolge je CALC_POSITION), analog zu
    // embed-snippet.html/index.html — freier Seitenfluss, daher lässt sich die
    // Chat-Höhe direkt nach dem Einfügen an die (eingeklappte) Rechner-Höhe
    // anpassen (siehe unten).
    var stack = document.createElement('div');
    stack.style.cssText =
      'display:flex;flex-direction:column;gap:16px;width:100%;max-width:420px;' +
      'font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;';

    var chatCol = document.createElement('div');
    chatCol.appendChild(disclosureBar());
    chatCol.appendChild(chat);

    if (CALC_POSITION === 'below') {
      stack.appendChild(chatCol);
      stack.appendChild(calcController.root);
    } else {
      stack.appendChild(calcController.root);
      stack.appendChild(chatCol);
    }

    insertWidgetRoot(stack);

    // Höhe des Rechner-Panels im eingeklappten Zustand einmalig messen — wird
    // als feste Chat-Höhe verwendet, damit beide Elemente gleich hoch wirken,
    // auch nachdem der Rechner nach der ersten Berechnung aufklappt (Chat-
    // Höhe bleibt dabei unverändert). Muss NACH dem Einfügen ins DOM erfolgen,
    // sonst liefert getBoundingClientRect() 0.
    var collapsedHeight = calcController.getCollapsedHeight();
    chat.style =
      'display:block;border-radius:0 0 14px 14px;border:1px solid #e2e5ea;border-top:none;' +
      'width:100%;max-width:420px;height:' + collapsedHeight + 'px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;';
  }

  function mountBubble(chat, advisor, calcController) {
    // display:block nötig: <deep-chat> ist per Default display:table-cell,
    // worauf height:100% nicht wie bei einem Block-Element auf die volle
    // Höhe des Flex-Containers skaliert (sonst bleibt der Chat zu niedrig
    // und es entsteht eine Lücke zwischen Eingabefeld und Panel-Unterkante).
    // Anders als bei mountInline bekommt der Chat hier KEINE an die
    // Rechner-Höhe angeglichene feste Höhe: Das Bubble-Panel hat eine feste
    // Gesamthöhe (min(600px,80vh)); der Chat füllt darin per flex:1 1 auto
    // einfach den nach Abzug von Header + Rechner verbleibenden Platz. Eine
    // Messung wie bei mountInline würde hier ohnehin 0 liefern, weil das
    // Panel bis zum ersten Öffnen display:none ist.
    chat.style = 'display:block;border:none;width:100%;flex:1 1 auto;min-height:160px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;';

    var panel = document.createElement('div');
    panel.setAttribute('aria-hidden', 'true');
    panel.style.cssText =
      'position:fixed;z-index:2147483000;bottom:96px;right:20px;width:380px;max-width:92vw;' +
      'height:min(600px,80vh);background:#fff;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.22);' +
      'display:none;flex-direction:column;overflow:hidden;';

    var header = document.createElement('div');
    header.style.cssText =
      'display:flex;align-items:center;gap:10px;padding:12px 14px;background:' + GREEN + ';color:' + TEXT_ON_ACCENT + ';' +
      'font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;flex:0 0 auto;';
    header.innerHTML =
      avatarMarkup(advisor, 32, '.8rem', 'rgba(0,0,0,.12)') +
      '<div style="flex:1 1 auto;min-width:0;">' +
        '<div style="font-weight:600;font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' +
          'Baufinanzierungs-Assistent' +
        '</div>' +
        (advisor && advisor.name
          ? '<div style="font-size:.78rem;opacity:.85;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + advisor.name + '</div>'
          : '') +
        '<div style="font-size:.7rem;opacity:.85;margin-top:2px;">' + DISCLOSURE_TEXT + '</div>' +
      '</div>';
    var closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.setAttribute('aria-label', 'Chat schließen');
    closeBtn.innerHTML = '✕';
    closeBtn.style.cssText =
      'background:transparent;border:none;color:' + TEXT_ON_ACCENT + ';font-size:1.1rem;cursor:pointer;padding:4px 6px;flex:0 0 auto;line-height:1;';
    header.appendChild(closeBtn);

    // Rechner behält seine natürliche (Inhalts-)Höhe, der Chat bekommt den
    // restlichen Platz (flex:1 1 auto, siehe oben) — bei sehr viel Inhalt
    // (Rechner aufgeklappt + langer Chatverlauf) scrollt body als Ganzes,
    // statt dass etwas über den Panel-Rand hinausragt.
    var body = document.createElement('div');
    body.style.cssText = 'flex:1 1 auto;min-height:0;display:flex;flex-direction:column;overflow-y:auto;';
    if (!calcController) {
      // Variante "nur Chat" (calcPosition: 'none') — Chat füllt body allein.
      body.appendChild(chat);
    } else {
      calcController.root.style.flex = '0 0 auto';
      if (CALC_POSITION === 'below') {
        body.appendChild(chat);
        body.appendChild(calcController.root);
      } else {
        body.appendChild(calcController.root);
        body.appendChild(chat);
      }
    }

    panel.appendChild(header);
    panel.appendChild(body);

    var launcher = document.createElement('button');
    launcher.type = 'button';
    launcher.setAttribute('aria-label', 'Chat öffnen');
    launcher.setAttribute('aria-expanded', 'false');
    launcher.style.cssText =
      'position:fixed;z-index:2147483000;bottom:20px;right:20px;width:60px;height:60px;border-radius:50%;' +
      'background:' + GREEN + ';color:' + TEXT_ON_ACCENT + ';border:none;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,.25);' +
      'display:flex;align-items:center;justify-content:center;padding:0;overflow:hidden;';
    launcher.innerHTML = avatarMarkup(advisor, 60, '26px', 'transparent');

    var open = false;
    function setOpen(next) {
      open = next;
      panel.style.display = open ? 'flex' : 'none';
      panel.setAttribute('aria-hidden', open ? 'false' : 'true');
      launcher.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    launcher.addEventListener('click', function () { setOpen(!open); });
    closeBtn.addEventListener('click', function () { setOpen(false); });

    document.body.appendChild(panel);
    document.body.appendChild(launcher);

    // 'open' (Feldname des älteren Widget-Baukastens): Panel direkt beim
    // Laden aufklappen statt auf den ersten Klick zu warten.
    if (START_OPEN) setOpen(true);
  }

  ensureDeepChat(function () {
    fetchAdvisor().then(function (advisor) {
      // calcController wird erst nach buildChatElement() gebaut (braucht die
      // fertige chat-Instanz für den "Neu berechnen"-Button), chat.connect
      // referenziert es aber schon jetzt per Closure — unproblematisch, da
      // der Handler erst bei der ersten Nutzer-Nachricht aufgerufen wird,
      // also lange nachdem calcController zugewiesen ist. Bleibt bei
      // calcPosition:'none' dauerhaft null (reine Chat-Variante ohne Panel) —
      // die drei Callbacks unten prüfen das jeweils ab.
      var calcController;
      var chat = buildChatElement(
        advisor,
        function (data) { if (calcController) calcController.updateCalcInput(data); },
        function (data) { if (calcController) calcController.updateCalcResult(data); },
        function () { if (calcController) calcController.handleTurnWithoutCalc(); }
      );
      calcController = CALC_POSITION === 'none' ? null : buildCalcPanel(chat);

      if (MODE === 'inline') {
        mountInline(chat, calcController);
      } else {
        mountBubble(chat, advisor, calcController);
      }
    });
  });
})();
