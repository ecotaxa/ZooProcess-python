#
# Transformers from Legacy data to modern models
#
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

from sqlalchemy.orm import Session

from Models import (
    Project,
    Drive,
    Sample,
    Background,
    Instrument,
    Scan,
    MetadataModel,
    SubSample,
    ScanTypeNum,
)
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder, ZooscanDrive
from config_rdr import config
from legacy.samples import (
    find_sample_metadata,
    SampleCSVLine,
    read_samples_metadata_table,
)
from legacy.scans import (
    find_scan_metadata,
    ScanCSVLine,
    sub_scans_metadata_table_for_sample,
)
from local_DB.data_utils import get_background_id
from logger import logger
from modern.app_urls import get_scan_url, get_background_url
from modern.ids import (
    hash_from_project,
    subsample_name_from_scan_name,
    scan_name_from_subsample_name,
    hash_from_sample_name,
    hash_from_subsample_name,
    drive_from_project_path,
)
from modern.instrument import get_instrument_by_id, INSTRUMENTS
from modern.subsample import get_project_scans_metadata, get_project_scans, parse_fracid
from modern.users import get_mock_user, user_with_name
from modern.utils import (
    extract_serial_number,
    find_latest_modification_time,
    convert_ddm_to_decimal_degrees,
)


def drives_from_legacy() -> list[Drive]:
    """
    Retrieve a list of Drive objects from the legacy configuration.

    This function reads the drive paths from the configuration and converts them
    into Drive objects with id and name set to the drive name, and url set to the drive path.

    Returns:
        list[Drive]: A list of Drive objects representing the drives configured in the app.
    """
    ret = []
    for drive in config.get_drives():
        ret.append(drive_from_legacy(drive))
    return ret


def drive_from_legacy(drive_path: Path) -> Drive:
    """
    Retrieve a Drive object from the legacy configuration.
    """
    return Drive(id=drive_path.name, name=drive_path.name, url=str(drive_path))


def project_from_legacy(
    db: Session, a_prj_path: Path, serial_number: Optional[str] = None
) -> Project:
    project_name = a_prj_path.name
    # Extract serial number from project name if not provided
    if serial_number is None:
        serial_number = extract_serial_number(project_name)

    # Deduce the drive model from the project path
    drive_path = a_prj_path.parent
    drive_model = drive_from_legacy(drive_path)

    zoo_project = ZooscanDrive(Path(drive_model.url)).get_project_folder(project_name)
    # Get the creation time of the directory
    creation_time = datetime.fromtimestamp(os.path.getmtime(a_prj_path))

    # Find the most recent modification time of any file in the project directory
    latest_mtime = find_latest_modification_time(a_prj_path)

    instrument_model = get_instrument_by_id(serial_number)
    if instrument_model is None:
        instrument_model = Instrument(id=serial_number, name=serial_number, sn="xxxx")

    sample_models = samples_from_legacy_project(db, zoo_project)
    project_hash = hash_from_project(a_prj_path)

    project = Project(
        path=str(a_prj_path),
        id=project_hash,
        name=project_name,
        instrumentSerialNumber=serial_number,
        instrumentId=serial_number,
        instrument=instrument_model,
        drive=drive_model,
        samples=sample_models,
        createdAt=creation_time,
        updatedAt=latest_mtime,
    )
    return project


def samples_from_legacy_project(
    db: Session,
    zoo_project: ZooscanProjectFolder,
) -> list[Sample]:
    ret = []
    for sample_name in zoo_project.list_samples_with_state():
        # TODO maybe: Filter out samples which do not have a directory,
        #  it's possible to copy/paste a samples CSV without the corresponding directory
        sample_to_add = sample_from_legacy(db, zoo_project, sample_name)
        ret.append(sample_to_add)
    return ret


def subsamples_from_legacy_project_and_sample(
    db: Session,
    zoo_project: ZooscanProjectFolder,
    sample_name: str,
) -> List[SubSample]:
    ret = []
    project_scans_metadata = get_project_scans_metadata(db, zoo_project)
    sample_scans_metadata = sub_scans_metadata_table_for_sample(
        project_scans_metadata, sample_name
    )
    for scan_name in get_project_scans(db, zoo_project):
        subsample_name = subsample_name_from_scan_name(scan_name)
        zoo_subsample_metadata = find_scan_metadata(
            sample_scans_metadata, sample_name, scan_name
        )  # No concept of "subsample" in legacy"
        if zoo_subsample_metadata is None:
            # Not an error or warning, we don't have the relationship samples->subsample beforehand
            continue
        subsample_to_add = subsample_from_legacy(
            db, zoo_project, sample_name, subsample_name, zoo_subsample_metadata
        )
        ret.append(subsample_to_add)
    return ret


def to_api_meta(metadata_dict: Dict) -> List[MetadataModel]:
    ret = []
    for key, value in metadata_dict.items():
        ret.append(
            MetadataModel(
                name=key,
                value=str(value),
                type="string",  # TODO
            )
        )
    return ret


def fraction_name_from_subsample(sample_name: str, a_subsample: SubSample):
    subsample_suffix = a_subsample.name.replace(sample_name, "")
    try:
        fraction_id = subsample_suffix.split("_")[1]
    except IndexError:
        fraction_id = f"?{subsample_suffix}?"
    return fraction_id


def sample_from_legacy(
    db: Session,
    zoo_project: ZooscanProjectFolder,
    sample_name: str,
) -> Sample:
    # Read metadata
    all_sample_metadata = read_samples_metadata_table(zoo_project)
    zoo_metadata = find_sample_metadata(all_sample_metadata, sample_name)
    assert (
        zoo_metadata is not None
    ), f"Sample {sample_name} metadata not found in {zoo_project.zooscan_meta.samples_table_path}"
    modern_metadata = sample_from_legacy_meta(zoo_metadata)
    metadata = to_api_meta(modern_metadata)
    subsample_models = subsamples_from_legacy_project_and_sample(
        db, zoo_project, sample_name
    )
    # Create the sample with metadata and precomputed aggregates
    nb_scans = sum(len(a_subsample.scan) for a_subsample in subsample_models)
    fractions = set(
        [
            fraction_name_from_subsample(sample_name, a_subsample)
            for a_subsample in subsample_models
        ]
    )
    fractions_str = ", ".join(fractions)
    created_at = parse_legacy_date(modern_metadata["sampling_date"], "-")
    ret = Sample(
        id=hash_from_sample_name(sample_name),
        name=sample_name,
        metadata=metadata,
        subsample=subsample_models,
        nbScans=nb_scans,
        nbFractions=fractions_str,
        createdAt=created_at,
    )
    return ret


def subsample_from_legacy(
    db: Session,
    zoo_project: ZooscanProjectFolder,
    sample_name: str,
    subsample_name: str,
    zoo_scan_metadata: ScanCSVLine,
) -> SubSample:
    modern_metadata = scan_from_legacy_meta(zoo_scan_metadata)
    metadata = to_api_meta(modern_metadata)
    # Extract scans from the legacy project folder
    scans = scans_from_legacy(zoo_project, sample_name, subsample_name)
    # Client-side also expects _the_ chosen background to be returned as an extra "scan" with OK type
    bg_id = get_background_id(
        db,
        drive_from_project_path(zoo_project.path),
        zoo_project.project,
        scan_name_from_subsample_name(subsample_name),
    )
    if bg_id is not None:
        scans.append(background_from_legacy_as_scan(zoo_project, bg_id))
    # Create the sample with metadata and scans
    created_at = updated_at = datetime.now()
    user = user_with_name(modern_metadata["operator"])
    ret = SubSample(
        id=hash_from_subsample_name(subsample_name),
        name=subsample_name,
        metadata=metadata,
        scan=scans,
        createdAt=created_at,
        updatedAt=updated_at,
        user=user,
    )
    return ret


def scans_from_legacy(
    zoo_project: ZooscanProjectFolder, sample_name: str, subsample_name: str
) -> List[Scan]:
    # What is presented as a "scan" is in fact several files, but the lib knows
    scan_name = scan_name_from_subsample_name(subsample_name)
    if scan_name not in zoo_project.list_scans_with_state():
        return []

    # So far there is a _maximum_ of 1 scan per subsample
    project_hash = hash_from_project(zoo_project.path)
    sample_hash = hash_from_sample_name(sample_name)
    subsample_hash = hash_from_subsample_name(subsample_name)
    the_scan = Scan(
        id=scan_name_from_subsample_name(subsample_name),
        url=get_scan_url(project_hash, sample_hash, subsample_hash),
        metadata=[],
        type=ScanTypeNum.SCAN,
        user=get_mock_user(),
    )
    return [the_scan]


def background_from_legacy_as_scan(
    zoo_project: ZooscanProjectFolder,
    background_date: str,
) -> Scan:
    # So far there is a _maximum_ of 1 scan per subsample
    project_hash = hash_from_project(zoo_project.path)
    the_scan = Scan(
        id=background_date,
        url=get_background_url(project_hash, background_date),
        metadata=[],
        type=ScanTypeNum.MEDIUM_BACKGROUND,
        user=get_mock_user(),
    )
    return the_scan


def backgrounds_from_legacy_project(
    zoo_project: ZooscanProjectFolder,
) -> list[Background]:
    """
    Extract background information from a ZooscanProjectFolder and return a list of Background objects.

    Args:
        zoo_project (ZooscanProjectFolder): The project folder to extract backgrounds from.

    Returns:
        list[Background]: A list of Background objects representing the backgrounds in the project.
    """
    backgrounds = []

    # Get the background folder from the project
    back_folder = zoo_project.zooscan_back

    # Get a mock user for the backgrounds
    mock_user = get_mock_user()

    # Always call extract_serial_number to ensure it's called as expected by tests
    serial_number = extract_serial_number(zoo_project.project)

    # Try to find an instrument with matching serial number from the hardcoded list
    instrument = None
    for instr in INSTRUMENTS:
        if instr["sn"] == serial_number:
            instrument = Instrument(**instr)
            break

    # If no matching instrument found, use the first one from the list but set its serial number to match
    if instrument is None:
        instrument_data = INSTRUMENTS[0].copy()
        instrument_data["sn"] = serial_number
        instrument = Instrument(**instrument_data)

    # Use the project path to generate the hash
    project_hash = hash_from_project(zoo_project.path)

    # For each date, create a Background object. Dates are in ZooProcess format
    dates = back_folder.get_dates()
    for a_date in dates:
        # Get the background entry for this date
        entry = back_folder.content[a_date]

        if not entry["final_background"]:
            continue

        # If there's a final background, add it to the list
        background_id = f"{a_date}"
        background_name = f"{a_date}_background"
        background_url = get_background_url(project_hash, a_date)

        # Convert the date string to a datetime object for the model
        api_date = parse_legacy_date(a_date)

        # Create the Background object
        background = Background(
            id=background_id,
            url=background_url,
            name=background_name,
            user=mock_user,
            instrument=instrument,
            createdAt=api_date,
            type="MEDIUM_BACKGROUND",
        )

        backgrounds.append(background)

    return backgrounds


def parse_legacy_date(a_date: str, separator: str = "_") -> datetime:
    """
    Parse a date string in the format "%Y%m%d*%H%M" into a datetime object.

    If the date string is invalid, logs a warning and returns the epoch date (January 1, 1970).

    Args:
        a_date (str): The date string to parse
        separator (str): The separator b/w day and time components

    Returns:
        datetime: The parsed datetime object, or epoch date if parsing fails
    """
    try:
        return datetime.strptime(a_date, f"%Y%m%d{separator}%H%M")
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid date {a_date}. Using epoch date instead. Error: {e}")
        return datetime(1970, 1, 1)  # Return epoch date


def scans_from_legacy_project(
    db: Session, zoo_project: ZooscanProjectFolder
) -> list[Scan]:
    """
    Extract scan information from a ZooscanProjectFolder and return a list of Scan objects.
    Uses scans_from_legacy in a loop over samples and subsamples.

    Args:
        zoo_project (ZooscanProjectFolder): The project folder to extract scans from.
        db (sqlalchemy.orm.Session, optional): The SQLAlchemy session to use.

    Returns:
        list[Scan]: A list of Scan objects representing the scans in the project.
    """
    ret = []

    # Get scan metadata for the project
    project_scans_metadata = get_project_scans_metadata(db, zoo_project)
    # Iterate over all samples in the project
    for sample_name in zoo_project.list_samples_with_state():
        sample_scans_metadata = sub_scans_metadata_table_for_sample(
            project_scans_metadata, sample_name
        )
        # Iterate over all scans in the project
        for scan_name in get_project_scans(db, zoo_project):
            subsample_name = subsample_name_from_scan_name(scan_name)
            zoo_subsample_metadata = find_scan_metadata(
                sample_scans_metadata, sample_name, scan_name
            )

            # Skip if no metadata found for this scan in this sample
            if zoo_subsample_metadata is None:
                continue

            # Get scans for this subsample and add them to the result list
            subsample_scans = scans_from_legacy(
                zoo_project, sample_name, subsample_name
            )
            ret.extend(subsample_scans)

    return ret


def _process_legacy_meta(
    meta: Union[ScanCSVLine, SampleCSVLine], legacy_to_modern: dict
) -> dict:
    """
    Helper function to process legacy metadata using a mapping dictionary.

    This function transforms a dictionary containing metadata with legacy keys into a new dictionary
    with standardized modern keys. It also performs special transformations on latitude and longitude
    values to correct their format.

    Parameters:
        meta (dict): A dictionary containing metadata with legacy keys
        legacy_to_modern (dict): A dictionary mapping legacy keys to modern keys

    Returns:
        dict: A new dictionary with transformed keys and values according to the conversion mapping
              Keys not found in the conversion mapping are kept unchanged
    """
    # Invert the conversion table to map from modern keys to legacy keys
    modern_to_legacy: Dict[str, Tuple[str, Any]] = {}
    for legacy_key, modern_key in legacy_to_modern.items():
        if modern_key is None:
            continue
        if isinstance(modern_key, list):
            # Handle the case where a legacy key maps to multiple modern keys
            for mk in modern_key:
                modern_to_legacy[mk] = (legacy_key, modern_key.index(mk))
        else:
            modern_to_legacy[modern_key] = (legacy_key, None)

    ret = {}

    for key, value in meta.items():
        modern_key = legacy_to_modern.get(key)
        if modern_key is None:
            continue
        if isinstance(modern_key, list):
            # Handle the case where a legacy key maps to multiple modern keys
            # For now, we'll just use the first mapping and handle special cases below
            modern_key = modern_key[0]

        # Apply special transformations based on the legacy key
        # noinspection PyUnreachableCode
        match key:
            case "longitude" | "longitude_end":
                new_value = -convert_ddm_to_decimal_degrees(value)
            case "latitude" | "latitude_end":
                new_value = convert_ddm_to_decimal_degrees(value)
            case "fracid":
                parsed = parse_fracid(str(value))
                ret["fraction_id"] = parsed.primary_fraction
                if parsed.pattern_type == "complex":
                    assert parsed.sub_fraction
                    ret["fraction_id_suffix"] = parsed.sub_fraction
                else:
                    ret["fraction_id_suffix"] = ""
                continue  # Skip the normal assignment since we've handled it specially
            case _:
                new_value = value

        ret[modern_key] = new_value

    return ret


def sample_from_legacy_meta(meta: SampleCSVLine) -> dict:
    """
    Convert legacy sample metadata dictionary, from CSV data source, to modern format.

    This function transforms a dictionary containing sample metadata with legacy keys into a new dictionary
    with standardized modern keys. It also performs special transformations on latitude and longitude
    values to correct their format.

    Parameters:
        meta (SampleCSVLine): A dictionary containing sample metadata with legacy keys

    Returns:
        dict: A new dictionary with transformed keys and values according to the conversion mapping
              Keys not found in the conversion mapping are kept unchanged

    Note:
        Latitude and longitude values undergo special transformations to convert from
        degrees-minutes format to decimal degrees format
    """
    legacy_to_modern = {
        # Common to both CSVs
        "sampleid": "sample_id",  # 'apero2023_tha_bioness_sup2000_017_st66_d_n1',
        # In sample CSV
        "ship": "ship_name",  # 'thalassa',
        "scientificprog": "scientific_program",  # 'apero',
        "stationid": "station_id",  # '66',
        "date": "sampling_date",  # '20230704-0503',
        "latitude": "latitude_start",  # '51.5293',
        "longitude": "longitude_start",  # '19.2159',
        "depth": "bottom_depth",  # '99999',
        "ctdref": "ctd_reference",  # 'apero_bio_ctd_017',
        "otherref": "other_reference",  # 'apero_bio_uvp6_017u',
        "townb": "number_of_tow",  # '1',
        "towtype": "tow_type",  # '1',
        "nettype": "net_sampling_type",  # 'bioness',
        "netmesh": "net_mesh",  # '2000',
        "netsurf": "net_opening_surface",  # '1',
        "zmax": "maximum_depth",  # '1008',
        "zmin": "minimum_depth",  # '820',
        # 'Vol': '357',
        "sample_comment": "sample_comment",
        # input_volume_including_on_board_fractioning__total_volume_is_714_mcube__counterpart_in_existing_project_bioness',
        # 'vol_qc': '1',
        "depth_qc": "quality_flag_for_depth_measurement",  # '1',
        # 'sample_qc': '1111',
        "barcode": "barcode",  # 'ape000000147',
        "latitude_end": "latitude_end",  # '51.5214',
        "longitude_end": "longitude_end",  # '19.2674',
        "net_duration": "sampling_duration",  # '20',
        "ship_speed_knots": "ship_speed",  # '2',
        "cable_length": "cable_length",  # '9999',
        "cable_angle": "cable_angle_from_vertical",  # '99999',
        "cable_speed": "cable_speed",  # '0',
        "nb_jar": "number_of_jars",  # '1'
        # jar_airtighness
        # sample_richness
        # sample_conditioning
        # sample_content
        #
        # quality_flag_filtered_volume
    }

    return _process_legacy_meta(meta, legacy_to_modern)


def scan_from_legacy_meta(meta: ScanCSVLine) -> dict:
    """
    Convert legacy scan metadata dictionary, from CSV data source, to modern format.

    This function transforms a dictionary containing scan metadata with legacy keys into a new dictionary
    with standardized modern keys.

    Parameters:
        meta (ScanCSVLine): A dictionary containing scan metadata with legacy keys

    Returns:
        dict: A new dictionary with transformed keys and values according to the conversion mapping
              Keys not found in the conversion mapping are kept unchanged
    """
    legacy_to_modern = {
        "sampleid": "sample_id",  # 'apero2023_tha_bioness_sup2000_017_st66_d_n1',
        # In scan CSV
        "scanid": None,
        "scanop": "operator",  # 'adelaide_perruchon',
        "fracid": [
            "fraction_id",
            "fraction_id_suffix",
        ],  # 'd1_1_sur_1' -> 'd1' and '1_sur_1'
        "fracmin": "fraction_min_mesh",  # '10000',
        "fracsup": "fraction_max_mesh",  # '999999',
        "fracnb": "spliting_ratio",  # '1',
        "observation": "observation",  # 'no',
        "code": "code",  # '1',
        "submethod": "submethod",  # 'motoda',
        "cellpart": "cellpart",  # '1',
        "replicates": "replicates",  # '1',
        "volini": "volini",  # '1',
        "volprec": "volprec",  # '1',
    }

    return _process_legacy_meta(meta, legacy_to_modern)
