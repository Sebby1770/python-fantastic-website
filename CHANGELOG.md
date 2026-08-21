# Changelog

## [2.2.0] - 2026-08-21

### Added

- `best_on_ink`, `scss_map`, and `recommend_body` in `studio.py`
- Studio Lab callouts for the best-on-ink swatch and a recommended body pair, plus a copyable SCSS map
- `GET /lab.json?seed=` JSON export (`seed`, `palette`, `ink`, `css`, `scss`, `best_on_ink`)
- Frozen `docs/sitemap.xml` and `docs/robots.txt` for GitHub Pages

### Changed

- Print stylesheet hides header nav, the menu toggle, and the contact form so work and journal articles stay readable
- README and project metadata at 2.2.0

## [2.1.0] - 2026-08-21

### Added

- WCAG AAA checks (`passes_aaa`), CSS variable export, pairing table, and named type ratios in `studio.py`
- Studio Lab ratio select (GET `ratio`, default major-third), AAA badges, pairing table, and copyable CSS tokens
- Journal index at `/journal` with two notes, plus `/journal/<slug>` article pages
- Frozen `docs/journal/` (index at depth 1, posts at depth 2)

### Changed

- Header navigation now includes Journal
- README and project metadata at 2.1.0

## [2.0.0] - 2026-08-21

### Added

- Studio Lab (`studio.py`) with deterministic seed palettes, WCAG contrast, and a major-third type scale
- `/lab` for live palette and type-scale previews, plus a static `lab.js` twin for GitHub Pages
- Case study routes at `/work/northline`, `/work/meridian`, and `/work/cobalt-room`
- In-memory per-IP contact rate limit (8 briefs / 10 minutes) with `429` JSON
- Static freeze into `docs/` via `scripts/freeze.py`, including `.nojekyll`
- CI on Python 3.11 and 3.12, plus an optional GitHub Pages workflow

### Changed

- Header navigation now includes Lab and work case links
- Work cards link through to case study pages
- README documents the lab, case studies, freeze, and Pages URL
