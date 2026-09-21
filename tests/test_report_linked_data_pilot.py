"""Render maintainer review packets for the linked-data pilot."""

from __future__ import annotations

import subprocess
import sys

from scripts import report_linked_data_pilot as reporter


def record(record_id: int = 3) -> dict:
    """Return one synthetic catalogue record."""
    return {
        "id": record_id,
        "library": "National | <script>alert(1)</script>",
        "website": "https://example.org/collection",
        "city": "Canberra",
        "nation": "Australia",
        "aggregators": [{"name": "Example portal", "url": "https://example.org"}],
    }


def pilot_row(
    *,
    record_id: str = "3",
    field: str = "wikidata_qid",
    candidate: str = "Q123",
    decision: str = "pending",
) -> dict[str, str]:
    """Return one synthetic pilot row."""
    return {
        "record_id": record_id,
        "field": field,
        "candidate_value": candidate,
        "decision": decision,
        "reviewer": "",
        "reviewed_on": "",
        "review_url": "",
        "note": "Confirm the target | scope.",
    }


def evidence_row() -> dict[str, str]:
    """Return one synthetic evidence row."""
    return {
        "record_id": "3",
        "field": "wikidata_qid",
        "value": "Q123",
        "status": "verified",
        "source_url": "https://www.wikidata.org/wiki/Q123",
        "corroborating_url": "https://example.org/about",
        "checked_on": "2026-09-21",
        "note": "Exact institution candidate.",
    }


def test_report_renders_pending_evidence_and_escapes_tables(monkeypatch):
    monkeypatch.setattr(reporter.pilot_validator, "PILOT_RECORD_IDS", frozenset({"3"}))

    report = reporter.render_report([record()], [pilot_row()], [evidence_row()])

    assert "1 field decision across 1 record; 1 decision remains pending" in report
    assert "## 3: National \\| &lt;script&gt;alert(1)&lt;/script&gt;" in report
    assert "<script>" not in report
    assert "[Source](<https://www.wikidata.org/wiki/Q123>)" in report
    assert "[Corroboration](<https://example.org/about>)" in report
    assert "Confirm the target \\| scope." in report


def test_report_hides_final_decisions_unless_requested(monkeypatch):
    monkeypatch.setattr(reporter.pilot_validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    row = pilot_row(decision="approve")

    pending = reporter.render_report([record()], [row], [evidence_row()])
    complete = reporter.render_report(
        [record()], [row], [evidence_row()], pending_only=False
    )

    assert "No decisions match the selected filters." in pending
    assert "`approve`" in complete


def test_report_uses_candidate_and_website_for_iiif(monkeypatch):
    monkeypatch.setattr(reporter.pilot_validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    manifest = "https://iiif.example.org/manifest"
    row = pilot_row(field="iiif_example_manifest_url", candidate=manifest)

    report = reporter.render_report([record()], [row], [])

    assert f"[Source](<{manifest}>)" in report
    assert "[Corroboration](<https://example.org/collection>)" in report


def test_report_filters_selected_records(monkeypatch):
    monkeypatch.setattr(
        reporter.pilot_validator,
        "PILOT_RECORD_IDS",
        frozenset({"3", "24"}),
    )
    rows = [pilot_row(), pilot_row(record_id="24")]

    report = reporter.render_report(
        [record(), record(24)],
        rows,
        [evidence_row()],
        record_ids={"24"},
    )

    assert "## 24:" in report
    assert "## 3:" not in report


def test_documented_command_runs_from_repository_root():
    result = subprocess.run(
        [
            sys.executable,
            str(reporter.REPO_ROOT / "scripts" / "report_linked_data_pilot.py"),
            "--record-id",
            "3",
        ],
        cwd=reporter.REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "# Linked-data pilot review packet" in result.stdout
    assert "## 3: National Library of Australia" in result.stdout
