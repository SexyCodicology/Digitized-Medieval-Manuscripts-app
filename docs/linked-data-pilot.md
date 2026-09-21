---
description: >-
  Review the first 25 DMMapp records for scoped authority and IIIF links.
---

# Linked-data audit pilot

This pilot tests DMMapp's evidence and approval workflow on 25 deliberately
varied directory records. It does not set a coverage target and does not imply
that their current identifiers are approved. Existing values remain visible
while maintainers check their target, type, and scope.

Selected from the catalogue on 21 September 2026, the pilot spans 16 catalogue
nation values, eight aggregators, repeated institution names,
institution-versus-portal distinctions, six rights categories, IIIF and
non-IIIF entries, and the only then-recorded direct IIIF Manifest. The
[`linked-data-pilot-review.csv`](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/blob/master/research/linked-data-pilot-review.csv)
ledger is the source of truth for field-level progress. The approved
[`link-assertions.csv`](assets/link-assertions.csv) register is the source of
truth for relationships that may enter JSON-LD. The research ledger provides
candidate evidence; it is not an approval register.

## Selected records

| ID | Directory entry | Candidates at selection | Why it is in the pilot |
| ---: | --- | --- | --- |
| 3 | National Library of Australia | ISIL, Wikidata, GeoNames | Tests whether an ISIL for a named service or unit has the right scope. |
| 24 | Universiteitsbibliotheek Gent | Wikidata, GeoNames | Compare with ID 29 before approving an institution-level target. |
| 29 | Universiteitsbibliotheek Gent | GeoNames | Same name and city as ID 24, but a different portal and IIIF state. |
| 47 | Det Kongelige Bibliotek | GeoNames | Compare a direct entry with aggregator-specific ID 670. |
| 670 | Det Kongelige Bibliotek | GeoNames | Tests the Irish Script on Screen access point and rights difference. |
| 411 | National Library of Scotland | Wikidata, GeoNames | Compare with ID 669 and resolve the country-label difference. |
| 669 | National Library of Scotland | GeoNames | Same institution name and city as ID 411, but a different access point. |
| 402 | Jagiellonian Library | Wikidata, GeoNames | Compare a direct entry with the e-Codices access point in ID 613. |
| 613 | Jagiellonian Library | GeoNames | Tests whether an aggregator view changes the relationship scope. |
| 235 | Staatsbibliothek zu Berlin | GeoNames | Compare a non-IIIF direct entry with ID 275. |
| 275 | Staatsbibliothek zu Berlin | GeoNames | Tests a same-name IIIF-marked aggregator access point. |
| 238 | ULB Düsseldorf | ISIL, Wikidata, GeoNames | Compare three institution/place candidates with ID 261. |
| 261 | ULB Düsseldorf | ISIL, Wikidata, GeoNames | Same candidates as ID 238, but through Handschriftenportal. |
| 51 | The Bodleian Library | GeoNames | Distinguish an institution entry from the digital portal in ID 62. |
| 62 | New Digital Bodleian | GeoNames | Tests an explicitly portal-level access point. |
| 44 | National Library of the Czech Republic | GeoNames | Covers Manuscriptorium and mixed or item-specific rights. |
| 267 | Bayerische Staatsbibliothek | ISIL, Wikidata, GeoNames, IIIF Manifest | Tests the only direct IIIF endpoint and all three authority fields. |
| 318 | National Library of Ireland | GeoNames | Covers an IIIF-marked, all-rights-reserved aggregator entry. |
| 433 | National Library of Sweden | GeoNames | Covers Alvin, CC0, and a non-IIIF entry. |
| 574 | Biblioteca Apostolica Vaticana | GeoNames | Tests a sovereign-city place target without an aggregator. |
| 515 | Harvard University | GeoNames | Covers Digital Scriptorium and an institution-wide name. |
| 409 | Batthyaneum Library – Branch of the National Library of Romania | GeoNames | Tests a named branch of a national library. |
| 78 | Bibliothèque municipale, Douai | GeoNames | Tests a generic repeated name disambiguated by place. |
| 154 | Bibliothèque municipale, Castres | None | Ensures the pilot also preserves a justified absence of identifiers. |
| 396 | National Library of New Zealand | GeoNames | Tests whether the listed suburb and institutional location align. |

Names are shortened in this table only. `data.json` remains authoritative for
the public record name and values.

## Review one record

1. Open the record in `data.json` and all three matching rows in
   `research/identifier-evidence.csv`.
2. Confirm what the DMMapp record describes: an institution, a branch, a
   manuscript portal, or an aggregator-specific access point.
3. Open every cited source. Check the target's name, type, location, parent or
   branch relationship, and public URL. A search-result resemblance is not
   enough.
4. For an IIIF endpoint, inspect the returned Presentation API JSON and confirm
   whether it is a Collection or one representative Manifest. Confirm that its
   contents fit this access point.
5. Decide each populated field separately: approve it, correct it with new
   evidence, remove it, or leave it pending. Do not let approval of one field
   imply approval of another.
6. For an approved relationship, add the exact current value and provenance to
   `link-assertions.csv`. For a correction or removal, update `data.json` and
   the research ledger in the same pull request.
7. Have a DMMapp maintainer review the final commit. Record that maintainer's
   GitHub name, review date, and pull-request URL only after the review happens.

Record one of these decisions in the pilot ledger:

| Decision | Use it when |
| --- | --- |
| `pending` | The candidate still awaits maintainer review. Leave all three review-provenance columns empty. |
| `approve` | The candidate is correct. Add the matching assertion row and use the same reviewer, date, and PR URL in both files. |
| `correct` | The candidate was wrong and `data.json` now contains a reviewed replacement. Add an assertion for the replacement. |
| `remove` | The candidate was wrong and the field has been removed from `data.json`. |
| `absent` | The deliberately empty control field should remain empty after review. |

Do not use a final decision without a DMMapp maintainer's public GitHub name,
review date, and DMMapp pull-request URL. The validator rejects a final
`approve` or `correct` decision unless it has an exact assertion with matching
review provenance.

## Completion criteria

The pilot is complete when maintainers have assessed every populated authority
or IIIF field in these 25 records and documented each outcome. An approval has
an exact assertion row. A correction or removal has updated evidence. A
deliberately absent value remains absent with an unresolved research reason.

Completion does not require every record to gain links. It requires clear,
reviewable decisions and conservative RDF. DMMapp never publishes `sameAs`
between a directory entry and an institution, place, or manuscript.

Run the catalogue, evidence, assertion, and history checks before merging the
pilot pull request. See [Update the dashboard data](update-data.md) for the
commands and review sequence.

**Command safety**: Safe

```bash
python scripts/validate_linked_data_pilot.py
```

The current ledger has 41 field decisions across the 25 selected records. A
passing validator can still report pending decisions; the pilot is complete
only when it reports zero pending.
