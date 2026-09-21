---
description: >-
  Reuse DMMapp's static JSON and JSON-LD safely, cite stable record IDs, and
  tell the project about a downstream integration.
---

# Reuse DMMapp linked data

DMMapp publishes a static directory for research tools, catalogues, teaching
resources, and other digital-humanities projects. You can reuse the full
dataset without scraping the dashboard or depending on a live API.

## Choose a download

| Need | Download | Notes |
| --- | --- | --- |
| Original DMMapp fields | [Catalogue JSON](assets/data.json) | Best for filters, exports, and applications that already use the DMMapp schema. |
| RDF relationships and catalogue structure | [Bulk JSON-LD](assets/dmmapp-linked-data.jsonld) | A DCAT catalogue containing all active records and access-point resources. |
| One stable record | `linked-data/records/<id>.jsonld` | Use the numeric ID from the catalogue. Withdrawn IDs remain as withdrawal notices. |
| Review provenance | [Reviewed link assertions](assets/link-assertions.csv) | Contains only relationships approved through DMMapp's review workflow. |

The files are rebuilt when the site is published. DMMapp does not currently
offer content negotiation, a SPARQL endpoint, a change feed, or a service-level
availability guarantee.

## Parse the RDF graph

The JSON-LD is standards-based RDF, so consumers should parse it as a graph
instead of depending on JSON key order. This example lists each DMMapp access
point and its source landing page:

```python
from rdflib import Graph, Namespace

DCAT = Namespace("http://www.w3.org/ns/dcat#")
graph = Graph().parse(
    "https://sexycodicology.github.io/"
    "Digitized-Medieval-Manuscripts-app/assets/dmmapp-linked-data.jsonld",
    format="json-ld",
)

for access_point, landing_page in graph.subject_objects(DCAT.landingPage):
    if "#access-point" in str(access_point):
        print(access_point, landing_page)
```

Install [RDFLib](https://rdflib.readthedocs.io/) in an isolated Python
environment to run the example. Production consumers should download and
cache the file deliberately rather than fetching it once per record or page
view.

## Interpret the model conservatively

- A DMMapp resource identifies a catalogued **access point**. It is not the
  holding institution, a manuscript, or an image.
- `dcat:landingPage` is where a reader can access the external collection. It
  is not an identity claim.
- A `dcat:qualifiedRelation` appears only after maintainers approve its target,
  role, evidence, and review provenance. An absent relation means “not
  published as a claim,” not “does not exist.”
- DMMapp does not publish `owl:sameAs` for access points.
- CC0 applies to DMMapp's directory data. Follow the linked institution's
  rights statement before reusing manuscript images or source metadata.

See [Linked data and persistent identifiers](linked-data.md) for the complete
identifier, persistence, modelling, licence, and correction policy.

## Cite and retain provenance

Keep the numeric DMMapp ID with any derived record. Link to its ID page rather
than a historical name-based alias. For reproducible research, also record the
date you downloaded the data and the repository commit or release reference
you used. DMMapp's current publication is updated in place and is not a
versioned research archive.

A minimal citation can include:

```text
DMMapp record <ID>, <library or access-point name>,
https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/libraries/id-<ID>/
(accessed <YYYY-MM-DD>).
```

## Report a reuse

If a public project, publication, dataset, or teaching resource uses DMMapp,
[report the linked-data reuse](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/issues/new?template=lod-reuse.yml).
The report helps maintainers measure citations, integrations, corrections, and
missing capabilities. It is also the best place to describe a concrete need
for a versioned snapshot, additional vocabulary mapping, or future API.

The issue is public. Include only public project information, and do not add
personal contact details, credentials, or private infrastructure URLs.
