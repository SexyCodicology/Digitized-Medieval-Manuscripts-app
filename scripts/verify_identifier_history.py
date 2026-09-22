"""Reject pull requests that discard published record IDs or legacy URLs.

The first release has no baseline registry. Later pull requests compare their
registry with the target branch, so renaming a library can add an alias but
cannot silently remove one that readers may already cite.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = "docs/assets/library-aliases.json"


def compare_aliases(previous: Any, current: Any) -> list[str]:
    """Report published IDs and URL aliases lost from the current registry."""
    if not isinstance(previous, dict) or not isinstance(current, dict):
        return ["both alias registries must be ID-to-alias mappings"]

    errors = []
    for record_id, old_slugs in previous.items():
        new_slugs = current.get(record_id)
        if new_slugs is None:
            errors.append(f"published record ID {record_id} was removed")
        elif (
            not isinstance(old_slugs, list)
            or not isinstance(new_slugs, list)
            or any(not isinstance(slug, str) for slug in [*old_slugs, *new_slugs])
        ):
            errors.append(f"record {record_id} has invalid alias lists")
        else:
            removed = set(old_slugs) - set(new_slugs)
            for slug in sorted(removed):
                errors.append(f"record {record_id} lost published alias {slug}")
    return errors


def git_output(*args: str) -> subprocess.CompletedProcess[str]:
    """Read Git history without using a shell or modifying the checkout."""
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def main(base_commit: str) -> int:
    """Compare a PR's registry to a full Git commit SHA from its base branch."""
    if not re.fullmatch(r"[0-9a-fA-F]{40}", base_commit):
        print("Expected a full 40-character base commit SHA.", file=sys.stderr)
        return 1
    if git_output("cat-file", "-e", f"{base_commit}^{{commit}}").returncode:
        print("Base commit is unavailable; fetch the PR base history.", file=sys.stderr)
        return 1

    baseline = git_output("show", f"{base_commit}:{REGISTRY_PATH}")
    if baseline.returncode:
        # The registry is introduced by this PR. It has no previous aliases.
        print("No baseline alias registry exists yet.")
        return 0

    try:
        previous = json.loads(baseline.stdout)
        current = json.loads((REPO_ROOT / REGISTRY_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot compare alias registries: {error}", file=sys.stderr)
        return 1

    errors = compare_aliases(previous, current)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"Identifier history preserved for {len(previous)} published records.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) == 2 else ""))
