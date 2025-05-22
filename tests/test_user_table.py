import sqlite3
import os
import tempfile
import shutil
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))


def test_user_table_exists():
    """
    Test if the User table exists in the database and has the correct structure.
    """
    # Import the modules after setting up the environment
    from src.local_db.sqlite_db import db_path, init_db

    # Initialize the database
    db_file = init_db()

    # Check if the database file exists
    assert os.path.exists(db_path), f"Database file does not exist at: {db_path}"
    assert os.path.exists(db_file), f"Database file does not exist at: {db_file}"
    assert db_path == db_file, f"Database paths do not match: {db_path} != {db_file}"

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the user table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    result = cursor.fetchone()
    assert result is not None, "User table does not exist in the database"

    # Check the table structure
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()

    # Verify the expected columns exist with correct types
    expected_columns = {
        "id": "TEXT",
        "name": "TEXT",
        "email": "TEXT",
        "password": "TEXT",
    }
    actual_columns = {col[1]: col[2] for col in columns}

    # In SQLite, these types are equivalent
    type_equivalents = {
        "TEXT": ["TEXT", "VARCHAR"],
        "INTEGER": ["INTEGER", "INT"],
        "REAL": ["REAL", "FLOAT", "DOUBLE"],
        "BLOB": ["BLOB"],
        "NUMERIC": ["NUMERIC", "DECIMAL"],
    }

    for col_name, expected_type in expected_columns.items():
        assert (
            col_name in actual_columns
        ), f"Expected column '{col_name}' not found in User table"

        actual_type = actual_columns[col_name]
        valid_types = type_equivalents.get(expected_type, [expected_type])

        assert any(
            actual_type.upper().startswith(t.upper()) for t in valid_types
        ), f"Column '{col_name}' has type '{actual_type}', expected one of {valid_types}"

    # Close the connection
    conn.close()


if __name__ == "__main__":
    # Set up the environment
    temp_dir = tempfile.mkdtemp()
    original_drives = os.environ.get("DRIVES", "")
    os.environ["DRIVES"] = temp_dir

    try:
        # Run the test
        print("Testing User table in database...")
        test_user_table_exists()
        print("User table test passed.")
    except AssertionError as e:
        print(f"User table test failed: {e}")
    finally:
        # Clean up
        if original_drives:
            os.environ["DRIVES"] = original_drives
        else:
            os.environ.pop("DRIVES", None)
        shutil.rmtree(temp_dir)
