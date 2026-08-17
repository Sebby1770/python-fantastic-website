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
