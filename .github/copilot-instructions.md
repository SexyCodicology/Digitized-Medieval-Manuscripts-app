# Copilot Code Review Instructions

When reviewing Pull Requests for the DMMapp repository, follow these specific guidelines:

## 1. JSON data (`docs/assets/data.json`)
- **Schema compliance:** Validate every changed entry against `schema.json`. Required fields are `id`, `library`, `nation`, `city`, `website`, `copyright`, `quantity`, `iiif`, `is_free_cultural_works_license`, and `is_part_of`.
- **Quantity:** Ensure the `quantity` field uses one of the schema's buckets: "Few", "Dozens", "Hundreds", "Thousands", or "Unknown". Reject any other value.
- **Booleans:** Ensure `iiif`, `is_free_cultural_works_license`, and `is_part_of` are strict booleans (`true`/`false`), not strings or integers (`0`/`1`).
- **Conditional fields:** If `is_part_of` is `true`, confirm `is_part_of_project_name` and `is_part_of_url` are present and non-empty.
- **Geography:** Verify that `city` and `nation` are capitalized correctly.
- **Trust boundary:** Verify that the `website` URL is reachable, that any IIIF claim (`iiif: true`) is backed by evidence the collection actually serves IIIF manifests, and that the `copyright`/`is_free_cultural_works_license` claim matches the license stated on the source site.

## 2. Documentation (`docs/*.md`)
- **Tone:** Enforce the **Microsoft Writing Style Guide**.
  - Use "You" (second person).
  - Be direct and action-oriented.
  - Avoid polite fluff ("Please", "Don't worry").
- **Structure:** Ensure headers use Sentence case (e.g., "How to update data").

## 3. Code (`docs/assets/dashboard.js`, `docs/assets/dashboard.css`)
- **Performance:** Flag any loops that iterate over the entire dataset unnecessarily.
- **Accessibility:** Ensure all `<img>` tags have `alt` text and colors have sufficient contrast.

