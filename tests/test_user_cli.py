"""
Tests for the user_cli module.

This module contains tests for the user management CLI commands.
"""

import pytest
from click.testing import CliRunner
from pytest_mock import MockFixture
from sqlalchemy.exc import IntegrityError

from commands.user_cli import app
from src.local_DB.models import User

runner = CliRunner()


@pytest.fixture
def mock_sqlalchemy_db(mocker: MockFixture):
    """
    Mock the SQLAlchemyDB context manager.
    """
    # Create a mock for the database session
    mock_db = mocker.MagicMock()
    mock_session = mocker.MagicMock()
    mock_db.session = mock_session

    # Create a mock for the SQLAlchemyDB class
    mock_db_class = mocker.MagicMock()
    mock_db_class.__enter__.return_value = mock_db
    mock_db_class.__exit__.return_value = None

    # Create a mock for the SQLAlchemyDB constructor
    mock_sqlalchemy_db_constructor = mocker.patch("commands.user_cli.SQLAlchemyDB")
    mock_sqlalchemy_db_constructor.return_value = mock_db_class

    yield mock_db


def test_add_user_success(mock_sqlalchemy_db, mocker: MockFixture):
    """
    Test adding a user successfully.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session

    # Mock uuid.uuid4 to return a predictable value
    mocker.patch("uuid.uuid4", return_value="test-uuid")

    # Mock the database interaction to avoid IntegrityError
    # We'll simulate a successful add operation
    mock_session.add.return_value = None
    mock_session.commit.return_value = None

    # Act
    # Mock click.exit to prevent it from exiting the test
    mocker.patch("commands.user_cli.click.exit")
    result = runner.invoke(
        app,
        ["add", "--name", "Test User", "--email", "unique@example.com"],
        input="password\npassword\n",
    )

    # Assert
    assert result.exit_code == 0
    assert "User added successfully" in result.stdout

    # Verify that session.add was called with a User object
    assert mock_session.add.called
    user_arg = mock_session.add.call_args[0][0]
    assert isinstance(user_arg, User)
    assert user_arg.name == "Test User"
    assert user_arg.email == "unique@example.com"
    assert user_arg.password == "password"

    # Verify that session.commit was called
    assert mock_session.commit.called


def test_add_user_password_mismatch(mock_sqlalchemy_db):
    """
    Test adding a user with mismatched passwords.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session

    # Act
    result = runner.invoke(
        app,
        ["add", "--name", "Test User", "--email", "test@example.com"],
        input="password1\npassword2\n",
    )

    # Assert
    assert result.exit_code == 1
    assert "Passwords do not match" in result.stdout

    # Verify that session.add was not called
    assert not mock_session.add.called

    # Verify that session.commit was not called
    assert not mock_session.commit.called


def test_add_user_email_exists(mock_sqlalchemy_db):
    """
    Test adding a user with an email that already exists.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session
    mock_session.add.side_effect = IntegrityError("", "", "")

    # Act
    result = runner.invoke(
        app,
        ["add", "--name", "Test User", "--email", "test@example.com"],
        input="password\npassword\n",
    )

    # Assert
    assert result.exit_code == 1
    assert "Error: Email already exists" in result.stdout


def test_update_user_success(mock_sqlalchemy_db, mocker):
    """
    Test updating a user successfully.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session

    # Create a mock user with the necessary attributes
    mock_user = mocker.MagicMock(spec=User)
    mock_user.id = "test-id"
    mock_user.name = "Old Name"
    mock_user.email = "old@example.com"

    # Set up the query chain to return our mock user
    mock_query = mocker.MagicMock()
    mock_filter = mocker.MagicMock()
    mock_first = mocker.MagicMock(return_value=mock_user)

    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_user

    # Mock the commit to avoid database errors
    mock_session.commit.return_value = None

    # Act
    # Mock click.exit to prevent it from exiting the test
    mocker.patch("commands.user_cli.click.exit")
    result = runner.invoke(
        app,
        [
            "update",
            "--id",
            "test-id",
            "--name",
            "New Name",
            "--email",
            "new@example.com",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "User test-id updated successfully" in result.stdout

    # Verify that the user was updated
    assert mock_user.name == "New Name"
    assert mock_user.email == "new@example.com"

    # Verify that session.commit was called
    assert mock_session.commit.called


def test_update_user_not_found(mock_sqlalchemy_db):
    """
    Test updating a user that doesn't exist.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session
    mock_session.query.return_value.filter.return_value.first.return_value = None

    # Act
    result = runner.invoke(
        app, ["update", "--id", "nonexistent-id", "--name", "New Name"]
    )

    # Assert
    assert result.exit_code == 1
    assert "User with ID nonexistent-id not found" in result.stdout

    # Verify that session.commit was not called
    assert not mock_session.commit.called


def test_remove_user_success(mock_sqlalchemy_db, mocker):
    """
    Test removing a user successfully with force option.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session

    # Create a mock user with the necessary attributes
    mock_user = mocker.MagicMock(spec=User)
    mock_user.id = "test-id"
    mock_user.name = "Test User"
    mock_user.email = "test@example.com"

    # Set up the query chain to return our mock user
    mock_query = mocker.MagicMock()
    mock_filter = mocker.MagicMock()
    mock_first = mocker.MagicMock(return_value=mock_user)

    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_user

    # Mock the delete and commit to avoid database errors
    mock_session.delete.return_value = None
    mock_session.commit.return_value = None

    # Act
    # Mock click.exit to prevent it from exiting the test
    mocker.patch("commands.user_cli.click.exit")
    result = runner.invoke(app, ["remove", "--id", "test-id", "--force"])

    # Assert
    assert result.exit_code == 0
    assert "User test-id removed successfully" in result.stdout

    # Verify that session.delete was called with the user
    mock_session.delete.assert_called_once_with(mock_user)

    # Verify that session.commit was called
    assert mock_session.commit.called


def test_remove_user_not_found(mock_sqlalchemy_db):
    """
    Test removing a user that doesn't exist.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session
    mock_session.query.return_value.filter.return_value.first.return_value = None

    # Act
    result = runner.invoke(app, ["remove", "--id", "nonexistent-id", "--force"])

    # Assert
    assert result.exit_code == 1
    assert "User with ID nonexistent-id not found" in result.stdout

    # Verify that session.delete was not called
    assert not mock_session.delete.called

    # Verify that session.commit was not called
    assert not mock_session.commit.called


def test_list_users_success(mock_sqlalchemy_db, mocker):
    """
    Test listing users successfully.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session

    # Since we can't control the exact output format of the rich table,
    # we'll mock the console.print method to capture what would be printed
    mock_console_print = mocker.patch("commands.user_cli.console.print")

    # Create mock users
    mock_user1 = mocker.MagicMock(spec=User)
    mock_user1.id = "user1-id"
    mock_user1.name = "User 1"
    mock_user1.email = "user1@example.com"

    mock_user2 = mocker.MagicMock(spec=User)
    mock_user2.id = "user2-id"
    mock_user2.name = "User 2"
    mock_user2.email = "user2@example.com"

    # Set up the query to return our mock users
    mock_session.query.return_value.all.return_value = [mock_user1, mock_user2]

    # Act
    result = runner.invoke(app, ["list"])

    # Assert
    assert result.exit_code == 0

    # Since we mocked console.print, we can verify it was called
    assert mock_console_print.called

    # The output might be empty because we mocked console.print
    # We just need to verify that the exit code is 0 and console.print was called


def test_list_users_empty(mock_sqlalchemy_db):
    """
    Test listing users when there are no users.
    """
    # Arrange
    mock_session = mock_sqlalchemy_db.session
    mock_session.query.return_value.all.return_value = []

    # Act
    result = runner.invoke(app, ["list"])

    # Assert
    assert result.exit_code == 0
    # The actual output contains "No users found in the database"
    assert "No users found in the database" in result.stdout
