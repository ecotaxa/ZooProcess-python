# A Datasource which mixes legacy scan CSV table with modern additions
from typing import List, Dict

from sqlalchemy.orm import Session

from Models import SubSampleIn
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from local_DB.models import InFlightScan
from logger import logger
from modern.ids import scan_name_from_subsample_name


def get_project_scans_metadata(
    db: Session,
    zoo_project: ZooscanProjectFolder,
) -> List[Dict[str, str]]:
    """
    Get the scans metadata for a project.

    This function calls read_scans_table() on a ZooscanProjectFolder to retrieve
    the scans metadata for the legacy project and amends it with deserialized data from InFlightScan.

    Args:
        db (sqlalchemy.orm.Session): The SQLAlchemy session to use.
        zoo_project (ZooscanProjectFolder): The project folder to get scans metadata from.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the scans metadata.
    """
    # Get the scans metadata from the project
    lgcy_scans_metadata = zoo_project.zooscan_meta.read_scans_table()

    # Extract drive name from the project path
    drive_path = zoo_project.path.parent
    drive_name = drive_path.name

    # Get the in-flight scans for this project and drive
    in_flight_scans = (
        db.query(InFlightScan)
        .filter_by(drive_name=drive_name, project_name=zoo_project.project)
        .all()
    )

    # Create a dictionary for quick lookup
    in_flight_scans_dict = {scan.scan_id: scan for scan in in_flight_scans}

    # Create a set of scan IDs that are already in the scans metadata
    existing_scan_ids = {
        scan_metadata["scanid"]
        for scan_metadata in lgcy_scans_metadata
        if "scanid" in scan_metadata
    }

    # Append in-flight scans to the result
    for scan_id, in_flight_scan in in_flight_scans_dict.items():
        if scan_id not in existing_scan_ids:
            # Create a new scan metadata entry from the in-flight scan data
            new_scan_metadata = {"scanid": scan_id}
            # noinspection PyTypeChecker
            new_scan_metadata.update(in_flight_scan.scan_data)
            lgcy_scans_metadata.append(new_scan_metadata)

    return lgcy_scans_metadata


def get_project_scans(db: Session, zoo_project: ZooscanProjectFolder) -> List[str]:
    ret = list(zoo_project.list_scans_with_state())

    # Extract drive name from the project path
    drive_path = zoo_project.path.parent
    drive_name = drive_path.name

    # Get the in-flight scans for this project and drive
    in_flight_scans = (
        db.query(InFlightScan)
        .filter_by(drive_name=drive_name, project_name=zoo_project.project)
        .all()
    )
    # noinspection PyTypeChecker
    ret.extend([scan.scan_id for scan in in_flight_scans])
    return ret


def add_subsample(
    db: Session,
    zoo_project: ZooscanProjectFolder,
    sample_name: str,
    subsample: SubSampleIn,
):
    """Add a subsample, in legacy filesystem, to a sample"""
    logger.info(
        f"Adding subsample with parameters: project_path={zoo_project}, sample_name={sample_name}, subsample={subsample}"
    )

    # Create scan data dictionary
    data = subsample.data
    # "spliting_ratio": 4,  from data, TODO, where?
    scan_id = scan_name_from_subsample_name(sample_name + "_" + data["scan_id"])
    scan_id = scan_name_from_subsample_name(
        subsample.name
    )  # Looks like it's not following conventions intentionally
    scan_data = {
        "scanid": scan_id,
        "sampleid": sample_name,
        "scanop": data["scanning_operator"],
        "fracid": data["fraction_id_suffix"],
        "fracmin": data["fraction_min_mesh"],
        "fracsup": data["fraction_max_mesh"],
        "fracnb": data["fraction_number"],
        "observation": data["observation"],
        "code": "1",
        "submethod": "1",
        "cellpart": "1",
        "replicates": "1",
        "volini": "1",
        "volprec": "1",
    }

    # Delete any pre-existing InFlightScan record with the same identifiers
    drive_name = zoo_project.path.parent.name
    db.query(InFlightScan).filter_by(
        drive_name=drive_name, project_name=zoo_project.project, scan_id=scan_id
    ).delete()  # TODO: Temporary until ID generation logic is cleared on front side

    # Add an InFlightScan record to the database
    in_flight_scan = InFlightScan(
        drive_name=drive_name,
        project_name=zoo_project.project,
        scan_id=scan_id,
        scan_data=scan_data,
    )
    db.add(in_flight_scan)
    db.commit()
    return scan_id
