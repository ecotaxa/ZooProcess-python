import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_pages_router_exists(client):
    """Test that the pages router exists and is accessible."""
    # This will fail if the router doesn't exist
    response = client.get("/ui/")
    # We expect a 200 OK because unauthenticated requests are redirected to the login page
    assert response.status_code == 200

    # Check that the response contains the login page content
    assert "Login" in response.text


def test_pages_router_about_exists(client):
    """Test that the about page exists and is accessible."""
    # This will fail if the router doesn't exist
    response = client.get("/ui/about")
    # We expect a 200 OK because unauthenticated requests are redirected to the login page
    assert response.status_code == 200

    # Check that the response contains the login page content
    assert "Login" in response.text
