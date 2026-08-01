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
- **copyright**: Copyright or license information (e.g., `"CC BY 4.0"`)
- **quantity**: Manuscript count (`"Few"`, `"Dozens"`, `"Hundreds"`, `"Thousands"`, or `"Unknown"`)
- **iiif**: Standardized image format support (`true` or `false`)
- **is_free_cultural_works_license**: Free license status (`true` or `false`)
- **is_part_of**: Whether the library belongs to a larger aggregating project (`true` or `false`)

### Conditional fields

- **is_part_of_project_name** and **is_part_of_url**: Required only when `is_part_of` is `true`. Leave them out (or set them to `null`) when `is_part_of` is `false`.

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
    "quantity": "Hundreds",
    "iiif": true,
    "is_free_cultural_works_license": false,
    "is_part_of": false
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
- Update copyright: `"copyright": "CC0 1.0"`
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
    
    - **Missing required field**: Add id, library, nation, city, website, copyright, quantity, iiif, is_free_cultural_works_license, and is_part_of
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
| `Missing required property` | Add id, library, nation, city, website, copyright, quantity, iiif, is_free_cultural_works_license, and is_part_of to every entry |
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
