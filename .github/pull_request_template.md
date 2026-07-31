## Change Type
- [ ] 🆕 New Library Entry
- [ ] ✏️ Correction (Typo, broken link, or other fix)
- [ ] 🗑️ Removal (Library closed/no longer digitized)
- [ ] 💻 Code / dashboard change
- [ ] 📚 Documentation change

## Description
*What does this change do, and why is it needed? If this is a library entry, which library is it?*

## Checklist

### Data changes (`docs/assets/data.json`)
- [ ] I have verified the URL works.
- [ ] I have checked that the JSON is valid (no trailing commas).
- [ ] I have checked that the entry validates against `schema.json` (required fields, correct types, valid `quantity` value).
- [ ] I have evidence for any IIIF claim (`iiif: true`) and for the stated `copyright`/`is_free_cultural_works_license` license.

### Code / documentation changes
- [ ] I have tested this change locally with `mkdocs serve` (the dashboard and docs are both built by MkDocs).
- [ ] I have not introduced unrelated formatting or dependency changes.
- [ ] I have updated relevant docs, if applicable.
