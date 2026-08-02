"""Generate the static parts of the site from the library dataset at build time.

MkDocs calls this hook (registered under ``hooks:`` in ``mkdocs.yml``) twice.
During ``on_files`` it reads ``docs/assets/data.json`` and adds one virtual page
per record at ``libraries/<slug>/``, so every library has its own crawlable URL,
its own ``<title>``, and its own meta description. During ``on_env`` it renders
the homepage directory table from the same dataset and hands it to
``overrides/home.html``, so the rows and the summary counts are in the HTML
before any JavaScript runs.

The pages are virtual: nothing is written into ``docs/``, so ``mkdocs serve``
and the CI build in ``.github/workflows/deploy.yml`` produce identical output
and no generated Markdown is ever committed.

``data.json`` is publicly contributed through pull requests, so every field is
treated as untrusted input. Slugs are restricted to ``[a-z0-9-]``, all text is
HTML-escaped before it reaches a page, and outbound links are dropped unless
they use the ``http`` or ``https`` scheme.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from jinja2 import Environment
from markupsafe import Markup
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File, Files, InclusionLevel

# Path of the dataset, relative to the docs directory.
DATA_PATH = ("assets", "data.json")

# Directory that generated pages live under, relative to the docs directory.
OUTPUT_DIR = "libraries"

# Where the id-to-slug map is published for other consumers of the built site.
SLUG_MAP_URI = "assets/library-slugs.json"

# Jinja global that overrides/home.html reads the pre-rendered directory from.
TEMPLATE_GLOBAL = "dmm_directory"

# Only these URL schemes may become a clickable link on a generated page.
SAFE_SCHEMES = frozenset({"http", "https"})

# Text fields every record must provide before a page can be generated for it.
# The id is checked separately, because it is an integer and 0 is valid.
REQUIRED_TEXT_FIELDS = ("library", "city", "nation")

# Longest slug body kept before the disambiguating record id is appended.
MAX_SLUG_LENGTH = 80

# Target length for a meta description, in line with common search snippets.
MAX_DESCRIPTION_LENGTH = 160

# Reads naturally in a sentence, unlike the raw enum value from the schema.
QUANTITY_PHRASES = {
    "Few": "A few",
    "Dozens": "Dozens of",
    "Hundreds": "Hundreds of",
    "Thousands": "Thousands of",
    "Unknown": "An unrecorded number of",
}


def plain_text(value: Any) -> str:
    """Return ``value`` as text that is safe to place in page front matter.

    MkDocs renders theme templates with autoescaping turned off, so a value
    reaching ``<title>`` or ``<meta name="description">`` through front matter
    is written verbatim. Dropping the three characters that can end a tag or
    an attribute leaves the value inert in both contexts. Ampersands are left
    alone, because they cannot inject markup and library names contain them.
    """
    text = re.sub(r'[<>"]', "", str(value))
    return re.sub(r"\s+", " ", text).strip()


def slug_for(record: dict[str, Any]) -> str:
    """Return the slug of a validated record."""
    return slugify(str(record["library"]), record["id"])


def slugify(library: str, record_id: int) -> str:
    """Return a stable, collision-free slug for a library record.

    The record id is always appended. Twenty library names in the dataset are
    duplicated, so the name alone does not identify a record, and keeping the
    id in the slug means a URL survives a later edit to the library name.
    """
    folded = unicodedata.normalize("NFKD", library)
    ascii_only = folded.encode("ascii", "ignore").decode("ascii")
    body = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    body = body[:MAX_SLUG_LENGTH].strip("-")
    return f"{body}-{record_id}" if body else f"library-{record_id}"


def safe_url(value: Any) -> str | None:
    """Return ``value`` if it is a link that is safe to render, else ``None``.

    Anything that is not an absolute ``http``/``https`` URL is discarded, so a
    ``javascript:`` or ``data:`` value contributed to the dataset cannot become
    a clickable link.
    """
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    try:
        parts = urlsplit(candidate)
    except ValueError:
        return None
    if parts.scheme.lower() not in SAFE_SCHEMES or not parts.netloc:
        return None
    return candidate


def link_host(value: Any) -> str | None:
    """Return the bare host of a safe URL, used to tell same-named records apart."""
    url = safe_url(value)
    if url is None:
        return None
    host = urlsplit(url).netloc.lower().split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host or None


def load_records(docs_dir: str) -> list[dict[str, Any]]:
    """Read and validate the dataset, failing the build loudly on bad input."""
    path = Path(docs_dir).joinpath(*DATA_PATH)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise PluginError(f"Cannot read the library dataset at {path}: {error}") from error

    try:
        records = json.loads(raw)
    except json.JSONDecodeError as error:
        raise PluginError(f"{path} is not valid JSON: {error}") from error

    if not isinstance(records, list):
        raise PluginError(f"{path} must contain a list of records, found {type(records).__name__}.")

    for position, record in enumerate(records):
        if not isinstance(record, dict):
            raise PluginError(f"{path}: record {position} is not an object.")
        if not isinstance(record.get("id"), int) or isinstance(record["id"], bool):
            raise PluginError(f"{path}: record {position} has a missing or non-integer id.")
        missing = [
            field
            for field in REQUIRED_TEXT_FIELDS
            if not str(record.get(field) or "").strip()
        ]
        if missing:
            raise PluginError(f"{path}: record {position} is missing {', '.join(missing)}.")

    return records


def build_titles(records: list[dict[str, Any]]) -> list[str]:
    """Return one unique ``<title>`` per record.

    Where two records share a library name, city, and nation, the host of the
    collection URL is added, because that is the fact in the dataset that
    actually tells the two collections apart. The record id settles anything
    the host cannot.
    """
    bases = [
        f"{plain_text(record['library'])} — "
        f"{plain_text(record['city'])}, {plain_text(record['nation'])}"
        for record in records
    ]
    counts = Counter(bases)

    titles = []
    for base, record in zip(bases, records):
        host = link_host(record.get("website")) if counts[base] > 1 else None
        titles.append(f"{base} ({host})" if host else base)

    return ensure_unique(titles, records)


def build_descriptions(records: list[dict[str, Any]]) -> list[str]:
    """Return one unique meta description per record, built from its own fields."""
    descriptions = []
    for record in records:
        opening = (
            f"{plain_text(record['library'])} in "
            f"{plain_text(record['city'])}, {plain_text(record['nation'])}."
        )
        quantity = QUANTITY_PHRASES.get(record.get("quantity"), "Digitised")
        facts = [f"{quantity} digitised medieval manuscripts."]

        features = []
        if record.get("iiif"):
            features.append("IIIF support")
        if record.get("is_free_cultural_works_license"):
            features.append("an open licence")
        if features:
            facts.append(f"With {' and '.join(features)}.")

        host = link_host(record.get("website"))
        if host:
            facts.append(f"Browse the collection at {host}.")

        tail = " ".join(facts)
        budget = MAX_DESCRIPTION_LENGTH - len(tail) - 1
        if len(opening) > budget:
            opening = f"{opening[: max(budget - 1, 0)].rstrip()}…"
        descriptions.append(f"{opening} {tail}".strip())

    # Records that differ only in fields the description does not mention, or
    # whose opening was truncated to the same text, still need to differ.
    return ensure_unique(descriptions, records)


def ensure_unique(values: list[str], records: list[dict[str, Any]]) -> list[str]:
    """Append the record id to any value that is not unique across the dataset."""
    counts = Counter(values)
    return [
        f"{value} (#{record['id']})" if counts[value] > 1 else value
        for value, record in zip(values, records)
    ]


def render_page(record: dict[str, Any], title: str, description: str) -> str:
    """Return the Markdown source of one library page.

    The body is plain HTML with every value escaped, so no dataset field can
    inject markup or Markdown syntax into the page.
    """
    meta = yaml.safe_dump(
        {"title": title, "description": description},
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )

    badges = []
    if record.get("iiif"):
        badges.append('<span class="badge badge--iiif">IIIF</span>')
    if record.get("is_free_cultural_works_license"):
        badges.append('<span class="badge badge--open">Open licence</span>')
    if not badges:
        badges.append('<span class="badge badge--standard">Standard access</span>')

    facts = [
        ("Digitised manuscripts", escape(str(record.get("quantity") or "Unknown"))),
        ("Rights", escape(str(record.get("copyright") or "Unknown"))),
        ("IIIF support", "Yes" if record.get("iiif") else "No"),
        ("Open licence", "Yes" if record.get("is_free_cultural_works_license") else "No"),
    ]

    # One "Part of" row listing every membership, so a collection findable
    # through several aggregators names all of them.
    links = []
    for entry in aggregators_of(record):
        label = escape(str(entry["name"]))
        url = safe_url(entry.get("url"))
        links.append(
            f'<a href="{escape(url, quote=True)}" rel="noopener noreferrer" '
            f'target="_blank">{label}</a>'
            if url
            else label
        )
    if links:
        facts.append(("Part of", ", ".join(links)))

    rows = "".join(f"<dt>{name}</dt><dd>{value}</dd>" for name, value in facts)

    website = safe_url(record.get("website"))
    visit = (
        f'<p><a class="btn-visit" href="{escape(website, quote=True)}" '
        f'rel="noopener noreferrer" target="_blank">Visit the collection</a></p>'
        if website
        else "<p>No collection URL is recorded for this library.</p>"
    )

    return (
        f"---\n{meta}---\n\n"
        f"<h1>{escape(str(record['library']))}</h1>\n\n"
        f"<p class=\"library-page__location\">{escape(str(record['city']))}, "
        f"{escape(str(record['nation']))}</p>\n\n"
        f'<p class="library-page__badges">{"".join(badges)}</p>\n\n'
        f'<dl class="library-page__facts">{rows}</dl>\n\n'
        f"{visit}\n\n"
        "[Back to the library directory](../index.md)\n"
    )


def build_pages(records: list[dict[str, Any]]) -> dict[str, str]:
    """Return a mapping of ``libraries/<slug>.md`` to its Markdown source."""
    slugs = [slug_for(record) for record in records]
    duplicates = [slug for slug, count in Counter(slugs).items() if count > 1]
    if duplicates:
        raise PluginError(f"Duplicate library slugs generated: {', '.join(sorted(duplicates))}.")

    titles = build_titles(records)
    descriptions = build_descriptions(records)

    return {
        f"{OUTPUT_DIR}/{slug}.md": render_page(record, title, description)
        for slug, record, title, description in zip(slugs, records, titles, descriptions)
    }


# ── Homepage directory table ──────────────────────────────────────────────
#
# docs/assets/dashboard.js no longer builds table rows. It reuses the rows
# generated here, matching each one to its record through data-record-id, so
# the markup of a row is defined in one place only.


def render_badges(record: dict[str, Any]) -> str:
    """Return the feature badges of one record."""
    badges = []
    if record.get("iiif"):
        badges.append(
            '<span class="badge badge--iiif">'
            '<i class="bi bi-images" aria-hidden="true"></i>IIIF</span>'
        )
    if record.get("is_free_cultural_works_license"):
        badges.append(
            '<span class="badge badge--open">'
            '<i class="bi bi-unlock" aria-hidden="true"></i>Open</span>'
        )
    if not badges:
        badges.append('<span class="badge badge--standard">Standard Access</span>')
    return "".join(badges)


def aggregators_of(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the record's usable aggregator entries, in dataset order.

    An entry without a name is dropped, because the name is what identifies
    the aggregator to a reader and to the homepage filter. The URL is allowed
    to be missing or unusable here; only the link is dropped further down.
    """
    entries = record.get("aggregators")
    if not isinstance(entries, list):
        return []
    return [
        entry
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("name") or "").strip()
    ]


def render_projects(record: dict[str, Any]) -> str:
    """Return the aggregator affiliations shown under the library name, if any.

    One block per membership, in dataset order. An aggregator is named even
    when its URL is unusable, because the name is still a fact about the
    collection. Only the link is dropped.
    """
    blocks = []
    for entry in aggregators_of(record):
        label = (
            '<i class="bi bi-collection" aria-hidden="true"></i>'
            f'{escape(str(entry["name"]))}'
        )
        url = safe_url(entry.get("url"))
        body = (
            f'<a href="{escape(url, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{label}</a>'
            if url
            else label
        )
        blocks.append(f'<div class="library-project">{body}</div>')
    return "".join(blocks)


def render_visit(record: dict[str, Any]) -> str:
    """Return the Visit control of one record, or a placeholder without a URL."""
    website = safe_url(record.get("website"))
    if not website:
        return '<span style="color:var(--dash-muted);font-size:.8rem">No URL</span>'
    return (
        f'<a href="{escape(website, quote=True)}" target="_blank" '
        'rel="noopener noreferrer" class="btn-visit">Visit'
        '<i class="bi bi-arrow-right-short" aria-hidden="true"></i></a>'
    )


def render_row(record: dict[str, Any]) -> str:
    """Return one directory row. Every dataset value is escaped on the way in."""
    # slugify only ever emits [a-z0-9-], so the href cannot break its attribute.
    slug = escape(slug_for(record), quote=True)
    return (
        f'<tr data-record-id="{record["id"]}">'
        f'<td><a class="library-name" href="libraries/{slug}/">'
        f'{escape(str(record["library"]))}</a>{render_projects(record)}</td>'
        f'<td><div class="location-nation">{escape(str(record["nation"]))}</div>'
        '<div class="location-city"><i class="bi bi-dot" aria-hidden="true"></i>'
        f'{escape(str(record["city"]))}</div></td>'
        f"<td>{render_badges(record)}</td>"
        f'<td style="text-align:right">{render_visit(record)}</td>'
        "</tr>"
    )


def directory_sort_key(record: dict[str, Any]) -> tuple[str, int]:
    """Order records the way a reader expects to find them.

    dashboard.js sorts with ``localeCompare``, which no Python key can
    reproduce exactly. Folding accents away and casefolding gets close enough
    that the reorder JavaScript performs on load happens behind the loader and
    is never seen. The id breaks ties so the order is stable across builds.
    """
    library = str(record["library"])
    folded = unicodedata.normalize("NFKD", library).encode("ascii", "ignore").decode()
    return (folded.casefold() or library.casefold(), record["id"])


def summarise(records: list[dict[str, Any]]) -> dict[str, int]:
    """Return the four homepage counts, using the same rules as dashboard.js."""
    return {
        "libraries": len(records),
        "nations": len({str(record["nation"]) for record in records}),
        "iiif": sum(1 for record in records if record.get("iiif")),
        "projects": len(
            {
                str(entry["name"])
                for record in records
                for entry in aggregators_of(record)
            }
        ),
    }


def build_directory(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the rows and counts that overrides/home.html renders."""
    rows = "".join(render_row(record) for record in sorted(records, key=directory_sort_key))
    # Markup keeps the rows intact whether or not the theme autoescapes.
    return {"rows": Markup(rows), "stats": summarise(records)}


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Add one generated page per library record, plus the id-to-slug map."""
    records = load_records(config.docs_dir)

    for src_uri, markdown in build_pages(records).items():
        files.append(
            File.generated(
                config,
                src_uri,
                content=markdown,
                # Keeps 584 entries out of the navigation sidebar, and out of
                # the "not included in nav" build warning, while still leaving
                # them in sitemap.xml and in the site search index.
                inclusion=InclusionLevel.NOT_IN_NAV,
            )
        )

    slug_map = {str(record["id"]): slug_for(record) for record in records}
    files.append(
        File.generated(
            config,
            SLUG_MAP_URI,
            content=json.dumps(slug_map, ensure_ascii=False, separators=(",", ":")),
        )
    )

    return files


def on_env(env: Environment, config: MkDocsConfig, files: Files) -> None:
    """Hand the pre-rendered directory table to the homepage template.

    The dataset is read again rather than carried over from ``on_files``, so
    that a change to data.json is picked up on every ``mkdocs serve`` rebuild
    and neither entry point depends on the other having run.
    """
    env.globals[TEMPLATE_GLOBAL] = build_directory(load_records(config.docs_dir))
