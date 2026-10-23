---
description: Maintain redirects and monitor search discovery after the DMMapp migration.
---

# Maintain the site migration

On 23 October 2026, the DMMapp and its blog moved to the static GitHub Pages
site. Keep the published project address stable:

- [Directory](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/)
- [Blog](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/blog/)

## Preserve access from old links

Keep the old domains, certificates, and permanent redirects working until at
least **23 October 2027**, preferably indefinitely. Preserve each known article,
library, feed, and image route with a server-side **301** redirect to its
corresponding destination. Avoid sending every old URL to the homepage.
Check domain and certificate renewal dates before they expire; a redirect rule
cannot preserve access after its old domain or HTTPS service stops working.

Before changing redirects, retain the previous rules for rollback. Check a
sample of old URLs, including deep links and images: each should reach the
intended destination without a loop, and the destination should return 200.
If a rule breaks a working route, restore its previous mapping and investigate
before extending the change. Keep historical article text intact when it
describes the former application.

## Maintain crawler discovery

This repository publishes [the page sitemap](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/sitemap.xml)
and [the image sitemap](https://sexycodicology.github.io/Digitized-Medieval-Manuscripts-app/image-sitemap.xml).
The image sitemap associates existing images displayed in article content
with those articles; it excludes navigation images and repeated blog listings.
Preserved image files that an article does not display are not listed.

The project-level `robots.txt` declares both sitemaps. Crawlers request
`robots.txt` at the **hostname root**, so maintain the declarations in the
separate [SexyCodicology hostname repository](https://github.com/SexyCodicology/sexycodicology.github.io)
as well. Editing this project's file alone does not update the hostname root.

Operators with access to Google Search Console and Bing Webmaster Tools
should submit both destination sitemaps and check their processing status.
Use the site-move tools where applicable and inspect representative old and
new URLs. Submission, a successful fetch, and a redirect are distinct from
indexing; none guarantees that a search engine will index a page or image.

## Monitor the first eight weeks

Review the migration for eight weeks, each Monday at 09:00 Europe/Amsterdam,
from **26 October to 14 December 2026**:

- Confirm the deployment and both sitemaps remain available.
- Test representative old-to-new journeys for pages, feeds, and images.
- Review Google and Bing crawl/indexing reports for unexpected errors,
  blocked resources, or conflicting canonical URLs.
- Compare page and image impressions and clicks with the previous period;
  investigate sustained losses alongside crawl errors and redirect failures.

Record the date, evidence, and corrective action in a maintenance issue.
Keep account details and private search-console exports out of this public
repository. Continue periodic redirect checks after the eight-week review.

## Further guidance

- [Google: site moves with URL changes](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)
- [Google: build and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google: image sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps)
