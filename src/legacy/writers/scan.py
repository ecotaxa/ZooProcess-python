import csv

from sqlalchemy.orm import Session

from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from legacy.scans import SCAN_CSV_COLUMNS
from local_DB.models import InFlightScan
from modern.to_legacy import reconstitute_csv_line


def add_legacy_scan(
    db: Session,
    zoo_project: ZooscanProjectFolder,
    scan_id: str,
):
    """
    Add a legacy scan to the system, i.e. persist in CSV an in-flight one.

    Args:
        db (Session): The database session
        zoo_project (ZooscanProjectFolder): The project folder
        sample_name (str): The name of the sample
        scan_id (str): The ID of the scan

    """
    # Extract drive name from the project path
    drive_name = zoo_project.path.parent.name

    # Get the InFlightScan record before deleting it
    in_flight_scan = (
        db.query(InFlightScan)
        .filter_by(
            drive_name=drive_name, project_name=zoo_project.project, scan_id=scan_id
        )
        .first()
    )

    if in_flight_scan:
        # Extract scan_data from the record
        scan_data = in_flight_scan.scan_data

        # Write scan_data to the scan header table CSV file
        scans_table_path = zoo_project.zooscan_meta.scans_table_path

        # Read existing headers from the CSV file
        try:
            with open(
                scans_table_path, "r", newline="", encoding="ISO-8859-1"
            ) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=";")
                fieldnames = reader.fieldnames
                assert fieldnames is not None
        except FileNotFoundError:
            # If file doesn't exist, use Line structure
            fieldnames = SCAN_CSV_COLUMNS

        # Append the scan_data to the CSV file
        with open(scans_table_path, "a", newline="", encoding="ISO-8859-1") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")

            # If file is new, write the header
            if csvfile.tell() == 0:
                writer.writeheader()

            csv_line = reconstitute_csv_line(scan_data)
            assert list(csv_line.keys()) == SCAN_CSV_COLUMNS

            # Write the scan_data row
            writer.writerow(csv_line)

        # Delete the record from the database
        db.query(InFlightScan).filter_by(
            drive_name=drive_name, project_name=zoo_project.project, scan_id=scan_id
        ).delete()
        db.commit()

    return scan_id
