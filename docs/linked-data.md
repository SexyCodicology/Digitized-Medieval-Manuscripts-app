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

The maintainers intend to preserve these IDs and aliases. This is a project
stewardship policy, not an uptime or permanent-hosting guarantee from GitHub
Pages. A future host migration must preserve the old paths or provide a
documented forwarding route.

## Download machine-readable data

The [original JSON directory](assets/data.json) remains the source for the
dashboard. The build also publishes:

- [Bulk JSON-LD](assets/dmmapp-linked-data.jsonld), with the directory
  catalogue and its active records.
- A JSON-LD file for each ID at `linked-data/records/<id>.jsonld`. Each human
  page advertises this file using an HTML `rel="alternate"` link.

The JSON-LD uses the [Data Catalog Vocabulary (DCAT)](https://www.w3.org/TR/vocab-dcat-3/).
It distinguishes a `dcat:CatalogRecord`—DMMapp's metadata entry—from a
`dcat:Resource` representing the catalogued access point. A source institution's
`website` is published as that resource's `dcat:landingPage`, not as an
identity claim. The bulk catalogue lists the current records and the available
distributions. These are static files rebuilt with the site, not a live API or
SPARQL endpoint. GitHub Pages may serve JSON-LD with a generic content type;
clients should parse the linked files as JSON-LD rather than assume HTTP
content negotiation.

The site's CC0 dedication applies to DMMapp's directory data and content. It
does **not** grant rights to manuscripts, images, or metadata hosted by linked
institutions. The linked-data graph therefore gives the DMMapp catalogue a CC0
licence but does not copy that licence onto access points or manuscripts.
Consult each source institution's terms before reuse.

## Interpret links and missing claims

DMMapp does not infer that two resources are identical from a shared name or
URL. The initial graph contains no `sameAs` assertions. Institution, place,
aggregator, and IIIF relationships need evidence that identifies the correct
target and its role. An `iiif: true` flag alone is not a collection endpoint;
a representative IIIF Manifest is not a complete IIIF Collection.

`last_checked` concerns the response of the collection URL on that date. It
does not verify the record's institutional identity, rights, or IIIF scope.
An absent authority link or IIIF endpoint means DMMapp has not published that
assertion, not that the institution or endpoint does not exist.

## Correct or extend a record

Use **Report a data issue** on the ID page to provide the record ID, proposed
correction, and a public authoritative source. Maintainers review material
changes before publication. See [Update the dashboard data](update-data.md)
for the contribution workflow.

When adding a record, add its current name-derived slug to
[`library-aliases.json`](assets/library-aliases.json) under the same ID. When
changing a name, append the new slug; never remove an older slug. The build
and data validation reject missing current aliases and collisions. Pull-request
CI also compares the registry with its base branch and rejects removed IDs or
aliases. Never reuse the ID of a withdrawn record for a different access point;
the meaning of an ID still needs human review when records are edited.

**Command safety**: Safe

```bash
python scripts/validate_data.py
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
verify their public URLs directly; a successful local build does not prove
GitHub Pages or source institutions are available.

## Evidence and review

| Item | Evidence | Verified | Review owner | Next review or trigger |
|---|---|---|---|---|
| Build and identifier behaviour | `hooks/library_pages.py`, `hooks/linked_data.py`, `mkdocs.yml` | 2026-09-20, local build | DMMapp maintainers | On route or hosting changes |
| Dataset licence boundary | `LICENSE`, `README.md`, `schema.json` | 2026-09-20, repository inspection | DMMapp maintainers | On licence or data-model changes |
| Public hosting and uptime | `mkdocs.yml`, `.github/workflows/deploy.yml`; no uptime commitment found | 2026-09-20, repository inspection | DMMapp maintainers | Confirm before claiming availability |

Unconfirmed: ownership of long-term hosting, recovery targets, and an external
adoption commitment. The DMMapp maintainers must confirm these before making
service-level or ecosystem-impact claims.
