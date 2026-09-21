"""Validate the field-level linked-data pilot review ledger."""

from __future__ import annotations

import csv
import json
from datetime import date

from scripts import validate_linked_data_pilot as validator

REVIEW_URL = (
    "https://github.com/SexyCodicology/"
    "Digitized-Medieval-Manuscripts-app/pull/123#pullrequestreview-1"
)


def pilot_row(
    field: str = "wikidata_qid",
    candidate: str = "Q123",
    decision: str = "pending",
) -> dict[str, str]:
    """Return one synthetic pilot decision."""
    return {
        "record_id": "3",
        "field": field,
        "candidate_value": candidate,
        "decision": decision,
        "reviewer": "" if decision == "pending" else "reviewer",
        "reviewed_on": "" if decision == "pending" else date.today().isoformat(),
        "review_url": "" if decision == "pending" else REVIEW_URL,
        "note": "Confirm the target and scope independently.",
    }


def assertion(field: str, value: str) -> dict[str, str]:
    """Return the review fields needed to match an approved assertion."""
    return {
        "record_id": "3",
        "field": field,
        "value": value,
        "reviewer": "reviewer",
        "reviewed_on": date.today().isoformat(),
        "review_url": REVIEW_URL,
    }


def test_repository_pilot_is_complete_and_pending():
    records = json.loads(validator.DATA_PATH.read_text(encoding="utf-8"))
    with validator.PILOT_PATH.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    with validator.ASSERTIONS_PATH.open(encoding="utf-8", newline="") as source:
        assertions = list(csv.DictReader(source))

    assert len(rows) == 41
    assert all(row["decision"] == "pending" for row in rows)
    assert validator.validate(records, rows, assertions) == []


def test_pending_decision_must_match_data_and_have_no_review(monkeypatch):
    monkeypatch.setattr(validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    row = pilot_row()
    row["reviewer"] = "reviewer"
    errors = validator.validate([{"id": 3, "wikidata_qid": "Q999"}], [row], [])

    assert any("must not name a review" in error for error in errors)
    assert any("disagrees with data.json" in error for error in errors)


def test_approval_requires_an_exact_assertion_and_matching_review(monkeypatch):
    monkeypatch.setattr(validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    row = pilot_row(decision="approve")
    records = [{"id": 3, "wikidata_qid": "Q123"}]

    missing = validator.validate(records, [row], [])
    approved = validator.validate(
        records,
        [row],
        [assertion("wikidata_qid", "Q123")],
    )

    assert any("needs an exact approved assertion" in error for error in missing)
    assert approved == []


def test_correction_requires_a_replacement_assertion(monkeypatch):
    monkeypatch.setattr(validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    row = pilot_row(candidate="Q123", decision="correct")
    records = [{"id": 3, "wikidata_qid": "Q456"}]

    errors = validator.validate(
        records,
        [row],
        [assertion("wikidata_qid", "Q123")],
    )
    corrected = validator.validate(
        records,
        [row],
        [assertion("wikidata_qid", "Q456")],
    )

    assert any("needs an exact approved assertion" in error for error in errors)
    assert corrected == []


def test_removal_and_absence_require_final_review_provenance(monkeypatch):
    monkeypatch.setattr(validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    removed = pilot_row(field="isil", candidate="AU-ANL", decision="remove")
    absent = pilot_row(field="isil", candidate="", decision="absent")

    assert validator.validate([{"id": 3}], [removed], []) == []
    assert validator.validate([{"id": 3}], [absent], []) == []
    absent["review_url"] = "https://example.org/review"
    errors = validator.validate([{"id": 3}], [absent], [])

    assert any("needs a DMMapp PR review URL" in error for error in errors)


def test_duplicate_unknown_and_missing_rows_fail(monkeypatch):
    monkeypatch.setattr(validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    row = pilot_row()
    records = [{"id": 3, "wikidata_qid": "Q123"}]

    duplicate = validator.validate(records, [row, row], [])
    unknown = validator.validate(records, [{**row, "field": "sameAs"}], [])
    missing = validator.validate(records, [], [])

    assert any("duplicate pilot decision" in error for error in duplicate)
    assert any("unknown pilot record or field" in error for error in unknown)
    assert any("missing pilot decision" in error for error in missing)
