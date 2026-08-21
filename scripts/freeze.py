from __future__ import annotations

import re
import sys
from pathlib import Path
from shutil import copytree, rmtree

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import JOURNAL, WORK, create_app  # noqa: E402

DOCS = ROOT / "docs"
STATIC = ROOT / "static"


def rewrite_urls(html: str, depth: int) -> str:
    prefix = "../" * depth
    html = html.replace("/static/", prefix)
    html = re.sub(r'\b(href|action)="/journal/([a-z0-9-]+)"', rf'\1="{prefix}journal/\2/"', html)
    html = re.sub(r'\b(href|action)="/journal"', rf'\1="{prefix}journal/"', html)
    html = re.sub(r'\b(href|action)="/work/([a-z0-9-]+)"', rf'\1="{prefix}work/\2/"', html)
    html = re.sub(r'\b(href|action)="/lab"', rf'\1="{prefix}lab/"', html)
    html = html.replace('href="/#', f'href="{prefix}index.html#')
    html = re.sub(r'\bhref="/"', f'href="{prefix}index.html"', html)
    return html


def freeze(dest: Path | None = None) -> Path:
    dest = (dest or DOCS).resolve()
    if dest == ROOT.resolve():
        raise ValueError("Refusing to freeze into the project root")
    if dest.exists():
        rmtree(dest)
    dest.mkdir(parents=True)

    for folder in ("css", "js", "img"):
        source = STATIC / folder
        if source.exists():
            copytree(source, dest / folder)

    (dest / ".nojekyll").write_text("", encoding="utf-8")
    (dest / "lab.js").write_text((STATIC / "js" / "lab.js").read_text(encoding="utf-8"), encoding="utf-8")

    pages = [
        ("/", dest / "index.html", 0),
        ("/lab", dest / "lab" / "index.html", 1),
        ("/journal", dest / "journal" / "index.html", 1),
    ]
    for item in WORK:
        pages.append((f"/work/{item.slug}", dest / "work" / item.slug / "index.html", 2))
    for post in JOURNAL:
        pages.append((f"/journal/{post.slug}", dest / "journal" / post.slug / "index.html", 2))

    app = create_app()
    with app.test_client() as client:
        for url, path, depth in pages:
            response = client.get(url)
            if response.status_code != 200:
                raise RuntimeError(f"Failed to freeze {url}: {response.status_code}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rewrite_urls(response.get_data(as_text=True), depth), encoding="utf-8")
    return dest


def main() -> None:
    target = freeze()
    print(f"Froze site to {target}")


if __name__ == "__main__":
    main()
