import importlib

from pytest_mock import MockFixture

import config_rdr
from conftest import DATA_DIR
from local_DB.db_dependencies import get_db
from local_DB.models import InFlightScan
from main import app
from modern.ids import (
    scan_name_from_subsample_name,
    hash_from_sample_name,
    hash_from_project,
)


def test_create_subsample(mocker: MockFixture, app_client, local_db):
    """Test that the create_subsample endpoint creates a subsample and returns it"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db
    # Point drives config to test data
    mock_drives_config = mocker.patch("legacy.drives.config.get_drives")

    # Prepare test data
    drive = DATA_DIR / "test_drive"
    mock_drives_config.return_value = [drive]
    project = drive / "test_project"
    project_hash = hash_from_project(project)
    sample_id = "jb19740123"
    sample_hash = hash_from_sample_name(sample_id)

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

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Make a request to the create_subsample endpoint
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_hash}/subsamples",
        json=subsample_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that the response is successful
    assert response.status_code == 200, response.text

    # Check that the response contains the created subsample
    created_subsample = response.json()
    assert created_subsample is not None
    assert created_subsample["name"] == subsample_name
    # There should be no attached scans yet
    assert created_subsample["scan"] == []

    # Check that the record was added to the database
    expected_scan_id = scan_name_from_subsample_name(subsample_data["name"])
    in_flight_scan = (
        local_db.query(InFlightScan)
        .filter_by(project_name="test_project", scan_id=expected_scan_id)
        .first()
    )
    assert in_flight_scan is not None
    assert in_flight_scan.scan_data["sampleid"] == sample_id

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_create_subsample_project_not_found(mocker: MockFixture, app_client, local_db):
    """Test that the create_subsample endpoint returns 404 when the project is not found"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Mock the necessary dependencies
    mock_drive_and_project_from_hash = mocker.patch(
        "routers.utils.drive_and_project_from_hash"
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
    sample_hash = hash_from_sample_name(sample_id)
    subsample_data = {
        "name": "test_subsample",
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

    # Make request to the create_subsample endpoint
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_hash}/subsamples",
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

    # Point drives config to test data
    mock_drives_config = mocker.patch("legacy.drives.config.get_drives")

    # Prepare test data
    drive = DATA_DIR / "test_drive"
    mock_drives_config.return_value = [drive]
    project = drive / "test_project"
    project_hash = hash_from_project(project)

    # Mock list_samples_with_state to return an empty list
    # This will cause the sample validation to fail
    mock_list_samples = mocker.patch(
        "ZooProcess_lib.ZooscanFolder.ZooscanProjectFolder.list_samples_with_state"
    )
    mock_list_samples.return_value = []  # No samples in the project

    # We don't need to explicitly raise an HTTPException here, as the validate_path_components
    # function will raise it when it can't find the sample

    # First, get a valid token by logging in
    login_data = {"email": "test@example.com", "password": "test_password"}
    login_response = app_client.post("/login", json=login_data)
    token = login_response.json()

    # Prepare test data
    sample_id = "nonexistent_sample_id"
    sample_hash = hash_from_sample_name(sample_id)
    subsample_data = {
        "name": "test_subsample",
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

    # Make request to the create_subsample endpoint
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_hash}/subsamples",
        json=subsample_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that the response is 404 Not Found
    assert response.status_code == 404
    assert (
        f"Sample with ID {sample_id} not found in project {project_hash}"
        in response.json()["detail"]
    )

    # Verify that the necessary functions were called with the correct arguments
    mock_list_samples.assert_called_once()

    # Clean up the dependency override
    app.dependency_overrides.clear()


def test_create_subsample_without_token(app_client):
    """Test that the create_subsample endpoint returns 401 without a token"""
    # Prepare test data
    project_hash = "test_project_hash"
    sample_id = "test_sample_id"
    sample_hash = hash_from_sample_name(sample_id)
    subsample_data = {
        "name": "test_subsample",
        "metadataModelId": "test_metadata_model_id",
        "data": {},
    }

    # Make request to the create_subsample endpoint without a token
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_hash}/subsamples",
        json=subsample_data,
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401


def test_create_subsample_with_invalid_token(app_client):
    """Test that the create_subsample endpoint returns 401 with an invalid token"""
    # Prepare test data
    project_hash = "test_project_hash"
    sample_id = "test_sample_id"
    sample_hash = hash_from_sample_name(sample_id)
    subsample_data = {
        "name": "test_subsample",
        "metadataModelId": "test_metadata_model_id",
        "data": {},
    }

    # Make request to the create_subsample endpoint with an invalid token
    response = app_client.post(
        f"/projects/{project_hash}/samples/{sample_hash}/subsamples",
        json=subsample_data,
        headers={"Authorization": "Bearer invalid_token"},
    )

    # Check that the response is 401 Unauthorized
    assert response.status_code == 401
