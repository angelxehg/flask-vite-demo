import pytest

from flask_vite_demo.app import create_app
from flask_vite_demo.core.csp import build_content_security_policy


def _directive(policy: str, name: str) -> str:
    for part in policy.split("; "):
        if part.startswith(name + " "):
            return part
    raise AssertionError(f"{name} not found in policy: {policy}")


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


@pytest.mark.parametrize("path", ["/", "/about", "/contact"])
def test_get_returns_ok(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert (
        response.headers["Content-Security-Policy"] == build_content_security_policy()
    )


def test_contact_post_echoes_submitted_name(client):
    response = client.post("/contact", data={"name": "Angel"})
    assert response.status_code == 200
    assert b"Angel" in response.data


def test_csp_is_self_only_when_static_url_unset(client, monkeypatch):
    monkeypatch.delenv("STATIC_URL", raising=False)
    policy = client.get("/").headers["Content-Security-Policy"]
    assert _directive(policy, "script-src") == "script-src 'self'"
    assert _directive(policy, "style-src") == "style-src 'self'"


@pytest.mark.parametrize(
    "directive_name",
    [
        "script-src",
        "style-src",
        "img-src",
        "font-src",
        "media-src",
        "connect-src",
        "manifest-src",
        "worker-src",
    ],
)
def test_csp_scopes_cdn_source_to_this_apps_prefix(client, monkeypatch, directive_name):
    monkeypatch.setenv(
        "STATIC_URL", "https://static.angelxehg.com/flask-vite-demo/prod/"
    )
    policy = client.get("/").headers["Content-Security-Policy"]
    assert (
        _directive(policy, directive_name)
        == f"{directive_name} 'self' https://static.angelxehg.com/flask-vite-demo/prod/"
    )


def test_csp_never_allows_arbitrary_third_party_origin(client, monkeypatch):
    monkeypatch.setenv(
        "STATIC_URL", "https://static.angelxehg.com/flask-vite-demo/prod/"
    )
    assert "evil.example" not in client.get("/").headers["Content-Security-Policy"]


def test_csp_source_scoping_survives_a_missing_trailing_slash(client, monkeypatch):
    monkeypatch.setenv(
        "STATIC_URL", "https://static.angelxehg.com/flask-vite-demo/prod"
    )
    policy = client.get("/").headers["Content-Security-Policy"]
    assert (
        _directive(policy, "script-src")
        == "script-src 'self' https://static.angelxehg.com/flask-vite-demo/prod/"
    )


def test_home_no_longer_references_external_cdn_script(client):
    assert b"unpkg.com" not in client.get("/").data


CDN = "https://static.angelxehg.com/flask-vite-demo/prod/"


def test_favicon_link_is_rendered_in_the_head(client):
    assert b'rel="icon"' in client.get("/").data


def test_favicon_ico_redirects_instead_of_404ing(client):
    """The browser asks for this path on its own, link tag or not."""
    response = client.get("/favicon.ico")
    assert response.status_code in (301, 302, 308)
    assert "favicon.svg" in response.headers["Location"]


def test_static_url_serves_from_the_cdn_when_one_is_configured(client, monkeypatch):
    monkeypatch.setenv("STATIC_URL", CDN)
    assert (CDN + "favicon.svg").encode() in client.get("/").data


def test_static_url_falls_back_to_flask_when_no_cdn_is_configured(client, monkeypatch):
    """Vite copies public/ into the same dist/ everything else builds into."""
    monkeypatch.delenv("STATIC_URL", raising=False)
    assert b"/static/dist/favicon.svg" in client.get("/").data


def test_the_icon_is_allowed_by_the_content_security_policy(client, monkeypatch):
    """img-src governs a rel=icon link, and it already scopes to this prefix."""
    monkeypatch.setenv("STATIC_URL", CDN)
    policy = client.get("/").headers["Content-Security-Policy"]
    assert _directive(policy, "img-src") == f"img-src 'self' {CDN}"


def test_unknown_path_renders_the_sites_own_404(client):
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert b"Not found" in response.data
    # The site shell, not Werkzeug's default page.
    assert b"<nav>" in response.data
    assert response.headers["Content-Security-Policy"] == (
        build_content_security_policy()
    )


# The distribution in front of this application lets the origin decide what is
# cacheable: its cache policy has a zero default TTL and a non-zero ceiling, so a
# response with no Cache-Control is not cached and one asking for an hour gets an
# hour. That makes these headers the whole of the edge caching configuration, and
# nothing else would report them missing -- an uncached index is not an error.
def test_index_is_cacheable_for_an_hour(client):
    assert client.get("/").headers["Cache-Control"] == "public, max-age=3600"


@pytest.mark.parametrize("path", ["/about", "/contact"])
def test_other_pages_are_not_cached(client, path):
    assert client.get(path).headers["Cache-Control"] == "no-store"


def test_a_post_response_is_never_cached(client):
    """Not that CloudFront would cache one -- only GET and HEAD are cached
    methods -- but the header should not depend on that being true."""
    response = client.post("/contact", data={"name": "Angel"})
    assert response.headers["Cache-Control"] == "no-store"


def test_the_error_page_is_not_cached(client):
    """A cached 404 outlives whatever caused it, and the deploy that fixes the
    route cannot invalidate it: no role holds cloudfront:CreateInvalidation."""
    response = client.get("/no-such-page")
    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"


def test_the_favicon_redirect_is_not_cached(client):
    assert client.get("/favicon.ico").headers["Cache-Control"] == "no-store"


def test_a_cacheable_endpoint_returning_an_error_is_not_cached(monkeypatch):
    """`home` is on the cacheable list, and the list is not the whole rule.

    Caching a 500 from the index would be the worst version of this: the page
    everyone lands on, wrong for an hour, with no way to flush it.
    """
    from flask_vite_demo.core.cache import cache_control_for

    assert cache_control_for("home", "GET", 200) == "public, max-age=3600"
    assert cache_control_for("home", "GET", 500) == "no-store"
    assert cache_control_for("home", "POST", 200) == "no-store"
    assert cache_control_for(None, "GET", 200) == "no-store"


RELATIVE_STATIC = "/static"


def test_assets_resolve_against_a_relative_static_url(client, monkeypatch):
    """What production actually sets. The distribution routes /static/* to a
    bucket, so these are same-origin with the page that references them."""
    monkeypatch.setenv("STATIC_URL", RELATIVE_STATIC)
    body = client.get("/").data
    assert b'href="/static/favicon.svg"' in body
    assert b'href="/static/assets/' in body


def test_a_relative_static_url_leaves_the_policy_self_only(client, monkeypatch):
    """The point of the move, expressed as a header.

    A relative path has no scheme and no host, so there is no source to add --
    and none is needed, because 'self' already covers same-origin. An absolute
    STATIC_URL is what puts a host in the policy, and production no longer has
    one.
    """
    monkeypatch.setenv("STATIC_URL", RELATIVE_STATIC)
    policy = client.get("/").headers["Content-Security-Policy"]
    for name in ("script-src", "style-src", "img-src", "connect-src"):
        assert _directive(policy, name) == f"{name} 'self'"
    assert "//" not in policy
