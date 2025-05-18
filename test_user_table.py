import sqlite3
import os
from src.config import WORKING_DIR
from src.sqlite_db import db_path
from src.db_models import User, get_engine


def test_user_table_exists():
    """
    Test if the User table exists in the database.
    """
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"Database file does not exist at: {db_path}")
        return False

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the user table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    table_exists = cursor.fetchone() is not None

    if table_exists:
        print("User table exists in the database.")

        # Check the table structure
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()

        print("User table columns:")
        for column in columns:
            print(f"  {column[1]}: {column[2]}, {'PRIMARY KEY' if column[5] else ''}")

        # Verify the expected columns exist
        expected_columns = {
            "id": "TEXT",
            "name": "TEXT",
            "email": "TEXT",
            "password": "TEXT",
        }
        actual_columns = {col[1]: col[2] for col in columns}

        for col_name, col_type in expected_columns.items():
            if col_name not in actual_columns:
                print(f"ERROR: Expected column '{col_name}' not found in User table")
                table_exists = False
            elif not actual_columns[col_name].startswith(col_type):
                print(
                    f"ERROR: Column '{col_name}' has type '{actual_columns[col_name]}', expected '{col_type}'"
                )
                table_exists = False

        if table_exists:
            print("User table has the correct structure.")
    else:
        print("User table does not exist in the database.")

    # Close the connection
    conn.close()
    return table_exists


if __name__ == "__main__":
    print(f"Testing User table in database: {db_path}")
    if test_user_table_exists():
        print("User table test passed.")
    else:
        print("User table test failed.")
