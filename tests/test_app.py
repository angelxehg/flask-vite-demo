import pytest

from flask_vite_demo.app import create_app
from flask_vite_demo.core.csp import CONTENT_SECURITY_POLICY


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


@pytest.mark.parametrize("path", ["/", "/about", "/contact"])
def test_get_returns_ok(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert "unpkg.com" not in response.headers["Content-Security-Policy"]


def test_contact_post_echoes_submitted_name(client):
    response = client.post("/contact", data={"name": "Angel"})
    assert response.status_code == 200
    assert b"Angel" in response.data
    assert response.headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY


def test_home_includes_external_module_rejected_by_csp(client):
    response = client.get("/")
    assert b"https://unpkg.com/lit@3.3.2/index.js" in response.data
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
