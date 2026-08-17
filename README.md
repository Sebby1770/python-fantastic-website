# Asteria Studio

An editorial Flask site for a small digital practice. Version 2.1 is a searchable multi-page studio: selected work, a markdown journal with a reading path, a dedicated brief, and a token-protected inquiry inbox.

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
| `ASTERIA_STUDIO_TOKEN` | Shared secret for `GET /studio` and `GET /studio.csv`. If unset, the inbox returns 404. |
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

## Search

`GET /search?q=` looks through case studies (name, summary, problem, approach, category) and journal posts (title, dek, body). Title hits rank above dek or summary, which rank above body copy. An empty query shows a prompt rather than every document. Every page carries a header field that submits to `/search`.

## Studio inbox

`POST /contact` validates a brief and stores it in SQLite. It does not send email.

The form includes a visually hidden `website` field. If that honeypot is filled, the endpoint still returns the usual thanks JSON and does not insert a row.

`GET /studio` lists inquiries when the request presents `ASTERIA_STUDIO_TOKEN` as `X-Studio-Token` or `?token=`. The page can search name, email, and message, and filter by status. Archive a row with `POST /studio/<id>/archive`, restore it with `POST /studio/<id>/unarchive`, and keep desk notes with `POST /studio/<id>/notes`. `GET /studio.csv` exports the same set with the same token. If the token is not configured, those routes are indistinguishable from a missing page.

Contact submissions are rate-limited in memory: five per IP every ten minutes.

## Content authoring

### Case studies

Work lives in `asteria/catalog.py` as `WORK`. Each study needs a slug, folio number, problem, approach, outcome, stack, and pull quote. Add a PNG under `static/img/` (see `scripts/make_assets.py`) and the study appears on `/`, `/work`, and `/sitemap.xml`. `/work?category=` filters the folio by the study's category.

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

Restart, or wait for the process to reload, after adding a file. The index, RSS feed (`/journal/feed.xml`), and sitemap pick the post up automatically. Detail pages show reading time, previous/next notes, and two other essays.

## Project structure

```text
app.py                 Flask entry (`create_app` lives in asteria/)
asteria/               Application factory, routes, catalog, journal, search, SQLite
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
| `/work`, `/work/<slug>` | Folio index (optional `?category=`) and case studies |
| `/journal`, `/journal/<slug>` | Essays |
| `/search` | Folio and journal search (`?q=`) |
| `/about` | Studio note, principles, stack |
| `/contact` | Dedicated brief |
| `/contact/thanks` | Optional confirmation for non-JS submits |
| `/studio` | Token-protected inbox |
| `/studio.csv` | Token-protected CSV export |
| `/health` | `{ok, service, version}` |
| `/sitemap.xml`, `/robots.txt`, `/journal/feed.xml` | Discovery |
