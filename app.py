"""Asteria Studio — Flask entry so `flask --app app` keeps working."""

from __future__ import annotations

from asteria import create_app

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
