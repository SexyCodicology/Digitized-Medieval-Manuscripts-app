"""Build conservative linked-data descriptions from DMMapp directory records.

The DMMapp record and the access point it describes are different resources.
Neither is the holding institution or an individual manuscript. Keeping those
identities separate prevents an unreviewed catalogue URL or name from turning
into a false equivalence assertion.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File, Files

CONTEXT = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dcterms": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
}
CC0_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
DCAT3_URL = "https://www.w3.org/TR/vocab-dcat-3/"
JSONLD_MEDIA_TYPE = "https://www.iana.org/assignments/media-types/application/ld+json"
JSON_MEDIA_TYPE = "https://www.iana.org/assignments/media-types/application/json"
CSV_MEDIA_TYPE = "https://www.iana.org/assignments/media-types/text/csv"
XSD_DATE = "http://www.w3.org/2001/XMLSchema#date"
RAW_DATA_PATH = "assets/data.json"
ALIAS_REGISTRY_PATH = "assets/library-aliases.json"
ASSERTIONS_PATH = "assets/link-assertions.csv"
BULK_PATH = "assets/dmmapp-linked-data.jsonld"
RECORD_PATH = "linked-data/records/{id}.jsonld"
ASSERTION_COLUMNS = (
    "record_id", "field", "value", "source_url", "corroborating_url",
    "checked_on", "reviewer", "reviewed_on", "review_url", "note",
)
ROLE_FRAGMENTS = {
    "isil": "institution-authority-record",
    "wikidata_qid": "holding-institution",
    "geonames_id": "listed-place",
    "iiif_collection_url": "iiif-collection",
    "iiif_example_manifest_url": "iiif-example-manifest",
}


def site_base(site_url: str) -> str:
    """Return an absolute site URL with one trailing slash."""
    parsed = urlsplit(site_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("site_url must be an absolute HTTP(S) URL")
    return site_url.rstrip("/") + "/"


def page_path(record_id: int) -> str:
    """Return the stable human-page path for a record ID."""
    return f"libraries/id-{record_id}/"


def page_url(site_url: str, record_id: int) -> str:
    """Return the stable human-page URL for a record ID."""
    return site_base(site_url) + page_path(record_id)


def record_graph(
    record: dict[str, Any],
    site_url: str,
    assertions: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Describe one DMMapp record and its catalogued access point.

    The website is a landing page, not an identity link or a rights claim.
    Authority and IIIF links are emitted only from separately reviewed
    assertions, never inferred from optional catalogue fields alone.
    """
    base = page_url(site_url, record["id"])
    access_point: dict[str, Any] = {
        "@id": base + "#access-point",
        "@type": "dcat:Resource",
        "dcterms:title": record["library"],
        "dcterms:description": (
            "A directory-listed access point to digitized medieval manuscripts "
            f"associated with {record['city']}, {record['nation']}."
        ),
    }
    website = record.get("website")
    if isinstance(website, str) and _is_http_url(website):
        access_point["dcat:landingPage"] = {"@id": website}

    relationships = _approved_relationships(record, site_url, assertions or [])
    if relationships:
        access_point["dcat:qualifiedRelation"] = relationships

    catalogue_record: dict[str, Any] = {
        "@id": base + "#record",
        "@type": "dcat:CatalogRecord",
        "dcterms:identifier": str(record["id"]),
        "dcterms:title": record["library"],
        "foaf:primaryTopic": {"@id": access_point["@id"]},
    }
    if record.get("added"):
        catalogue_record["dcterms:issued"] = record["added"]
    if record.get("last_edited"):
        catalogue_record["dcterms:modified"] = record["last_edited"]

    return [catalogue_record, access_point]


def _approved_relationships(
    record: dict[str, Any],
    site_url: str,
    assertions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Build qualified relations that exactly match approved catalogue values."""
    relationships = []
    for assertion in assertions:
        field = assertion.get("field", "")
        value = assertion.get("value", "")
        source = assertion.get("source_url", "")
        if (
            assertion.get("record_id") != str(record["id"])
            or field not in ROLE_FRAGMENTS
            or str(record.get(field, "")) != value
            or not isinstance(source, str)
            or not _is_http_url(source)
        ):
            continue
        target = assertion_target(field, value, source)
        relationship: dict[str, Any] = {
            "@id": page_url(site_url, record["id"]) + f"#relation-{field}",
            "@type": "dcat:Relationship",
            "dcterms:relation": {"@id": target},
            "dcat:hadRole": {
                "@id": site_base(site_url)
                + "linked-data/#"
                + ROLE_FRAGMENTS[field]
            },
            "dcterms:source": [{"@id": source}],
        }
        corroborating = assertion.get("corroborating_url", "")
        if isinstance(corroborating, str) and _is_http_url(corroborating):
            relationship["dcterms:source"].append({"@id": corroborating})
        reviewed_on = assertion.get("reviewed_on", "")
        if reviewed_on:
            relationship["dcterms:modified"] = {
                "@value": reviewed_on,
                "@type": XSD_DATE,
            }
        review_url = assertion.get("review_url", "")
        if isinstance(review_url, str) and _is_http_url(review_url):
            relationship["dcterms:isReferencedBy"] = {"@id": review_url}
        reviewer = assertion.get("reviewer", "")
        if reviewer:
            relationship["dcterms:contributor"] = {
                "@id": f"https://github.com/{reviewer}"
            }
        note = assertion.get("note", "")
        if note:
            relationship["dcterms:description"] = note
        relationships.append(relationship)
    return relationships


def assertion_target(field: str, value: str, source_url: str) -> str:
    """Return the canonical RDF target for an approved assertion."""
    if field == "wikidata_qid":
        return f"https://www.wikidata.org/entity/{value}"
    if field == "geonames_id":
        return f"https://sws.geonames.org/{value}/"
    if field in {"iiif_collection_url", "iiif_example_manifest_url"}:
        return value
    return source_url


def _is_http_url(value: str) -> bool:
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return parts.scheme.lower() in {"http", "https"} and bool(parts.netloc)


def record_jsonld(
    record: dict[str, Any],
    site_url: str,
    assertions: list[dict[str, str]] | None = None,
) -> str:
    """Serialise one record as a standalone JSON-LD graph."""
    document = {
        "@context": CONTEXT,
        "@graph": record_graph(record, site_url, assertions),
    }
    return _serialize(document)


def retired_jsonld(record_id: str, site_url: str) -> str:
    """Keep the record URI dereferenceable after a catalogue withdrawal."""
    document = {
        "@context": CONTEXT,
        "@graph": [{
            "@id": page_url(site_url, int(record_id)) + "#record",
            "@type": "dcat:CatalogRecord",
            "dcterms:identifier": record_id,
            "dcterms:description": "This DMMapp directory record has been withdrawn.",
        }],
    }
    return _serialize(document)


def bulk_jsonld(
    records: list[dict[str, Any]],
    site_url: str,
    assertions: list[dict[str, str]] | None = None,
) -> str:
    """Serialise the catalog, distribution, and all directory records."""
    base = site_base(site_url)
    catalog = {
        "@id": base + "#catalog",
        "@type": "dcat:Catalog",
        "dcterms:title": "DMMapp digitized manuscript access directory",
        "dcterms:description": (
            "A curated directory of online access points to digitized medieval "
            "manuscript collections."
        ),
        "dcterms:license": {"@id": CC0_URL},
        "dcterms:conformsTo": {"@id": DCAT3_URL},
        "dcat:landingPage": {"@id": base},
        "dcat:record": [
            {"@id": page_url(base, record["id"]) + "#record"}
            for record in records
        ],
        "dcat:resource": [
            {"@id": page_url(base, record["id"]) + "#access-point"}
            for record in records
        ],
        "dcat:distribution": [
            {
                "@id": base + BULK_PATH,
                "@type": "dcat:Distribution",
                "dcterms:title": "DMMapp bulk JSON-LD",
                "dcat:downloadURL": {"@id": base + BULK_PATH},
                "dcat:mediaType": {"@id": JSONLD_MEDIA_TYPE},
                "dcterms:license": {"@id": CC0_URL},
            },
            {
                "@id": base + RAW_DATA_PATH,
                "@type": "dcat:Distribution",
                "dcterms:title": "DMMapp source catalogue JSON",
                "dcat:downloadURL": {"@id": base + RAW_DATA_PATH},
                "dcat:mediaType": {"@id": JSON_MEDIA_TYPE},
                "dcterms:license": {"@id": CC0_URL},
            },
            {
                "@id": base + ASSERTIONS_PATH,
                "@type": "dcat:Distribution",
                "dcterms:title": "DMMapp reviewed link assertion register",
                "dcat:downloadURL": {"@id": base + ASSERTIONS_PATH},
                "dcat:mediaType": {"@id": CSV_MEDIA_TYPE},
                "dcterms:license": {"@id": CC0_URL},
            },
        ],
    }
    graph = [catalog]
    for record in records:
        graph.extend(record_graph(record, base, assertions))
    return _serialize({"@context": CONTEXT, "@graph": graph})


def _serialize(document: dict[str, Any]) -> str:
    """Keep contributed text inert even if a future template embeds JSON-LD."""
    result = json.dumps(document, ensure_ascii=False, indent=2)
    return result.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026") + "\n"


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Add static JSON-LD representations to the MkDocs build."""
    source = Path(config.docs_dir) / RAW_DATA_PATH
    registry_path = Path(config.docs_dir) / ALIAS_REGISTRY_PATH
    assertions_path = Path(config.docs_dir) / ASSERTIONS_PATH
    try:
        records = json.loads(source.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise PluginError(f"Cannot publish linked data: {error}") from error
    try:
        if assertions_path.is_file():
            with assertions_path.open(encoding="utf-8", newline="") as assertion_file:
                reader = csv.DictReader(assertion_file)
                if tuple(reader.fieldnames or ()) != ASSERTION_COLUMNS:
                    raise ValueError(
                        "link-assertions.csv has unexpected or reordered columns"
                    )
                assertions = list(reader)
        else:
            # Small third-party or test builds can omit the optional register.
            assertions = []
    except (OSError, ValueError) as error:
        raise PluginError(f"Cannot publish linked data: {error}") from error
    if not isinstance(records, list):
        raise PluginError(f"{source} must contain a list of records")
    if not isinstance(registry, dict):
        raise PluginError(f"{registry_path} must contain an ID-to-alias mapping")

    try:
        site_url = site_base(config.site_url)
    except ValueError as error:
        raise PluginError(str(error)) from error

    for record in records:
        files.append(
            File.generated(
                config,
                RECORD_PATH.format(id=record["id"]),
                content=record_jsonld(record, site_url, assertions),
            )
        )
    current_ids = {str(record["id"]) for record in records}
    for record_id in registry.keys() - current_ids:
        files.append(
            File.generated(
                config,
                RECORD_PATH.format(id=record_id),
                content=retired_jsonld(record_id, site_url),
            )
        )
    files.append(
        File.generated(
            config,
            BULK_PATH,
            content=bulk_jsonld(records, site_url, assertions),
        )
    )
    return files
