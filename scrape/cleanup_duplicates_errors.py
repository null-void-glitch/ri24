import json
import re
import hashlib

INPUT_FILE = "results.json"
OUTPUT_FILE = "results_cleaned.json"

ERROR_SIGNATURE = 'waiting for locator("a[href=\\"#legal\\"]")'


def is_bad_error(entry):
    return (
        entry.get("status") == "error"
        and ERROR_SIGNATURE in entry.get("message", "")
    )


def normalize_text(text: str) -> str:
    """
    Normalize agency text for reliable deduplication.
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def content_fingerprint(entry):
    """
    Create a stable fingerprint for agency content.
    """
    text = entry.get("popup_content_text", "")
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen_fingerprints = set()
    cleaned = []

    removed_error_count = 0
    removed_duplicate_agency_count = 0

    for entry in data:
        # 1) Remove known timeout errors
        if is_bad_error(entry):
            removed_error_count += 1
            continue

        # Only dedupe successful entries with content
        if entry.get("status") == "success":
            fp = content_fingerprint(entry)

            if fp in seen_fingerprints:
                removed_duplicate_agency_count += 1
                continue

            seen_fingerprints.add(fp)

        cleaned.append(entry)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Original entries: {len(data)}")
    print(f"Removed timeout errors: {removed_error_count}")
    print(f"Removed duplicate agency entries: {removed_duplicate_agency_count}")
    print(f"Remaining entries: {len(cleaned)}")
    print(f"Cleaned file written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
