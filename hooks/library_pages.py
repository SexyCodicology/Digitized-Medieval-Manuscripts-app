"""Generate one static page per manuscript library at build time.

MkDocs calls this hook (registered under ``hooks:`` in ``mkdocs.yml``) during
``on_files``. It reads ``docs/assets/data.json`` and adds one virtual page per
record at ``libraries/<slug>/``, so every library has its own crawlable URL,
its own ``<title>``, and its own meta description.

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
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File, Files, InclusionLevel

# Path of the dataset, relative to the docs directory.
DATA_PATH = ("assets", "data.json")

# Directory that generated pages live under, relative to the docs directory.
OUTPUT_DIR = "libraries"

# Where the id-to-slug map is published for the homepage table to consume.
SLUG_MAP_URI = "assets/library-slugs.json"

# Only these URL schemes may become a clickable link on a generated page.
SAFE_SCHEMES = frozenset({"http", "https"})

# Fields every record must provide before a page can be generated for it.
REQUIRED_FIELDS = ("id", "library", "city", "nation")

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
        missing = [field for field in REQUIRED_FIELDS if not record.get(field)]
        if missing:
            raise PluginError(f"{path}: record {position} is missing {', '.join(missing)}.")
        if not isinstance(record["id"], int) or isinstance(record["id"], bool):
            raise PluginError(f"{path}: record {position} has a non-integer id.")

    return records


def build_titles(records: list[dict[str, Any]]) -> list[str]:
    """Return one unique ``<title>`` per record.

    Where two records share a library name, city, and nation, the host of the
    collection URL is added, because that is the fact in the dataset that
    actually tells the two collections apart. The record id settles anything
    the host cannot.
    """
    bases = [f"{record['library']} — {record['city']}, {record['nation']}" for record in records]
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
        opening = f"{record['library']} in {record['city']}, {record['nation']}."
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

    project_url = safe_url(record.get("is_part_of_url"))
    project_name = record.get("is_part_of_project_name")
    if record.get("is_part_of") and project_name:
        label = escape(str(project_name))
        value = (
            f'<a href="{escape(project_url, quote=True)}" rel="noopener noreferrer" '
            f'target="_blank">{label}</a>'
            if project_url
            else label
        )
        facts.append(("Part of", value))

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
    slugs = [slugify(str(record["library"]), record["id"]) for record in records]
    duplicates = [slug for slug, count in Counter(slugs).items() if count > 1]
    if duplicates:
        raise PluginError(f"Duplicate library slugs generated: {', '.join(sorted(duplicates))}.")

    titles = build_titles(records)
    descriptions = build_descriptions(records)

    return {
        f"{OUTPUT_DIR}/{slug}.md": render_page(record, title, description)
        for slug, record, title, description in zip(slugs, records, titles, descriptions)
    }


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

    slug_map = {
        str(record["id"]): slugify(str(record["library"]), record["id"]) for record in records
    }
    files.append(
        File.generated(
            config,
            SLUG_MAP_URI,
            content=json.dumps(slug_map, ensure_ascii=False, separators=(",", ":")),
        )
    )

    return files
