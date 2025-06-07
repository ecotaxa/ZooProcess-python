# Conventional namings
from modern.ids import subsample_name_from_scan_name, THE_SCAN_PER_SUBSAMPLE


def raw_file_name(scan_name: str) -> str:
    subsample_name = subsample_name_from_scan_name(scan_name)
    return f"{subsample_name}_raw_{THE_SCAN_PER_SUBSAMPLE}.tif"
