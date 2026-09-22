"""Validate the field-level decisions for the linked-data audit pilot.

The pilot ledger records every candidate selected for the first review batch,
including one record chosen to test deliberate absence. Approved and corrected
relationships must agree with the public assertion register.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

try:
    from scripts.validate_link_assertions import (
        COLUMNS as ASSERTION_COLUMNS,
        FIELDS,
        REVIEWER_NAME,
        parse_date,
        safe_note,
        valid_url,
        valid_review_url,
    )
except ModuleNotFoundError:  # Direct execution sets scripts/ as sys.path[0].
    from validate_link_assertions import (  # type: ignore[no-redef]
        COLUMNS as ASSERTION_COLUMNS,
        FIELDS,
        REVIEWER_NAME,
        parse_date,
        safe_note,
        valid_url,
        valid_review_url,
    )

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"
ASSERTIONS_PATH = REPO_ROOT / "docs" / "assets" / "link-assertions.csv"
PILOT_PATH = REPO_ROOT / "research" / "linked-data-pilot-review.csv"
PILOT_RECORD_IDS = frozenset(
    {
        "3", "24", "29", "44", "47", "51", "62", "78", "154", "235",
        "238", "261", "267", "275", "318", "396", "402", "409", "411",
        "433", "515", "574", "613", "669", "670",
    }
)
COLUMNS = (
    "record_id",
    "field",
    "candidate_value",
    "decision",
    "reviewer",
    "reviewed_on",
    "review_url",
    "note",
)
DECISIONS = frozenset({"pending", "approve", "correct", "remove", "absent"})
REVIEW_COLUMNS = ("reviewer", "reviewed_on", "review_url")
ABSENCE_CONTROL_ID = "154"
CANDIDATE_PATTERNS = {
    "isil": re.compile(r"[A-Z]{1,4}-[A-Za-z0-9][A-Za-z0-9:/-]*\Z"),
    "wikidata_qid": re.compile(r"Q[1-9][0-9]*\Z"),
    "geonames_id": re.compile(r"[1-9][0-9]*\Z"),
}


def valid_candidate(field: str, value: str) -> bool:
    """Return whether a non-empty pilot candidate has the expected shape."""
    if field in FIELDS and field.endswith("_url"):
        return valid_url(value)
    pattern = CANDIDATE_PATTERNS.get(field)
    return pattern is not None and pattern.fullmatch(value) is not None


def assertion_for(
    assertions: list[dict[str, str]],
    record_id: str,
    field: str,
    value: str,
) -> dict[str, str] | None:
    """Return the exact approved assertion for a pilot decision, if present."""
    return next(
        (
            row
            for row in assertions
            if row.get("record_id") == record_id
            and row.get("field") == field
            and row.get("value") == value
        ),
        None,
    )


def review_errors(line: int, row: dict[str, str]) -> list[str]:
    """Return missing or malformed provenance errors for a final decision."""
    prefix = f"line {line}: {row.get('record_id', '')}/{row.get('field', '')}"
    errors: list[str] = []
    if REVIEWER_NAME.fullmatch(row.get("reviewer", "")) is None:
        errors.append(f"{prefix} needs a GitHub reviewer name")
    if parse_date(row.get("reviewed_on", "")) is None:
        errors.append(f"{prefix} needs a valid review date")
    if not valid_review_url(row.get("review_url", "")):
        errors.append(f"{prefix} needs a DMMapp PR review URL")
    return errors


def assertion_review_errors(
    line: int,
    row: dict[str, str],
    assertion: dict[str, str] | None,
) -> list[str]:
    """Return consistency errors between a decision and its assertion row."""
    prefix = f"line {line}: {row['record_id']}/{row['field']}"
    if assertion is None:
        return [f"{prefix} needs an exact approved assertion"]
    if any(
        row.get(column) != assertion.get(column)
        for column in REVIEW_COLUMNS
    ):
        return [f"{prefix} review provenance disagrees with link-assertions.csv"]
    return []


def expected_current_keys(records: list[dict]) -> set[tuple[str, str]]:
    """Return populated pilot fields plus the deliberate absence control."""
    expected: set[tuple[str, str]] = set()
    for record in records:
        record_id = str(record.get("id"))
        if record_id not in PILOT_RECORD_IDS:
            continue
        for field in FIELDS:
            if record.get(field) not in {None, ""} or record_id == ABSENCE_CONTROL_ID:
                expected.add((record_id, field))
    return expected


def validate(
    records: list[dict],
    rows: list[dict[str, str]],
    assertions: list[dict[str, str]],
) -> list[str]:
    """Return all pilot-selection, decision, and provenance errors."""
    errors: list[str] = []
    by_id = {str(record.get("id")): record for record in records}
    seen: set[tuple[str, str]] = set()

    for line, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f"line {line}: malformed CSV row")
            continue
        record_id = row.get("record_id", "")
        field = row.get("field", "")
        key = (record_id, field)
        if key in seen:
            errors.append(f"line {line}: duplicate pilot decision for {record_id}/{field}")
            continue
        seen.add(key)
        if record_id not in PILOT_RECORD_IDS or record_id not in by_id or field not in FIELDS:
            errors.append(f"line {line}: unknown pilot record or field {record_id}/{field}")
            continue

        candidate = row.get("candidate_value", "")
        decision = row.get("decision", "")
        current_value = by_id[record_id].get(field)
        current = "" if current_value is None else str(current_value)
        prefix = f"line {line}: {record_id}/{field}"

        if decision not in DECISIONS:
            errors.append(f"{prefix} has invalid decision {decision!r}")
            continue
        if not safe_note(row.get("note", "")):
            errors.append(f"{prefix} needs a safe review note")
        if candidate and not valid_candidate(field, candidate):
            errors.append(f"{prefix} has a malformed candidate value")

        if decision == "pending":
            if any(row.get(column) for column in REVIEW_COLUMNS):
                errors.append(f"{prefix} pending decision must not name a review")
            if current and candidate != current:
                errors.append(
                    f"{prefix} pending candidate cannot replace a published value"
                )
            continue

        errors.extend(review_errors(line, row))
        if decision == "approve":
            if not candidate or current != candidate:
                errors.append(f"{prefix} approved candidate disagrees with data.json")
            assertion = assertion_for(assertions, record_id, field, candidate)
            errors.extend(assertion_review_errors(line, row, assertion))
        elif decision == "correct":
            if not candidate or not current or current == candidate:
                errors.append(f"{prefix} correction must replace the pilot candidate")
            assertion = assertion_for(assertions, record_id, field, current)
            errors.extend(assertion_review_errors(line, row, assertion))
        elif decision == "remove":
            if not candidate or current:
                errors.append(f"{prefix} removal must clear the pilot candidate")
        elif decision == "absent" and (candidate or current):
            errors.append(f"{prefix} absence decision must remain empty")

    missing_records = PILOT_RECORD_IDS - {record_id for record_id, _ in seen}
    for record_id in sorted(missing_records, key=int):
        errors.append(f"pilot record {record_id} has no field decisions")
    for record_id, field in sorted(
        expected_current_keys(records) - seen,
        key=lambda item: (int(item[0]), item[1]),
    ):
        errors.append(f"missing pilot decision for {record_id}/{field}")
    return errors


def read_csv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a CSV file and require its exact public column contract."""
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != columns:
            raise ValueError(f"{path.name} expected columns: {', '.join(columns)}")
        return list(reader)


def main() -> int:
    """Validate the tracked catalogue, pilot ledger, and assertion register."""
    try:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        rows = read_csv(PILOT_PATH, COLUMNS)
        assertions = read_csv(ASSERTIONS_PATH, ASSERTION_COLUMNS)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Cannot validate linked-data pilot: {error}", file=sys.stderr)
        return 1

    errors = validate(records, rows, assertions)
    if errors:
        print(f"Linked-data pilot failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    pending = sum(row["decision"] == "pending" for row in rows)
    print(
        f"Linked-data pilot passed for {len(PILOT_RECORD_IDS)} records "
        f"({len(rows)} decisions; {pending} pending)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
