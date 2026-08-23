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
