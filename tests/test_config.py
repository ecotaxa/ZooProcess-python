import os
import tempfile


def test_working_dir_default():
    """Test that WORKING_DIR is set to the current directory by default"""
    # Import the config module
    from config_rdr import config

    # Check that WORKING_DIR is also available in the config module
    assert config.WORKING_DIR == os.getcwd()


def test_working_dir_from_env():
    """Test that WORKING_DIR is set from the environment variable if provided"""
    # Save the original environment variable
    original_working_dir = os.environ.get("WORKING_DIR")

    try:
        # Set a test directory
        test_dir = tempfile.mkdtemp()
        os.environ["WORKING_DIR"] = test_dir

        # Reload the config module to pick up the new environment variable
        import importlib
        import config_rdr

        importlib.reload(config_rdr)

        # Import the config module again
        from config_rdr import config

        # Check that WORKING_DIR is also available in the config module
        assert config.WORKING_DIR == test_dir
    finally:
        # Restore the original environment variable
        if original_working_dir is not None:
            os.environ["WORKING_DIR"] = original_working_dir
        else:
            os.environ.pop("WORKING_DIR", None)

        # Clean up the test directory
        os.rmdir(test_dir)

        # Reload the config module to restore the original state
        import importlib
        import config_rdr

        importlib.reload(config_rdr)
