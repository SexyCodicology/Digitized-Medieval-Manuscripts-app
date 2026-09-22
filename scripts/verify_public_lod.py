"""Check that a deployed Pages release serves the linked-data directory.

The build verifier checks every generated file before upload. This smaller
network check confirms that the published dataset matches the checked-out
release and that representative human and JSON-LD URLs are reachable.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_RESPONSE_BYTES = 8_000_000
REQUEST_TIMEOUT_SECONDS = 20


class LinkParser(HTMLParser):
    """Collect public link and metadata elements without depending on markup order."""

    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"a", "link", "meta"}:
            self.elements.append((tag, {key: value or "" for key, value in attrs}))

    def has_link(self, relation: str, url: str) -> bool:
        """Return whether a link element advertises this URL and relation."""
        return any(
            tag == "link"
            and relation in attributes.get("rel", "").split()
            and attributes.get("href") == url
            for tag, attributes in self.elements
        )

    def has_anchor(self, url: str) -> bool:
        """Return whether a reader-visible anchor points to the URL."""
        return any(
            tag == "a" and attributes.get("href") == url
            for tag, attributes in self.elements
        )


def fetch_text(url: str) -> str:
    """Read one public file with a timeout and bounded response size."""
    request = Request(url, headers={"User-Agent": "DMMapp-release-check/1.0"})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise ValueError(f"{url} returned HTTP {response.status}")
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError(f"{url} exceeds the release-check size limit")
    return body.decode("utf-8")


def fetch_content_type(url: str) -> str:
    """Read one public file's Content-Type header without its body."""
    request = Request(
        url, method="HEAD", headers={"User-Agent": "DMMapp-release-check/1.0"}
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise ValueError(f"{url} returned HTTP {response.status}")
        return response.headers.get("Content-Type", "")


def content_type_errors(
    base_url: str,
    records: list[dict[str, Any]],
    fetch_type: Callable[[str], str],
) -> list[str]:
    """Report distribution URLs whose Content-Type disagrees with their format.

    GitHub Pages may serve JSON-LD with a generic content type (see
    docs/linked-data.md); this turns that documented uncertainty into a
    checked fact on every deployment instead of an unverified assumption.
    """
    base = base_url.rstrip("/") + "/"
    checks = [
        (base + "assets/dmmapp-linked-data.jsonld", "application/ld+json"),
        (base + "assets/link-assertions.csv", "text/csv"),
    ]
    checks.extend(
        (base + f"linked-data/records/{record_id}.jsonld", "application/ld+json")
        for record_id in sample_ids(records)
    )
    errors = []
    for url, expected in checks:
        actual = fetch_type(url).split(";", 1)[0].strip()
        if actual != expected:
            errors.append(
                f"{url} served Content-Type {actual or '(missing)'!r}, "
                f"expected {expected!r}"
            )
    return errors


def sample_ids(records: list[dict[str, Any]]) -> list[str]:
    """Select first, middle, and last IDs without relying on dataset order."""
    ids = sorted(record["id"] for record in records)
    if not ids:
        return []
    return list(dict.fromkeys(str(ids[index]) for index in (0, len(ids) // 2, -1)))


def inspect_site(
    base_url: str,
    records: list[dict[str, Any]],
    aliases: dict[str, list[str]],
    expected_assertions: str,
    fetch: Callable[[str], str],
) -> list[str]:
    """Report content and discovery failures on the deployed static site."""
    base = base_url.rstrip("/") + "/"
    errors: list[str] = []
    if not records:
        return ["checked-out release has no records"]
    remote_records = json.loads(fetch(base + "assets/data.json"))
    if remote_records != records:
        errors.append("public data.json does not match the checked-out release")
    remote_assertions = fetch(base + "assets/link-assertions.csv")
    if remote_assertions.splitlines() != expected_assertions.splitlines():
        errors.append("public link assertion register does not match the release")

    bulk = json.loads(fetch(base + "assets/dmmapp-linked-data.jsonld"))
    if not isinstance(bulk, dict):
        return [*errors, "public JSON-LD document is not an object"]
    graph = bulk.get("@graph", [])
    if not isinstance(graph, list):
        return [*errors, "public JSON-LD graph is not a list"]
    catalogue = next(
        (
            node for node in graph
            if isinstance(node, dict) and node.get("@id") == base + "#catalog"
        ),
        None,
    )
    expected = {
        base + f"libraries/id-{record['id']}/#record" for record in records
    }
    catalogue_records = catalogue.get("dcat:record", []) if catalogue else []
    actual = {
        node.get("@id") for node in catalogue_records if isinstance(node, dict)
    } if isinstance(catalogue_records, list) else set()
    if actual != expected:
        errors.append("public JSON-LD catalogue record IDs differ from data.json")

    sitemap = ElementTree.fromstring(fetch(base + "sitemap.xml"))
    locations = {
        element.text
        for element in sitemap.iter()
        if element.tag.rsplit("}", 1)[-1] == "loc"
    }
    for record_id in sample_ids(records):
        page_url = base + f"libraries/id-{record_id}/"
        data_url = base + f"linked-data/records/{record_id}.jsonld"
        page = LinkParser()
        page.feed(fetch(page_url))
        if not page.has_link("canonical", page_url):
            errors.append(f"public ID page {record_id} lacks its canonical URL")
        if not page.has_link("alternate", data_url):
            errors.append(f"public ID page {record_id} lacks its JSON-LD link")
        if page_url not in locations:
            errors.append(f"public ID page {record_id} is absent from the sitemap")

        record_document = json.loads(fetch(data_url))
        record_graph = (
            record_document.get("@graph", [])
            if isinstance(record_document, dict)
            else []
        )
        if not isinstance(record_graph, list) or not any(
            isinstance(node, dict) and node.get("@id") == page_url + "#record"
            for node in record_graph
        ):
            errors.append(f"public JSON-LD file {record_id} has the wrong record ID")

        old_slugs = aliases.get(record_id, [])
        if old_slugs:
            alias = LinkParser()
            alias.feed(fetch(base + f"libraries/{old_slugs[0]}/"))
            if not alias.has_link("canonical", page_url):
                errors.append(f"public alias {old_slugs[0]} has the wrong canonical URL")
            if not alias.has_anchor(f"../id-{record_id}/"):
                errors.append(f"public alias {old_slugs[0]} lacks a visible target")
    return errors


def main() -> int:
    """Retry a post-deployment smoke check while Pages propagates a release."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="GitHub Pages deployment URL")
    parser.add_argument("--attempts", type=int, default=5)
    parser.add_argument("--retry-seconds", type=int, default=15)
    options = parser.parse_args()
    url = urlsplit(options.base_url)
    if (
        url.scheme != "https"
        or not url.netloc
        or url.query
        or url.fragment
        or options.attempts < 1
        or options.retry_seconds < 0
    ):
        parser.error("provide an HTTPS deployment URL and at least one attempt")

    try:
        records = json.loads(
            (REPO_ROOT / "docs/assets/data.json").read_text(encoding="utf-8")
        )
        aliases = json.loads(
            (REPO_ROOT / "docs/assets/library-aliases.json").read_text(encoding="utf-8")
        )
        assertions = (REPO_ROOT / "docs/assets/link-assertions.csv").read_text(
            encoding="utf-8"
        )
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read local release data: {error}", file=sys.stderr)
        return 1

    for attempt in range(1, options.attempts + 1):
        try:
            errors = inspect_site(
                options.base_url,
                records,
                aliases,
                assertions,
                fetch_text,
            )
            errors += content_type_errors(options.base_url, records, fetch_content_type)
        except (OSError, ValueError, UnicodeError, ElementTree.ParseError) as error:
            errors = [str(error)]
        if not errors:
            print(f"Public linked-data smoke check passed on attempt {attempt}.")
            return 0
        print(f"Public check attempt {attempt} failed: {', '.join(errors)}", file=sys.stderr)
        if attempt < options.attempts:
            time.sleep(options.retry_seconds)
    return 1


if __name__ == "__main__":
    sys.exit(main())
