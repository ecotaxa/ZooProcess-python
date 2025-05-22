import importlib
import os
import sys
from pathlib import Path
from typing import Optional


def get_drive_path(drive_name) -> Optional[Path]:
    """
    Returns the full path of a drive from its name (end of path).

    Args:
        drive_name (str): The name of the drive (last component of the path)

    Returns:
        Path: The full path of the drive if found, None otherwise
    """
    from config_rdr import config

    for drive_path in config.DRIVES:
        drive = Path(drive_path)
        if drive.name == drive_name:
            return Path(drive_path)

    return None


def validate_drives():
    """Validate DRIVES at application startup"""
    # Import the config module to ensure we have the latest values
    import config_rdr

    # Try to reload the module, but handle the case where it's not in sys.modules
    try:
        importlib.reload(config_rdr)
    except ImportError:
        # If the module is not in sys.modules, we can continue with the imported module
        pass

    from config_rdr import config

    if not config.DRIVES:
        print("ERROR: DRIVES environment variable is empty or not set.")
        print("Application startup failed.")
        sys.exit(1)

    # Check if all paths in DRIVES exist, are accessible, and are directories
    invalid_drives = []
    not_directories = []
    for drive in config.DRIVES:
        if drive and not os.path.exists(drive):
            invalid_drives.append(drive)
        elif drive and not os.path.isdir(drive):
            not_directories.append(drive)

    if invalid_drives:
        print(
            f"ERROR: The following drives do not exist or are not accessible: {', '.join(invalid_drives)}"
        )
        sys.exit(1)

    if not_directories:
        print(
            f"ERROR: The following drives are not directories: {', '.join(not_directories)}"
        )
        sys.exit(1)

    # Check for duplicate drives
    unique_drives = set()
    duplicate_drives = []
    for drive in config.DRIVES:
        if drive in unique_drives:
            duplicate_drives.append(drive)
        else:
            unique_drives.add(drive)

    if duplicate_drives:
        print(
            f"ERROR: The following drives are duplicated: {', '.join(duplicate_drives)}"
        )
        sys.exit(1)
