"""Studio copy: case studies, services, process, and about material."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stat:
    value: str
    label: str


@dataclass(frozen=True)
class Service:
    title: str
    summary: str


@dataclass(frozen=True)
class ProcessStep:
    label: str
    title: str
    summary: str


@dataclass(frozen=True)
class Principle:
    title: str
    summary: str


@dataclass(frozen=True)
class CaseStudy:
    slug: str
    folio: str
    name: str
    category: str
    summary: str
    image: str
    year: str
    problem: str
    approach: str
    outcome: str
    stack: tuple[str, ...]
    quote: str
    attribution: str


VERSION = "2.0.0"

STATS = [
    Stat("47", "launches shipped"),
    Stat("1.2s", "typical first load"),
    Stat("96%", "client retention"),
]

SERVICES = [
    Service(
        "Python web builds",
        "Flask foundations, clean routing, production-minded project structure, and fast server-rendered pages.",
    ),
    Service(
        "Visual systems",
        "A tailored interface language with responsive layouts, crisp sections, and reusable components.",
    ),
    Service(
        "Launch readiness",
        "Accessibility checks, useful tests, simple deployment notes, and a repository that is easy to extend.",
    ),
]

PROCESS = [
    ProcessStep(
        "01",
        "Shape the story",
        "Clarify the offer, audience, and strongest first impression before touching the interface.",
    ),
    ProcessStep(
        "02",
        "Build the system",
        "Turn the visual direction into resilient templates, styling, and Python routes.",
    ),
    ProcessStep(
        "03",
        "Polish the launch",
        "Test the important paths, tune the responsive details, and prepare the repo for GitHub.",
    ),
]

PRINCIPLES = [
    Principle(
        "Story before surface",
        "If the offer is muddy, no amount of type will save it. We write the first screen out loud before we open a template.",
    ),
    Principle(
        "Server-rendered unless it cannot be",
        "Most studio sites are documents with a few honest interactions. HTML that arrives whole is faster to test and kinder to read.",
    ),
    Principle(
        "Color with a job",
        "Paper, ink, teal, coral, and gold are the rooms of the system. New hues have to earn a purpose, not a mood board.",
    ),
    Principle(
        "A repo someone else can inherit",
        "Clear routes, tests on the words that matter, and no framework theatre. The next person should ship a change on the first afternoon.",
    ),
]

STACK = [
    "Python 3.11+",
    "Flask & Jinja",
    "SQLite for inquiries",
    "Vanilla CSS and a little JavaScript",
    "pytest on the routes that matter",
    "Gunicorn in a slim container",
]

PROJECT_TYPES = [
    "Website",
    "Brand platform",
    "Product site",
    "Editorial / catalog",
    "Other",
]

BUDGETS = [
    "To be scoped",
    "Under $15k",
    "$15–40k",
    "$40k and up",
]

TIMELINES = [
    "As soon as we can",
    "This quarter",
    "This year",
    "Still exploring",
]

WORK = [
    CaseStudy(
        slug="northline",
        folio="01",
        name="Northline",
        category="Brand platform",
        summary="A high-trust launch system for a technical consulting firm.",
        image="img/work-northline.png",
        year="2024",
        problem=(
            "Northline advises on infrastructure that clients never see. Their previous site "
            "read like a staffing brochure: stock corridors, interchangeable adjectives, a form "
            "that asked for a phone number and nothing else. Serious buyers skimmed once and left. "
            "The practice was careful. The website argued otherwise."
        ),
        approach=(
            "We treated the site as a launch system, not a pamphlet. Case narratives carry the proof. "
            "The type is restrained; the first screen states the work in a sentence a partner can "
            "repeat. Pages stay server-rendered so a buyer can read them on a train without waiting "
            "on a JavaScript handshake. The contact path asks for the brief, the constraint, and "
            "the timeline — not a newsletter signup."
        ),
        outcome=(
            "First meaningful paint sits under 1.2 seconds on a mid-range laptop. The volume of "
            "inquiries did not explode; the quality did. Partners now arrive already knowing what "
            "Northline will not take on, which is the point of a high-trust practice."
        ),
        stack=("Flask", "Jinja", "Custom CSS", "pytest"),
        quote="They made the practice look as careful as the work.",
        attribution="Director, Northline",
    ),
    CaseStudy(
        slug="meridian",
        folio="02",
        name="Meridian",
        category="Product website",
        summary="A conversion-focused site with clear paths for buyers and partners.",
        image="img/work-meridian.png",
        year="2025",
        problem=(
            "Meridian had a capable product and a website that explained none of it. Buyers and "
            "partners landed on the same scrolling pitch. One group wanted pricing they could defend "
            "internally. The other wanted an integration story. Both left with a vague sense that "
            "the thing was 'powerful' and no idea what to do next."
        ),
        approach=(
            "Two paths from the first screen, labelled in language a human would say out loud. "
            "Pricing that can be read in a meeting without a salesperson translating. A technical "
            "appendix for the people who need it, kept off the path of the people who do not. "
            "We kept the Flask app small: routes for the story, the product, the partners, and "
            "a single brief."
        ),
        outcome=(
            "Demo requests rose. Support tickets that began with 'what does this actually do' fell. "
            "The sales team stopped rewriting the homepage in slide decks because the page finally "
            "did the job."
        ),
        stack=("Flask", "Jinja", "Modular CSS", "Form endpoint"),
        quote="Finally a site that does not argue with the product.",
        attribution="Head of Product, Meridian",
    ),
    CaseStudy(
        slug="cobalt-room",
        folio="03",
        name="Cobalt Room",
        category="Experience design",
        summary="A cinematic editorial presence for an intimate events venue.",
        image="img/work-cobalt.png",
        year="2025",
        problem=(
            "Cobalt Room is an intimate venue with a cinematic interior and a booking process that "
            "lived on a Facebook page plus a PDF. The room is particular: low light, a long table, "
            "no confetti cannons. The web presence invited every kind of night, which is how you "
            "fill a calendar with the wrong ones."
        ),
        approach=(
            "Large stills, short copy, a booking brief that reads like an invitation. Dark surfaces, "
            "gold rules, no stock celebration imagery. We designed the page to feel like crossing "
            "the threshold: you know in four seconds whether the room is for you. The Flask form "
            "collects date, shape of the evening, and how they found the room."
        ),
        outcome=(
            "The calendar filled with quieter, better-fit nights. Inquiries that began with 'do you "
            "do daytime expos' dropped away, which the operators count as a success. The site is "
            "now the first thing they send, not the thing they apologize for."
        ),
        stack=("Flask", "Editorial CSS", "Responsive media", "Booking brief"),
        quote="It feels like walking in.",
        attribution="Host, Cobalt Room",
    ),
    CaseStudy(
        slug="harbor-press",
        folio="04",
        name="Harbor Press",
        category="Catalog & identity",
        summary="A reading-room catalog for a small literary press that refused to treat books as SKUs.",
        image="img/work-harbor.png",
        year="2026",
        problem=(
            "Harbor Press publishes a dozen titles a year and had a theme that treated every book "
            "as a tile with an add-to-cart button. Writers submitting work could not tell the press "
            "had a point of view. Readers could not browse the way they browse a table: slowly, "
            "by season, by the company a book keeps."
        ),
        approach=(
            "Seasonal issues as chapters. Each title gets a long page — jacket, excerpt, a printer's "
            "note — and the catalog is a shelf, not a grid of products. Search is quiet; browsing "
            "is the point. We built the catalog in Flask with Markdown entries the editors can "
            "file themselves, and a visual system that can hold a letterpress scan without shouting."
        ),
        outcome=(
            "Direct orders held steady while the quality of unsolicited submissions rose. Writers "
            "began citing specific titles in their cover letters. The press finally has a site they "
            "are willing to print the address of on a colophon."
        ),
        stack=("Flask", "Markdown catalog", "Custom type", "SQLite lists"),
        quote="At last a site that treats books as books.",
        attribution="Publisher, Harbor Press",
    ),
]


def get_study(slug: str) -> CaseStudy | None:
    return next((item for item in WORK if item.slug == slug), None)


def neighboring_studies(slug: str) -> tuple[CaseStudy | None, CaseStudy | None]:
    index = next((i for i, item in enumerate(WORK) if item.slug == slug), None)
    if index is None:
        return None, None
    previous_item = WORK[index - 1] if index > 0 else None
    next_item = WORK[index + 1] if index + 1 < len(WORK) else None
    return previous_item, next_item
