import os
import sys
import builtins
import importlib

# Use builtins.print to make it easier to mock in tests
print = builtins.print


def validate_drives():
    """Validate DRIVES at application startup"""
    # Import the config module to ensure we have the latest values
    import src.config

    # Try to reload the module, but handle the case where it's not in sys.modules
    try:
        importlib.reload(src.config)
    except ImportError:
        # If the module is not in sys.modules, we can continue with the imported module
        pass

    from src.config import config

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
