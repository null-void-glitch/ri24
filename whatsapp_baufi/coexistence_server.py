#!/usr/bin/env python3
"""
Backend for WhatsApp Coexistence onboarding via Embedded Signup.

Coexistence connects an EXISTING WhatsApp Business App number to the Cloud API WITHOUT
disconnecting the app or losing chat history. The end-user scans a QR code in their
WhatsApp Business App during the popup; there is NO request_code / verify_code / register
step and NO new PIN (that is the self-service flow, which severs the app — see migrate_number.py).

What this server does:
  1. Serves coexistence_onboard.html (the Embedded Signup front-end) with APP_ID/CONFIG_ID injected.
  2. Handles POST /install with { code, waba_id, phone_number_id } from the front-end:
       a. Exchanges the OAuth `code` for a long-lived business access token.
       b. Subscribes your app to webhooks for the WABA  (POST /<WABA_ID>/subscribed_apps).
       c. Reads back the phone number's status so you can confirm it's connected.
     It DOES NOT call /register (coexistence keeps the app alive).

Config (env or .env in the working dir):
  META_APP_ID         your Meta app id           (public; injected into the page)
  META_APP_SECRET     your Meta app secret        (server-side only; NEVER sent to the browser)
  META_CONFIG_ID      Facebook Login for Business configuration id (public; injected into the page)
  GRAPH_VERSION       default v25.0
  PORT                default 8080

Run:
  python3 coexistence_server.py
  # open http://localhost:8080  (the domain must be allow-listed in your Meta app's
  # Facebook Login for Business settings; use a tunnel/HTTPS domain for real onboarding)

Stdlib only — no dependencies.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coexistence_onboard.html")


def load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def cfg(name, default=None, required=False):
    val = os.environ.get(name, default)
    if required and not val:
        sys.exit(f"ERROR: {name} is not set (env or .env).")
    return val


def graph_base():
    return f"https://graph.facebook.com/{cfg('GRAPH_VERSION', 'v25.0')}"


def _request(method, path, params):
    url = f"{graph_base()}/{path}"
    params = {k: v for k, v in params.items() if v is not None}
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, method="GET")
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() or "{}"
        try:
            return {"_http_error": e.code, **json.loads(body)}
        except json.JSONDecodeError:
            return {"_http_error": e.code, "raw": body}


def exchange_code(code):
    """Step a: swap the short-lived OAuth code for a business access token."""
    return _request("GET", "oauth/access_token", {
        "client_id": cfg("META_APP_ID", required=True),
        "client_secret": cfg("META_APP_SECRET", required=True),
        "code": code,
    })


def subscribe_app(waba_id, token):
    """Step b: subscribe your app to webhooks for the WABA."""
    return _request("POST", f"{waba_id}/subscribed_apps", {"access_token": token})


def phone_status(phone_number_id, token):
    """Step c: read back the phone number's connection/verification status."""
    return _request("GET", f"{phone_number_id}", {
        "fields": "id,display_phone_number,verified_name,code_verification_status,"
                  "name_status,platform_type,quality_rating",
        "access_token": token,
    })


def do_install(payload):
    code = payload.get("code")
    waba_id = payload.get("waba_id")
    phone_number_id = payload.get("phone_number_id")
    if not (code and waba_id):
        return {"success": False, "error": "missing code or waba_id", "payload": payload}

    token_resp = exchange_code(code)
    token = token_resp.get("access_token")
    if not token:
        return {"success": False, "step": "exchange_code", "response": token_resp}

    sub = subscribe_app(waba_id, token)
    if not sub.get("success"):
        return {"success": False, "step": "subscribe_app", "response": sub,
                "note": "token obtained; webhook subscription failed"}

    status = phone_status(phone_number_id, token) if phone_number_id else {}
    return {
        "success": True,
        "waba_id": waba_id,
        "phone_number_id": phone_number_id,
        "subscribed": sub,
        "phone_status": status,
        "note": "Store the access_token securely server-side. Coexistence active; "
                "app messages remain free, Cloud API messages are billed.",
        # Do NOT echo the token to the browser in production; logged server-side only.
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/index.html"):
            return self._send(404, {"error": "not found"})
        with open(HTML_FILE, encoding="utf-8") as fh:
            html = fh.read()
        html = (html
                .replace("{{APP_ID}}", cfg("META_APP_ID", required=True))
                .replace("{{CONFIG_ID}}", cfg("META_CONFIG_ID", required=True))
                .replace("{{GRAPH_VERSION}}", cfg("GRAPH_VERSION", "v25.0")))
        self._send(200, html.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/install":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length).decode() or "{}")
        except json.JSONDecodeError:
            return self._send(400, {"success": False, "error": "invalid JSON"})
        result = do_install(payload)
        # Server-side log (full detail incl. token stays here, not in the browser):
        print(json.dumps({"install_result": {**result}}, indent=2), flush=True)
        # Strip nothing extra here since do_install already omits the token from its return.
        self._send(200, result)

    def log_message(self, *a):
        pass  # quiet default access logging


def main():
    load_dotenv()
    cfg("META_APP_ID", required=True)
    cfg("META_APP_SECRET", required=True)
    cfg("META_CONFIG_ID", required=True)
    port = int(cfg("PORT", "8080"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Coexistence onboarding server on http://localhost:{port}  (Ctrl-C to stop)")
    print("Reminder: this domain must be allow-listed in your Meta app's Login-for-Business config.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
