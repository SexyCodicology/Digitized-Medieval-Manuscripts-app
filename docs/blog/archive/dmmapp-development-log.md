---
description: Historical release notes preserved from the original DMMapp Blog.
---

# DMMapp Development Log

!!! info "Archived page"
    This page preserves the text of the [original DMMapp Blog page](https://blog.digitizedmedievalmanuscripts.org/dmmapp-development-log/).
    References to the former application and support arrangements are historical.
    The original blog content was published under [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

Here you can find all the latest updates for the DMMapp – Digitized Medieval Manuscripts app – by the Sexy Codicology team.

*We would like to thank [our patrons](https://blog.digitizedmedievalmanuscripts.org/support-us/patrons/) over at [Patreon](https://www.patreon.com/SexyCodicology) for supporting us with the right quantity of coffee needed to pour endless code into our computers.*

### v4.0 (2018/02/2019)

- Complete code rewrite of the DMMapp
    - Migrated to Laravel framework
- Optimized overall loading performance
- Implemented permalinks for all entries in the DMMapp data: for each institution and individual ID (“DMMapp ID”)
- Vast improvements to website’s metadata to help “discoverability”
    - Each Institution page has its own metadata:
        - Individual page title
        - Individual description of the page’s contents
        - Additional metadata about Sexy Codicology and the DMMapp
- Database migrated from JSON to SQLite
- Created admin panel to easily, quickly, and effectively update DMMapp data entries
- Vast update to the DMMapp’s data (links, location, library names, etc.)
- Additional data added: “Is part of” and “IIIF” fields
- Secured Google Maps’ API usage
- Improved database security (CSFR tokens)
- URL updated to <https://digitizedmedievalmanuscripts.org> instead of https://digitizedmedievalmanuscripts.org/app
- https://digitizedmedievalmanuscripts.org/beta is now archived
- Implemented 301-redirects: “beta” URLs to final URLs
- Improvements to the landing page
    - Endless text edits
    - Easier to find links to the “Data” part of the app
    - Improved visibility of “Report error”
    - Improved visibility of “Report missing repository”
- Improvements to the table’s navigability on smaller screens
    - Long URLs will no longer mess up the interface
- General improvements to performance and looks on small screens (phones and tablets)
- An endless list of smaller improvements
