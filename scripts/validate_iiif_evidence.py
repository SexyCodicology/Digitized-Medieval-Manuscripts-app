"""Check evidence for published and proposed direct IIIF endpoints.

Run from the repository root with ``python scripts/validate_iiif_evidence.py``.
The check validates the research contract and its agreement with the catalogue
and pilot ledger. It does not make network requests or approve an endpoint.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import validate_linked_data_pilot as pilot_validator  # noqa: E402
from scripts.validate_link_assertions import (  # noqa: E402
    IIIF_FIELDS,
    parse_date,
    safe_note,
    valid_url,
)

DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"
PILOT_PATH = REPO_ROOT / "research" / "linked-data-pilot-review.csv"
EVIDENCE_PATH = REPO_ROOT / "research" / "iiif-evidence.csv"
COLUMNS = (
    "record_id",
    "field",
    "value",
    "status",
    "source_url",
    "corroborating_url",
    "checked_on",
    "note",
)
STATUSES = frozenset({"verified", "proposed"})


def required_evidence(
    records: list[dict],
    pilot_rows: list[dict[str, str]],
) -> dict[tuple[str, str], tuple[str, str]]:
    """Return the value and status required for each direct IIIF endpoint."""
    by_id = {str(record.get("id")): record for record in records}
    required: dict[tuple[str, str], tuple[str, str]] = {}

    for record_id, record in by_id.items():
        for field in IIIF_FIELDS:
            value = record.get(field)
            if value:
                required[(record_id, field)] = (str(value), "verified")

    for row in pilot_rows:
        record_id = row.get("record_id", "")
        field = row.get("field", "")
        candidate = row.get("candidate_value", "")
        record = by_id.get(record_id, {})
        if (
            field in IIIF_FIELDS
            and candidate
            and not record.get(field)
            and row.get("decision") == "pending"
        ):
            required[(record_id, field)] = (candidate, "proposed")

    return required


def validate(
    records: list[dict],
    pilot_rows: list[dict[str, str]],
    rows: list[dict[str, str]],
) -> list[str]:
    """Return all IIIF evidence contract and catalogue-consistency errors."""
    errors: list[str] = []
    expected = required_evidence(records, pilot_rows)
    seen: set[tuple[str, str]] = set()

    for line, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f"line {line}: malformed CSV row")
            continue

        record_id = row.get("record_id", "")
        field = row.get("field", "")
        key = (record_id, field)
        prefix = f"line {line}: {record_id}/{field}"
        if key in seen:
            errors.append(f"{prefix} has duplicate IIIF evidence")
            continue
        seen.add(key)

        requirement = expected.get(key)
        if requirement is None:
            errors.append(f"{prefix} has no published or proposed endpoint")
            continue

        expected_value, expected_status = requirement
        value = row.get("value", "")
        status = row.get("status", "")
        source = row.get("source_url", "")
        corroborating = row.get("corroborating_url", "")
        checked_on = row.get("checked_on", "")

        if value != expected_value:
            errors.append(f"{prefix} evidence value disagrees with its endpoint")
        if status not in STATUSES:
            errors.append(f"{prefix} has invalid status {status!r}")
        elif status != expected_status:
            errors.append(f"{prefix} must use status {expected_status!r}")
        if source != value or not valid_url(source):
            errors.append(f"{prefix} source must be the direct IIIF endpoint")
        if not valid_url(corroborating):
            errors.append(f"{prefix} needs a public corroborating URL")
        elif corroborating == value:
            errors.append(f"{prefix} corroborating URL must differ from the endpoint")
        if parse_date(checked_on) is None:
            errors.append(f"{prefix} has invalid checked_on date {checked_on!r}")
        if not safe_note(row.get("note", "")):
            errors.append(f"{prefix} needs a safe evidence note")

    for record_id, field in sorted(
        expected.keys() - seen,
        key=lambda item: (int(item[0]), item[1]),
    ):
        errors.append(f"missing IIIF evidence for {record_id}/{field}")
    return errors


def read_csv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a CSV file and require its exact public column contract."""
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != columns:
            raise ValueError(f"{path.name} expected columns: {', '.join(columns)}")
        return list(reader)


def main() -> int:
    """Read the catalogue and research ledgers, then report every violation."""
    try:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        pilot_rows = read_csv(PILOT_PATH, pilot_validator.COLUMNS)
        rows = read_csv(EVIDENCE_PATH, COLUMNS)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Cannot validate IIIF evidence: {error}", file=sys.stderr)
        return 1

    errors = validate(records, pilot_rows, rows)
    if errors:
        print(f"IIIF evidence failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    proposed = sum(row["status"] == "proposed" for row in rows)
    verified = len(rows) - proposed
    print(
        f"IIIF evidence passed for {len(rows)} endpoints "
        f"({verified} verified; {proposed} proposed)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
