"""Validate maintainer-approved external link assertions.

The register is deliberately narrower than the catalogue. Existing identifiers
may remain published while their semantic relationships are audited, but only
rows in this register are approved for linked-data publication.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"
ASSERTIONS_PATH = REPO_ROOT / "docs" / "assets" / "link-assertions.csv"
FIELDS = (
    "isil",
    "wikidata_qid",
    "geonames_id",
    "iiif_collection_url",
    "iiif_example_manifest_url",
)
IIIF_FIELDS = frozenset({"iiif_collection_url", "iiif_example_manifest_url"})
COLUMNS = (
    "record_id", "field", "value", "source_url", "corroborating_url",
    "checked_on", "reviewer", "reviewed_on", "review_url", "note",
)
REVIEW_PATH = re.compile(
    r"/SexyCodicology/Digitized-Medieval-Manuscripts-app/pull/[1-9][0-9]*"
    r"(?:/.*)?\Z"
)
REVIEWER_NAME = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\Z")
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")

def valid_url(value: str) -> bool:
    """Return whether a source is an absolute, non-local HTTP(S) URL."""
    try:
        parts = urlsplit(value)
        host = parts.hostname
        if (
            parts.scheme not in {"http", "https"}
            or not host
            or parts.port == 0
            or parts.username
            or parts.password
            or host == "localhost"
            or host.endswith((".localhost", ".local", ".internal"))
        ):
            return False
        try:
            return ip_address(host).is_global
        except ValueError:
            return True
    except ValueError:
        return False


def valid_review_url(value: str) -> bool:
    """Return whether a review URL points to this repository's pull requests."""
    if not valid_url(value):
        return False
    parts = urlsplit(value)
    return (
        parts.scheme == "https"
        and parts.hostname == "github.com"
        and REVIEW_PATH.fullmatch(parts.path) is not None
    )


def source_identifies_target(field: str, value: str, source_url: str) -> bool:
    """Return whether an authority source identifies the asserted target type."""
    try:
        parts = urlsplit(source_url)
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    path_segments = [segment for segment in parts.path.split("/") if segment]
    if field == "wikidata_qid":
        return host == "www.wikidata.org" and any(
            segment == value or segment.startswith(f"{value}.")
            for segment in path_segments
        )
    if field == "geonames_id":
        return host in {"www.geonames.org", "sws.geonames.org"} and bool(
            path_segments and path_segments[0] == value
        )
    if field in IIIF_FIELDS:
        return source_url == value
    return True


def parse_date(value: str) -> date | None:
    """Return a past or present calendar date in extended ISO format."""
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() == value and parsed <= date.today():
            return parsed
    except ValueError:
        pass
    return None


def safe_note(value: str) -> bool:
    """Keep spreadsheet formula prefixes out of the public CSV notes."""
    trimmed = value.lstrip()
    return bool(trimmed) and not trimmed.startswith(CSV_FORMULA_PREFIXES)


def validate(records: list[dict], rows: list[dict[str, str]]) -> list[str]:
    """Return consistency and provenance errors in approved assertions."""
    errors: list[str] = []
    by_id = {str(record["id"]): record for record in records}
    seen: set[tuple[str, str]] = set()

    for line, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f"line {line}: malformed CSV row")
            continue
        record_id = row.get("record_id", "")
        field = row.get("field", "")
        key = (record_id, field)
        if key in seen:
            errors.append(f"line {line}: duplicate assertion for {record_id}/{field}")
            continue
        seen.add(key)
        if record_id not in by_id or field not in FIELDS:
            errors.append(f"line {line}: unknown record or field {record_id}/{field}")
            continue

        value = row.get("value", "")
        published = by_id[record_id].get(field)
        if published is None or value != str(published):
            errors.append(f"line {line}: {record_id}/{field} disagrees with data.json")

        source = row.get("source_url", "")
        corroborating = row.get("corroborating_url", "")
        if not valid_url(source):
            errors.append(f"line {line}: {record_id}/{field} needs a public source URL")
        elif not source_identifies_target(field, value, source):
            errors.append(
                f"line {line}: {record_id}/{field} source has the wrong target type"
            )
        if not valid_url(corroborating) or corroborating == source:
            errors.append(
                f"line {line}: {record_id}/{field} needs a distinct corroborating URL"
            )
        checked = parse_date(row.get("checked_on", ""))
        reviewed = parse_date(row.get("reviewed_on", ""))
        if checked is None:
            errors.append(f"line {line}: {record_id}/{field} needs a valid check date")
        if reviewed is None or (checked is not None and reviewed < checked):
            errors.append(
                f"line {line}: {record_id}/{field} needs a review date after checking"
            )
        if REVIEWER_NAME.fullmatch(row.get("reviewer", "")) is None:
            errors.append(f"line {line}: {record_id}/{field} needs a GitHub reviewer name")
        if not valid_review_url(row.get("review_url", "")):
            errors.append(f"line {line}: {record_id}/{field} needs a DMMapp PR review URL")
        if not safe_note(row.get("note", "")):
            errors.append(f"line {line}: {record_id}/{field} needs a safe relationship note")

    return errors


def main() -> int:
    """Validate the tracked catalogue and approved assertion register."""
    try:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        if not isinstance(records, list) or any(
            not isinstance(record, dict) or not isinstance(record.get("id"), int)
            for record in records
        ):
            raise ValueError("data.json must contain records with numeric IDs")
        with ASSERTIONS_PATH.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise ValueError(f"expected CSV columns: {', '.join(COLUMNS)}")
            rows = list(reader)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Cannot validate link assertions: {error}", file=sys.stderr)
        return 1

    errors = validate(records, rows)
    if errors:
        print(f"Link assertions failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Link assertions passed for {len(records)} records ({len(rows)} reviewed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
