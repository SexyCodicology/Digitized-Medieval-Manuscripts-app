# Insular Scripts: image sources and reuse

These three images illustrate `docs/codicology/medieval-scripts/insular-scripts.md`.
Source identities and rights statements were checked on 30 October 2026.
The catalogue's collection-level rights fields are not used as permission for
individual images. No catalogue records were changed.

## Sources and rights

### Life of Columba, Gen. 1, p. 4, detail

- Asset: `docs/codicology/medieval-scripts/assets/2026/10/insular-columba-gen1-p4-detail.webp`.
- Holding institution: Stadtbibliothek, Schaffhausen; DMMapp record 442.
- Source and rights evidence: University of Zurich,
  [Ad fontes, “Insular Scripts”](https://www.adfontes.uzh.ch/en/tutorium/schriften-lesen/schriftgeschichte/unziale-und-halbunziale).
  Its image caption identifies the manuscript, page, e-codices source, and
  public-domain CC0 1.0 status.
- [Downloaded image](https://www.adfontes.uzh.ch/media/files/2_Tutorium/Insular%20Scripts/Vita%20Columbae_Insular%20Scripts%201.png).
- Rights: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
- Credit retained in the article: e-codices, via Ad fontes, with the holding
  institution, shelfmark, and page.
- The source is already a detail. No additional cropping or retouching was
  applied. Converted from PNG to WebP at the supplied dimensions, 904 × 412.

### Book of Durrow, MS 57, fol. 86r

- Asset: `docs/codicology/medieval-scripts/assets/2026/10/insular-durrow-ms57-f86r.webp`.
- Holding institution: Trinity College Dublin; DMMapp record 332 (Digital
  Collections, rather than the separate ISOS record).
- Source and item-level rights evidence:
  [Trinity's image on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:IE_TCD_MS_57_f.86r.jpg).
  The page credits Trinity College Dublin Library, Digital Collections
  Department, identifies fol. 86r, links the library's
  [manuscript record](https://doi.org/10.48495/wm117t53k), and specifies CC BY 4.0.
  The embedded usage terms name The Board of Trinity College Dublin as the
  required credit.
- [Downloaded 1280-pixel preview](https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c8/IE_TCD_MS_57_f.86r.jpg/1280px-IE_TCD_MS_57_f.86r.jpg).
- Rights: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Credit retained in the article: © The Board of Trinity College Dublin,
  Digital Collections Department; linked source and licence; modification notice.
- Corroborating policy: Trinity's
  [Policy on Open Licensing of the Library's Digitised Content](https://www.tcd.ie/media/tcd/about/policies/pdfs/open-licensing-library-digitised-content-policy.pdf),
  issued 4 June 2025, sections 6–7. The specific image licence is the basis for
  this reuse; the general policy does not establish permissions for other items.
- Resized from 1280 × 1756 to 840 × 1152 and converted to WebP. No cropping or
  retouching was applied.

### Lindisfarne Gospels, Cotton MS Nero D IV, fol. 5r, detail

- Asset: `docs/codicology/medieval-scripts/assets/2026/10/insular-lindisfarne-f5r-gloss-detail.webp`.
- Holding institution: British Library; DMMapp record 49.
- Source and item-level rights evidence:
  [“Column of preface from Lindisfarne Gospels.png” on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Column_of_preface_from_Lindisfarne_Gospels.png).
  Its source field identifies the British Library scan and fol. 5r; its
  description identifies the Latin text and Aldred's Old English interlineations.
  Its licensing section marks the reproduction as public domain, including
  public-domain status in the source country and the United States.
- [Downloaded 960-pixel preview](https://thumb.wikimedia.org/wikipedia/commons/thumb/0/09/Column_of_preface_from_Lindisfarne_Gospels.png/960px-Column_of_preface_from_Lindisfarne_Gospels.png).
  The original-file endpoint returned HTTP 429; the cached preview was retrieved
  after the retry interval. The preview is 960 × 1015; the file record describes
  an 866 × 916 original. The final derivative is smaller than either.
- Rights statement: [Public Domain Mark 1.0](https://creativecommons.org/publicdomain/mark/1.0/).
  This is a public-domain identification, not a CC0 licence.
- Credit retained in the article: British Library, via Wikimedia Commons, with
  shelfmark, folio, linked source and public-domain statement, and modification
  notice.
- The source is already a detail. Resized to 800 × 846 and converted to WebP;
  no additional cropping or retouching was applied.

## Optimisation

Pillow encodes the RGB derivatives as WebP with `method=6`. Quality is 72 for
the two text details and 64 for the Durrow opening. Resizing uses Lanczos.
EXIF and other source metadata are not copied into the derivatives; the credits
and rights are preserved above and in the article captions.

| Asset | Dimensions | Bytes |
| --- | --- | ---: |
| Columba detail | 904 × 412 | 29,988 |
| Durrow opening | 840 × 1152 | 154,248 |
| Lindisfarne gloss detail | 800 × 846 | 70,434 |
| **Total** | | **254,670** |

The total is approximately 249 KiB. Images are served locally, load lazily,
request asynchronous decoding, and declare their dimensions to reserve layout
space. Full-resolution source files and unused candidates are not added to the
repository. Captions link to the sources for closer inspection.
