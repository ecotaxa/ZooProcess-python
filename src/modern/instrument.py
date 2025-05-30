from typing import List, Optional

from Models import Instrument, Calibration

# Hardcoded list of instruments
INSTRUMENTS = [
    {"id": "sn001", "model": "Zooscan", "name": "Zooscan 1", "sn": "sn001"},
    {"id": "sn002", "model": "Zooscan", "name": "Zooscan 2", "sn": "sn002"},
    {"id": "sn003", "model": "Zooscan", "name": "Zooscan 3", "sn": "sn003"},
    {"id": "sn033", "model": "Zooscan", "name": "Zooscan 33", "sn": "sn033"},
    {"id": "1", "model": "Zooscan", "name": "Zooscan HC", "sn": "sn001"},
]


def create_mock_calibration(instrument_id: str) -> Calibration:
    """
    Creates a mock ZooscanCalibration for an instrument.

    Args:
        instrument_id (str): The ID of the instrument to create a calibration for.

    Returns:
        Calibration: A mock calibration object.
    """
    return Calibration(
        id=f"cal-{instrument_id}",
        frame="default",
        xOffset=0.0,
        yOffset=0.0,
        xSize=2400.0,
        ySize=1800.0,
    )


def get_instruments() -> List[Instrument]:
    """
    Returns a list of all instruments.

    Returns:
        List[Instrument]: A list of Instrument objects.
    """
    instruments = []
    for instrument_data in INSTRUMENTS:
        instrument = Instrument(**instrument_data, ZooscanCalibration=[])
        # Add a mocked ZooscanCalibration to each instrument
        instrument.ZooscanCalibration = [create_mock_calibration(instrument.id)]
        instruments.append(instrument)
    return instruments


def get_instrument_by_id(instrument_id: str) -> Optional[Instrument]:
    """
    Returns an instrument by its ID.

    Args:
        instrument_id (str): The ID of the instrument to retrieve.

    Returns:
        Instrument: The instrument with the specified ID, or None if not found.
    """
    for instrument_data in INSTRUMENTS:
        if instrument_data["id"] == instrument_id:
            instrument = Instrument(**instrument_data)
            # Add a mocked ZooscanCalibration to the instrument
            instrument.ZooscanCalibration = [create_mock_calibration(instrument_id)]
            return instrument
    return None
