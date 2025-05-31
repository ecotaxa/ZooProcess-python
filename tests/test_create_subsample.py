from pathlib import Path
from unittest.mock import MagicMock
from pytest_mock import MockFixture

from local_DB.db_dependencies import get_db
from local_DB.models import InFlightScan
from main import app
from Models import SubSampleIn, SubSample
from modern.ids import scan_name_from_subsample_name
from legacy.utils import find_scan_metadata


def test_create_subsample(mocker: MockFixture, app_client, local_db):
    """Test that the create_subsample endpoint creates a subsample and returns it"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock only the necessary dependencies that interact with external systems
    mock_drive_and_project_from_hash = mocker.patch(
        "routers.subsamples.drive_and_project_from_hash"
    )
    mock_check_sample_exists = mocker.patch("routers.subsamples.check_sample_exists")
    mock_zooscan_drive = mocker.patch("routers.subsamples.ZooscanDrive")
    # Note: We're not mocking add_subsample anymore as per the issue description
    mock_get_project_scans_metadata = mocker.patch(
        "routers.subsamples.get_project_scans_metadata"
    )
    mock_subsample_from_legacy = mocker.patch(
        "routers.subsamples.subsample_from_legacy"
    )

    # Set up the mocks
    mock_drive_and_project_from_hash.return_value = ("/path/to/drive", "test_project")
    # Create a mock ZooscanProjectFolder object
    mock_project_folder = MagicMock()
    mock_project_folder.project = "test_project"
    mock_project_folder.path = Path("/path/to/drive/test_project")
    mock_zooscan_drive.return_value.get_project_folder.return_value = (
        mock_project_folder
    )

    # Prepare test data
    project_hash = "test_project_hash"
    sample_id = "test_sample_id"
    subsample_name = "test_subsample"
    subsample_data = {
        "name": subsample_name,
        "metadataModelId": "test_metadata_model_id",
        "data": {
            "scanning_operator": "Test Operator",
            "scan_id": "test_scan_id",
            "fraction_number": "d1",
            "fraction_id_suffix": "01",
            "fraction_min_mesh": 200,
            "fraction_max_mesh": 300,
            "spliting_ratio": 4,
            "observation": "Test observation",
        },
    }

    # Create test metadata for find_scan_metadata to use
    # Use the real scan_name_from_subsample_name function to get the scan_id
    scan_id = scan_name_from_subsample_name(subsample_name)
    test_metadata = {
        "sampleid": sample_id,
        "scanid": scan_id,
        "metadata": "test_metadata",
    }
    mock_get_project_scans_metadata.return_value = [test_metadata]

    # Mock the subsample_from_legacy to return a SubSample object
    mock_subsample = SubSample(
        id="test_subsample_id",
        name=subsample_name,
        metadata=[],
        scan=[],
        createdAt="2023-01-01T00:00:00",
        updatedAt="2023-01-01T00:00:00",
    )
    mock_subsample_from_legacy.return_value = mock_subsample

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Make request to the create_subsample endpoint
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_id}/subsamples",
        json=subsample_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response contains the created subsample
    created_subsample = response.json()
    assert created_subsample is not None
    assert created_subsample["id"] == mock_subsample.id
    assert created_subsample["name"] == mock_subsample.name

    # Verify that the necessary functions were called with the correct arguments
    mock_drive_and_project_from_hash.assert_called_once_with(project_hash)
    mock_check_sample_exists.assert_called_once_with(project_hash, sample_id)
    mock_zooscan_drive.assert_called_once()
    mock_zooscan_drive.return_value.get_project_folder.assert_called_once_with(
        "test_project"
    )
    # Check that the record was added to the database
    # Note: We're not mocking add_subsample anymore, so we check the database directly
    in_flight_scan = (
        local_db.query(InFlightScan)
        .filter_by(
            project_name="test_project", scan_id=subsample_data["metadataModelId"]
        )
        .first()
    )
    assert in_flight_scan is not None
    assert in_flight_scan.scan_data["subsample"] == subsample_data["name"]
    assert in_flight_scan.scan_data["sample"] == sample_id

    mock_get_project_scans_metadata.assert_called_once()
    # We're using the real scan_name_from_subsample_name function now
    # We're using the real find_scan_metadata function now
    mock_subsample_from_legacy.assert_called_once_with(
        mock_project_folder,
        sample_id,
        subsample_data["name"],
        test_metadata,
    )

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_create_subsample_project_not_found(mocker: MockFixture, app_client, local_db):
    """Test that the create_subsample endpoint returns 404 when the project is not found"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock the necessary dependencies
    mock_drive_and_project_from_hash = mocker.patch(
        "routers.subsamples.drive_and_project_from_hash"
    )

    # Set up the mock to raise an HTTPException
    from fastapi import HTTPException

    mock_drive_and_project_from_hash.side_effect = HTTPException(
        status_code=404, detail="Project not found"
    )

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Prepare test data
    project_hash = "nonexistent_project_hash"
    sample_id = "test_sample_id"
    subsample_data = {
        "name": "test_subsample",
        "metadataModelId": "test_metadata_model_id",
        "data": {},
    }

    # Make request to the create_subsample endpoint
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_id}/subsamples",
        json=subsample_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that the response is 404 Not Found
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]

    # Verify that the necessary functions were called with the correct arguments
    mock_drive_and_project_from_hash.assert_called_once_with(project_hash)

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_create_subsample_sample_not_found(mocker: MockFixture, app_client, local_db):
    """Test that the create_subsample endpoint returns 404 when the sample is not found"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock the necessary dependencies
    mock_drive_and_project_from_hash = mocker.patch(
        "routers.subsamples.drive_and_project_from_hash"
    )
    mock_check_sample_exists = mocker.patch("routers.subsamples.check_sample_exists")

    # Set up the mocks
    mock_drive_and_project_from_hash.return_value = ("/path/to/drive", "test_project")

    # Set up the mock to raise an HTTPException
    from fastapi import HTTPException

    mock_check_sample_exists.side_effect = HTTPException(
        status_code=404, detail="Sample not found"
    )

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Prepare test data
    project_hash = "test_project_hash"
    sample_id = "nonexistent_sample_id"
    subsample_data = {
        "name": "test_subsample",
        "metadataModelId": "test_metadata_model_id",
        "data": {},
    }

    # Make request to the create_subsample endpoint
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_id}/subsamples",
        json=subsample_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that the response is 404 Not Found
    assert response.status_code == 404
    assert "Sample not found" in response.json()["detail"]

    # Verify that the necessary functions were called with the correct arguments
    mock_drive_and_project_from_hash.assert_called_once_with(project_hash)
    mock_check_sample_exists.assert_called_once_with(project_hash, sample_id)

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_create_subsample_without_token(app_client):
    """Test that the create_subsample endpoint returns 401 without a token"""
    # Prepare test data
    project_hash = "test_project_hash"
    sample_id = "test_sample_id"
    subsample_data = {
        "name": "test_subsample",
        "metadataModelId": "test_metadata_model_id",
        "data": {},
    }

    # Make request to the create_subsample endpoint without a token
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_id}/subsamples", json=subsample_data
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401


def test_create_subsample_with_invalid_token(app_client):
    """Test that the create_subsample endpoint returns 401 with an invalid token"""
    # Prepare test data
    project_hash = "test_project_hash"
    sample_id = "test_sample_id"
    subsample_data = {
        "name": "test_subsample",
        "metadataModelId": "test_metadata_model_id",
        "data": {},
    }

    # Make request to the create_subsample endpoint with an invalid token
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_id}/subsamples",
        json=subsample_data,
        headers={"Authorization": "Bearer invalid_token"},
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401
