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
    # We expect a 401 Unauthorized because we're not authenticated
    assert response.status_code == 401

    # Check that the response contains the expected error message
    assert "Not authenticated" in response.text


def test_pages_router_about_exists(client):
    """Test that the about page exists and is accessible."""
    # This will fail if the router doesn't exist
    response = client.get("/ui/about")
    # We expect a 401 Unauthorized because we're not authenticated
    assert response.status_code == 401

    # Check that the response contains the expected error message
    assert "Not authenticated" in response.text
