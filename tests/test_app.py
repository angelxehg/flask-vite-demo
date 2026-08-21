import pytest

from flask_vite_demo.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


@pytest.mark.parametrize("path", ["/", "/about", "/contact"])
def test_get_returns_ok(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_contact_post_echoes_submitted_name(client):
    response = client.post("/contact", data={"name": "Angel"})
    assert response.status_code == 200
    assert b"Angel" in response.data
