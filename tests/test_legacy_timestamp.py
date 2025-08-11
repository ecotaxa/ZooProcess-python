from unittest.mock import MagicMock

import pytest

from legacy.backgrounds import LegacyBackgroundDir
from legacy.timestamp import LegacyTimeStamp


@pytest.fixture
def mock_zoo_project():
    """
    Create a mock ZooscanProjectFolder with entries from 2021.
    """
    mock_project = MagicMock()
    mock_back_folder = MagicMock()
    mock_project.zooscan_back = mock_back_folder

    # Create mock entries for 2021 dates from the example directory
    # zooscan_lov/Zooscan_triatlas_m158_2019_mtn_200microns_sn001_1SAMPLE/Zooscan_back/
    entries_2021 = {
        "20210622_1421": [
            _create_mock_dir_entry("20210622_1421_background_large_manual.tif")
        ],
        "20210623_1041": [
            _create_mock_dir_entry("20210623_1041_background_large_manual.tif")
        ],
        "20210624_0852": [
            _create_mock_dir_entry("20210624_0852_background_large_manual.tif")
        ],
        "20210625_0921": [
            _create_mock_dir_entry("20210625_0921_background_large_manual.tif")
        ],
    }

    mock_back_folder.read_groups.return_value = entries_2021

    return mock_project


def _create_mock_dir_entry(name):
    """
    Create a mock DirEntry object.
    """
    mock_entry = MagicMock()
    mock_entry.name = name
    mock_entry.path = f"zooscan_lov/Zooscan_triatlas_m158_2019_mtn_200microns_sn001_1SAMPLE/Zooscan_back/{name}"
    return mock_entry


class TestDatesOlderThan:
    """
    Test the dates_older_than method of the LegacyBackgroundDir class.
    """

    def test_dates_older_than_all_included(self, mock_zoo_project):
        """
        Test that all entries are returned when the reference date is after all entries.
        """
        # Create a LegacyBackgroundDir instance with the mock project
        background_dir = LegacyBackgroundDir(mock_zoo_project)

        # Create a reference timestamp after all entries (July 1, 2021)
        reference_timestamp = LegacyTimeStamp.from_string("20210701_0000")

        # Get entries older than the reference timestamp
        older_entries = background_dir.dates_older_than(reference_timestamp)

        # All entries should be included (4 entries)
        assert len(older_entries) == 4

        # Verify that all entries from 2021 are included
        entry_names = [entry.name for entry in older_entries]
        assert "20210622_1421_background_large_manual.tif" in entry_names
        assert "20210623_1041_background_large_manual.tif" in entry_names
        assert "20210624_0852_background_large_manual.tif" in entry_names
        assert "20210625_0921_background_large_manual.tif" in entry_names

    def test_dates_older_than_some_included(self, mock_zoo_project):
        """
        Test that only entries older than the reference date are returned.
        """
        # Create a LegacyBackgroundDir instance with the mock project
        background_dir = LegacyBackgroundDir(mock_zoo_project)

        # Create a reference timestamp in the middle of the entries (June 24, 2021, 09:00)
        reference_timestamp = LegacyTimeStamp.from_string("20210624_0900")

        # Get entries older than the reference timestamp
        older_entries = background_dir.dates_older_than(reference_timestamp)

        # Only entries before June 24, 09:00 should be included (3 entries)
        assert len(older_entries) == 3

        # Verify that only the correct entries are included
        entry_names = [entry.name for entry in older_entries]
        assert "20210622_1421_background_large_manual.tif" in entry_names
        assert "20210623_1041_background_large_manual.tif" in entry_names
        assert "20210624_0852_background_large_manual.tif" in entry_names
        assert "20210625_0921_background_large_manual.tif" not in entry_names

    def test_dates_older_than_none_included(self, mock_zoo_project):
        """
        Test that no entries are returned when the reference date is before all entries.
        """
        # Create a LegacyBackgroundDir instance with the mock project
        background_dir = LegacyBackgroundDir(mock_zoo_project)

        # Create a reference timestamp before all entries (June 1, 2021)
        reference_timestamp = LegacyTimeStamp.from_string("20210601_0000")

        # Get entries older than the reference timestamp
        older_entries = background_dir.dates_older_than(reference_timestamp)

        # No entries should be included
        assert len(older_entries) == 0


class TestDatesYoungerThan:
    """
    Test the dates_younger_than method of the LegacyBackgroundDir class.
    """

    def test_dates_younger_than_all_included(self, mock_zoo_project):
        """
        Test that all dates are returned when the reference date is before all entries.
        """
        # Create a LegacyBackgroundDir instance with the mock project
        background_dir = LegacyBackgroundDir(mock_zoo_project)

        # Create a reference timestamp before all entries (June 1, 2021)
        reference_timestamp = LegacyTimeStamp.from_string("20210601_0000")

        # Get dates younger than the reference timestamp
        younger_dates = background_dir.dates_younger_than(reference_timestamp)

        # All dates should be included (4 dates)
        assert len(younger_dates) == 4

        # Verify that all dates from 2021 are included
        date_strings = [date.to_string() for date in younger_dates]
        assert "20210622_1421" in date_strings
        assert "20210623_1041" in date_strings
        assert "20210624_0852" in date_strings
        assert "20210625_0921" in date_strings

    def test_dates_younger_than_some_included(self, mock_zoo_project):
        """
        Test that only dates younger than the reference date are returned.
        """
        # Create a LegacyBackgroundDir instance with the mock project
        background_dir = LegacyBackgroundDir(mock_zoo_project)

        # Create a reference timestamp in the middle of the entries (June 24, 2021, 09:00)
        reference_timestamp = LegacyTimeStamp.from_string("20210624_0900")

        # Get dates younger than the reference timestamp
        younger_dates = background_dir.dates_younger_than(reference_timestamp)

        # Only dates after June 24, 09:00 should be included (1 date)
        assert len(younger_dates) == 1

        # Verify that only the correct dates are included
        date_strings = [date.to_string() for date in younger_dates]
        assert "20210622_1421" not in date_strings
        assert "20210623_1041" not in date_strings
        assert "20210624_0852" not in date_strings
        assert "20210625_0921" in date_strings

    def test_dates_younger_than_none_included(self, mock_zoo_project):
        """
        Test that no dates are returned when the reference date is after all entries.
        """
        # Create a LegacyBackgroundDir instance with the mock project
        background_dir = LegacyBackgroundDir(mock_zoo_project)

        # Create a reference timestamp after all entries (July 1, 2021)
        reference_timestamp = LegacyTimeStamp.from_string("20210701_0000")

        # Get dates younger than the reference timestamp
        younger_dates = background_dir.dates_younger_than(reference_timestamp)

        # No dates should be included
        assert len(younger_dates) == 0
