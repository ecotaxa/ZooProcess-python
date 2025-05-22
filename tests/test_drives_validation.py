import os
import sys
import tempfile
import shutil

import legacy.drives

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Function to simulate the validation logic in config_rdr.py
def validate_drives_helper(drives):
    """
    Validate that drives is not empty, all paths exist, all paths are directories, and all paths are unique.
    Returns a tuple (is_valid, error_message)
    """
    if not drives:
        return (
            False,
            "ERROR: DRIVES environment variable is empty or not set. Application startup failed.",
        )

    invalid_drives = []
    not_directories = []
    for drive in drives:
        if drive and not os.path.exists(drive):
            invalid_drives.append(drive)
        elif drive and not os.path.isdir(drive):
            not_directories.append(drive)

    if invalid_drives:
        return (
            False,
            f"ERROR: The following drives do not exist or are not accessible: {', '.join(invalid_drives)}",
        )

    if not_directories:
        return (
            False,
            f"ERROR: The following drives are not directories: {', '.join(not_directories)}",
        )

    # Check for duplicate drives
    unique_drives = set()
    duplicate_drives = []
    for drive in drives:
        if drive in unique_drives:
            duplicate_drives.append(drive)
        else:
            unique_drives.add(drive)

    if duplicate_drives:
        return (
            False,
            f"ERROR: The following drives are duplicated: {', '.join(duplicate_drives)}",
        )

    return True, None


def test_validate_drives_empty():
    """Test that validation fails when drives is empty."""
    is_valid, error_message = validate_drives_helper([])
    assert not is_valid
    assert (
        error_message
        == "ERROR: DRIVES environment variable is empty or not set. Application startup failed."
    )


def test_validate_drives_invalid_paths():
    """Test that validation fails when drives contains invalid paths."""
    is_valid, error_message = validate_drives_helper(
        ["/nonexistent/path1", "/nonexistent/path2"]
    )
    assert not is_valid
    assert (
        error_message
        == "ERROR: The following drives do not exist or are not accessible: /nonexistent/path1, /nonexistent/path2"
    )


def test_validate_drives_valid_paths():
    """Test that validation passes when drives contains valid paths."""
    # Create temporary directories for testing
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    try:
        is_valid, error_message = validate_drives_helper([temp_dir1, temp_dir2])
        assert is_valid
        assert error_message is None
    finally:
        # Clean up the temporary directories
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)


def test_validate_drives_not_directories():
    """Test that validation fails when drives contains paths that are not directories."""
    # Create a temporary directory and a temporary file
    temp_dir = tempfile.mkdtemp()
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()

    try:
        is_valid, error_message = validate_drives_helper([temp_dir, temp_file.name])
        assert not is_valid
        assert (
            error_message
            == f"ERROR: The following drives are not directories: {temp_file.name}"
        )
    finally:
        # Clean up the temporary directory and file
        shutil.rmtree(temp_dir)
        os.unlink(temp_file.name)


def test_validate_drives_duplicates():
    """Test that validation fails when drives contains duplicate paths."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        is_valid, error_message = validate_drives_helper([temp_dir, temp_dir])
        assert not is_valid
        assert (
            error_message == f"ERROR: The following drives are duplicated: {temp_dir}"
        )
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)


def test_config_validation_empty(mocker):
    """Test that validation fails when DRIVES is empty."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    try:
        # Unset the DRIVES environment variable
        if "DRIVES" in os.environ:
            del os.environ["DRIVES"]

        # Import the config module first to set up config.DRIVES
        import config_rdr
        from config_rdr import config
        import importlib

        importlib.reload(config_rdr)

        # Mock sys.exit to prevent the test from actually exiting
        mock_exit = mocker.patch("legacy.drives.sys.exit")
        mock_print = mocker.patch("builtins.print")

        # Call validate_drives() which should exit with code 1
        legacy.drives.validate_drives()

        # Check that sys.exit was called with exit code 1
        mock_exit.assert_called_once_with(1)
    finally:
        # Restore the original DRIVES value
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]


def test_config_validation_invalid_paths(mocker):
    """Test that validation fails when DRIVES contains invalid paths."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    try:
        # Set the DRIVES environment variable with non-existent paths
        os.environ["DRIVES"] = "/nonexistent/path1,/nonexistent/path2"

        # Import the config module first to set up config.DRIVES
        import config_rdr
        from config_rdr import config
        import importlib

        importlib.reload(config_rdr)

        # Mock sys.exit to prevent the test from actually exiting
        mock_exit = mocker.patch("legacy.drives.sys.exit")
        mock_print = mocker.patch("builtins.print")

        # Call validate_drives() which should exit with code 1
        legacy.drives.validate_drives()

        # Check that sys.exit was called with exit code 1
        mock_exit.assert_called_once_with(1)
    finally:
        # Restore the original DRIVES value
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]


def test_config_validation_valid_paths():
    """Test that validation passes when DRIVES contains valid paths."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Create temporary directories for testing
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    try:
        # Set the DRIVES environment variable with the temporary directories
        os.environ["DRIVES"] = f"{temp_dir1},{temp_dir2}"

        # Import the config module first to set up config.DRIVES
        import config_rdr
        from config_rdr import config
        import importlib

        importlib.reload(config_rdr)
        from config_rdr import config

        # Check that DRIVES is correctly loaded
        assert config.DRIVES == [temp_dir1, temp_dir2]
    finally:
        # Restore the original DRIVES value
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]

        # Clean up the temporary directories
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)


def test_config_validation_not_directories(mocker):
    """Test that validation fails when DRIVES contains paths that are not directories."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Create a temporary directory and a temporary file
    temp_dir = tempfile.mkdtemp()
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()

    try:
        # Set the DRIVES environment variable with the temporary directory and file
        os.environ["DRIVES"] = f"{temp_dir},{temp_file.name}"

        # Import the config module first to set up config.DRIVES
        import config_rdr
        from config_rdr import config
        import importlib

        importlib.reload(config_rdr)

        # Mock sys.exit to prevent the test from actually exiting
        mock_exit = mocker.patch("legacy.drives.sys.exit")
        mock_print = mocker.patch("builtins.print")

        # Call validate_drives() which should exit with code 1
        legacy.drives.validate_drives()

        # Check that sys.exit was called with exit code 1
        mock_exit.assert_called_once_with(1)
    finally:
        # Restore the original DRIVES value
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]

        # Clean up the temporary directory and file
        shutil.rmtree(temp_dir)
        os.unlink(temp_file.name)


def test_config_validation_duplicates(mocker):
    """Test that validation fails when DRIVES contains duplicate paths."""
    # Save the original DRIVES value
    original_drives = os.environ.get("DRIVES")

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Set the DRIVES environment variable with duplicate paths
        os.environ["DRIVES"] = f"{temp_dir},{temp_dir}"

        # Import the config module first to set up config.DRIVES
        import config_rdr
        from config_rdr import config
        import importlib

        importlib.reload(config_rdr)

        # Mock sys.exit to prevent the test from actually exiting
        mock_exit = mocker.patch("legacy.drives.sys.exit")
        mock_print = mocker.patch("builtins.print")

        # Call validate_drives() which should exit with code 1
        legacy.drives.validate_drives()

        # Check that sys.exit was called with exit code 1
        mock_exit.assert_called_once_with(1)
    finally:
        # Restore the original DRIVES value
        if original_drives is not None:
            os.environ["DRIVES"] = original_drives
        else:
            if "DRIVES" in os.environ:
                del os.environ["DRIVES"]

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
