# Conventional namings from Legacy app
from ZooProcess_lib.ZooscanFolder import MEASURE_ENDING, SEP_ENDING, MSK1_ENDING
from modern.ids import subsample_name_from_scan_name, THE_SCAN_PER_SUBSAMPLE


def raw_file_name(scan_name: str) -> str:
    subsample_name = subsample_name_from_scan_name(scan_name)
    return f"{subsample_name}_raw_{THE_SCAN_PER_SUBSAMPLE}.tif"


def measure_file_name(subsample_name: str) -> str:
    return f"{subsample_name}_{THE_SCAN_PER_SUBSAMPLE}{MEASURE_ENDING}"


def separator_file_name(subsample_name: str) -> str:
    return f"{subsample_name}_{THE_SCAN_PER_SUBSAMPLE}{SEP_ENDING}"


def mask_file_name(subsample_name: str) -> str:
    return f"{subsample_name}_{THE_SCAN_PER_SUBSAMPLE}{MSK1_ENDING}"
