---
description: >-
  Guidelines for contributing to DMMapp, including how to add library
  entries, follow the data schema, and pass automated validation.
---

# Contributing Guide

Thank you for your interest in contributing to the DMMapp Library Directory! This guide will help you add new libraries or improve existing entries.

## How to Contribute

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
    "quantity": "Thousands",
    "iiif": true,
    "is_free_cultural_works_license": true,
    "aggregators": []
}
```

## Validation

Your contribution will be automatically validated against our schema when you submit a pull request. The validation checks:

1. **JSON Syntax**: Proper JSON formatting
2. **Required Fields**: All mandatory fields are present
3. **Data Types**: Values match expected types (string, boolean, etc.)
4. **URL Format**: The `website` field contains a valid URL
5. **Enum Values**: The `quantity` field uses one of the allowed values

## Guidelines

### Quality Standards

- **Accuracy**: Ensure all information is correct and up-to-date
- **Completeness**: Fill in all required fields
- **Verification**: Test the website URL to confirm it works
- **IIIF Status**: Verify IIIF support before marking as `true`
- **License**: Check the library's terms of use for license information

### Best Practices

1. **Website URLs**: Use the most direct link to the digitized manuscript collection
2. **Library Names**: Use the official name as it appears on the library's website
3. **Location**: Use standardized country and city names (English spelling)
4. **Quantity Estimation**: Choose the category that best matches the collection size — see the [Data Schema](schema.md#approximate-number-of-manuscripts) page for the exact category boundaries

## Questions?

If you have questions or need help:

1. Check existing entries in `docs/assets/data.json` for examples
2. Review the `schema.json` file for technical details
3. Open an issue on GitHub for assistance

Thank you for helping make this resource better!
