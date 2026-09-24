"""Validate the maintainer-approved external assertion register."""

from __future__ import annotations

import csv
import json
from datetime import date, timedelta

from scripts import validate_link_assertions as validator

REVIEW_URL = (
    "https://github.com/SexyCodicology/"
    "Digitized-Medieval-Manuscripts-app/pull/123#pullrequestreview-1"
)


def assertion(field: str, value: str) -> dict[str, str]:
    """Return a complete synthetic maintainer-reviewed assertion."""
    source = {
        "wikidata_qid": f"https://www.wikidata.org/wiki/{value}",
        "geonames_id": f"https://www.geonames.org/{value}/place.html",
    }.get(field, value if field in validator.IIIF_FIELDS else "https://isil.example.org/123")
    return {
        "record_id": "1",
        "field": field,
        "value": value,
        "source_url": source,
        "corroborating_url": "https://library.example.org/about",
        "checked_on": date.today().isoformat(),
        "reviewer": "reviewer",
        "reviewed_on": date.today().isoformat(),
        "review_url": REVIEW_URL,
        "note": "The target describes the holding institution or its city.",
    }


def test_current_catalogue_has_only_reviewed_assertions():
    records = json.loads(validator.DATA_PATH.read_text(encoding="utf-8"))
    with validator.ASSERTIONS_PATH.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    expected = {
        (record_id, field, value)
        for record_id in ("238", "261")
        for field, value in (
            ("isil", "DE-61"),
            ("wikidata_qid", "Q2496254"),
            ("geonames_id", "2934246"),
        )
    }
    expected.add(
        (
            "154",
            "iiif_example_manifest_url",
            "https://api.irht.cnrs.fr/ark:/63955/f3c0etxh8kt0/manifest.json",
        )
    )
    assert {(row["record_id"], row["field"], row["value"]) for row in rows} == expected
    assert validator.validate(records, rows) == []


def test_existing_identifier_can_remain_pending_review():
    record = {"id": 1, "wikidata_qid": "Q123"}

    assert validator.validate([record], []) == []
    assert validator.validate([record], [assertion("wikidata_qid", "Q123")]) == []


def test_approved_iiif_endpoint_requires_the_correct_target_type():
    endpoint = "https://iiif.example.org/collection/123"
    record = {"id": 1, "iiif_collection_url": endpoint}
    row = assertion("iiif_collection_url", endpoint)

    assert validator.validate([record], []) == []
    assert validator.validate([record], [row]) == []
    row["source_url"] = "https://iiif.example.org/collection/other"
    assert any(
        "source has the wrong target type" in error
        for error in validator.validate([record], [row])
    )


def test_authority_source_must_identify_the_asserted_target():
    wikidata = assertion("wikidata_qid", "Q123")
    wikidata["source_url"] = "https://www.wikidata.org/wiki/Q999"
    geonames = assertion("geonames_id", "2640729")
    geonames["source_url"] = "https://www.geonames.org/123/other.html"

    wikidata_errors = validator.validate(
        [{"id": 1, "wikidata_qid": "Q123"}],
        [wikidata],
    )
    geonames_errors = validator.validate(
        [{"id": 1, "geonames_id": 2640729}],
        [geonames],
    )

    assert any("wrong target type" in error for error in wikidata_errors)
    assert any("wrong target type" in error for error in geonames_errors)


def test_unpublished_or_mismatched_row_cannot_stage_a_candidate():
    row = assertion("isil", "DE-12")
    errors = validator.validate([{"id": 1}], [row])
    assert any("disagrees with data.json" in error for error in errors)

    errors = validator.validate([{"id": 1, "isil": "DE-13"}], [row])
    assert any("disagrees with data.json" in error for error in errors)


def test_review_provenance_and_distinct_sources_are_required():
    row = assertion("geonames_id", "123")
    row.update(
        corroborating_url=row["source_url"],
        reviewed_on=(date.today() - timedelta(days=1)).isoformat(),
        reviewer=" ",
        review_url="https://example.org/review/1",
        note="",
    )
    errors = validator.validate([{"id": 1, "geonames_id": 123}], [row])

    assert any("distinct corroborating URL" in error for error in errors)
    assert any("review date after checking" in error for error in errors)
    assert any("GitHub reviewer name" in error for error in errors)
    assert any("DMMapp PR review URL" in error for error in errors)
    assert any("relationship note" in error for error in errors)


def test_public_csv_rejects_formula_like_notes_and_usernames():
    row = assertion("isil", "DE-12")
    row["note"] = "  =HYPERLINK(\"https://attacker.example.org\")"
    row["reviewer"] = "@reviewer"

    errors = validator.validate([{"id": 1, "isil": "DE-12"}], [row])

    assert any("safe relationship note" in error for error in errors)
    assert any("GitHub reviewer name" in error for error in errors)


def test_duplicate_unknown_and_malformed_rows_fail():
    row = assertion("isil", "DE-12")
    records = [{"id": 1, "isil": "DE-12"}]

    errors = validator.validate(records, [row, row])
    assert any("duplicate assertion" in error for error in errors)
    unknown = validator.validate(records, [{**row, "field": "sameAs"}])
    malformed = validator.validate(records, [{**row, None: ["extra"]}])
    assert any("unknown record or field" in error for error in unknown)
    assert any("malformed CSV row" in error for error in malformed)


def test_invalid_urls_and_future_dates_fail():
    row = assertion("isil", "DE-12")
    row["source_url"] = "https://user:pass@registry.example.org/DE-12"
    row["corroborating_url"] = "http://localhost/about"
    row["checked_on"] = (date.today() + timedelta(days=1)).isoformat()
    errors = validator.validate([{"id": 1, "isil": "DE-12"}], [row])

    assert any("public source URL" in error for error in errors)
    assert any("distinct corroborating URL" in error for error in errors)
    assert any("valid check date" in error for error in errors)
