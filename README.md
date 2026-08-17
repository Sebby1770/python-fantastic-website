# Asteria Studio

An editorial Flask site for a small digital practice. Version 2 is a multi-page studio: selected work, markdown journal, a dedicated brief, and a token-protected inquiry inbox.

The visual system stays Asteria — paper, ink, teal, coral, gold — not a generic SaaS gradient.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/make_assets.py
flask --app app run --debug
```

Then open `http://127.0.0.1:5000`.

Optional environment:

| Variable | Purpose |
| --- | --- |
| `ASTERIA_STUDIO_TOKEN` | Shared secret for `GET /studio`. If unset, the inbox returns 404. |
| `ASTERIA_DATABASE` | SQLite path. Defaults to `data/inquiries.db`. |

```bash
export ASTERIA_STUDIO_TOKEN="a-long-random-string"
flask --app app run --debug
```

Open the inbox with the header `X-Studio-Token` or `?token=`.

## Test

```bash
pytest
```

## Docker

```bash
docker build -t asteria-studio .
docker run --rm -p 5000:5000 -e ASTERIA_STUDIO_TOKEN=a-long-random-string asteria-studio
```

The container serves Gunicorn on port 5000. Mount a volume over `/app/data` if you want inquiries to survive restarts.

## Studio inbox

`POST /contact` validates a brief and stores it in SQLite. It does not send email.

`GET /studio` lists inquiries when the request presents `ASTERIA_STUDIO_TOKEN` as `X-Studio-Token` or `?token=`. Archive a row with `POST /studio/<id>/archive` using the same token. If the token is not configured, the route is indistinguishable from a missing page.

Contact submissions are rate-limited in memory: five per IP every ten minutes.

## Content authoring

### Case studies

Work lives in `asteria/catalog.py` as `WORK`. Each study needs a slug, folio number, problem, approach, outcome, stack, and pull quote. Add a PNG under `static/img/` (see `scripts/make_assets.py`) and the study appears on `/`, `/work`, and `/sitemap.xml`.

### Journal

Essays are Markdown files in `content/journal/`:

```markdown
---
title: The title as it should be typeset
date: 2026-08-17
dek: One-sentence standfirst.
---

Paragraphs, lists, and `##` headings. The filename becomes the slug.
```

Restart, or wait for the process to reload, after adding a file. The index, RSS feed (`/journal/feed.xml`), and sitemap pick the post up automatically.

## Project structure

```text
app.py                 Flask entry (`create_app` lives in asteria/)
asteria/               Application factory, routes, catalog, journal, SQLite
content/journal/       Markdown essays
templates/             Shared base plus page templates
static/                CSS, JS, and generated PNGs
scripts/make_assets.py Local PNG asset generator
tests/                 Route, persistence, and feed tests
```

## Routes

| Path | Purpose |
| --- | --- |
| `/` | Home: hero, signals, work teaser, services, process, brief |
| `/work`, `/work/<slug>` | Folio index and case studies |
| `/journal`, `/journal/<slug>` | Essays |
| `/about` | Studio note, principles, stack |
| `/contact` | Dedicated brief |
| `/studio` | Token-protected inbox |
| `/health` | `{ok, service, version}` |
| `/sitemap.xml`, `/robots.txt`, `/journal/feed.xml` | Discovery |
