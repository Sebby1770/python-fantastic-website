import sqlite3
import json

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
    app = create_app({"FORCE_HTTPS": True})

    with app.test_client() as client:
        response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
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


def test_metrics_endpoint_can_require_bearer_token(tmp_path):
    app = create_app({"CONTACT_DB_PATH": str(tmp_path / "contacts.sqlite3"), "METRICS_TOKEN": "secret"})

    with app.test_client() as client:
        denied = client.get("/metrics")
        allowed = client.get("/metrics", headers={"Authorization": "Bearer secret"})

    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_admin_contacts_return_privacy_preserving_summaries(tmp_path):
    app = create_app(
        {
            "CONTACT_DB_PATH": str(tmp_path / "contacts.sqlite3"),
            "CONTACT_RATE_LIMIT": 20,
            "ADMIN_TOKEN": "admin-secret",
        }
    )

    with app.test_client() as client:
        client.post(
            "/contact",
            json={
                "name": "Grace Hopper",
                "email": "grace@example.com",
                "message": "I need a production launch system.",
            },
        )
        denied = client.get("/admin/contacts")
        allowed = client.get("/admin/contacts", headers={"Authorization": "Bearer admin-secret"})

    payload = allowed.get_json()
    assert denied.status_code == 401
    assert allowed.status_code == 200
    assert payload["count"] == 1
    assert payload["contacts"][0]["name"] == "Grace Hopper"
    assert "email_hash_prefix" in payload["contacts"][0]
    assert "grace@example.com" not in str(payload)


def test_api_discovery_routes_render():
    app = create_app()

    with app.test_client() as client:
        status = client.get("/api/status")
        changelog = client.get("/api/changelog")
        integrations = client.get("/api/integrations")
        openapi = client.get("/openapi.json")

    assert status.status_code == 200
    assert status.get_json()["version"]
    assert "vercel" in status.get_json()["features"]
    assert changelog.get_json()["entries"][0]["version"] == "2.3.0"
    assert integrations.get_json()["vercel"]["configured"] is True
    assert openapi.get_json()["openapi"] == "3.1.0"


def test_contact_can_sync_privacy_payload_to_supabase(tmp_path, monkeypatch):
    calls = []

    class FakeResponse:
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse()

    monkeypatch.setattr("app.urlopen", fake_urlopen)
    app = create_app(
        {
            "CONTACT_DB_PATH": str(tmp_path / "contacts.sqlite3"),
            "CONTACT_RATE_LIMIT": 20,
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SECRET_KEY": "sb_secret_test",
            "SUPABASE_CONTACT_TABLE": "asteria_contact_submissions",
            "SUPABASE_TIMEOUT_SECONDS": 1,
        }
    )

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
    assert len(calls) == 1
    request, timeout = calls[0]
    body = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "https://example.supabase.co/rest/v1/asteria_contact_submissions"
    assert timeout == 1
    assert body["name"] == "Ada Lovelace"
    assert body["email_hash"] != "ada@example.com"
    assert "ada@example.com" not in request.data.decode("utf-8")


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
