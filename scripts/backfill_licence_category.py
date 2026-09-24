"""Populate normalised licence categories from DMMapp's verbatim rights data.

Run once from the repository root after adding a new mapping:

    python scripts/backfill_licence_category.py

The mapping is deliberately exhaustive for the dataset rather than using
heuristics. A new rights string must be reviewed and mapped explicitly before
this script may write data, so uncertainty is not silently relabelled as
``Unknown``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"

LICENCE_CATEGORIES = frozenset(
    {
        "CC0",
        "CC-BY",
        "CC-BY-NC",
        "CC-BY-NC-SA",
        "CC-BY-NC-ND",
        "All Rights Reserved",
        "Mixed/Item-specific",
        "Unknown",
    }
)

# Keep every current verbatim string here. CC BY-SA is grouped with CC-BY
# because the controlled vocabulary has no standalone CC-BY-SA category.
COPYRIGHT_TO_LICENCE_CATEGORY = {
    "All Rights Reserved": "All Rights Reserved",
    "All Rights Reserved, some images: Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)": "Mixed/Item-specific",
    "Attribution 4.0 International (CC BY 4.0)": "CC-BY",
    "Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)": "CC-BY-NC",
    "Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)": "CC-BY-NC-SA",
    "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)": "CC-BY",
    "CC BY 4.0": "CC-BY",
    "CC BY-NC": "CC-BY-NC",
    "CC BY-NC 3.0": "CC-BY-NC",
    "CC BY-NC 4.0": "CC-BY-NC",
    "CC BY-NC 4.0 and CC BY 2.0 (item-specific)": "Mixed/Item-specific",
    "CC BY-NC-ND": "CC-BY-NC-ND",
    "CC BY-NC-ND 2.0 AT, CC BY-NC-ND 4.0, and Unknown (item-specific)": "Mixed/Item-specific",
    "CC BY-NC-SA 4.0": "CC-BY-NC-SA",
    "CC BY-NC-SA 4.0 and NoC-NC 1.0 (item-specific)": "Mixed/Item-specific",
    "CC-BY": "CC-BY",
    "CC0 1.0": "CC0",
    "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication": "CC0",
    "Non-commercial reuse with attribution": "CC-BY-NC",
    "Private study only (ISOS)": "All Rights Reserved",
    "Public Domain": "CC0",
    "Public Domain Mark 1.0": "CC0",
    "Public Domain Mark 1.0 / CC BY 4.0": "Mixed/Item-specific",
    "Unknown": "Unknown",
}


def backfill_licence_categories(records: list[dict[str, Any]]) -> list[str]:
    """Add a category to each record and return any unmapped rights strings."""
    unmapped = sorted(
        {
            copyright
            for record in records
            if isinstance((copyright := record.get("copyright")), str)
            and copyright not in COPYRIGHT_TO_LICENCE_CATEGORY
        }
    )
    if unmapped:
        return unmapped

    for record in records:
        copyright = record.get("copyright")
        if not isinstance(copyright, str):
            continue
        record["licence_category"] = COPYRIGHT_TO_LICENCE_CATEGORY[copyright]

    return []


def main(argv: list[str] | None = None) -> int:
    """Write category values after verifying that every copyright is mapped."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    args = parser.parse_args(argv)

    try:
        records = json.loads(args.data.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"Cannot read {args.data}: {error}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(f"{args.data} is not valid JSON: {error}", file=sys.stderr)
        return 1

    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        print(f"{args.data} must contain an array of objects", file=sys.stderr)
        return 1

    unmapped = backfill_licence_categories(records)
    if unmapped:
        print("Refusing to write: add explicit mappings for:", file=sys.stderr)
        for copyright in unmapped:
            print(f"  {copyright!r}", file=sys.stderr)
        return 1

    args.data.write_text(
        json.dumps(records, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Updated {len(records)} record(s) in {args.data}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
