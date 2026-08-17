from app import create_app


def test_sitemap_contains_key_routes():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/sitemap.xml")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for path in (
        "/",
        "/work",
        "/work/northline",
        "/work/harbor-press",
        "/journal",
        "/journal/color-as-architecture",
        "/about",
        "/contact",
    ):
        assert path in body
    assert "/studio" not in body


def test_rss_contains_a_post_title():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/journal/feed.xml")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Server-rendered is not a compromise" in body
    assert "Color as architecture" in body


def test_robots_points_at_sitemap():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/robots.txt")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Sitemap:" in body
    assert "/sitemap.xml" in body
    assert "Disallow: /studio" in body
