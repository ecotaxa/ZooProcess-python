import os
import sys
import subprocess
import tempfile
import shutil

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Test script to verify that main.py validation works correctly
def test_empty_drives():
    """Test that importing main.py fails when DRIVES is empty."""
    # Create a temporary script that imports config.py and then main.py
    script = f"""
import os
import sys
# Add the project root directory to the Python path
sys.path.append("{PROJECT_ROOT}")
# Unset DRIVES environment variable
if "DRIVES" in os.environ:
    del os.environ["DRIVES"]
# Import config.py first to set up config.DRIVES
from src.config import config
# Import main.py, which should fail
try:
    import main
    print("ERROR: Import succeeded when it should have failed")
    sys.exit(1)
except SystemExit:
    print("SUCCESS: Import failed as expected")
    sys.exit(0)
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(script.encode())
        script_path = f.name

    try:
        # Run the script and check the exit code
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True
        )
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        print(f"Error: {result.stderr}")
        assert (
            result.returncode == 0
        ), f"Script failed with exit code {result.returncode}"
        assert "SUCCESS: Import failed as expected" in result.stdout
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


def test_invalid_drives():
    """Test that importing main.py fails when DRIVES contains invalid paths."""
    # Create a temporary script that imports config.py and then main.py
    script = f"""
import os
import sys
# Add the project root directory to the Python path
sys.path.append("{PROJECT_ROOT}")
# Set DRIVES environment variable with invalid paths
os.environ["DRIVES"] = "/nonexistent/path1,/nonexistent/path2"
# Import config.py first to set up config.DRIVES
from src.config import config
# Import main.py, which should fail
try:
    import main
    print("ERROR: Import succeeded when it should have failed")
    sys.exit(1)
except SystemExit:
    print("SUCCESS: Import failed as expected")
    sys.exit(0)
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(script.encode())
        script_path = f.name

    try:
        # Run the script and check the exit code
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True
        )
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        print(f"Error: {result.stderr}")
        assert (
            result.returncode == 0
        ), f"Script failed with exit code {result.returncode}"
        assert "SUCCESS: Import failed as expected" in result.stdout
    finally:
        # Clean up the temporary script
        os.unlink(script_path)


def test_valid_drives():
    """Test that importing main.py succeeds when DRIVES contains valid paths."""
    # Create temporary directories for testing
    temp_dir1 = tempfile.mkdtemp()
    temp_dir2 = tempfile.mkdtemp()

    # Create a temporary script that imports config.py and then main.py
    script = f"""
import os
import sys
# Add the project root directory to the Python path
sys.path.append("{PROJECT_ROOT}")
# Set DRIVES environment variable with valid paths
os.environ["DRIVES"] = "{temp_dir1},{temp_dir2}"
# Import config.py first to set up config.DRIVES
from src.config import config
print(f"DEBUG: config.DRIVES = {{config.DRIVES}}")
# Import main.py, which should succeed
import main
# Check that DRIVES is correctly loaded
if config.DRIVES == ["{temp_dir1}", "{temp_dir2}"]:
    print("SUCCESS: Import succeeded and DRIVES is correctly loaded")
else:
    print(f"ERROR: DRIVES not correctly loaded. Expected [{temp_dir1}, {temp_dir2}], got {{config.DRIVES}}")
    sys.exit(1)
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(script.encode())
        script_path = f.name

    try:
        # Run the script and check the exit code
        result = subprocess.run(
            [sys.executable, script_path], capture_output=True, text=True
        )
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        print(f"Error: {result.stderr}")
        assert (
            result.returncode == 0
        ), f"Script failed with exit code {result.returncode}"
        assert (
            "SUCCESS: Import succeeded and DRIVES is correctly loaded" in result.stdout
        )
    finally:
        # Clean up the temporary script and directories
        os.unlink(script_path)
        shutil.rmtree(temp_dir1)
        shutil.rmtree(temp_dir2)
