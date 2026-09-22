"""Verify that DMMapp's generated JSON-LD is conservative, parseable RDF."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rdflib import Graph, Literal, Namespace, RDF, URIRef

from hooks import linked_data

REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://example.org/dmmapp/"
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

RECORD = {
    "id": 42,
    "library": "Example Library",
    "city": "Oxford",
    "nation": "United Kingdom",
    "website": "https://source.example.org/manuscripts",
    "copyright": "All Rights Reserved",
    "licence_category": "All Rights Reserved",
    "iiif": True,
    "wikidata_qid": "Q123",
    "isil": "GB-Example",
    "geonames_id": 2640729,
    "iiif_example_manifest_url": "https://source.example.org/iiif/42/manifest",
    "last_checked": "2026-09-20",
}


def parse(document: str) -> Graph:
    """Parse JSON-LD as RDF, not merely as ordinary JSON."""
    return Graph().parse(data=document, format="json-ld")


def test_record_graph_distinguishes_metadata_from_access_point():
    graph = parse(linked_data.record_jsonld(RECORD, SITE_URL))
    page = SITE_URL + "libraries/id-42/"
    record = URIRef(page + "#record")
    access_point = URIRef(page + "#access-point")

    assert (record, RDF.type, DCAT.CatalogRecord) in graph
    assert (record, FOAF.primaryTopic, access_point) in graph
    assert (access_point, RDF.type, DCAT.Resource) in graph
    assert (
        access_point,
        DCTERMS.type,
        URIRef(SITE_URL + "linked-data/#" + linked_data.ACCESS_POINT_TYPE_FRAGMENT),
    ) in graph
    assert (
        access_point,
        DCAT.landingPage,
        URIRef("https://source.example.org/manuscripts"),
    ) in graph
    assert (record, DCTERMS.identifier, Literal("42")) in graph
    assert not list(graph.objects(access_point, DCTERMS.spatial))
    assert list(graph.objects(access_point, DCTERMS.description))


def test_unreviewed_authorities_rights_and_iiif_are_not_asserted():
    document = linked_data.record_jsonld(RECORD, SITE_URL)
    graph = parse(document)

    assert "Q123" not in document
    assert "GB-Example" not in document
    assert "2640729" not in document
    assert "iiif/42/manifest" not in document
    assert "All Rights Reserved" not in document
    assert not list(graph.triples((None, DCTERMS.license, None)))
    assert "sameAs" not in document


def test_approved_assertion_becomes_a_qualified_relation():
    source = "https://www.wikidata.org/wiki/Q123"
    corroborating = "https://source.example.org/about"
    review_url = "https://github.com/example/repository/pull/1"
    assertion = {
        "record_id": "42",
        "field": "wikidata_qid",
        "value": "Q123",
        "source_url": source,
        "corroborating_url": corroborating,
        "reviewed_on": "2026-09-20",
        "reviewer": "reviewer",
        "review_url": review_url,
        "note": "The authority item and official site identify the library.",
    }
    graph = parse(linked_data.record_jsonld(RECORD, SITE_URL, [assertion]))
    access_point = URIRef(SITE_URL + "libraries/id-42/#access-point")
    relations = list(graph.objects(access_point, DCAT.qualifiedRelation))

    assert len(relations) == 1
    relation = relations[0]
    assert (relation, RDF.type, DCAT.Relationship) in graph
    assert (relation, DCTERMS.relation, URIRef("https://www.wikidata.org/entity/Q123")) in graph
    assert (
        relation,
        DCAT.hadRole,
        URIRef(SITE_URL + "linked-data/#holding-institution"),
    ) in graph
    assert (relation, DCTERMS.source, URIRef(source)) in graph
    assert (relation, DCTERMS.source, URIRef(corroborating)) in graph
    assert (relation, DCTERMS.isReferencedBy, URIRef(review_url)) in graph
    assert (
        relation,
        DCTERMS.contributor,
        URIRef("https://github.com/reviewer"),
    ) in graph
    assert list(graph.objects(relation, DCTERMS.modified))
    assert not list(
        graph.triples((None, URIRef("http://www.w3.org/2002/07/owl#sameAs"), None))
    )


def test_assertion_must_match_the_record_and_exact_value():
    assertions = [{
        "record_id": "42",
        "field": "wikidata_qid",
        "value": "Q999",
        "source_url": "https://www.wikidata.org/entity/Q999",
    }]
    graph = parse(linked_data.record_jsonld(RECORD, SITE_URL, assertions))
    access_point = URIRef(SITE_URL + "libraries/id-42/#access-point")

    assert not list(graph.objects(access_point, DCAT.qualifiedRelation))


def test_authority_targets_use_canonical_linked_data_uris():
    assertions = [
        {
            "record_id": "42",
            "field": "wikidata_qid",
            "value": "Q123",
            "source_url": "https://www.wikidata.org/wiki/Q123",
        },
        {
            "record_id": "42",
            "field": "geonames_id",
            "value": "2640729",
            "source_url": "https://www.geonames.org/2640729/oxford.html",
        },
    ]
    graph = parse(linked_data.record_jsonld(RECORD, SITE_URL, assertions))

    assert (
        None,
        DCTERMS.relation,
        URIRef("https://www.wikidata.org/entity/Q123"),
    ) in graph
    assert (
        None,
        DCTERMS.relation,
        URIRef("https://sws.geonames.org/2640729/"),
    ) in graph


def test_hostile_text_is_json_escaped_and_does_not_create_markup():
    hostile = {**RECORD, "library": '</script><script>alert("xss")</script>'}
    document = linked_data.record_jsonld(hostile, SITE_URL)

    assert "<script" not in document
    assert "</script>" not in document
    assert json.loads(document)["@graph"][0]["dcterms:title"] == hostile["library"]
    assert (
        URIRef(SITE_URL + "libraries/id-42/#record"),
        DCTERMS.title,
        Literal(hostile["library"]),
    ) in parse(document)


def test_bulk_graph_contains_every_current_record_and_catalogue_license():
    records = json.loads(
        (REPO_ROOT / "docs" / "assets" / "data.json").read_text(encoding="utf-8")
    )
    graph = parse(linked_data.bulk_jsonld(records, SITE_URL))
    catalog = URIRef(SITE_URL + "#catalog")

    assert (catalog, RDF.type, DCAT.Catalog) in graph
    assert len(list(graph.objects(catalog, DCAT.record))) == len(records)
    resources = {
        URIRef(SITE_URL + f"libraries/id-{record['id']}/#access-point")
        for record in records
    }
    assert set(graph.objects(catalog, DCAT.resource)) == resources
    assert (
        catalog,
        DCTERMS.license,
        URIRef(linked_data.CC0_URL),
    ) in graph
    assert (
        catalog,
        DCTERMS.conformsTo,
        URIRef(linked_data.DCAT3_URL),
    ) in graph
    assert (catalog, DCAT.landingPage, URIRef(SITE_URL)) in graph
    assert list(graph.objects(catalog, DCTERMS.description))
    for path in (
        linked_data.BULK_PATH,
        linked_data.RAW_DATA_PATH,
        linked_data.ASSERTIONS_PATH,
    ):
        assert (
            URIRef(SITE_URL + path),
            DCTERMS.license,
            URIRef(linked_data.CC0_URL),
        ) in graph
    assert all(not list(graph.objects(resource, DCTERMS.license)) for resource in resources)
    assert not list(graph.triples((None, URIRef("http://www.w3.org/2002/07/owl#sameAs"), None)))


def test_retired_record_keeps_its_identifier_without_old_claims():
    graph = parse(linked_data.retired_jsonld("42", SITE_URL))
    record = URIRef(SITE_URL + "libraries/id-42/#record")

    assert (record, RDF.type, DCAT.CatalogRecord) in graph
    assert (record, DCTERMS.identifier, Literal("42")) in graph
    assert not list(graph.objects(record, FOAF.primaryTopic))


@pytest.mark.parametrize(
    "url", ["", "https://example.org/#fragment", "https://example.org/?query=1", "file:///tmp"]
)
def test_invalid_site_url_is_rejected(url):
    with pytest.raises(ValueError):
        linked_data.site_base(url)
