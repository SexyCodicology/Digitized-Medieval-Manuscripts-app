"""Check institution-name research against the published directory data."""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "docs" / "assets" / "data.json"
EVIDENCE_PATH = ROOT / "research" / "name-evidence.csv"
COLUMNS = (
    "record_id", "field", "value", "language", "status", "source_url",
    "checked_on", "note",
)
FIELDS = {"library", "access_point_title", "library_alternate_names"}
STATUSES = {"pending", "verified"}
LANGUAGE_PATTERN = re.compile(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*\Z")


def valid_date(value: str) -> bool:
    """Return whether a date is real, ISO-formatted, and not in the future."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value and parsed <= date.today()


def valid_source(value: str) -> bool:
    """Return whether an evidence URL has an HTTP(S) origin."""
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return parts.scheme.lower() in {"http", "https"} and bool(parts.netloc)


def validate(records: list[dict], rows: list[dict[str, str]]) -> list[str]:
    """Return evidence errors without claiming that cited names are true."""
    errors = []
    by_id = {str(record["id"]): record for record in records}
    preferred_seen: set[str] = set()
    row_keys: set[tuple[str, str, str]] = set()
    verified: set[tuple[str, str, str]] = set()

    for number, row in enumerate(rows, start=2):
        record_id, field = row["record_id"], row["field"]
        value, language = row["value"], row["language"]
        status = row["status"]
        key = (record_id, field, value.casefold())
        if record_id not in by_id or field not in FIELDS or not value.strip():
            errors.append(f"row {number}: unknown record, field, or blank value")
            continue
        if key in row_keys:
            errors.append(f"row {number}: duplicate name decision for record {record_id}")
        row_keys.add(key)
        if status not in STATUSES:
            errors.append(f"row {number}: invalid status {status!r}")
        if field == "library":
            if record_id in preferred_seen:
                errors.append(f"row {number}: duplicate preferred name for record {record_id}")
            preferred_seen.add(record_id)
            if value != by_id[record_id]["library"]:
                errors.append(f"row {number}: preferred name differs from data.json")
        if field != "library_alternate_names" and language:
            errors.append(f"row {number}: language belongs only on alternate names")
        if language and not LANGUAGE_PATTERN.fullmatch(language):
            errors.append(f"row {number}: invalid language tag")
        if status == "verified":
            if not valid_source(row["source_url"]) or not valid_date(row["checked_on"]):
                errors.append(f"row {number}: verified name needs a public source and check date")
            if not row["note"].strip():
                errors.append(f"row {number}: verified name needs a match note")
            if field == "access_point_title" and value != by_id[record_id].get(field):
                errors.append(f"row {number}: verified title differs from data.json")
            if field == "library_alternate_names" and not any(
                entry["name"] == value and entry.get("language", "") == language
                for entry in by_id[record_id].get(field, [])
            ):
                errors.append(f"row {number}: verified alternate name differs from data.json")
            verified.add((record_id, field, value))
        if row["checked_on"] and not valid_date(row["checked_on"]):
            errors.append(f"row {number}: invalid check date")
        if row["source_url"] and not valid_source(row["source_url"]):
            errors.append(f"row {number}: invalid source URL")

    for record_id, record in by_id.items():
        if record_id not in preferred_seen:
            errors.append(f"record {record_id}: missing preferred-name decision")
        title = record.get("access_point_title")
        if title and (record_id, "access_point_title", title) not in verified:
            errors.append(f"record {record_id}: access_point_title lacks verified evidence")
        for alternate in record.get("library_alternate_names", []):
            name = alternate["name"]
            if (record_id, "library_alternate_names", name) not in verified:
                errors.append(f"record {record_id}: alternate name {name!r} lacks verified evidence")
            if not any(
                row["record_id"] == record_id
                and row["field"] == "library_alternate_names"
                and row["value"] == name
                and row["language"] == alternate.get("language", "")
                and row["status"] == "verified"
                for row in rows
            ):
                errors.append(f"record {record_id}: alternate name language differs from evidence")
    return errors


def main() -> int:
    """Validate the tracked evidence register and report its review progress."""
    try:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        with EVIDENCE_PATH.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise ValueError("name-evidence.csv has unexpected columns")
            rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError("name-evidence.csv has a malformed row")
        errors = validate(records, rows)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Name evidence validation failed: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    pending = sum(row["status"] == "pending" for row in rows)
    print(f"Name evidence passed for {len(records)} records ({pending} pending decisions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
