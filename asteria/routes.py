"""HTTP routes for the studio site."""

from __future__ import annotations

import csv
import hmac
from email.utils import format_datetime, parseaddr
from datetime import datetime, timezone
from io import StringIO
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, tostring

from flask import (
    Flask,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from asteria.catalog import (
    BUDGETS,
    PRINCIPLES,
    PROCESS,
    PROJECT_TYPES,
    SERVICES,
    STACK,
    STATS,
    TIMELINES,
    VERSION,
    WORK,
    get_study,
    neighboring_studies,
    work_categories,
)
from asteria.journal import get_post, load_posts, neighboring_posts, related_posts
from asteria.limiter import RateLimiter
from asteria.search import search_site
from asteria import store


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.remote_addr or "unknown"


def _clean(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _valid_email(email: str) -> bool:
    parsed = parseaddr(email)[1]
    if "@" not in parsed:
        return False
    local, _, domain = parsed.partition("@")
    return bool(local) and "." in domain and " " not in parsed


def _studio_token() -> str:
    return str(current_app.config.get("STUDIO_TOKEN") or "")


def _provided_studio_token() -> str:
    header = request.headers.get("X-Studio-Token", "")
    if header:
        return header
    return str(request.args.get("token") or request.form.get("token") or "")


def _studio_authorized() -> bool:
    expected = _studio_token()
    if not expected:
        return False
    provided = _provided_studio_token()
    if not provided:
        return False
    return hmac.compare_digest(provided, expected)


def _wants_json() -> bool:
    if request.is_json:
        return True
    return request.accept_mimetypes.best == "application/json"


def _thanks_payload(name: str) -> dict:
    first_name = name.split()[0]
    return {
        "ok": True,
        "message": f"Thanks, {first_name}. Your brief is ready for the next conversation.",
    }


def _contact_success(name: str):
    if _wants_json():
        return jsonify(_thanks_payload(name))
    return redirect(url_for("contact_thanks"))


def _form_context() -> dict:
    return {
        "project_types": PROJECT_TYPES,
        "budgets": BUDGETS,
        "timelines": TIMELINES,
    }


def _absolute(path: str) -> str:
    return urljoin(request.url_root, path)


def register_routes(app: Flask) -> None:
    limiter: RateLimiter = app.extensions["rate_limiter"]

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            page_class="home",
            stats=STATS,
            work=WORK,
            services=SERVICES,
            process=PROCESS,
            **_form_context(),
        )

    @app.get("/work")
    def work_index():
        category = (request.args.get("category") or "").strip()
        items = WORK
        if category:
            items = tuple(item for item in WORK if item.category == category)
        return render_template(
            "work/index.html",
            page_class="interior",
            title="Work — Asteria Studio",
            description="Selected case studies from Asteria Studio.",
            work=items,
            categories=work_categories(),
            active_category=category,
        )

    @app.get("/work/<slug>")
    def work_detail(slug: str):
        study = get_study(slug)
        if study is None:
            abort(404)
        previous_item, next_item = neighboring_studies(slug)
        return render_template(
            "work/detail.html",
            page_class="interior",
            title=f"{study.name} — Asteria Studio",
            description=study.summary,
            study=study,
            previous_item=previous_item,
            next_item=next_item,
        )

    @app.get("/journal")
    def journal_index():
        posts = load_posts()
        return render_template(
            "journal/index.html",
            page_class="interior",
            title="Journal — Asteria Studio",
            description="Notes from Asteria Studio on making websites with a point of view.",
            posts=posts,
        )

    @app.get("/journal/<slug>")
    def journal_detail(slug: str):
        post = get_post(slug)
        if post is None:
            abort(404)
        previous_item, next_item = neighboring_posts(slug)
        return render_template(
            "journal/detail.html",
            page_class="interior",
            title=f"{post.title} — Asteria Studio",
            description=post.dek,
            post=post,
            previous_item=previous_item,
            next_item=next_item,
            related=related_posts(slug),
        )

    @app.get("/search")
    def search():
        query = (request.args.get("q") or "").strip()
        hits = search_site(query)
        return render_template(
            "search.html",
            page_class="interior",
            title="Search — Asteria Studio",
            description="Search Asteria Studio case studies and journal notes.",
            query=query,
            hits=hits,
        )

    @app.get("/about")
    def about():
        return render_template(
            "about.html",
            page_class="interior",
            title="About — Asteria Studio",
            description="A studio note on how Asteria works, what we believe, and the stack we ship.",
            principles=PRINCIPLES,
            stack=STACK,
        )

    @app.get("/contact")
    def contact_page():
        return render_template(
            "contact.html",
            page_class="interior",
            title="Contact — Asteria Studio",
            description="Send Asteria Studio a brief for the next website.",
            **_form_context(),
        )

    @app.get("/contact/thanks")
    def contact_thanks():
        return render_template(
            "thanks.html",
            page_class="interior",
            title="Thanks — Asteria Studio",
            description="Your brief is on file with Asteria Studio.",
            robots="noindex, nofollow",
        )

    @app.post("/contact")
    def contact():
        if not limiter.allow(_client_ip()):
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "Please wait a few minutes before sending another brief.",
                    }
                ),
                429,
            )

        payload = request.get_json(silent=True) or request.form
        name = _clean(payload.get("name"), 120)
        email = _clean(payload.get("email"), 200)
        message = _clean(payload.get("message"), 5000)
        budget = _clean(payload.get("budget"), 80)
        timeline = _clean(payload.get("timeline"), 80)
        project_type = _clean(payload.get("project_type"), 80)
        website = _clean(payload.get("website"), 200)

        if not name or not email or not message:
            return (
                jsonify(
                    {
                        "ok": False,
                        "message": "Please add your name, email, and a short project note.",
                    }
                ),
                400,
            )

        if not _valid_email(email):
            return jsonify({"ok": False, "message": "Please enter a valid email address."}), 400

        if website:
            return _contact_success(name)

        store.insert_inquiry(
            current_app,
            name=name,
            email=email,
            message=message,
            budget=budget,
            timeline=timeline,
            project_type=project_type,
        )

        return _contact_success(name)

    @app.get("/studio")
    def studio():
        if not _studio_authorized():
            abort(404)
        query = (request.args.get("q") or "").strip()
        status = (request.args.get("status") or "").strip()
        inquiries = store.list_inquiries(current_app, query=query, status=status)
        return render_template(
            "studio.html",
            page_class="interior",
            title="Inbox — Asteria Studio",
            description="Token-protected inquiry inbox.",
            robots="noindex, nofollow",
            inquiries=inquiries,
            studio_token=_provided_studio_token(),
            studio_query=query,
            studio_status=status,
        )

    @app.get("/studio.csv")
    def studio_csv():
        if not _studio_authorized():
            abort(404)
        query = (request.args.get("q") or "").strip()
        status = (request.args.get("status") or "").strip()
        rows = store.list_inquiries(current_app, query=query, status=status)
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "id",
                "created_at",
                "name",
                "email",
                "message",
                "budget",
                "timeline",
                "project_type",
                "status",
                "notes",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["id"],
                    row["created_at"],
                    row["name"],
                    row["email"],
                    row["message"],
                    row["budget"] or "",
                    row["timeline"] or "",
                    row["project_type"] or "",
                    row["status"],
                    row["notes"] or "",
                ]
            )
        return current_app.response_class(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": 'attachment; filename="inquiries.csv"'},
        )

    @app.post("/studio/<int:inquiry_id>/archive")
    def studio_archive(inquiry_id: int):
        if not _studio_authorized():
            abort(404)
        store.archive_inquiry(current_app, inquiry_id)
        if _wants_json():
            return jsonify({"ok": True, "id": inquiry_id, "status": "archived"})
        return redirect(url_for("studio", token=_provided_studio_token()))

    @app.post("/studio/<int:inquiry_id>/unarchive")
    def studio_unarchive(inquiry_id: int):
        if not _studio_authorized():
            abort(404)
        store.unarchive_inquiry(current_app, inquiry_id)
        if _wants_json():
            return jsonify({"ok": True, "id": inquiry_id, "status": "new"})
        return redirect(url_for("studio", token=_provided_studio_token()))

    @app.post("/studio/<int:inquiry_id>/notes")
    def studio_notes(inquiry_id: int):
        if not _studio_authorized():
            abort(404)
        payload = request.get_json(silent=True) or request.form
        notes = _clean(payload.get("notes"), 8000)
        store.update_notes(current_app, inquiry_id, notes)
        if _wants_json():
            return jsonify({"ok": True, "id": inquiry_id, "notes": notes})
        return redirect(url_for("studio", token=_provided_studio_token()))

    @app.get("/health")
    def health():
        return jsonify(
            {
                "ok": True,
                "service": "asteria-studio",
                "version": current_app.config.get("VERSION", VERSION),
            }
        )

    @app.get("/sitemap.xml")
    def sitemap():
        urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        paths = [
            "/",
            "/work",
            "/journal",
            "/about",
            "/contact",
        ]
        paths.extend(f"/work/{item.slug}" for item in WORK)
        paths.extend(f"/journal/{post.slug}" for post in load_posts())
        for path in paths:
            url_el = SubElement(urlset, "url")
            SubElement(url_el, "loc").text = _absolute(path)
        xml = tostring(urlset, encoding="utf-8", xml_declaration=True)
        return current_app.response_class(xml, mimetype="application/xml")

    @app.get("/robots.txt")
    def robots():
        body = (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /studio\n"
            f"Sitemap: {_absolute('/sitemap.xml')}\n"
        )
        return current_app.response_class(body, mimetype="text/plain")

    @app.get("/journal/feed.xml")
    def journal_feed():
        posts = load_posts()
        rss = Element("rss", version="2.0")
        channel = SubElement(rss, "channel")
        SubElement(channel, "title").text = "Asteria Studio Journal"
        SubElement(channel, "link").text = _absolute("/journal")
        SubElement(channel, "description").text = (
            "Notes from Asteria Studio on making websites with a point of view."
        )
        SubElement(channel, "language").text = "en-us"
        for post in posts:
            item = SubElement(channel, "item")
            SubElement(item, "title").text = post.title
            SubElement(item, "link").text = _absolute(f"/journal/{post.slug}")
            SubElement(item, "guid").text = _absolute(f"/journal/{post.slug}")
            SubElement(item, "pubDate").text = format_datetime(
                datetime.combine(post.date, datetime.min.time(), tzinfo=timezone.utc)
            )
            SubElement(item, "description").text = post.dek
        xml = tostring(rss, encoding="utf-8", xml_declaration=True)
        return current_app.response_class(xml, mimetype="application/rss+xml")

    @app.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "404.html",
                page_class="interior",
                title="Not in the folio — Asteria Studio",
                description="This page is not in the Asteria Studio folio.",
            ),
            404,
        )
