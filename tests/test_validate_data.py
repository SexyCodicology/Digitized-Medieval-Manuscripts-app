"""Checks for the shared data-integrity validator in scripts/validate_data.py.

Run with ``pytest`` from the repository root. The script is loaded by path,
matching the convention already used for hooks/library_pages.py in
tests/test_library_pages.py, because scripts/ is not an installed package.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_data", REPO_ROOT / "scripts" / "validate_data.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator()

VALID_RECORD = {
    "id": 1,
    "library": "Bodleian Library",
    "nation": "United Kingdom",
    "city": "Oxford",
    "website": "https://digital.bodleian.ox.ac.uk",
    "copyright": "Public Domain",
    "quantity": "Thousands",
    "iiif": True,
    "is_free_cultural_works_license": True,
    "is_part_of": False,
    "is_part_of_project_name": None,
    "is_part_of_url": None,
}

VALID_PROJECT_RECORD = {
    **VALID_RECORD,
    "id": 2,
    "is_part_of": True,
    "is_part_of_project_name": "Europeana Manuscripts",
    "is_part_of_url": "https://www.europeana.eu/",
}


@pytest.fixture(scope="module")
def schema() -> dict:
    return validator.load_json(REPO_ROOT / "schema.json")


# ── Happy path ────────────────────────────────────────────────────────────


def test_current_production_dataset_passes_unmodified(schema):
    records = validator.load_json(REPO_ROOT / "docs" / "assets" / "data.json")

    errors = validator.validate(schema, records)

    assert errors == []


def test_a_normal_record_passes(schema):
    assert validator.validate(schema, [VALID_RECORD]) == []


def test_a_valid_project_record_passes(schema):
    assert validator.validate(schema, [VALID_PROJECT_RECORD]) == []


# ── Malformed input ───────────────────────────────────────────────────────


def test_missing_required_field_fails(schema):
    record = copy.deepcopy(VALID_RECORD)
    del record["copyright"]

    errors = validator.validate(schema, [record])

    assert any("copyright" in error for error in errors)


def test_unexpected_property_fails(schema):
    record = {**copy.deepcopy(VALID_RECORD), "extra_field": "not allowed"}

    errors = validator.validate(schema, [record])

    assert any("extra_field" in error or "additional" in error.lower() for error in errors)


# ── Trust boundary: URL scheme ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "field, value",
    [
        ("website", "javascript:alert(1)"),
        ("website", "ftp://example.org/manuscripts"),
        ("website", "not-a-url"),
    ],
)
def test_non_http_website_fails(schema, field, value):
    record = {**copy.deepcopy(VALID_RECORD), field: value}

    errors = validator.validate(schema, [record])

    assert errors != []


def test_non_http_project_url_fails(schema):
    record = {**copy.deepcopy(VALID_PROJECT_RECORD), "is_part_of_url": "data:text/html,x"}

    errors = validator.validate(schema, [record])

    assert errors != []


# ── Cross-record: duplicate ids ─────────────────────────────────────────────


def test_duplicate_ids_fail(schema):
    first = copy.deepcopy(VALID_RECORD)
    second = {**copy.deepcopy(VALID_RECORD), "library": "Another Library"}

    errors = validator.validate(schema, [first, second])

    assert any("duplicate id" in error for error in errors)


def test_non_contiguous_ids_remain_valid(schema):
    first = copy.deepcopy(VALID_RECORD)
    second = {**copy.deepcopy(VALID_RECORD), "id": 500, "library": "Another Library"}

    assert validator.validate(schema, [first, second]) == []


@pytest.mark.parametrize("bad_id", [0, -1, 1.5])
def test_non_positive_or_non_integer_id_fails(schema, bad_id):
    record = {**copy.deepcopy(VALID_RECORD), "id": bad_id}

    errors = validator.validate(schema, [record])

    assert errors != []


# ── Project-field consistency ────────────────────────────────────────────────


def test_independent_record_with_null_project_fields_is_valid(schema):
    assert validator.validate(schema, [VALID_RECORD]) == []


def test_is_part_of_true_without_project_name_fails(schema):
    record = {**copy.deepcopy(VALID_PROJECT_RECORD), "id": 9999, "is_part_of_project_name": None}

    errors = validator.check_project_consistency([record])

    assert any("is_part_of_project_name is missing" in error for error in errors)


def test_is_part_of_true_without_project_url_fails(schema):
    record = {**copy.deepcopy(VALID_PROJECT_RECORD), "id": 9999, "is_part_of_url": None}

    errors = validator.check_project_consistency([record])

    assert any("is_part_of_url is missing" in error for error in errors)


def test_is_part_of_false_with_project_name_fails(schema):
    record = {**copy.deepcopy(VALID_RECORD), "id": 9999, "is_part_of_project_name": "Should not be here"}

    errors = validator.check_project_consistency([record])

    assert any("is_part_of_project_name is not null" in error for error in errors)


def test_is_part_of_false_with_project_url_fails(schema):
    record = {**copy.deepcopy(VALID_RECORD), "id": 9999, "is_part_of_url": "https://example.org"}

    errors = validator.check_project_consistency([record])

    assert any("is_part_of_url is not null" in error for error in errors)


def test_known_legacy_exceptions_are_narrowly_scoped():
    """The four previously grandfathered records (14, 338, 585, 584) have
    since been fixed (see issue #37), so no exceptions remain."""
    assert validator.KNOWN_PROJECT_FIELD_EXCEPTIONS == {}


# ── External dependency failure ──────────────────────────────────────────────


def test_a_non_array_dataset_fails(schema):
    errors = validator.validate(schema, {"records": []})

    assert errors != []


def test_malformed_json_raises_system_exit(tmp_path):
    bad_file = tmp_path / "data.json"
    bad_file.write_text("{ not json", encoding="utf-8")

    with pytest.raises(SystemExit):
        validator.load_json(bad_file)


def test_missing_file_raises_system_exit(tmp_path):
    with pytest.raises(SystemExit):
        validator.load_json(tmp_path / "missing.json")


# ── Regression guard: main() exit codes ──────────────────────────────────────


def test_main_returns_zero_for_the_real_dataset():
    assert validator.main() == 0
