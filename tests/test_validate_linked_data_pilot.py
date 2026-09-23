"""Validate the field-level linked-data pilot review ledger."""

from __future__ import annotations

import csv
import json
from datetime import date

import pytest

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


def test_repository_pilot_tracks_approved_and_pending_decisions():
    records = json.loads(validator.DATA_PATH.read_text(encoding="utf-8"))
    with validator.PILOT_PATH.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    with validator.ASSERTIONS_PATH.open(encoding="utf-8", newline="") as source:
        assertions = list(csv.DictReader(source))

    assert len(rows) == 41
    approved = {(row["record_id"], row["field"]) for row in rows if row["decision"] == "approve"}
    assert approved == {
        (record_id, field)
        for record_id in ("238", "261")
        for field in ("isil", "wikidata_qid", "geonames_id")
    }
    assert sum(row["decision"] == "pending" for row in rows) == 35
    assert validator.validate(records, rows, assertions) == []


def test_pending_proposal_may_be_unpublished_but_has_no_review(monkeypatch):
    monkeypatch.setattr(validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    manifest = "https://iiif.example.org/manifest"
    row = pilot_row(field="iiif_example_manifest_url", candidate=manifest)

    assert validator.validate([{"id": 3}], [row], []) == []

    row["reviewer"] = "reviewer"
    errors = validator.validate([{"id": 3}], [row], [])

    assert any("must not name a review" in error for error in errors)


def test_pending_candidate_cannot_replace_published_value(monkeypatch):
    monkeypatch.setattr(validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    row = pilot_row()
    errors = validator.validate(
        [{"id": 3, "wikidata_qid": "Q999"}],
        [row],
        [],
    )

    assert any("cannot replace a published value" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "candidate"),
    [
        ("isil", "AUANL"),
        ("wikidata_qid", "q123"),
        ("geonames_id", "0"),
        ("iiif_collection_url", "file:///collection.json"),
        ("iiif_example_manifest_url", "not-a-url"),
    ],
)
def test_pending_candidate_must_have_the_expected_shape(
    monkeypatch,
    field,
    candidate,
):
    monkeypatch.setattr(validator, "PILOT_RECORD_IDS", frozenset({"3"}))
    row = pilot_row(field=field, candidate=candidate)
    errors = validator.validate([{"id": 3}], [row], [])

    assert any("malformed candidate value" in error for error in errors)


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
