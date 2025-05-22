from fastapi.testclient import TestClient

from remote.request import getInstrumentFromSN
from main import app

client = TestClient(app)


def test_returns_matching_instrument(mocker):
    # Arrange
    db = mocker.Mock()  # Mock DB object
    sn = "ZS001"  # Use a serial number from the hardcoded list

    # Act
    result = getInstrumentFromSN(db, sn)

    # Assert
    assert result is not None
    assert result["sn"] == sn
    assert result["name"] == "Zooscan 1"
    assert result["id"] == "1"
    assert result["model"] == "Zooscan"


# Returns None when no instrument matches the provided serial number
def test_returns_none_when_no_match(mocker):
    # Arrange
    db = mocker.Mock()  # Mock DB object
    sn = "NONEXISTENT"

    # Act
    result = getInstrumentFromSN(db, sn)

    # Assert
    assert result is None


# Test the new endpoint for getting an instrument by ID
def test_get_instrument_by_id():
    # Arrange
    from remote.DB import get_instrument_by_id

    # Act
    result = get_instrument_by_id("1")

    # Assert
    assert result is not None
    assert result.id == "1"
    assert result.name == "Zooscan 1"
    assert result.sn == "ZS001"
    assert result.model == "Zooscan"


# Test the new endpoint for getting an instrument by ID when the ID doesn't exist
def test_get_instrument_by_id_not_found():
    # Arrange
    from remote.DB import get_instrument_by_id

    # Act
    result = get_instrument_by_id("999")

    # Assert
    assert result is None


# Test the instruments endpoint with full=False (default)
def test_get_instruments_simplified():
    # Act
    response = client.get("/instruments")

    # Assert
    assert response.status_code == 200
    instruments = response.json()
    assert len(instruments) > 0
    # Check that each instrument only has id and name
    for instrument in instruments:
        assert "id" in instrument
        assert "name" in instrument
        assert "model" not in instrument
        assert "sn" not in instrument


# Test the instruments endpoint with full=True
def test_get_instruments_full():
    # Act
    response = client.get("/instruments?full=true")

    # Assert
    assert response.status_code == 200
    instruments = response.json()
    assert len(instruments) > 0
    # Check that each instrument has all fields
    for instrument in instruments:
        assert "id" in instrument
        assert "name" in instrument
        assert "model" in instrument
        assert "sn" in instrument
