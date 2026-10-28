// Native fetch is available in Node 18+

export interface ContactFormParams {
  expose_url: string;
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
  console.log(`[contact] Sende Kontaktanfrage via internem Endpunkt für: ${params.expose_url}`);
  
  try {
    const response = await fetch("https://www.regionalimmobilien24.de/api/request/chatbot/contact/immo/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      },
      body: JSON.stringify(params)
    });
    
    let text = await response.text();
    let data: any = {};
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text.substring(0, 500) };
    }

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
