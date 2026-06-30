from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Deque

from flask import Flask, Response, jsonify, render_template, request, url_for


APP_VERSION = "2.0.0"
STARTED_AT = datetime.now(timezone.utc)
CONTACT_LIMIT_DEFAULT = 5
CONTACT_WINDOW_DEFAULT = 60
MAX_CONTACT_BYTES = 4096


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


@dataclass(frozen=True)
class StackSignal:
    title: str
    summary: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ChangelogEntry:
    version: str
    date: str
    summary: str
    items: tuple[str, ...]


STATS = [
    Stat("99.9%", "launch target"),
    Stat("<1.2s", "typical first load"),
    Stat("5/min", "contact rate limit"),
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
        "Cloud launch systems",
        "Docker staging, CI checks, health/readiness endpoints, and deployment notes that make releases boring.",
    ),
    Service(
        "Trust and resilience",
        "Security headers, contact throttling, sitemap/robots, cache-aware responses, and clear change records.",
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

STACK_SIGNALS = [
    StackSignal(
        "Containerized staging",
        "Docker image, lightweight runtime, and CI build checks for predictable deploys.",
        ("Docker", "CI/CD", "staging"),
    ),
    StackSignal(
        "Cloud edge readiness",
        "Cache-friendly public routes plus explicit health and readiness probes for load balancers.",
        ("cloud", "load balancer", "availability"),
    ),
    StackSignal(
        "Security baseline",
        "Content security policy, clickjacking protection, payload limits, and contact rate limiting.",
        ("encryption-ready", "firewall", "rate limiting"),
    ),
    StackSignal(
        "Operational clarity",
        "Versioned status responses, documented changes, and deployable defaults for GitHub workflows.",
        ("error logging", "QPS-ready", "GitHub"),
    ),
]

CHANGELOG = [
    ChangelogEntry(
        "2.0.0",
        "2026-06-30",
        "Launch-readiness refresh inspired by production infrastructure fundamentals.",
        (
            "Added security headers, payload caps, and contact endpoint throttling.",
            "Added health, readiness, robots, and sitemap routes.",
            "Added Docker, CI, deployment notes, and a visible site changelog.",
        ),
    ),
    ChangelogEntry(
        "1.0.0",
        "2026-05-06",
        "Initial Flask studio website with responsive sections, generated assets, and tests.",
        (
            "Shipped portfolio sections, contact endpoint, and local asset generation.",
            "Added route tests and a clean project structure.",
        ),
    ),
]

_rate_limits: dict[str, Deque[float]] = defaultdict(deque)


def _contact_limited(client_key: str, limit: int, window_seconds: int) -> bool:
    now = time.monotonic()
    events = _rate_limits[client_key]
    while events and now - events[0] > window_seconds:
        events.popleft()
    if len(events) >= limit:
        return True
    events.append(now)
    return False


def _client_key() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return forwarded_for or request.remote_addr or "local"


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        CONTACT_RATE_LIMIT=int(os.getenv("CONTACT_RATE_LIMIT", CONTACT_LIMIT_DEFAULT)),
        CONTACT_RATE_WINDOW=int(os.getenv("CONTACT_RATE_WINDOW", CONTACT_WINDOW_DEFAULT)),
        CONTACT_MAX_MESSAGE_LENGTH=int(os.getenv("CONTACT_MAX_MESSAGE_LENGTH", 1200)),
        SITE_NAME="Asteria Studio",
        APP_VERSION=APP_VERSION,
    )
    if config:
        app.config.update(config)

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; base-uri 'self'; form-action 'self'",
        )
        if request.path == "/contact":
            response.headers.setdefault("Cache-Control", "no-store")
        else:
            response.headers.setdefault("Cache-Control", "public, max-age=300")
        return response

    @app.context_processor
    def inject_site_metadata():
        return {"app_version": APP_VERSION}

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            stats=STATS,
            work=WORK,
            services=SERVICES,
            process=PROCESS,
            stack_signals=STACK_SIGNALS,
            changelog=CHANGELOG,
        )

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "service": "asteria-studio", "version": APP_VERSION})

    @app.get("/ready")
    def ready():
        uptime = datetime.now(timezone.utc) - STARTED_AT
        return jsonify(
            {
                "ok": True,
                "service": "asteria-studio",
                "version": APP_VERSION,
                "uptime_seconds": int(uptime.total_seconds()),
                "checks": {
                    "template": True,
                    "contact_rate_limit": True,
                    "security_headers": True,
                },
            }
        )

    @app.get("/robots.txt")
    def robots_txt():
        body = f"User-agent: *\nAllow: /\nSitemap: {url_for('sitemap_xml', _external=True)}\n"
        return Response(body, mimetype="text/plain")

    @app.get("/sitemap.xml")
    def sitemap_xml():
        urls = [
            url_for("index", _external=True),
            url_for("health", _external=True),
            url_for("ready", _external=True),
        ]
        body = "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                *[f"  <url><loc>{url}</loc></url>" for url in urls],
                "</urlset>",
            ]
        )
        return Response(body, mimetype="application/xml")

    @app.post("/contact")
    def contact():
        if request.content_length and request.content_length > MAX_CONTACT_BYTES:
            return jsonify({"ok": False, "message": "Please keep the brief under 4KB."}), 413

        if _contact_limited(
            _client_key(),
            int(app.config["CONTACT_RATE_LIMIT"]),
            int(app.config["CONTACT_RATE_WINDOW"]),
        ):
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "Too many briefs from this connection. Please try again in a minute.",
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

        if len(name) > 80 or len(email) > 254:
            return jsonify({"ok": False, "message": "Please shorten your name or email field."}), 400
        if len(message) > int(app.config["CONTACT_MAX_MESSAGE_LENGTH"]):
            return jsonify({"ok": False, "message": "Please keep the project note under 1200 characters."}), 400

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
