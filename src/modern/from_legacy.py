#
# Transformers from Legacy data to modern models
#
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from Models import (
    Project,
    Drive,
    Sample,
    Background,
    Instrument,
    ScanIn,
    Scan,
    MetadataModel,
    SubSample,
)
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder, ZooscanDrive
from config_rdr import config
from legacy.utils import find_sample_metadata, find_subsample_metadata
from modern.ids import hash_from_drive_and_project
from modern.instrument import get_instrument_by_id, INSTRUMENTS
from modern.users import get_mock_user
from modern.utils import (
    extract_serial_number,
    parse_sample_name,
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
    a_drive: str
    for a_drive in config.DRIVES:
        drv = Path(a_drive)
        name = drv.name
        ret.append(Drive(id=name, name=name, url=a_drive))
    return ret


def drive_from_legacy(drive_path: Path) -> Drive:
    """
    Retrieve a Drive object from the legacy configuration.
    """
    return Drive(id=drive_path.name, name=drive_path.name, url=str(drive_path))


def project_from_legacy(
    drive_model: Drive, a_prj_path: Path, serial_number: str = None
) -> Project:
    unq_id = hash_from_drive_and_project(drive_model, a_prj_path)
    project_name = a_prj_path.name
    # Extract serial number from project name if not provided
    if serial_number is None:
        serial_number = extract_serial_number(project_name)

    zoo_project = ZooscanDrive(Path(drive_model.url)).get_project_folder(project_name)
    # Get the creation time of the directory
    creation_time = datetime.fromtimestamp(os.path.getmtime(a_prj_path))

    # Find the most recent modification time of any file in the project directory
    latest_mtime = find_latest_modification_time(a_prj_path)

    instrument_model = get_instrument_by_id(serial_number)
    if instrument_model is None:
        instrument_model = Instrument(id=serial_number, name=serial_number, sn="xxxx")

    sample_models = samples_from_legacy_project(zoo_project)

    project = Project(
        path=str(a_prj_path),
        id=unq_id,
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
    zoo_project: ZooscanProjectFolder,
) -> list[Sample]:
    ret = []
    for sample_name in zoo_project.list_samples_with_state():
        sample_to_add = sample_from_legacy(zoo_project, sample_name)
        ret.append(sample_to_add)
    return ret


def subsamples_from_legacy_project_and_sample(
    zoo_project: ZooscanProjectFolder, sample_name: str
):
    ret = []
    scans_metadata = zoo_project.zooscan_meta.read_scans_table()
    for subsample_name in zoo_project.list_scans_with_state():
        sample_to_add = subsample_from_legacy(
            scans_metadata, sample_name, subsample_name
        )
        if sample_to_add is not None:
            ret.append(sample_to_add)
    return ret


def to_modern_meta(metadata_dict: Dict) -> List[MetadataModel]:
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


def sample_from_legacy(zoo_project: ZooscanProjectFolder, sample_name: str) -> Sample:
    # Parse the sample name into components
    parsed_name = parse_sample_name(sample_name)
    # Create metadata from parsed components
    all_sample_metadata = zoo_project.zooscan_meta.read_samples_table()
    zoo_metadata = find_sample_metadata(all_sample_metadata, sample_name)
    assert (
        zoo_metadata is not None
    ), f"Sample {sample_name} metadata not found in {zoo_project.zooscan_meta.samples_table_path}"
    metadata = to_modern_meta(from_legacy_meta(zoo_metadata))
    subsample_models = subsamples_from_legacy_project_and_sample(
        zoo_project, sample_name
    )
    # for key, value in parsed_name.items():
    #     if key not in ["full_name", "components", "num_components"]:
    #         metadata.append(
    #             {
    #                 "id": f"{sample_name}_{key}",
    #                 "name": key,
    #                 "value": str(value),
    #                 "description": f"Extracted from sample name: {key}",
    #             }
    #         )
    # Create the sample with metadata
    ret = Sample(
        id=sample_name, name=sample_name, metadata=metadata, subsample=subsample_models
    )
    return ret


def subsample_from_legacy(
    scans_metadata: List[Dict],
    sample_name: str,
    subsample_name: str,
) -> Optional[SubSample]:
    # Create metadata from parsed components
    zoo_metadata = find_subsample_metadata(scans_metadata, sample_name, subsample_name)
    if zoo_metadata is None:
        return None
    else:
        # assert (
        #     zoo_metadata is not None
        # ), f"SubSample {subsample_name} metadata not found in {zoo_project.zooscan_meta.scans_table_path}"
        metadata_dict = from_legacy_meta(zoo_metadata)
        metadata = to_modern_meta(metadata_dict)
    # Parse the subsample name into components
    parsed_name = parse_sample_name(subsample_name)
    scans = [
        Scan(
            id=subsample_name,
            url="toto",
            metadata=[],
            type="MEDIUM",
            user=get_mock_user(),
        )
    ]
    # Create the sample with metadata and scans
    ret = SubSample(
        id=subsample_name, name=subsample_name, metadata=metadata, scan=scans
    )
    return ret


def backgrounds_from_legacy_project(
    drive_model: Drive, project: ZooscanProjectFolder
) -> list[Background]:
    """
    Extract background information from a ZooscanProjectFolder and return a list of Background objects.

    Args:
        project (ZooscanProjectFolder): The project folder to extract backgrounds from.
        drive_model (Drive): The drive model containing the project. If None, the drive from the project will be used.

    Returns:
        list[Background]: A list of Background objects representing the backgrounds in the project.
    """
    backgrounds = []

    # Get the background folder from the project
    back_folder = project.zooscan_back

    # Get all dates for which backgrounds exist
    dates = back_folder.get_dates()

    # Get a mock user for the backgrounds
    # In a real implementation, this would be fetched from a database
    mock_user = get_mock_user()

    # Always call extract_serial_number to ensure it's called as expected by tests
    serial_number = extract_serial_number(project.project)

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

    # Use the provided drive if available, otherwise use the project's drive
    project_hash = hash_from_drive_and_project(drive_model, project.path)

    # For each date, create a Background object. Dates are in ZooProcess format
    for a_date in dates:
        # Get the background entry for this date
        entry = back_folder.content[a_date]

        # If there's a final background, add it to the list
        if entry["final_background"]:
            background_id = f"{a_date}"
            background_name = f"{a_date}_background"
            background_url = (
                config.public_url + f"/projects/{project_hash}/background/{a_date}.jpg"
            )

            # Convert the date string to a datetime object for the model
            api_date = datetime.strptime(a_date, "%Y%m%d_%H%M")

            # Create the Background object
            background = Background(
                id=background_id,
                url=background_url,
                name=background_name,
                user=mock_user,
                instrument=instrument,
                createdAt=api_date,
            )

            backgrounds.append(background)

    return backgrounds


def scans_from_legacy_project(project: ZooscanProjectFolder) -> list[Scan]:
    """
    Extract scan information from a ZooscanProjectFolder and return a list of Scan objects.

    Args:
        project (ZooscanProjectFolder): The project folder to extract scans from.

    Returns:
        list[ScanIn]: A list of Scan objects representing the scans in the project.
    """
    scans = []

    # Get a mock user for the scans
    # In a real implementation, this would be fetched from a database
    mock_user = get_mock_user()

    # Iterate over all samples in the project
    for scan_name in project.list_scans_with_state():
        scans.append(
            Scan(id=scan_name, url="toto", type="MEDIUM", metadata=[], user=mock_user)
        )

    return scans


def from_legacy_meta(meta: dict) -> dict:
    """
    Convert legacy metadata dictionary to modern format.

    This function transforms a dictionary containing metadata with legacy keys into a new dictionary
    with standardized modern keys. It also performs special transformations on latitude and longitude
    values to correct their format.

    Parameters:
        meta (dict): A dictionary containing metadata with legacy keys

    Returns:
        dict: A new dictionary with transformed keys and values according to the conversion mapping
              Keys not found in the conversion mapping are kept unchanged

    Note:
        Latitude and longitude values undergo special transformations to convert from
        degrees-minutes format to decimal degrees format
    """
    # sample CSV structure
    #   sampleid;ship;scientificprog;stationid;date;latitude;longitude;depth;ctdref;otherref;townb;towtype;nettype;netmesh;
    #   netsurf;zmax;zmin;vol;sample_comment;vol_qc;depth_qc;sample_qc;barcode;latitude_end;longitude_end;net_duration;
    #   ship_speed_knots;cable_length;cable_angle;cable_speed;nb_jar
    # scan CSV structure
    #   scanid;sampleid;scanop;fracid;fracmin;fracsup;fracnb;observation;code;submethod;cellpart;
    #   replicates;volini;volprec
    conversion_table = {
        # Common to both CSVs
        "sampleid": "sample_id",  # 'apero2023_tha_bioness_sup2000_017_st66_d_n1',
        # In sample CSV
        "ship": "ship_name",  # 'thalassa',
        "scientificprog": "scientific_program",  # 'apero',
        "stationid": "station_id",  # '66',
        # 'date': 'sampling_date' , # '20230704-0503',
        "createdAt": "sampling_date",  # '20230704-0503',
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
        # fraction_id_suffix
        # spliting_ratio
        # quality_flag_filtered_volume
        #
        # In scan CSV
        "scanop": "scanning_operator",  # 'adelaide_perruchon',
        # 'FracId': 'd1_1_sur_1',
        "fracmin": "fraction_min_mesh",  # '10000',
        "fracsup": "fraction_max_mesh",  # '999999',
        "fracnb": "fraction_number",  # '1',
        "observation": "observation",  # 'no',
        # 'SubMethod': 'motoda',
        # 'Code': '1',
        # 'CellPart': '1',
        # 'Replicates': '1',
        # 'VolIni': '1',
        # 'VolPrec': '1',
    }

    ret = {}

    for key, value in meta.items():
        if key in conversion_table:
            new_key = conversion_table[key]
            # noinspection PyUnreachableCode
            match key:
                case "longitude" | "longitude_end":
                    new_value = -convert_ddm_to_decimal_degrees(value)
                case "latitude" | "latitude_end":
                    new_value = convert_ddm_to_decimal_degrees(value)
                case _:
                    new_value = value
            ret[new_key] = new_value
        else:
            ret[key] = value  # Keep the key unchanged
    return ret
