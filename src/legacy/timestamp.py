from datetime import datetime, timedelta
from typing import Optional, Union


class LegacyTimeStamp:
    """
    Class for manipulating legacy dates in the format "%Y%m%d_%H%M".
    """

    FORMAT = "%Y%m%d_%H%M"

    def __init__(self, dt: Optional[datetime] = None):
        """
        Initialize a LegacyTimeStamp with the given datetime or current time.

        Args:
            dt (datetime, optional): The datetime to use. Defaults to current time.
        """
        self.dt = dt if dt is not None else datetime.now()

    @classmethod
    def from_string(cls, timestamp_str: str) -> "LegacyTimeStamp":
        """
        Create a LegacyTimeStamp from a string in the format "%Y%m%d_%H%M".

        Args:
            timestamp_str (str): The timestamp string to parse

        Returns:
            LegacyTimeStamp: A new LegacyTimeStamp instance
        """
        dt = datetime.strptime(timestamp_str, cls.FORMAT)
        return cls(dt)

    @classmethod
    def now(cls) -> "LegacyTimeStamp":
        """
        Create a LegacyTimeStamp with the current time.

        Returns:
            LegacyTimeStamp: A new LegacyTimeStamp instance with current time
        """
        return cls()

    def to_string(self) -> str:
        """
        Convert the timestamp to a string in the format "%Y%m%d_%H%M".

        Returns:
            str: The formatted timestamp string
        """
        return self.dt.strftime(self.FORMAT)

    def __str__(self) -> str:
        """
        String representation of the timestamp.

        Returns:
            str: The formatted timestamp string
        """
        return self.to_string()

    def __repr__(self) -> str:
        """
        Representation of the LegacyTimeStamp instance.

        Returns:
            str: A string representation of the instance
        """
        return f"LegacyTimeStamp({self.dt.isoformat()})"

    def add_minutes(self, minutes: int) -> "LegacyTimeStamp":
        """
        Add minutes to the timestamp.

        Args:
            minutes (int): Number of minutes to add

        Returns:
            LegacyTimeStamp: A new LegacyTimeStamp with added minutes
        """
        new_dt = self.dt + timedelta(minutes=minutes)
        return LegacyTimeStamp(new_dt)

    def subtract_minutes(self, minutes: int) -> "LegacyTimeStamp":
        """
        Subtract minutes from the timestamp.

        Args:
            minutes (int): Number of minutes to subtract

        Returns:
            LegacyTimeStamp: A new LegacyTimeStamp with subtracted minutes
        """
        new_dt = self.dt - timedelta(minutes=minutes)
        return LegacyTimeStamp(new_dt)

    def __eq__(self, other: Union["LegacyTimeStamp", str, datetime]) -> bool:
        """
        Compare equality with another timestamp.

        Args:
            other: Another LegacyTimeStamp, datetime, or timestamp string

        Returns:
            bool: True if equal, False otherwise
        """
        if isinstance(other, LegacyTimeStamp):
            return self.dt == other.dt
        elif isinstance(other, str):
            return self.dt == datetime.strptime(other, self.FORMAT)
        elif isinstance(other, datetime):
            return self.dt == other
        return NotImplemented

    def __lt__(self, other: Union["LegacyTimeStamp", str, datetime]) -> bool:
        """
        Compare less than with another timestamp.

        Args:
            other: Another LegacyTimeStamp, datetime, or timestamp string

        Returns:
            bool: True if less than, False otherwise
        """
        if isinstance(other, LegacyTimeStamp):
            return self.dt < other.dt
        elif isinstance(other, str):
            return self.dt < datetime.strptime(other, self.FORMAT)
        elif isinstance(other, datetime):
            return self.dt < other
        return NotImplemented

    def __gt__(self, other: Union["LegacyTimeStamp", str, datetime]) -> bool:
        """
        Compare greater than with another timestamp.

        Args:
            other: Another LegacyTimeStamp, datetime, or timestamp string

        Returns:
            bool: True if greater than, False otherwise
        """
        if isinstance(other, LegacyTimeStamp):
            return self.dt > other.dt
        elif isinstance(other, str):
            return self.dt > datetime.strptime(other, self.FORMAT)
        elif isinstance(other, datetime):
            return self.dt > other
        return NotImplemented
