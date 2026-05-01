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
    assert response.get_json() == {"ok": True, "service": "asteria-studio"}


def test_contact_requires_fields():
    app = create_app()

    with app.test_client() as client:
        response = client.post("/contact", json={"name": "Ada"})

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
