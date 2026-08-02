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
- Copyright or license information
- Approximate number of manuscripts
- Technical format support (IIIF)
- License type (Free Cultural Works or other)
- Project participation

These fields are essential to create a reliable, searchable directory.

## How to fill out each field

### Unique identification

#### ID number

A unique number that identifies this library in our database. IDs are assigned sequentially.

**Example:** `502`

**Why it matters:** This number prevents duplicate entries and ensures accurate record tracking.

#### Library name

The official name of the institution that holds the manuscript collection.

**Tips:**
- Use the formal institutional name as it appears on their website
- Minimum 2 characters
- Include "Library," "Archive," or "Museum" if it's part of the official name

**Example:** `"National Library of France"` or `"Bodleian Library"`

**Why it matters:** Researchers use the library name to find specific collections and verify the source of manuscripts.

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

## How we check the data

All records are validated against our data structure standards before being added to the directory.

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
