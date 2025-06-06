import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from local_DB.models import InFlightScan, Base
from modern.subsample import get_project_scans_metadata
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder


def test_create_in_flight_scan(local_db):
    """Test creating an in-flight scan."""
    # Create a sample scan data
    scan_data = {
        "scanid": "test_scan_001",
        "sample": "test_sample",
        "date": "2023-01-01",
        "time": "12:00:00",
        "operator": "test_operator",
        "comment": "Test scan",
    }

    # Create an in-flight scan
    in_flight_scan = InFlightScan(
        scan_id="test_scan_001",
        project_name="test_project",
        drive_name="test_drive",
        scan_data=scan_data,
    )

    # Add the in-flight scan to the session
    local_db.add(in_flight_scan)
    local_db.commit()

    # Query the in-flight scan
    result = (
        local_db.query(InFlightScan)
        .filter_by(
            scan_id="test_scan_001",
            project_name="test_project",
            drive_name="test_drive",
        )
        .first()
    )

    # Check that the in-flight scan was created correctly
    assert result is not None
    assert result.scan_id == "test_scan_001"
    assert result.project_name == "test_project"
    assert result.drive_name == "test_drive"
    assert result.scan_data == scan_data


def test_get_project_scans_metadata(local_db):
    """Test that get_project_scans_metadata appends in-flight scans to the result from read_scans_table."""
    # Create sample scan data for existing scan in InFlightScan
    existing_scan_data = {
        "scanid": "test_scan_001",
        "sampleid": "test_sample",
        "additional_key": "additional_value",
    }

    # Create sample scan data for new scan in InFlightScan
    new_scan_data = {
        "scanid": "test_scan_003",
        "sampleid": "new_sample",
        "scanop": "new_operator",
    }

    # Create in-flight scans
    existing_in_flight_scan = InFlightScan(
        scan_id="test_scan_001",
        project_name="test_project",
        drive_name="test_drive",
        scan_data=existing_scan_data,
    )

    new_in_flight_scan = InFlightScan(
        scan_id="test_scan_003",
        project_name="test_project",
        drive_name="test_drive",
        scan_data=new_scan_data,
    )

    # Add the in-flight scans to the session
    local_db.add(existing_in_flight_scan)
    local_db.add(new_in_flight_scan)
    local_db.commit()

    # Create a mock ZooscanProjectFolder
    mock_project = MagicMock(spec=ZooscanProjectFolder)
    mock_project.project = "test_project"
    mock_project.zooscan_meta = MagicMock()

    # Set up the path attribute for drive name extraction
    mock_path = MagicMock()
    mock_parent = MagicMock()
    mock_parent.name = "test_drive"
    mock_path.parent = mock_parent
    mock_project.path = mock_path

    # Mock the read_scans_table method to return a predefined list of scans
    mock_project.zooscan_meta.read_scans_table.return_value = [
        {
            "scanid": "test_scan_001",
            "sampleid": "test_sample_from_table",
            "scanop": "table_operator",
            "fracid": "d1",
            "fracmin": "100",
            "fracsup": "200",
            "fracnb": "1",
            "observation": "test observation",
            "code": "1",
            "submethod": "test method",
            "cellpart": "1",
            "replicates": "1",
            "volini": "100",
            "volprec": "10",
        },
        {
            "scanid": "test_scan_002",  # This scan is not in InFlightScan
            "sampleid": "another_sample",
            "scanop": "another_operator",
            "fracid": "d2",
            "fracmin": "200",
            "fracsup": "300",
            "fracnb": "2",
            "observation": "another observation",
            "code": "2",
            "submethod": "another method",
            "cellpart": "2",
            "replicates": "2",
            "volini": "200",
            "volprec": "20",
        },
    ]

    # Call the function under test, passing the local_db session
    result = get_project_scans_metadata(local_db, mock_project)

    # Check that the result includes the expected number of scans (2 original + 1 new from in-flight)
    assert len(result) == 3

    # Check that the existing scans are unchanged and have all required fields
    assert result[0]["scanid"] == "test_scan_001"
    assert result[0]["sampleid"] == "test_sample_from_table"
    assert result[0]["scanop"] == "table_operator"
    assert result[0]["fracid"] == "d1"
    assert result[0]["fracmin"] == "100"
    assert result[0]["fracsup"] == "200"
    assert result[0]["fracnb"] == "1"
    assert result[0]["observation"] == "test observation"
    assert result[0]["code"] == "1"
    assert result[0]["submethod"] == "test method"
    assert result[0]["cellpart"] == "1"
    assert result[0]["replicates"] == "1"
    assert result[0]["volini"] == "100"
    assert result[0]["volprec"] == "10"
    assert (
        "additional_key" not in result[0]
    )  # No additional keys added to existing scan

    assert result[1]["scanid"] == "test_scan_002"
    assert result[1]["sampleid"] == "another_sample"
    assert result[1]["scanop"] == "another_operator"
    assert result[1]["fracid"] == "d2"
    assert result[1]["fracmin"] == "200"
    assert result[1]["fracsup"] == "300"
    assert result[1]["fracnb"] == "2"
    assert result[1]["observation"] == "another observation"
    assert result[1]["code"] == "2"
    assert result[1]["submethod"] == "another method"
    assert result[1]["cellpart"] == "2"
    assert result[1]["replicates"] == "2"
    assert result[1]["volini"] == "200"
    assert result[1]["volprec"] == "20"

    # Check that the new in-flight scan is appended to the result and has all required fields
    assert result[2]["scanid"] == "test_scan_003"
    assert result[2]["sampleid"] == "new_sample"
    assert result[2]["scanop"] == "new_operator"
    # Check that all required fields are present with default values
    assert result[2]["fracid"] == ""
    assert result[2]["fracmin"] == ""
    assert result[2]["fracsup"] == ""
    assert result[2]["fracnb"] == ""
    assert result[2]["observation"] == ""
    assert result[2]["code"] == ""
    assert result[2]["submethod"] == ""
    assert result[2]["cellpart"] == ""
    assert result[2]["replicates"] == ""
    assert result[2]["volini"] == ""
    assert result[2]["volprec"] == ""
