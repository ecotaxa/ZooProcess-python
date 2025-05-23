import pytest
from local_DB.models import User


def test_local_db_fixture(local_db):
    """
    Test that the local_db fixture creates a database with a test user.
    """
    # Query the user from the database
    user = local_db.query(User).filter(User.email == "test@example.com").first()

    # Check that the user exists and has the expected attributes
    assert user is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.password == "test_password"


def test_local_db_authentication(local_db):
    """
    Test that the local_db fixture can be used for authentication.
    """
    # Import the authentication function
    from auth import get_user_from_db

    # Get the user from the database using the authentication function
    user = get_user_from_db("test@example.com", local_db)

    # Check that the user exists and has the expected attributes
    assert user is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.password == "test_password"
