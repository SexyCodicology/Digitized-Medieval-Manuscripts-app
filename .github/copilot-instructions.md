# Copilot Code Review Instructions

When reviewing Pull Requests for the DMMapp repository, follow these specific guidelines:

## 1. JSON data (`docs/assets/data.json`)
- **Schema compliance:** Validate every changed entry against `schema.json`. Required fields are `id`, `library`, `nation`, `city`, `website`, `copyright`, `quantity`, `iiif`, `is_free_cultural_works_license`, and `aggregators`.
- **Quantity:** Ensure the `quantity` field uses one of the schema's buckets: "Few", "Dozens", "Hundreds", "Thousands", or "Unknown". Reject any other value.
- **Booleans:** Ensure `iiif` and `is_free_cultural_works_license` are strict booleans (`true`/`false`), not strings or integers (`0`/`1`).
- **Aggregators:** Ensure `aggregators` is an array. Confirm every entry has a non-empty `name` and an HTTP(S) `url`, that no library lists the same aggregator twice, and that a given aggregator name uses the same URL in every record. Use `[]` for a library with no aggregator membership.
- **Link status:** `is_disabled` and `last_checked` are optional. If `is_disabled` is `true`, confirm `last_checked` is present and is a real ISO 8601 date (`YYYY-MM-DD`). Reject a broken-link claim backed only by a timeout, 403, 429, or 5xx response — those describe the server, not the collection. A collection that moved needs a corrected `website`, not a broken-link mark.
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

