# A Datasource which mixes legacy scan CSV table with modern additions
from functools import lru_cache
from typing import List, Optional, NamedTuple, cast, Dict

from sqlalchemy.orm import Session

from Models import SubSampleIn
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from helpers.logger import logger
from legacy.scans import ScanCSVLine, read_scans_metadata_table
from local_DB.models import InFlightScan
from modern.ids import scan_name_from_subsample_name
from modern.to_legacy import reconstitute_csv_line, reconstitute_fracid


class FracIdComponents(NamedTuple):
    primary_fraction: str
    pattern_type: str
    sub_fraction: Optional[str] = None
    denominator: Optional[int] = None


@lru_cache(maxsize=1, typed=True)
def get_project_scans_metadata(
    db: Session,
    zoo_project: ZooscanProjectFolder,
) -> List[ScanCSVLine]:
    """
    Get the scans metadata for a project.

    This function calls read_scans_table() on a ZooscanProjectFolder to retrieve
    the scans metadata for the legacy project and amends it with deserialized data
    from InFlightScan DB table.

    Args:
        db (sqlalchemy.orm.Session): The SQLAlchemy session to use.
        zoo_project (ZooscanProjectFolder): The project folder to get scans metadata from.

    Returns:
        List[ScanCSVLine]: A list of ScanCSVLine objects containing the scans metadata.
    """
    # Get the scans metadata from the project
    lgcy_scans_metadata = read_scans_metadata_table(zoo_project)

    # Extract drive name from the project path
    drive_path = zoo_project.path.parent
    drive_name = drive_path.name

    # Get the in-flight scans for this project and drive
    in_flight_scans = (
        db.query(InFlightScan)
        .filter_by(drive_name=drive_name, project_name=zoo_project.project)
        .all()
    )

    # Create a dictionary for a quick lookup
    in_flight_scans_dict = {scan.scan_id: scan for scan in in_flight_scans}

    # Create a set of scan IDs that are already in the scans metadata
    existing_scan_ids = {
        scan_metadata["scanid"] for scan_metadata in lgcy_scans_metadata
    }

    # Append in-flight scans to the result
    for scan_id, in_flight_scan in in_flight_scans_dict.items():
        if scan_id not in existing_scan_ids:
            # Create a new scan metadata entry from the in-flight scan data
            new_scan_metadata = reconstitute_csv_line(in_flight_scan.scan_data)
            lgcy_scans_metadata.append(new_scan_metadata)

    result: List[ScanCSVLine] = []
    for scan_metadata in lgcy_scans_metadata:
        result.append(scan_metadata)

    return result


@lru_cache(maxsize=1, typed=True)
def get_project_scans(db: Session, zoo_project: ZooscanProjectFolder) -> List[str]:
    ret = list(zoo_project.list_scans_with_state())

    # Extract drive name from the project path
    drive_path = zoo_project.path.parent
    drive_name = drive_path.name

    # Get the in-flight scans for this project and drive
    in_flight_qry = db.query(InFlightScan).filter_by(
        drive_name=drive_name, project_name=zoo_project.project
    )
    # noinspection PyTypeChecker
    ret.extend([scan.scan_id for scan in in_flight_qry])
    return ret


def parse_fracid(fracid: str) -> FracIdComponents:
    """
    Parse a 'fracid' (fraction_id) value into its components.

    The function handles the following patterns:
    1. Simple identifiers: 'd1', 'd2', 'd3'
    2. Complex patterns: 'dx_y_sur_z' where:
       - 'dx' is a primary fraction category (d1, d2, d3)
       - 'y' is a sub-fraction number (typically 1-8)
       - 'z' represents a denominator in a fraction (1, 2, 3, 4, 5, 8)
    3. Total samples: 'tot'

    Args:
        fracid (str): The fraction ID to parse

    Returns:
        FracIdComponents: A named tuple containing the parsed components:
            - primary_fraction: The primary fraction identifier (e.g., 'd1', 'd2', 'd3', 'tot')
            - pattern_type: The type of pattern detected ('simple', 'complex', 'total', 'unknown')
            - sub_fraction: The sub-fraction (e.g., 1_sur_1 or 3_sur_4) or None if not applicable
            - denominator: The denominator in a fraction (e.g., 1, 2, 4, 8) or None if not applicable
    """
    # Handle 'tot' (total) case
    if fracid.lower() == "tot":
        return FracIdComponents(
            primary_fraction="tot",
            pattern_type="total",
        )

    # Handle complex pattern: 'dx_y_sur_z'
    if "_" in fracid and "sur" in fracid.lower():
        parts = fracid.split("_")
        if len(parts) >= 4:
            try:
                sub_fraction = "_".join(parts[1:])
                denominator = int(parts[3])
                return FracIdComponents(
                    primary_fraction=parts[0],
                    pattern_type="complex",
                    sub_fraction=sub_fraction,
                    denominator=denominator,
                )
            except (ValueError, IndexError):
                # Handle malformed values gracefully
                return FracIdComponents(
                    primary_fraction=fracid,
                    pattern_type="unknown",
                )
        else:
            # Handle malformed complex patterns (not enough parts)
            return FracIdComponents(
                primary_fraction=fracid,
                pattern_type="unknown",
            )

    # Handle simple pattern: 'd1', 'd2', 'd3'
    if fracid.startswith("d") and len(fracid) > 1 and fracid[1:].isdigit():
        return FracIdComponents(
            primary_fraction=fracid,
            pattern_type="simple",
        )

    # If we get here, it's an unknown pattern
    return FracIdComponents(
        primary_fraction=fracid,
        pattern_type="unknown",
    )


def add_subsample(
    db: Session,
    zoo_project: ZooscanProjectFolder,
    sample_name: str,
    subsample: SubSampleIn,
):
    """Add an in-flight subsample, to a sample"""
    logger.info(
        f"Adding subsample with parameters: project_path={zoo_project}, sample_name={sample_name}, subsample={subsample}"
    )

    # Create scan data dictionary
    data = subsample.data
    scan_id = scan_name_from_subsample_name(subsample.name)
    scan_data = ScanCSVLine(
        scanid=scan_id,
        sampleid=sample_name,
        scanop=data.scanning_operator,
        fracid=reconstitute_fracid(data.fraction_id, data.fraction_id_suffix),
        fracmin=str(data.fraction_min_mesh),
        fracsup=str(data.fraction_max_mesh),
        fracnb=str(data.spliting_ratio),
        observation=data.observation,
        code="1",
        submethod=data.submethod,
        cellpart="1",
        replicates="1",
        volini="1",
        volprec="1",
    )

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
        scan_data=cast(Dict[str, str], scan_data),
    )
    db.add(in_flight_scan)
    db.commit()
    return scan_id
