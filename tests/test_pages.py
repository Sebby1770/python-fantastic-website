from app import create_app


def test_work_index_and_case_studies():
    app = create_app()

    with app.test_client() as client:
        index = client.get("/work")
        northline = client.get("/work/northline")
        meridian = client.get("/work/meridian")
        cobalt = client.get("/work/cobalt-room")
        harbor = client.get("/work/harbor-press")
        missing = client.get("/work/not-a-study")

    assert index.status_code == 200
    html = index.get_data(as_text=True)
    assert "Northline" in html
    assert "Meridian" in html
    assert "Cobalt Room" in html
    assert "Harbor Press" in html

    for response in (northline, meridian, cobalt, harbor):
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "Problem" in body
        assert "Approach" in body
        assert "Outcome" in body

    assert missing.status_code == 404


def test_journal_index_and_posts():
    app = create_app()

    with app.test_client() as client:
        index = client.get("/journal")
        post = client.get("/journal/server-rendered-is-not-a-compromise")
        missing = client.get("/journal/missing-essay")

    assert index.status_code == 200
    listing = index.get_data(as_text=True)
    assert "Server-rendered is not a compromise" in listing
    assert "Color as architecture" in listing
    assert "The brief should be a brief" in listing
    assert "18 March 2026" in listing or "March 2026" in listing

    assert post.status_code == 200
    assert "Documents should arrive whole" in post.get_data(as_text=True)
    assert missing.status_code == 404


def test_about_and_contact_pages():
    app = create_app()

    with app.test_client() as client:
        about = client.get("/about")
        contact = client.get("/contact")

    assert about.status_code == 200
    about_html = about.get_data(as_text=True)
    assert "Principles" in about_html
    assert "Stack" in about_html

    assert contact.status_code == 200
    contact_html = contact.get_data(as_text=True)
    assert 'name="project_type"' in contact_html
    assert 'name="budget"' in contact_html
    assert 'name="timeline"' in contact_html


def test_custom_404_page():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/definitely-not-here")

    assert response.status_code == 404
    assert "not in the folio" in response.get_data(as_text=True).lower()


def test_search_finds_work_and_journal_and_unknown():
    app = create_app()

    with app.test_client() as client:
        work = client.get("/search?q=Northline")
        journal = client.get("/search?q=Color as architecture")
        unknown = client.get("/search?q=zzzz-not-a-real-phrase")
        empty = client.get("/search")
        blank = client.get("/search?q=")

    assert work.status_code == 200
    work_html = work.get_data(as_text=True)
    assert "Northline" in work_html
    assert "/work/northline" in work_html

    assert journal.status_code == 200
    journal_html = journal.get_data(as_text=True)
    assert "Color as architecture" in journal_html
    assert "/journal/color-as-architecture" in journal_html

    assert unknown.status_code == 200
    unknown_html = unknown.get_data(as_text=True)
    assert "No matches" in unknown_html
    assert "/work/northline" not in unknown_html
    assert "/journal/color-as-architecture" not in unknown_html

    for response in (empty, blank):
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "/work/northline" not in html
        assert "/journal/color-as-architecture" not in html
        assert "Look through the folio" in html


def test_work_category_filter():
    app = create_app()

    with app.test_client() as client:
        filtered = client.get("/work", query_string={"category": "Brand platform"})
        all_work = client.get("/work")

    assert filtered.status_code == 200
    filtered_html = filtered.get_data(as_text=True)
    assert "Northline" in filtered_html
    assert "Meridian" not in filtered_html
    assert "Cobalt Room" not in filtered_html
    assert "Harbor Press" not in filtered_html

    assert all_work.status_code == 200
    listing = all_work.get_data(as_text=True)
    assert "Northline" in listing
    assert "Meridian" in listing
    assert ">All<" in listing or "All</a>" in listing


def test_journal_detail_has_reading_time_and_neighbors():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/journal/color-as-architecture")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "min read" in html.lower()
    assert "Previous" in html or "Next" in html
