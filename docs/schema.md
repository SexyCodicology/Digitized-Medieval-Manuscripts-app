---
description: >-
  A field-by-field guide to DMMapp's library data structure, covering
  required fields, validation rules, and how to fill out each entry.
---

# Data structure guide

This guide explains how DMMapp organizes information about manuscript libraries. Whether you're adding a new library or editing an existing entry, understanding the data structure helps you provide complete and accurate information.

## How the database is organized

Each library record contains the same set of information fields. This consistency ensures that researchers can search, filter, and compare collections reliably across the entire directory.

All records follow the same format defined in `schema.json`, our data validation file.

## Required information

Every library record must include the following information:

- Unique ID number
- Library name
- Country and city
- Website address
- Verbatim copyright or licence information
- Normalised licence category
- Approximate number of manuscripts
- Technical format support (IIIF)
- License type (Free Cultural Works or other)
- Project participation

These fields are essential to create a reliable, searchable directory.

## How to fill out each field

### Unique identification

#### ID number

A unique number that identifies this directory entry. New IDs need not be
sequential; gaps are valid, and a retired ID must never be reused.

**Example:** `502`

**Why it matters:** This number prevents duplicate entries and ensures accurate record tracking.

The public page uses `/libraries/id-<id>/` so a name correction does not change
the record's address. Never reuse a retired ID. See [Linked data and persistent
identifiers](linked-data.md) for the difference between a DMMapp record and a
source institution.

### Optional institutional identifiers

These optional fields link a library record to established authority files and
geographic catalogues. They help people match the same institution across
DMMapp, library registries, linked-data services, and other catalogues. Leave
them out when you cannot verify an identifier.

The `research/identifier-evidence.csv` ledger records a source or an unresolved
reason for each of the three fields on every record. Its check confirms that
the ledger agrees with `data.json`; a maintainer still checks whether a source
describes the correct institution or place. See [Identifier
research](identifier-research.md) for the required rows and review workflow.
Existing values may be awaiting that semantic review. Only values listed in
the approved [link assertion register](assets/link-assertions.csv) are emitted
as linked-data relationships.

Each generated library page embeds the DMMapp record and its catalogued access
point as separate DCAT resources. Optional identifiers become qualified
linked-data relationships only after a maintainer approves their role and
evidence in the public assertion register. See [how identifiers reach linked
data](identifier-research.md#how-these-identifiers-reach-linked-data).

#### ISIL

The International Standard Identifier for Libraries and Related Organizations,
written as a registered agency prefix and local code separated by a hyphen.
The prefix is usually a two-letter country code, but registered non-national
prefixes also exist. Confirm the exact holding institution or unit in the
issuing registry before adding its code; a parent institution may have a
different ISIL.

**Example:** `"GB-OxBodl"`

#### Wikidata QID

The library's Wikidata item identifier. It begins with an uppercase `Q` and is
followed by a positive number.

**Example:** `"Q1131283"`

#### GeoNames ID

The positive numeric GeoNames identifier for the library's location.
Match the listed city and country, including the administrative area when
names are ambiguous. [GeoNames](https://www.geonames.org/) data is available
under CC BY 4.0; credit GeoNames when reusing its place data.

**Example:** `2640729`

#### Library name

The verified official name of the institution or relevant unit that holds the
manuscript collection. Keep its self-published form, script, and diacritics.
The name labels a directory entry; the entry's stable ID identifies an access
point, not the institution itself.

**Tips:**
- Use the formal institutional name as it appears on their website
- Minimum 2 characters
- Include "Library," "Archive," or "Museum" if it's part of the official name

**Example:** `"National Library of France"` or `"Bodleian Library"`

**Why it matters:** Researchers use the library name to find specific collections and verify the source of manuscripts.

#### Access-point title and alternate institution names

Use optional `access_point_title` for a source-verified name of the portal or
collection reached through this record. It appears below the institution name
and titles the access point in JSON-LD. When absent, the access point retains
`library` as a directory label; this is not an identity claim.

Use optional `library_alternate_names` for verified *current* names or
translations of the same institution. Each entry has a `name` and may have a
BCP 47 `language` tag, such as `en`. Alternate names help readers find a
record through dashboard search and appear in the source JSON and exports.
They are not published as RDF labels on the access point. Do not put former
names or portal titles here.

```json
"library": "KU Leuven Bibliotheken",
"library_alternate_names": [
  {"name": "KU Leuven Libraries", "language": "en"}
]
```

Use the [institution-name research procedure](name-research.md) to record the
public source and check the related authority claims before a correction.

### Geographic information

#### Country

The country where the library is located. Use the English name of the country.

**Example:** `"France"` or `"United Kingdom"`

**Tips:**
- Use standard country names (not abbreviations)
- Be consistent with other entries

**Why it matters:** Geographic filtering helps researchers discover collections in their region of interest.

#### City

The city or town where the library is located.

**Example:** `"Paris"` or `"Oxford"`

**Tips:**
- Use the city name in English where possible
- Include the city name as it appears on maps

**Why it matters:** Precise location information helps researchers contact institutions and plan research visits.

### Access information

#### Website address

A direct link to the library's manuscript collection or digital portal.

**Requirements:**
- Must be a working URL
- Link directly to the manuscript section when possible
- Use HTTPS (secure) links when available

**Example:** `"https://gallica.bnf.fr/html/und/manuscrits/manuscrits"`

**Tips:**
- Test the link before submitting to ensure it works
- Avoid links to the institution's home page—link directly to manuscripts

**Why it matters:** This is the fastest way for researchers to access the collection. A working link is essential.

#### Copyright or license information

A description of the rights and restrictions that apply to the digitized manuscripts.

**What to enter:**
- License type (e.g., `"CC BY 4.0"`, `"CC0 1.0"`)
- `"Unknown"` if you cannot determine the copyright status
- Institution-specific copyright information if applicable

**Common licenses:**
- `"CC0 1.0"` — Public domain; free to use, modify, and share
- `"CC BY 4.0"` — Attribution required; free to use and share with credit
- `"CC BY-SA 4.0"` — Attribution and share-alike required
- `"All rights reserved"` — Restricted; contact institution for permission

**Example:** `"CC0 1.0"`

**Tips:**
- Check the library's website for their stated copyright or license
- If unclear, enter `"Unknown"`

**Why it matters:** Researchers need to understand what they can do with the materials before using them in their work.

#### Licence category

A controlled category that groups equivalent rights statements in the dashboard
filter. Keep **copyright** as the exact wording supplied by the institution,
then choose one of these values for **licence_category**:

- `CC0`
- `CC-BY`
- `CC-BY-NC`
- `CC-BY-NC-SA`
- `CC-BY-NC-ND`
- `All Rights Reserved`
- `Mixed/Item-specific`
- `Unknown`

Use `Mixed/Item-specific` when different items in a collection have different
rights. CC BY-SA belongs in the broader `CC-BY` category because DMMapp does
not maintain a separate CC BY-SA filter. Use `Unknown` only when the
institution's rights statement is genuinely unknown; it does not replace the
verbatim `copyright` value.

### Collection characteristics

#### Approximate number of manuscripts

An estimate of how many medieval manuscripts are in the digitized collection.

**Categories:**
- `"Few"` — Fewer than 50 manuscripts
- `"Dozens"` — 50 to 100 manuscripts
- `"Hundreds"` — 100 to 1,000 manuscripts
- `"Thousands"` — More than 1,000 manuscripts
- `"Unknown"` — Unable to determine

**Example:** `"Hundreds"`

**Tips:**
- Check the library's website for collection size information
- Use ranges when exact numbers aren't available
- When in doubt, choose `"Unknown"` rather than guessing

**Why it matters:** Knowing the collection size helps researchers understand the scope and value of available materials.

#### Standardized image format support (IIIF)

Whether the collection supports a standardized image format that allows researchers to view, zoom, compare, and use manuscripts in advanced ways.

**Choose one:**
- `true` — The collection supports standardized image format
- `false` — The collection does not support standardized image format

**Example:** `true`

**How to check:**
- Look for "IIIF" or "Mirador" on the library's website
- Check if images can be zoomed, rotated, or downloaded in high quality
- Contact the institution if you're unsure

**Why it matters:** Collections with this format support offer researchers more flexibility and powerful research tools.

#### IIIF collection URL

The optional `iiif_collection_url` field is the direct HTTP(S) endpoint for a
IIIF Presentation API v2 or v3 collection. Use it only when the collection's
scope matches the listed medieval manuscript collection. It is not the address
of an institution's viewer page. Add it only when `iiif` is `true`.

**Example:** `"https://example.org/iiif/medieval-manuscripts/collection"`

#### IIIF example manifest

Use `iiif_example_manifest_url` for a direct HTTP(S) IIIF Presentation API v2
or v3 manifest for one representative manuscript. It requires
`iiif_example_manifest_label`, which names that manuscript for readers.

**Example:**

```json
"iiif_example_manifest_url": "https://example.org/iiif/manuscript-123/manifest",
"iiif_example_manifest_label": "Manuscript 123"
```

**How to check:** Open each endpoint in the [IIIF Presentation API
Validator](https://presentation-validator.iiif.io/) and then in the
[Universal Viewer](https://www.universalviewer.dev/uv.html#?manifest=). Confirm
that it returns presentation JSON and displays the expected collection or
manuscript. The library detail page labels collection browsing separately from
a named example manuscript and lists the collection action first when both are
available.

**Why it matters:** Explicit scope tells readers whether they are browsing the
listed collection or opening one representative manuscript.

#### License type (Free Cultural Works)

Whether the collection uses a very permissive open license that allows maximum reuse.

**Choose one:**
- `true` — Collection uses a Free Cultural Works license (CC0, CC BY, CC BY-SA)
- `false` — Collection uses a different license or the license type is unknown

**Example:** `false`

**Tips:**
- Free Cultural Works licenses include CC0, CC BY, and CC BY-SA
- If the copyright information includes "All rights reserved," enter `false`
- When unsure, enter `false`

**Why it matters:** Researchers quickly identify collections with the most generous permissions for reuse in their own work.

### Aggregator memberships

#### Aggregators

The aggregator projects or websites this collection is discoverable through. A
collection can belong to none, one, or several.

**Requirements:**
- Always include the field, even when the collection belongs to no aggregator
- Use an empty array (`[]`) when the collection is discoverable only through the library's own site
- Give each membership a `name` and a `url`
- Don't list the same aggregator twice on one library

**Example:**

```json
"aggregators": [
    { "name": "Europeana Manuscripts", "url": "https://www.europeana.eu/" }
]
```

**Tips:**
- Check whether the library mentions a larger initiative or programme
- Examples: Europeana, Internet Archive, digital humanities projects
- Add every aggregator the collection appears in, not just the best-known one

**Why it matters:** Researchers can discover related collections within the same
initiative, and a library that participates in several is findable under each of
them.

#### Aggregator name

The name of the aggregator project the collection belongs to.

**Requirements:**
- Must not be empty
- Use the same spelling other records use for that aggregator

**Example:** `"Europeana Manuscripts"`

**Why it matters:** The name helps researchers understand the organisational
context, and it's what the project filter on the homepage groups records by, so
a spelling that differs from other records splits one aggregator into two
filter entries.

#### Aggregator URL

A direct link to the aggregator's website or portal.

**Requirements:**
- Must be a working URL that starts with `http://` or `https://`
- Use the aggregator's home page, not a deep link to this library's results
- Every record naming the same aggregator must use the same URL

**Example:** `"https://www.europeana.eu/"`

**Why it matters:** Researchers can access the aggregator directly to explore
other participating collections.

### Link status

Both fields are optional and are normally set for you by the weekly link
check rather than by hand. See [How we check for broken links](./workflow-link-checking.md).

#### Broken link

Whether the collection URL has been confirmed unreachable.

**Choose one:**
- `true` — The link was checked and found to be dead
- Leave the field out — The link is believed to work

**Example:** `true`

**Tips:**
- Only set this when you have confirmed the link is dead, not when a site is
  merely slow or blocks automated checks
- If the collection has simply moved, update the website address instead

**Why it matters:** A reader is warned before clicking a URL the project
already knows is dead, and can filter those collections out of the directory.

#### Last checked

The date the collection URL was last assessed, as an ISO 8601 calendar date.
For working links, the individual collection page shows it as the date the URL
was last confirmed working. For a broken link, it dates the broken-link
warning instead.

**Requirements:**
- Write it as `YYYY-MM-DD`, for example `2026-08-02`
- Required when the broken-link field is `true`, so the warning can be dated
- Must be a real date

**Example:** `"2026-08-02"`

**Why it matters:** Readers can judge how current a working-link confirmation
or broken-link warning is. A link confirmed broken years ago deserves less
trust than one checked last week.

### Homepage recency

These optional dates let the homepage show recently added and materially updated
library records. Leave them out when a record's date cannot be verified.

#### Added

The calendar date when the record first entered DMMapp. Write a real,
non-future date as YYYY-MM-DD, for example 2026-08-02.

#### Last edited

The calendar date of the record's most recent material correction or update.
Write a real, non-future date as YYYY-MM-DD, for example 2026-08-02. Do not use
it for formatting-only changes.

## How we check the data

All records are validated against our data structure standards before being added to the directory.

### Link status consistency

A record marked as having a broken link must say when that was established,
so no warning shown to a reader is undated. The date must be a real calendar
date written as `YYYY-MM-DD`.

**Valid example:**

```json
{
  "is_disabled": true,
  "last_checked": "2026-08-02"
}
```

**Also valid (checked recently and working):**

```json
{
  "last_checked": "2026-08-02"
}
```

**Rejected (no date for the warning):**

```json
{
  "is_disabled": true
}
```

### Aggregator membership consistency

Every membership you list must carry both a name and a working URL, so the
information is complete and usable. Two further rules keep the aggregator
filter trustworthy:

- Don't list the same aggregator twice on one library. Names are compared
  ignoring case and surrounding spaces, so `e-codices` and `E-Codices` count
  as the same aggregator.
- Don't give one aggregator two different URLs. Every record naming the same
  aggregator must point at the same address.

**Valid example (one membership):**

```json
{
  "aggregators": [
    { "name": "Europeana Manuscripts", "url": "https://www.europeana.eu/" }
  ]
}
```

**Also valid (several memberships):**

```json
{
  "aggregators": [
    { "name": "Europeana Manuscripts", "url": "https://www.europeana.eu/" },
    { "name": "Digital Scriptorium", "url": "https://search.digital-scriptorium.org/" }
  ]
}
```

**Also valid (no membership):**

```json
{
  "aggregators": []
}
```

## Why we organize data this way

### Required fields ensure completeness

### Why all fields matter

Include every field so researchers have complete information about each collection. Complete entries make searching and comparing libraries reliable.

### Categories instead of exact numbers

We use approximate ranges (Few, Dozens, Hundreds, Thousands) for manuscript counts because:

- Exact numbers are difficult to obtain from institutions
- Ranges are sufficient for researchers to understand collection scope
- Consistent categories make comparison easier
- Categories reduce data entry errors

### Yes/No choices for technical features

We use simple Yes/No choices for format support and license type because:

- Clear and easy to understand
- Fast to search and filter
- Straightforward for researchers to find what they need

### Flexible aggregator association

Collections can be independent or belong to any number of aggregators because:

- Not all libraries participate in coordinated initiatives
- Many that do participate in more than one
- When they do, researchers benefit from discovering related collections
- A list accommodates all three cases without duplicating the library

## Related files

- `schema.json` — The technical validation rules for our data
- `docs/assets/data.json` — The actual library records
- [Update the dashboard data](./update-data.md) — How to add or edit library information
