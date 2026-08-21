# Changelog

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
