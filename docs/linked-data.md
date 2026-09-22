---
description: >-
  Use and cite DMMapp's stable directory identifiers and linked-data exports.
---

# Linked data and persistent identifiers

DMMapp is a directory of access points to digitized medieval manuscripts. It
does not catalogue individual manuscripts or host their images. A directory
record may describe a library's manuscript portal, a collection within a
larger portal, or an institutional holding discoverable through an aggregator.
Do not treat the DMMapp record as the institution or as a manuscript.

## Identify and cite a record

Each record has a numeric ID that stays with that directory entry. Cite its
ID-based page, for example
`https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/libraries/id-1/`.
Names can change without changing that address. The site's library index and
dashboard link to ID-based pages.

Older name-based URLs remain as compatibility pages. They point to the ID-based
page, including a visible link for readers without automatic redirects. GitHub
Pages does not issue a server-side 301 redirect for these pages. The
[`library-aliases.json`](assets/library-aliases.json) registry retains the
historical slugs. If a record is withdrawn, its ID page and JSON-LD file remain
available as withdrawal notices rather than silently identifying another entry.
Static GitHub Pages hosting cannot return a custom status for these paths, so
a withdrawn record's pages still respond `200 OK`; do not treat that response
code as confirmation that a record is still active, and do not rely on `404`
or `410` to detect a withdrawal the way DMMapp's own link checker does for
external collection URLs (see
[Link Health Check](workflow-link-checking.md))—check the page content or the
JSON-LD `dcterms:description` instead.

The maintainers intend to preserve these IDs and aliases. This is a project
stewardship policy, not an uptime or permanent-hosting guarantee from GitHub
Pages. A future host migration must preserve the old paths or provide a
documented forwarding route.

## Download machine-readable data

The [original JSON directory](assets/data.json) remains the source for the
dashboard. The build also publishes:

- [Bulk JSON-LD](assets/dmmapp-linked-data.jsonld), with the directory
  catalogue and its active records.
- [Reviewed link assertions](assets/link-assertions.csv), with the public
  evidence and review provenance for relationships promoted to JSON-LD.
- A JSON-LD file for each ID at `linked-data/records/<id>.jsonld`. Each human
  page advertises this file using an HTML `rel="alternate"` link.

The JSON-LD uses the [Data Catalog Vocabulary (DCAT)](https://www.w3.org/TR/vocab-dcat-3/).
It distinguishes a `dcat:CatalogRecord`—DMMapp's metadata entry—from a
`dcat:Resource` representing the catalogued access point. A source institution's
`website` is published as that resource's `dcat:landingPage`, not as an
identity claim. The bulk catalogue links to both its metadata records and the
access points they describe. It also lists the available distributions. These
are static files rebuilt with the site, not a live API or SPARQL endpoint.
GitHub Pages does not offer HTTP content negotiation; clients should parse the
linked files as JSON-LD by their known path rather than by requesting a
particular `Accept` type. The post-deployment smoke check
(`scripts/verify_public_lod.py`) confirms the served `Content-Type` header on
the bulk JSON-LD, a sample of per-record JSON-LD files, and the assertion CSV,
so a hosting change that starts serving them generically fails the release
check instead of going unnoticed.

The site's CC0 dedication applies to DMMapp's directory data and content. It
does **not** grant rights to manuscripts, images, or metadata hosted by linked
institutions. The linked-data graph therefore gives the DMMapp catalogue a CC0
licence and repeats it on the DMMapp downloads, but does not copy that licence
onto access points or manuscripts. Consult each source institution's terms
before reuse.

For a runnable RDF example, citation guidance, and the public reuse-reporting
form, see [Reuse DMMapp linked data](reuse-linked-data.md).

## Interpret links and missing claims

DMMapp does not infer that two resources are identical from a shared name or
URL. The graph contains no `sameAs` assertions. Institution, place,
aggregator, and IIIF relationships need evidence that identifies the correct
target and its role. An `iiif: true` flag alone is not a collection endpoint;
a representative IIIF Manifest is not a complete IIIF Collection.

`last_checked` concerns the response of the collection URL on that date. It
does not verify the record's institutional identity, rights, or IIIF scope.
An absent authority link or IIIF endpoint means DMMapp has not published that
assertion, not that the institution or endpoint does not exist.
The [public assertion register](assets/link-assertions.csv) contains only links
that have passed maintainer review, with their source and review provenance.
The separate research ledger may contain published values that still await
that semantic review. Those values remain visible in the original JSON and on
human-readable pages, but the JSON-LD does not promote them to relationships
until a maintainer approves them. Automated validation does not authenticate
the reviewer or prove that an authority target is correct.

The [linked-data audit pilot](linked-data-pilot.md) selects 25 varied records
for the first maintainer review batch. The selection includes duplicate-name
and portal-scope cases so the team tests the difficult boundaries before
expanding approvals across the catalogue.

Approved links use the DCAT qualified-relation pattern. The DMMapp access point
has a `dcat:qualifiedRelation` to a `dcat:Relationship`; that relationship
links to the reviewed target with `dcterms:relation` and names its function
with `dcat:hadRole`. This describes a scoped relationship without claiming
that the DMMapp entry, institution, place, or IIIF resource is identical to
another resource.

## Resource types

DCAT's `dcat:Resource` class is not meant to be used directly on an instance;
the [DCAT vocabulary](https://www.w3.org/TR/vocab-dcat-3/) recommends either a
more specific sub-class or a `dcterms:type` value naming the resource's kind.
DMMapp is not a `dcat:Dataset` publisher or a `dcat:DataService`, so every
access point carries the following `dcterms:type` instead.

### Directory access point

`#directory-access-point` means the described `dcat:Resource` is a DMMapp
directory entry for an online access point. It does not mean the resource is
a downloadable dataset or a live data service.

## Approved relationship roles

The following DMMapp role identifiers form a small controlled vocabulary.
Their fragment URLs are stable within this publication. The bulk JSON-LD also
describes each one as a `skos:Concept` with a `skos:prefLabel`, so a consumer
loading the graph into RDF tooling does not need to fetch and scrape this HTML
page to know what a role term means.

### Institution authority record

`#institution-authority-record` means the related resource is a reviewed ISIL
registry record describing the holding institution or relevant unit. DMMapp
uses the reviewed registry URL because ISIL agencies do not share one universal
linked-data resolver.

### Holding institution

`#holding-institution` means the related resource is the reviewed Wikidata
entity for the holding institution or relevant unit. DMMapp constructs the
target from the approved QID using Wikidata's `/entity/<QID>` URI pattern. It
does not mean the DMMapp access-point resource is that institution.

### Listed place

`#listed-place` means the related resource is the reviewed GeoNames place for
the city or location associated with the listed access point. DMMapp constructs
the target as `https://sws.geonames.org/<id>/`, which identifies the place
rather than the document that describes it. It does not assert that the access
point is a place.

### IIIF collection

`#iiif-collection` means the related resource is a reviewed direct IIIF
Presentation API Collection endpoint whose scope fits the listed access point.

### IIIF example manifest

`#iiif-example-manifest` means the related resource is a reviewed direct IIIF
Presentation API Manifest for one named representative manuscript. It does
not represent the complete collection.

Each approved relationship has its own stable fragment URI on the ID page. Its
RDF includes the two reviewed evidence URLs, review date, pull-request review,
reviewer's public GitHub profile, and relationship note. The CSV register
remains the source record for that provenance.

## Correct or extend a record

Use **Report a data issue** on the ID page to provide the record ID, proposed
correction, and a public authoritative source. Maintainers review material
changes before publication. See [Update the dashboard data](update-data.md)
for the contribution workflow.

When adding a record, add its current name-derived slug to
[`library-aliases.json`](assets/library-aliases.json) under the same ID. When
changing a name, append the new slug; never remove an older slug. The build
and data validation reject missing current aliases and collisions. Pull-request
CI compares the registry with its base branch, and deployment CI repeats that
comparison against the previous `master` revision. Both checks reject removed
IDs or aliases. Never reuse the ID of a withdrawn record for a different access
point; the meaning of an ID still needs human review when records are edited.

**Command safety**: Safe

```bash
python scripts/validate_data.py
```

**Command safety**: Safe

```bash
python scripts/validate_link_assertions.py
```

**Command safety**: State-changing (writes ignored build output and cache)

```bash
mkdocs build --clean
```

**Command safety**: Safe (reads the built site)

```bash
python scripts/verify_linked_data.py site
```

Inspect the generated ID page, old alias, per-record JSON-LD, and bulk file
before publishing. The verifier checks these outputs for every record, plus
withdrawal notices for IDs no longer in the active dataset. After deployment,
the Pages workflow also compares the public JSON dataset with the release and
checks the bulk JSON-LD, sitemap, and a small sample of ID pages, JSON-LD files,
and old aliases. This is a publication smoke check, not a guarantee that every
public URL or linked source institution is available. A failed check does not
automatically roll back a Pages deployment; investigate the reported URL and
the deployment before promoting the release as usable.

## Evidence and review

| Item | Evidence | Verified | Review owner | Next review or trigger |
|---|---|---|---|---|
| Build and identifier behaviour | `hooks/library_pages.py`, `hooks/linked_data.py`, `mkdocs.yml` | 2026-09-20, local build | DMMapp maintainers | On route or hosting changes |
| Public release smoke check | `.github/workflows/deploy.yml`, `scripts/verify_public_lod.py`; not yet run after a deployment | 2026-09-20, repository inspection | DMMapp maintainers | On publication changes |
| Dataset licence boundary | `LICENSE`, `README.md`, `schema.json` | 2026-09-20, repository inspection | DMMapp maintainers | On licence or data-model changes |
| Authority and IIIF release gate | `scripts/validate_link_assertions.py`, `scripts/verify_link_assertion_history.py`, `assets/link-assertions.csv`; no approved claims yet | 2026-09-21, local validation | DMMapp maintainers | On each proposed external assertion |
| Public hosting and uptime | `mkdocs.yml`, `.github/workflows/deploy.yml`; no uptime commitment found | 2026-09-20, repository inspection | DMMapp maintainers | Confirm before claiming availability |

Unconfirmed: ownership of long-term hosting, recovery targets, and an external
adoption commitment. The DMMapp maintainers must confirm these before making
service-level or ecosystem-impact claims.
