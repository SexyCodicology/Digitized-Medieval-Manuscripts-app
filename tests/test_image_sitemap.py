"""Check image discovery against rendered articles and final MkDocs routes."""

from pathlib import Path
from xml.etree import ElementTree

import pytest
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import PluginError

from hooks import image_sitemap as hook

SITE_URL = "https://example.org/project/"
NAMESPACES = {"sm": hook.SITEMAP_NAMESPACE, "image": hook.IMAGE_NAMESPACE}


def test_parser_reads_content_images_without_navigation_or_author_avatars():
    parser = hook.ArticleImages()
    parser.feed(
        '<link rel="canonical" href="https://example.org/project/story/">'
        '<aside><img src="avatar.jpg"></aside>'
        '<article><img src="first.jpg"><figure><img src="second.jpg"/>'
        '</figure></article><footer><img src="logo.svg"></footer>'
    )
    assert parser.canonical_url == SITE_URL + "story/"
    assert parser.images == ["first.jpg", "second.jpg"]


def test_local_images_keep_existing_site_images_and_exclude_unsafe_paths(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "image & detail.jpg").write_bytes(b"image")
    sources = [
        "../assets/image%20%26%20detail.jpg#detail",
        "../assets/image%20%26%20detail.jpg",
        "../assets/missing.png",
        "https://other.example.org/image.jpg",
        "https://example.org/outside.jpg",
        "/project/%2e%2e/outside.jpg",
        "data:image/png;base64,cGljdHVyZQ==",
    ]
    assert hook.local_images(sources, SITE_URL + "story/", SITE_URL, tmp_path) == [
        SITE_URL + "assets/image%20%26%20detail.jpg"
    ]


def test_image_sitemap_escapes_urls_deduplicates_and_omits_empty_pages():
    document = hook.image_sitemap({
        SITE_URL + "story/": [SITE_URL + "image.jpg?a=1&b=2"] * 2,
        SITE_URL + "empty/": [],
    })
    root = ElementTree.fromstring(document)
    entries = root.findall("sm:url", NAMESPACES)
    assert len(entries) == 1
    assert entries[0].findtext("sm:loc", namespaces=NAMESPACES) == SITE_URL + "story/"
    assert entries[0].findtext("image:image/image:loc", namespaces=NAMESPACES) == (
        SITE_URL + "image.jpg?a=1&b=2"
    )
    assert len(entries[0].findall("image:image", NAMESPACES)) == 1


def test_image_sitemap_rejects_more_than_google_limit():
    with pytest.raises(PluginError, match="exceeds 1,000"):
        hook.image_sitemap({SITE_URL: [f"{SITE_URL}{n}.jpg" for n in range(1001)]})


def test_noindex_directive_survives_multiple_robots_meta_tags():
    parser = hook.ArticleImages()
    parser.feed('<meta name="robots" content="noindex,follow">'
                '<meta name="robots" content="follow"><meta name>')
    assert parser.noindex


def test_mkdocs_build_uses_final_post_routes_and_excludes_listing_excerpts(tmp_path):
    docs = tmp_path / "docs"
    posts = docs / "blog" / "posts"
    (posts / "assets").mkdir(parents=True)
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs / "blog" / "index.md").write_text("# Blog\n", encoding="utf-8")
    (posts / "assets" / "photo.jpg").write_bytes(b"local image")
    (posts / "source-name.md").write_text(
        "---\ndate: 2024-01-01\nslug: stable-route\n---\n# Story\n\n"
        "![Detail](assets/photo.jpg)\n\n<!-- more -->\n\nArticle.\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "mkdocs.yml"
    hook_path = Path(hook.__file__).resolve().as_posix()
    config_path.write_text(
        f"site_name: Test\nsite_url: {SITE_URL}\ntheme:\n  name: material\n"
        "plugins:\n  - blog:\n      post_url_format: '{slug}'\n"
        f"hooks:\n  - '{hook_path}'\n",
        encoding="utf-8",
    )
    config = load_config(str(config_path))
    build(config)
    sitemap_path = Path(config.site_dir) / hook.SITEMAP_PATH
    root = ElementTree.fromstring(sitemap_path.read_bytes())
    entries = root.findall("sm:url", NAMESPACES)
    assert len(entries) == 1
    assert entries[0].findtext("sm:loc", namespaces=NAMESPACES) == (
        SITE_URL + "blog/stable-route/"
    )
    assert entries[0].findtext("image:image/image:loc", namespaces=NAMESPACES) == (
        SITE_URL + "blog/assets/photo.jpg"
    )
    # Rebuilding the same configuration refreshes the per-build page list.
    (posts / "source-name.md").write_text(
        "---\ndate: 2024-01-01\nslug: stable-route\n---\n# Story\n\n"
        "No image.\n\n<!-- more -->\n\nArticle.\n", encoding="utf-8"
    )
    build(config)
    root = ElementTree.fromstring(sitemap_path.read_bytes())
    assert not root.findall("sm:url", NAMESPACES)
