---
description: >-
  Guidelines for contributing to DMMapp, including how to add library
  entries, follow the data schema, pass automated validation, and
  contribute to the dashboard's code.
---

# Contributing Guide

Thank you for your interest in contributing to DMMapp! This guide covers both
ways to contribute: adding or correcting library entries, and improving the
dashboard's code.

## Contribute library data

This section will help you add new libraries or improve existing entries.

### Adding a New Library

1. **Fork the Repository**: Create your own fork of the project on GitHub

2. **Edit docs/assets/data.json**: Add a new entry following the schema below

3. **Submit a Pull Request**: Create a PR with your changes

### Data Schema

Each library entry must include the following fields:

```json
{
    "id": 501,
    "library": "Library Name",
    "nation": "Country Name",
    "city": "City Name",
    "website": "https://example.com",
    "copyright": "CC BY 4.0",
    "licence_category": "CC-BY",
    "quantity": "Thousands",
    "iiif": true,
    "is_free_cultural_works_license": false,
    "aggregators": []
}
```

For the full field-by-field definitions, requirements, and the manuscript-count categories, see the [Data Schema](schema.md) page.

### Example Entry

```json
{
    "id": 502,
    "library": "Bibliothèque nationale de France",
    "nation": "France",
    "city": "Paris",
    "website": "https://gallica.bnf.fr/",
    "copyright": "CC0 1.0",
    "licence_category": "CC0",
    "quantity": "Thousands",
    "iiif": true,
    "is_free_cultural_works_license": true,
    "aggregators": []
}
```

### Validation

Your contribution will be automatically validated against our schema when you submit a pull request. The validation checks:

1. **JSON Syntax**: Proper JSON formatting
2. **Required Fields**: All mandatory fields are present
3. **Data Types**: Values match expected types (string, boolean, etc.)
4. **URL Format**: The `website` field contains a valid URL
5. **Enum Values**: The `quantity` and `licence_category` fields use one of the allowed values
6. **Name evidence**: Every record has a preferred-name decision; new names and titles cite a public source
7. **Identifier evidence**: Every record has one ISIL, Wikidata, and GeoNames decision in the evidence ledger
8. **IIIF evidence**: Every published direct IIIF endpoint has a checked endpoint and exact corroborating page in the IIIF evidence ledger

### Guidelines

#### Quality Standards

- **Accuracy**: Ensure all information is correct and up-to-date
- **Completeness**: Fill in all required fields
- **Verification**: Test the website URL to confirm it works
- **IIIF Status**: Verify IIIF support before marking as `true`
- **License**: Check the library's terms of use for license information

#### Best Practices

1. **Website URLs**: Use the most direct link to the digitized manuscript collection
2. **Library Names**: Use the institution's official self-published name. For a correction or an alternate name, follow [Institution-name research](name-research.md) and cite the public source.
3. **Location**: Use standardized country and city names (English spelling)
4. **Quantity Estimation**: Choose the category that best matches the collection size — see the [Data Schema](schema.md#approximate-number-of-manuscripts) page for the exact category boundaries
5. **Name evidence**: Add a preferred-name decision for a new record. Read [Institution-name research](name-research.md) before changing a name or adding a portal title.
6. **Identifier evidence**: Add three ledger rows for every new record. Read [Identifier research](identifier-research.md) before adding an ISIL, Wikidata QID, or GeoNames ID.
7. **IIIF evidence**: Read [IIIF endpoint research](iiif-research.md) before adding a Collection or representative Manifest URL.

## Contribute code

Improving the dashboard, the build process, or the documentation itself
follows the usual GitHub workflow: fork, branch, and open a pull request.

### Project layout

- `hooks/library_pages.py` — the MkDocs build hook that generates the
  homepage directory table, the alphabetical library index, and one page per
  library from `docs/assets/data.json`, including a conservative DCAT record
  graph rendered into `<head>` by `overrides/main.html`
- `hooks/linked_data.py` — the build hook that generates per-record and bulk
  JSON-LD and adds only maintainer-approved external relationships
- `docs/assets/dashboard.js` / `dashboard.css` — the dashboard's client-side
  search, filtering, sorting, export, and share behavior
- `scripts/` — `validate_data.py` (schema validation);
  `validate_name_evidence.py` and `verify_name_history.py` (name evidence
  and changed-name checks);
  `validate_identifier_evidence.py`, `validate_iiif_evidence.py`, and
  `validate_link_assertions.py` (check the research and approval ledgers
  against `data.json`); `validate_linked_data_pilot.py` (checks the 25-record
  pilot); `verify_identifier_history.py` and `verify_link_assertion_history.py`
  (reject a pull request that drops a published ID, alias, or approved link);
  `verify_linked_data.py` and `verify_public_lod.py` (check the built and
  deployed linked-data release); `report_linked_data_pilot.py` (renders the
  pilot review packet); `apply_link_status.py` (turns the weekly link check
  into data proposals); and `backfill_licence_category.py`
- `tests/` — the pytest suite covering `hooks/` and `scripts/`
- `docs/assets/dashboard.test.js` — the Node test suite covering
  `dashboard.js`

See [Project setup](setup.md) for installing dependencies and running the
site locally.

### Run the checks before you open a pull request

These are the same checks the [deploy workflow](workflow-validation.md) runs
on every pull request:

**Command safety**: Safe, State-changing

```bash
pip install -r requirements-dev.txt
python scripts/validate_data.py
python scripts/validate_name_evidence.py
python scripts/validate_identifier_evidence.py
python scripts/validate_iiif_evidence.py
python scripts/validate_link_assertions.py
python scripts/validate_linked_data_pilot.py
python -m pytest tests -q
npm ci
npm test
mkdocs build --clean
python scripts/verify_linked_data.py site
```

### Guidelines

- Keep changes focused—separate unrelated fixes into their own pull requests
- Add or update tests in `tests/` or `docs/assets/dashboard.test.js` for any
  behavior change
- Update the relevant page under `docs/` when your change affects what a
  reader or contributor sees
- Describe what changed and why in your pull request description

## Questions?

If you have questions or need help:

1. Check existing entries in `docs/assets/data.json` for examples
2. Review the `schema.json` file for technical details
3. Open an issue on GitHub for assistance

Thank you for helping make this resource better!
