from app import CONTACT_RATE_LIMIT, JOURNAL, create_app
from studio import TYPE_RATIOS, css_variables, palette_from_seed, type_scale


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
    assert 'href="/journal"' in html
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
    assert "AAA" in html
    assert 'name="ratio"' in html
    assert 'value="major-third"' in html
    assert css_variables(palette).splitlines()[0] in html
    assert "Foreground" in html
    assert "Copy" in html


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


def test_lab_ratio_query_changes_type_scale():
    app = create_app()
    fifth = type_scale(ratio=TYPE_RATIOS["perfect-fifth"])

    with app.test_client() as client:
        response = client.get("/lab?ratio=perfect-fifth")
        fallback = client.get("/lab?ratio=not-a-ratio")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'value="perfect-fifth"' in html
    assert "121.5px" in html
    for size in fifth:
        label = f"{int(size)}px" if size == int(size) else f"{size}px"
        assert label in html
    assert fallback.status_code == 200
    assert "48.83px" in fallback.get_data(as_text=True)


def test_journal_index_and_posts_render():
    app = create_app()

    with app.test_client() as client:
        index = client.get("/journal")
        missing = client.get("/journal/not-a-note")
        posts = {post.slug: client.get(f"/journal/{post.slug}") for post in JOURNAL}

    assert index.status_code == 200
    html = index.get_data(as_text=True)
    assert "Journal" in html
    for post in JOURNAL:
        assert post.title in html
        assert f'href="/journal/{post.slug}"' in html
        article = posts[post.slug]
        assert article.status_code == 200
        article_html = article.get_data(as_text=True)
        assert post.title in article_html
        assert post.dek in article_html
        assert post.body[0] in article_html
    assert missing.status_code == 404


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
