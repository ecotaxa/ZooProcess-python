from typing import List

from Models import Instrument

# Hardcoded list of instruments
INSTRUMENTS = [
    {"id": "1", "model": "Zooscan", "name": "Zooscan 1", "sn": "ZS001"},
    {"id": "2", "model": "Zooscan", "name": "Zooscan 2", "sn": "ZS002"},
    {"id": "3", "model": "Zooscan", "name": "Zooscan 3", "sn": "ZS003"},
]


def get_instruments() -> List[Instrument]:
    """
    Returns a list of all instruments.

    Returns:
        List[Instrument]: A list of Instrument objects.
    """
    return [Instrument(**instrument) for instrument in INSTRUMENTS]


def get_instrument_by_id(instrument_id: str) -> Instrument:
    """
    Returns an instrument by its ID.

    Args:
        instrument_id (str): The ID of the instrument to retrieve.

    Returns:
        Instrument: The instrument with the specified ID, or None if not found.
    """
    for instrument in INSTRUMENTS:
        if instrument["id"] == instrument_id:
            return Instrument(**instrument)
    return None
