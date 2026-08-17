# Changelog

## 2.1.0 — 2026-08-17

The studio becomes searchable, the journal grows a reading path, and the inbox gets tools. Paper, teal, coral, and gold stay in their rooms.

### Added

- Site search at `GET /search?q=` over case studies and journal posts, with a header field on every page
- Work index category chips (`/work?category=`) drawn from the folio
- Journal reading time, previous/next notes, and two related essays
- Studio inbox search, status filter, CSV export (`GET /studio.csv`), notes, and unarchive
- Contact honeypot field `website` (filled submissions return thanks and are not stored)
- Optional `/contact/thanks` page for non-JavaScript submits
- Open Graph and Twitter tags on the shared base; Organization JSON-LD on home; Article JSON-LD on journal essays

### Changed

- Health `version` is now `2.1.0`

## 2.0.0 — 2026-08-17

Asteria Studio becomes a multi-page practice site. The paper/teal/coral/gold system stays; the one-pager does not.

### Added

- Shared Jinja base with skip link, header, footer, and mobile navigation on every page
- Work index and case studies for Northline, Meridian, Cobalt Room, and Harbor Press
- Markdown journal with index, essay pages, and `/journal/feed.xml`
- About page (studio note, principles, stack)
- Dedicated `/contact` brief alongside the homepage form
- Optional brief fields: project type, budget, timeline
- SQLite inquiry store at `data/inquiries.db`
- Token-protected `/studio` inbox and archive action
- In-memory contact rate limit (5 / 10 minutes / IP)
- Dark theme via CSS variables, `prefers-color-scheme`, and a persisted toggle
- `/sitemap.xml` and `/robots.txt`
- Custom 404
- Health payload now includes `version`
- Dockerfile (Gunicorn on port 5000) and GitHub Actions CI for Python 3.11 and 3.12

### Changed

- Application factory lives in the `asteria` package; `app.py` remains the Flask entry
- Homepage work cards link through to case studies
- `pyproject.toml` project metadata set to 2.0.0
