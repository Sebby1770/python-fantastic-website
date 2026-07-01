import sqlite3

from app import create_app


def test_homepage_renders_brand_and_sections():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Asteria Studio" in html
    assert "Selected work" in html
    assert "Start the conversation" in html


def test_health_endpoint():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert response.get_json()["service"] == "asteria-studio"
    assert "version" in response.get_json()


def test_ready_endpoint_reports_checks():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/ready")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["checks"]["security_headers"] is True
    assert payload["checks"]["contact_store"] is True


def test_public_routes_include_security_headers():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_robots_and_sitemap_render():
    app = create_app()

    with app.test_client() as client:
        robots = client.get("/robots.txt")
        sitemap = client.get("/sitemap.xml")

    assert robots.status_code == 200
    assert "Sitemap:" in robots.get_data(as_text=True)
    assert sitemap.status_code == 200
    assert "<urlset" in sitemap.get_data(as_text=True)


def test_contact_requires_fields():
    app = create_app()

    with app.test_client() as client:
        response = client.post("/contact", json={"name": "Ada"})

    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_contact_accepts_valid_payload():
    app = create_app({"CONTACT_RATE_LIMIT": 20})

    with app.test_client() as client:
        response = client.post(
            "/contact",
            json={
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "message": "I need a launch site for a Python product.",
            },
        )

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert "Ada" in response.get_json()["message"]


def test_contact_submission_is_stored_privately(tmp_path):
    db_path = tmp_path / "contacts.sqlite3"
    app = create_app({"CONTACT_DB_PATH": str(db_path), "CONTACT_RATE_LIMIT": 20})

    with app.test_client() as client:
        response = client.post(
            "/contact",
            json={
                "name": "Grace Hopper",
                "email": "grace@example.com",
                "message": "I need a production launch system.",
            },
        )

    assert response.status_code == 200
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT name, email_hash, message_preview FROM contact_submissions"
        ).fetchone()

    assert row[0] == "Grace Hopper"
    assert row[1] != "grace@example.com"
    assert "production launch" in row[2]


def test_metrics_endpoint_reports_qps_and_contacts(tmp_path):
    app = create_app({"CONTACT_DB_PATH": str(tmp_path / "contacts.sqlite3"), "CONTACT_RATE_LIMIT": 20})

    with app.test_client() as client:
        client.get("/")
        client.post(
            "/contact",
            json={
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "message": "I need a launch site for a Python product.",
            },
        )
        response = client.get("/metrics")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["requests"] >= 2
    assert payload["qps_60s"] > 0
    assert payload["stored_contact_count"] == 1


def test_contact_rate_limits_bursts():
    app = create_app({"CONTACT_RATE_LIMIT": 1, "CONTACT_RATE_WINDOW": 60})
    payload = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "message": "I need a launch site for a Python product.",
    }

    with app.test_client() as client:
        first = client.post("/contact", json=payload, environ_base={"REMOTE_ADDR": "203.0.113.10"})
        second = client.post("/contact", json=payload, environ_base={"REMOTE_ADDR": "203.0.113.10"})

    assert first.status_code == 200
    assert second.status_code == 429
