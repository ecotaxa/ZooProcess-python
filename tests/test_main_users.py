import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from main import app, get_db
from auth import decode_jwt_token
from local_DB.models import User as DBUser


@pytest.fixture
def client():
    # Create the test client
    client = TestClient(app)

    # Return the client for use in tests
    yield {"client": client}

    # Cleanup (equivalent to tearDown)
    app.dependency_overrides.clear()


def test_users_me_endpoint_with_valid_token(client, local_db):
    """Test that the /users/me endpoint returns user information with a valid token"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = client["client"].post("/login", json=login_data)
    token = login_response.json()

    # Make request to the /users/me endpoint with the token
    response = client["client"].get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response contains user information
    user_data = response.json()
    assert user_data is not None
    assert user_data["email"] == login_data["email"]


def test_users_me_endpoint_without_token(client):
    """Test that the /users/me endpoint returns 401 without a token"""
    # Make request to the /users/me endpoint without a token
    response = client["client"].get("/users/me")

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401


def test_users_me_endpoint_with_invalid_token(client):
    """Test that the /users/me endpoint returns 401 with an invalid token"""
    # Make request to the /users/me endpoint with an invalid token
    response = client["client"].get(
        "/users/me", headers={"Authorization": "Bearer invalid_token"}
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401
