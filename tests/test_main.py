from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app, get_db
from src.auth import decode_jwt_token
from src.db_models import User as DBUser


@pytest.fixture
def client():
    # Create a mock database session
    mock_db = MagicMock()

    # Create a mock user for testing
    mock_user = MagicMock(spec=DBUser)
    mock_user.id = "123456789"
    mock_user.name = "John Doe"
    mock_user.email = "test@example.com"
    mock_user.password = "test_password"

    # Override the get_db dependency to return our mock session
    app.dependency_overrides[get_db] = lambda: mock_db

    # Create the test client
    client = TestClient(app)

    # Return both the client and the mocks for use in tests
    yield {"client": client, "mock_db": mock_db, "mock_user": mock_user}

    # Cleanup (equivalent to tearDown)
    app.dependency_overrides.clear()


@patch("src.auth.get_user_from_db")
def test_login_endpoint(mock_get_user_from_db, client):
    """Test that the /login endpoint returns a valid JWT token"""
    # Set up the mock to return our mock user
    mock_get_user_from_db.return_value = client["mock_user"]

    # Test data
    login_data = {"email": "test@example.com", "password": "test_password"}

    # Make request to the login endpoint
    response = client["client"].post("/login", json=login_data)

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response contains a token
    token = response.json()
    assert token is not None

    # Verify that the token is a valid JWT token
    decoded = decode_jwt_token(token)
    assert decoded["email"] == login_data["email"]

    # Verify that get_user_from_db was called with the correct arguments
    mock_get_user_from_db.assert_called_once_with(
        login_data["email"], client["mock_db"]
    )


@patch("src.auth.get_user_from_db")
def test_users_me_endpoint_with_valid_token(mock_get_user_from_db, client):
    """Test that the /users/me endpoint returns user information with a valid token"""
    # Set up the mock to return our mock user
    mock_get_user_from_db.return_value = client["mock_user"]

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    with patch("src.auth.get_user_from_db", return_value=client["mock_user"]):
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

    # Verify that get_user_from_db was called with the correct arguments
    mock_get_user_from_db.assert_called_with(login_data["email"], client["mock_db"])


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


@patch("src.auth.get_user_from_db")
@patch("src.DB.DB.get")
def test_projects_endpoint_with_valid_token(mock_db_get, mock_get_user_from_db, client):
    """Test that the /projects endpoint returns project information with a valid token"""
    # Set up the mock to return our mock user
    mock_get_user_from_db.return_value = client["mock_user"]

    # Set up the mock to return a list of projects
    mock_projects = [
        {
            "id": "project1",
            "name": "Project 1",
            "path": "/path/to/project1",
            "instrumentSerialNumber": "SN001",
            "description": "Test Project 1",
        },
        {
            "id": "project2",
            "name": "Project 2",
            "path": "/path/to/project2",
            "instrumentSerialNumber": "SN002",
            "description": "Test Project 2",
        },
    ]
    mock_db_get.return_value = mock_projects

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    with patch("src.auth.get_user_from_db", return_value=client["mock_user"]):
        login_response = client["client"].post("/login", json=login_data)
        token = login_response.json()

    # Make request to the /projects endpoint with the token
    response = client["client"].get(
        "/projects", headers={"Authorization": f"Bearer {token}"}
    )

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response contains project information
    projects_data = response.json()
    assert projects_data is not None
    assert len(projects_data) == 2
    assert projects_data[0]["name"] == "Project 1"
    assert projects_data[1]["name"] == "Project 2"

    # Verify that get_user_from_db was called with the correct arguments
    mock_get_user_from_db.assert_called_with(login_data["email"], client["mock_db"])

    # Verify that DB.get was called with the correct arguments
    mock_db_get.assert_called_once_with("/projects")


def test_projects_endpoint_without_token(client):
    """Test that the /projects endpoint returns 401 without a token"""
    # Make request to the /projects endpoint without a token
    response = client["client"].get("/projects")

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401


def test_projects_endpoint_with_invalid_token(client):
    """Test that the /projects endpoint returns 401 with an invalid token"""
    # Make request to the /projects endpoint with an invalid token
    response = client["client"].get(
        "/projects", headers={"Authorization": "Bearer invalid_token"}
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401
