#!/usr/bin/env python3
"""
Migrate an existing WhatsApp *Business App* number into your existing Cloud API WABA.

This implements the Cloud API "Migrate an existing WhatsApp number to a business account"
flow (NOT the Solution-Partner-to-Solution-Partner flow). Numbers are migrated ONE AT A TIME.

  WARNING: Step 4 (register) disconnects the number from the WhatsApp Business App and the
  app's chat history is lost. Back up first. See MIGRATION_RUNBOOK.md.

Usage (guided, interactive — recommended):
    export WABA_ID=...           # destination WABA you own
    export WA_ACCESS_TOKEN=...   # system-user token w/ whatsapp_business_management
    python3 migrate_number.py migrate --cc 49 --number 15123456789 \
        --name "My Business" --pin 123456 --code-method SMS

Or run each step on its own:
    python3 migrate_number.py add          --cc 49 --number 15123456789 --name "My Business"
    python3 migrate_number.py request-code --phone-id <PHONE_NUMBER_ID> --code-method SMS
    python3 migrate_number.py verify-code   --phone-id <PHONE_NUMBER_ID> --code 123456
    python3 migrate_number.py register      --phone-id <PHONE_NUMBER_ID> --pin 123456
    python3 migrate_number.py status        # list numbers on the WABA

Config is read from env vars or a .env file in the working dir (see .env.example).
Stdlib only — no dependencies.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v25.0")
BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def load_dotenv(path=".env"):
    """Minimal .env loader: KEY=VALUE lines, ignores comments/blank lines."""
    if not os.path.exists(path):
        return
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def _post(path, params):
    token = os.environ.get("WA_ACCESS_TOKEN")
    if not token:
        sys.exit("ERROR: WA_ACCESS_TOKEN is not set (env or .env).")
    params = {k: v for k, v in params.items() if v is not None}
    params["access_token"] = token
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=data, method="POST")
    return _send(req)


def _get(path, params=None):
    token = os.environ.get("WA_ACCESS_TOKEN")
    if not token:
        sys.exit("ERROR: WA_ACCESS_TOKEN is not set (env or .env).")
    params = dict(params or {})
    params["access_token"] = token
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    return _send(urllib.request.Request(url, method="GET"))


def _send(req):
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode() or "{}")
        print(json.dumps(body, indent=2), file=sys.stderr)
        sys.exit(f"HTTP {e.code} from Graph API — see error above.")
    return body


def _waba_id(args):
    wid = getattr(args, "waba_id", None) or os.environ.get("WABA_ID")
    if not wid:
        sys.exit("ERROR: WABA_ID is not set (env, .env, or --waba-id).")
    return wid


# --- step commands -----------------------------------------------------------

def cmd_add(args):
    """Step 1: add the phone number to the destination WABA."""
    body = _post(f"{_waba_id(args)}/phone_numbers", {
        "cc": args.cc,
        "phone_number": args.number,
        "verified_name": args.name,
    })
    print(json.dumps(body, indent=2))
    phone_id = body.get("id")
    if phone_id:
        print(f"\nPHONE_NUMBER_ID = {phone_id}")
    return phone_id


def cmd_request_code(args):
    """Step 2: request the verification code."""
    body = _post(f"{args.phone_id}/request_code", {
        "code_method": args.code_method,
        "language": args.language,
    })
    print(json.dumps(body, indent=2))
    return body


def cmd_verify_code(args):
    """Step 3: verify the code received via SMS/VOICE."""
    body = _post(f"{args.phone_id}/verify_code", {"code": args.code})
    print(json.dumps(body, indent=2))
    return body


def cmd_register(args):
    """Step 4: register the number on Cloud API with a new 2-step PIN."""
    body = _post(f"{args.phone_id}/register", {
        "messaging_product": "whatsapp",
        "pin": args.pin,
    })
    print(json.dumps(body, indent=2))
    return body


def cmd_status(args):
    """List phone numbers on the WABA with their verification/name status."""
    body = _get(f"{_waba_id(args)}/phone_numbers", {
        "fields": "id,display_phone_number,verified_name,code_verification_status,"
                  "name_status,platform_type,quality_rating"
    })
    print(json.dumps(body, indent=2))


def cmd_migrate(args):
    """Guided end-to-end migration for a single number (pauses for the SMS/VOICE code)."""
    print(f"== Migrating +{args.cc}{args.number} into WABA {_waba_id(args)} ==")
    print("\n[1/4] Adding number to WABA ...")
    phone_id = cmd_add(args)
    if not phone_id:
        sys.exit("Could not obtain PHONE_NUMBER_ID; aborting.")

    print(f"\n[2/4] Requesting {args.code_method} verification code ...")
    args.phone_id = phone_id
    cmd_request_code(args)

    code = input("\nEnter the 6-digit code you received: ").strip()
    args.code = code
    print("\n[3/4] Verifying code ...")
    cmd_verify_code(args)

    print("\n[4/4] Registering on Cloud API (this disconnects the WhatsApp Business App) ...")
    confirm = input("Type the number again to confirm irreversible registration: ").strip()
    if confirm != args.number:
        sys.exit("Confirmation did not match; not registering. Re-run 'register' manually when ready.")
    cmd_register(args)
    print(f"\nDone. Verify with:  python3 {sys.argv[0]} status")


def build_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--waba-id", help="Destination WABA ID (overrides WABA_ID env).")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="Step 1: add number to WABA")
    a.add_argument("--cc", required=True)
    a.add_argument("--number", required=True)
    a.add_argument("--name", required=True, help="Display / verified name")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("request-code", help="Step 2: request verification code")
    r.add_argument("--phone-id", required=True)
    r.add_argument("--code-method", default="SMS", choices=["SMS", "VOICE"])
    r.add_argument("--language", default="en_US")
    r.set_defaults(func=cmd_request_code)

    v = sub.add_parser("verify-code", help="Step 3: verify code")
    v.add_argument("--phone-id", required=True)
    v.add_argument("--code", required=True)
    v.set_defaults(func=cmd_verify_code)

    g = sub.add_parser("register", help="Step 4: register on Cloud API")
    g.add_argument("--phone-id", required=True)
    g.add_argument("--pin", required=True, help="New 6-digit 2-step PIN")
    g.set_defaults(func=cmd_register)

    s = sub.add_parser("status", help="List numbers on the WABA")
    s.set_defaults(func=cmd_status)

    m = sub.add_parser("migrate", help="Guided end-to-end migration of ONE number")
    m.add_argument("--cc", required=True)
    m.add_argument("--number", required=True)
    m.add_argument("--name", required=True)
    m.add_argument("--pin", required=True, help="New 6-digit 2-step PIN")
    m.add_argument("--code-method", default="SMS", choices=["SMS", "VOICE"])
    m.add_argument("--language", default="en_US")
    m.set_defaults(func=cmd_migrate)
    return p


def main():
    load_dotenv()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
