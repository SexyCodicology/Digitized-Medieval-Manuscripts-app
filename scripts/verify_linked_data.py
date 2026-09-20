"""Verify the built linked-data release, not only its source functions.

Run after ``mkdocs build --clean`` from the repository root:

    python scripts/verify_linked_data.py site
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from rdflib import Graph, Literal, Namespace, RDF, URIRef

REPO_ROOT = Path(__file__).resolve().parent.parent
DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
CC0_URL = URIRef("https://creativecommons.org/publicdomain/zero/1.0/")


def parse_graph(path: Path) -> Graph:
    """Parse a built JSON-LD file as RDF, raising on malformed output."""
    return Graph().parse(path, format="json-ld")


def verify(
    site: Path, records: list[dict[str, Any]], aliases: dict[str, list[str]], site_url: str
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
    for path in ("assets/dmmapp-linked-data.jsonld", "assets/data.json"):
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
        if (record_uri, DCTERMS.identifier, Literal(record_id)) not in record_graph:
            errors.append(f"record {record_id} has the wrong identifier")
        if list(record_graph.triples((resource_uri, DCTERMS.license, None))):
            errors.append(f"record {record_id} incorrectly licences source material")
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
        config = yaml.safe_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"Cannot verify linked data: {error}", file=sys.stderr)
        return 1

    errors = verify(site, records, aliases, config["site_url"])
    if errors:
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Linked-data release verified for {len(records)} records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
