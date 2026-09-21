---
description: >-
  Research, record, and validate verified ISIL, Wikidata, and GeoNames
  identifiers for DMMapp library records.
---

# Identifier research

Use this guide when you add, correct, or review an ISIL, Wikidata QID, or
GeoNames ID. DMMapp only publishes an identifier when the evidence identifies
the same holding institution, relevant unit, or place as the catalogue record.

The authoritative catalogue remains `docs/assets/data.json`. The accompanying
`research/identifier-evidence.csv` ledger records how each identifier decision
was reached. The ledger has one row for every record and identifier field,
including identifiers that remain absent because the research was unresolved.

Research status is not maintainer approval. Values introduced before the
approval gate remain public while DMMapp maintainers audit their target and
scope. Only an exact row in
[`link-assertions.csv`](assets/link-assertions.csv), backed by a reviewed DMMapp
pull request, marks a relationship as approved for linked-data publication.
Every new or changed value requires that approval before merge.

## Decide whether to add an identifier

Add a value only after you confirm the exact match. Leave the field absent when
the source is ambiguous, describes a different branch, has a conflicting
location, or cannot be checked reliably.

| Field | It identifies | Accept a value when | Do not accept a value when |
| --- | --- | --- | --- |
| `isil` | The holding institution or relevant unit | The issuing ISIL registry or an institutional source names the same unit | It names a parent university, another branch, or an institution in another city |
| `wikidata_qid` | The holding institution or relevant unit | The item name and location agree, and an official website or verified ISIL corroborates it | A search result only looks similar, or the item conflicts with the record |
| `geonames_id` | The listed city and country | The GeoNames record agrees on place, country, and administrative context where needed | Same-name places cannot be distinguished from the available evidence |

For ISIL syntax, DMMapp accepts a registered one-to-four-letter agency prefix,
a hyphen, and an identifier up to 16 characters long. The prefix is usually a
country code, but registered non-country prefixes are valid. The [ISIL
technical guidance](https://biblstandard.dk/rfid/docs/clarification_28560-3.htm)
describes those prefixes and the identifier length.

## Record the decision in the evidence ledger

The CSV header is fixed. Do not rename, reorder, or omit columns.

```text
record_id,field,value,status,source_url,corroborating_url,checked_on,note
```

Each record requires exactly three rows: one for `isil`, one for
`wikidata_qid`, and one for `geonames_id`.

### Verified row

Use `status` `verified` when you add the same value to `data.json`.

- Set `value` to the identifier exactly as it appears in `data.json`.
- Set `source_url` to the direct public authority or registry record.
- For `wikidata_qid`, set `corroborating_url` to a matching official
  institutional site or issuing-registry record.
- Set `checked_on` to the date you reviewed the source in `YYYY-MM-DD` format.
- Explain the match briefly in `note`, such as the matching institution, unit,
  city, or country.

Example:

```text
3,wikidata_qid,Q623578,verified,https://www.wikidata.org/wiki/Q623578,https://www.nla.gov.au/,2026-09-20,"Exact institution item; country and city agree; official website matches."
```

### Unresolved row

Use `status` `unresolved` when you leave the identifier field out of
`data.json`.

- Leave `value`, `source_url`, and `corroborating_url` empty.
- Set `checked_on` to the research date.
- State the reason in `note`. Examples include `No exact issuing-registry
  match was confirmed for this institution or unit.` and `2 same-name place
  candidates; no unique location crosswalk.`

An unavailable or blocked source is not evidence that the identifier does not
exist. Record the access limitation and leave the field unresolved.

## Research workflow

1. Read the catalogue record and preserve its existing ID, collection URL,
   rights data, link status, and recency fields.
2. Find candidates in the relevant authority source. A search result is a lead,
   not a verified match.
3. Confirm the exact institution or place using the criteria above.
4. Update `data.json` only for verified values.
5. Add or update all three ledger rows for the record.
6. Run the checks before requesting review.

For GeoNames, begin with the [downloadable country
extracts](https://download.geonames.org/export/dump/) when a batch needs place
candidates. Confirm a selected ID on its GeoNames record page or RDF record.
The place data used by DMMapp requires [GeoNames attribution](https://www.geonames.org/export/);
this guide and the data schema credit GeoNames accordingly.

If you query Wikimedia services programmatically, identify DMMapp in the user
agent, keep concurrency low, and honour retry responses. Follow the current
[Wikimedia API rate-limit guidance](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits/).

## Validate the catalogue and ledger

Run the two checks together after changing a record or its evidence.

**Command safety**: Safe

```bash
python scripts/validate_data.py
python scripts/validate_identifier_evidence.py
```

`validate_data.py` checks JSON structure and the schema, including the ISIL
format. `validate_identifier_evidence.py` checks that the ledger has one unique
row per record and field, that its verified values agree with `data.json`, and
that source, date, and status rules are met.

The evidence checker does not establish that an external authority record is
semantically correct. Reviewers must open the linked records and assess the
institution, unit, city, country, and source authority before merging.

## Review a proposed identifier change

Review the catalogue and ledger together.

1. Check that the identifier in `data.json` matches the verified ledger value.
2. Open the direct source and confirm the named institution or place.
3. For a Wikidata QID, also open the corroborating official or registry source.
4. Confirm that unresolved rows contain no identifier or source URL and explain
   the gap.
5. Run the validation commands, or confirm that the `validate-data` GitHub
   check passed on the pull request.
6. For a new or changed value, confirm that the approved assertion row records
   the reviewer and the final reviewed pull-request revision.

## Evidence and review

| Item | Evidence | Verified | Review owner | Next review or trigger |
| --- | --- | --- | --- | --- |
| Ledger format and rules | `scripts/validate_identifier_evidence.py` and `tests/test_validate_identifier_evidence.py` | 2026-09-20 | Data maintainer | Any schema or ledger change |
| Identifier syntax | `schema.json` and `tests/test_validate_data.py` | 2026-09-20 | Data maintainer | ISIL rule change |
| Automated enforcement | `.github/workflows/validate.yml` and `.github/workflows/deploy.yml` | 2026-09-20 | Repository maintainer | Workflow change |
