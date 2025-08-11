import sys
from pathlib import Path
from typing import Optional

from config_rdr import config


def get_drive_path(drive_name) -> Optional[Path]:
    """
    Returns the full path of a drive from its name (end of path).

    Args:
        drive_name (str): The name of the drive (last component of the path)

    Returns:
        Path: The full path of the drive if found, None otherwise
    """
    for drive in config.get_drives():
        if drive.name == drive_name:
            return drive

    return None


def validate_drives():
    """Validate DRIVES at application startup"""
    if not config.get_drives():
        print("ERROR: DRIVES environment variable is empty or not set.")
        print("Application startup failed.")
        sys.exit(1)

    # Check if all paths in DRIVES exist, are accessible, and are directories
    invalid_drives = []
    not_directories = []
    for drive in config.get_drives():
        if drive and not drive.exists():
            invalid_drives.append(drive)
        elif drive and not drive.is_dir():
            not_directories.append(drive)

    if invalid_drives:
        print(
            f"ERROR: The following drives do not exist or are not accessible: {', '.join(str(d) for d in invalid_drives)}"
        )
        sys.exit(1)

    if not_directories:
        print(
            f"ERROR: The following drives are not directories: {', '.join(str(d) for d in not_directories)}"
        )
        sys.exit(1)

    # Check for duplicate drives
    unique_drives = set()
    duplicate_drives = []
    for drive in config.get_drives():
        if drive in unique_drives:
            duplicate_drives.append(drive)
        else:
            unique_drives.add(drive)

    if duplicate_drives:
        print(
            f"ERROR: The following drives are duplicated: {', '.join(str(d) for d in duplicate_drives)}"
        )
        sys.exit(1)
