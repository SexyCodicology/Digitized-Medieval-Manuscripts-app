"""Render a read-only maintainer review packet for the LOD pilot."""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    from scripts import validate_identifier_evidence as evidence_validator
    from scripts import validate_link_assertions as assertion_validator
    from scripts import validate_linked_data_pilot as pilot_validator
except (ImportError, ModuleNotFoundError):  # Direct execution sets scripts/ first.
    import validate_identifier_evidence as evidence_validator  # type: ignore[no-redef]
    import validate_link_assertions as assertion_validator  # type: ignore[no-redef]
    import validate_linked_data_pilot as pilot_validator  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "docs" / "assets" / "data.json"
EVIDENCE_PATH = REPO_ROOT / "research" / "identifier-evidence.csv"
PILOT_PATH = REPO_ROOT / "research" / "linked-data-pilot-review.csv"
ASSERTIONS_PATH = REPO_ROOT / "docs" / "assets" / "link-assertions.csv"


def read_csv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a CSV file and require its exact public column contract."""
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != columns:
            raise ValueError(
                f"{path.name} expected columns: {', '.join(columns)}"
            )
        return list(reader)


def markdown_text(value: object) -> str:
    """Escape a value for use inside a Markdown table cell."""
    escaped = html.escape(str(value), quote=False)
    return escaped.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def code_value(value: str) -> str:
    """Format a candidate value without producing an empty table cell."""
    if not value:
        return "—"
    return f"`{markdown_text(value).replace('`', '&#96;')}`"


def url_value(value: str, label: str) -> str:
    """Format a public evidence URL as a compact Markdown link."""
    if not value:
        return "—"
    destination = (
        value.replace("\\", "%5C")
        .replace("<", "%3C")
        .replace(">", "%3E")
        .replace(" ", "%20")
    )
    return f"[{label}](<{destination}>)"


def record_scope(record: dict) -> str:
    """Describe whether the record is direct or aggregator-specific."""
    aggregators = record.get("aggregators", [])
    if isinstance(aggregators, list):
        names = [
            str(item.get("name", "")).strip()
            for item in aggregators
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        ]
        if names:
            return "Aggregator access point via " + ", ".join(names)
    return "Direct catalogue access point"


def render_report(
    records: list[dict],
    pilot_rows: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    *,
    record_ids: set[str] | None = None,
    pending_only: bool = True,
) -> str:
    """Return a Markdown review packet from the validated pilot sources."""
    records_by_id = {str(record["id"]): record for record in records}
    evidence_by_key = {
        (row["record_id"], row["field"]): row for row in evidence_rows
    }
    selected = [
        row
        for row in pilot_rows
        if (record_ids is None or row["record_id"] in record_ids)
        and (not pending_only or row["decision"] == "pending")
    ]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in selected:
        grouped[row["record_id"]].append(row)

    total_pending = sum(row["decision"] == "pending" for row in pilot_rows)
    decision_label = "decision" if len(pilot_rows) == 1 else "decisions"
    record_label = (
        "record" if len(pilot_validator.PILOT_RECORD_IDS) == 1 else "records"
    )
    pending_label = "decision remains" if total_pending == 1 else "decisions remain"
    lines = [
        "# Linked-data pilot review packet",
        "",
        (
            f"The pilot contains {len(pilot_rows)} field {decision_label} across "
            f"{len(pilot_validator.PILOT_RECORD_IDS)} {record_label}; "
            f"{total_pending} {pending_label} pending. This packet shows "
            f"{len(selected)} decision(s)."
        ),
        "",
        (
            "This report assembles existing evidence for human review. It does "
            "not approve an assertion or establish that an external target is "
            "semantically correct."
        ),
    ]
    if not selected:
        lines.extend(["", "No decisions match the selected filters."])
        return "\n".join(lines) + "\n"

    for record_id in sorted(grouped, key=int):
        record = records_by_id[record_id]
        lines.extend(
            [
                "",
                "## "
                + record_id
                + ": "
                + markdown_text(record.get("library", "Unnamed record")),
                "",
                "- **Access point:** "
                + url_value(str(record.get("website", "")), "Open catalogue website"),
                f"- **Catalogue context:** {markdown_text(record_scope(record))}",
                "- **Listed place:** "
                + markdown_text(record.get("city", ""))
                + ", "
                + markdown_text(record.get("nation", "")),
                "",
                (
                    "| Field | Candidate | Decision | Source | Corroboration | "
                    "Review question |"
                ),
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in grouped[record_id]:
            key = (record_id, row["field"])
            evidence = evidence_by_key.get(key, {})
            candidate = row["candidate_value"]
            if row["field"] in assertion_validator.IIIF_FIELDS:
                source = candidate
                corroborating = str(record.get("website", ""))
            else:
                source = evidence.get("source_url", "")
                corroborating = evidence.get("corroborating_url", "")
            lines.append(
                "| "
                + " | ".join(
                    [
                        code_value(row["field"]),
                        code_value(candidate),
                        code_value(row["decision"]),
                        url_value(source, "Source"),
                        url_value(corroborating, "Corroboration"),
                        markdown_text(row["note"]),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Maintainer next step",
            "",
            (
                "1. Open every cited source and compare its target and scope "
                "with the DMMapp access point."
            ),
            (
                "2. Decide each field independently as `approve`, `correct`, "
                "`remove`, `pending`, or `absent`."
            ),
            (
                "3. Record reviewer provenance only after review through a "
                "public DMMapp pull request."
            ),
            (
                "4. Run the pilot and assertion validators before merging a "
                "final decision."
            ),
            "",
            (
                "DMMapp does not publish `sameAs` between an access point and an "
                "institution, place, portal, or manuscript collection."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    """Parse review-packet filters from the command line."""
    parser = argparse.ArgumentParser(
        description="Render the validated linked-data pilot as Markdown."
    )
    parser.add_argument(
        "--record-id",
        action="append",
        type=int,
        default=[],
        help="Include one pilot record ID; repeat to include more than one.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include final decisions as well as pending decisions.",
    )
    return parser.parse_args()


def main() -> int:
    """Validate the pilot inputs, then print a Markdown review packet."""
    args = parse_args()
    try:
        records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        if not isinstance(records, list) or any(
            not isinstance(record, dict) or not isinstance(record.get("id"), int)
            for record in records
        ):
            raise ValueError("data.json must contain records with numeric IDs")
        evidence_rows = read_csv(EVIDENCE_PATH, evidence_validator.COLUMNS)
        pilot_rows = read_csv(PILOT_PATH, pilot_validator.COLUMNS)
        assertions = read_csv(ASSERTIONS_PATH, assertion_validator.COLUMNS)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Cannot report linked-data pilot: {error}", file=sys.stderr)
        return 1

    errors = [
        *(
            f"evidence: {error}"
            for error in evidence_validator.validate(records, evidence_rows)
        ),
        *(
            f"assertion: {error}"
            for error in assertion_validator.validate(records, assertions)
        ),
        *(
            f"pilot: {error}"
            for error in pilot_validator.validate(records, pilot_rows, assertions)
        ),
    ]
    if errors:
        print(
            f"Cannot report linked-data pilot with {len(errors)} issue(s):",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    record_ids = {str(record_id) for record_id in args.record_id}
    unknown = record_ids - pilot_validator.PILOT_RECORD_IDS
    if unknown:
        values = ", ".join(sorted(unknown, key=int))
        print(f"Unknown pilot record ID(s): {values}", file=sys.stderr)
        return 2

    print(
        render_report(
            records,
            pilot_rows,
            evidence_rows,
            record_ids=record_ids or None,
            pending_only=not args.all,
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
