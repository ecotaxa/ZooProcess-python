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


def test_projects_endpoint_with_valid_token(mocker: MockFixture, client, local_db):
    """Test that the /projects endpoint returns subdirectories from DRIVES with a valid token"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Still mock the file system operations and list_all_projects
    mock_iterdir = mocker.patch("pathlib.Path.iterdir")
    mock_exists = mocker.patch("pathlib.Path.exists")
    mock_is_dir = mocker.patch("pathlib.Path.is_dir")
    mock_list_all_projects = mocker.patch("main.list_all_projects")

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
    login_response = client["client"].post("/login", json=login_data)
    token = login_response.json()  # The login endpoint returns the token as JSON

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

    # Clean up the dependency override
    app.dependency_overrides.clear()


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
