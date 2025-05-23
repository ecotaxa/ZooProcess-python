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


def test_project_by_id_endpoint_with_valid_token(mocker: MockFixture, client, local_db):
    """Test that the /projects/{project_id} endpoint returns a specific project with a valid token"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock the file system operations
    mock_exists = mocker.patch("pathlib.Path.exists")
    mock_is_dir = mocker.patch("pathlib.Path.is_dir")

    # Mock the extract_drive_and_project function
    mock_extract = mocker.patch("main.extract_drive_and_project")

    # Set up the mocks for Path methods
    mock_exists.return_value = True
    mock_is_dir.return_value = True

    # Create mock Path objects
    from pathlib import Path
    from Models import Project, Drive

    mock_drive_path = mocker.MagicMock(spec=Path)
    mock_drive_path.name = "drive1"
    mock_drive_path.__str__.return_value = "/path/to/drive1"

    mock_project_path = mocker.MagicMock(spec=Path)
    mock_project_path.name = "Project1"
    mock_project_path.__str__.return_value = "/path/to/drive1/Project1"

    # Set up mock for extract_drive_and_project to return our mock paths
    mock_extract.return_value = (mock_drive_path, "Project1", mock_project_path)

    # Create a test project
    drive_model = Drive(id="drive1", name="drive1", url="/path/to/drive1")
    test_project = Project(
        path="/path/to/drive1/Project1",
        id="drive1|Project1",
        name="Project1",
        instrumentSerialNumber="TEST123",
        drive=drive_model,
    )

    # Mock the project_from_legacy function to return our test project
    mock_project_from_legacy = mocker.patch("main.project_from_legacy")
    mock_project_from_legacy.return_value = test_project

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = client["client"].post("/login", json=login_data)
    token = login_response.json()

    # Make request to the /projects/{project_id} endpoint with the token
    response = client["client"].get(
        "/projects/drive1|Project1", headers={"Authorization": f"Bearer {token}"}
    )

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response contains the correct project information
    project_data = response.json()
    assert project_data is not None
    assert project_data["name"] == "Project1"
    assert project_data["path"] == "/path/to/drive1/Project1"
    assert project_data["id"] == "drive1|Project1"
    assert project_data["instrumentSerialNumber"] == "TEST123"

    # Verify that extract_drive_and_project was called with the correct project_id
    mock_extract.assert_called_once_with("drive1|Project1")

    # Verify that project_from_legacy was called with the correct arguments
    mock_project_from_legacy.assert_called_once()

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_project_by_id_endpoint_with_invalid_drive(
    mocker: MockFixture, client, local_db
):
    """Test that the /projects/{project_id} endpoint returns 404 when the drive is not found"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock get_drive_path to return None (drive not found)
    mock_get_drive_path = mocker.patch("main.get_drive_path")
    mock_get_drive_path.return_value = None

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = client["client"].post("/login", json=login_data)
    token = login_response.json()

    # Make request to the /projects/{project_id} endpoint with the token and an invalid drive
    response = client["client"].get(
        "/projects/invalid_drive|Project1", headers={"Authorization": f"Bearer {token}"}
    )

    # Check that the response is 404 Not Found
    assert response.status_code == 404

    # Check that the response contains the correct error message
    error_data = response.json()
    assert error_data["detail"] == "Project with ID invalid_drive|Project1 not found"

    # Verify that get_drive_path was called with the correct drive name
    mock_get_drive_path.assert_called_once_with("invalid_drive")

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_project_by_id_endpoint_with_invalid_project(
    mocker: MockFixture, client, local_db
):
    """Test that the /projects/{project_id} endpoint returns 404 when the project does not exist"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock get_drive_path to return a valid drive path
    mock_get_drive_path = mocker.patch("main.get_drive_path")

    # Create a mock drive path
    from pathlib import Path

    mock_drive_path = mocker.MagicMock(spec=Path)
    mock_drive_path.name = "drive1"
    mock_drive_path.__str__.return_value = "/path/to/drive1"

    mock_get_drive_path.return_value = mock_drive_path

    # Mock Path.exists and Path.is_dir to simulate a non-existent project
    mock_exists = mocker.patch("pathlib.Path.exists")
    mock_is_dir = mocker.patch("pathlib.Path.is_dir")

    # Project path does not exist
    mock_exists.return_value = False
    mock_is_dir.return_value = False

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = client["client"].post("/login", json=login_data)
    token = login_response.json()

    # Make request to the /projects/{project_id} endpoint with the token and a non-existent project
    response = client["client"].get(
        "/projects/drive1|NonExistentProject",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that the response is 404 Not Found
    assert response.status_code == 404

    # Check that the response contains the correct error message
    error_data = response.json()
    assert error_data["detail"] == "Project with ID drive1|NonExistentProject not found"

    # Verify that get_drive_path was called with the correct drive name
    mock_get_drive_path.assert_called_once_with("drive1")

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_project_by_id_endpoint_with_invalid_format(client, local_db):
    """Test that the /projects/{project_id} endpoint returns an error when the project_id is not in the correct format"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = client["client"].post("/login", json=login_data)
    token = login_response.json()

    # Make request to the /projects/{project_id} endpoint with the token and a project_id in an invalid format
    response = client["client"].get(
        "/projects/invalid_format",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that the response is an error (500 Internal Server Error due to ValueError)
    assert response.status_code == 500

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_project_by_id_endpoint_without_token(client):
    """Test that the /projects/{project_id} endpoint returns 401 without a token"""
    # Make request to the /projects/{project_id} endpoint without a token
    response = client["client"].get("/projects/drive1|Project1")

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401


def test_project_by_id_endpoint_with_invalid_token(client):
    """Test that the /projects/{project_id} endpoint returns 401 with an invalid token"""
    # Make request to the /projects/{project_id} endpoint with an invalid token
    response = client["client"].get(
        "/projects/drive1|Project1",
        headers={"Authorization": "Bearer invalid_token"},
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401
