import sys
import os
import uuid
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the project root and src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from local_DB.models import Base, User
from main import app, get_db


@pytest.fixture
def app_client():
    """
    Create a TestClient for the FastAPI app.

    This fixture creates a TestClient instance for testing API endpoints.

    Example usage:
    ```python
    def test_something(app_client):
        response = app_client.get("/some-endpoint")
        assert response.status_code == 200
    ```

    Returns:
        A FastAPI TestClient instance.
    """
    # Create the test client
    client = TestClient(app)

    # Return the client for use in tests
    yield client

    # Cleanup (equivalent to tearDown)
    app.dependency_overrides.clear()


@pytest.fixture
def local_db():
    """
    Create a SQLite database in a file for testing.

    This fixture creates a database, initializes the schema,
    and adds a user with known credentials for testing.

    The test user has the following credentials:
        - email: "test@example.com"
        - password: "test_password"
        - name: "Test User"

    Example usage:
    ```python
    def test_something(local_db):
        # Query the user from the database
        user = local_db.query(User).filter(User.email == "test@example.com").first()

        # Use the user for authentication
        from auth import get_user_from_db
        user = get_user_from_db("test@example.com", local_db)
    ```

    Returns:
        A SQLAlchemy session connected to the file-based database.
    """
    # Create a temporary file-based SQLite database
    temp_db_file = f"test_db_{uuid.uuid4()}.db"
    engine = create_engine(f"sqlite:///{temp_db_file}")

    # Create all tables in the database
    Base.metadata.create_all(engine)

    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a test user
    test_user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        password="test_password",
    )

    # Add the user to the database
    session.add(test_user)
    session.commit()

    # Return the session for use in tests
    yield session

    # Clean up after the test
    try:
        session.close()
    except Exception as e:
        # Ignore errors when closing the session
        # This prevents issues during teardown
        pass

    # Remove the temporary database file
    try:
        if os.path.exists(temp_db_file):
            os.remove(temp_db_file)
    except Exception as e:
        # Ignore errors when removing the file
        pass
