"""Require verified evidence when a pull request changes published names."""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_PATH = ROOT / "research" / "name-evidence.csv"
DATA_PATH = "docs/assets/data.json"


def changed_names(previous: list[dict], current: list[dict]) -> set[tuple[str, str, str, str]]:
    """Return newly published preferred names, titles, and alternatives."""
    old = {record["id"]: record for record in previous}
    changes = set()
    for record in current:
        record_id = str(record["id"])
        before = old.get(record["id"], {})
        for field in ("library", "access_point_title"):
            value = record.get(field)
            if value and value != before.get(field):
                changes.add((record_id, field, value, ""))
        old_alternates = {
            (entry["name"], entry.get("language", ""))
            for entry in before.get("library_alternate_names", [])
        }
        for entry in record.get("library_alternate_names", []):
            value = (entry["name"], entry.get("language", ""))
            if value not in old_alternates:
                changes.add((record_id, "library_alternate_names", *value))
    return changes


def compare(previous: list[dict], current: list[dict], rows: list[dict[str, str]]) -> list[str]:
    """Report new names that lack a verified, matching evidence decision."""
    approved = {
        (row["record_id"], row["field"], row["value"], row["language"])
        for row in rows if row["status"] == "verified"
    }
    return [
        f"record {record_id}: changed {field} {value!r} lacks verified name evidence"
        for record_id, field, value, language in sorted(changed_names(previous, current))
        if (record_id, field, value, language) not in approved
    ]


def main(base_commit: str) -> int:
    """Compare current name fields with the supplied full Git base SHA."""
    if not re.fullmatch(r"[0-9a-fA-F]{40}", base_commit):
        print("Expected a full 40-character base commit SHA.", file=sys.stderr)
        return 1
    if subprocess.run(
        ["git", "cat-file", "-e", f"{base_commit}^{{commit}}"],
        cwd=ROOT, capture_output=True, check=False,
    ).returncode:
        print("Base commit is unavailable; fetch the base history.", file=sys.stderr)
        return 1
    baseline = subprocess.run(
        ["git", "show", f"{base_commit}:{DATA_PATH}"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    if baseline.returncode:
        print("No baseline catalogue exists for name comparison.")
        return 0
    try:
        previous = json.loads(baseline.stdout)
        current = json.loads((ROOT / DATA_PATH).read_text(encoding="utf-8"))
        with EVIDENCE_PATH.open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Cannot compare published names: {error}", file=sys.stderr)
        return 1
    errors = compare(previous, current, rows)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("New published names have matching verified evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) == 2 else ""))
