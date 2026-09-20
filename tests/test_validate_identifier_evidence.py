"""Check completeness and agreement of the identifier research ledger."""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "validate_identifier_evidence", REPO_ROOT / "scripts" / "validate_identifier_evidence.py"
)
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def decisions() -> list[dict[str, str]]:
    today = date.today().isoformat()
    return [
        {
            "record_id": "1", "field": field, "value": "", "status": "unresolved",
            "source_url": "", "corroborating_url": "", "checked_on": today,
            "note": "No reliable match verified.",
        }
        for field in validator.FIELDS
    ]


def test_complete_unresolved_ledger_passes():
    assert validator.validate([{"id": 1}], decisions()) == []


def test_verified_identifier_requires_source_and_data_agreement():
    rows = decisions()
    rows[0].update(
        value="O-FITHE", status="verified", source_url="https://example.org/registry/O-FITHE",
        note="Exact institution verified in registry.",
    )

    assert validator.validate([{"id": 1, "isil": "O-FITHE"}], rows) == []

    rows[0]["value"] = "O-OTHER"
    assert any("disagrees" in error for error in validator.validate([{"id": 1, "isil": "O-FITHE"}], rows))


def test_wikidata_identifier_needs_independent_corroboration():
    rows = decisions()
    rows[1].update(value="Q82133", status="verified", source_url="https://www.wikidata.org/wiki/Q82133")

    errors = validator.validate([{"id": 1, "wikidata_qid": "Q82133"}], rows)

    assert any("corroborating URL" in error for error in errors)


def test_missing_and_duplicate_decisions_fail():
    rows = decisions()
    rows.pop()
    rows.append(rows[0].copy())

    errors = validator.validate([{"id": 1}], rows)

    assert any("missing decision" in error for error in errors)
    assert any("duplicate decision" in error for error in errors)


def test_unknown_field_and_invalid_source_url_fail():
    rows = decisions()
    rows[0].update(value="O-FITHE", status="verified", source_url="not-a-url")
    rows[1]["field"] = "external_id"

    errors = validator.validate([{"id": 1, "isil": "O-FITHE"}], rows)

    assert any("needs a source URL" in error for error in errors)
    assert any("unknown record or field" in error for error in errors)
    assert any("missing decision" in error for error in errors)


def test_unresolved_decision_needs_reason_and_no_data_value():
    rows = decisions()
    rows[0]["note"] = ""

    errors = validator.validate([{"id": 1, "isil": "O-FITHE"}], rows)

    assert any("must have no identifier" in error for error in errors)
    assert any("needs a reason" in error for error in errors)
