# Copilot Code Review Instructions

When reviewing Pull Requests for the DMMapp repository, follow these specific guidelines:

## 1. JSON Data (`data.json`)
- **Quantity:** Ensure the `quantity` field uses specific buckets: "One", "Dozens", "Hundreds", "Thousands". Reject vague terms like "Many" or "A few".
- **Booleans:** Ensure `iiif`, `is_free_cultural_works_license`, and `has_post` are strict Booleans (`true`/`false`), not integers (`0`/`1`).
- **Geography:** Verify that `city` and `nation` are capitalized correctly.
- **Coordinates:** Ensure `lat` and `lng` are numerical strings, not numbers (e.g., "41.9028", not 41.9028).

## 2. Documentation (`docs/*.md`)
- **Tone:** Enforce the **Microsoft Writing Style Guide**.
  - Use "You" (second person).
  - Be direct and action-oriented.
  - Avoid polite fluff ("Please", "Don't worry").
- **Structure:** Ensure headers use Sentence case (e.g., "How to update data").

## 3. Code (`script.js`, `index.html`)
- **Performance:** Flag any loops that iterate over the entire dataset unnecessarily.
- **Accessibility:** Ensure all `<img>` tags have `alt` text and colors have sufficient contrast.

