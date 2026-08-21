from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from app import JOURNAL  # noqa: E402
from freeze import PAGES_ORIGIN, freeze, rewrite_urls, sitemap_locs  # noqa: E402


def test_rewrite_urls_uses_relative_asset_paths():
    html = (
        '<link href="/static/css/styles.css">'
        '<a href="/">Home</a>'
        '<a href="/#work">Work</a>'
        '<a href="/lab">Lab</a>'
        '<a href="/journal">Journal</a>'
        '<a href="/journal/ink-and-paper">Ink</a>'
        '<a href="/work/northline">Northline</a>'
    )
    home = rewrite_urls(html, 0)
    assert 'href="css/styles.css"' in home
    assert 'href="index.html"' in home
    assert 'href="index.html#work"' in home
    assert 'href="lab/"' in home
    assert 'href="journal/"' in home
    assert 'href="journal/ink-and-paper/"' in home
    assert 'href="work/northline/"' in home
    assert "/static/" not in home

    nested = rewrite_urls(html, 2)
    assert 'href="../../css/styles.css"' in nested
    assert 'href="../../lab/"' in nested
    assert 'href="../../journal/"' in nested
    assert 'href="../../journal/ink-and-paper/"' in nested
    assert 'href="../../work/northline/"' in nested


def test_freeze_writes_pages_and_assets(tmp_path):
    dest = freeze(tmp_path / "docs")
    assert (dest / ".nojekyll").exists()
    assert (dest / "css" / "styles.css").exists()
    assert (dest / "js" / "lab.js").exists()
    assert (dest / "lab.js").exists()
    assert (dest / "img" / "hero.png").exists()
    assert (dest / "index.html").exists()
    assert (dest / "lab" / "index.html").exists()
    assert (dest / "journal" / "index.html").exists()
    assert (dest / "journal" / "ink-and-paper" / "index.html").exists()
    assert (dest / "journal" / "a-scale-you-can-hear" / "index.html").exists()
    assert (dest / "work" / "northline" / "index.html").exists()
    assert (dest / "work" / "meridian" / "index.html").exists()
    assert (dest / "work" / "cobalt-room" / "index.html").exists()

    home = (dest / "index.html").read_text(encoding="utf-8")
    lab = (dest / "lab" / "index.html").read_text(encoding="utf-8")
    journal = (dest / "journal" / "index.html").read_text(encoding="utf-8")
    note = (dest / "journal" / "ink-and-paper" / "index.html").read_text(encoding="utf-8")
    work = (dest / "work" / "northline" / "index.html").read_text(encoding="utf-8")
    assert "/static/" not in home
    assert 'href="css/styles.css"' in home
    assert 'href="work/northline/"' in home
    assert 'href="journal/"' in home
    assert 'src="../js/lab.js"' in lab
    assert 'href="../journal/"' in lab
    assert "Journal" in journal
    assert 'href="../journal/ink-and-paper/"' in journal
    assert "Ink, paper, and the seven-to-one line" in note
    assert 'href="../../css/styles.css"' in note
    assert 'href="../../css/styles.css"' in work
    assert "Studio Lab" in lab
    assert "Northline" in work
    assert "Best on ink" in lab
    assert "SCSS map" in lab
    assert "$studio:" in lab
    assert "Copy lab link" in lab
    assert "data-mix" in lab
    assert not (dest / "lab.json").exists()
    assert 'rel="alternate"' in journal
    assert 'type="application/rss+xml"' in journal
    assert "feed.xml" in journal

    feed = (dest / "feed.xml").read_text(encoding="utf-8")
    assert 'rss version="2.0"' in feed
    assert f"{PAGES_ORIGIN}/journal/" in feed
    for post in JOURNAL:
        assert post.title in feed
        assert post.dek in feed
        assert f"{PAGES_ORIGIN}/journal/{post.slug}/" in feed

    sitemap = (dest / "sitemap.xml").read_text(encoding="utf-8")
    robots = (dest / "robots.txt").read_text(encoding="utf-8")
    locs = sitemap_locs()
    assert locs == [
        f"{PAGES_ORIGIN}/",
        f"{PAGES_ORIGIN}/lab/",
        f"{PAGES_ORIGIN}/journal/",
        f"{PAGES_ORIGIN}/work/northline/",
        f"{PAGES_ORIGIN}/work/meridian/",
        f"{PAGES_ORIGIN}/work/cobalt-room/",
        f"{PAGES_ORIGIN}/journal/ink-and-paper/",
        f"{PAGES_ORIGIN}/journal/a-scale-you-can-hear/",
    ]
    for loc in locs:
        assert loc in sitemap
        assert loc.endswith("/")
    assert "lab.json" not in sitemap
    assert "Allow: /" in robots
    assert f"Sitemap: {PAGES_ORIGIN}/sitemap.xml" in robots

    css = (dest / "css" / "styles.css").read_text(encoding="utf-8")
    assert "@media print" in css
    assert ".site-nav" in css.split("@media print")[1]
    assert ".menu-toggle" in css.split("@media print")[1]
    assert ".contact-form" in css.split("@media print")[1]
