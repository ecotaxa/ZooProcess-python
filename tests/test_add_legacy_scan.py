import os
import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path

from sqlalchemy.orm import Session

from Models import SubSampleIn, SubSampleData
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from legacy.writers.scan import add_legacy_scan
from legacy.scans import ScanCSVLine, SCAN_CSV_COLUMNS
from modern.subsample import add_subsample
from local_DB.models import InFlightScan


def test_add_legacy_scan_with_add_subsample(local_db):
    """Test that add_legacy_scan works correctly with a scan created by add_subsample."""
    # Create a mock ZooscanProjectFolder
    mock_project = MagicMock(spec=ZooscanProjectFolder)
    mock_project.project = "test_project"

    # Set up the path attribute for drive name extraction
    mock_path = MagicMock()
    mock_parent = MagicMock()
    mock_parent.name = "test_drive"
    mock_path.parent = mock_parent
    mock_project.path = mock_path

    # Create a mock for the zooscan_meta attribute
    mock_zooscan_meta = MagicMock()
    mock_project.zooscan_meta = mock_zooscan_meta

    # Create a temporary file for the scans table
    temp_scans_table = Path("temp_scans_table.csv")
    mock_zooscan_meta.scans_table_path = str(temp_scans_table)

    # Sample and subsample data
    sample_name = "test_sample"
    subsample_name = f"{sample_name}_d1"

    # Create a SubSampleIn object
    subsample_data = SubSampleData(
        scan_id="d1",
        scanning_operator="test_operator",
        fraction_id_suffix="d1",
        fraction_min_mesh=100,
        fraction_max_mesh=200,
        spliting_ratio=1,
        fraction_number="1",
        observation="Test observation",
    )
    subsample = SubSampleIn(
        name=subsample_name,
        data=subsample_data,
        metadataModelId="test_metadata_model_id",
    )

    # Add the subsample using add_subsample
    scan_id = add_subsample(local_db, mock_project, sample_name, subsample)

    # Verify that the InFlightScan record was created
    in_flight_scan = (
        local_db.query(InFlightScan)
        .filter_by(
            drive_name="test_drive", project_name="test_project", scan_id=scan_id
        )
        .first()
    )
    assert in_flight_scan is not None
    assert in_flight_scan.scan_data["scanid"] == scan_id
    assert in_flight_scan.scan_data["sampleid"] == sample_name
    assert in_flight_scan.scan_data["scanop"] == "test_operator"
    assert in_flight_scan.scan_data["fracid"] == "d1"

    # Now use add_legacy_scan to process the InFlightScan record
    # Create a mock for csv.DictReader
    mock_reader = MagicMock()
    mock_reader.fieldnames = [
        "scanid",
        "sampleid",
        "scanop",
        "fracid",
        "fracmin",
        "fracsup",
        "fracnb",
        "observation",
        "code",
        "submethod",
        "cellpart",
        "replicates",
        "volini",
        "volprec",
    ]

    # Mock open, csv.DictReader, and ScanCSVLine
    with patch("builtins.open", create=True) as mock_open, patch(
        "csv.DictReader", return_value=mock_reader
    ), patch("legacy.writers.scan.ScanCSVLine") as mock_scan_csv_line, patch(
        "legacy.writers.scan.SCAN_CSV_COLUMNS", SCAN_CSV_COLUMNS
    ):

        # Configure the mock ScanCSVLine to return an object with the expected keys
        mock_scan_csv_line_instance = MagicMock()
        mock_scan_csv_line_instance.keys.return_value = SCAN_CSV_COLUMNS
        mock_scan_csv_line.return_value = mock_scan_csv_line_instance

        # Mock file for writing
        mock_file = MagicMock()
        mock_file.tell.return_value = 0  # Simulate a new file
        mock_open.return_value.__enter__.return_value = mock_file

        # Call add_legacy_scan
        result_scan_id = add_legacy_scan(local_db, mock_project, scan_id)

        # Verify that add_legacy_scan returned the correct scan_id
        assert result_scan_id == scan_id

        # Verify that the file was opened for reading and writing
        assert mock_open.call_count >= 2

        # Check for the write operation
        write_call = [call for call in mock_open.call_args_list if "a" in call[0][1]]
        assert len(write_call) > 0
        assert write_call[0][0][0] == str(temp_scans_table)

        # Verify that data was written to the file
        assert mock_file.write.called or hasattr(mock_file, "writerow")

    # Verify that the InFlightScan record was deleted
    in_flight_scan = (
        local_db.query(InFlightScan)
        .filter_by(
            drive_name="test_drive", project_name="test_project", scan_id=scan_id
        )
        .first()
    )
    assert in_flight_scan is None
