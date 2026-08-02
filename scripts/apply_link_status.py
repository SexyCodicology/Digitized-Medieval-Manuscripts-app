"""Turn a lychee link-check report into proposed is_disabled/last_checked edits.

.github/workflows/link-checker.yml runs this after the weekly check and opens
a pull request with whatever it changes, so a human confirms every status
before it reaches the public site.

Run from the repository root:

    python scripts/apply_link_status.py --report lychee-report.md --today 2026-08-02

Only a response that proves the collection is gone marks a record as broken.
A real report is mostly noise for this purpose: of the 78 errors in the first
run after the check was repaired, 58 were timeouts and 26 were 403/429/5xx,
none of which distinguishes a dead collection from a slow or bot-averse
server. Acting on those would have marked dozens of live collections dead.

Exits non-zero, printing what went wrong, if the report cannot be trusted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"

# Statuses that prove the collection is not at this address any more. A
# timeout, a 403, a 429, or a 5xx says something about the server or the
# network on the day, not about the collection, so none of them appears here.
DEAD_STATUSES = frozenset({"404", "410"})

# "* [404] <https://example.org/x> (at 4864:21) | Rejected status code: ..."
DETAIL_LINE = re.compile(r"^\s*\*\s*\[(?P<status>[^\]]+)\]\s*<(?P<url>[^>]+)>")

# "| 🚫 Errors      | 78    |"
SUMMARY_ROW = re.compile(r"^\s*\|\s*\S*\s*(?P<label>[A-Za-z]+)\s*\|\s*(?P<count>\d+)\s*\|")


class ReportError(RuntimeError):
    """The report cannot be trusted, so no status may be written from it."""


def parse_report(text: str) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Return (url -> statuses seen, summary counts) for a lychee report.

    Raises ReportError rather than returning an empty result, because an
    unparseable report and a clean run look identical downstream, and
    treating the first as the second would quietly mark every link healthy.
    """
    summary: dict[str, int] = {}
    for line in text.splitlines():
        match = SUMMARY_ROW.match(line)
        if match:
            summary[match.group("label").lower()] = int(match.group("count"))

    if "total" not in summary:
        raise ReportError("no summary table found; the report format may have changed")

    by_url: dict[str, set[str]] = {}
    for line in text.splitlines():
        match = DETAIL_LINE.match(line)
        if match:
            by_url.setdefault(match.group("url"), set()).add(match.group("status").upper())

    problems = summary.get("errors", 0) + summary.get("timeouts", 0)
    if problems and not by_url:
        raise ReportError(
            f"summary reports {problems} problem(s) but no detail line could be parsed"
        )

    return by_url, summary


def plan_changes(
    records: list[dict[str, Any]],
    by_url: dict[str, set[str]],
    today: str,
) -> tuple[list[str], list[str]]:
    """Apply the status to ``records`` in place; return (disabled, restored) notes.

    Only a record's own ``website`` is considered. An aggregator URL failing
    says the aggregator is down, not that this library's collection is gone.
    """
    disabled, restored = [], []

    for record in records:
        website = record.get("website")
        if not isinstance(website, str):
            continue
        statuses = by_url.get(website)
        is_dead = bool(statuses and statuses & DEAD_STATUSES)
        was_disabled = record.get("is_disabled") is True

        if is_dead and not was_disabled:
            record["is_disabled"] = True
            record["last_checked"] = today
            disabled.append(
                f"  id {record.get('id')}: {record.get('library')} "
                f"[{', '.join(sorted(statuses))}]"
            )
        elif is_dead and was_disabled:
            # Still dead: refresh the date so the warning shown to a reader
            # reflects the most recent confirmation rather than the first.
            record["last_checked"] = today
        elif was_disabled and statuses is None:
            # Absent from the report's problem list means it responded, so the
            # collection is reachable again.
            record.pop("is_disabled", None)
            record["last_checked"] = today
            restored.append(f"  id {record.get('id')}: {record.get('library')}")

    return disabled, restored


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--today",
        required=True,
        help="ISO date to stamp, supplied by the caller so a run is reproducible",
    )
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    args = parser.parse_args(argv)

    try:
        text = args.report.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Cannot read the link report at {args.report}: {error}", file=sys.stderr)
        return 1

    try:
        by_url, summary = parse_report(text)
    except ReportError as error:
        print(f"Refusing to apply link status: {error}", file=sys.stderr)
        return 1

    records = json.loads(args.data.read_text(encoding="utf-8"))
    disabled, restored = plan_changes(records, by_url, args.today)

    inconclusive = sum(
        1 for statuses in by_url.values() if not statuses & DEAD_STATUSES
    )
    print(f"Checked {summary.get('total', 0)} link(s); {len(by_url)} reported a problem.")
    print(f"Newly marked broken: {len(disabled)}")
    for line in disabled:
        print(line)
    print(f"Reachable again: {len(restored)}")
    for line in restored:
        print(line)
    print(
        f"Left alone as inconclusive: {inconclusive} "
        "(timeouts, 403, 429, and 5xx say nothing about the collection)"
    )

    if disabled or restored:
        args.data.write_text(
            json.dumps(records, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"Updated {args.data}")
    else:
        print("No change proposed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
