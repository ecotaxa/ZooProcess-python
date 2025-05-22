import os

from src.config import config
from src.local_db.sqlite_db import SQLAlchemyDB, init_db
from src.local_db.models import Example, User


class TestSQLAlchemyDB:
    """Test the SQLAlchemyDB class and SQLAlchemy ORM functionality."""

    def test_db_creation(self):
        """Test that the database file is created."""
        # Initialize the database
        db_path = init_db()

        # Check that the database file exists
        assert os.path.exists(db_path)
        assert os.path.basename(db_path) == config.DB_NAME

    def test_db_session(self):
        """Test that we can create a SQLAlchemy session."""
        db = SQLAlchemyDB()
        with db:
            # Check that the session is created
            assert db.session is not None

    def test_orm_query(self):
        """Test that we can use SQLAlchemy ORM to query the database."""
        db = SQLAlchemyDB()
        with db:
            # Insert a test record using ORM
            example = Example(name="test_orm", value="orm_value")
            db.session.add(example)
            db.session.commit()

            # Query the test record using ORM
            result = db.session.query(Example).filter_by(name="test_orm").first()

            # Check that the record was inserted correctly
            assert result is not None
            assert result.name == "test_orm"
            assert result.value == "orm_value"

            # Clean up
            db.session.delete(result)
            db.session.commit()

    def test_user_orm_query(self):
        """Test that we can use SQLAlchemy ORM to query the User table."""
        db = SQLAlchemyDB()
        with db:
            # Insert a test user using ORM
            user = User(
                id="test123",
                name="Test User",
                email="test@example.com",
                password="encrypted_password_hash",  # Add encrypted password
            )
            db.session.add(user)
            db.session.commit()

            # Query the test user using ORM
            result = db.session.query(User).filter_by(id="test123").first()

            # Check that the user was inserted correctly
            assert result is not None
            assert result.id == "test123"
            assert result.name == "Test User"
            assert result.email == "test@example.com"
            assert result.password == "encrypted_password_hash"

            # Clean up
            db.session.delete(result)
            db.session.commit()
