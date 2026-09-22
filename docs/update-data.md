---
description: >-
  Learn how to add new libraries or edit existing entries in DMMapp's
  directory using GitHub's built-in editor, with no coding required.
---

# Update the dashboard data

This guide explains how to add new libraries and edit existing information in the DMMapp library directory. You don't need coding knowledge—the process uses GitHub's built-in editor.

## What you'll learn

- Find and open the data file
- Add new libraries or edit existing entries
- Submit changes for review
- Verify that the dashboard reflects your updates

## Prerequisites

- A GitHub account ([create one](https://github.com/signup) if needed)
- Write access to the repository
- A modern web browser (Chrome, Firefox, Safari, or Edge)

!!! tip "New to GitHub?"
    GitHub is a platform for storing and collaborating on code and documents. This guide uses GitHub's built-in editor, so you won't need to use the command line.

!!! info "About data governance"
    The docs/assets/data.json file is maintained by @Dioscorides. When you submit changes, they review your work to ensure quality standards. This keeps the library directory accurate and reliable for researchers worldwide.

## Report a data issue

If you spot an incorrect library name, collection link, licence, or other data
problem while viewing a library page, select **Report a data issue**. The
GitHub form includes the record ID, library name, and page URL automatically.
Choose the kind of problem, describe the correction, and include a public
source when one supports the change. Maintainers verify the report before they
update the directory.

## 1. Find the data file

1. Open your GitHub repository in your browser
2. Open the **docs** folder, then the **assets** folder
3. Click **data.json** in the file list

The file displays in read-only format.

## 2. Enter edit mode

Click the **pencil icon** (✎) in the toolbar at the top of the file viewer.

Your browser switches to an editor. You'll see the data formatted as JSON—a structured format for storing information.

!!! warning "About JSON format"
    JSON has strict formatting rules. Each library entry uses curly braces `{ }`, fields are separated by commas, and text values must be in quotes. GitHub validates your changes before submission, so you can make corrections as needed.

## 3. Make your changes

### Required fields

Every library entry must include:

- **id**: Unique record identifier (e.g., `503`)
- **library**: Institution name (e.g., "Bodleian Library")
- **nation**: Country name (e.g., "United Kingdom")
- **city**: City name (e.g., "Oxford")
- **website**: Working URL to the digitized collection (must start with `http://` or `https://`)
- **copyright**: The institution's verbatim copyright or licence information (e.g., `"CC BY 4.0"`)
- **licence_category**: The normalised filter category (e.g., `"CC-BY"`)
- **quantity**: Manuscript count (`"Few"`, `"Dozens"`, `"Hundreds"`, `"Thousands"`, or `"Unknown"`)
- **iiif**: Standardized image format support (`true` or `false`)
- **is_free_cultural_works_license**: Free license status (`true` or `false`)
- **aggregators**: The aggregating projects the library is discoverable through, as a list. Use `[]` when there are none.

Use the institution's current official name for **library**, preserving its
script and diacritics. If a verified portal or collection has a different
title, add optional **access_point_title**. Put verified current translations
or alternate institution names in optional **library_alternate_names**, with
a language tag when known. See [Institution-name research](name-research.md)
for examples, evidence rules, and the separate name register. Do not use a
matching name or website to merge two record IDs.

Each ID has a stable public page. For a new entry, add its name-derived slug
to [`library-aliases.json`](assets/library-aliases.json) under the new ID. If
you change a library name, append the new slug under the existing ID and keep
every older slug. This preserves links shared before the correction. The
[linked-data guide](linked-data.md) explains the identifier policy. If you are
unsure of the correct slug, ask a maintainer to prepare this part of the change.

### Aggregator entries

Each entry in **aggregators** needs a **name** and a **url**. List one entry per
aggregator when a library belongs to several, rather than adding a second row
for the same library:

```json
"aggregators": [
    { "name": "Europeana Manuscripts", "url": "https://www.europeana.eu/" },
    { "name": "Digital Scriptorium", "url": "https://search.digital-scriptorium.org/" }
]
```

Use the aggregator's home page for **url**, spell the **name** the way other
records spell it, and don't list the same aggregator twice on one library.

### Choose a licence category

Keep **copyright** exactly as the institution states it. Choose the matching
**licence_category** from `CC0`, `CC-BY`, `CC-BY-NC`, `CC-BY-NC-SA`,
`CC-BY-NC-ND`, `All Rights Reserved`, `Mixed/Item-specific`, or `Unknown`.
Use `Mixed/Item-specific` when one collection uses several rights statements.
Use `Unknown` only if the institution's verbatim rights statement is unknown.
Place CC BY-SA in `CC-BY`, because the dashboard does not use a separate
CC BY-SA category.

### Link status fields

Two optional fields record whether a collection URL still works:

- **is_disabled**: Set it to `true` only when the link has been confirmed
  dead. Leave the field out otherwise.
- **last_checked**: The date the link was last assessed, written as
  `YYYY-MM-DD`. For a working link, its individual page shows this as the date
  it was last confirmed working. Required when **is_disabled** is `true`, so
  the warning a reader sees can be dated.

The weekly link check normally sets these for you and opens a pull request
with its proposal, so you rarely need to write them by hand. See
[How we check for broken links](./workflow-link-checking.md) for what the
check does and does not conclude. If a collection has moved rather than
closed, update **website** instead of marking it broken.

### IIIF collection and example-manuscript endpoints

When a collection supports IIIF, you can add either or both optional endpoint
types below. Each must be a direct `http://` or `https://` IIIF Presentation
API v2/v3 JSON endpoint—not the institution's viewer page. Set them only when
**iiif** is `true`.

- **iiif_collection_url**: a IIIF collection whose scope matches the listed
  medieval manuscript collection.
- **iiif_example_manifest_url**: a direct manifest for one representative
  manuscript. It requires **iiif_example_manifest_label**, the readable name
  of that manuscript.

```json
"iiif": true,
"iiif_collection_url": "https://example.org/iiif/medieval-manuscripts/collection",
"iiif_example_manifest_url": "https://example.org/iiif/manuscript-123/manifest",
"iiif_example_manifest_label": "Manuscript 123"
```

Do not use an institution-wide IIIF collection when it includes material far
outside the listed medieval manuscripts. In that case, record a named example
manifest instead. Before you submit an endpoint, open it in the [IIIF
Presentation API Validator](https://presentation-validator.iiif.io/) and in
the [Universal Viewer](https://www.universalviewer.dev/uv.html#?manifest=).
Confirm that the endpoint returns presentation JSON and displays the expected
collection or manuscript. DMMapp labels the resulting detail-page actions as
**Browse IIIF collection** and **Open example manuscript in IIIF: [label]**;
it lists the collection action first when both are present.

Record every published direct endpoint in `research/iiif-evidence.csv`. Add the
direct JSON URL, an exact institutional catalogue or item page, the date you
checked both, and a short scope note. A generic collection homepage does not
corroborate a representative Manifest. Follow [IIIF endpoint
research](iiif-research.md) for the exact columns, statuses, and checks.

### Optional institutional identifiers

You can add the following optional fields after a DMMapp maintainer reviews
the exact target and its relationship to the access point. Do not guess an
identifier, and leave the field out when you cannot find a reliable match.

- **isil**: The library's International Standard Identifier for Libraries,
  written as `<AgencyPrefix>-<LocalCode>`, for example `"GB-OxBodl"`. A
  registered non-national prefix is also valid. Confirm the exact library or
  unit through its issuing registry; do not use a parent institution's code
  for a separately identified library. Start with the [ISIL agency
  list](https://biblstandard.dk/isil/).
- **wikidata_qid**: The library's Wikidata item ID, such as `"Q1131283"`.
  Find it through [Wikidata item search](https://www.wikidata.org/w/index.php?search=).
  Confirm that the item describes the listed institution, rather than a
  similarly named collection, parent organisation, or branch.
- **geonames_id**: The positive numeric GeoNames ID for the library's
  location, such as `2640729`. Find it through [GeoNames search](https://www.geonames.org/).
  Match the listed city and country; check the administrative area if several
  places share the name. Credit GeoNames when reusing its CC BY 4.0 place data.

These fields are not required for new or existing records. They appear on the
library detail page and are included in dashboard exports when present.

For every library record, the tracked `research/identifier-evidence.csv` file
records one decision for each of these three fields. If you add a record, add
three rows to that file. Use `verified` with a direct public source URL for a
confirmed value, or `unresolved` with a short reason when you cannot confirm
one. Enter the date you checked the source as `YYYY-MM-DD`. A Wikidata value
also needs a corroborating institution or registry URL. If you propose a
correction through GitHub's editor and cannot edit the research file, ask a
maintainer to complete those rows in your pull request before merging it.

Follow the [Identifier research](identifier-research.md) guide for the exact
ledger columns, source criteria, examples, and checks.

### Review an authority or IIIF assertion

Research status and maintainer approval are different. The identifier ledger
records how a candidate was found; it does not approve the relationship.
Existing identifier values published before this review gate remain visible
while the maintainers audit them. Do not describe them as individually
approved. For each new or changed `isil`, `wikidata_qid`, `geonames_id`,
`iiif_collection_url`, or `iiif_example_manifest_url`, add one matching row to
[`link-assertions.csv`](assets/link-assertions.csv). The row records the exact
value, the authoritative target or endpoint URL, a distinct corroborating
source for its relationship to this access point, the check date, the
maintainer's GitHub username (without `@`) and review date, a DMMapp
pull-request URL, and a short note explaining the relationship. Use real dates
in `YYYY-MM-DD` format.

Open a draft pull request with the proposed field and supporting source links
first. Its evidence check will remain red until a maintainer has reviewed the
claim. After the review, add the approved CSV row with that pull request's
URL and push the final change. The maintainer then approves the latest push;
an earlier approval is not enough after the CSV is updated. Do not write a
reviewer's name or review date before that review has happened.

A reviewer checks the target's type and scope as well as its identifier. A
DMMapp record is **not** the institution, city, or manuscript. A GeoNames ID
must identify the place associated with the listed institution, and a IIIF
Collection must cover the listed access point rather than an entire unrelated
holding. The CSV validator checks completeness and consistency, not the truth
of an external claim or the identity of the named reviewer. Use the repository's
normal pull-request review before merging. If the proposal remains uncertain,
leave the field and CSV row out; the directory entry remains available.

The validator also checks that a Wikidata source names the approved QID on
`www.wikidata.org`, that a GeoNames source names the approved numeric ID on a
GeoNames domain, and that an IIIF source is the exact approved endpoint. These
checks prevent a field from pointing at the wrong kind of authority target;
they do not replace the maintainer's semantic review.

The history check compares a pull request with its target branch. Values that
were already public when this gate was introduced may remain while they are
audited. Any addition or changed value, including a change to an older IIIF
endpoint, needs a matching approved row. Approval does not transfer from one
value, record, or field to another.

**Command safety**: Safe

```bash
python scripts/validate_link_assertions.py
python scripts/validate_iiif_evidence.py
```

For a record in the first linked-data pilot, update its field-level decision in
[`linked-data-pilot-review.csv`](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/blob/master/research/linked-data-pilot-review.csv).
Keep `pending` until the maintainer review has happened. Final `approve` and
`correct` decisions must match the assertion register's reviewer, date, and PR
URL.

**Command safety**: Safe

```bash
python scripts/validate_linked_data_pilot.py
```

### Homepage recency fields

Two optional fields let the homepage show when a record was added or materially
updated:

- **added**: The date the record first entered DMMapp, written as YYYY-MM-DD.
- **last_edited**: The date of its most recent material correction or update,
  written as YYYY-MM-DD.

Use only a real, verifiable date that is not in the future. Leave either field
out when you cannot verify it. The reviewer confirms these dates as part of the
pull-request workflow.

### Add a new library

Locate the last library entry in the file:

```json
{
    "id": 500,
    "library": "Bodleian Library",
    "nation": "United Kingdom",
    "city": "Oxford",
    "website": "https://digital.bodleian.ox.ac.uk",
    "copyright": "CC BY-NC 4.0",
    "licence_category": "CC-BY-NC",
    "quantity": "Hundreds",
    "iiif": true,
    "is_free_cultural_works_license": false,
    "aggregators": []
}
```

1. Place your cursor after the closing `}`
2. Add a comma (`,`)
3. Press Enter
4. Copy the template above and replace values with your library's information
5. Verify all required fields are filled

### Edit existing information

Click any value and change it. Examples:

- Update website: `"website": "https://new-collection-link.org"`
- Correct city name: `"city": "Berlin"`
- Update copyright: `"copyright": "CC0 1.0"` and `"licence_category": "CC0"`
- Update quantity: `"quantity": "Thousands"`

!!! danger "Avoid these mistakes"
    - **Missing commas**: Every field needs a comma after it, except the last one. Correct: `"field": "value",`
    - **Unquoted text**: All text values require quotes. Wrong: `"city": Berlin`. Right: `"city": "Berlin"`
    - **Boolean values**: Use `true` or `false` without quotes
    - **Invalid URLs**: Websites must start with `http://` or `https://`
    - **Quantity values**: Use exactly one of the five options (capitalization matters)
    
    GitHub validates your changes before submission and alerts you to errors.

## 4. Submit your changes for review

Scroll to the bottom and complete the **Propose changes** section.

!!! info "About pull requests"
    A "pull request" (PR) is a formal way to submit changes for review. It ensures quality and accuracy before updating the official data.

### Fill in the change details

Select a change type:
- 🆕 New Library Entry
- ✏️ Correction (Typo, broken link, or other fix)
- 🗑️ Removal (Library closed or no longer digitized)

Write a brief description of your change. Examples:

- "Added University of Rome manuscript library with IIIF support"
- "Updated website URL for Paris collection—old link was broken"
- "Fixed spelling of library name in Berlin entry"

### Complete the verification checklist

Before submitting, verify:

- ✓ URL works (test the link in your browser)
- ✓ JSON is valid (no missing commas or brackets)
- ✓ Data format is correct (required fields present, proper capitalization)

!!! tip "Validate your JSON"
    GitHub's automatic validation message shows if your JSON is correct. A green checkmark (✓) means you're ready to submit. A red X (✗) indicates what needs fixing.

## 5. Wait for review and validation

### Automatic validation (1-2 minutes)

GitHub runs automatic checks:

- **JSON Syntax Check**: Verifies proper formatting
- **Schema Validation**: Confirms required fields and correct format
- **Format Verification**: Validates URLs and quantity values

A green checkmark (✓) indicates all checks passed.

!!! warning "If validation fails"
    GitHub displays errors describing what's wrong. Common issues:
    
    - **Missing required field**: Add id, library, nation, city, website, copyright, licence_category, quantity, iiif, is_free_cultural_works_license, and aggregators
    - **Invalid URL format**: Website must start with http:// or https://
    - **JSON syntax error**: Check for missing commas between fields
    - **Invalid quantity value**: Use "Few", "Dozens", "Hundreds", "Thousands", or "Unknown"
    
    Edit your data to fix the issue and resubmit.

### Review by @Dioscorides (24-48 hours)

@Dioscorides reviews your changes for:

- Accuracy of library information
- Working website links to digitized manuscripts
- Overall data quality

Your pull request will be:

- ✅ **Approved and merged** — Changes added to the live database
- 💬 **Requested for changes** — Updates needed before approval
- ❌ **Declined** — Information doesn't meet quality standards

### Dashboard updates (5-15 minutes after approval)

After approval and merge:

1. GitHub automatically rebuilds the website
2. Your library appears on the dashboard
3. Search and filters include your data

!!! tip "Verify your changes"
    After approval:
    
    1. Wait 10-15 minutes
    2. Refresh your dashboard page (press F5)
    3. Search for your library or look for your edits
    
    If changes don't appear after 15 minutes, clear your browser cache (Ctrl+Shift+Delete on Windows).

## Troubleshooting

### Resolve validation errors

GitHub displays error messages indicating what's wrong:

1. Read the error message carefully
2. Return to your data and find the problem (typically missing commas, quotes, or invalid URLs)
3. Click **Edit** to correct it
4. Resubmit

**Common validation errors:**

| Error                       | Fix                                                             |
|-----------------------------|-----------------------------------------------------------------|
| `Invalid JSON`              | Check each field—every field before the last needs a comma      |
| `Invalid URI format`        | Ensure URL starts with `http://` or `https://`                  |
| `Missing required property` | Add id, library, nation, city, website, copyright, licence_category, quantity, iiif, is_free_cultural_works_license, and aggregators to every entry |
| `Invalid enum value`        | Use only "Few", "Dozens", "Hundreds", "Thousands", or "Unknown" |

### Follow up on pending reviews

If your pull request hasn't been reviewed after 24 hours:

1. Go to your pull request
2. Scroll to the bottom and comment: "Hi @Dioscorides, could you review this when available?"
3. Check that validation passed (look for a green checkmark)

Fix any validation failures before requesting review.

### Respond to requested changes

If @Dioscorides requests changes:

1. Read their comment carefully
2. Click the **Files changed** tab to see flagged items
3. Click **Edit** to make corrections
4. Save and resubmit (GitHub updates your existing PR)
5. Add a comment: "Done—I've made the requested changes."

### Handle declined changes

If your changes are declined:

1. Read @Dioscorides's explanation
2. Gather additional information (verify websites, confirm copyright status)
3. Create a new pull request with improved data
4. Reference the original PR: "This improves on PR #123 with verified data"

### Investigate deployment issues

If the dashboard appears broken after approval:

1. Go to your merged pull request
2. Click **Commits** to see what changed
3. Wait 10-15 minutes (deployment may still be in progress)
4. Check the **Actions** tab for deployment status
5. Contact your repository administrator if errors persist

!!! tip "Create a backup"
    Before making significant changes, select all data, copy it, and save it to a text file on your computer. You can restore it if needed.

## Best practices

- **Write specific descriptions**: Instead of "update data," write "Added City Library in Paris with IIIF support and verified copyright"
- **Test URLs before submitting**: Verify the website link works in your browser
- **Make one change type per PR**: Add all new libraries in one PR, but keep additions separate from corrections
- **Verify spelling**: Library names and cities should match official sources
- **Complete the checklist**: Verify all three items before submitting
- **Allow time for review**: @Dioscorides typically responds within 24-48 hours

## Additional resources

- [Data schema](schema.md) — Field definitions and format details
- [IIIF field reference](schema.md) — Understand standardized image format support
- [Contributing guidelines](contributing.md) — Contribute to other project areas
- [Dashboard](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/) — View how your data appears
- [About the project](about.md) — Project context and history

Happy updating! 🎉
