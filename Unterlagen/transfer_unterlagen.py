#!/usr/bin/env python3
"""
transfer_unterlagen.py
======================

Transfer customer documents (Unterlagen) of a loan case from one Europace
instance to another, preserving category and assignment (Zuordnung).

Both instances share the same API host (api.europace2.de) but are reached with
*different OAuth client credentials* (different partner accounts that expose a
different panel of banks). The script authenticates twice and streams every
document through RAM only -- nothing is written to disk permanently.

Flow per document
-----------------
  source:  GET  /v1/dokumente/?vorgangsNummer={SRC}      -> list + metadata
           GET  /v1/dokumente/{id}/seiten                -> category + bezug
           GET  /v1/dokumente/{id}/content               -> file bytes (RAM)
  mapping: source bezug  --(typ + name)-->  target assignmentId
           via /v1/dokumente/moeglichezuordnungen on both sides
  target:  POST /v2/dokumente/file?caseId&displayName&category&assignmentId
                                                          -> upload (multipart)

Required OAuth scopes
---------------------
  source token: unterlagen:dokument:lesen, unterlagen:unterlage:lesen
  target token: unterlagen:dokument:schreiben, unterlagen:unterlage:lesen

Configuration (environment variables)
-------------------------------------
  EUROPACE_SRC_CLIENT_ID / EUROPACE_SRC_CLIENT_SECRET   credentials of source
  EUROPACE_TGT_CLIENT_ID / EUROPACE_TGT_CLIENT_SECRET   credentials of target
  EUROPACE_TOKEN_URL   (default https://api.europace.de/auth/token)
  EUROPACE_API_BASE    (default https://api.europace2.de)

Usage
-----
  python3 transfer_unterlagen.py --source-case A23WYC --target-case B98ZZ
  python3 transfer_unterlagen.py --source-case A23WYC --target-case B98ZZ --dry-run
  python3 transfer_unterlagen.py ... --no-metadata        # files only, no category/assignment
  python3 transfer_unterlagen.py ... --antragsnummer XYZ  # use application-specific assignments

Requires: Python 3.8+, `requests`  (pip install requests)
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

DEFAULT_TOKEN_URL = "https://api.europace.de/auth/token"
DEFAULT_API_BASE = "https://api.europace2.de"

# Scopes requested per side. Keep these minimal.
SRC_SCOPES = "unterlagen:dokument:lesen unterlagen:unterlage:lesen"
TGT_SCOPES = "unterlagen:dokument:schreiben unterlagen:unterlage:lesen"

REQUEST_TIMEOUT = 120  # seconds; documents may be up to 100 MB


# --------------------------------------------------------------------------- #
# OAuth client                                                                #
# --------------------------------------------------------------------------- #
class EuropaceClient:
    """A thin authenticated client for one Europace instance (one credential set)."""

    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        scope: str,
        token_url: str,
        api_base: str,
    ) -> None:
        self.name = name
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token_url = token_url
        self.api_base = api_base.rstrip("/")
        self._session = requests.Session()
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    # -- auth -------------------------------------------------------------- #
    def _fetch_token(self) -> None:
        # client_credentials grant, HTTP Basic auth with client_id:client_secret.
        data = {"grant_type": "client_credentials"}
        if self._scope:
            data["scope"] = self._scope
        resp = self._session.post(
            self._token_url,
            data=data,
            auth=(self._client_id, self._client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"[{self.name}] token request failed ({resp.status_code}): {resp.text}"
            )
        body = resp.json()
        self._token = body["access_token"]
        # refresh 60s before the real expiry to be safe
        self._token_expiry = time.monotonic() + int(body.get("expires_in", 3600)) - 60
        granted = body.get("scope", "")
        print(f"[{self.name}] authenticated; granted scopes: {granted}")

    def _auth_header(self) -> Dict[str, str]:
        if self._token is None or time.monotonic() >= self._token_expiry:
            self._fetch_token()
        return {"Authorization": f"Bearer {self._token}"}

    # -- generic request helpers ------------------------------------------ #
    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self._session.get(
            self.api_base + path,
            headers=self._auth_header(),
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self._session.post(
            self.api_base + path,
            headers=self._auth_header(),
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )

    # -- high-level API calls --------------------------------------------- #
    def list_documents(self, case_id: str) -> List[Dict[str, Any]]:
        resp = self.get("/v1/dokumente/", params={"vorgangsNummer": case_id})
        resp.raise_for_status()
        return resp.json()

    def get_pages(self, document_id: str) -> List[Dict[str, Any]]:
        resp = self.get(f"/v1/dokumente/{document_id}/seiten")
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        # endpoint returns a bare array of Seite
        return data if isinstance(data, list) else data.get("seiten", [])

    def download_document(self, document_id: str) -> bytes:
        resp = self.get(f"/v1/dokumente/{document_id}/content")
        resp.raise_for_status()
        return resp.content

    def possible_assignments(
        self, case_id: str, antrags_nummer: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params: Dict[str, str] = {"vorgangsNummer": case_id}
        if antrags_nummer:
            params["antragsNummer"] = antrags_nummer
        resp = self.get("/v1/dokumente/moeglichezuordnungen", params=params)
        resp.raise_for_status()
        return resp.json()

    def upload_document(
        self,
        case_id: str,
        filename: str,
        display_name: str,
        content: bytes,
        mime_type: str,
        category: Optional[str] = None,
        assignment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, str] = {"caseId": case_id}
        if display_name:
            params["displayName"] = display_name
        if category:
            params["category"] = category
        if assignment_id:
            params["assignmentId"] = assignment_id
        # multipart/form-data with the raw bytes held only in memory
        files = {"file": (filename, io.BytesIO(content), mime_type)}
        resp = self.post("/v2/dokumente/file", params=params, files=files)
        if resp.status_code != 200:
            raise RuntimeError(
                f"upload failed ({resp.status_code}): {resp.text}"
            )
        return resp.json()


# --------------------------------------------------------------------------- #
# Assignment mapping (source bezug -> target assignmentId)                    #
# --------------------------------------------------------------------------- #
@dataclass
class AssignmentIndex:
    """Index of a case's possible assignments, keyed for cross-case mapping."""

    # (typ, name) -> assignment id     e.g. ("antragsteller", "Max Mustermann") -> "antragsteller:1"
    by_typ_name: Dict[tuple, str] = field(default_factory=dict)
    # bezug id -> (typ, name)
    by_id: Dict[str, tuple] = field(default_factory=dict)
    # typ -> ordered list of ids (positional fallback)
    by_typ: Dict[str, List[str]] = field(default_factory=dict)
    # set of valid category ids in this case
    categories: set = field(default_factory=set)

    @classmethod
    def from_response(cls, data: List[Dict[str, Any]]) -> "AssignmentIndex":
        idx = cls()
        for entry in data:
            kat = entry.get("kategorie") or {}
            if isinstance(kat, dict) and kat.get("id"):
                idx.categories.add(kat["id"])
            for bez in entry.get("bezuege", []) or []:
                bez_id = bez.get("id")
                typ = bez.get("typ")
                name = bez.get("name")
                if not bez_id:
                    continue
                idx.by_id.setdefault(bez_id, (typ, name))
                if typ is not None:
                    idx.by_typ_name.setdefault((typ, name), bez_id)
                    lst = idx.by_typ.setdefault(typ, [])
                    if bez_id not in lst:
                        lst.append(bez_id)
        return idx


def map_assignment(
    src_bezug: Optional[str],
    src_index: AssignmentIndex,
    tgt_index: AssignmentIndex,
) -> tuple[Optional[str], str]:
    """
    Translate a source bezug id into the matching target assignmentId.

    Returns (target_assignment_id_or_None, note).
    """
    if not src_bezug:
        return None, "no source assignment"

    typ_name = src_index.by_id.get(src_bezug)

    # 1) exact same bezug id exists in target (common for Baufi: immobilie:4711)
    if src_bezug in tgt_index.by_id:
        return src_bezug, "matched by id"

    if typ_name is None:
        return None, f"source bezug '{src_bezug}' not found in source assignments"

    typ, name = typ_name

    # 2) match by (typ, name)
    hit = tgt_index.by_typ_name.get((typ, name))
    if hit:
        return hit, f"matched by typ+name ({typ}/{name})"

    # 3) positional fallback within the same typ (same ordinal index)
    src_list = src_index.by_typ.get(typ, [])
    tgt_list = tgt_index.by_typ.get(typ, [])
    if src_bezug in src_list:
        pos = src_list.index(src_bezug)
        if pos < len(tgt_list):
            return tgt_list[pos], f"matched by position ({typ}#{pos})"

    return None, f"no target match for {typ}/{name}; uploading without assignment"


# --------------------------------------------------------------------------- #
# Per-document category/assignment extraction                                 #
# --------------------------------------------------------------------------- #
def derive_category_and_bezug(
    pages: List[Dict[str, Any]],
) -> tuple[Optional[str], Optional[str]]:
    """
    Pick the dominant (category, bezug) for a document from its pages.

    Each page has an optional `zuordnung` {kategorie, bezug}. We take the most
    frequent fully-assigned zuordnung; falling back to the first page that has a
    category at all (predicted classification).
    """
    counts: Dict[tuple, int] = {}
    fallback_category: Optional[str] = None

    for page in pages:
        z = page.get("zuordnung") or {}
        kat = z.get("kategorie")
        bez = z.get("bezug")
        if kat:
            counts[(kat, bez)] = counts.get((kat, bez), 0) + 1
        if fallback_category is None:
            klass = (page.get("klassifizierung") or {}).get("kategorien") or []
            if klass:
                fallback_category = klass[0]

    if counts:
        (kat, bez), _ = max(counts.items(), key=lambda kv: kv[1])
        return kat, bez

    return fallback_category, None


# --------------------------------------------------------------------------- #
# Main transfer routine                                                       #
# --------------------------------------------------------------------------- #
@dataclass
class TransferResult:
    source_id: str
    display_name: str
    status: str  # "uploaded" | "skipped" | "failed" | "dry-run"
    target_id: Optional[str] = None
    category: Optional[str] = None
    assignment_id: Optional[str] = None
    note: str = ""


def transfer_case(
    src: EuropaceClient,
    tgt: EuropaceClient,
    source_case: str,
    target_case: str,
    *,
    with_metadata: bool,
    antrags_nummer: Optional[str],
    dry_run: bool,
) -> List[TransferResult]:
    print(f"\nListing documents in source case {source_case} ...")
    documents = src.list_documents(source_case)
    print(f"Found {len(documents)} document(s).")

    src_index = tgt_index = AssignmentIndex()
    if with_metadata:
        print("Loading possible assignments on both instances ...")
        src_index = AssignmentIndex.from_response(
            src.possible_assignments(source_case, antrags_nummer)
        )
        tgt_index = AssignmentIndex.from_response(
            tgt.possible_assignments(target_case, antrags_nummer)
        )

    results: List[TransferResult] = []

    for i, doc in enumerate(documents, 1):
        doc_id = doc.get("id")
        display_name = doc.get("anzeigename") or doc.get("filename") or doc_id
        filename = doc.get("filename") or f"{display_name}"
        mime_type = doc.get("type") or "application/octet-stream"
        res = TransferResult(source_id=doc_id, display_name=display_name, status="")

        print(f"\n[{i}/{len(documents)}] {display_name}  (id={doc_id}, {mime_type})")

        try:
            category: Optional[str] = None
            assignment_id: Optional[str] = None

            if with_metadata:
                pages = src.get_pages(doc_id)
                category, src_bezug = derive_category_and_bezug(pages)
                assignment_id, note = map_assignment(src_bezug, src_index, tgt_index)
                # only keep a category the target actually accepts (if we know the list)
                if (
                    category
                    and tgt_index.categories
                    and category not in tgt_index.categories
                ):
                    note = f"{note}; category '{category}' unknown on target -> dropped"
                    category = None
                res.category = category
                res.assignment_id = assignment_id
                res.note = note
                print(
                    f"    category={category!r} "
                    f"src_bezug={src_bezug!r} -> assignmentId={assignment_id!r} ({note})"
                )

            if dry_run:
                res.status = "dry-run"
                results.append(res)
                continue

            # --- stream the bytes through RAM: download then upload --------- #
            content = src.download_document(doc_id)
            print(f"    downloaded {len(content):,} bytes; uploading to {target_case} ...")
            upload = tgt.upload_document(
                case_id=target_case,
                filename=filename,
                display_name=display_name,
                content=content,
                mime_type=mime_type,
                category=category,
                assignment_id=assignment_id,
            )
            # release the copy as soon as the upload returns
            del content
            res.target_id = upload.get("id")
            res.status = "uploaded"
            print(f"    -> uploaded as id={res.target_id}")

        except Exception as exc:  # isolate failures per document
            res.status = "failed"
            res.note = (res.note + "; " if res.note else "") + f"ERROR: {exc}"
            print(f"    !! FAILED: {exc}", file=sys.stderr)

        results.append(res)

    return results


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        sys.exit(f"Missing required environment variable: {name}")
    return val


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transfer Unterlagen (documents) between two Europace instances."
    )
    parser.add_argument("--source-case", required=True, help="vorgangsNummer in the source instance")
    parser.add_argument("--target-case", required=True, help="caseId in the target instance")
    parser.add_argument(
        "--antragsnummer",
        default=None,
        help="optional application number for application-specific assignments",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="transfer files only, without category/assignment",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list what would be transferred (incl. resolved assignments) without uploading",
    )
    args = parser.parse_args()

    token_url = os.environ.get("EUROPACE_TOKEN_URL", DEFAULT_TOKEN_URL)
    api_base = os.environ.get("EUROPACE_API_BASE", DEFAULT_API_BASE)

    src = EuropaceClient(
        name="source",
        client_id=require_env("EUROPACE_SRC_CLIENT_ID"),
        client_secret=require_env("EUROPACE_SRC_CLIENT_SECRET"),
        scope=SRC_SCOPES,
        token_url=token_url,
        api_base=api_base,
    )
    tgt = EuropaceClient(
        name="target",
        client_id=require_env("EUROPACE_TGT_CLIENT_ID"),
        client_secret=require_env("EUROPACE_TGT_CLIENT_SECRET"),
        scope=TGT_SCOPES,
        token_url=token_url,
        api_base=api_base,
    )

    results = transfer_case(
        src,
        tgt,
        args.source_case,
        args.target_case,
        with_metadata=not args.no_metadata,
        antrags_nummer=args.antragsnummer,
        dry_run=args.dry_run,
    )

    # ---- summary --------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    by_status: Dict[str, int] = {}
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        flag = {"uploaded": "OK ", "dry-run": "DRY", "failed": "ERR", "skipped": "SKIP"}.get(
            r.status, "?"
        )
        line = f"  [{flag}] {r.display_name}"
        if r.category or r.assignment_id:
            line += f"  (category={r.category}, assignmentId={r.assignment_id})"
        if r.note:
            line += f"  -- {r.note}"
        print(line)
    print("-" * 70)
    print(", ".join(f"{k}: {v}" for k, v in sorted(by_status.items())))

    if any(r.status == "failed" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
