from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from email.utils import parseaddr
from threading import Lock
from time import monotonic

from flask import Flask, abort, jsonify, render_template, request

from studio import (
    INK,
    TYPE_RATIOS,
    contrast_ratio,
    css_variables,
    palette_from_seed,
    pairing_table,
    passes_aa,
    passes_aaa,
    type_scale,
)

CONTACT_RATE_LIMIT = 8
CONTACT_RATE_WINDOW = 600


@dataclass(frozen=True)
class Stat:
    value: str
    label: str


@dataclass(frozen=True)
class WorkItem:
    name: str
    slug: str
    category: str
    summary: str
    image: str
    year: str
    client: str
    role: str
    challenge: str
    approach: str
    outcome: str
    highlights: tuple[str, ...]


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
class Swatch:
    hex: str
    ratio: float
    aa: bool
    aa_large: bool
    aaa: bool
    aaa_large: bool


@dataclass(frozen=True)
class JournalPost:
    title: str
    slug: str
    date: str
    dek: str
    body: tuple[str, ...]


class RateLimiter:
    def __init__(self, max_hits: int, window_seconds: float) -> None:
        self.max_hits = max_hits
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_hits:
                return False
            bucket.append(now)
            return True


STATS = [
    Stat("47", "launches shipped"),
    Stat("1.2s", "typical first load"),
    Stat("96%", "client retention"),
]

WORK = [
    WorkItem(
        "Northline",
        "northline",
        "Brand platform",
        "A high-trust launch system for a technical consulting firm.",
        "img/work-northline.png",
        "2025",
        "Northline Advisory",
        "Brand, site, and launch",
        "The firm needed a public presence as precise as the work behind closed doors. "
        "The previous site buried the offer in generic language, slow templates, and a "
        "contact path that asked for too much too soon.",
        "We shaped a brand platform in Flask: a tight visual system, a high-trust narrative, "
        "and pages that load as quickly as the argument they make. Generated studies keep the "
        "repository portable without depending on a separate asset pipeline.",
        "A launch system that presents Northline as a serious partner—clear services, selected "
        "work, and a direct path into conversation.",
        ("High-trust brand language", "Sub-2s first load target", "One system for brand and site"),
    ),
    WorkItem(
        "Meridian",
        "meridian",
        "Product website",
        "A conversion-focused site with clear paths for buyers and partners.",
        "img/work-meridian.png",
        "2025",
        "Meridian",
        "Product site and conversion",
        "Buyers and partners were landing in the same funnel. The product story was strong, "
        "but the next step was not, and comparison pages repeated the same pitch instead of "
        "routing intent.",
        "We rebuilt the information architecture around two audiences, with conversion paths "
        "that stay specific: proof for buyers, context for partners, and a contact brief that "
        "arrives ready for the next conversation.",
        "A product website that routes intent without diluting the story, and a visual system "
        "that can grow with the catalogue.",
        ("Split paths for buyers and partners", "Proof before pitch", "Contact that ships a brief"),
    ),
    WorkItem(
        "Cobalt Room",
        "cobalt-room",
        "Experience design",
        "A cinematic editorial presence for an intimate events venue.",
        "img/work-cobalt.png",
        "2024",
        "Cobalt Room",
        "Editorial site and atmosphere",
        "The room had atmosphere in person and a brochure online. Night photography fought a "
        "generic template, and the booking path felt like an inquiry form rather than an invitation.",
        "We treated the site as editorial experience design: cinematic pacing, a restrained "
        "palette, and copy that sounds like the room. The Flask build stays quiet so the images "
        "and type can carry the evening.",
        "A presence that feels like the venue—intimate, considered, and ready to book—without "
        "losing the operational clarity a small team needs.",
        ("Editorial pacing", "Cinematic stills in a quiet layout", "A booking path with manners"),
    ),
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

JOURNAL = [
    JournalPost(
        "Ink, paper, and the seven-to-one line",
        "ink-and-paper",
        "2026-08-21",
        "Why the studio measures every swatch against #101418, and why AAA is a different brief from AA.",
        (
            "The Asteria palette is paper, teal, sky, coral, and gold, held in place by ink. "
            "#101418 is dark enough to carry headlines and quiet enough to sit under a photograph. "
            "Every generated swatch is asked the same first question: can it speak against that ink?",
            "AA is the floor we will not go below for body copy. It is 4.5:1 for normal text and 3:1 "
            "for large type—enough for a caption, a chip, a label that still has to be read. "
            "AAA is a stricter brief: 7:1 for normal text, 4.5:1 when the type is large. "
            "The pairing table in Studio Lab now reports both, so a seed can be judged instead of guessed.",
            "Consecutive pairs matter as much as the ink test. A five-color ramp can look tuned in isolation "
            "and still fail when two neighbors are asked to sit on top of each other. "
            "If the coral cannot hold a line of type on the gold, the system is not finished.",
            "We export the result as CSS variables so the same tokens can move from the lab into a layout: "
            "--studio-1 through --studio-5, plus --studio-ink. Same seed, same five colors, same ink.",
        ),
    ),
    JournalPost(
        "A scale you can hear",
        "a-scale-you-can-hear",
        "2026-08-14",
        "Major thirds, perfect fifths, and the reason a marketing site should feel tuned.",
        (
            "Type is easier to trust when the sizes are related. A modular scale takes a base—16px here—"
            "and multiplies it by the same ratio at each step. The default in Studio Lab is a major third, "
            "1.25, which gives a ramp that can hold an eyebrow, a deck, a section title, and a display line "
            "without inventing a new size for each block.",
            "The other ratios in the lab are musical on purpose. A minor third (1.2) stays compact, useful "
            "when the page is already dense. A perfect fourth (1.333) opens more air between steps. "
            "A perfect fifth (1.5) is dramatic: fewer useful stops, but the large sizes feel like a poster.",
            "The point is not to worship the math. It is to keep the paper, teal, sky, coral, and gold "
            "from competing with type that was chosen at random. When the scale is consistent, the color "
            "can be quieter, and the site reads as one system instead of a stack of decisions.",
            "Pick a ratio, keep the seed, and the lab will show the sizes in place. The same numbers ship "
            "in Python and in the static twin, so a frozen GitHub Pages build does not drift from Flask.",
        ),
    ),
]


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or (request.remote_addr or "unknown")
    return request.remote_addr or "unknown"


def _lab_ratio(name: str | None) -> tuple[str, float]:
    key = (name or "major-third").strip() or "major-third"
    if key not in TYPE_RATIOS:
        key = "major-third"
    return key, TYPE_RATIOS[key]


def _ratio_label(name: str) -> str:
    label = name.replace("-", " ")
    return label[:1].upper() + label[1:]


def _lab_swatches(seed: str) -> list[Swatch]:
    swatches: list[Swatch] = []
    for color in palette_from_seed(seed):
        ratio = contrast_ratio(color, INK)
        swatches.append(
            Swatch(
                hex=color,
                ratio=ratio,
                aa=passes_aa(color, INK, large=False),
                aa_large=passes_aa(color, INK, large=True),
                aaa=passes_aaa(color, INK, large=False),
                aaa_large=passes_aaa(color, INK, large=True),
            )
        )
    return swatches


def create_app() -> Flask:
    app = Flask(__name__)
    limiter = RateLimiter(CONTACT_RATE_LIMIT, CONTACT_RATE_WINDOW)

    @app.context_processor
    def inject_nav() -> dict[str, object]:
        return {"nav_work": WORK}

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            stats=STATS,
            work=WORK,
            services=SERVICES,
            process=PROCESS,
        )

    @app.get("/lab")
    def lab():
        seed = (request.args.get("seed") or "asteria").strip() or "asteria"
        ratio_name, ratio = _lab_ratio(request.args.get("ratio"))
        palette = palette_from_seed(seed)
        return render_template(
            "lab.html",
            seed=seed,
            ink=INK,
            swatches=_lab_swatches(seed),
            scale=type_scale(ratio=ratio),
            ratio_name=ratio_name,
            ratio_label=_ratio_label(ratio_name),
            ratios=TYPE_RATIOS,
            pairings=pairing_table(palette),
            css_vars=css_variables(palette),
        )

    @app.get("/journal")
    def journal_index():
        return render_template("journal_index.html", posts=JOURNAL)

    @app.get("/journal/<slug>")
    def journal_detail(slug: str):
        post = next((entry for entry in JOURNAL if entry.slug == slug), None)
        if post is None:
            abort(404)
        others = [entry for entry in JOURNAL if entry.slug != slug]
        return render_template("journal.html", post=post, others=others)

    @app.get("/work/<slug>")
    def work_detail(slug: str):
        item = next((entry for entry in WORK if entry.slug == slug), None)
        if item is None:
            abort(404)
        related = [entry for entry in WORK if entry.slug != slug]
        return render_template("work.html", item=item, related=related)

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "service": "asteria-studio"})

    @app.post("/contact")
    def contact():
        if not limiter.allow(_client_ip()):
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "Too many briefs from this network. Please wait a few minutes and try again.",
                    }
                ),
                429,
            )

        payload = request.get_json(silent=True) or request.form
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip()
        message = str(payload.get("message", "")).strip()

        if not name or not email or not message:
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "Please add your name, email, and a short project note.",
                    }
                ),
                400,
            )

        parsed_email = parseaddr(email)[1]
        if "@" not in parsed_email or "." not in parsed_email.rsplit("@", 1)[-1]:
            return jsonify({"ok": False, "message": "Please enter a valid email address."}), 400

        first_name = name.split()[0]
        return jsonify(
            {
                "ok": True,
                "message": f"Thanks, {first_name}. Your brief is ready for the next conversation.",
            }
        )

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
