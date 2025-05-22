import pytest
from fastapi.testclient import TestClient

from main import app, get_db
from auth import decode_jwt_token
from local_DB.models import User as DBUser


@pytest.fixture
def client(mocker):
    # Create a mock database session
    mock_db = mocker.MagicMock()

    # Create a mock user for testing
    mock_user = mocker.MagicMock(spec=DBUser)
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


def test_login_endpoint(mocker, client):
    """Test that the /login endpoint returns a valid JWT token"""
    mock_get_user_from_db = mocker.patch("auth.get_user_from_db")
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


def test_users_me_endpoint_with_valid_token(mocker, client):
    """Test that the /users/me endpoint returns user information with a valid token"""
    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_mock = mocker.patch("auth.get_user_from_db", return_value=client["mock_user"])
    login_response = client["client"].post("/login", json=login_data)
    token = login_response.json()
    login_mock.reset_mock()

    # Mock get_user_from_token to return user data with the correct email
    mock_get_user_from_token = mocker.patch("auth.get_user_from_token")
    mock_get_user_from_token.return_value = {
        "id": client["mock_user"].id,
        "name": client["mock_user"].name,
        "email": login_data["email"],
    }

    # Mock get_user_from_db to return our mock user
    mock_get_user_from_db = mocker.patch("auth.get_user_from_db")
    mock_get_user_from_db.return_value = client["mock_user"]

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
    mock_get_user_from_db.assert_called_once_with(
        login_data["email"], client["mock_db"]
    )


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


def test_projects_endpoint_with_valid_token(mocker, client):
    """Test that the /projects endpoint returns subdirectories from DRIVES with a valid token"""
    mock_get_user_from_db = mocker.patch("auth.get_user_from_db")
    mock_iterdir = mocker.patch("pathlib.Path.iterdir")
    mock_exists = mocker.patch("pathlib.Path.exists")
    mock_is_dir = mocker.patch("pathlib.Path.is_dir")
    mock_list_all_projects = mocker.patch("main.list_all_projects")
    # Set up the mock to return our mock user
    mock_get_user_from_db.return_value = client["mock_user"]

    # Set up the mocks for Path methods
    mock_exists.return_value = True
    mock_is_dir.return_value = True

    # Create mock Path objects for subdirectories
    from pathlib import Path
    from Models import Project, Drive

    mock_dir1 = mocker.MagicMock(spec=Path)
    mock_dir1.is_dir.return_value = True
    mock_dir1.name = "Project1"
    mock_dir1.__str__.return_value = "/path/to/drive1/Project1"

    mock_dir2 = mocker.MagicMock(spec=Path)
    mock_dir2.is_dir.return_value = True
    mock_dir2.name = "Project2"
    mock_dir2.__str__.return_value = "/path/to/drive1/Project2"

    # Set up the mock to return our mock directories
    mock_iterdir.return_value = [mock_dir1, mock_dir2]

    # Set up mock for list_all_projects to return test projects
    drive_model = Drive(id="drive1", name="drive1", url="/path/to/drive1")
    mock_list_all_projects.return_value = [
        Project(
            path="/path/to/drive1/Project1",
            id="drive1|Project1",
            name="Project1",
            instrumentSerialNumber="TEST123",
            drive=drive_model,
        ),
        Project(
            path="/path/to/drive1/Project2",
            id="drive1|Project2",
            name="Project2",
            instrumentSerialNumber="TEST123",
            drive=drive_model,
        ),
    ]

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_mock = mocker.patch("auth.get_user_from_db", return_value=client["mock_user"])
    login_response = client["client"].post("/login", json=login_data)
    token = (
        login_response.text
    )  # The login endpoint returns the token directly as text, not as JSON
    login_mock.reset_mock()

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
    assert projects_data[0]["name"] == "Project1"
    assert projects_data[1]["name"] == "Project2"
    assert projects_data[0]["path"] == "/path/to/drive1/Project1"
    assert projects_data[1]["path"] == "/path/to/drive1/Project2"

    # Verify that get_user_from_db was called with the correct arguments
    mock_get_user_from_db.assert_called_with(login_data["email"], client["mock_db"])


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
