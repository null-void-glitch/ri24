"""Thin wrapper around the IS24 ``/financing/construction/v2/lead`` endpoint."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from requests_oauthlib import OAuth1Session

from auth import SANDBOX_BASE

LEAD_URL = f"{SANDBOX_BASE}/restapi/api/financing/construction/v2/lead"

# IS24 expects: yyyy-MM-dd'T'HH:mm:ss (no timezone, Europe/Berlin local)
IS24_DATE_FMT = "%Y-%m-%dT%H:%M:%S"


def _fmt(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime(IS24_DATE_FMT) if dt else None


def fetch_leads(
    session: OAuth1Session,
    *,
    scout_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    test: bool = False,
) -> dict:
    """Call GET /lead and return the parsed JSON body.

    If ``test=True``, IS24 ignores all other params and returns sample leads.
    Otherwise pass ``scout_id`` + ``since``/``until`` for a real time-window
    query. Omitting ``scout_id`` returns leads for every scoutId the token is
    authorized for.
    """
    if test:
        params: dict[str, str] = {"test": "true"}
    else:
        params = {}
        if scout_id:
            params["scoutid"] = scout_id
        if since:
            params["from"] = _fmt(since) or ""
        if until:
            params["to"] = _fmt(until) or ""

    response = session.get(
        LEAD_URL, params=params, headers={"Accept": "application/json"}
    )
    response.raise_for_status()
    return response.json()
