from __future__ import annotations

from dataclasses import dataclass
from email.utils import parseaddr

from flask import Flask, jsonify, render_template, request


@dataclass(frozen=True)
class Stat:
    value: str
    label: str


@dataclass(frozen=True)
class WorkItem:
    name: str
    category: str
    summary: str
    image: str


@dataclass(frozen=True)
class Service:
    title: str
    summary: str


@dataclass(frozen=True)
class ProcessStep:
    label: str
    title: str
    summary: str


STATS = [
    Stat("47", "launches shipped"),
    Stat("1.2s", "typical first load"),
    Stat("96%", "client retention"),
]

WORK = [
    WorkItem(
        "Northline",
        "Brand platform",
        "A high-trust launch system for a technical consulting firm.",
        "img/work-northline.png",
    ),
    WorkItem(
        "Meridian",
        "Product website",
        "A conversion-focused site with clear paths for buyers and partners.",
        "img/work-meridian.png",
    ),
    WorkItem(
        "Cobalt Room",
        "Experience design",
        "A cinematic editorial presence for an intimate events venue.",
        "img/work-cobalt.png",
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


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            stats=STATS,
            work=WORK,
            services=SERVICES,
            process=PROCESS,
        )

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "service": "asteria-studio"})

    @app.post("/contact")
    def contact():
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

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
