from datetime import datetime, timedelta
from os import DirEntry
from typing import List

from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from .timestamp import LegacyTimeStamp


class LegacyBackgroundDir:
    def __init__(self, zoo_project: ZooscanProjectFolder):
        self.entries_by_date = zoo_project.zooscan_back.read_groups()

    def dates_older_than(self, start_timestamp: LegacyTimeStamp) -> List[DirEntry]:
        """
        Returns a list of DirEntry objects with dates older than the given timestamp.

        Args:
            start_timestamp (LegacyTimeStamp): The reference timestamp

        Returns:
            List[DirEntry]: List of DirEntry objects with dates older than the reference timestamp
        """
        # Filter entries by date
        result = []
        for date_str, entries in self.entries_by_date.items():
            # Convert date string to LegacyTimeStamp object
            entry_timestamp = LegacyTimeStamp.from_string(date_str)

            # Check if entry date is older than (before) the reference timestamp
            if entry_timestamp < start_timestamp:
                result.extend(entries)

        return result

    def dates_younger_than(
        self, start_timestamp: LegacyTimeStamp
    ) -> List[LegacyTimeStamp]:
        """
        Returns a list of LegacyTimeStamp objects with dates younger than the given timestamp.

        Args:
            start_timestamp (LegacyTimeStamp): The reference timestamp

        Returns:
            List[LegacyTimeStamp]: List of LegacyTimeStamp objects with dates younger than the reference timestamp
        """
        # Filter entries by date
        result = []
        for date_str, entries in self.entries_by_date.items():
            # Convert date string to LegacyTimeStamp object
            entry_timestamp = LegacyTimeStamp.from_string(date_str)

            # Check if entry date is younger than (after) the reference timestamp
            if entry_timestamp > start_timestamp:
                result.append(entry_timestamp)

        return result


def find_final_background_file(project: ZooscanProjectFolder, background_date: str):
    ret = project.zooscan_back.get_processed_background_file(background_date, 1)
    return ret


def find_raw_background_file(
    project: ZooscanProjectFolder, background_date: str, index: str
):
    ret = project.zooscan_back.get_raw_background_file(background_date, index)
    return ret
