"""Check that every catalogue identifier has an auditable research decision.

Run from the repository root with ``python scripts/validate_identifier_evidence.py``.
This checks ledger completeness and agreement with data.json; it cannot prove
that a linked authority record refers to the right institution or place.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"
EVIDENCE_PATH = REPO_ROOT / "research" / "identifier-evidence.csv"
FIELDS = ("isil", "wikidata_qid", "geonames_id")
COLUMNS = (
    "record_id", "field", "value", "status", "source_url",
    "corroborating_url", "checked_on", "note",
)


def valid_url(value: str) -> bool:
    """Return whether a source is an absolute public HTTP(S) URL."""
    try:
        parsed = urlsplit(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not (
            parsed.username or parsed.password
        )
    except ValueError:
        return False


def valid_date(value: str) -> bool:
    """Return whether a date is real, ISO formatted, and not in the future."""
    try:
        parsed = date.fromisoformat(value)
        return parsed.isoformat() == value and parsed <= date.today()
    except ValueError:
        return False


def validate(records: list[dict], rows: list[dict[str, str]]) -> list[str]:
    """Return all evidence errors for catalogue records and ledger rows."""
    errors: list[str] = []
    by_id = {str(record["id"]): record for record in records}
    expected = {(record_id, field) for record_id in by_id for field in FIELDS}
    seen: set[tuple[str, str]] = set()

    for line, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f"line {line}: malformed CSV row")
            continue
        record_id = row.get("record_id", "")
        field = row.get("field", "")
        key = (record_id, field)
        if key in seen:
            errors.append(f"line {line}: duplicate decision for {record_id}/{field}")
            continue
        seen.add(key)
        if key not in expected:
            errors.append(f"line {line}: unknown record or field {record_id}/{field}")
            continue

        record = by_id[record_id]
        value = row.get("value", "")
        status = row.get("status", "")
        source = row.get("source_url", "")
        corroborating = row.get("corroborating_url", "")
        checked = row.get("checked_on", "")
        note = row.get("note", "")
        data_value = record.get(field)

        if status == "verified":
            if data_value is None or value != str(data_value):
                errors.append(f"line {line}: verified {record_id}/{field} disagrees with data.json")
            if not valid_url(source):
                errors.append(f"line {line}: verified {record_id}/{field} needs a source URL")
            if field == "wikidata_qid" and not valid_url(corroborating):
                errors.append(f"line {line}: Wikidata match needs a corroborating URL")
        elif status == "unresolved":
            if data_value is not None or value or source or corroborating:
                errors.append(
                    f"line {line}: unresolved {record_id}/{field} "
                    "must have no identifier or source"
                )
            if not note.strip():
                errors.append(f"line {line}: unresolved {record_id}/{field} needs a reason")
        else:
            errors.append(f"line {line}: invalid status {status!r}")

        if corroborating and not valid_url(corroborating):
            errors.append(f"line {line}: invalid corroborating URL")
        if not valid_date(checked):
            errors.append(f"line {line}: invalid checked_on date {checked!r}")

    for record_id, field in sorted(expected - seen, key=lambda item: (int(item[0]), item[1])):
        errors.append(f"missing decision for {record_id}/{field}")
    return errors


def main() -> int:
    """Read the tracked catalogue and ledger, then report every violation."""
    try:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        with EVIDENCE_PATH.open(encoding="utf-8", newline="") as evidence:
            reader = csv.DictReader(evidence)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise ValueError(f"expected CSV columns: {', '.join(COLUMNS)}")
            rows = list(reader)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Cannot validate identifier evidence: {error}", file=sys.stderr)
        return 1

    errors = validate(records, rows)
    if errors:
        print(f"Identifier evidence failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Identifier evidence passed for {len(records)} records ({len(rows)} decisions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
