// Native fetch is available in Node 18+

export interface ContactFormParams {
  expose_url: string;
  oid: string;
  vorname: string;
  nachname: string;
  email: string;
  telefon?: string;
  strasse?: string;
  plz?: string;
  ort?: string;
  nachricht?: string;
  rueckruf?: boolean;
  besichtigung?: boolean;
  info?: boolean;
  finanzierung?: boolean;
}

export interface ContactFormResult {
  success: boolean;
  message: string;
}

export async function submitContactForm(params: ContactFormParams): Promise<ContactFormResult> {
  console.log(`[contact] Sende Kontaktanfrage via internem Endpunkt für: ${params.expose_url} (oid=${params.oid})`);

  // Das Backend ist eine klassische PHP-$_POST-Route und erwartet
  // application/x-www-form-urlencoded, nicht JSON.
  const body = new URLSearchParams();
  body.set("ioi", params.oid);
  body.set("refritrack", "expose");
  body.set("vorname", params.vorname);
  body.set("nachname", params.nachname);
  body.set("email", params.email);
  if (params.telefon) body.set("telefon", params.telefon);
  if (params.strasse) body.set("strasse_name_nr", params.strasse);
  if (params.plz) body.set("plz", params.plz);
  if (params.ort) body.set("ort", params.ort);
  if (params.rueckruf) body.set("rueckruf", "1");
  if (params.besichtigung) body.set("besichtigung", "1");
  if (params.info) body.set("info", "1");

  if (params.finanzierung) body.set("zinsangebot", "1");
  const nachricht = params.finanzierung
    ? `${params.nachricht ? params.nachricht + " " : ""}Kostenfreien Finanzierungsvergleich gewünscht.`
    : params.nachricht;
  if (nachricht) body.set("nachricht", nachricht);

  try {
    const response = await fetch("https://www.regionalimmobilien24.de/api/request/chatbot/contact/immo/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest"
      },
      body: body.toString()
    });
    
    let text = await response.text();
    let data: any = {};
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text.substring(0, 500) };
    }
    console.log(`[contact] Body gesendet: ${body.toString()}`);
    console.log(`[contact] Antwort HTTP ${response.status}: ${text.substring(0, 500)}`);

    if (response.ok && data.status !== false) {
      console.log('[contact] ✅ Kontaktanfrage erfolgreich gesendet!');
      return {
        success: true,
        message: `Ihre Kontaktanfrage wurde erfolgreich an den Anbieter gesendet! Eine Bestätigung geht an ${params.email}.`
      };
    } else {
      console.warn(`[contact] ❌ API-Fehler: ${data.msg || response.statusText}`);
      return {
        success: false,
        message: `Die Kontaktanfrage konnte nicht gesendet werden: ${data.msg || response.statusText}. Bitte kontaktieren Sie den Anbieter direkt.`
      };
    }
  } catch (error) {
    console.error(`[contact] Fehler beim Senden: ${error}`);
    return {
      success: false,
      message: `Netzwerkfehler beim Senden der Anfrage: ${String(error)}`
    };
  }
}

// ── Finanzierungsanfrage ─────────────────────────────────────────────────
// Geht über den dedizierten Chatbot-API-Endpunkt direkt an den
// Finanzierungsberater des Teams (team_id), das dem Objekt (ioi) zugeordnet
// ist. team_id wird - wie expose_url - vom aufrufenden System übergeben.

export interface FinancingRequestParams {
  oid: string;
  teamId: string;
  vorname: string;
  nachname: string;
  email: string;
  telefon: string;
  betreff?: string;
  finanzDs: string;
  finanzWr: string;
  finanzZb: string;
}

export async function submitFinancingForm(params: FinancingRequestParams): Promise<ContactFormResult> {
  console.log(`[financing] Sende Finanzierungsanfrage (ioi=${params.oid}, team_id=${params.teamId})`);

  const body = new URLSearchParams();
  body.set("ioi", params.oid);
  body.set("refritrack", "expose");
  if (params.betreff) body.set("betreff", params.betreff);
  body.set("vorname", params.vorname);
  body.set("nachname", params.nachname);
  body.set("email", params.email);
  body.set("telefon", params.telefon);
  body.set("finanz_ds", params.finanzDs);
  body.set("finanz_wr", params.finanzWr);
  body.set("finanz_zb", params.finanzZb);
  body.set("team_id", params.teamId);

  try {
    const response = await fetch("https://www.regionalimmobilien24.de/api/request/chatbot/finance/immo/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest"
      },
      body: body.toString()
    });

    const text = await response.text();
    let data: any = {};
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text.substring(0, 500) };
    }
    console.log(`[financing] Body gesendet: ${body.toString()}`);
    console.log(`[financing] Antwort HTTP ${response.status}: ${text.substring(0, 500)}`);

    // "status" ist laut API-Doku unzuverlässig (bleibt teils true bei Fehlern);
    // "is_finance" zeigt an, ob die Finanzierungsanfrage tatsächlich angelegt wurde.
    if (response.ok && data.is_finance === true) {
      console.log('[financing] ✅ Finanzierungsanfrage erfolgreich gesendet!');
      return {
        success: true,
        message: `Ihre Finanzierungsanfrage wurde erfolgreich an den Finanzierungsberater gesendet! Eine Bestätigung geht an ${params.email}.`
      };
    } else {
      console.warn(`[financing] ❌ API-Fehler: ${data.msg || response.statusText}`);
      return {
        success: false,
        message: `Die Finanzierungsanfrage konnte nicht gesendet werden: ${data.msg || response.statusText}.`
      };
    }
  } catch (error) {
    console.error(`[financing] Fehler beim Senden: ${error}`);
    return {
      success: false,
      message: `Netzwerkfehler beim Senden der Finanzierungsanfrage: ${String(error)}`
    };
  }
}
