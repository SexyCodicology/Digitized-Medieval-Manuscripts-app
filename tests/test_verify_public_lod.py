"""Check published-release discovery without making network requests."""

from __future__ import annotations

import json

from hooks.linked_data import bulk_jsonld, record_jsonld
from scripts.verify_public_lod import inspect_site, sample_ids

BASE = "https://example.org/dmmapp/"
RECORDS = [
    {
        "id": record_id,
        "library": f"Library {record_id}",
        "city": "Oxford",
        "nation": "United Kingdom",
    }
    for record_id in (1, 42, 99)
]
ALIASES = {str(record["id"]): [f"library-{record['id']}"] for record in RECORDS}
ASSERTIONS = (
    "record_id,field,value,source_url,corroborating_url,checked_on,reviewer,"
    "reviewed_on,review_url,note\n"
)


def responses() -> dict[str, str]:
    """Represent a published release with canonical pages and legacy links."""
    result = {
        BASE + "assets/data.json": json.dumps(RECORDS),
        BASE + "assets/dmmapp-linked-data.jsonld": bulk_jsonld(RECORDS, BASE),
        BASE + "assets/link-assertions.csv": ASSERTIONS,
    }
    sitemap_locations = []
    for record in RECORDS:
        record_id = record["id"]
        page_url = BASE + f"libraries/id-{record_id}/"
        data_url = BASE + f"linked-data/records/{record_id}.jsonld"
        result[page_url] = (
            f'<link rel="canonical" href="{page_url}">'
            f'<link rel="alternate" href="{data_url}">'
        )
        result[data_url] = record_jsonld(record, BASE)
        result[BASE + f"libraries/library-{record_id}/"] = (
            f'<link rel="canonical" href="{page_url}">'
            f'<a href="../id-{record_id}/">Continue</a>'
        )
        sitemap_locations.append(f"<url><loc>{page_url}</loc></url>")
    result[BASE + "sitemap.xml"] = (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(sitemap_locations)
        + "</urlset>"
    )
    return result


def test_sample_ids_are_stable_and_unique():
    assert sample_ids([RECORDS[2], RECORDS[0], RECORDS[1]]) == ["1", "42", "99"]
    assert sample_ids([RECORDS[0]]) == ["1"]
    assert sample_ids([]) == []


def test_public_release_accepts_current_pages_and_data():
    remote = responses()

    assert inspect_site(BASE, RECORDS, ALIASES, ASSERTIONS, remote.__getitem__) == []


def test_public_release_rejects_stale_data_and_missing_alternate():
    remote = responses()
    remote[BASE + "assets/data.json"] = "[]"
    remote[BASE + "libraries/id-42/"] = (
        f'<link rel="canonical" href="{BASE}libraries/id-42/">'
    )

    errors = inspect_site(BASE, RECORDS, ALIASES, ASSERTIONS, remote.__getitem__)

    assert "public data.json does not match the checked-out release" in errors
    assert "public ID page 42 lacks its JSON-LD link" in errors


def test_public_release_rejects_wrong_alias_and_catalogue():
    remote = responses()
    remote[BASE + "libraries/library-1/"] = '<a href="../id-99/">Wrong</a>'
    remote[BASE + "assets/dmmapp-linked-data.jsonld"] = bulk_jsonld([], BASE)

    errors = inspect_site(BASE, RECORDS, ALIASES, ASSERTIONS, remote.__getitem__)

    assert "public JSON-LD catalogue record IDs differ from data.json" in errors
    assert "public alias library-1 has the wrong canonical URL" in errors
    assert "public alias library-1 lacks a visible target" in errors


def test_public_release_rejects_a_stale_assertion_register():
    remote = responses()
    remote[BASE + "assets/link-assertions.csv"] += "stale,row\n"

    errors = inspect_site(BASE, RECORDS, ALIASES, ASSERTIONS, remote.__getitem__)

    assert "public link assertion register does not match the release" in errors
