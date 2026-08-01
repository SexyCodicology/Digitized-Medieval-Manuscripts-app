# How we validate data

When you submit changes to the library directory, an automated system checks your data before it's added to the live dashboard. This ensures that all library records are accurate, complete, and formatted correctly.

## What the validation system does

The system performs two levels of checking:

1. **Format check**: Verifies that the data is properly structured
2. **Content check**: Confirms that all information is complete and correct

Both checks happen automatically and provide instant feedback through GitHub.

## When validation runs

The system checks your data in two situations:

- **Automatically**: When you submit a pull request that changes the library data
- **On demand**: When you manually request a validation check from the GitHub Actions tab

## How the format check works

The first check ensures your data is properly formatted as a JSON file (a structured text format used to store information).

The system verifies:

- All brackets and braces are correctly matched
- Commas separate fields properly
- Text is properly enclosed in quotation marks
- There are no trailing commas or other syntax errors
- The file uses standard UTF-8 encoding

!!! failure "Example: Missing comma"

    ```json
    {
      "library": "Example"
      "nation": "Country"
    }
    ```

    The system finds the missing comma between fields and alerts you to fix it.

!!! failure "Example: Trailing comma"

    ```json
    {
      "library": "Example",
    }
    ```

    Commas should not appear after the last field.

## How the content check works

The second check ensures all your data follows the required structure and contains valid information.

The system verifies:

1. **All required fields are present, and no unrecognised fields are included**
   - Every library record must include exactly: ID, name, country, city, website, copyright information, manuscript count, format support, license type, and project information
   - Extra fields that aren't part of this list are rejected, so a typo in a field name is caught rather than silently ignored

2. **Data types are correct**
   - Text fields contain text (not numbers)
   - Yes/No fields use true or false (not the words "true" or "false")
   - Number fields contain whole numbers

3. **IDs are unique**
   - Every record's ID must be a positive whole number
   - No two records may share the same ID

4. **Websites are valid**
   - Website addresses follow proper format: `https://example.com`
   - URLs start with `http://` or `https://`
   - Links are reachable and functional

5. **Relationships are consistent**
   - When you indicate a library is part of a larger project, you must provide the project name and website
   - When a library operates independently, project fields must be empty

6. **Categories use correct values**
   - Manuscript counts must be: "Few", "Dozens", "Hundreds", "Thousands", or "Unknown"
   - No other values are accepted

!!! failure "Example: Multiple violations"

    ```json
    {
      "id": 1,
      "library": "Example Library",
      "nation": "Country",
      "city": "City",
      "website": "not-a-valid-url",
      "iiif": "false",
      "quantity": "Many"
    }
    ```
    
    **Issues the system finds**:
    
    - `website`: Format is invalid (missing protocol)
    - `iiif`: Should be true or false, not the word "false"
    - `quantity`: "Many" is not an allowed value

## What you see on GitHub

After you submit changes, GitHub displays the validation results next to your pull request.

### Validation passed

You see a **green checkmark** (✓) and a **"Passed"** status.

This means:
- Your data format is correct
- All required information is present
- Content meets all standards
- Your pull request can be reviewed and merged

### Validation failed

You see a **red X** (✗) and a **"Failed"** status.

This means:
- Your data has one or more errors
- The system cannot process your changes until you fix the issues
- Click the **"Details"** link to see what's wrong

## Reading error messages

When validation fails, GitHub shows you exactly what needs to be fixed.

!!! example "Format error"

    ```
    Expecting ',' delimiter: line 45 column 3 (char 1234)
    ```
    
    **What it means**: Line 45 is missing a comma.  
    **How to fix**: Go to line 45 in your data and add a comma between fields.

!!! example "Missing field"

    ```
    record 122 (id: 123): <record>: 'iiif' is a required property
    ```
    
    **What it means**: The record at position 122 (with ID 123) is missing the IIIF field.  
    **How to fix**: Add `"iiif": true` or `"iiif": false` to that record.

!!! example "Invalid website"

    ```
    record 455 (id: 456): website: 'not-a-valid-url' does not match '^https?://'
    ```
    
    **What it means**: The website address in the record with ID 456 doesn't start with `http://` or `https://`.  
    **How to fix**: Ensure the URL starts with `https://` and is a working link. Example: `"website": "https://example.com/manuscripts"`

!!! example "Incomplete project information"

    ```
    record 788 (id: 789): is_part_of is true but is_part_of_project_name is missing
    ```
    
    **What it means**: The record with ID 789 says it's part of a project but doesn't provide the project name.  
    **How to fix**: Either provide both the project name and project website, or set the library as independent (`"is_part_of": false`).

!!! example "Duplicate ID"

    ```
    record 583 (id: 42): duplicate id, already used by record 17
    ```
    
    **What it means**: Two records share the same ID (42).  
    **How to fix**: Give the new record an ID that isn't already used anywhere in `data.json`.

## Common errors and how to fix them

### Missing required fields

**Error message**: `is a required property`

**What went wrong**: You forgot to include one or more required fields.

**Example**:
```json
{
  "id": 1,
  "library": "Example"
}
```

Missing: country, city, website, copyright information, manuscript count, format support, license type, and project information.

**How to fix**: Review the [Data Structure Guide](./schema.md) and add all required fields to your record.

---

### Text written as "true" or "false" instead of true/false

**Error message**: `must be boolean`

**What went wrong**: You used quotation marks around true or false, making them text instead of yes/no values.

**Example**:
```json
{
  "iiif": "false"
}
```

**How to fix**: Remove quotation marks:
```json
{
  "iiif": false
}
```

---

### Website URL missing the protocol

**Error message**: `does not match '^https?://'`

**What went wrong**: Your website address doesn't start with `http://` or `https://`.

**Example**:
```json
{
  "website": "www.example.com"
}
```

**How to fix**: Add the protocol:
```json
{
  "website": "https://www.example.com"
}
```

---

### Manuscript count not in the allowed list

**Error message**: `must be equal to one of the allowed values`

**What went wrong**: You used a value that's not in the approved list.

**Example**:
```json
{
  "quantity": "Some"
}
```

Approved values: "Few", "Dozens", "Hundreds", "Thousands", "Unknown"

**How to fix**: Use one of the five approved values:
```json
{
  "quantity": "Dozens"
}
```

---

### Project marked as true but no project name provided

**Error message**: `is_part_of is true but is_part_of_project_name is missing`

**What went wrong**: You indicated the library is part of a project but didn't provide the project's name.

**Example**:
```json
{
  "is_part_of": true,
  "is_part_of_project_name": null,
  "is_part_of_url": null
}
```

**How to fix**: Either provide the project name and website:
```json
{
  "is_part_of": true,
  "is_part_of_project_name": "Europeana Manuscripts",
  "is_part_of_url": "https://www.europeana.eu/"
}
```

Or mark the library as independent:
```json
{
  "is_part_of": false,
  "is_part_of_project_name": null,
  "is_part_of_url": null
}
```

---

### Duplicate ID

**Error message**: `duplicate id, already used by record`

**What went wrong**: You reused an ID that another record in `data.json` already has.

**How to fix**: Give your new record a whole number that isn't used anywhere else in the file. IDs don't need to be sequential — gaps are fine.

---

### Unrecognised field

**Error message**: `Additional properties are not allowed`

**What went wrong**: Your record includes a field name that isn't part of the twelve recognised fields (for example, a typo such as `webiste` instead of `website`).

**How to fix**: Check the field name against the [Data Structure Guide](./schema.md) and correct or remove it.

## Manual validation check

To run a validation check on demand:

1. Go to your GitHub repository
2. Click the **Actions** tab
3. Find **Data Guardrails** in the workflow list
4. Click **Run workflow**
5. Select your branch
6. Click **Run workflow**

The system checks your data and displays results within 1-2 minutes.

**When to use manual validation**:
- Before submitting a pull request to catch issues early
- After making changes to schema rules
- To verify data on a specific branch without a pull request

## Performance

**Typical validation time**: 20-40 seconds

**Cost**: Free (included with GitHub)

## Preventing validation failures

### Before you submit changes

1. Review the [Data Structure Guide](./schema.md) to understand all required fields
2. Check the [Update the Dashboard Data](./update-data.md) guide for step-by-step instructions
3. Test your website links in a browser before submitting
4. Verify spelling of library names, cities, and countries

### If validation fails

1. Read the error message carefully—it tells you exactly what's wrong
2. Click the error details in GitHub to see which record and field have the problem
3. Compare your data to the examples in the [Data Structure Guide](./schema.md)
4. Fix the issue and resubmit
5. Use the manual validation check to verify before creating a new pull request

## Still stuck?

If you can't figure out the error:

1. Review the "Common errors and how to fix them" section above
2. Check the [Data Structure Guide](./schema.md) for field requirements
3. Look at other records in the database to see examples of correct formatting
4. [Open an issue](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/issues) or contact @Dioscorides for help

## Related documentation

- [Data Structure Guide](./schema.md) — Understanding the data fields
- [Update the Dashboard Data](./update-data.md) — How to add or edit libraries
- [Contributing Guide](./contributing.md) — Ways to help the project

---

**Last Updated**: August 1, 2026
