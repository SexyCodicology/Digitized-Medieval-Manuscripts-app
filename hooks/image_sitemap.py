"""Publish an image sitemap from images displayed in built article content."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlsplit
from xml.etree import ElementTree

from jinja2 import Environment
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import Files

SITEMAP_PATH = "image-sitemap.xml"
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
IMAGE_NAMESPACE = "http://www.google.com/schemas/sitemap-image/1.1"
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
PAGE_PATHS_KEY = "_image_sitemap_page_paths"
MAX_IMAGES_PER_PAGE = 1000


class ArticleImages(HTMLParser):
    """Read canonical URLs and content images, excluding template decoration."""

    def __init__(self) -> None:
        super().__init__()
        self.canonical_url = ""
        self.noindex = False
        self.images: list[str] = []
        self._article_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "link" and "canonical" in (attributes.get("rel") or "").split():
            self.canonical_url = attributes.get("href") or ""
        if tag == "meta" and (attributes.get("name") or "").lower() == "robots":
            if "noindex" in (attributes.get("content") or "").lower():
                self.noindex = True
        if tag == "article":
            self._article_depth += 1
        if tag == "img" and self._article_depth and attributes.get("src"):
            self.images.append(attributes["src"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "article" and self._article_depth:
            self._article_depth -= 1


def local_images(
    sources: list[str], page_url: str, site_url: str, site_dir: Path
) -> list[str]:
    """Resolve displayed images to existing files within this published site."""
    base = urlsplit(site_url.rstrip("/") + "/")
    root = site_dir.resolve()
    images = set()
    for source in sources:
        image_url = urldefrag(urljoin(page_url, source))[0]
        parsed = urlsplit(image_url)
        if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
            continue
        if not parsed.path.startswith(base.path):
            continue
        target = (root / unquote(parsed.path[len(base.path):])).resolve()
        if (
            target.is_relative_to(root)
            and target.suffix.lower() in IMAGE_EXTENSIONS
            and target.is_file()
        ):
            images.add(image_url)
    return sorted(images)


def image_sitemap(pages: dict[str, list[str]]) -> bytes:
    """Serialise page/image associations using Google's supported XML tags."""
    root = ElementTree.Element(
        "urlset", {"xmlns": SITEMAP_NAMESPACE, "xmlns:image": IMAGE_NAMESPACE}
    )
    for page_url, images in sorted(pages.items()):
        unique_images = sorted(set(images))
        if not unique_images:
            continue
        if len(unique_images) > MAX_IMAGES_PER_PAGE:
            raise PluginError(f"Image sitemap exceeds 1,000 images for {page_url}")
        entry = ElementTree.SubElement(root, "url")
        ElementTree.SubElement(entry, "loc").text = page_url
        for image_url in unique_images:
            image = ElementTree.SubElement(entry, "image:image")
            ElementTree.SubElement(image, "image:loc").text = image_url
    ElementTree.indent(root, space="  ")
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def on_env(env: Environment, config: MkDocsConfig, files: Files) -> Environment:
    """Remember real source pages after plugins establish their final routes."""
    # Keep state on the build configuration, so repeated serve builds reset it.
    # Generated blog listings repeat excerpts and should not own their images.
    config.extra[PAGE_PATHS_KEY] = [
        file.dest_uri
        for file in files.documentation_pages()
        if (Path(config.docs_dir) / file.src_uri).is_file()
        and (
            not file.src_uri.startswith("blog/")
            or file.src_uri.startswith(("blog/posts/", "blog/archive/"))
        )
    ]
    return env


def on_post_build(config: MkDocsConfig) -> None:
    """Write the sitemap after all image URLs and files have been published."""
    root = Path(config.site_dir)
    base = config.site_url.rstrip("/") + "/"
    pages: dict[str, list[str]] = {}
    for relative_path in config.extra.get(PAGE_PATHS_KEY, []):
        parser = ArticleImages()
        parser.feed((root / relative_path).read_text(encoding="utf-8"))
        page_url = parser.canonical_url
        if parser.noindex or not page_url.startswith(base):
            continue
        images = local_images(parser.images, page_url, base, root)
        if images:
            pages[page_url] = images
    (root / SITEMAP_PATH).write_bytes(image_sitemap(pages))
