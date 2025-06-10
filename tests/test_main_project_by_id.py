from pytest_mock import MockFixture

from local_DB.db_dependencies import get_db
from main import app


def test_project_by_id_endpoint_with_valid_token(
    mocker: MockFixture, app_client, local_db
):
    """Test that the /projects/{project_id} endpoint returns a specific project with a valid token"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock the file system operations
    mock_exists = mocker.patch("pathlib.Path.exists")
    mock_is_dir = mocker.patch("pathlib.Path.is_dir")

    # Create mock Path objects
    from pathlib import Path
    from Models import Project, Drive, Instrument
    from ZooProcess_lib.ZooscanFolder import ZooscanDrive, ZooscanProjectFolder

    mock_drive_path = mocker.MagicMock(spec=Path)
    mock_drive_path.name = "drive1"
    mock_drive_path.__str__.return_value = "/path/to/drive1"

    mock_project_path = mocker.MagicMock(spec=Path)
    mock_project_path.name = "Project1"
    mock_project_path.__str__.return_value = "/path/to/drive1/Project1"

    # Set up the mocks for Path methods
    mock_exists.return_value = True
    mock_is_dir.return_value = True

    # Create mock ZooscanDrive and ZooscanProjectFolder objects
    mock_zoo_drive = mocker.MagicMock(spec=ZooscanDrive)
    mock_zoo_project = mocker.MagicMock(spec=ZooscanProjectFolder)
    mock_zoo_project.path = mock_project_path
    mock_zoo_project.name = "Project1"

    # Mock validate_path_components to return our mock objects
    mock_validate = mocker.patch("routers.projects.validate_path_components")
    mock_validate.return_value = (mock_zoo_drive, mock_zoo_project, "", "")

    # Create a test project
    drive_model = Drive(id="drive1", name="drive1", url="/path/to/drive1")
    instrument_model = Instrument(
        id="1",
        name="Default Zooscan",
        sn="TEST123",
    )
    test_project = Project(
        path="/path/to/drive1/Project1",
        id="drive1|Project1",
        name="Project1",
        instrumentSerialNumber="TEST123",
        drive=drive_model,
        instrument=instrument_model,
    )

    # Mock the ZooscanDrive.get_project_folder method to prevent it from trying to read files
    mock_get_project_folder = mocker.patch(
        "ZooProcess_lib.ZooscanFolder.ZooscanDrive.get_project_folder"
    )
    mock_project_folder = mocker.MagicMock()
    mock_get_project_folder.return_value = mock_project_folder

    # Mock os.path.getmtime to return a fixed timestamp
    mock_getmtime = mocker.patch("os.path.getmtime")
    mock_getmtime.return_value = 1625097600  # July 1, 2021

    # Mock find_latest_modification_time to return a fixed timestamp
    from datetime import datetime

    mock_find_latest = mocker.patch("modern.from_legacy.find_latest_modification_time")
    mock_find_latest.return_value = datetime.fromtimestamp(1625097600)  # July 1, 2021

    # Mock extract_serial_number to return TEST123
    mock_extract_serial = mocker.patch("modern.from_legacy.extract_serial_number")
    mock_extract_serial.return_value = "TEST123"

    # Mock the project_from_legacy function to return our test project
    mock_project_from_legacy = mocker.patch("routers.projects.project_from_legacy")
    mock_project_from_legacy.return_value = test_project

    # Mock the projects_cache to return a known value
    mock_cache = mocker.MagicMock()
    mock_cache.id_from_name.return_value = "dummy_id"
    mock_cache.name_from_id.return_value = "drive1|Project1"
    mocker.patch("modern.ids.projects_cache", mock_cache)

    # Use the mocked project_id
    project_id = "dummy_id"

    # Generate a project hash for our test project
    project_hash = project_id

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Make request to the /projects/{project_id} endpoint with the token
    response = app_client.get(
        f"/projects/{project_hash}", headers={"Authorization": f"Bearer {token}"}
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

    # Verify that validate_path_components was called with the correct project_id
    mock_validate.assert_called_once_with(local_db, "dummy_id")

    # Verify that project_from_legacy was called with the correct arguments
    mock_project_from_legacy.assert_called_once()

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_project_by_id_endpoint_with_invalid_drive(
    mocker: MockFixture, app_client, local_db
):
    """Test that the /projects/{project_id} endpoint returns 404 when the drive is not found"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock get_drive_path to return None (drive not found)
    mock_get_drive_path = mocker.patch("modern.ids.get_drive_path")
    mock_get_drive_path.return_value = None

    # Mock the projects_cache to return a known value
    mock_cache = mocker.MagicMock()
    mock_cache.name_from_id.return_value = "invalid_drive|Project1"
    mocker.patch("modern.ids.projects_cache", mock_cache)

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Use a dummy project hash (the actual value doesn't matter as we're mocking the cache)
    invalid_drive_hash = "dummy_hash"

    # Make request to the /projects/{project_id} endpoint with the token and a valid hash with an invalid drive
    response = app_client.get(
        f"/projects/{invalid_drive_hash}",
        headers={"Authorization": f"Bearer {token}"},
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
    mocker: MockFixture, app_client, local_db
):
    """Test that the /projects/{project_id} endpoint returns 404 when the project does not exist"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Create a mock drive path
    from pathlib import Path

    mock_drive_path = mocker.MagicMock(spec=Path)
    mock_drive_path.name = "drive1"
    mock_drive_path.__str__.return_value = "/path/to/drive1"

    # Mock get_drive_path to return our mock drive path
    mock_get_drive_path = mocker.patch("modern.ids.get_drive_path")
    mock_get_drive_path.return_value = mock_drive_path

    # Mock Path.exists and Path.is_dir to simulate a non-existent project
    mock_exists = mocker.patch("pathlib.Path.exists")
    mock_is_dir = mocker.patch("pathlib.Path.is_dir")
    mock_exists.return_value = False
    mock_is_dir.return_value = False

    # Mock the projects_cache to return a known value
    mock_cache = mocker.MagicMock()
    mock_cache.name_from_id.return_value = "drive1|NonExistentProject"
    mocker.patch("modern.ids.projects_cache", mock_cache)

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Use a dummy project hash (the actual value doesn't matter as we're mocking the cache)
    invalid_project_hash = "dummy_hash"

    # Make request to the /projects/{project_id} endpoint with the token and a valid hash with a non-existent project
    response = app_client.get(
        f"/projects/{invalid_project_hash}",
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


def test_project_by_id_endpoint_with_invalid_format(app_client, local_db, mocker):
    """Test that the /projects/{project_id} endpoint returns an error when the project_id is not in the correct format"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock the projects_cache to raise a KeyError when name_from_id is called with an invalid ID
    mock_cache = mocker.MagicMock()
    mock_cache.name_from_id.side_effect = KeyError("Invalid ID")
    mocker.patch("modern.ids.projects_cache", mock_cache)

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Make request to the /projects/{project_id} endpoint with the token and a project_id in an invalid format
    response = app_client.get(
        "/projects/invalid_format",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that the response is an error
    assert response.status_code == 400

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_project_by_id_endpoint_without_token(app_client, mocker):
    """Test that the /projects/{project_id} endpoint returns 401 without a token"""
    # Mock the projects_cache to return a known value
    mock_cache = mocker.MagicMock()
    mock_cache.id_from_name.return_value = "dummy_id"
    mocker.patch("modern.ids.projects_cache", mock_cache)

    # Generate a project hash for our test project
    project_hash = "dummy_id"

    # Make request to the /projects/{project_id} endpoint without a token
    response = app_client.get(f"/projects/{project_hash}")

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401


def test_project_by_id_endpoint_with_invalid_token(app_client, mocker):
    """Test that the /projects/{project_id} endpoint returns 401 with an invalid token"""
    # Mock the projects_cache to return a known value
    mock_cache = mocker.MagicMock()
    mock_cache.id_from_name.return_value = "dummy_id"
    mocker.patch("modern.ids.projects_cache", mock_cache)

    # Generate a project hash for our test project
    project_hash = "dummy_id"

    # Make request to the /projects/{project_id} endpoint with an invalid token
    response = app_client.get(
        f"/projects/{project_hash}",
        headers={"Authorization": "Bearer invalid_token"},
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401
