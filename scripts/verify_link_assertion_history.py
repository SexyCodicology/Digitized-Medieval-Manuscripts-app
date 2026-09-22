"""Require approval for new or changed authority and IIIF links.

Values already present in the base revision may remain public while DMMapp
maintainers audit them. This comparison prevents later catalogue changes from
expanding that unreviewed set.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_link_assertions import COLUMNS, FIELDS  # noqa: E402

DATA_PATH = "docs/assets/data.json"
ASSERTIONS_PATH = REPO_ROOT / "docs" / "assets" / "link-assertions.csv"


def approved_keys(rows: list[dict[str, str]]) -> set[tuple[str, str, str]]:
    """Return exact record, field, and value keys from approved rows."""
    return {
        (row["record_id"], row["field"], row["value"])
        for row in rows
        if all(column in row for column in ("record_id", "field", "value"))
    }


def compare_links(
    previous: Any,
    current: Any,
    reviewed: set[tuple[str, str, str]],
) -> list[str]:
    """Report new or changed links that have no exact approved assertion."""
    if not isinstance(previous, list) or not isinstance(current, list):
        return ["both data files must contain lists of records"]
    if any(not isinstance(record, dict) for record in [*previous, *current]):
        return ["both data files must contain record objects"]

    old_by_id = {str(record.get("id")): record for record in previous}
    errors: list[str] = []
    for record in current:
        record_id = str(record.get("id"))
        old_record = old_by_id.get(record_id, {})
        for field in FIELDS:
            value = record.get(field)
            if value is None or value == old_record.get(field):
                continue
            key = (record_id, field, str(value))
            if key not in reviewed:
                errors.append(
                    f"new or changed {record_id}/{field} lacks maintainer approval"
                )
    return errors


def git_output(*args: str) -> subprocess.CompletedProcess[str]:
    """Read Git history without using a shell or modifying the checkout."""
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def main(base_commit: str) -> int:
    """Compare current external links with a full base commit SHA."""
    if not re.fullmatch(r"[0-9a-fA-F]{40}", base_commit):
        print("Expected a full 40-character base commit SHA.", file=sys.stderr)
        return 1
    if git_output("cat-file", "-e", f"{base_commit}^{{commit}}").returncode:
        print("Base commit is unavailable; fetch the PR base history.", file=sys.stderr)
        return 1

    baseline = git_output("show", f"{base_commit}:{DATA_PATH}")
    if baseline.returncode:
        print("Base data.json is unavailable at the supplied commit.", file=sys.stderr)
        return 1

    try:
        previous = json.loads(baseline.stdout)
        current = json.loads((REPO_ROOT / DATA_PATH).read_text(encoding="utf-8"))
        with ASSERTIONS_PATH.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise ValueError(f"expected CSV columns: {', '.join(COLUMNS)}")
            reviewed = approved_keys(list(reader))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Cannot compare reviewed link history: {error}", file=sys.stderr)
        return 1

    errors = compare_links(previous, current, reviewed)
    if errors:
        print(f"Link assertion history failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("New and changed authority and IIIF links have maintainer approval.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) == 2 else ""))
