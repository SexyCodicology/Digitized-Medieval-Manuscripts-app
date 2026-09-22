"""Check evidence for published and proposed direct IIIF endpoints."""

from __future__ import annotations

from datetime import date

from scripts import validate_iiif_evidence as validator

PUBLISHED = "https://iiif.example.org/published/manifest"
PROPOSED = "https://iiif.example.org/proposed/manifest"
COLLECTION = "https://iiif.example.org/collection"


def pilot_row() -> dict[str, str]:
    """Return one pending unpublished IIIF proposal."""
    return {
        "record_id": "2",
        "field": "iiif_example_manifest_url",
        "candidate_value": PROPOSED,
        "decision": "pending",
    }


def evidence_row(
    record_id: str,
    value: str,
    status: str,
    field: str = "iiif_example_manifest_url",
) -> dict[str, str]:
    """Return one synthetic IIIF evidence row."""
    return {
        "record_id": record_id,
        "field": field,
        "value": value,
        "status": status,
        "source_url": value,
        "corroborating_url": f"https://catalogue.example.org/record/{record_id}",
        "checked_on": date.today().isoformat(),
        "note": "The catalogue record and direct Manifest identify the same item.",
    }


def records() -> list[dict]:
    """Return one published endpoint and one proposal-only record."""
    return [
        {"id": 1, "iiif_example_manifest_url": PUBLISHED},
        {"id": 2},
    ]


def test_complete_public_and_proposed_evidence_passes():
    rows = [
        evidence_row("1", PUBLISHED, "verified"),
        evidence_row("2", PROPOSED, "proposed"),
    ]

    assert validator.validate(records(), [pilot_row()], rows) == []


def test_published_collection_requires_verified_evidence():
    rows = [
        evidence_row(
            "1",
            COLLECTION,
            "verified",
            field="iiif_collection_url",
        )
    ]

    errors = validator.validate(
        [{"id": 1, "iiif_collection_url": COLLECTION}],
        [],
        rows,
    )

    assert errors == []


def test_missing_and_extra_evidence_fail():
    missing = validator.validate(
        records(),
        [pilot_row()],
        [evidence_row("1", PUBLISHED, "verified")],
    )
    extra = validator.validate(
        records(),
        [],
        [
            evidence_row("1", PUBLISHED, "verified"),
            evidence_row("2", PROPOSED, "proposed"),
        ],
    )

    assert any("missing IIIF evidence" in error for error in missing)
    assert any("no published or proposed endpoint" in error for error in extra)


def test_public_endpoint_cannot_use_proposed_status():
    row = evidence_row("1", PUBLISHED, "proposed")

    errors = validator.validate(
        [{"id": 1, "iiif_example_manifest_url": PUBLISHED}],
        [],
        [row],
    )

    assert any("must use status 'verified'" in error for error in errors)


def test_evidence_requires_exact_endpoint_and_provenance():
    row = evidence_row("1", PUBLISHED, "verified")
    row.update(
        source_url="https://iiif.example.org/other/manifest",
        corroborating_url=PUBLISHED,
        checked_on="2099-01-01",
        note="=unsafe",
    )

    errors = validator.validate(
        [{"id": 1, "iiif_example_manifest_url": PUBLISHED}],
        [],
        [row],
    )

    assert any("source must be the direct IIIF endpoint" in error for error in errors)
    assert any("must differ from the endpoint" in error for error in errors)
    assert any("invalid checked_on" in error for error in errors)
    assert any("needs a safe evidence note" in error for error in errors)


def test_evidence_rejects_malformed_corroborating_url():
    row = evidence_row("1", PUBLISHED, "verified")
    row["corroborating_url"] = "not-a-url"

    errors = validator.validate(
        [{"id": 1, "iiif_example_manifest_url": PUBLISHED}],
        [],
        [row],
    )

    assert any("needs a public corroborating URL" in error for error in errors)


def test_duplicate_evidence_fails():
    row = evidence_row("1", PUBLISHED, "verified")
    errors = validator.validate(
        [{"id": 1, "iiif_example_manifest_url": PUBLISHED}],
        [],
        [row, row],
    )

    assert any("duplicate IIIF evidence" in error for error in errors)
