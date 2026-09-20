# AGENTS.md

Repository instructions for AI coding agents. Follow the closest `AGENTS.md`
in the directory tree when one exists; explicit user instructions take
precedence over every repository instruction.

## Project overview

DMMapp is a public, CC0-licensed directory of digitised medieval manuscript
collections. It publishes a MkDocs Material site to GitHub Pages. The site
combines a curated JSON catalogue, Python validation and build hooks, and a
vanilla JavaScript dashboard.

This is a public repository. Write guidance and examples for external
contributors. Do not add private infrastructure details, credentials, personal
data, unpublished research, or non-public institution URLs.

## Read before changing

- Read `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` before preparing a
  contribution.
- For a catalogue change, read `docs/update-data.md`, `docs/schema.md`, and
  `schema.json` before editing data.
- For link-status work, read `docs/workflow-link-checking.md`. For validation
  behaviour, read `docs/workflow-validation.md` and
  `scripts/validate_data.py`.
- Match nearby code and documentation. Do not introduce a framework, build
  system, dependency, tracking service, or broad reformatting without a
  confirmed need.

## Repository map

| Area | Primary files |
| --- | --- |
| Catalogue data | `docs/assets/data.json`, `schema.json`, `scripts/validate_data.py` |
| Public documentation | `docs/`, `mkdocs.yml` |
| Homepage and generated collection pages | `overrides/`, `hooks/library_pages.py` |
| Dashboard behaviour and styling | `docs/assets/dashboard.js`, `docs/assets/dashboard.css` |
| Dashboard tests | `docs/assets/dashboard.test.js` |
| Build-hook tests | `tests/` |
| Deployment and automated checks | `.github/workflows/` |

`site/`, `.cache/`, `node_modules/`, virtual environments, and local editor
files are generated or local-only. Do not commit them.

## Catalogue and editorial integrity

- Treat every record as a public research aid. Use authoritative public sources
  and verify factual changes before editing. In a pull request, state the
  source or evidence that supports a material catalogue correction.
- Preserve a record's stable `id`. For a new record, use a unique positive
  integer; gaps are valid. Do not renumber existing records.
- Use the institution's official name and the direct digitised-manuscript
  collection URL where available. Test a new or changed URL before proposing
  it.
- Copy `copyright` exactly as the institution states it. Choose
  `licence_category` only from the documented controlled values. Use
  `Unknown` rather than inventing a rights statement or an approximate count.
- Set `iiif` to `true` only after verifying IIIF support. Add IIIF collection
  or manifest URLs only when they are direct Presentation API v2/v3 JSON
  endpoints for the listed collection or a named representative manuscript.
- Do not mark a collection `is_disabled` because of a timeout, access denial,
  rate limit, or 5xx response. The automated link check treats only 404 and
  410 as conclusive; investigate a move and update `website` when appropriate.
- Keep data changes focused. Do not silently change unrelated records while
  researching one collection.

## Implementation conventions

- Keep the dashboard dependency-free and follow the existing vanilla
  JavaScript, HTML, and CSS patterns.
- Preserve accessibility and progressive enhancement: use semantic markup,
  keyboard-accessible controls, visible focus, and text alternatives for
  non-text content.
- Keep generated page routes and public URLs stable unless the change includes
  a compatibility assessment and an update to affected links and tests.
- Write concise public documentation in clear British English. Explain
  non-obvious decisions, not obvious syntax.

## Setup and verification

Use the narrowest check that covers the change, then inspect the final diff.
The continuous-integration build uses Python 3.11 and Node 22.

```bash
python -m pip install -r requirements-dev.txt
npm ci
```

| Change | Run before submitting |
| --- | --- |
| Catalogue data or schema | `python scripts/validate_data.py` |
| Python hook or generated-page behaviour | `python -m pytest tests -q` |
| Dashboard JavaScript | `npm test` |
| Markdown, templates, assets, configuration, or a release candidate | `mkdocs build --clean` |

Use `mkdocs serve` to preview the site locally. The build creates the ignored
`site/` directory. Do not claim that an external collection, IIIF service, or
GitHub Pages deployment works unless you verified that service directly.

## Contribution discipline

- Make a small, cohesive change that preserves unrelated behaviour and
  existing contributor work.
- Do not commit credentials, access tokens, personal contact details, private
  correspondence, or copied manuscript images and metadata without clear
  permission.
- Respect source institutions' rights statements. CC0 applies to this
  repository's material; it does not change the terms for material available
  through linked collections.
- Keep commits and pull requests focused, and explain user-visible or data
  consequences. Follow the contribution workflow in `CONTRIBUTING.md`.
