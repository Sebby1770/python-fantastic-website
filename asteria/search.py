"""Site search over case studies and journal posts."""

from __future__ import annotations

from dataclasses import dataclass

from asteria.catalog import WORK
from asteria.journal import load_posts

TITLE_WEIGHT = 3
SUMMARY_WEIGHT = 2
BODY_WEIGHT = 1


@dataclass(frozen=True)
class SearchHit:
    kind: str
    slug: str
    title: str
    summary: str
    score: int

    @property
    def kind_label(self) -> str:
        return "Case study" if self.kind == "work" else "Journal"


def rank(query: str, *, title: str = "", summary: str = "", body: str = "") -> int:
    """Score a document. Title hits outrank dek/summary, which outrank body."""
    needle = query.casefold().strip()
    if not needle:
        return 0
    score = 0
    if needle in title.casefold():
        score += TITLE_WEIGHT
    if needle in summary.casefold():
        score += SUMMARY_WEIGHT
    if needle in body.casefold():
        score += BODY_WEIGHT
    return score


def search_site(query: str) -> list[SearchHit]:
    needle = (query or "").strip()
    if not needle:
        return []

    hits: list[SearchHit] = []
    for study in WORK:
        score = rank(
            needle,
            title=study.name,
            summary=f"{study.summary} {study.category}",
            body=f"{study.problem} {study.approach}",
        )
        if score:
            hits.append(
                SearchHit(
                    kind="work",
                    slug=study.slug,
                    title=study.name,
                    summary=study.summary,
                    score=score,
                )
            )

    for post in load_posts():
        score = rank(
            needle,
            title=post.title,
            summary=post.dek,
            body=post.body,
        )
        if score:
            hits.append(
                SearchHit(
                    kind="journal",
                    slug=post.slug,
                    title=post.title,
                    summary=post.dek,
                    score=score,
                )
            )

    hits.sort(key=lambda hit: (-hit.score, hit.title.casefold(), hit.kind))
    return hits
