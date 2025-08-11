import os

from config_rdr import config
from local_DB.sqlite_db import SQLiteDB, init_db


def test_db_creation():
    """Test that the database file is created."""
    # Initialize the database
    db_path = init_db()

    # Check that the database file exists
    assert os.path.exists(db_path)
    assert os.path.basename(db_path) == config.DB_NAME


def test_db_connection():
    """Test that we can connect to the database."""
    db = SQLiteDB()
    with db:
        # Execute a simple query
        cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        # Check that the required tables exist
        table_names = [table[0] for table in tables]
        assert "example" in table_names
        assert "user" in table_names


def test_db_query():
    """Test that we can execute queries on the database."""
    db = SQLiteDB()
    with db:
        # Insert a test record
        db.execute("INSERT INTO example (name, value) VALUES (?, ?)", ("test", "value"))
        db.commit()

        # Query the test record
        cursor = db.execute("SELECT * FROM example WHERE name=?", ("test",))
        result = cursor.fetchone()

        # Check that the record was inserted correctly
        assert result is not None
        assert result[1] == "test"
        assert result[2] == "value"

        # Clean up
        db.execute("DELETE FROM example WHERE name=?", ("test",))
        db.commit()
