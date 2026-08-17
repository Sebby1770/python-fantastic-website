"""Load markdown essays from content/journal."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import markdown
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent.parent
JOURNAL_DIR = ROOT / "content" / "journal"


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    date: date
    dek: str
    body: str
    html: Markup
    source: Path

    @property
    def date_label(self) -> str:
        return f"{self.date.day} {self.date.strftime('%B %Y')}"

    @property
    def iso_date(self) -> str:
        return self.date.isoformat()

    @property
    def word_count(self) -> int:
        return len(self.body.split())

    @property
    def reading_minutes(self) -> int:
        return max(1, math.ceil(self.word_count / 220))


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}, stripped
    parts = stripped.split("---", 2)
    if len(parts) < 3:
        return {}, stripped
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta, parts[2].strip()


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _render(body: str) -> Markup:
    html = markdown.markdown(
        body,
        extensions=["smarty", "fenced_code", "tables", "sane_lists"],
        output_format="html5",
    )
    return Markup(html)


def _load_post(path: Path) -> Post:
    meta, body = _split_frontmatter(path.read_text(encoding="utf-8"))
    title = meta.get("title") or path.stem.replace("-", " ").title()
    dek = meta.get("dek") or ""
    published = _parse_date(meta.get("date") or "1970-01-01")
    return Post(
        slug=path.stem,
        title=title,
        date=published,
        dek=dek,
        body=body,
        html=_render(body),
        source=path,
    )


@lru_cache(maxsize=1)
def load_posts() -> tuple[Post, ...]:
    if not JOURNAL_DIR.exists():
        return ()
    posts = [_load_post(path) for path in JOURNAL_DIR.glob("*.md")]
    posts.sort(key=lambda post: (post.date, post.slug), reverse=True)
    return tuple(posts)


def get_post(slug: str) -> Post | None:
    return next((post for post in load_posts() if post.slug == slug), None)


def neighboring_posts(slug: str) -> tuple[Post | None, Post | None]:
    posts = load_posts()
    index = next((i for i, post in enumerate(posts) if post.slug == slug), None)
    if index is None:
        return None, None
    previous_item = posts[index - 1] if index > 0 else None
    next_item = posts[index + 1] if index + 1 < len(posts) else None
    return previous_item, next_item


def related_posts(slug: str, limit: int = 2) -> tuple[Post, ...]:
    others = [post for post in load_posts() if post.slug != slug]
    return tuple(others[:limit])


def clear_post_cache() -> None:
    load_posts.cache_clear()
