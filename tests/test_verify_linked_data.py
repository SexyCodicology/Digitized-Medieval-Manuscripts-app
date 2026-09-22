"""Exercise release verification against a small generated site fixture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hooks.linked_data import bulk_jsonld, record_jsonld, retired_jsonld
from scripts.verify_linked_data import verify

SITE_URL = "https://example.org/dmmapp/"
RECORD = {
    "id": 42,
    "library": "Example Library",
    "city": "Oxford",
    "nation": "United Kingdom",
    "website": "https://example.org/collection",
}


def write(site: Path, path: str, content: str) -> None:
    """Create one file in the test-only site tree."""
    target = site / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def built_site(
    tmp_path: Path,
    assertions: list[dict[str, str]] | None = None,
    record: dict[str, Any] | None = None,
) -> Path:
    """Build the minimum valid output for one active and one retired ID."""
    current_record = record or RECORD
    active = SITE_URL + "libraries/id-42/"
    retired = SITE_URL + "libraries/id-7/"
    write(
        tmp_path,
        "assets/dmmapp-linked-data.jsonld",
        bulk_jsonld([current_record], SITE_URL, assertions),
    )
    write(
        tmp_path,
        "linked-data/records/42.jsonld",
        record_jsonld(current_record, SITE_URL, assertions),
    )
    write(tmp_path, "linked-data/records/7.jsonld", retired_jsonld("7", SITE_URL))
    write(
        tmp_path,
        "libraries/id-42/index.html",
        f'<link rel="canonical" href="{active}">'
        '<link href="https://example.org/dmmapp/linked-data/records/42.jsonld">',
    )
    write(
        tmp_path,
        "libraries/example-library-42/index.html",
        f'<link rel="canonical" href="{active}">'
        '<a href="../id-42/">Continue</a>',
    )
    write(
        tmp_path,
        "libraries/id-7/index.html",
        "DMMapp no longer lists this access point.",
    )
    write(
        tmp_path,
        "libraries/old-library-7/index.html",
        f'<link rel="canonical" href="{retired}">'
        '<a href="../id-7/">Continue</a>',
    )
    write(tmp_path, "sitemap.xml", f"<loc>{active}</loc>")
    return tmp_path


def test_verifier_accepts_active_and_retired_records(tmp_path):
    site = built_site(tmp_path)

    assert verify(
        site,
        [RECORD],
        {"42": ["example-library-42"], "7": ["old-library-7"]},
        SITE_URL,
    ) == []


def test_verifier_detects_missing_alias_and_retired_tombstone(tmp_path):
    site = built_site(tmp_path)
    (site / "libraries/example-library-42/index.html").unlink()
    (site / "linked-data/records/7.jsonld").unlink()

    errors = verify(
        site,
        [RECORD],
        {"42": ["example-library-42"], "7": ["old-library-7"]},
        SITE_URL,
    )

    assert any("alias example-library-42 is missing" in error for error in errors)
    assert any("retired record 7 is missing" in error for error in errors)


def test_verifier_detects_wrong_bulk_identity(tmp_path):
    site = built_site(tmp_path)
    write(site, "assets/dmmapp-linked-data.jsonld", bulk_jsonld([], SITE_URL))

    errors = verify(site, [RECORD], {"42": ["example-library-42"]}, SITE_URL)

    assert "bulk catalogue record IDs differ from data.json" in errors
    assert "bulk catalogue resources differ from data.json" in errors


def test_verifier_detects_unlicensed_directory_download(tmp_path):
    site = built_site(tmp_path)
    bulk = json.loads(bulk_jsonld([RECORD], SITE_URL))
    bulk["@graph"][0]["dcat:distribution"][0].pop("dcterms:license")
    write(site, "assets/dmmapp-linked-data.jsonld", json.dumps(bulk))

    errors = verify(site, [RECORD], {"42": ["example-library-42"]}, SITE_URL)

    assert any("dmmapp-linked-data.jsonld lacks its CC0 licence" in error for error in errors)


def test_verifier_checks_approved_relationship_provenance(tmp_path):
    assertion = {
        "record_id": "42",
        "field": "geonames_id",
        "value": "2640729",
        "source_url": "https://www.geonames.org/2640729/oxford.html",
        "corroborating_url": "https://example.org/collection",
        "reviewed_on": "2026-09-21",
        "reviewer": "reviewer",
        "review_url": "https://github.com/example/repository/pull/1",
        "note": "The city and collection location agree.",
    }
    record = {**RECORD, "geonames_id": 2640729}
    site = built_site(tmp_path, [assertion], record)

    assert verify(
        site,
        [record],
        {"42": ["example-library-42"], "7": ["old-library-7"]},
        SITE_URL,
        [assertion],
    ) == []
