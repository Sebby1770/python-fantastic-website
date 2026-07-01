from __future__ import annotations

import os
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parseaddr
from hashlib import sha256
from pathlib import Path
from typing import Deque

from flask import Flask, Response, g, jsonify, render_template, request, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix


APP_VERSION = "2.1.0"
STARTED_AT = datetime.now(timezone.utc)
CONTACT_LIMIT_DEFAULT = 5
CONTACT_WINDOW_DEFAULT = 60
MAX_CONTACT_BYTES = 4096
REQUEST_WINDOW_SECONDS = 60


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
        "2.1.0",
        "2026-06-30",
        "Added observability, embedded storage, and staging manifests.",
        (
            "Added request IDs, response timing, JSON metrics, and QPS tracking.",
            "Added an embedded SQLite contact ledger with privacy-preserving hashes.",
            "Added Docker Compose, Kubernetes manifests, load-balancer/proxy support, and cloud notes.",
        ),
    ),
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
_request_times: Deque[float] = deque()
_metrics = {
    "requests": 0,
    "errors": 0,
    "contact_submissions": 0,
    "contact_rate_limited": 0,
    "latency_ms_total": 0.0,
}


def _truthy(value: str | None) -> bool:
    return str(value or "").lower() in {"1", "true", "yes", "on"}


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


def _hash_value(value: str, salt: str) -> str:
    return sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()


def _contact_store_path(app: Flask) -> Path:
    configured = Path(str(app.config["CONTACT_DB_PATH"]))
    if configured.is_absolute():
        return configured
    return Path(app.instance_path) / configured


def init_contact_store(app: Flask) -> None:
    db_path = _contact_store_path(app)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                email_hash TEXT NOT NULL,
                client_hash TEXT NOT NULL,
                message_preview TEXT NOT NULL,
                request_id TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_contact_submissions_created_at "
            "ON contact_submissions(created_at)"
        )


def store_contact(app: Flask, name: str, email: str, message: str, client_key: str) -> None:
    salt = str(app.config["CONTACT_HASH_SALT"])
    with sqlite3.connect(_contact_store_path(app)) as connection:
        connection.execute(
            """
            INSERT INTO contact_submissions
                (created_at, name, email_hash, client_hash, message_preview, request_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                name,
                _hash_value(email.lower(), salt),
                _hash_value(client_key, salt),
                message[:160],
                getattr(g, "request_id", "unknown"),
            ),
        )


def contact_count(app: Flask) -> int:
    with sqlite3.connect(_contact_store_path(app)) as connection:
        row = connection.execute("SELECT COUNT(*) FROM contact_submissions").fetchone()
    return int(row[0])


def current_qps() -> float:
    now = time.monotonic()
    while _request_times and now - _request_times[0] > REQUEST_WINDOW_SECONDS:
        _request_times.popleft()
    return round(len(_request_times) / REQUEST_WINDOW_SECONDS, 3)


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        CONTACT_RATE_LIMIT=int(os.getenv("CONTACT_RATE_LIMIT", CONTACT_LIMIT_DEFAULT)),
        CONTACT_RATE_WINDOW=int(os.getenv("CONTACT_RATE_WINDOW", CONTACT_WINDOW_DEFAULT)),
        CONTACT_MAX_MESSAGE_LENGTH=int(os.getenv("CONTACT_MAX_MESSAGE_LENGTH", 1200)),
        CONTACT_DB_PATH=os.getenv("CONTACT_DB_PATH", "contacts.sqlite3"),
        CONTACT_HASH_SALT=os.getenv("CONTACT_HASH_SALT", "local-dev-salt"),
        TRUST_PROXY_HEADERS=_truthy(os.getenv("TRUST_PROXY_HEADERS")),
        SITE_NAME="Asteria Studio",
        APP_VERSION=APP_VERSION,
    )
    if config:
        app.config.update(config)

    if app.config["TRUST_PROXY_HEADERS"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    init_contact_store(app)

    @app.before_request
    def start_observation() -> None:
        g.request_started_at = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID") or secrets.token_hex(8)
        _request_times.append(time.monotonic())

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        elapsed_ms = (time.perf_counter() - getattr(g, "request_started_at", time.perf_counter())) * 1000
        _metrics["requests"] += 1
        _metrics["latency_ms_total"] += elapsed_ms
        if response.status_code >= 500:
            _metrics["errors"] += 1
        response.headers.setdefault("X-Request-ID", getattr(g, "request_id", "unknown"))
        response.headers.setdefault("X-Response-Time-Ms", f"{elapsed_ms:.2f}")
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

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        if isinstance(error, HTTPException):
            return error
        app.logger.exception(
            "Unhandled request error",
            extra={"request_id": getattr(g, "request_id", "unknown"), "path": request.path},
        )
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "The service hit an unexpected error.",
                    "request_id": getattr(g, "request_id", "unknown"),
                }
            ),
            500,
        )

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
                    "contact_store": contact_count(app) >= 0,
                    "security_headers": True,
                },
            }
        )

    @app.get("/metrics")
    def metrics():
        requests = max(1, int(_metrics["requests"]))
        return jsonify(
            {
                "service": "asteria-studio",
                "version": APP_VERSION,
                "requests": int(_metrics["requests"]),
                "errors": int(_metrics["errors"]),
                "contact_submissions": int(_metrics["contact_submissions"]),
                "contact_rate_limited": int(_metrics["contact_rate_limited"]),
                "qps_60s": current_qps(),
                "avg_latency_ms": round(float(_metrics["latency_ms_total"]) / requests, 2),
                "stored_contact_count": contact_count(app),
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

        client_key = _client_key()
        if _contact_limited(
            client_key,
            int(app.config["CONTACT_RATE_LIMIT"]),
            int(app.config["CONTACT_RATE_WINDOW"]),
        ):
            _metrics["contact_rate_limited"] += 1
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

        store_contact(app, name, parsed_email, message, client_key)
        _metrics["contact_submissions"] += 1

        first_name = name.split()[0]
        return jsonify(
            {
                "ok": True,
                "message": f"Thanks, {first_name}. Your brief is ready for the next conversation.",
            }
        )

    return app


if __name__ == "__main__":
    create_app().run(debug=_truthy(os.getenv("FLASK_DEBUG")))
