# Asteria Studio

A polished Python-powered website built with Flask, responsive HTML/CSS, a working contact endpoint, local generated PNG assets, and route tests.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/make_assets.py
flask --app app run --debug
```

Then open `http://127.0.0.1:5000`.

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
```
