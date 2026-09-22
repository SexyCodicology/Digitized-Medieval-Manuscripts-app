"""Verify the built linked-data release, not only its source functions.

Run after ``mkdocs build --clean`` from the repository root:

    python scripts/verify_linked_data.py site
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hooks.linked_data import (  # noqa: E402
    ACCESS_POINT_TYPE_FRAGMENT,
    ROLE_FRAGMENTS,
    ROLE_LABELS,
    assertion_target,
)

DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
CC0_URL = URIRef("https://creativecommons.org/publicdomain/zero/1.0/")
DCAT3_URL = URIRef("https://www.w3.org/TR/vocab-dcat-3/")


def parse_graph(path: Path) -> Graph:
    """Parse a built JSON-LD file as RDF, raising on malformed output."""
    return Graph().parse(path, format="json-ld")


def verify(
    site: Path,
    records: list[dict[str, Any]],
    aliases: dict[str, list[str]],
    site_url: str,
    assertions: list[dict[str, str]] | None = None,
) -> list[str]:
    """Return publication errors for every current record and alias."""
    errors: list[str] = []
    base = site_url.rstrip("/") + "/"
    catalog_uri = URIRef(base + "#catalog")
    bulk = site / "assets" / "dmmapp-linked-data.jsonld"
    try:
        graph = parse_graph(bulk)
    except (OSError, ValueError) as error:
        return [f"cannot parse bulk JSON-LD: {error}"]

    if (catalog_uri, RDF.type, DCAT.Catalog) not in graph:
        errors.append("bulk graph has no DMMapp catalogue")
    if (catalog_uri, DCTERMS.license, CC0_URL) not in graph:
        errors.append("bulk catalogue lacks its CC0 licence")
    if (catalog_uri, DCTERMS.conformsTo, DCAT3_URL) not in graph:
        errors.append("bulk catalogue does not identify its DCAT profile")
    if (catalog_uri, DCAT.landingPage, URIRef(base)) not in graph:
        errors.append("bulk catalogue lacks its landing page")
    if not list(graph.objects(catalog_uri, DCTERMS.description)):
        errors.append("bulk catalogue lacks its description")
    for fragment, label in ROLE_LABELS.items():
        concept = URIRef(base + "linked-data/#" + fragment)
        if (concept, RDF.type, SKOS.Concept) not in graph:
            errors.append(f"bulk graph role concept {fragment} is not typed as skos:Concept")
        if (concept, SKOS.prefLabel, Literal(label)) not in graph:
            errors.append(f"bulk graph role concept {fragment} lacks its skos:prefLabel")
    expected_records = {
        URIRef(base + f"libraries/id-{record['id']}/#record") for record in records
    }
    if set(graph.objects(catalog_uri, DCAT.record)) != expected_records:
        errors.append("bulk catalogue record IDs differ from data.json")
    expected_resources = {
        URIRef(base + f"libraries/id-{record['id']}/#access-point")
        for record in records
    }
    if set(graph.objects(catalog_uri, DCAT.resource)) != expected_resources:
        errors.append("bulk catalogue resources differ from data.json")
    for path in (
        "assets/dmmapp-linked-data.jsonld",
        "assets/data.json",
        "assets/link-assertions.csv",
    ):
        if (URIRef(base + path), DCTERMS.license, CC0_URL) not in graph:
            errors.append(f"bulk distribution {path} lacks its CC0 licence")

    sitemap = site / "sitemap.xml"
    try:
        sitemap_text = sitemap.read_text(encoding="utf-8")
    except OSError as error:
        return [*errors, f"cannot read sitemap: {error}"]

    for record in records:
        record_id = str(record["id"])
        page_url = base + f"libraries/id-{record_id}/"
        page_path = site / "libraries" / f"id-{record_id}" / "index.html"
        linked_path = site / "linked-data" / "records" / f"{record_id}.jsonld"
        try:
            html = page_path.read_text(encoding="utf-8")
            record_graph = parse_graph(linked_path)
        except (OSError, ValueError) as error:
            errors.append(f"record {record_id} has missing or invalid output: {error}")
            continue

        record_uri = URIRef(page_url + "#record")
        resource_uri = URIRef(page_url + "#access-point")
        if (record_uri, RDF.type, DCAT.CatalogRecord) not in record_graph:
            errors.append(f"record {record_id} lacks a DCAT catalogue record")
        if (record_uri, RDF.type, DCAT.CatalogRecord) not in graph:
            errors.append(f"record {record_id} is missing from the bulk graph")
        if (record_uri, FOAF.primaryTopic, resource_uri) not in record_graph:
            errors.append(f"record {record_id} lacks its distinct access point")
        if (record_uri, FOAF.primaryTopic, resource_uri) not in graph:
            errors.append(f"record {record_id} lacks its bulk access-point link")
        if (resource_uri, RDF.type, DCAT.Resource) not in record_graph:
            errors.append(f"record {record_id} has no DCAT access point")
        access_point_type = URIRef(base + "linked-data/#" + ACCESS_POINT_TYPE_FRAGMENT)
        if (resource_uri, DCTERMS.type, access_point_type) not in record_graph:
            errors.append(f"record {record_id} lacks its dcterms:type")
        if (record_uri, DCTERMS.identifier, Literal(record_id)) not in record_graph:
            errors.append(f"record {record_id} has the wrong identifier")
        if list(record_graph.triples((resource_uri, DCTERMS.license, None))):
            errors.append(f"record {record_id} incorrectly licences source material")
        approved = [
            assertion
            for assertion in assertions or []
            if assertion.get("record_id") == record_id
        ]
        expected_relations = {
            URIRef(page_url + f"#relation-{assertion['field']}"): assertion
            for assertion in approved
        }
        actual_relations = set(
            record_graph.objects(resource_uri, DCAT.qualifiedRelation)
        )
        if actual_relations != set(expected_relations):
            errors.append(f"record {record_id} has the wrong approved relationships")
        bulk_relations = set(graph.objects(resource_uri, DCAT.qualifiedRelation))
        if bulk_relations != set(expected_relations):
            errors.append(
                f"record {record_id} has the wrong bulk approved relationships"
            )
        for relation_uri, assertion in expected_relations.items():
            field = assertion["field"]
            target = URIRef(
                assertion_target(field, assertion["value"], assertion["source_url"])
            )
            role = URIRef(base + "linked-data/#" + ROLE_FRAGMENTS[field])
            sources = {
                URIRef(assertion["source_url"]),
                URIRef(assertion["corroborating_url"]),
            }
            contributor = URIRef(f"https://github.com/{assertion['reviewer']}")
            review = URIRef(assertion["review_url"])
            note = Literal(assertion["note"])
            for relation_graph, label in (
                (record_graph, "record graph"),
                (graph, "bulk graph"),
            ):
                if (relation_uri, RDF.type, DCAT.Relationship) not in relation_graph:
                    errors.append(
                        f"record {record_id} relation is untyped in the {label}"
                    )
                if (relation_uri, DCTERMS.relation, target) not in relation_graph:
                    errors.append(
                        f"record {record_id} relation has the wrong target in the {label}"
                    )
                if (relation_uri, DCAT.hadRole, role) not in relation_graph:
                    errors.append(
                        f"record {record_id} relation has the wrong role in the {label}"
                    )
                if set(relation_graph.objects(relation_uri, DCTERMS.source)) != sources:
                    errors.append(
                        f"record {record_id} relation lacks evidence in the {label}"
                    )
                reviewed = Literal(assertion["reviewed_on"], datatype=XSD.date)
                if (relation_uri, DCTERMS.modified, reviewed) not in relation_graph:
                    errors.append(
                        f"record {record_id} relation lacks its review date in the {label}"
                    )
                if (
                    relation_uri,
                    DCTERMS.contributor,
                    contributor,
                ) not in relation_graph:
                    errors.append(
                        f"record {record_id} relation lacks its reviewer in the {label}"
                    )
                if (relation_uri, DCTERMS.isReferencedBy, review) not in relation_graph:
                    errors.append(
                        f"record {record_id} relation lacks its review URL in the {label}"
                    )
                if (relation_uri, DCTERMS.description, note) not in relation_graph:
                    errors.append(
                        f"record {record_id} relation lacks its note in the {label}"
                    )
        if f'rel="canonical" href="{page_url}"' not in html:
            errors.append(f"record {record_id} lacks its canonical HTML URL")
        alternate = base + f"linked-data/records/{record_id}.jsonld"
        if f'href="{alternate}"' not in html:
            errors.append(f"record {record_id} lacks its JSON-LD alternate")
        if f"<loc>{page_url}</loc>" not in sitemap_text:
            errors.append(f"record {record_id} is missing from the sitemap")

        for slug in aliases.get(record_id, []):
            alias_path = site / "libraries" / slug / "index.html"
            try:
                alias_html = alias_path.read_text(encoding="utf-8")
            except OSError as error:
                errors.append(f"alias {slug} is missing: {error}")
                continue
            if f'rel="canonical" href="{page_url}"' not in alias_html:
                errors.append(f"alias {slug} has the wrong canonical target")
            if f'href="../id-{record_id}/"' not in alias_html:
                errors.append(f"alias {slug} has no reader-visible target")

    active_ids = {str(record["id"]) for record in records}
    for retired_id in aliases.keys() - active_ids:
        retired_page = site / "libraries" / f"id-{retired_id}" / "index.html"
        retired_data = site / "linked-data" / "records" / f"{retired_id}.jsonld"
        try:
            retired_html = retired_page.read_text(encoding="utf-8")
            retired_graph = parse_graph(retired_data)
        except (OSError, ValueError) as error:
            errors.append(f"retired record {retired_id} is missing: {error}")
            continue
        retired_uri = URIRef(base + f"libraries/id-{retired_id}/#record")
        if "no longer lists this access point" not in retired_html:
            errors.append(f"retired record {retired_id} lacks a withdrawal notice")
        if (retired_uri, RDF.type, DCAT.CatalogRecord) not in retired_graph:
            errors.append(f"retired record {retired_id} lacks a JSON-LD tombstone")
        if list(retired_graph.objects(retired_uri, FOAF.primaryTopic)):
            errors.append(f"retired record {retired_id} still asserts an access point")

    if re.search(r'"(?:owl:)?sameAs"', bulk.read_text(encoding="utf-8")):
        errors.append("bulk graph contains an unreviewed identity assertion")
    return errors


def main() -> int:
    """Check a built site and print a concise publication result."""
    site = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "site"
    try:
        records = json.loads(
            (REPO_ROOT / "docs" / "assets" / "data.json").read_text(encoding="utf-8")
        )
        aliases = json.loads(
            (REPO_ROOT / "docs" / "assets" / "library-aliases.json").read_text(
                encoding="utf-8"
            )
        )
        with (REPO_ROOT / "docs" / "assets" / "link-assertions.csv").open(
            encoding="utf-8",
            newline="",
        ) as source:
            assertions = list(csv.DictReader(source))
        config = yaml.safe_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"Cannot verify linked data: {error}", file=sys.stderr)
        return 1

    errors = verify(site, records, aliases, config["site_url"], assertions)
    if errors:
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Linked-data release verified for {len(records)} records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
