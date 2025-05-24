import re
from pathlib import Path

import pytest

from config_rdr import config


def test_crash_endpoint(server_client):
    """
    Test that the /crash endpoint raises a 500 error and logs the stack trace.

    This test:
    1. Makes a request to the /crash endpoint using a real server in a subprocess
    2. Verifies that it returns a 500 error
    3. Checks that the call stack is correctly logged in the log file
    """
    # Get the path to the log file from the config
    log_file_path = Path(config.WORKING_DIR) / "logs" / "zooprocess.log"

    # Get the current size of the log file to read only new content
    initial_size = log_file_path.stat().st_size if log_file_path.exists() else 0
    print(log_file_path, initial_size)

    # Make request to the crash endpoint
    response = server_client.get("/crash")

    # Check that the response is a 500 error
    assert response.status_code == 500

    # Check that the response contains the error message
    assert "This is a deliberate crash for testing error handling" in response.text

    # Check that the response contains a stack trace
    assert "BACK-END" in response.text

    # Check that the log file contains the error message and stack trace
    if log_file_path.exists():
        with open(log_file_path, "r") as f:
            # Skip to the position where we were before the test
            f.seek(initial_size)
            log_content = f.read()
            print("LOG:", log_content, "END")

            # Check that the log contains the info message before the crash
            assert "Crash endpoint called - about to raise an exception" in log_content

            # Check that the log contains the error message
            assert (
                "This is a deliberate crash for testing error handling" in log_content
            )

            # Check that the log contains a stack trace (look for typical stack trace patterns)
            assert re.search(
                r"Traceback \(most recent call last\):", log_content
            ) or re.search(r"File \".*\", line \d+, in", log_content)
    else:
        pytest.fail(f"Log file not found at {log_file_path}")
