"""Checks for the per-library page generator in hooks/library_pages.py.

Run with ``pytest`` from the repository root. The hook is loaded by path
because ``hooks/`` is a MkDocs hook directory rather than an installed package.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _load_hook():
    spec = importlib.util.spec_from_file_location(
        "library_pages", REPO_ROOT / "hooks" / "library_pages.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


hook = _load_hook()

# A record built to be as hostile as the schema allows: markup in every text
# field, path traversal in the name, and links that are not http(s).
HOSTILE_RECORD = {
    "id": 9001,
    "library": '../../../etc/passwd <script>alert("xss")</script> & "quoted"',
    "city": '<img src=x onerror=alert(1)>Città',
    "nation": "Nation & Co </title>",
    "quantity": "Few",
    "copyright": '"><script>alert(2)</script>',
    "website": "javascript:alert(3)",
    "iiif": True,
    "is_free_cultural_works_license": True,
    "aggregators": [
        {"name": "<b>Project</b>", "url": "data:text/html,<script>alert(4)</script>"}
    ],
}


def _front_matter(markdown: str) -> dict:
    _, meta, _ = markdown.split("---", 2)
    return yaml.safe_load(meta)


@pytest.fixture(scope="module")
def records() -> list[dict]:
    return hook.load_records(str(DOCS_DIR))


@pytest.fixture(scope="module")
def pages(records) -> dict[str, str]:
    return hook.build_pages(records)


# ── Happy path ────────────────────────────────────────────────────────────


def test_one_page_per_record(records, pages):
    assert len(pages) == len(records)
    assert len(set(pages)) == len(records)
    assert all(uri.startswith(f"{hook.OUTPUT_DIR}/") for uri in pages)


def test_titles_and_descriptions_are_unique(pages):
    meta = [_front_matter(markdown) for markdown in pages.values()]
    titles = [entry["title"] for entry in meta]
    descriptions = [entry["description"] for entry in meta]

    assert len(set(titles)) == len(titles)
    assert len(set(descriptions)) == len(descriptions)
    assert all(title and description for title, description in zip(titles, descriptions))


def test_every_slug_is_url_safe(records):
    for record in records:
        slug = hook.slugify(record["library"], record["id"])
        assert SLUG_PATTERN.match(slug), slug
        assert slug.endswith(f"-{record['id']}")


# ── Malformed and hostile input ───────────────────────────────────────────


def test_hostile_library_name_produces_a_safe_slug():
    slug = hook.slugify(HOSTILE_RECORD["library"], HOSTILE_RECORD["id"])

    assert SLUG_PATTERN.match(slug), slug
    assert ".." not in slug
    assert "/" not in slug and "\\" not in slug
    assert slug.endswith("-9001")


def test_hostile_record_content_is_escaped():
    markdown = hook.build_pages([HOSTILE_RECORD])["libraries/id-9001.md"]
    body = markdown.split("---", 2)[2]

    # No dataset value opens a tag; the text survives as escaped entities.
    assert "<script" not in body
    assert "<img" not in body
    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;" in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body
    assert "&amp; &quot;quoted&quot;" in body


def test_hostile_record_front_matter_cannot_break_out():
    markdown = hook.build_pages([HOSTILE_RECORD])["libraries/id-9001.md"]
    meta = _front_matter(markdown)

    # MkDocs renders templates without autoescaping, so these two values reach
    # <title> and <meta content="..."> verbatim.
    for value in (meta["title"], meta["description"]):
        assert "<" not in value
        assert ">" not in value
        assert '"' not in value


def test_slug_is_never_empty_for_a_name_with_no_usable_characters():
    assert hook.slugify("→→→", 42) == "library-42"
    assert hook.slugify("中文图书馆", 7) == "library-7"


def test_accented_names_are_transliterated():
    assert hook.slugify("Universitätsbibliothek Köln", 12) == "universitatsbibliothek-koln-12"


# ── Trust boundary: outbound links ────────────────────────────────────────


@pytest.mark.parametrize(
    "value",
    [
        "javascript:alert(1)",
        "JavaScript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
        "file:///etc/passwd",
        "not a url at all",
        "",
        "   ",
        None,
        42,
    ],
)
def test_unsafe_urls_are_rejected(value):
    assert hook.safe_url(value) is None


@pytest.mark.parametrize(
    "value",
    ["https://example.org/manuscripts", "http://example.org", "HTTPS://Example.org/x?y=1"],
)
def test_safe_urls_are_kept(value):
    assert hook.safe_url(value) == value


def test_unsafe_links_do_not_become_clickable():
    markdown = hook.build_pages([HOSTILE_RECORD])["libraries/id-9001.md"]

    body = markdown.split("---", 2)[2]

    assert "javascript:" not in markdown
    assert "data:text/html" not in markdown
    assert "No collection URL is recorded" in body
    # The project is still named, but not linked.
    assert "&lt;b&gt;Project&lt;/b&gt;" in body
    # The report control does not depend on the unsafe collection URL.
    assert body.count("<a") == 1
    assert "btn-report-data-issue" in body


# ── Per-record data issue reports ─────────────────────────────────────────


def _report_data_issue_query(body: str) -> dict[str, list[str]]:
    """Return the decoded query values from a generated report control."""
    href = re.search(
        r'<a class="btn-visit btn-report-data-issue" href="([^"]+)"', body
    ).group(1)
    return parse_qs(urlsplit(unescape(href)).query)


def test_data_issue_form_has_the_prefilled_record_fields():
    form = yaml.safe_load(
        (REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "report-data-issue.yml").read_text(
            encoding="utf-8"
        )
    )
    fields = {field["id"]: field for field in form["body"]}

    assert form["labels"] == ["data/xml"]
    assert set(fields) >= {
        "record_id",
        "library_name",
        "page_url",
        "issue_type",
        "current_value",
        "correction",
        "evidence_url",
        "review_checklist",
    }
    assert "Match the record ID" in fields["review_checklist"]["attributes"]["value"]


def test_report_control_prefills_the_public_record_identity():
    record = {
        **HOSTILE_RECORD,
        "library": "Bodleian Library",
        "website": "https://example.org",
    }

    body = _page_body(record)
    query = _report_data_issue_query(body)

    assert "Report a data issue" in body
    assert query == {
        "template": ["report-data-issue.yml"],
        "record_id": ["9001"],
        "library_name": ["Bodleian Library"],
        "page_url": [
            "https://sexycodicology.github.io/"
            "Digitized-Medieval-Manuscripts-app/libraries/id-9001/"
        ],
    }


def test_report_control_preserves_a_zero_record_id():
    body = _page_body({**HOSTILE_RECORD, "id": 0})

    assert _report_data_issue_query(body)["record_id"] == ["0"]


def test_report_control_encodes_special_characters_in_a_library_name():
    record = {
        **HOSTILE_RECORD,
        "library": "Biblioth\u00e8que & #?= \u00c9tudes",
    }

    body = _page_body(record)
    query = _report_data_issue_query(body)

    assert "Biblioth%C3%A8que+%26+%23%3F%3D+%C3%89tudes" in body
    assert query["library_name"] == ["Biblioth\u00e8que & #?= \u00c9tudes"]


def test_report_control_keeps_hostile_values_inside_the_href_attribute():
    body = _page_body(HOSTILE_RECORD)
    control = re.search(
        r'<a class="btn-visit btn-report-data-issue"[^>]+>', body
    ).group(0)

    assert '<a class="btn-visit btn-report-data-issue"' in body
    assert "%3Cscript%3E" in control
    assert "&lt;" not in control
    assert " onclick=" not in control
    assert _report_data_issue_query(body)["record_id"] == ["9001"]


def test_report_control_survives_a_missing_collection_url():
    body = _page_body({**HOSTILE_RECORD, "website": None})
    query = _report_data_issue_query(body)

    assert "No collection URL is recorded" in body
    assert query["page_url"] == [
        "https://sexycodicology.github.io/"
        "Digitized-Medieval-Manuscripts-app/libraries/"
        "id-9001/"
    ]
    assert "None" not in body


def test_report_control_uses_no_client_side_script_or_handler():
    body = _page_body(HOSTILE_RECORD)
    control = re.search(
        r'<a class="btn-visit btn-report-data-issue"[^>]+>', body
    ).group(0)

    assert "<script" not in body
    assert " on" not in control


# ── Multiple memberships on a library page ────────────────────────────────


def _page_body(record: dict) -> str:
    markdown = hook.render_page(record, "Title", "Description")
    return markdown.split("---", 2)[2]


def test_access_point_title_is_secondary_and_escaped():
    body = _page_body({
        **HOSTILE_RECORD,
        "library": "Example Library",
        "access_point_title": '<script>alert("x")</script>',
    })

    assert "<h1>Example Library</h1>" in body
    assert "<dt>Access point</dt><dd>&lt;script&gt;" in body
    assert '<script>alert("x")</script>' not in body

    row = hook.render_row({
        **HOSTILE_RECORD,
        "library": "Example Library",
        "access_point_title": '<script>alert("x")</script>',
    })
    assert '<a class="library-name"' in row
    assert '<div class="library-access-point">&lt;script&gt;' in row
    assert '<script>alert("x")</script>' not in row


def test_alternate_names_are_visible_below_the_institution_and_escaped():
    record = {
        **HOSTILE_RECORD,
        "library": "Example Library",
        "access_point_title": "Example portal",
        "library_alternate_names": [
            {"name": "Example Libraries", "language": "en"},
            {"name": '<img src=x onerror=alert(1)> & Co'},
        ],
    }
    body = _page_body(record)
    row = hook.render_row(record)

    for rendered in (body, row):
        assert 'library-alternate-names' in rendered
        assert 'Also known as:' in rendered
        assert '<span lang="en">Example Libraries</span>' in rendered
        assert '&lt;img src=x onerror=alert(1)&gt; &amp; Co' in rendered
        assert '<img src=x onerror=alert(1)>' not in rendered
        assert rendered.count('Also known as:') == 1
    assert body.index('<h1>Example Library</h1>') < body.index('Also known as:')
    assert body.index('Also known as:') < body.index('library-page__location')
    assert row.index('Also known as:') < row.index('Example portal')


def test_absent_or_unusable_alternate_names_add_no_label():
    for entries in (None, [], [{}], [{"name": "  "}]):
        record = {**HOSTILE_RECORD, "library_alternate_names": entries}
        assert 'Also known as:' not in _page_body(record)
        assert 'Also known as:' not in hook.render_row(record)


def test_unusable_language_tag_is_not_added_to_markup():
    record = {
        **HOSTILE_RECORD,
        "library_alternate_names": [
            {"name": "Example Library", "language": 'en" onclick="bad()'},
        ],
    }

    assert '<span>Example Library</span>' in _page_body(record)
    assert 'onclick=' not in _page_body(record)


def test_the_part_of_row_lists_every_membership():
    body = _page_body({**HOSTILE_RECORD, "aggregators": [
        {"name": "Polonsky", "url": "https://polonsky.example.org"},
        {"name": "Biblissima", "url": "https://biblissima.example.org"},
    ]})

    assert "<dt>Part of</dt>" in body
    assert body.count("<dt>Part of</dt>") == 1, "one row, not one row per membership"
    assert "Polonsky" in body
    assert "Biblissima" in body
    assert 'href="https://polonsky.example.org"' in body
    assert 'href="https://biblissima.example.org"' in body


def test_no_part_of_row_without_a_membership():
    body = _page_body({**HOSTILE_RECORD, "aggregators": []})

    assert "Part of" not in body


def test_an_unlinkable_membership_is_still_named_alongside_a_linked_one():
    body = _page_body({**HOSTILE_RECORD, "aggregators": [
        {"name": "Unsafe", "url": "javascript:alert(1)"},
        {"name": "Biblissima", "url": "https://biblissima.example.org"},
    ]})

    assert "javascript:" not in body
    assert "Unsafe" in body
    assert 'href="https://biblissima.example.org"' in body


# ── Optional external identifiers on a library page ───────────────────────


def test_external_identifier_rows_render_with_their_canonical_links():
    body = _page_body({
        **HOSTILE_RECORD,
        "isil": "GB-OxBodl",
        "wikidata_qid": "Q1131283",
        "geonames_id": 2640729,
    })

    assert "<dt>ISIL</dt><dd>GB-OxBodl</dd>" in body
    assert "<dt>Wikidata</dt>" in body
    assert 'href="https://www.wikidata.org/wiki/Q1131283"' in body
    assert "<dt>GeoNames</dt>" in body
    assert 'href="https://www.geonames.org/2640729"' in body
    assert body.count('rel="noopener noreferrer" target="_blank"') >= 2


def test_external_identifier_rows_are_omitted_when_fields_are_absent():
    body = _page_body(HOSTILE_RECORD)

    assert "<dt>ISIL</dt>" not in body
    assert "<dt>Wikidata</dt>" not in body
    assert "<dt>GeoNames</dt>" not in body
    assert "undefined" not in body
    assert ">None<" not in body


# ── conservative DCAT JSON-LD front matter ───────────────────────────────


def _structured_data(record: dict) -> dict:
    markdown = hook.render_page(record, "Title", "Description")
    return _front_matter(markdown)["structured_data"]


def _structured_nodes(data: dict) -> dict[str, dict]:
    return {node["@id"]: node for node in data["@graph"]}


def test_structured_data_separates_the_record_from_its_access_point():
    data = _structured_data({
        "id": 12,
        "library": "Bare Library",
        "city": "Somewhere",
        "nation": "Nowhere",
    })

    assert data["@context"] == hook.linked_data.CONTEXT
    page = (
        "https://sexycodicology.github.io/"
        "Digitized-Medieval-Manuscripts-app/libraries/id-12/"
    )
    nodes = _structured_nodes(data)
    record = nodes[page + "#record"]
    access_point = nodes[page + "#access-point"]

    assert record["@type"] == "dcat:CatalogRecord"
    assert record["dcterms:identifier"] == "12"
    assert record["foaf:primaryTopic"] == {"@id": access_point["@id"]}
    assert access_point["@type"] == "dcat:Resource"
    assert access_point["dcterms:title"] == "Bare Library"


def test_structured_data_uses_website_as_the_access_point_landing_page():
    data = _structured_data({
        **HOSTILE_RECORD, "library": "Example Library",
        "website": "https://example.org/manuscripts",
    })
    access_point = next(
        node for node in data["@graph"] if node["@type"] == "dcat:Resource"
    )

    assert access_point["dcat:landingPage"] == {
        "@id": "https://example.org/manuscripts"
    }


def test_structured_data_drops_an_unsafe_website():
    data = _structured_data({**HOSTILE_RECORD, "website": "javascript:alert(1)"})
    access_point = next(
        node for node in data["@graph"] if node["@type"] == "dcat:Resource"
    )

    assert "dcat:landingPage" not in access_point


def test_structured_data_omits_unreviewed_authority_values():
    data = _structured_data({
        **HOSTILE_RECORD,
        "wikidata_qid": "Q1131283",
        "geonames_id": 2640729,
        "isil": "GB-OxBodl",
    })

    serialized = json.dumps(data)
    assert "Q1131283" not in serialized
    assert "2640729" not in serialized
    assert "GB-OxBodl" not in serialized
    assert "sameAs" not in serialized


def test_structured_data_id_matches_the_report_data_issue_page_url():
    record = {**HOSTILE_RECORD, "library": "Bodleian Library"}

    data = _structured_data(record)
    query = _report_data_issue_query(_page_body(record))

    page = query["page_url"][0]
    assert page.endswith("/libraries/id-9001/")
    assert {node["@id"] for node in data["@graph"]} == {
        page + "#record",
        page + "#access-point",
    }


def test_rights_row_shows_verbatim_and_normalised_category():
    body = _page_body({
        **HOSTILE_RECORD,
        "copyright": "Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)",
        "licence_category": "CC-BY-NC",
    })

    assert "Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)" in body
    assert 'class="badge badge--standard">Licence category: CC-BY-NC</span>' in body


# ── IIIF viewer action on a library page ──────────────────────────────────


def test_iiif_collection_endpoint_renders_a_distinct_viewer_action():
    collection = "https://example.org/iiif/collection.json?locale=en"
    body = _page_body({
        **HOSTILE_RECORD,
        "website": "https://example.org/collection",
        "iiif_collection_url": collection,
    })

    action = re.search(
        r'<a class="btn-visit btn-iiif-viewer btn-iiif-collection"\s+href="([^"]+)"',
        body,
    )

    assert action is not None
    assert "Browse digitised manuscripts" in body
    assert body.index("Browse digitised manuscripts") < body.index("Browse IIIF collection")
    viewer_url = urlsplit(unescape(action.group(1)))
    assert viewer_url.scheme == "https"
    assert viewer_url.netloc == "www.universalviewer.dev"
    assert viewer_url.path == "/uv.html"
    assert viewer_url.query == ""
    assert viewer_url.fragment.startswith("?")
    assert parse_qs(viewer_url.fragment[1:]) == {"manifest": [collection]}


def test_named_example_manifest_renders_a_distinct_viewer_action():
    manifest = "https://example.org/iiif/manifest.json?item=12&locale=en"
    body = _page_body({
        **HOSTILE_RECORD,
        "website": "https://example.org/collection",
        "iiif_example_manifest_url": manifest,
        "iiif_example_manifest_label": "Example manuscript",
    })

    action = re.search(
        r'<a class="btn-visit btn-iiif-viewer btn-iiif-example"\s+href="([^"]+)"',
        body,
    )

    assert action is not None
    assert "Open example manuscript in IIIF: Example manuscript" in body
    viewer_url = urlsplit(unescape(action.group(1)))
    assert viewer_url.scheme == "https"
    assert viewer_url.netloc == "www.universalviewer.dev"
    assert viewer_url.path == "/uv.html"
    assert viewer_url.query == ""
    assert viewer_url.fragment.startswith("?")
    assert parse_qs(viewer_url.fragment[1:]) == {"manifest": [manifest]}


def test_iiif_collection_action_precedes_a_named_example_manifest():
    body = _page_body({
        **HOSTILE_RECORD,
        "website": "https://example.org/collection",
        "iiif_collection_url": "https://example.org/iiif/collection.json",
        "iiif_example_manifest_url": "https://example.org/iiif/manifest.json",
        "iiif_example_manifest_label": "Example manuscript",
    })

    assert body.index("Browse digitised manuscripts") < body.index("Browse IIIF collection")
    assert body.index("Browse IIIF collection") < body.index(
        "Open example manuscript in IIIF: Example manuscript"
    )


def test_iiif_viewer_actions_are_absent_without_an_endpoint():
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org/collection"})

    assert "Browse IIIF collection" not in body
    assert "Open example manuscript in IIIF" not in body
    assert "btn-iiif-viewer" not in body


def test_unsafe_or_unnamed_iiif_endpoints_do_not_render_viewer_actions():
    body = _page_body({
        **HOSTILE_RECORD,
        "website": "https://example.org/collection",
        "iiif_collection_url": "javascript:alert(1)",
        "iiif_example_manifest_url": "javascript:alert(2)",
        "iiif_example_manifest_label": "Example manuscript",
    })

    assert "Browse IIIF collection" not in body
    assert "Open example manuscript in IIIF" not in body
    assert "javascript:" not in body

    unnamed_example = _page_body({
        **HOSTILE_RECORD,
        "iiif_example_manifest_url": "https://example.org/iiif/manifest.json",
    })

    assert "Open example manuscript in IIIF" not in unnamed_example


# ── Collisions ────────────────────────────────────────────────────────────


def test_identical_library_names_get_distinct_slugs_and_titles():
    twins = [
        {**HOSTILE_RECORD, "id": 1, "library": "Stadtbibliothek", "city": "Trier",
         "nation": "Germany", "website": "https://a.example.org", "aggregators": []},
        {**HOSTILE_RECORD, "id": 2, "library": "Stadtbibliothek", "city": "Trier",
         "nation": "Germany", "website": "https://b.example.org", "aggregators": []},
    ]
    pages = hook.build_pages(twins)

    assert set(pages) == {"libraries/id-1.md", "libraries/id-2.md"}

    titles = [_front_matter(markdown)["title"] for markdown in pages.values()]
    assert len(set(titles)) == 2
    assert all("Stadtbibliothek — Trier, Germany" in title for title in titles)


def test_records_differing_only_by_id_still_get_unique_metadata():
    clones = [
        {**HOSTILE_RECORD, "id": index, "library": "Same", "city": "Same", "nation": "Same",
         "website": "https://same.example.org", "aggregators": []}
        for index in (1, 2, 3)
    ]
    meta = [_front_matter(markdown) for markdown in hook.build_pages(clones).values()]

    assert len({entry["title"] for entry in meta}) == 3
    assert len({entry["description"] for entry in meta}) == 3


def test_alias_registry_preserves_current_slugs_and_accepts_earlier_names(records):
    registry = hook.load_alias_registry(str(DOCS_DIR))

    assert len(registry) == len(records)
    assert all(hook.slug_for(record) in registry[str(record["id"])] for record in records)

    renamed = {**records[0], "library": "A corrected institutional name"}
    with pytest.raises(hook.PluginError, match="missing its current slug"):
        hook.build_alias_pages([renamed], "https://example.org/", {
            str(renamed["id"]): [hook.slug_for(records[0])]
        })

    pages = hook.build_alias_pages([renamed], "https://example.org/", {
        str(renamed["id"]): [hook.slug_for(records[0]), hook.slug_for(renamed)]
    })
    assert len(pages) == 2
    assert all(f"../id-{renamed['id']}/" in page for page in pages.values())


def test_alias_collision_and_retired_id_are_handled_explicitly():
    record = {**HOSTILE_RECORD, "id": 2, "library": "Example"}
    with pytest.raises(hook.PluginError, match="collides"):
        hook.build_alias_pages([record], "https://example.org/", {
            "1": [hook.slug_for(record)],
            "2": [hook.slug_for(record)],
        })

    retired = hook.render_retired_page("1")
    assert "Retired directory record 1" in retired
    assert "dmm_record_id: 1" in retired
    assert "no longer lists this access point" in retired


# ── External dependency failure ───────────────────────────────────────────


@pytest.mark.parametrize(
    "content",
    [
        "{ not json",
        '{"records": []}',
        "[{}]",
        '[{"id": "12", "library": "L", "city": "C", "nation": "N"}]',
        '[{"id": true, "library": "L", "city": "C", "nation": "N"}]',
        '[{"library": "L", "city": "C", "nation": "N"}]',
        '[{"id": 1, "library": "   ", "city": "C", "nation": "N"}]',
        "[1, 2, 3]",
    ],
)
def test_a_broken_dataset_fails_the_build(tmp_path, content):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "data.json").write_text(content, encoding="utf-8")

    with pytest.raises(hook.PluginError):
        hook.load_records(str(tmp_path))


def test_a_record_with_id_zero_is_accepted(tmp_path):
    """0 is a legal integer id, so it must not be read as a missing field."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "data.json").write_text(
        '[{"id": 0, "library": "Zeroth Library", "city": "C", "nation": "N"}]',
        encoding="utf-8",
    )

    records = hook.load_records(str(tmp_path))

    assert hook.slug_for(records[0]) == "zeroth-library-0"


def test_a_missing_dataset_fails_the_build(tmp_path):
    with pytest.raises(hook.PluginError):
        hook.load_records(str(tmp_path))


# ── Regression guard: the rest of the site is untouched ───────────────────


def test_nav_lists_the_library_index_but_not_generated_library_pages():
    config = yaml.safe_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))

    assert config["hooks"] == ["hooks/library_pages.py", "hooks/linked_data.py"]
    assert hook.OUTPUT_DIR not in yaml.safe_dump(config["nav"])
    assert {"Library Index": hook.LIBRARY_INDEX_URI} in config["nav"]
    assert len(config["nav"]) == 7


# ── End-to-end build ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def built_site(tmp_path_factory) -> Path:
    """Build a miniature site through real MkDocs, hostile record included."""
    project = tmp_path_factory.mktemp("site")
    docs = project / "docs"
    (docs / "assets").mkdir(parents=True)

    dataset = [
        {
            "id": 1,
            "library": "Bodleian Library",
            "city": "Oxford",
            "nation": "United Kingdom",
            "quantity": "Thousands",
            "copyright": "Public Domain",
            "website": "https://digital.bodleian.ox.ac.uk",
            "iiif": True,
            "is_free_cultural_works_license": True,
            "aggregators": [],
        },
        HOSTILE_RECORD,
    ]
    (docs / "assets" / "data.json").write_text(json.dumps(dataset), encoding="utf-8")
    (docs / "assets" / "library-aliases.json").write_text(
        json.dumps({
            "1": ["bodleian-library-1"],
            "9001": ["etc-passwd-script-alert-xss-script-quoted-9001"],
        }),
        encoding="utf-8",
    )
    (docs / "index.md").write_text("# Directory\n", encoding="utf-8")
    (project / "mkdocs.yml").write_text(
        "site_name: Test\n"
        "site_url: https://example.org/\n"
        "docs_dir: docs\n"
        "theme:\n  name: material\n"
        f"  custom_dir: {(REPO_ROOT / 'overrides').as_posix()}\n"
        "nav:\n  - Home: index.md\n  - Library index: library-index.md\n"
        "hooks:\n"
        f"  - {(REPO_ROOT / 'hooks' / 'library_pages.py').as_posix()}\n"
        f"  - {(REPO_ROOT / 'hooks' / 'linked_data.py').as_posix()}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--clean", "--strict"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return project / "site"


def test_build_emits_id_pages_and_legacy_aliases(built_site):
    assert sorted(path.name for path in (built_site / "libraries").iterdir()) == [
        "bodleian-library-1",
        "etc-passwd-script-alert-xss-script-quoted-9001",
        "id-1",
        "id-9001",
    ]


def test_generated_pages_reach_the_sitemap(built_site):
    sitemap = (built_site / "sitemap.xml").read_text(encoding="utf-8")

    assert "https://example.org/libraries/id-1/" in sitemap
    assert "https://example.org/libraries/id-9001/" in sitemap


def test_library_index_lists_every_record_and_reaches_the_sitemap(built_site):
    index = (built_site / "library-index" / "index.html").read_text(encoding="utf-8")
    sitemap = (built_site / "sitemap.xml").read_text(encoding="utf-8")

    hrefs = re.findall(r'<li><a href="([^\"]+)">', index)

    assert hrefs == [
        "../libraries/id-1/",
        "../libraries/id-9001/",
    ]
    assert [
        urljoin("https://example.org/DMMapp/library-index/", href) for href in hrefs
    ] == [
        "https://example.org/DMMapp/libraries/id-1/",
        "https://example.org/DMMapp/libraries/id-9001/",
    ]
    assert "https://example.org/library-index/" in sitemap


def test_library_index_groups_accented_and_non_alphabetic_names():
    accented_name = chr(0x00C5) + "ngstr" + chr(0x00F6) + "m Library"
    records = [
        {"id": 1, "library": accented_name, "city": "City", "nation": "Nation"},
        {"id": 2, "library": "7 Hills Library", "city": "City", "nation": "Nation"},
        {
            "id": 3,
            "library": chr(0x4E2D) + chr(0x6587),
            "city": "City",
            "nation": "Nation",
        },
    ]

    index = hook.build_library_index(records)

    assert "## A" in index
    assert "## Other" in index
    assert index.index(accented_name) < index.index("7 Hills Library")
    assert index.count("<li>") == len(records)


def test_homepage_library_index_link_uses_the_button_style():
    template = (REPO_ROOT / "overrides" / "home.html").read_text(encoding="utf-8")
    stylesheet = (REPO_ROOT / "docs" / "assets" / "dashboard.css").read_text(
        encoding="utf-8"
    )

    assert 'class="hero__actions"' in template
    assert 'class="btn-visit hero__index-link"' in template
    assert 'class="bi bi-list-ol"' in template
    assert "Browse every library alphabetically" in template
    assert ".hero__actions .hero__index-link:hover" in stylesheet


def test_built_pages_carry_unique_seo_metadata(built_site):
    titles, descriptions = set(), set()
    for page in (built_site / "libraries").glob("id-*/index.html"):
        html = page.read_text(encoding="utf-8")
        titles.add(re.search(r"<title>(.*?)</title>", html, re.S).group(1))
        descriptions.add(
            re.search(r'<meta name="description" content="(.*?)">', html, re.S).group(1)
        )

    assert len(titles) == 2
    assert len(descriptions) == 2


def test_hostile_record_injects_nothing_into_the_built_page(built_site):
    html = (
        built_site / "libraries" / "id-9001" / "index.html"
    ).read_text(encoding="utf-8")

    # MkDocs renders templates without autoescaping, so the two front-matter
    # values must already be inert by the time they reach the <head>.
    title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
    description = re.search(r'<meta name="description" content="(.*?)">', html, re.S).group(1)
    for value in (title, description):
        assert "<" not in value and ">" not in value and '"' not in value

    # Nothing from the dataset became markup in the page content either.
    article = html.split("<article", 1)[1].split("</article>", 1)[0]
    assert "<script" not in article
    assert "<img" not in article
    assert "javascript:" not in html
    assert "data:text/html" not in html


# ── conservative DCAT JSON-LD in the built page ──────────────────────────


@pytest.fixture(scope="module")
def built_site_with_overrides(tmp_path_factory) -> Path:
    """Build a miniature site through real MkDocs, using the real overrides.

    ``built_site`` above uses the stock Material theme, which never loads
    ``overrides/main.html`` and so never renders the JSON-LD block that lives
    there. This fixture uses ``custom_dir`` like the production build does,
    so the structured-data output is checked end to end.
    """
    project = tmp_path_factory.mktemp("site-overrides")
    docs = project / "docs"
    (docs / "assets").mkdir(parents=True)

    dataset = [
        {
            "id": 1,
            "library": "Bodleian Library",
            "city": "Oxford",
            "nation": "United Kingdom",
            "quantity": "Thousands",
            "copyright": "Public Domain",
            "website": "https://digital.bodleian.ox.ac.uk",
            "iiif": True,
            "is_free_cultural_works_license": True,
            "aggregators": [],
            "isil": "GB-OxBodl",
            "wikidata_qid": "Q1131283",
            "geonames_id": 2640729,
        },
        HOSTILE_RECORD,
    ]
    (docs / "assets" / "data.json").write_text(json.dumps(dataset), encoding="utf-8")
    (docs / "assets" / "library-aliases.json").write_text(
        json.dumps({
            "1": ["bodleian-library-1"],
            "9001": ["etc-passwd-script-alert-xss-script-quoted-9001"],
        }),
        encoding="utf-8",
    )
    (docs / "index.md").write_text("# Directory\n", encoding="utf-8")
    (project / "mkdocs.yml").write_text(
        "site_name: Test\n"
        "site_url: https://example.org/\n"
        "docs_dir: docs\n"
        f"theme:\n  name: material\n  custom_dir: {(REPO_ROOT / 'overrides').as_posix()}\n"
        "nav:\n  - Home: index.md\n  - Library index: library-index.md\n"
        f"hooks:\n  - {(REPO_ROOT / 'hooks' / 'library_pages.py').as_posix()}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--clean"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return project / "site"


def _ld_json_blocks(html: str) -> list[dict]:
    return [
        json.loads(match)
        for match in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S
        )
    ]


def test_the_built_library_page_ships_conservative_dcat_jsonld(
    built_site_with_overrides,
):
    html = (
        built_site_with_overrides / "libraries" / "id-1" / "index.html"
    ).read_text(encoding="utf-8")

    blocks = _ld_json_blocks(html)
    documents = [block for block in blocks if "@graph" in block]
    assert len(documents) == 1

    data = documents[0]
    nodes = _structured_nodes(data)
    page = hook.SITE_URL + "libraries/id-1/"
    assert nodes[page + "#record"]["@type"] == "dcat:CatalogRecord"
    assert nodes[page + "#access-point"]["dcat:landingPage"] == {
        "@id": "https://digital.bodleian.ox.ac.uk"
    }
    serialized = json.dumps(data)
    assert "Q1131283" not in serialized
    assert "GB-OxBodl" not in serialized
    assert "2640729" not in serialized
    assert "sameAs" not in serialized


def test_the_hostile_records_jsonld_stays_valid_json_and_inert(built_site_with_overrides):
    html = (
        built_site_with_overrides
        / "libraries"
        / "id-9001"
        / "index.html"
    ).read_text(encoding="utf-8")

    # json.loads succeeding on every block proves none of them was broken out
    # of by the hostile library name (which contains a literal "</script>").
    raw_blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    )
    assert raw_blocks
    for raw in raw_blocks:
        assert "<script" not in raw.lower()

    documents = [block for block in _ld_json_blocks(html) if "@graph" in block]
    assert len(documents) == 1
    titles = [
        node["dcterms:title"]
        for node in documents[0]["@graph"]
        if "dcterms:title" in node
    ]
    assert any("script" in title for title in titles)


def test_the_slug_map_matches_the_generated_pages(built_site):
    slugs = json.loads((built_site / "assets" / "library-slugs.json").read_text(encoding="utf-8"))

    assert slugs == {
        "1": "bodleian-library-1",
        "9001": "etc-passwd-script-alert-xss-script-quoted-9001",
    }
    for slug in slugs.values():
        assert (built_site / "libraries" / slug / "index.html").is_file()


def test_stable_pages_offer_rdf_and_aliases_resolve_to_them(built_site):
    stable = (built_site / "libraries" / "id-1" / "index.html").read_text(encoding="utf-8")
    alias = (built_site / "libraries" / "bodleian-library-1" / "index.html").read_text(
        encoding="utf-8"
    )

    assert 'rel="canonical" href="https://example.org/libraries/id-1/"' in stable
    assert 'rel="alternate" type="application/ld+json"' in stable
    assert 'https://example.org/linked-data/records/1.jsonld' in stable
    assert 'rel="canonical" href="https://example.org/libraries/id-1/"' in alias
    assert 'http-equiv="refresh" content="0; url=https://example.org/libraries/id-1/"' in alias
    assert (built_site / "linked-data" / "records" / "1.jsonld").is_file()
    assert (built_site / "assets" / "dmmapp-linked-data.jsonld").is_file()


# ── Broken-link status on a generated page ────────────────────────────────


def test_a_broken_link_page_carries_a_dated_notice():
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org",
                       "is_disabled": True, "last_checked": "2026-08-02"})

    assert 'class="library-page__broken"' in body
    assert "confirmed broken on 2026-08-02" in body
    assert 'class="badge badge--broken"' in body
    # The link stays reachable but is never offered as a working collection.
    assert "Browse digitised manuscripts" not in body
    assert "Try the collection anyway" in body
    assert "btn-visit--broken" in body
    assert "btn-visit--primary" not in body
    assert body.index('class="library-page__broken"') < body.index("Try the collection anyway")


def test_a_broken_page_without_a_date_still_warns():
    """Validation forbids this combination, but the page must not print
    "confirmed broken on " with a dangling date if bad data reaches it."""
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org",
                       "is_disabled": True})

    assert "confirmed broken." in body
    assert "broken on" not in body


def test_a_page_without_the_field_has_no_notice():
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org"})

    assert "library-page__broken" not in body
    assert "Browse digitised manuscripts" in body
    assert "broken" not in body.lower()


def test_collection_button_uses_the_record_url_above_the_facts():
    website = 'https://example.org/manuscripts?name="old"&view=grid'
    body = _page_body({
        **HOSTILE_RECORD,
        "library": "Example Library",
        "city": "Oxford",
        "nation": "United Kingdom",
        "website": website,
        "iiif_collection_url": "https://example.org/iiif/collection.json",
    })

    button = (
        '<a class="btn-visit btn-visit--primary" '
        'href="https://example.org/manuscripts?name=&quot;old&quot;&amp;view=grid"'
    )
    assert button in body
    assert body.count("Browse digitised manuscripts") == 1
    assert body.index("<h1>Example Library</h1>") < body.index("Oxford, United Kingdom")
    assert body.index("Oxford, United Kingdom") < body.index(button)
    assert body.index(button) < body.index('class="library-page__facts"')
    assert body.index(button) < body.index("Browse IIIF collection")
    assert body.index(button) < body.index("Report a data issue")
    assert 'href="' + website + '"' not in body


def test_unusable_collection_url_has_plain_fallback_before_facts():
    body = _page_body(HOSTILE_RECORD)

    assert "No collection URL is recorded for this library." in body
    assert body.index("No collection URL is recorded") < body.index(
        'class="library-page__facts"'
    )
    assert "Browse digitised manuscripts" not in body
    assert 'class="btn-visit btn-visit--primary"' not in body


def test_a_working_link_page_carries_a_dated_confirmation():
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org",
                       "last_checked": "2026-08-02"})

    assert 'class="library-page__checked"' in body
    assert "last confirmed working on 2026-08-02" in body
    assert "library-page__broken" not in body


def test_a_hostile_last_checked_is_escaped_on_the_page():
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org",
                       "is_disabled": True,
                       "last_checked": '<img src=x onerror=alert(1)>'})

    assert "<img" not in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body


def test_a_hostile_working_last_checked_is_escaped_on_the_page():
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org",
                       "last_checked": '<img src=x onerror=alert(1)>'})

    assert "<img" not in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body


def test_a_broken_record_with_no_usable_website_says_so():
    body = _page_body({**HOSTILE_RECORD, "is_disabled": True,
                       "last_checked": "2026-08-02"})

    assert "No collection URL is recorded" in body
    assert "javascript:" not in body
    # The warning is still shown; the missing URL is a separate fact.
    assert 'class="library-page__broken"' in body
