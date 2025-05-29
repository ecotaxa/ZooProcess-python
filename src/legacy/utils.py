from typing import List, Dict


def find_sample_metadata(all_sample_metadata: List[Dict], sample_name: str):
    for a_sample_meta in all_sample_metadata:
        if a_sample_meta["sampleid"] == sample_name:
            return a_sample_meta
    return None


def find_scan_metadata(scans_metadata: List[Dict], sample_name: str, scan_name: str):
    for a_subsample_meta in scans_metadata:
        if (a_subsample_meta["sampleid"], a_subsample_meta["scanid"]) == (
            sample_name,
            scan_name,
        ):
            return a_subsample_meta
    return None


def sub_table_for_sample(
    project_scans_metadata: List[Dict], sample_name: str
) -> List[Dict]:
    return list(filter(lambda x: x["sampleid"] == sample_name, project_scans_metadata))
