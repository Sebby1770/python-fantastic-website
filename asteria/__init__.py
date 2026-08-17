"""Asteria Studio application factory."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from asteria.catalog import VERSION
from asteria.limiter import RateLimiter

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = ROOT / "data" / "inquiries.db"


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.config.from_mapping(
        VERSION=VERSION,
        DATABASE=os.environ.get("ASTERIA_DATABASE", str(DEFAULT_DATABASE)),
        STUDIO_TOKEN=os.environ.get("ASTERIA_STUDIO_TOKEN", ""),
        RATE_LIMIT=5,
        RATE_WINDOW=600,
    )
    if test_config:
        app.config.update(test_config)

    app.extensions["rate_limiter"] = RateLimiter(
        max_requests=int(app.config.get("RATE_LIMIT", 5)),
        window_seconds=int(app.config.get("RATE_WINDOW", 600)),
    )

    from asteria.routes import register_routes

    register_routes(app)
    return app
