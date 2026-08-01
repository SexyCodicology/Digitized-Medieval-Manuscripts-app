"""Checks for the homepage directory table generated in hooks/library_pages.py.

Run with ``pytest`` from the repository root. The hook is loaded by path
because ``hooks/`` is a MkDocs hook directory rather than an installed package.

The table is what a visitor and a crawler see without running any JavaScript,
so these checks cover the row count, the summary counts, and the two ways
publicly contributed data could turn into markup: unescaped text and an
unsafe link.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"

# Matches the rows the hook emits, whichever record they describe.
ROW_PATTERN = re.compile(r'<tr data-record-id="(-?\d+)">')


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
# field, and links that are not http(s).
HOSTILE_RECORD = {
    "id": 9001,
    "library": '<script>alert("xss")</script> & "quoted"',
    "city": "<img src=x onerror=alert(1)>Città",
    "nation": "Nation & Co </td>",
    "quantity": "Few",
    "copyright": '"><script>alert(2)</script>',
    "website": "javascript:alert(3)",
    "iiif": True,
    "is_free_cultural_works_license": True,
    "is_part_of": True,
    "is_part_of_project_name": "<b>Project</b>",
    "is_part_of_url": "data:text/html,<script>alert(4)</script>",
}

SAFE_RECORD = {
    "id": 1,
    "library": "Bodleian Library",
    "city": "Oxford",
    "nation": "United Kingdom",
    "quantity": "Thousands",
    "copyright": "Public Domain",
    "website": "https://digital.bodleian.ox.ac.uk",
    "iiif": True,
    "is_free_cultural_works_license": True,
    "is_part_of": True,
    "is_part_of_project_name": "Polonsky",
    "is_part_of_url": "https://polonsky.example.org",
}


@pytest.fixture(scope="module")
def records() -> list[dict]:
    return hook.load_records(str(DOCS_DIR))


@pytest.fixture(scope="module")
def directory(records) -> dict:
    return hook.build_directory(records)


# ── Happy path ────────────────────────────────────────────────────────────


def test_one_row_per_record(records, directory):
    ids = ROW_PATTERN.findall(directory["rows"])

    assert len(ids) == len(records)
    assert sorted(ids, key=int) == sorted((str(record["id"]) for record in records), key=int)


def test_rows_are_ordered_by_library_name(records, directory):
    order = [int(record_id) for record_id in ROW_PATTERN.findall(directory["rows"])]
    by_id = {record["id"]: record for record in records}
    names = [hook.directory_sort_key(by_id[record_id]) for record_id in order]

    assert names == sorted(names)


def test_a_row_links_the_library_to_its_generated_page():
    row = hook.render_row(SAFE_RECORD)

    assert f'<a class="library-name" href="libraries/{hook.slug_for(SAFE_RECORD)}/">' in row
    assert ">Bodleian Library</a>" in row
    assert '<div class="location-nation">United Kingdom</div>' in row
    assert "Oxford</div>" in row
    assert '<a href="https://digital.bodleian.ox.ac.uk"' in row
    assert '<a href="https://polonsky.example.org"' in row


def test_badges_reflect_the_record_features():
    plain = {**SAFE_RECORD, "iiif": False, "is_free_cultural_works_license": False}

    assert hook.render_badges(SAFE_RECORD).count("<span") == 2
    assert "badge--iiif" in hook.render_badges(SAFE_RECORD)
    assert "badge--open" in hook.render_badges(SAFE_RECORD)
    assert hook.render_badges(plain) == '<span class="badge badge--standard">Standard Access</span>'


def test_a_record_without_a_website_gets_no_link():
    row = hook.render_row({**SAFE_RECORD, "website": None})

    assert "btn-visit" not in row
    assert "No URL" in row


# ── Summary counts ────────────────────────────────────────────────────────


def test_counts_use_the_same_rules_as_dashboard_js():
    dataset = [
        {**SAFE_RECORD, "id": 1, "nation": "France", "iiif": True},
        {**SAFE_RECORD, "id": 2, "nation": "France", "iiif": False},
        {**SAFE_RECORD, "id": 3, "nation": "Italy", "iiif": True,
         "is_part_of_project_name": "Biblissima"},
        # Named but not flagged as part of a project, so it counts for neither.
        {**SAFE_RECORD, "id": 4, "nation": "Italy", "iiif": False, "is_part_of": False,
         "is_part_of_project_name": "Ignored"},
    ]

    assert hook.summarise(dataset) == {
        "libraries": 4,
        "nations": 2,
        "iiif": 2,
        "projects": 2,
    }


def test_counts_match_the_real_dataset(records, directory):
    nations = {str(record["nation"]) for record in records}

    assert directory["stats"]["libraries"] == len(records)
    assert directory["stats"]["nations"] == len(nations)
    assert directory["stats"]["iiif"] == sum(1 for r in records if r.get("iiif"))


# ── Malformed and hostile input ───────────────────────────────────────────


def test_hostile_text_is_rendered_as_text():
    row = hook.render_row(HOSTILE_RECORD)

    assert "<script" not in row
    assert "<img" not in row
    assert "<b>Project</b>" not in row
    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;" in row
    assert "&lt;img src=x onerror=alert(1)&gt;" in row
    assert "Nation &amp; Co &lt;/td&gt;" in row
    assert "&lt;b&gt;Project&lt;/b&gt;" in row

    # The row still has exactly the four cells the table header describes.
    assert row.count("<td") == 4
    assert row.count("</tr>") == 1


def test_unsafe_urls_do_not_become_clickable():
    row = hook.render_row(HOSTILE_RECORD)

    assert "javascript:" not in row
    assert "data:text/html" not in row
    assert "btn-visit" not in row
    assert "No URL" in row
    # The project is still named, but the only link left is the library page.
    assert row.count("<a ") == 1
    assert 'class="library-name"' in row


@pytest.mark.parametrize(
    "value",
    ["javascript:alert(1)", "data:text/html,<b>", "//example.org", "not a url", "", None, 42],
)
def test_an_unusable_project_url_leaves_the_name_unlinked(value):
    row = hook.render_row({**SAFE_RECORD, "is_part_of_url": value})

    assert '<div class="library-project">' in row
    assert "Polonsky" in row
    assert row.count("<a ") == 2  # library name and Visit, not the project


# ── External dependency failure ───────────────────────────────────────────


def test_a_broken_dataset_fails_the_build(tmp_path):
    """A table that cannot be built must stop the build, not ship empty."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "data.json").write_text("{ not json", encoding="utf-8")

    with pytest.raises(hook.PluginError):
        hook.build_directory(hook.load_records(str(tmp_path)))


# ── End-to-end build ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def built_home(tmp_path_factory) -> str:
    """Build a miniature site through real MkDocs, using the real overrides."""
    project = tmp_path_factory.mktemp("home")
    docs = project / "docs"
    (docs / "assets").mkdir(parents=True)

    (docs / "assets" / "data.json").write_text(
        json.dumps([SAFE_RECORD, HOSTILE_RECORD]), encoding="utf-8"
    )
    (docs / "index.md").write_text("---\ntemplate: home.html\n---\n", encoding="utf-8")
    (project / "mkdocs.yml").write_text(
        "site_name: Test\n"
        "site_url: https://example.org/\n"
        "docs_dir: docs\n"
        f"theme:\n  name: material\n  custom_dir: {(REPO_ROOT / 'overrides').as_posix()}\n"
        "nav:\n  - Home: index.md\n"
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
    return (project / "site" / "index.html").read_text(encoding="utf-8")


def test_the_built_homepage_ships_the_rows(built_home):
    body = built_home.split('<tbody id="tableBody">', 1)[1].split("</tbody>", 1)[0]

    assert len(ROW_PATTERN.findall(body)) == 2
    assert "Bodleian Library" in body
    assert 'href="libraries/bodleian-library-1/"' in body


def test_the_built_homepage_ships_the_counts(built_home):
    counts = {
        name: re.search(rf'id="{name}">(.*?)<', built_home).group(1)
        for name in ("statTotal", "statNations", "statIIIF", "statProjects")
    }

    assert counts == {
        "statTotal": "2",
        "statNations": "2",
        "statIIIF": "2",
        "statProjects": "2",
    }
    assert re.search(r'id="showingCount">(.*?)<', built_home).group(1) == "2"


def test_the_built_homepage_hides_the_loader_without_javascript(built_home):
    assert "<noscript>" in built_home
    assert re.search(r"<noscript>.*?#loader.*?</noscript>", built_home, re.S)


def test_the_hostile_record_injects_nothing_into_the_built_homepage(built_home):
    body = built_home.split('<tbody id="tableBody">', 1)[1].split("</tbody>", 1)[0]

    assert "<script" not in body
    assert "<img" not in body
    assert "javascript:" not in body
    assert "data:text/html" not in body
