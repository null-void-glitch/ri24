# Onboarding two WhatsApp Business App numbers via Coexistence (Embedded Signup)

> **Goal:** connect two numbers that currently live in the **WhatsApp Business App** to your
> **existing Cloud API WABA** using **Coexistence**, so that:
> - chat history is preserved (up to ~6 months imported, new chats sync both ways),
> - the WhatsApp Business App on the phone keeps working,
> - your automation can send at scale via the Cloud API.
>
> This is the **recommended** route and replaces the self-service "delete + re-register" flow
> (which would sever the app and lose history — kept only as a fallback at the bottom).

---

## Billing model (why coexistence)

| Sent from | Billed? |
|---|---|
| **WhatsApp Business App** (the physical phone) | **Free** |
| **Cloud API** (your automation) | Charged — Meta per-message pricing, by template category & country |

There is **no separate platform fee** for coexistence itself. So: human one-to-one replies from the
phone stay free; automated/template sends through the API are billed. (See research notes / sources below.)

---

## How coexistence onboarding actually works

Unlike the self-service flow, there is **no `request_code` / `verify_code` / `register` and no new PIN**.
Instead the number's owner authorizes coexistence by **scanning a QR code in the WhatsApp Business App**
during a Meta-hosted **Embedded Signup** popup. The flow is:

```
[Your web page]  --FB.login(config_id, featureType: whatsapp_business_app_onboarding)-->  [Meta popup]
        |                                                                                      |
        |   user picks Business Portfolio + the app number, scans QR in WhatsApp Business App  |
        |                                                                                      |
        |<-- popup posts session-info { waba_id, phone_number_id } + returns OAuth `code` ------|
        v
[Your backend /install]:  code --> business access token  -->  POST /<WABA_ID>/subscribed_apps
                          -->  read phone status  -->  done (app stays connected)
```

---

## Prerequisites (one-time)

- [ ] A **Meta app** (Business type) with **WhatsApp** product added.
- [ ] **Facebook Login for Business** configured for WhatsApp Embedded Signup → gives you a
      **configuration id** (`META_CONFIG_ID`).
- [ ] App has advanced access to **`whatsapp_business_management`**, **`whatsapp_business_messaging`**,
      and **`business_management`** (App Review may be required to onboard numbers you don't own;
      for your own business this is typically fine in dev/standard access during testing).
- [ ] You are set up as a **Tech Provider / Solution Partner** (coexistence onboarding requires it).
- [ ] A **webhook callback URL + verify token** configured on the app (for inbound messages).
- [ ] The domain serving the onboarding page is **allow-listed** in the Login-for-Business config
      (Meta requires HTTPS for real onboarding — use a tunnel like a public HTTPS dev domain).
- [ ] `META_APP_ID`, `META_APP_SECRET`, `META_CONFIG_ID` to hand (see `.env.example`).

## Prerequisites (per number — both of yours)

- [ ] Number is active in the **WhatsApp Business App** and you have the phone to scan the QR.
- [ ] Number is **not** a WhatsApp test number.
- [ ] (No 2-step PIN disable needed and no history backup needed — coexistence preserves both.)

---

## Run it (per number — repeat for the second)

```bash
cp .env.example .env          # fill META_APP_ID / META_APP_SECRET / META_CONFIG_ID
python3 coexistence_server.py # serves the page + handles the code exchange
# open the allow-listed HTTPS URL (or http://localhost:8080 for a local dry run)
```

1. Click **Connect with Facebook**, log in with the account that owns the business.
2. Select your **Business Portfolio** and the number that's on the WhatsApp Business App.
3. On the phone: **WhatsApp Business App → Settings → Linked devices / scan QR**, scan the popup's QR.
4. Wait for **Success** on the page. The backend has: exchanged the code for a token, subscribed your
   app to the WABA's webhooks, and read back the phone status (logged server-side).
5. **Repeat for the second number** (the API has no bulk onboarding).

## Post-onboarding verification

- [ ] Server log shows `"success": true` and `phone_status.platform_type` reflects Cloud API.
- [ ] Send a **test template** via the Cloud API to a known number.
- [ ] Send a normal reply **from the phone app** and confirm it appears in your API webhook (sync works).
- [ ] Confirm inbound customer messages hit your webhook endpoint.
- [ ] Securely persist the **business access token** + `waba_id` + `phone_number_id` per number.

## Notes & gotchas

- Coexistence imports up to ~6 months of one-to-one history; **group chats are not supported** via API.
- Keep human one-to-one replies in the **app** to stay free; push templates/automation via the **API**.
- The `featureType` value in `coexistence_onboard.html`
  (`whatsapp_business_app_onboarding`) is the coexistence flag — **confirm the exact current
  string against Meta's "Onboarding WhatsApp Business app users" doc and your Login config**, since
  Meta iterates on Embedded Signup parameters frequently.
- Token returned by the code exchange is long-lived but treat it as rotatable; store it server-side only.

---

## Files

| File | Purpose |
|---|---|
| `coexistence_onboard.html` | Embedded Signup front-end (FB.login + QR + session-info capture). |
| `coexistence_server.py` | Stdlib backend: serves the page, exchanges `code`→token, subscribes app to webhooks, reads phone status. |
| `.env.example` | Config template. |
| `migrate_number.py` | **Fallback only** — self-service flow (severs app, loses history). |

---

## Fallback: self-service flow (NOT recommended here)

`migrate_number.py` implements the Cloud API "delete + re-register" flow
(`add` → `request_code` → `verify_code` → `register` with a new PIN). Use it **only** if you decide
you don't need to preserve chat history or keep the WhatsApp Business App working for a number.
Running its `register` step **disconnects the number from the app and the history is lost**.

---

## Sources
- [Onboarding WhatsApp Business app users — "Coexistence" (Meta)](https://developers.facebook.com/docs/whatsapp/embedded-signup/custom-flows/onboarding-business-app-users/)
- [Embedded Signup overview & implementation (Meta)](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/overview/)
- [Pricing on the WhatsApp Business Platform (Meta)](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing)
- [WhatsApp Coexistence billing — app messages free, API charged (360dialog)](https://docs.360dialog.com/docs/resources/phone-numbers/coexistence.md)
- [Embedded Signup implementation reference (Bird)](https://docs.bird.com/api/channels-api/supported-channels/programmable-whatsapp/whatsapp-isv-integration/whatsapp-channel-onboarding/setting-up-the-whatsapp-embedded-flow)
