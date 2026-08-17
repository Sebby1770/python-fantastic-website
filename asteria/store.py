"""SQLite inquiry store. Schema lives in data/inquiries.db by default."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from flask import Flask

SCHEMA = """
CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    budget TEXT,
    timeline TEXT,
    project_type TEXT,
    status TEXT NOT NULL DEFAULT 'new'
);
"""


def database_path(app: Flask) -> Path:
    return Path(app.config["DATABASE"])


def connect(app: Flask) -> sqlite3.Connection:
    path = database_path(app)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def get_db(app: Flask) -> Iterator[sqlite3.Connection]:
    conn = connect(app)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def insert_inquiry(
    app: Flask,
    *,
    name: str,
    email: str,
    message: str,
    budget: str = "",
    timeline: str = "",
    project_type: str = "",
) -> int:
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with get_db(app) as conn:
        cursor = conn.execute(
            """
            INSERT INTO inquiries (
                created_at, name, email, message, budget, timeline, project_type, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'new')
            """,
            (created_at, name, email, message, budget, timeline, project_type),
        )
        return int(cursor.lastrowid)


def list_inquiries(app: Flask) -> list[sqlite3.Row]:
    with get_db(app) as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, name, email, message, budget, timeline,
                   project_type, status
            FROM inquiries
            ORDER BY
                CASE status WHEN 'new' THEN 0 ELSE 1 END,
                datetime(created_at) DESC,
                id DESC
            """
        ).fetchall()
        return list(rows)


def archive_inquiry(app: Flask, inquiry_id: int) -> bool:
    with get_db(app) as conn:
        cursor = conn.execute(
            "UPDATE inquiries SET status = 'archived' WHERE id = ? AND status != 'archived'",
            (inquiry_id,),
        )
        return cursor.rowcount > 0
