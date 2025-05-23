import pytest
from fastapi.testclient import TestClient

from auth import decode_jwt_token
from main import app, get_db


def test_login_endpoint(app_client, local_db):
    """Test that the /login endpoint returns a valid JWT token"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Test data
    login_data = {"email": "test@example.com", "password": "test_password"}

    # Make request to the login endpoint
    response = app_client.post("/login", json=login_data)

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response contains a token
    token = response.json()
    assert token is not None

    # Verify that the token is a valid JWT token
    decoded = decode_jwt_token(token)
    assert decoded["email"] == login_data["email"]
