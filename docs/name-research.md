---
description: >-
  Review holding-institution names and access-point titles without changing
  DMMapp's stable directory identifiers or unreviewed linked-data claims.
---

# Institution-name research

Use this procedure when you correct a `library` name or add an
`access_point_title` or `library_alternate_names` entry. The tracked
`research/name-evidence.csv` register holds one preferred-name decision for
every directory record. Legacy labels start as `pending`; that status does not
mean the name has been checked. The first review queue includes the 25 record
IDs already selected for the [linked-data pilot](linked-data-pilot.md). Review
them in small batches; their name decisions remain separate from authority and
IIIF decisions.

## Identify what the record describes

Read the record's `website`, `city`, `nation`, aggregators, and any existing
authority evidence. Decide which institution or relevant unit holds the
manuscripts and which portal or collection provides the access point. Two
records can name the same institution while describing different access points.
Do not merge or renumber them because their names, authority identifiers, or
websites match.

Use the institution's current official name as it publishes it, preserving
its script and diacritics. Use a public institutional page or issuing registry
to confirm the exact unit. A search result, `last_checked` date, or shared URL
does not verify the institution. Keep a doubtful existing label `pending` and
explain the uncertainty in the register.

Add `access_point_title` only when the source names a distinct portal or
collection. Add a current official variant or translation under
`library_alternate_names`; add its BCP 47 `language` when known. A former name,
incorrect spelling, or portal title is not an alternate institution name.
These source fields support reader discovery. They do not create an RDF
institution resource or an identity relationship.

## Record and review evidence

The register columns are fixed:

```text
record_id,field,value,language,status,source_url,checked_on,note
```

Use `field` `library`, `access_point_title`, or `library_alternate_names`.
Keep exactly one `library` row per record. Use `pending` for an unverified
current name or unpublished candidate. Use `verified` only after opening a
public source that names the correct institution, unit, or access point.
Verified rows need the exact published value, source URL, and real check date.
For alternate names, the register's language must match the data entry.

Before changing `library`, check whether the record's ISIL, Wikidata QID, and
any approved holding-institution relationship still describe that holder or
unit. Follow [identifier research](identifier-research.md) and the existing
assertion approval process if one of those values must change. A name-only
correction does not add a row to `link-assertions.csv`. Preserve `last_checked`
unless you actually reassessed the collection URL.

For a changed `library`, append its new name-derived slug under the same ID in
`library-aliases.json`. Keep every earlier slug. Set `last_edited` to the real
date of a material correction; keep `added` and the stable ID unchanged.
Document the public name evidence and any unresolved scope question in the
pull request for maintainer review.

**Command safety**: Safe

```bash
python scripts/validate_data.py
python scripts/validate_name_evidence.py
```

The first check validates catalogue shape and alias coverage. The second
checks register completeness and agreement with published fields. In pull
requests, `verify_name_history.py` also requires a verified row for every
newly published name or title. These checks cannot establish that a source's
institutional claim is true; a maintainer must inspect the cited page.

For the full build and publication checks, follow
[How we validate data](workflow-validation.md) and
[Linked data and persistent identifiers](linked-data.md).
