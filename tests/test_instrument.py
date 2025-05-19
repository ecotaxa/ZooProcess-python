import pytest
from unittest.mock import Mock, patch

from src.request import getInstrumentFromSN
from src.Models import Instrument


def test_returns_matching_instrument():
    # Arrange
    db = Mock()  # Mock DB object
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
def test_returns_none_when_no_match():
    # Arrange
    db = Mock()  # Mock DB object
    sn = "NONEXISTENT"

    # Act
    result = getInstrumentFromSN(db, sn)

    # Assert
    assert result is None


# Test the new endpoint for getting an instrument by ID
def test_get_instrument_by_id():
    # Arrange
    from src.DB import get_instrument_by_id

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
    from src.DB import get_instrument_by_id

    # Act
    result = get_instrument_by_id("999")

    # Assert
    assert result is None
