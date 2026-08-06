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
from pathlib import Path

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
    markdown = hook.build_pages([HOSTILE_RECORD])["libraries/etc-passwd-script-alert-xss-script-quoted-9001.md"]
    body = markdown.split("---", 2)[2]

    # No dataset value opens a tag; the text survives as escaped entities.
    assert "<script" not in body
    assert "<img" not in body
    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;" in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body
    assert "&amp; &quot;quoted&quot;" in body


def test_hostile_record_front_matter_cannot_break_out():
    markdown = hook.build_pages([HOSTILE_RECORD])["libraries/etc-passwd-script-alert-xss-script-quoted-9001.md"]
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
    markdown = hook.build_pages([HOSTILE_RECORD])["libraries/etc-passwd-script-alert-xss-script-quoted-9001.md"]

    body = markdown.split("---", 2)[2]

    assert "javascript:" not in markdown
    assert "data:text/html" not in markdown
    assert "No collection URL is recorded" in body
    # The project is still named, but not linked.
    assert "&lt;b&gt;Project&lt;/b&gt;" in body
    assert "<a" not in body


# ── Multiple memberships on a library page ────────────────────────────────


def _page_body(record: dict) -> str:
    markdown = hook.render_page(record, "Title", "Description")
    return markdown.split("---", 2)[2]


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


# ── Collisions ────────────────────────────────────────────────────────────


def test_identical_library_names_get_distinct_slugs_and_titles():
    twins = [
        {**HOSTILE_RECORD, "id": 1, "library": "Stadtbibliothek", "city": "Trier",
         "nation": "Germany", "website": "https://a.example.org", "aggregators": []},
        {**HOSTILE_RECORD, "id": 2, "library": "Stadtbibliothek", "city": "Trier",
         "nation": "Germany", "website": "https://b.example.org", "aggregators": []},
    ]
    pages = hook.build_pages(twins)

    assert set(pages) == {"libraries/stadtbibliothek-1.md", "libraries/stadtbibliothek-2.md"}

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


def test_nav_does_not_list_the_generated_pages():
    config = yaml.safe_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))

    assert config["hooks"] == ["hooks/library_pages.py"]
    assert hook.OUTPUT_DIR not in yaml.safe_dump(config["nav"])
    assert len(config["nav"]) == 4


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
    (docs / "index.md").write_text("# Directory\n", encoding="utf-8")
    (project / "mkdocs.yml").write_text(
        "site_name: Test\n"
        "site_url: https://example.org/\n"
        "docs_dir: docs\n"
        "theme:\n  name: material\n"
        "nav:\n  - Home: index.md\n"
        f"hooks:\n  - {(REPO_ROOT / 'hooks' / 'library_pages.py').as_posix()}\n",
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


def test_build_emits_one_page_per_record(built_site):
    assert sorted(path.name for path in (built_site / "libraries").iterdir()) == [
        "bodleian-library-1",
        "etc-passwd-script-alert-xss-script-quoted-9001",
    ]


def test_generated_pages_reach_the_sitemap(built_site):
    sitemap = (built_site / "sitemap.xml").read_text(encoding="utf-8")

    assert "https://example.org/libraries/bodleian-library-1/" in sitemap
    assert "https://example.org/libraries/etc-passwd-script-alert-xss-script-quoted-9001/" in sitemap


def test_built_pages_carry_unique_seo_metadata(built_site):
    titles, descriptions = set(), set()
    for page in (built_site / "libraries").glob("*/index.html"):
        html = page.read_text(encoding="utf-8")
        titles.add(re.search(r"<title>(.*?)</title>", html, re.S).group(1))
        descriptions.add(
            re.search(r'<meta name="description" content="(.*?)">', html, re.S).group(1)
        )

    assert len(titles) == 2
    assert len(descriptions) == 2


def test_hostile_record_injects_nothing_into_the_built_page(built_site):
    html = (
        built_site / "libraries" / "etc-passwd-script-alert-xss-script-quoted-9001" / "index.html"
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


def test_the_slug_map_matches_the_generated_pages(built_site):
    slugs = json.loads((built_site / "assets" / "library-slugs.json").read_text(encoding="utf-8"))

    assert slugs == {
        "1": "bodleian-library-1",
        "9001": "etc-passwd-script-alert-xss-script-quoted-9001",
    }
    for slug in slugs.values():
        assert (built_site / "libraries" / slug / "index.html").is_file()


# ── Broken-link status on a generated page ────────────────────────────────


def test_a_broken_link_page_carries_a_dated_notice():
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org",
                       "is_disabled": True, "last_checked": "2026-08-02"})

    assert 'class="library-page__broken"' in body
    assert "confirmed broken on 2026-08-02" in body
    assert 'class="badge badge--broken"' in body
    # The link stays reachable but is never offered as a working collection.
    assert "Visit the collection" not in body
    assert "Try the collection anyway" in body
    assert "btn-visit--broken" in body


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
    assert "Visit the collection" in body
    assert "broken" not in body.lower()


def test_a_hostile_last_checked_is_escaped_on_the_page():
    body = _page_body({**HOSTILE_RECORD, "website": "https://example.org",
                       "is_disabled": True,
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
