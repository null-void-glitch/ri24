# Europace Unterlagen Transfer

Move a loan case's customer documents from one Europace instance to another,
preserving category and assignment. Files are streamed through RAM only — no
permanent copy is kept on your machine.

## Why two instances
Different Europace partner accounts expose a different panel of banks. Both use
the same host (`api.europace2.de`); they are distinguished purely by separate
OAuth client credentials. The script authenticates to each side independently.

## Setup
```bash
pip install requests
cp .env.example .env      # fill in the four client_id / client_secret values
set -a; source .env; set +a
```

The OAuth client of each side must have these scopes:
- **source**: `unterlagen:dokument:lesen`, `unterlagen:unterlage:lesen`
- **target**: `unterlagen:dokument:schreiben`, `unterlagen:unterlage:lesen`

## Run
```bash
# preview (no upload): see which category/assignment each doc would get
python3 transfer_unterlagen.py --source-case A23WYC --target-case B98ZZ --dry-run

# do the transfer
python3 transfer_unterlagen.py --source-case A23WYC --target-case B98ZZ

# files only, categorize manually later in the target
python3 transfer_unterlagen.py --source-case A23WYC --target-case B98ZZ --no-metadata
```

## How it works
1. `GET /v1/dokumente/?vorgangsNummer=` — list source documents + metadata.
2. `GET /v1/dokumente/{id}/seiten` — read the dominant `zuordnung` (category + `bezug`).
3. Map the source `bezug` to a **target** `assignmentId` via
   `/v1/dokumente/moeglichezuordnungen` on both sides (matched by id, then
   type+name, then position). Assignment IDs are case-specific, so this remap
   is mandatory.
4. `GET /v1/dokumente/{id}/content` — download bytes into memory.
5. `POST /v2/dokumente/file` — multipart upload to the target with
   `caseId`, `displayName`, `category`, `assignmentId`. The in-memory copy is
   discarded immediately after.

## Notes & limits
- **Always `--dry-run` first.** The assignment remap is heuristic; if a source
  assignment has no counterpart in the target case it is uploaded with the
  category only (logged in the summary).
- One category/assignment per document (the dominant one across its pages).
  Mixed-category documents are not split.
- Documents like *Kreditentscheidungsinformation* / *Selbstauskunft* are **not**
  exposed by this API (they live in the Antraege API) and cannot be transferred.
- Releasing the uploaded documents to a bank (Freigabe) is a separate step and
  is intentionally **not** automated here.
- Supported file types: pdf, jpg, png, tiff (max 100 MB each).
- Failures are isolated per document; the run continues and exits non-zero if
  any document failed.
