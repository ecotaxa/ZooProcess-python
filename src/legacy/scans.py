from typing import List, Dict, TypedDict, Optional, cast

from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder


class ScanCSVLine(TypedDict):
    """TypedDict representing the structure of a scan CSV record.
    It's a text line, so every field is a string"""

    scanid: str  # Per Project unique identifier for the scan
    sampleid: str  # Reference to the sample ID (e.g., 'apero2023_tha_bioness_sup2000_017_st66_d_n1')
    scanop: str  # Operator who performed the scan (e.g., 'adelaide_perruchon')
    fracid: str  # Fraction ID (e.g., 'd1_1_sur_1'), parsed into fraction_id and fraction_id_suffix
    fracmin: str  # Minimum mesh size for the fraction in microns (e.g., '10000')
    fracsup: str  # Maximum mesh size for the fraction in microns (e.g., '999999')
    fracnb: str  # Splitting ratio (e.g., '1')
    observation: str  # Observations (e.g., 'no')
    code: str  # Code (e.g., '1')
    submethod: str  # Submethod (e.g., 'motoda')
    cellpart: str  # Cell part (e.g., '1')
    replicates: str  # Number of replicates (e.g., '1')
    volini: str  # Initial volume (e.g., '1')
    volprec: str  # Precision volume (e.g., '1')


SCAN_CSV_COLUMNS = list(ScanCSVLine.__annotations__.keys())


def read_scans_metadata_table(zoo_project: ZooscanProjectFolder) -> List[ScanCSVLine]:
    ret = zoo_project.zooscan_meta.read_scans_table()
    if len(ret) > 0:
        assert list(ret[0].keys()) == SCAN_CSV_COLUMNS
    return cast(List[ScanCSVLine], ret)


def find_scan_metadata(
    scans_metadata: List[ScanCSVLine], sample_name: str, scan_name: str
) -> Optional[ScanCSVLine]:
    """
    Find and return scan metadata that matches the given sample name and scan name.

    Args:
        scans_metadata (List[Dict]): List of scan metadata dictionaries
        sample_name (str): The sample ID to match
        scan_name (str): The scan ID to match

    Returns:
        Dict or None: The matching scan metadata dictionary if found, None otherwise
    """
    for a_subsample_meta in scans_metadata:
        if (a_subsample_meta["sampleid"], a_subsample_meta["scanid"]) == (
            sample_name,
            scan_name,
        ):
            return a_subsample_meta
    return None


def sub_scans_metadata_table_for_sample(
    project_scans_metadata: List[ScanCSVLine], sample_name: str
) -> List[ScanCSVLine]:
    return list(filter(lambda x: x["sampleid"] == sample_name, project_scans_metadata))
