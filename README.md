# Asteria Studio

A polished Python-powered website built with Flask, responsive HTML/CSS, local generated PNG assets, and route tests. The refresh adds launch-readiness features inspired by production infrastructure basics: Docker staging, CI, status probes, security headers, rate limiting, robots, sitemap, and a visible changelog.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/make_assets.py
flask --app app run --debug
```

Then open `http://127.0.0.1:5000`.

## Production-minded endpoints

- `/health` - lightweight liveness probe.
- `/ready` - readiness payload with version, uptime, and enabled checks.
- `/robots.txt` - crawler policy with sitemap URL.
- `/sitemap.xml` - crawlable public route inventory.
- `/contact` - JSON/form endpoint with payload caps, email validation, and per-client rate limiting.

Optional environment variables:

```bash
CONTACT_RATE_LIMIT=5
CONTACT_RATE_WINDOW=60
CONTACT_MAX_MESSAGE_LENGTH=1200
```

## Docker

```bash
docker build -t asteria-studio .
docker run --rm -p 5000:5000 asteria-studio
```

## Test

```bash
pytest
```

## Project structure

```text
app.py                 Flask application factory and routes
templates/index.html   Main page template
static/css/styles.css  Responsive visual system
static/js/main.js      Navigation and contact form behavior
scripts/make_assets.py Local PNG asset generator
tests/test_app.py      Route and endpoint tests
Dockerfile             Containerized Flask runtime
.github/workflows/ci.yml GitHub Actions checks
CHANGELOG.md           Versioned change log
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
