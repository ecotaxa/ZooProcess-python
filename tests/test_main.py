import unittest
from unittest.mock import Mock, patch

from src.importe import getInstrumentFromSN 

class Test_main(unittest.TestCase):

    def test_returns_matching_instrument(self):
        # Arrange
        db = "http://localhost:8000/"
        bearer = "test-bearer"
        sn = "123ABC"
        mock_instrument = {"sn": "123ABC", "name": "Test Instrument"}
    
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [mock_instrument]
            mock_get.return_value = mock_response

            # Act
            result = getInstrumentFromSN(db, bearer, sn)

            # Assert
            self.assertEqual(result, mock_instrument)
            mock_get.assert_called_once_with(
                "http://localhost:8000/instruments",
                headers={
                    "Authorization": "Bearer test-bearer",
                    "Content-Type": "application/json"
                }
            )

    # Returns None when no instrument matches the provided serial number
    def test_returns_none_when_no_match(self):
        # Arrange
        db = "http://localhost:8000/"
        bearer = "test-bearer" 
        sn = "NONEXISTENT"
        mock_instruments = [
            {"sn": "123ABC", "name": "Test Instrument 1"},
            {"sn": "456DEF", "name": "Test Instrument 2"}
        ]

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_instruments
            mock_get.return_value = mock_response

            # Act
            result = getInstrumentFromSN(db, bearer, sn)

            # Assert
            self.assertIsNone(result)
            mock_get.assert_called_once_with(
                "http://localhost:8000/instruments",
                headers={
                    "Authorization": "Bearer test-bearer",
                    "Content-Type": "application/json"
                }
            )
