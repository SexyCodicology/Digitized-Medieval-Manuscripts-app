"""Validate docs/assets/data.json against schema.json and the invariants
that JSON Schema cannot express.

Both .github/workflows/validate.yml (pull requests that touch data.json)
and .github/workflows/deploy.yml (the Pages build) call this script as the
single authoritative validation entry point, so a pull request and a
deployment enforce identical rules.

Run directly from the repository root:

    python scripts/validate_data.py

Exits non-zero, listing every violation found (record index, id when
available, and the rule broken) without printing unrelated record content.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema.json"
DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"

# schema.json cannot express "every record except these must satisfy the
# is_part_of project-field rule", so the rule itself lives in
# check_project_consistency() below rather than in a schema if/then. These
# four records predate that rule being enforced anywhere; rewriting existing
# library records is out of scope for validation-tooling work (tracked in
# https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/issues/31),
# so they are grandfathered explicitly instead of silently loosening the rule
# for every record, present and future.
KNOWN_PROJECT_FIELD_EXCEPTIONS: dict[int, frozenset[str]] = {
    14: frozenset({"is_part_of_project_name"}),
    338: frozenset({"is_part_of_project_name"}),
    585: frozenset({"is_part_of_project_name"}),
    584: frozenset({"is_part_of_url"}),
}


def load_json(path: Path) -> Any:
    """Return the parsed contents of ``path``, failing loudly on bad input."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"Cannot read {path}: {error}") from error
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit(f"{path} is not valid JSON: {error}") from error


def check_schema(schema: dict, records: list) -> list[str]:
    """Return one message per per-record schema violation."""
    validator = Draft7Validator(schema["items"], format_checker=FormatChecker())
    errors = []
    for index, record in enumerate(records):
        record_id = record.get("id") if isinstance(record, dict) else None
        for error in validator.iter_errors(record):
            field = "/".join(str(part) for part in error.path) or "<record>"
            errors.append(f"record {index} (id: {record_id}): {field}: {error.message}")
    return errors


def check_duplicate_ids(records: list) -> list[str]:
    """Return one message per id used by more than one record."""
    seen: dict[Any, int] = {}
    errors = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        record_id = record.get("id")
        if record_id in seen:
            errors.append(
                f"record {index} (id: {record_id}): duplicate id, already used by "
                f"record {seen[record_id]}"
            )
        else:
            seen[record_id] = index
    return errors


def check_project_consistency(records: list) -> list[str]:
    """Return one message per is_part_of/project-field inconsistency.

    When is_part_of is true, both project fields must be set. When it is
    false, both must be null. KNOWN_PROJECT_FIELD_EXCEPTIONS narrowly exempts
    specific (id, field) pairs that already violate this on production data.
    """
    errors = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        record_id = record.get("id")
        allowed = KNOWN_PROJECT_FIELD_EXCEPTIONS.get(record_id, frozenset())
        is_part_of = record.get("is_part_of")
        name = record.get("is_part_of_project_name")
        url = record.get("is_part_of_url")

        if is_part_of is True:
            if not url and "is_part_of_url" not in allowed:
                errors.append(
                    f"record {index} (id: {record_id}): is_part_of is true but "
                    "is_part_of_url is missing"
                )
            if not name and "is_part_of_project_name" not in allowed:
                errors.append(
                    f"record {index} (id: {record_id}): is_part_of is true but "
                    "is_part_of_project_name is missing"
                )
        elif is_part_of is False:
            if name is not None and "is_part_of_project_name" not in allowed:
                errors.append(
                    f"record {index} (id: {record_id}): is_part_of is false but "
                    "is_part_of_project_name is not null"
                )
            if url is not None and "is_part_of_url" not in allowed:
                errors.append(
                    f"record {index} (id: {record_id}): is_part_of is false but "
                    "is_part_of_url is not null"
                )
    return errors


def validate(schema: dict, records: Any) -> list[str]:
    """Return every validation failure found for ``records`` against ``schema``."""
    if not isinstance(records, list):
        return [f"dataset must be a JSON array, found {type(records).__name__}"]

    return [
        *check_schema(schema, records),
        *check_duplicate_ids(records),
        *check_project_consistency(records),
    ]


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    records = load_json(DATA_PATH)

    errors = validate(schema, records)
    if errors:
        print(f"Data validation failed with {len(errors)} issue(s):", file=sys.stderr)
        for message in errors:
            print(f"  - {message}", file=sys.stderr)
        return 1

    print(f"Data validation passed for {len(records)} records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
