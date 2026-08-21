from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from freeze import freeze, rewrite_urls  # noqa: E402


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
