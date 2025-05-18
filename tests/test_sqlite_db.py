import os
import unittest
from pathlib import Path

from src.config import WORKING_DIR
from src.sqlite_db import SQLiteDB, init_db


class TestSQLiteDB(unittest.TestCase):
    """Test the SQLiteDB class."""

    def test_db_creation(self):
        """Test that the database file is created."""
        # Initialize the database
        db_path = init_db()

        # Check that the database file exists
        self.assertTrue(os.path.exists(db_path))
        self.assertEqual(os.path.basename(db_path), "v10.sqlite")

    def test_db_connection(self):
        """Test that we can connect to the database."""
        db = SQLiteDB()
        with db:
            # Execute a simple query
            cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            # Check that the required tables exist
            table_names = [table[0] for table in tables]
            self.assertIn("example", table_names)
            self.assertIn("user", table_names)

    def test_db_query(self):
        """Test that we can execute queries on the database."""
        db = SQLiteDB()
        with db:
            # Insert a test record
            db.execute(
                "INSERT INTO example (name, value) VALUES (?, ?)", ("test", "value")
            )
            db.commit()

            # Query the test record
            cursor = db.execute("SELECT * FROM example WHERE name=?", ("test",))
            result = cursor.fetchone()

            # Check that the record was inserted correctly
            self.assertIsNotNone(result)
            self.assertEqual(result[1], "test")
            self.assertEqual(result[2], "value")

            # Clean up
            db.execute("DELETE FROM example WHERE name=?", ("test",))
            db.commit()


if __name__ == "__main__":
    unittest.main()
