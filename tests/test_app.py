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
    assert "/work/northline" in html
    assert "Skip to content" in html


def test_health_endpoint():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["service"] == "asteria-studio"
    assert payload["version"] == "2.0.0"


def test_contact_requires_fields():
    app = create_app()

    with app.test_client() as client:
        response = client.post("/contact", json={"name": "Ada"})

    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_contact_rejects_invalid_email(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "inquiries.db")})

    with app.test_client() as client:
        response = client.post(
            "/contact",
            json={
                "name": "Ada Lovelace",
                "email": "not-an-email",
                "message": "I need a launch site for a Python product.",
            },
        )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_contact_accepts_valid_payload():
    app = create_app()

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


def test_contact_persists_a_row(tmp_path):
    database = tmp_path / "inquiries.db"
    app = create_app({"DATABASE": str(database)})

    with app.test_client() as client:
        response = client.post(
            "/contact",
            json={
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "message": "I need a launch site for a Python product.",
                "budget": "$15–40k",
                "timeline": "This quarter",
                "project_type": "Product site",
            },
        )

    assert response.status_code == 200
    assert database.exists()
    with sqlite3.connect(database) as conn:
        row = conn.execute(
            """
            SELECT name, email, message, budget, timeline, project_type, status
            FROM inquiries
            """
        ).fetchone()
    assert row == (
        "Ada Lovelace",
        "ada@example.com",
        "I need a launch site for a Python product.",
        "$15–40k",
        "This quarter",
        "Product site",
        "new",
    )


def test_contact_rate_limit_trips(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "inquiries.db")})
    payload = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "message": "I need a launch site for a Python product.",
    }

    with app.test_client() as client:
        codes = [client.post("/contact", json=payload).status_code for _ in range(6)]

    assert codes[:5] == [200, 200, 200, 200, 200]
    assert codes[5] == 429


def test_studio_404_without_token(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "inquiries.db")})

    with app.test_client() as client:
        missing = client.get("/studio")
        guessed = client.get("/studio?token=guess")
        headered = client.get("/studio", headers={"X-Studio-Token": "guess"})

    assert missing.status_code == 404
    assert guessed.status_code == 404
    assert headered.status_code == 404
    assert "not in the folio" in missing.get_data(as_text=True).lower()


def test_studio_200_with_token_lists_inquiry(tmp_path):
    app = create_app(
        {
            "DATABASE": str(tmp_path / "inquiries.db"),
            "STUDIO_TOKEN": "secret-token",
        }
    )

    with app.test_client() as client:
        client.post(
            "/contact",
            json={
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "message": "I need a launch site for a Python product.",
            },
        )
        via_query = client.get("/studio?token=secret-token")
        via_header = client.get("/studio", headers={"X-Studio-Token": "secret-token"})
        denied = client.get("/studio?token=wrong")

    assert via_query.status_code == 200
    assert via_header.status_code == 200
    assert denied.status_code == 404
    html = via_query.get_data(as_text=True)
    assert "Ada Lovelace" in html
    assert "I need a launch site for a Python product." in html


def test_studio_archives_inquiry(tmp_path):
    database = tmp_path / "inquiries.db"
    app = create_app({"DATABASE": str(database), "STUDIO_TOKEN": "secret-token"})

    with app.test_client() as client:
        client.post(
            "/contact",
            json={
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "message": "Ready to archive.",
            },
        )
        response = client.post(
            "/studio/1/archive",
            headers={"X-Studio-Token": "secret-token"},
            json={},
        )

    assert response.status_code == 200
    assert response.get_json()["status"] == "archived"
    with sqlite3.connect(database) as conn:
        status = conn.execute("SELECT status FROM inquiries WHERE id = 1").fetchone()[0]
    assert status == "archived"
