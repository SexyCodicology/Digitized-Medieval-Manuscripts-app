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

### Project association

#### Part of a larger project

Whether this library's collection is part of a coordinated digitization initiative.

**Choose one:**
- `true` — Collection is part of a larger project
- `false` — Collection operates independently

**Example:** `true`

**Tips:**
- Check if the library mentions a larger initiative or program
- Examples: Europeana, Internet Archive, Digital Humanities projects

**Why it matters:** Researchers can discover related collections within the same initiative.

#### Project name (if applicable)

The name of the larger project to which this collection belongs.

**Requirements:**
- Only fill this in if you answered `true` above
- Must not be empty when filled in

**Example:** `"Europeana Manuscripts"`

**Why it matters:** The project name helps researchers understand the organizational context and find other related collections.

#### Project website (if applicable)

A direct link to the larger project's website or portal.

**Requirements:**
- Only fill this in if you answered `true` above
- Must be a working URL

**Example:** `"https://www.europeana.eu/"`

**Why it matters:** Researchers can access the project directly to explore other participating collections.

## How we check the data

All records are validated against our data structure standards before being added to the directory.

### Project information consistency

If you indicate that a collection is part of a larger project (`true`), you must provide:

- The project name (at least 1 character)
- The project website (a valid URL)

This ensures that project information is complete and usable.

**Valid example:**

```json
{
  "is_part_of": true,
  "is_part_of_project_name": "Europeana Manuscripts",
  "is_part_of_url": "https://www.europeana.eu/"
}
```

**Also valid (independent collection):**

```json
{
  "is_part_of": false,
  "is_part_of_project_name": null,
  "is_part_of_url": null
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

### Flexible project association

Collections can be independent or part of projects because:

- Not all libraries participate in coordinated initiatives
- When they do, researchers benefit from discovering related collections
- Optional project information accommodates both types

## Related files

- `schema.json` — The technical validation rules for our data
- `data.json` — The actual library records
- [Update the dashboard data](./update-data.md) — How to add or edit library information
