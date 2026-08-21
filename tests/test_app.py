from pytest import approx

from app import CONTACT_RATE_LIMIT, JOURNAL, create_app
from studio import (
    INK,
    TYPE_RATIOS,
    best_on_ink,
    closest_pair,
    contrast_ratio,
    css_variables,
    farthest_pair,
    json_tokens,
    lab_query,
    mix_hex,
    palette_from_seed,
    scss_map,
    sort_by_luminance,
    svg_strip,
    tailwind_theme,
    type_scale,
)


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
    assert scss_map(palette) in html
    assert best_on_ink(palette)["hex"] in html
    assert "Best on ink" in html
    assert "Body pair" in html
    assert "SCSS map" in html
    assert "Foreground" in html
    assert "Copy" in html
    assert "Copy lab link" in html
    assert "data-mix" in html
    assert "data-mix-a" in html
    assert "data-mix-b" in html
    assert "data-mix-t" in html
    assert mix_hex(palette[0], palette[1], 0.5) in html
    assert "data-body-pair hidden" in html
    assert "JSON tokens" in html
    assert "Tailwind theme" in html
    assert "Closest pair" in html
    assert "Farthest pair" in html
    assert "Lightest to darkest" in html
    assert "SVG strip" in html
    assert "UI pass" in html or "UI fail" in html
    assert json_tokens(palette) in html
    assert tailwind_theme(palette) in html
    assert svg_strip(palette) in html


def test_lab_json_returns_palette_tokens():
    app = create_app()
    seed = "asteria"
    palette = palette_from_seed(seed)
    best = best_on_ink(palette)

    with app.test_client() as client:
        response = client.get("/lab.json?seed=asteria")
        defaulted = client.get("/lab.json")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["seed"] == seed
    assert payload["palette"] == palette
    assert payload["ink"] == "#101418"
    assert payload["css"] == css_variables(palette)
    assert payload["scss"] == scss_map(palette)
    assert payload["best_on_ink"]["hex"] == best["hex"]
    assert payload["best_on_ink"]["aa"] is best["aa"]
    assert payload["best_on_ink"]["aaa"] is best["aaa"]
    assert payload["best_on_ink"]["ratio"] == approx(best["ratio"])
    assert payload["query"] == lab_query(seed)
    assert payload["tokens"] == json_tokens(palette)
    assert payload["tailwind"] == tailwind_theme(palette)
    assert payload["closest"]["a"] == closest_pair(palette)["a"]
    assert payload["closest"]["b"] == closest_pair(palette)["b"]
    assert payload["closest"]["i"] == closest_pair(palette)["i"]
    assert payload["closest"]["j"] == closest_pair(palette)["j"]
    assert payload["closest"]["delta_e"] == approx(closest_pair(palette)["delta_e"])
    assert payload["farthest"]["a"] == farthest_pair(palette)["a"]
    assert payload["farthest"]["b"] == farthest_pair(palette)["b"]
    assert payload["luminance"] == sort_by_luminance(palette)
    assert payload["svg"] == svg_strip(palette)
    assert set(payload) == {
        "seed",
        "palette",
        "ink",
        "css",
        "scss",
        "tokens",
        "tailwind",
        "best_on_ink",
        "closest",
        "farthest",
        "luminance",
        "svg",
        "query",
    }
    assert defaulted.status_code == 200
    assert defaulted.get_json()["seed"] == "asteria"
    assert defaulted.get_json()["query"] == lab_query("asteria")
    assert "mix" not in defaulted.get_json()


def test_lab_json_optional_mix_and_query():
    app = create_app()
    seed = "asteria"
    palette = palette_from_seed(seed)
    mixed = mix_hex(palette[0], palette[4], 0.5)

    with app.test_client() as client:
        response = client.get("/lab.json?seed=asteria&mix=0,4,0.5")
        ratioed = client.get("/lab.json?seed=hello+world&ratio=perfect-fifth")
        invalid = client.get("/lab.json?seed=asteria&mix=9,1,0.5")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["query"] == lab_query(seed)
    assert payload["mix"]["hex"] == mixed
    assert payload["mix"]["a"] == 0
    assert payload["mix"]["b"] == 4
    assert payload["mix"]["t"] == 0.5
    assert payload["mix"]["ratio"] == approx(contrast_ratio(mixed, INK))
    assert payload["mix"]["aa"] is (contrast_ratio(mixed, INK) >= 4.5)
    assert payload["mix"]["aaa"] is (contrast_ratio(mixed, INK) >= 7.0)
    assert ratioed.get_json()["query"] == lab_query("hello world", "perfect-fifth")
    assert "mix" not in invalid.get_json()


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
    assert 'rel="alternate"' in html
    assert 'type="application/rss+xml"' in html
    assert "feed.xml" in html
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
