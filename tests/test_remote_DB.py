import pytest
from pytest_mock import MockFixture

from remote.DB import DB


def test_init_with_valid_bearer_and_default_db():
    # Arrange

    # Act
    bearer_token = "test_bearer"
    db_instance = DB(bearer_token)

    # Assert
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
def test_get_retrieves_json_data_from_valid_url(mocker: MockFixture):
    # Arrange
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.status_code = 200  # Add status_code attribute
    mock_get = mocker.patch("requests.get", return_value=mock_response)

    db = DB("test_token")
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
def test_get_handles_empty_url_parameter(mocker: MockFixture):
    # Create a mock response with status_code 200
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    # Patch requests.get to return our mock response
    mock_get = mocker.patch("requests.get", return_value=mock_response)

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
    from config_rdr import config

    # Act
    db = DB("test_token")

    # print("url", db.makeUrl("/test"))

    # Assert
    assert db.db == "http://zooprocess.imev-mer.fr:8081/v1"
    assert db.bearer == "test_token"
    assert db.db == config.DB_SERVER

    assert db.makeUrl("/test") == "http://zooprocess.imev-mer.fr:8081/v1/test"


def test_db_init_with_swapped_parameters():
    db_url = "http://test-url.com"
    bearer_token = "test_bearer"

    with pytest.raises(ValueError) as excinfo:
        db_instance = DB(db=bearer_token, bearer=db_url)

    assert str(excinfo.value) == "Invalid DB URL format"
