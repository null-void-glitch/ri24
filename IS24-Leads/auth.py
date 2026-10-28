"""IS24 OAuth 1.0a (3-legged) helpers.

Public entry point is ``get_session()``: it returns an authenticated
``OAuth1Session`` ready to call the IS24 REST API. On first run it walks the
interactive authorize dance; subsequent runs reuse the cached access token
in ``tokens.json``.
"""
from __future__ import annotations

import json
import webbrowser
from pathlib import Path

from requests_oauthlib import OAuth1Session

SANDBOX_BASE = "https://rest.immobilienscout24.de"
REQUEST_TOKEN_URL = f"{SANDBOX_BASE}/restapi/security/oauth/request_token"
AUTHORIZE_URL = f"{SANDBOX_BASE}/restapi/security/oauth/confirm_access"
ACCESS_TOKEN_URL = f"{SANDBOX_BASE}/restapi/security/oauth/access_token"

ROOT = Path(__file__).parent
CRED_FILE = ROOT / "credentials.txt"
TOKEN_FILE = ROOT / "tokens.json"


def parse_credentials(path: Path = CRED_FILE) -> dict[str, str]:
    creds: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        creds[key.strip()] = val.strip()
    return creds


def _oauth_dance(consumer_key: str, consumer_secret: str) -> dict:
    print("Requesting OAuth request token from IS24...")
    oauth = OAuth1Session(
        consumer_key, client_secret=consumer_secret, callback_uri="oob"
    )
    rt = oauth.fetch_request_token(REQUEST_TOKEN_URL, params={"scope": "S_BAUFIMANAGER"})

    auth_url = oauth.authorization_url(AUTHORIZE_URL)
    print()
    print("=" * 72)
    print("Open this URL, log in with your IS24 account, approve:")
    print()
    print(f"  {auth_url}")
    print("=" * 72)

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    verifier = input("Paste the verifier shown after approving: ").strip()

    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=rt["oauth_token"],
        resource_owner_secret=rt["oauth_token_secret"],
        verifier=verifier,
    )
    return oauth.fetch_access_token(ACCESS_TOKEN_URL)


def get_session(consumer_key: str | None = None,
                consumer_secret: str | None = None) -> OAuth1Session:
    """Return an authenticated OAuth1Session, running the dance if needed."""
    if consumer_key is None or consumer_secret is None:
        creds = parse_credentials()
        consumer_key = consumer_key or creds["System Key / Consumer Key"]
        consumer_secret = consumer_secret or creds[
            "API Secret / Consumer Secret"
        ]

    if TOKEN_FILE.exists():
        tokens = json.loads(TOKEN_FILE.read_text())
    else:
        tokens = _oauth_dance(consumer_key, consumer_secret)
        TOKEN_FILE.write_text(json.dumps(tokens, indent=2))
        print(f"Access token cached in {TOKEN_FILE.name}")

    return OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=tokens["oauth_token"],
        resource_owner_secret=tokens["oauth_token_secret"],
    )
