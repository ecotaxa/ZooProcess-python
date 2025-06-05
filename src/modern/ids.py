from base64 import urlsafe_b64encode, urlsafe_b64decode
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException

from helpers.cached_ids import CachedIds
from legacy.drives import get_drive_path

DO_HASH = False


def name_from_hash(encoded_str: str) -> str:
    """
    Safely decode a base64 encoded string and convert it to a UTF-8 string.
    Never throws an exception but returns the original string instead.

    Args:
        encoded_str: The base64 encoded string

    Returns:
        str: The decoded string or the original string if decoding fails
    """
    if not DO_HASH:
        return encoded_str
    # noinspection PyBroadException
    try:
        decoded_bytes = urlsafe_b64decode(encoded_str)
        return decoded_bytes.decode()
    except Exception:
        # Return the original string instead of an empty string
        return ""


def hash_from_name(name: str) -> str:
    if not DO_HASH:
        return name
    return urlsafe_b64encode(name.encode()).decode()


def hash_from_project(a_prj_path: Path) -> str:
    """
    Compute some user and browser compatible IDs for URLs
    Assumes that the drive's name is _always_ the project parent directory name
    """
    drive_name = drive_from_project_path(a_prj_path)
    url_hash = f"{drive_name}|{a_prj_path.name}"
    return hash_from_name(url_hash)


def drive_from_project_path(a_prj_path: Path) -> str:
    return a_prj_path.parent.name


def drive_and_project_from_hash(project_hash: str) -> Tuple[Path, str]:
    """
    Extract drive and project names from a project hash generated above.
    """
    project_hash = name_from_hash(project_hash)
    try:
        drive_name, project_name = project_hash.split("|")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project ID format: {project_hash}. Expected format: drive|project",
        )

    drive_path = get_drive_path(drive_name)
    if drive_path is None:
        raise HTTPException(
            status_code=404, detail=f"Project with ID {project_hash} not found"
        )
    project_path = Path(drive_path) / project_name
    if not (project_path.exists() and project_path.is_dir()):
        raise HTTPException(
            status_code=404, detail=f"Project with ID {project_hash} not found"
        )
    return drive_path, project_name


THE_SCAN_PER_SUBSAMPLE = 1


def subsample_name_from_scan_name(scan_name: str) -> str:
    """
    Extract subsample name from scan name by removing trailing "_1" if present.

    Args:
        scan_name (str): The scan name

    Returns:
        str: The subsample name
    """
    if scan_name.endswith(f"_{THE_SCAN_PER_SUBSAMPLE}"):
        return scan_name[:-2]
    return scan_name


def scan_name_from_subsample_name(subsample_name: str) -> str:
    """
    Create scan name from subsample name by adding trailing "_1".
    This is the reverse function of subsample_name_from_scan_name.

    Args:
        subsample_name (str): The subsample name

    Returns:
        str: The scan name
    """
    return f"{subsample_name}_{THE_SCAN_PER_SUBSAMPLE}"


def hash_from_sample_name(sample_name: str) -> str:
    return hash_from_name(sample_name)


def sample_name_from_sample_hash(sample_hash: str) -> str:
    return name_from_hash(sample_hash)


def hash_from_user_name(user_name):
    return name_from_hash(user_name)


subsamples_cache = CachedIds("subsamples")


def hash_from_subsample_name(subsample_name: str) -> str:
    return subsamples_cache.id_from_name(subsample_name)


def subsample_name_from_hash(subsample_hash: str) -> str:
    return subsamples_cache.name_from_id(subsample_hash)
