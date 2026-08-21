# Asteria Studio

A polished Python-powered website built with Flask, responsive HTML/CSS, a working contact endpoint, local generated PNG assets, and route tests.

Version 2 adds Studio Lab, case study pages, contact rate limiting, and a GitHub Pages static freeze.

Live: [https://sebby1770.github.io/python-fantastic-website/](https://sebby1770.github.io/python-fantastic-website/)

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/make_assets.py
flask --app app run --debug
```

Then open `http://127.0.0.1:5000`.

- Home: `/`
- Studio Lab: `/lab`
- Case studies: `/work/northline`, `/work/meridian`, `/work/cobalt-room`
- Health: `/health`

## Test

```bash
pytest
```

## GitHub Pages freeze

Render the site into `docs/` with relative asset paths (needed for project Pages):

```bash
python scripts/freeze.py
```

That writes `docs/index.html`, `docs/lab/`, `docs/work/<slug>/`, copies `css/`, `js/`, and `img/`, and adds `docs/.nojekyll`. Studio Lab on Pages is driven by `docs/js/lab.js` (and `docs/lab.js`), which mirrors `studio.py` (SHA-256 seed, the same HSL palette, WCAG contrast, major-third type scale).

The Pages site is served from `https://sebby1770.github.io/python-fantastic-website/`. Contact POST still requires the Flask app; the static freeze is the marketing site.

## Project structure

```text
app.py                 Flask application factory and routes
studio.py              Palette, contrast, and type-scale tools
templates/             Home, lab, case study, and 404 templates
static/css/styles.css  Responsive visual system
static/js/main.js      Navigation and contact form behavior
static/js/lab.js       Client-side Studio Lab (matches studio.py)
scripts/make_assets.py Local PNG asset generator
scripts/freeze.py      Static export into docs/
tests/                 Route, lab, and freeze tests
docs/                  Frozen GitHub Pages site
```
