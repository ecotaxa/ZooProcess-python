from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from remote.request import getInstrumentFromSN
from main import app

client = TestClient(app)


def test_returns_matching_instrument(mocker: MockFixture):
    # Arrange
    db = mocker.Mock()  # Mock DB object
    sn = "sn001"  # Use a serial number from the hardcoded list

    # Act
    result = getInstrumentFromSN(db, sn)

    # Assert
    assert result is not None
    assert result["sn"] == sn
    assert result["name"] == "Zooscan 1"
    assert result["id"] == "sn001"
    assert result["model"] == "Zooscan"


# Returns None when no instrument matches the provided serial number
def test_returns_none_when_no_match(mocker: MockFixture):
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
    from modern.instrument import get_instrument_by_id

    # Act
    result = get_instrument_by_id("sn001")

    # Assert
    assert result is not None
    assert result.id == "sn001"
    assert result.name == "Zooscan 1"
    assert result.sn == "sn001"
    assert result.model == "Zooscan"
    # Check that ZooscanCalibration is present and has the expected structure
    assert result.ZooscanCalibration is not None
    assert isinstance(result.ZooscanCalibration, list)
    assert len(result.ZooscanCalibration) > 0
    calibration = result.ZooscanCalibration[0]
    assert calibration.id == f"cal-{result.id}"
    assert calibration.frame == "default"
    assert calibration.xOffset == 0.0
    assert calibration.yOffset == 0.0
    assert calibration.xSize == 2400.0
    assert calibration.ySize == 1800.0


# Test the new endpoint for getting an instrument by ID when the ID doesn't exist
def test_get_instrument_by_id_not_found():
    # Arrange
    from modern.instrument import get_instrument_by_id

    # Act
    result = get_instrument_by_id("999")

    # Assert
    assert result is None


# Test the instruments endpoint with full=False (default)
def test_get_instruments_simplified():
    # Act
    response = client.get("/api/instruments")

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
    response = client.get("/api/instruments?full=true")

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
        # Check that ZooscanCalibration is present
        assert "ZooscanCalibration" in instrument
        assert instrument["ZooscanCalibration"] is not None
        assert len(instrument["ZooscanCalibration"]) > 0
        # Check the first calibration
        calibration = instrument["ZooscanCalibration"][0]
        assert "id" in calibration
        assert calibration["id"] == f"cal-{instrument['id']}"
        assert "frame" in calibration
        assert calibration["frame"] == "default"
        assert "xOffset" in calibration
        assert calibration["xOffset"] == 0.0
        assert "yOffset" in calibration
        assert calibration["yOffset"] == 0.0
        assert "xSize" in calibration
        assert calibration["xSize"] == 2400.0
        assert "ySize" in calibration
        assert calibration["ySize"] == 1800.0
