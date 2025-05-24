# Mock ZooProcess_lib module
import sys
from pathlib import Path
from unittest.mock import MagicMock

from pytest_mock import MockFixture

# Create a mock for ZooProcess_lib
sys.modules["ZooProcess_lib"] = MagicMock()
sys.modules["ZooProcess_lib.ZooscanFolder"] = MagicMock()
sys.modules["ZooProcess_lib.ZooscanFolder"].ZooscanProjectFolder = MagicMock
sys.modules["ZooProcess_lib.ZooscanFolder"].ZooscanDrive = MagicMock

# Now we can import from modern.from_legacy
from modern.from_legacy import backgrounds_from_legacy_project
from Models import Drive


def test_background_from_legacy_project(mocker: MockFixture):
    """
    Test the background_from_legacy_project function by mocking the values returned by get_dates() and content.
    """
    # Create a mock ZooscanProjectFolder
    mock_project = mocker.MagicMock()
    mock_project.project = "test_project"

    # Create a mock Drive
    mock_drive = Drive(id="test_drive", name="test_drive", url="/path/to/test_drive")
    mock_project.drive = mock_drive

    # Create a mock ZooscanBackFolder
    mock_back_folder = mocker.MagicMock()
    mock_project.zooscan_back = mock_back_folder

    # Mock the get_dates method to return a list of dates
    mock_dates = ["20230101_1200", "20230102_1300"]
    mock_back_folder.get_dates.return_value = mock_dates

    # Create mock background entries
    mock_background_path1 = mocker.MagicMock(spec=Path)
    mock_background_path1.__str__.return_value = "/path/to/background1.tif"

    mock_background_path2 = mocker.MagicMock(spec=Path)
    mock_background_path2.__str__.return_value = "/path/to/background2.tif"

    # Mock the content dictionary
    mock_back_folder.content = {
        "20230101_1200": {
            "final_background": mock_background_path1,
        },
        "20230102_1300": {
            "final_background": mock_background_path2,
        },
    }

    # Mock the extract_serial_number function
    mock_extract_serial_number = mocker.patch(
        "modern.from_legacy.extract_serial_number"
    )
    mock_extract_serial_number.return_value = "TEST123"

    # Call the function
    backgrounds = backgrounds_from_legacy_project(mock_drive, mock_project)

    # Verify the results
    assert len(backgrounds) == 2

    # Check the first background
    assert backgrounds[0].id == "test_project_20230101_1200_background"
    assert backgrounds[0].name == "20230101_1200_background"
    assert backgrounds[0].url == "/path/to/background1.tif"
    assert backgrounds[0].createdAt == "20230101_1200"
    assert backgrounds[0].user.id == "user1"
    assert backgrounds[0].instrument.sn == "TEST123"

    # Check the second background
    assert backgrounds[1].id == "test_project_20230102_1300_background"
    assert backgrounds[1].name == "20230102_1300_background"
    assert backgrounds[1].url == "/path/to/background2.tif"
    assert backgrounds[1].createdAt == "20230102_1300"
    assert backgrounds[1].user.id == "user1"
    assert backgrounds[1].instrument.sn == "TEST123"

    # Verify that extract_serial_number was called with the correct argument
    mock_extract_serial_number.assert_called_once_with("test_project")


def test_background_from_legacy_project_no_backgrounds(mocker: MockFixture):
    """
    Test the background_from_legacy_project function when there are no backgrounds.
    """
    # Create a mock ZooscanProjectFolder
    mock_project = mocker.MagicMock()
    mock_project.project = "test_project"

    # Create a mock Drive
    mock_drive = Drive(id="test_drive", name="test_drive", url="/path/to/test_drive")
    mock_project.drive = mock_drive

    # Create a mock ZooscanBackFolder
    mock_back_folder = mocker.MagicMock()
    mock_project.zooscan_back = mock_back_folder

    # Mock the get_dates method to return an empty list
    mock_back_folder.get_dates.return_value = []

    # Mock the content dictionary
    mock_back_folder.content = {}

    # Mock the extract_serial_number function
    mock_extract_serial_number = mocker.patch(
        "modern.from_legacy.extract_serial_number"
    )
    mock_extract_serial_number.return_value = "TEST123"

    # Call the function
    backgrounds = backgrounds_from_legacy_project(mock_drive, mock_project)

    # Verify the results
    assert len(backgrounds) == 0

    # Verify that extract_serial_number was called with the correct argument
    mock_extract_serial_number.assert_called_once_with("test_project")


def test_background_from_legacy_project_no_final_background(mocker: MockFixture):
    """
    Test the background_from_legacy_project function when there is no final_background.
    """
    # Create a mock ZooscanProjectFolder
    mock_project = mocker.MagicMock()
    mock_project.project = "test_project"

    # Create a mock Drive
    mock_drive = Drive(id="test_drive", name="test_drive", url="/path/to/test_drive")
    mock_project.drive = mock_drive

    # Create a mock ZooscanBackFolder
    mock_back_folder = mocker.MagicMock()
    mock_project.zooscan_back = mock_back_folder

    # Mock the get_dates method to return a list of dates
    mock_dates = ["20230101_1200"]
    mock_back_folder.get_dates.return_value = mock_dates

    # Mock the content dictionary with no final_background
    mock_back_folder.content = {
        "20230101_1200": {
            "final_background": None,
        }
    }

    # Mock the extract_serial_number function
    mock_extract_serial_number = mocker.patch(
        "modern.from_legacy.extract_serial_number"
    )
    mock_extract_serial_number.return_value = "TEST123"

    # Call the function
    backgrounds = backgrounds_from_legacy_project(mock_drive, mock_project)

    # Verify the results
    assert len(backgrounds) == 0

    # Verify that extract_serial_number was called with the correct argument
    mock_extract_serial_number.assert_called_once_with("test_project")
