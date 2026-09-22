---
description: >-
  Research, record, and validate direct IIIF Collection and representative
  Manifest endpoints for DMMapp library records.
---

# IIIF endpoint research

Use this guide when you add, correct, or review a direct IIIF endpoint. DMMapp
records collection access points, not every manuscript held by an institution.
Only record an endpoint after you confirm its type, contents, and relationship
to the listed access point.

The catalogue remains authoritative for published values. The sparse
`research/iiif-evidence.csv` ledger covers every direct endpoint already in
`data.json` and every pending endpoint proposal in the linked-data pilot. It
does not record a row when research found no endpoint.

Evidence is not approval. A DMMapp maintainer approves a relationship through
a reviewed pull request and an exact row in
[`link-assertions.csv`](assets/link-assertions.csv). Until then, the linked-data
export does not publish the endpoint as a semantic relationship.

## Choose the correct endpoint type

| Field | Use it for | Confirm before recording it |
| --- | --- | --- |
| `iiif_collection_url` | A direct IIIF Presentation API Collection representing the listed medieval-manuscript access point | The response is a v2 or v3 Collection, and its members or description have the right collection scope |
| `iiif_example_manifest_url` | One named representative manuscript | The response is a v2 or v3 Manifest, and its label, shelfmark, holding institution, or catalogue record identifies the same item |

Do not use an image-service `info.json`, an HTML viewer, a search-result page,
or an institution-wide Collection that includes unrelated holdings. Do not
infer a Collection URL from a working Manifest URL.

## Record the evidence

The CSV header is fixed:

```text
record_id,field,value,status,source_url,corroborating_url,checked_on,note
```

Use `verified` when `value` is already published in `data.json`. Use `proposed`
only for a pending pilot candidate whose catalogue field is empty.

- Set `source_url` to the direct endpoint. It must equal `value`.
- Set `corroborating_url` to a distinct, exact public catalogue,
  institutional, or item page that establishes the endpoint's relationship to
  the DMMapp access point. A generic homepage is not enough.
- Set `checked_on` to the date you inspected both sources, in `YYYY-MM-DD`
  format.
- In `note`, record the Presentation API version, resource type, identifying
  label or shelfmark, and the relevant scope. Mention a stale embedded link if
  you found one, and use the current working catalogue URL as corroboration.

Do not add a `proposed` row outside the pilot. Add the endpoint to `data.json`
and its reviewed assertion in one pull request after the ordinary maintainer
review process.

## Research workflow

1. Read the DMMapp record and decide whether it represents a direct catalogue,
   a portal, or an aggregator-specific access point.
2. Open the candidate endpoint as JSON. Confirm its IIIF Presentation API
   context and whether it is a Collection or Manifest.
3. Inspect the label, metadata, members, canvases, and rights statement where
   available. These properties help identify the resource but do not prove its
   relationship to DMMapp by themselves.
4. Open an exact institutional catalogue or item page and compare the
   institution, collection, shelfmark, and title.
5. Record the evidence row. Keep a pilot candidate `proposed` until a
   maintainer reviews it.
6. Run the offline checks before requesting review.

## Validate the evidence

**Command safety**: Safe

```bash
python scripts/validate_data.py
python scripts/validate_iiif_evidence.py
python scripts/validate_link_assertions.py
```

The IIIF evidence validator does not make network requests. It checks the CSV
contract, public URL syntax, dates, status, uniqueness, and exact agreement
with the catalogue or pending pilot candidate. It cannot determine whether an
endpoint is a real IIIF resource or has the right semantic scope. The reviewer
must open both sources and make that decision.

## Review an endpoint

1. Confirm that the direct JSON is a Presentation API v2 or v3 Collection or
   Manifest, as claimed.
2. Confirm that the exact corroborating page identifies the same collection or
   manuscript and holding institution.
3. For a Collection, check that the scope matches the DMMapp access point. For
   a Manifest, check that it is a suitable named representative item.
4. Check the catalogue publication state in the generated pilot review packet.
5. Record a final pilot decision and assertion provenance only after the
   maintainer has reviewed the final pull-request revision.

## Evidence and review

| Item | Evidence | Verified | Review owner | Next review or trigger |
| --- | --- | --- | --- | --- |
| Ledger format and rules | `scripts/validate_iiif_evidence.py` and `tests/test_validate_iiif_evidence.py` | 2026-09-22 | Data maintainer | Any IIIF field or ledger change |
| Review packet integration | `scripts/report_linked_data_pilot.py` and `tests/test_report_linked_data_pilot.py` | 2026-09-22 | Data maintainer | Pilot workflow change |
| Automated enforcement | `.github/workflows/validate.yml` and `.github/workflows/deploy.yml` | 2026-09-22 | Repository maintainer | Workflow change |
