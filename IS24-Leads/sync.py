"""Sync driver: fetch leads for every configured scoutId, emit envelopes.

Walks every (pool, scout_id) in ``config.json``, calls the IS24 lead endpoint
for each within a time window, validates the response, wraps each lead in a
``LeadEnvelope`` tagged with its pool, and writes the combined batch to
``out/leads-<ISO timestamp>.json`` for CRM ingestion.

Usage::

    python3 sync.py --test                              # use IS24 test leads
    python3 sync.py --since 2026-05-20T00:00:00         # last week, real
    python3 sync.py --since ... --until ...             # explicit window
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config as cfg
from auth import get_session
from client import fetch_leads
from schema import RawLeadsResponse, envelope

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "out"


def _parse_dt(s: str) -> datetime:
    # Accept "2026-05-27T00:00:00" or "2026-05-27"
    if "T" not in s:
        s = s + "T00:00:00"
    return datetime.fromisoformat(s)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync IS24 leads to JSON.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use IS24 test leads (test=true). Ignores --since/--until.",
    )
    parser.add_argument(
        "--since",
        type=_parse_dt,
        default=None,
        help="Start of time window (ISO). Defaults to 24h ago.",
    )
    parser.add_argument(
        "--until",
        type=_parse_dt,
        default=None,
        help="End of time window (ISO). Defaults to now.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=cfg.DEFAULT_CONFIG_FILE,
        help="Path to config.json.",
    )
    args = parser.parse_args(argv)

    conf = cfg.load(args.config)
    pools = conf.pools()
    if not pools:
        print("No scoutIds configured. Add organization.scout_id or advisors[].")
        return 2

    until = args.until or datetime.now()
    since = args.since or (until - timedelta(days=1))

    session = get_session()
    fetched_at = datetime.now(tz=timezone.utc)

    all_envelopes = []
    seen_ids: set[int] = set()

    for pool_name, scout_id in pools:
        if args.test:
            print(f"[{pool_name}] scoutId={scout_id}  GET /lead?test=true")
            raw = fetch_leads(session, test=True)
        else:
            print(
                f"[{pool_name}] scoutId={scout_id}  "
                f"from={since.isoformat()} to={until.isoformat()}"
            )
            raw = fetch_leads(
                session, scout_id=scout_id, since=since, until=until
            )

        parsed = RawLeadsResponse.model_validate(raw)
        print(f"  → {len(parsed.lead)} lead(s)")

        for lead in parsed.lead:
            if lead.id in seen_ids:
                # A lead can be returned via both the org and the advisor's
                # scoutId; we keep the first occurrence.
                continue
            seen_ids.add(lead.id)
            all_envelopes.append(
                envelope(lead, pool=pool_name, fetched_at=fetched_at)
            )

    OUT_DIR.mkdir(exist_ok=True)
    stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")
    out_file = OUT_DIR / f"leads-{stamp}.json"
    out_file.write_text(
        json.dumps(
            [e.model_dump(mode="json") for e in all_envelopes],
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"\nWrote {len(all_envelopes)} unique lead(s) to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
