# A Datasource which mixes legacy scan CSV table with modern additions
# from typing import Dict, List
from typing import List, Dict

from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder


def get_project_scans_metadata(
    zoo_project: ZooscanProjectFolder,
) -> List[Dict[str, str]]:
    """
    Get the scans metadata for a project.

    This function calls read_scans_table() on a ZooscanProjectFolder to retrieve
    the scans metadata for the project.

    Args:
        zoo_project (ZooscanProjectFolder): The project folder to get scans metadata from.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the scans metadata.
    """
    return zoo_project.zooscan_meta.read_scans_table()
