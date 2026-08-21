from app import CONTACT_RATE_LIMIT, create_app
from studio import palette_from_seed


def test_homepage_renders_brand_and_sections():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Asteria Studio" in html
    assert "Selected work" in html
    assert "Start the conversation" in html
    assert 'href="/lab"' in html
    assert 'href="/work/northline"' in html
    assert 'href="/work/meridian"' in html
    assert 'href="/work/cobalt-room"' in html


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


def test_contact_rate_limit_per_ip():
    app = create_app()
    payload = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "message": "I need a launch site for a Python product.",
    }

    with app.test_client() as client:
        for _ in range(CONTACT_RATE_LIMIT):
            allowed = client.post(
                "/contact",
                json=payload,
                headers={"X-Forwarded-For": "203.0.113.10"},
            )
            assert allowed.status_code == 200

        limited = client.post(
            "/contact",
            json=payload,
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
        other_ip = client.post(
            "/contact",
            json=payload,
            headers={"X-Forwarded-For": "203.0.113.20"},
        )

    assert limited.status_code == 429
    assert limited.get_json()["ok"] is False
    assert other_ip.status_code == 200


def test_lab_renders_palette_and_type_scale():
    app = create_app()
    seed = "asteria"
    palette = palette_from_seed(seed)

    with app.test_client() as client:
        response = client.get("/lab")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Studio Lab" in html
    assert 'name="seed"' in html
    assert seed in html
    for color in palette:
        assert color in html
    assert "16px" in html
    assert "AA" in html


def test_lab_seed_changes_palette():
    app = create_app()

    with app.test_client() as client:
        first = client.get("/lab?seed=northline")
        second = client.get("/lab?seed=meridian")

    assert first.status_code == 200
    assert second.status_code == 200
    first_html = first.get_data(as_text=True)
    second_html = second.get_data(as_text=True)
    assert first_html != second_html
    assert palette_from_seed("northline")[0] in first_html
    assert palette_from_seed("meridian")[0] in second_html


def test_work_case_studies_render():
    app = create_app()

    with app.test_client() as client:
        northline = client.get("/work/northline")
        meridian = client.get("/work/meridian")
        cobalt = client.get("/work/cobalt-room")
        missing = client.get("/work/not-a-project")

    assert northline.status_code == 200
    assert "Northline" in northline.get_data(as_text=True)
    assert meridian.status_code == 200
    assert "Meridian" in meridian.get_data(as_text=True)
    assert cobalt.status_code == 200
    assert "Cobalt Room" in cobalt.get_data(as_text=True)
    assert missing.status_code == 404
