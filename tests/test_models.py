import pytest
from src.Models import Instrument


def test_instrument_model_creation():
    # Test creating an Instrument with valid data
    instrument = Instrument(
        id="123", model="Zooscan", name="Test Instrument", sn="ABC123"
    )

    assert instrument.id == "123"
    assert instrument.model == "Zooscan"
    assert instrument.name == "Test Instrument"
    assert instrument.sn == "ABC123"


def test_instrument_model_validation():
    # Test that validation fails when required fields are missing
    with pytest.raises(ValueError):
        Instrument(
            id="123",
            model="Zooscan",
            name="Test Instrument",
            # Missing sn field
        )

    # Test that validation fails when model is not "Zooscan"
    with pytest.raises(ValueError):
        Instrument(
            id="123",
            model="InvalidModel",  # Not "Zooscan"
            name="Test Instrument",
            sn="ABC123",
        )
