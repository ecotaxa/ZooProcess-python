import pytest
from fastapi.testclient import TestClient

from local_DB.db_dependencies import get_db
from main import app


def test_users_me_endpoint_with_valid_token(app_client, local_db):
    """Test that the /users/me endpoint returns user information with a valid token"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Make request to the /users/me endpoint with the token
    response = app_client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response contains user information
    user_data = response.json()
    assert user_data is not None
    assert user_data["email"] == login_data["email"]


def test_users_me_endpoint_without_token(app_client):
    """Test that the /users/me endpoint returns 401 without a token"""
    # Make request to the /users/me endpoint without a token
    response = app_client.get("/users/me")

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401


def test_users_me_endpoint_with_invalid_token(app_client):
    """Test that the /users/me endpoint returns 401 with an invalid token"""
    # Make request to the /users/me endpoint with an invalid token
    response = app_client.get(
        "/users/me", headers={"Authorization": "Bearer invalid_token"}
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401
