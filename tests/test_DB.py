from src.remote_db.DB import DB

import pytest
from unittest.mock import patch, MagicMock

import sys


@pytest.fixture
def setup_db():
    # This fixture replaces the setUp method
    return {"maxDiff": None, "capturedOutput": sys.stdout}


@patch("src.DB.requests")
def test_init_with_valid_bearer_and_default_db(mock_requests):
    # # Arrange
    # # with mock.patch('src.DB.requests') as mock_requests:

    # #     mock_config = mocker.patch('config.db', 'http://example.com/')
    # bearer_token = "valid_token"

    # # Act
    # db_instance = DB("test_bearer")

    # # db_instance = DB(bearer=bearer_token)

    # # Assert
    # self.assertEqual(db_instance.bearer, bearer_token)
    # self.assertEqual(db_instance.db, "http://example.com")

    bearer_token = "test_bearer"
    db_instance = DB(bearer_token)
    assert db_instance.bearer == bearer_token
    assert db_instance.db == "http://zooprocess.imev-mer.fr:8081/v1"


def test_init_with_empty_bearer_raises_error():
    # Arrange
    empty_bearer = ""

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        DB(bearer=empty_bearer)

    assert str(excinfo.value) == "Bearer token is required"


# Successfully retrieves JSON data from a valid URL
def test_get_retrieves_json_data_from_valid_url():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"key": "value"}

    with patch("requests.get", return_value=mock_response) as mock_get:
        db = DB("test_token")
        # db.bearer = "test_token"
        db.db = "http://test-url.com"

        # Act
        result = db.get("/test-path")

        # Assert
        mock_get.assert_called_once_with(
            "http://test-url.com/test-path",
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json",
            },
        )
        assert result == {"key": "value"}


# Handles empty URL parameter
@patch("requests.get")
def test_get_handles_empty_url_parameter(mock_get):
    db = DB("test_token", "http://test-url.com")
    db.get("")
    mock_get.assert_called_once_with(
        "http://test-url.com/",
        headers={
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json",
        },
    )


def test_get_db_from_config():
    # Arrange
    from src.config import config

    # Act
    db = DB("test_token")

    # print("url", db.makeUrl("/test"))

    # Assert
    assert db.db == "http://zooprocess.imev-mer.fr:8081/v1"
    assert db.bearer == "test_token"
    assert db.db == config.dbserver

    assert db.makeUrl("/test") == "http://zooprocess.imev-mer.fr:8081/v1/test"


def test_db_init_with_swapped_parameters():
    db_url = "http://test-url.com"
    bearer_token = "test_bearer"

    with pytest.raises(ValueError) as excinfo:
        db_instance = DB(db=bearer_token, bearer=db_url)

    assert str(excinfo.value) == "Invalid DB URL format"
