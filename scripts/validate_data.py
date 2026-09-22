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
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema.json"
DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"

# Reuse the build hook's slug rules so CI and publication cannot disagree about
# which historical URLs must remain available.
sys.path.insert(0, str(REPO_ROOT))
from hooks.library_pages import build_alias_pages, load_alias_registry, PluginError  # noqa: E402

# An aggregator's url is its canonical home page, so the same aggregator must
# not be recorded with two different URLs across the dataset. schema.json
# validates one record at a time and cannot express a cross-record rule, so it
# lives in check_aggregator_uniqueness() below.
#
# The mapping is normalised aggregator name -> the record ids allowed to
# disagree with the rest of the dataset about that aggregator's URL. It is
# empty because the current data has no conflict; the mechanism is kept so a
# future legitimate exception (an aggregator that genuinely moved, recorded
# both ways during a transition) can be grandfathered narrowly instead of
# silently loosening the rule for every record, present and future.
KNOWN_AGGREGATOR_URL_EXCEPTIONS: dict[str, frozenset[int]] = {}
RECENCY_FIELDS = ("added", "last_edited")


def normalise_aggregator_name(name: str) -> str:
    """Return the form of an aggregator name used to compare two entries."""
    return name.strip().lower()


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


def check_name_fields(records: list) -> list[str]:
    """Reject blank or repeated names within one directory entry."""
    errors = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        record_id = record.get("id")
        preferred = record.get("library")
        if isinstance(preferred, str) and not preferred.strip():
            errors.append(f"record {index} (id: {record_id}): library is blank")
        title = record.get("access_point_title")
        if isinstance(title, str) and not title.strip():
            errors.append(f"record {index} (id: {record_id}): access_point_title is blank")

        names = record.get("library_alternate_names")
        if not isinstance(names, list):
            continue
        seen = {preferred.strip().casefold()} if isinstance(preferred, str) else set()
        for entry in names:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                continue
            name = entry["name"].strip()
            if not name:
                errors.append(
                    f"record {index} (id: {record_id}): alternate name is blank"
                )
            elif name.casefold() in seen:
                errors.append(
                    f"record {index} (id: {record_id}): alternate name "
                    f"{name!r} repeats another institution name"
                )
            seen.add(name.casefold())
    return errors


def check_aggregator_uniqueness(records: list) -> list[str]:
    """Return one message per aggregator naming or URL conflict.

    Two rules that schema.json cannot express, both compared on the name
    normalised by ``normalise_aggregator_name``:

    * within one record, an aggregator must not be listed twice;
    * across the dataset, one aggregator name must resolve to exactly one
      canonical URL, so the same project cannot be recorded under two
      addresses. KNOWN_AGGREGATOR_URL_EXCEPTIONS narrowly exempts named
      records from the second rule.
    """
    errors = []
    # normalised name -> (url, index, id) of the first record that used it.
    canonical: dict[str, tuple[str, int, Any]] = {}

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        record_id = record.get("id")
        aggregators = record.get("aggregators")
        if not isinstance(aggregators, list):
            # Shape is schema.json's job; check_schema has already reported it.
            continue

        seen: set[str] = set()
        for entry in aggregators:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            url = entry.get("url")
            if not isinstance(name, str) or not isinstance(url, str):
                continue
            key = normalise_aggregator_name(name)

            if key in seen:
                errors.append(
                    f"record {index} (id: {record_id}): duplicate aggregator "
                    f"{name!r} listed more than once"
                )
                continue
            seen.add(key)

            if record_id in KNOWN_AGGREGATOR_URL_EXCEPTIONS.get(key, frozenset()):
                continue

            first = canonical.get(key)
            if first is None:
                canonical[key] = (url, index, record_id)
            elif first[0] != url:
                errors.append(
                    f"record {index} (id: {record_id}): aggregator {name!r} uses "
                    f"url {url!r}, but record {first[1]} (id: {first[2]}) uses "
                    f"{first[0]!r}"
                )

    return errors


def check_link_status(records: list) -> list[str]:
    """Return one message per broken-link status inconsistency.

    A reader is told a link is dead and when that was established, so a record
    claiming is_disabled without a usable last_checked would produce an
    undated warning. schema.json checks the shape of last_checked, but its
    "date" format check is only enforced when the runtime supplies that
    format checker, and it cannot express the dependency between the two
    fields; both rules are therefore settled here as well.
    """
    errors = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        record_id = record.get("id")
        disabled = record.get("is_disabled")
        checked = record.get("last_checked")

        if disabled is True and not checked:
            errors.append(
                f"record {index} (id: {record_id}): is_disabled is true but "
                "last_checked is missing"
            )

        if checked is not None:
            if not isinstance(checked, str) or not is_iso_date(checked):
                errors.append(
                    f"record {index} (id: {record_id}): last_checked "
                    f"{checked!r} is not an ISO 8601 date (YYYY-MM-DD)"
                )

    return errors


def check_iiif_links(records: list) -> list[str]:
    """Return consistency errors for explicit IIIF collection and example links."""
    errors = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        record_id = record.get("id")
        for field in (
            "iiif_collection_url",
            "iiif_example_manifest_url",
            "iiif_example_manifest_label",
        ):
            if record.get(field) is not None and record.get("iiif") is not True:
                errors.append(
                    f"record {index} (id: {record_id}): {field} is set but "
                    "iiif must be true"
                )

        example_manifest = record.get("iiif_example_manifest_url")
        example_label = record.get("iiif_example_manifest_label")
        if example_manifest is not None and (
            not isinstance(example_label, str) or not example_label.strip()
        ):
            errors.append(
                f"record {index} (id: {record_id}): "
                "iiif_example_manifest_url requires iiif_example_manifest_label"
            )
        if example_label is not None and example_manifest is None:
            errors.append(
                f"record {index} (id: {record_id}): "
                "iiif_example_manifest_label is set but "
                "iiif_example_manifest_url is missing"
            )
    return errors


def check_recency_dates(records: list) -> list[str]:
    """Return one message per malformed or future homepage recency date."""
    errors = []
    today = date.today()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        record_id = record.get("id")
        for field in RECENCY_FIELDS:
            value = record.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not is_iso_date(value):
                errors.append(
                    f"record {index} (id: {record_id}): {field} {value!r} "
                    "is not an ISO 8601 date (YYYY-MM-DD)"
                )
            elif date.fromisoformat(value) > today:
                errors.append(
                    f"record {index} (id: {record_id}): {field} {value!r} "
                    "must not be in the future"
                )
    return errors


def is_iso_date(value: str) -> bool:
    """Return whether ``value`` is a real calendar date written as YYYY-MM-DD.

    date.fromisoformat accepts only the extended format on Python 3.11, which
    is the version both workflows pin, so a same-day check here matches what
    schema.json's pattern allows.
    """
    try:
        date.fromisoformat(value)
    except (ValueError, TypeError):
        return False
    return True


def validate(schema: dict, records: Any) -> list[str]:
    """Return every validation failure found for ``records`` against ``schema``."""
    if not isinstance(records, list):
        return [f"dataset must be a JSON array, found {type(records).__name__}"]

    return [
        *check_schema(schema, records),
        *check_duplicate_ids(records),
        *check_name_fields(records),
        *check_aggregator_uniqueness(records),
        *check_link_status(records),
        *check_iiif_links(records),
        *check_recency_dates(records),
    ]


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    records = load_json(DATA_PATH)

    errors = validate(schema, records)
    if not errors:
        try:
            aliases = load_alias_registry(str(REPO_ROOT / "docs"))
            missing = {str(record["id"]) for record in records} - aliases.keys()
            if missing:
                errors.append(
                    "alias registry has no entry for IDs: " + ", ".join(sorted(missing))
                )
            else:
                build_alias_pages(records, "https://example.org/", aliases)
        except PluginError as error:
            errors.append(str(error))
    if errors:
        print(f"Data validation failed with {len(errors)} issue(s):", file=sys.stderr)
        for message in errors:
            print(f"  - {message}", file=sys.stderr)
        return 1

    print(f"Data validation passed for {len(records)} records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
