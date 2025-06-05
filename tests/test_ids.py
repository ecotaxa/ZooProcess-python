import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from modern.ids import (
    hash_from_project,
    drive_and_project_from_hash,
    subsample_name_from_scan_name,
    scan_name_from_subsample_name,
    THE_SCAN_PER_SUBSAMPLE,
    DO_HASH,
)


def test_hash_from_project():
    """Test that hash_from_project correctly creates a hash from a project path."""
    # Create a mock Path object
    mock_path = Path("/drives/test_drive/test_project")

    # Call the function
    result = hash_from_project(mock_path)

    # Check that the result is as expected
    # If DO_HASH is True, the function returns a base64 encoded string
    # If DO_HASH is False, the function returns the original string
    expected = (
        "dGVzdF9kcml2ZXx0ZXN0X3Byb2plY3Q=" if DO_HASH else "test_drive|test_project"
    )
    assert result == expected


@patch("modern.ids.get_drive_path")
def test_drive_and_project_from_hash_success(mock_get_drive_path):
    """Test that drive_and_project_from_hash correctly extracts drive and project names."""
    # Set up the mock to return a valid drive path
    mock_drive_path = Path("/drives/test_drive")
    mock_get_drive_path.return_value = mock_drive_path

    # Create a mock project path that exists and is a directory
    mock_project_path = mock_drive_path / "test_project"

    # Use different input based on DO_HASH
    project_hash = (
        "dGVzdF9kcml2ZXx0ZXN0X3Byb2plY3Q=" if DO_HASH else "test_drive|test_project"
    )

    # Mock the exists and is_dir methods
    with patch.object(Path, "exists", return_value=True), patch.object(
        Path, "is_dir", return_value=True
    ):
        # Call the function
        drive_path, project_name = drive_and_project_from_hash(project_hash)

        # Check that the result is as expected
        assert drive_path == mock_drive_path
        assert project_name == "test_project"

        # Check that get_drive_path was called with the correct argument
        mock_get_drive_path.assert_called_once_with("test_drive")


@patch("modern.ids.get_drive_path")
def test_hash_from_project_and_drive_and_project_from_hash_roundtrip(
    mock_get_drive_path,
):
    """Test the roundtrip functionality of hash_from_project and drive_and_project_from_hash."""
    # Set up the mock to return a valid drive path
    mock_drive_path = Path("/drives/test_drive")
    mock_get_drive_path.return_value = mock_drive_path

    # Create a mock project path
    mock_project_path = mock_drive_path / "test_project"

    # Step 1: Generate a hash from the project path
    project_hash = hash_from_project(mock_project_path)

    # Verify the hash is correctly formatted based on DO_HASH
    expected_hash = (
        "dGVzdF9kcml2ZXx0ZXN0X3Byb2plY3Q=" if DO_HASH else "test_drive|test_project"
    )
    assert project_hash == expected_hash

    # Step 2: Extract drive path and project name from the hash
    # Mock the exists and is_dir methods
    with patch.object(Path, "exists", return_value=True), patch.object(
        Path, "is_dir", return_value=True
    ):
        extracted_drive_path, extracted_project_name = drive_and_project_from_hash(
            project_hash
        )

        # Verify the extracted information matches the original input
        assert extracted_drive_path == mock_drive_path
        assert extracted_project_name == "test_project"

        # Verify that the reconstructed project path matches the original
        reconstructed_project_path = extracted_drive_path / extracted_project_name
        assert str(reconstructed_project_path) == str(mock_project_path)

        # Check that get_drive_path was called with the correct argument
        mock_get_drive_path.assert_called_once_with("test_drive")


@patch("modern.ids.get_drive_path")
def test_drive_and_project_from_hash_invalid_format(mock_get_drive_path):
    """Test that drive_and_project_from_hash raises an exception for invalid hash format."""
    # Use different input based on DO_HASH
    invalid_hash = (
        "aW52YWxpZF9oYXNo" if DO_HASH else "invalid_hash"
    )  # Base64 for "invalid_hash" if DO_HASH is True

    # Call the function with an invalid hash format
    with pytest.raises(HTTPException) as excinfo:
        drive_and_project_from_hash(invalid_hash)

    # Check that the exception has the expected status code and detail
    assert excinfo.value.status_code == 400
    assert "Invalid project ID format: invalid_hash" in excinfo.value.detail

    # Check that get_drive_path was not called
    mock_get_drive_path.assert_not_called()


@patch("modern.ids.get_drive_path")
def test_drive_and_project_from_hash_drive_not_found(mock_get_drive_path):
    """Test that drive_and_project_from_hash raises an exception when the drive is not found."""
    # Set up the mock to return None (drive not found)
    mock_get_drive_path.return_value = None

    # Use different input based on DO_HASH
    project_hash = (
        "dGVzdF9kcml2ZXx0ZXN0X3Byb2plY3Q=" if DO_HASH else "test_drive|test_project"
    )

    # Call the function
    with pytest.raises(HTTPException) as excinfo:
        drive_and_project_from_hash(project_hash)

    # Check that the exception has the expected status code and detail
    assert excinfo.value.status_code == 404
    assert "Project with ID test_drive|test_project not found" in excinfo.value.detail

    # Check that get_drive_path was called with the correct argument
    mock_get_drive_path.assert_called_once_with("test_drive")


@patch("modern.ids.get_drive_path")
def test_drive_and_project_from_hash_project_not_found(mock_get_drive_path):
    """Test that drive_and_project_from_hash raises an exception when the project is not found."""
    # Set up the mock to return a valid drive path
    mock_drive_path = Path("/drives/test_drive")
    mock_get_drive_path.return_value = mock_drive_path

    # Use different input based on DO_HASH
    project_hash = (
        "dGVzdF9kcml2ZXx0ZXN0X3Byb2plY3Q=" if DO_HASH else "test_drive|test_project"
    )

    # Mock the exists method to return False (project not found)
    with patch.object(Path, "exists", return_value=False):
        # Call the function
        with pytest.raises(HTTPException) as excinfo:
            drive_and_project_from_hash(project_hash)

        # Check that the exception has the expected status code and detail
        assert excinfo.value.status_code == 404
        assert (
            "Project with ID test_drive|test_project not found" in excinfo.value.detail
        )

        # Check that get_drive_path was called with the correct argument
        mock_get_drive_path.assert_called_once_with("test_drive")


@patch("modern.ids.get_drive_path")
def test_drive_and_project_from_hash_not_a_directory(mock_get_drive_path):
    """Test that drive_and_project_from_hash raises an exception when the project is not a directory."""
    # Set up the mock to return a valid drive path
    mock_drive_path = Path("/drives/test_drive")
    mock_get_drive_path.return_value = mock_drive_path

    # Use different input based on DO_HASH
    project_hash = (
        "dGVzdF9kcml2ZXx0ZXN0X3Byb2plY3Q=" if DO_HASH else "test_drive|test_project"
    )

    # Mock the exists method to return True but is_dir to return False
    with patch.object(Path, "exists", return_value=True), patch.object(
        Path, "is_dir", return_value=False
    ):
        # Call the function
        with pytest.raises(HTTPException) as excinfo:
            drive_and_project_from_hash(project_hash)

        # Check that the exception has the expected status code and detail
        assert excinfo.value.status_code == 404
        assert (
            "Project with ID test_drive|test_project not found" in excinfo.value.detail
        )

        # Check that get_drive_path was called with the correct argument
        mock_get_drive_path.assert_called_once_with("test_drive")


def test_subsample_name_from_scan_name():
    """Test that subsample_name_from_scan_name correctly extracts the subsample name."""
    # Test with a scan name that has the expected suffix
    scan_name = f"test_subsample_{THE_SCAN_PER_SUBSAMPLE}"
    result = subsample_name_from_scan_name(scan_name)
    assert result == "test_subsample"

    # Test with a scan name that doesn't have the expected suffix
    scan_name = "test_subsample"
    result = subsample_name_from_scan_name(scan_name)
    assert result == "test_subsample"

    # Test with a scan name that has a different suffix
    scan_name = "test_subsample_2"
    result = subsample_name_from_scan_name(scan_name)
    assert result == "test_subsample_2"


def test_scan_name_from_subsample_name():
    """Test that scan_name_from_subsample_name correctly creates a scan name."""
    # Test with a simple subsample name
    subsample_name = "test_subsample"
    result = scan_name_from_subsample_name(subsample_name)
    assert result == f"test_subsample_{THE_SCAN_PER_SUBSAMPLE}"

    # Test with a subsample name that already has a suffix
    subsample_name = "test_subsample_2"
    result = scan_name_from_subsample_name(subsample_name)
    assert result == f"test_subsample_2_{THE_SCAN_PER_SUBSAMPLE}"
