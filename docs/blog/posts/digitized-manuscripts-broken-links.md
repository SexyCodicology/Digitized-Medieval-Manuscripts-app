---
date:
  created: 2017-09-26
  updated: 2023-03-13
categories:
- Digitized Libraries
- Broken Links
- DMMapp Updates
authors:
- giulio
slug: digitized-manuscripts-broken-links
---
# Disappearing Digitized Manuscripts: a very sad story of broken links

Every year we go through the links in the [DMMapp](https://digitizedmedievalmanuscripts.org/), knowing that unavoidably we will encounter broken links: links that once worked and lead to beautiful digitized manuscripts and that now are simply gone.
*pouf* - no more.

<!-- more -->

## Fancy statistics about broken links

We would like to share some statistics from this year's tests that will help drawing an interesting picture:

- Of our 500+ links only 311 returned a *200 OK* response which means: they are working links and everything is OK.
- 31 returned the code ***301 Moved permanently*** - This is very good: the repository moved to a new web-address and when you go to the old website you are automatically redirected to the new one.
- 21 returned *302 Moved temporarily*, found - Similar to 301, it indicates that the website has temporary new address. Good!
- 15 **returned error *404 Cannot be found*** - The saddest message of them all: The website or page does not exist anymore.
- One *500 Internal server error* - Usually a temporary issue. The repository is having some technical issues.

Whenever we encounter these broken links, we try to repair them: we start a small hunt on Google, we edit the URLs, try everything to find these repositories again. Unfortunately, this time we were successful to revive only two links. **The rest had disappeared resulting in broken links, and with them all their digitized manuscripts. That's around 2% of the DMMapp's links gone.**
How many digitized are not longer accessible precisely? Difficult to say; hundreds of digital books, at least; but without detailed data it is impossible to count.
Here's what is missing:
**Leimonos Monastery (Μονή Λειμώνος)**
Former URL: https://84.205.233.134/library/xeirografa_en.php
**Biblioteca Malatestiana**
Former URL: https://catalogoaperto.malatestiana.it/cgi-bin/wxis.exe/?IsisScript=Opcat/search2.xis
**Uppsala Universitetsbibliotek**
Former URL: https://www.ub.uu.se/samlingar/handskrifter/vasterlandska-medeltidshandskrifter/?languageId=1
Library:Stanford University Libraries
**Stanford Collections**
Former URL: https://collections.stanford.edu/images/bin/search/advanced/process?sort=title&clauseMapped(collectionBrowse)=Medieval+Manuscripts+and+Fragments&browse=1
**Castello del Buonconsiglio**
Former URL: https://www.trentinocultura.net/portal/server.pt/community/musical_manuscripts_%27400/814/sfoglia_codice/22660?Codice=Tr87
**Stiftsbibliothek Kremsmunster**
Former URL: https://schulen.eduhi.at/stift_kremsmuenster/vat/index.htm
**Biblioteca Nonantolana**
Former URL: https://www.bncrm.librari.beniculturali.it/index.php?it/175/biblioteca-nonantolana-virtuale
**Sapienza Digital Library**
Former URL: https://sapienzadigitallibrary.uniroma1.it/search/dl_cineca_solr/manoscritti?keys=manoscritti#?query=facet%3Dtrue%26facet.field%3Davailability_it%26facet.field%3DcollectionName%26facet.field%3DportalType_it%26facet.field%3DdescMetadata.name%26facet.field%3DdescMetadata.subject%26facet.field%3Ddate%26facet.field%3Dconcepts_it%26fq%3Davailability_it%253A*%26q%3Dmanoscritti%26rows%3D10%26facet.limit%3D50%26facet.mincount%3D1%26json.nl%3Dmap%26sort%3Dscore%2520desc%252CtitleSort%2520asc%26hl%3Dtrue%26hl.fl%3D*

## What happens now?

There is little the Sexy Codicology team can do. We try to find what is missing, but if we can't we have to remove the links from the DMMapp database, which is always a disappointment.

## What could have been done?

Whenever a digital collection moves or is removed for any reason the website's managers have to **make sure that a *301 redirect* is in place**. This could redirect to the new repository's website, or to a page explaining why the repository has been taken offline. This is essential not only for users, but also for search engines, that can then understand where the new website has gone and can the redirect users there. If this is not done, broken links are the result.
It is the institution's responsibility to make sure that their digitized heritage is always findable. **What is the point of digitizing everything if then everything gets lost with a click?**

## Other news

On the positive side of things, we noticed some problems with the permalinks that were coming from [Manuscripta Maedievalia](https://manuscripta-mediaevalia.de) (the offered permalinks were not encoded, and for some reasons some of them wouldn't work at all. Nevertheless, we found the correct way to add them to the list!). **We have fixed these and updated the list with new wonderful manuscripts coming from the same website.** We have also added Manuscripta Maedievalia's portal to the extra resources in the DMMapp. It's an incredible website that everyone should visit! We'll be working on adding the individual libraries to coming from this website to the database.
As always, all our data updates are visible on [GitHub](https://github.com/SexyCodicology/DMMapp/blob/master/js/data.json)!
