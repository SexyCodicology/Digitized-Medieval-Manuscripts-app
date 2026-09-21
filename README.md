# 📚 Digitized Medieval Manuscripts App

> A curated, interactive directory of digitized medieval manuscript libraries worldwide with support for standardized image formats and open access resources.

[![License: CC0 1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-green)](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/)
[![Build Status](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/actions/workflows/deploy.yml/badge.svg)](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/actions/workflows/deploy.yml)
[![JSON Schema Validation](https://img.shields.io/badge/Data%20Format-JSON%20Schema-blue)](./schema.json)

## What you can do

Use DMMapp (Digitized Medieval Manuscripts Application) to discover and access digitized medieval manuscript collections from around the world. Instead of visiting dozens of institutional websites, you can search a single directory that gives you:

- 🔍 Advanced filtering and search capabilities
- 🌍 Global coverage with location-based discovery
- 📋 Real-time statistics and insights
- ♿ Full accessibility support
- 🚀 Lightning-fast performance with no external dependencies

## Features

### Interactive dashboard
- **Real-time search**: Filter libraries instantly by name, city, nation, project, or copyright text
- **Advanced filters**:
  - Filter by nation or aggregating project (e.g. Europeana)
  - Filter by standardized image format support (lets you access images the same way across different libraries)
  - Filter by open license or normalized licence category (CC0, CC BY, All Rights Reserved, etc.)
  - Filter to only collections whose link isn't known to be broken
- **Sorting**: Sort alphabetically by library or location, or by approximate manuscript quantity
- **Export and share**: Download the current results as CSV or JSON, or copy a shareable link that preserves your search, filters, and sort order
- **Discovery tools**: Jump to a randomly chosen library, or browse every entry in a crawlable alphabetical index
- **Recently added and updated**: A homepage list surfaces the latest dated additions and corrections
- **Live statistics**: Total libraries, participating nations, IIIF-enabled collections, and linked aggregator projects
- **Responsive design**: Works on desktop, tablet, and mobile devices

### Detailed library information
Each library gets its own crawlable page, generated at build time, with:
- **Library name and location**: Official institution name, city, and country
- **Website link**: Direct access to the digitized collection, including a dated "last confirmed working" or "broken link" notice
- **Standardized image format support**: Badge and, when available, direct links to browse the IIIF collection or open an example manifest
- **Open license**: Badge for freely reusable collections, alongside the institution's verbatim copyright statement
- **Manuscript quantity**: Approximate number of digitized manuscripts (Few, Dozens, Hundreds, Thousands, Unknown)
- **Aggregator memberships**: Every aggregating project the collection is discoverable through
- **Optional identifiers**: ISIL, Wikidata QID, and GeoNames ID, when verified
- **Stable record address**: An ID-only URL that survives a library-name correction
- **A pre-filled "Report a data issue" link**: Opens a GitHub issue form that already identifies the record

### Comprehensive documentation
- Getting started guide for browsing, searching, and filtering the dashboard
- Data structure guide covering every field, including optional identifiers and IIIF endpoints
- Identifier research guide covering source criteria, evidence rows, review, and GeoNames attribution
- Guides to the automated data validation and weekly link-checking workflows
- About the project, contributing guidelines, and local development setup
- A codicology primer for readers new to manuscript studies
- [Linked-data guidance](./docs/linked-data.md) for citing record IDs and reusing the static JSON-LD exports

## Quick start

### For researchers
Visit the live dashboard to browse and search:
👉 [Digitized Medieval Manuscripts App](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/)

No installation required. Everything runs in your browser.

### For contributors
Clone the repository and set up your local environment:

```bash
git clone https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app.git
cd Digitized-Medieval-Manuscripts-app
```

The dashboard is a MkDocs Material page, so you preview it the same way as the rest of the documentation. Install the dependencies from `requirements.txt`, then start the MkDocs development server:

```bash
pip install -r requirements.txt
mkdocs serve
```

Open `http://localhost:8000` in your browser to see the full dashboard.

## Project structure

```
Digitized-Medieval-Manuscripts-app/
├── mkdocs.yml                     # Documentation and dashboard build settings
├── schema.json                    # Data format definition (JSON Schema)
├── requirements.txt                # Python dependencies to build the site
├── requirements-dev.txt            # Adds pytest and jsonschema for local/CI testing
├── package.json                    # Node test tooling for docs/assets/dashboard.js
│
├── hooks/
│   ├── library_pages.py            # MkDocs build hook: generates the homepage
│                                    # table, the alphabetical index, and one
│                                    # page per library from data.json
│   └── linked_data.py              # Generates per-record and bulk JSON-LD
├── scripts/
│   ├── validate_data.py            # Validates data.json against schema.json
│   ├── validate_identifier_evidence.py
│   │                                # Checks the identifier evidence ledger
│   ├── apply_link_status.py        # Turns the weekly link-check report into
│                                    # is_disabled/last_checked proposals
│   └── backfill_licence_category.py
├── tests/                          # pytest suite for hooks/ and scripts/
│
├── research/
│   └── identifier-evidence.csv     # Source or unresolved decision per record and identifier
│
├── overrides/
│   ├── home.html                   # Dashboard template (extends Material's main.html)
│   ├── main.html                   # Site-wide template overrides
│   └── partials/
│
├── docs/                           # Documentation and dashboard source
│   ├── index.md                    # Dashboard home page (uses the home.html template)
│   ├── about.md                    # About the project
│   ├── getting-started.md          # How to use the dashboard
│   ├── docs-home.md                # Documentation landing page
│   ├── schema.md                   # Data structure guide
│   ├── update-data.md              # How to add or edit library entries
│   ├── identifier-research.md       # Evidence and review for authority identifiers
│   ├── workflow-validation.md      # How automated data validation works
│   ├── workflow-link-checking.md   # How the weekly link check works
│   ├── linked-data.md              # Persistent IDs, JSON-LD, and rights policy
│   ├── contributing.md             # How to contribute data or code
│   ├── setup.md                    # Local development setup
│   ├── support-us.md / store.md    # Patreon and merchandise
│   ├── codicology/                 # Manuscript-studies primer (not app-specific)
│   ├── blog/                       # Project news and updates
│   └── assets/
│       ├── dashboard.js            # Dashboard interactivity
│       ├── dashboard.test.js       # Node test suite for dashboard.js
│       ├── dashboard.css           # Dashboard styling
│       ├── library-aliases.json     # Historical name-based URL registry
│       └── data.json               # Library database
│
├── .github/workflows/
│   ├── deploy.yml                  # Validates, tests, builds, and deploys to Pages
│   ├── validate.yml                # Runs scripts/validate_data.py on data changes
│   └── link-checker.yml            # Weekly link health check, files issues and PRs
│
├── README.md                       # This file
├── CONTRIBUTING.md                 # Contribution guide
└── LICENSE                         # CC0 1.0 Universal license
```

Two pieces of the site are generated rather than written by hand:
`library-index.md` (a crawlable alphabetical index of every library) and one
page per library under `libraries/id-<id>/`. Historical name-based URLs remain
as compatibility pages. The build also publishes per-record and bulk JSON-LD.
These files come from the build hooks reading `docs/assets/data.json`, so they
are not committed as generated pages or exports.

## Technology stack

### Frontend dashboard
- **HTML5**: Semantic markup
- **CSS3**: Custom Material Design styling
- **Vanilla JavaScript**: No frameworks, pure web standards
- **Bootstrap Icons**: Accessible icons
- **Google Fonts (Roboto)**: Professional typography

### Documentation
- **MkDocs**: Static site generator
- **Material for MkDocs**: Responsive theme

### Data and validation
- **Data format**: A single JSON array (`docs/assets/data.json`), validated against `schema.json`
- **Data validation**: `scripts/validate_data.py` checks JSON syntax, required fields, data types, URL formats, identifier syntax, and aggregator name/URL consistency
- **Identifier evidence**: `research/identifier-evidence.csv` records one verified or unresolved ISIL, Wikidata, and GeoNames decision for every record; `scripts/validate_identifier_evidence.py` checks that it agrees with the catalogue
- **Automated testing**: `pytest` covers the build hook and scripts; a Node test suite (`docs/assets/dashboard.test.js`) covers the dashboard's client-side behavior
- **Link health**: A weekly [lychee](https://github.com/lycheeverse/lychee)-based check flags unreachable collection URLs and proposes dated status updates by pull request
- **GitHub Actions**: Automatic validation, testing, building, and deployment on every change

### Hosting and deployment
- **GitHub Pages**: Free, reliable hosting
- **GitHub Actions**: Automatic updates when you make changes

## Data schema

Each library entry in [docs/assets/data.json](./docs/assets/data.json) requires:

```json
{
  "id": "Unique record identifier",
  "library": "Official institution name",
  "nation": "Country name",
  "city": "City name",
  "website": "URL to digitized collection",
  "copyright": "Verbatim copyright or licence information",
  "licence_category": "CC0 | CC-BY | CC-BY-NC | CC-BY-NC-SA | CC-BY-NC-ND | All Rights Reserved | Mixed/Item-specific | Unknown",
  "quantity": "Few | Dozens | Hundreds | Thousands | Unknown",
  "iiif": "Supports standardized image format",
  "is_free_cultural_works_license": "Has open license",
  "aggregators": "Aggregating projects the library is discoverable through, as a list of { name, url }"
}
```

Several fields are optional and add extra detail when it can be verified:
`isil`, `wikidata_qid`, and `geonames_id` (authority-file identifiers),
`iiif_collection_url` and `iiif_example_manifest_url`/`iiif_example_manifest_label`
(direct IIIF endpoints), `is_disabled` and `last_checked` (link status, normally
set by the weekly link check), and `added`/`last_edited` (homepage recency
dates).

See [schema.json](./schema.json) for the complete definition and
[docs/schema.md](./docs/schema.md) for a field-by-field guide. Read
[docs/identifier-research.md](./docs/identifier-research.md) before adding or
reviewing an authority identifier.

## Contributing

You can help in several ways:

### Add libraries
1. **Search first**: Make sure the library isn't already listed in [docs/assets/data.json](./docs/assets/data.json)
2. **Edit the file**: Add your entry following the data format
3. **Submit a pull request**: Send it to the `master` branch

[See detailed contributing guide →](./CONTRIBUTING.md)

### Report issues
Found an error or have a suggestion?
[Open an issue](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/issues)

### Improve the codebase
- Enhance the dashboard
- Improve documentation
- Suggest features
- Fix bugs

## About standardized image formats

Libraries that support standardized image formats (like IIIF) let you:
- **Search across multiple collections** simultaneously
- **View and compare manuscripts** side-by-side
- **Zoom, rotate, and annotate** images
- **Reuse collections** freely in your own projects

## Design principles

1. **Simplicity**: Clean, maintainable code and design
2. **Performance**: Fast loading with minimal dependencies
3. **Accessibility**: Works for all users, including those using assistive technology
4. **Consistency**: Unified design across all components
5. **Open source**: Transparent development, community-driven

## License

This project is dedicated to the public domain under the
[CC0 1.0 Universal license](./LICENSE).

You can copy, modify, and distribute the project's directory data and site
content without requesting permission. Check the source institution's terms
before reusing material from a linked collection.

## Support and questions

- **Documentation**: See the [docs/](./docs/) folder
- **Issues and discussions**: [GitHub Issues](https://github.com/SexyCodicology/Digitized-Medieval-Manuscripts-app/issues)
- **Contributing**: See [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Code of Conduct**: See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)

## Related resources

- [Standardized image format information](https://iiif.io/)
- [MkDocs documentation](https://www.mkdocs.org/)
- [Data schema resources](https://json-schema.org/)
- [Material Design](https://material.io/)
- [GitHub Pages](https://pages.github.com/)

## Project statistics

- **Total libraries**: Check the dashboard for current count
- **Countries represented**: Explore the directory to discover
- **Collections with standardized image format support**: Use the filter to see available options
- **Last updated**: Check the GitHub commit history

## Roadmap

Future enhancements you might see:
- Geographic map view of libraries
- Advanced search with manuscript details
- Collections comparison tool
- User submissions and voting
- API for other applications
- Multi-language support

## Author

Created with ❤️ in the Netherlands

Want recognition? [Contribute today!](./CONTRIBUTING.md)

---

**Made with ❤️ for researchers, historians, and manuscript enthusiasts everywhere.**

[Visit the live dashboard](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/) | [View documentation](./docs/) | [Contribute](./CONTRIBUTING.md)
