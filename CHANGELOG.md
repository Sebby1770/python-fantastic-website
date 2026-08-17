# Changelog

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
