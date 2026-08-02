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
    "aggregators": [],
}

VALID_PROJECT_RECORD = {
    **VALID_RECORD,
    "id": 2,
    "aggregators": [{"name": "Europeana Manuscripts", "url": "https://www.europeana.eu/"}],
}

VALID_MULTI_PROJECT_RECORD = {
    **VALID_RECORD,
    "id": 3,
    "aggregators": [
        {"name": "Europeana Manuscripts", "url": "https://www.europeana.eu/"},
        {"name": "Digital Scriptorium", "url": "https://search.digital-scriptorium.org/"},
    ],
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


def test_a_record_with_several_memberships_passes(schema):
    assert validator.validate(schema, [VALID_MULTI_PROJECT_RECORD]) == []


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


@pytest.mark.parametrize(
    "value",
    ["data:text/html,x", "javascript:alert(1)", "ftp://example.org/", "not-a-url"],
)
def test_non_http_aggregator_url_fails(schema, value):
    record = copy.deepcopy(VALID_PROJECT_RECORD)
    record["aggregators"][0]["url"] = value

    errors = validator.validate(schema, [record])

    assert errors != []


def test_aggregator_entry_without_a_name_fails(schema):
    record = copy.deepcopy(VALID_PROJECT_RECORD)
    del record["aggregators"][0]["name"]

    errors = validator.validate(schema, [record])

    assert errors != []


def test_aggregator_entry_without_a_url_fails(schema):
    record = copy.deepcopy(VALID_PROJECT_RECORD)
    del record["aggregators"][0]["url"]

    errors = validator.validate(schema, [record])

    assert errors != []


def test_aggregator_entry_with_an_unexpected_property_fails(schema):
    record = copy.deepcopy(VALID_PROJECT_RECORD)
    record["aggregators"][0]["note"] = "not allowed"

    errors = validator.validate(schema, [record])

    assert errors != []


def test_an_empty_aggregator_name_fails(schema):
    record = copy.deepcopy(VALID_PROJECT_RECORD)
    record["aggregators"][0]["name"] = ""

    errors = validator.validate(schema, [record])

    assert errors != []


def test_aggregators_must_be_an_array(schema):
    record = {**copy.deepcopy(VALID_RECORD), "aggregators": None}

    errors = validator.validate(schema, [record])

    assert errors != []


def test_a_record_missing_aggregators_fails(schema):
    record = copy.deepcopy(VALID_RECORD)
    del record["aggregators"]

    errors = validator.validate(schema, [record])

    assert any("aggregators" in error for error in errors)


@pytest.mark.parametrize("field", ["is_part_of", "is_part_of_project_name", "is_part_of_url"])
def test_the_legacy_singular_fields_are_now_rejected(schema, field):
    record = {**copy.deepcopy(VALID_RECORD), field: None}

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


# ── Aggregator uniqueness ────────────────────────────────────────────────────


def test_a_record_with_no_memberships_is_valid(schema):
    assert validator.validate(schema, [VALID_RECORD]) == []


def test_the_same_aggregator_listed_twice_on_one_record_fails(schema):
    record = copy.deepcopy(VALID_PROJECT_RECORD)
    record["aggregators"].append(
        {"name": "Europeana Manuscripts", "url": "https://www.europeana.eu/"}
    )

    errors = validator.validate(schema, [record])

    assert any("duplicate aggregator" in error for error in errors)


@pytest.mark.parametrize("variant", ["europeana manuscripts", "  Europeana Manuscripts  "])
def test_duplicate_aggregator_names_are_compared_case_and_space_insensitively(schema, variant):
    record = copy.deepcopy(VALID_PROJECT_RECORD)
    record["aggregators"].append({"name": variant, "url": "https://www.europeana.eu/"})

    errors = validator.check_aggregator_uniqueness([record])

    assert any("duplicate aggregator" in error for error in errors)


def test_two_different_aggregators_on_one_record_are_valid(schema):
    assert validator.check_aggregator_uniqueness([VALID_MULTI_PROJECT_RECORD]) == []


def test_one_aggregator_name_with_conflicting_urls_across_records_fails(schema):
    first = copy.deepcopy(VALID_PROJECT_RECORD)
    second = {
        **copy.deepcopy(VALID_RECORD),
        "id": 9999,
        "aggregators": [{"name": "Europeana Manuscripts", "url": "https://europeana.example/"}],
    }

    errors = validator.validate(schema, [first, second])

    assert any("uses url" in error for error in errors)


def test_a_conflicting_url_is_detected_across_normalised_name_variants(schema):
    first = copy.deepcopy(VALID_PROJECT_RECORD)
    second = {
        **copy.deepcopy(VALID_RECORD),
        "id": 9999,
        "aggregators": [{"name": "EUROPEANA manuscripts", "url": "https://europeana.example/"}],
    }

    errors = validator.check_aggregator_uniqueness([first, second])

    assert any("uses url" in error for error in errors)


def test_the_same_aggregator_url_repeated_across_records_is_valid(schema):
    first = copy.deepcopy(VALID_PROJECT_RECORD)
    second = {**copy.deepcopy(VALID_PROJECT_RECORD), "id": 9999}

    assert validator.check_aggregator_uniqueness([first, second]) == []


def test_a_url_conflict_can_be_grandfathered_by_record_id(schema, monkeypatch):
    first = copy.deepcopy(VALID_PROJECT_RECORD)
    second = {
        **copy.deepcopy(VALID_RECORD),
        "id": 9999,
        "aggregators": [{"name": "Europeana Manuscripts", "url": "https://europeana.example/"}],
    }
    monkeypatch.setattr(
        validator,
        "KNOWN_AGGREGATOR_URL_EXCEPTIONS",
        {"europeana manuscripts": frozenset({9999})},
    )

    assert validator.check_aggregator_uniqueness([first, second]) == []


def test_no_url_exceptions_are_currently_needed():
    """The dataset has no aggregator recorded under two URLs, so the narrow
    escape hatch stays empty; it exists for a future legitimate exception."""
    assert validator.KNOWN_AGGREGATOR_URL_EXCEPTIONS == {}


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


# ── Broken-link status ───────────────────────────────────────────────────────


BROKEN_RECORD = {
    **VALID_RECORD,
    "id": 4,
    "is_disabled": True,
    "last_checked": "2026-08-02",
}


def test_a_record_without_either_link_status_field_is_valid(schema):
    """The dataset's records carry neither field, so omitting both must pass."""
    assert validator.validate(schema, [VALID_RECORD]) == []


def test_a_valid_broken_record_passes(schema):
    assert validator.validate(schema, [BROKEN_RECORD]) == []


def test_a_working_record_may_still_record_when_it_was_checked(schema):
    record = {**copy.deepcopy(VALID_RECORD), "is_disabled": False, "last_checked": "2026-08-02"}

    assert validator.validate(schema, [record]) == []


@pytest.mark.parametrize("missing", [None, ""])
def test_is_disabled_true_without_last_checked_fails(schema, missing):
    record = copy.deepcopy(BROKEN_RECORD)
    if missing is None:
        del record["last_checked"]
    else:
        record["last_checked"] = missing

    errors = validator.validate(schema, [record])

    assert errors != []
    assert any("last_checked is missing" in error for error in errors)


@pytest.mark.parametrize(
    "value",
    [
        "2026-02-30",   # a date that does not exist
        "2026-13-01",   # month out of range
        "02-08-2026",   # the wrong field order
        "2026-8-2",     # not zero-padded
        "not-a-date",
        "2026-08-02T00:00:00Z",
    ],
)
def test_a_last_checked_that_is_not_an_iso_date_fails(schema, value):
    record = {**copy.deepcopy(BROKEN_RECORD), "last_checked": value}

    errors = validator.validate(schema, [record])

    assert errors != []


def test_a_non_string_last_checked_fails(schema):
    record = {**copy.deepcopy(BROKEN_RECORD), "last_checked": 20260802}

    errors = validator.validate(schema, [record])

    assert errors != []


def test_a_non_boolean_is_disabled_fails(schema):
    record = {**copy.deepcopy(VALID_RECORD), "is_disabled": "true"}

    errors = validator.validate(schema, [record])

    assert errors != []


def test_the_date_rule_holds_without_the_schema_format_checker(schema):
    """check_link_status must not rely on jsonschema's optional "date" format
    checker, which silently passes everything when the runtime lacks it."""
    record = {**copy.deepcopy(BROKEN_RECORD), "last_checked": "2026-02-30"}

    errors = validator.check_link_status([record])

    assert any("is not an ISO 8601 date" in error for error in errors)


@pytest.mark.parametrize(
    "value, expected",
    [("2026-08-02", True), ("2026-02-30", False), ("", False), ("2026-8-2", False)],
)
def test_is_iso_date(value, expected):
    assert validator.is_iso_date(value) is expected
