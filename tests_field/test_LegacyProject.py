import pytest
from pathlib import Path
from Models import Project
from legacy_to_remote.LegacyProject import LegacyProject


# Initialize LegacyProject with a valid Project object containing an existing path
@pytest.mark.skip(reason="Obsolete piqv ref.")
def test_init_with_valid_project_path():
    # Create a test path that exists
    test_path = Path.cwd()
    project = Project(
        id="6789R",
        path=str(test_path),
        bearer="test_bearer",
        db="test_db",
        instrumentSerialNumber="test_serial",
    )

    # Act
    legacy_project = LegacyProject(project)

    # Assert
    assert legacy_project.project_name == test_path.name
    assert legacy_project.piqvhome == test_path.name.parent
    assert legacy_project.home == Path(test_path.name.parent)
    assert legacy_project.folder == test_path


# Initialize with a Project object containing a non-existent path
@pytest.mark.skip(reason="Not sure how to test this")
def test_init_with_nonexistent_project_path():
    # Create a test path that doesn't exist
    test_path = Path.cwd() / "nonexistent_directory"
    project = Project(
        path=str(test_path),
        bearer="test_bearer",
        db="test_db",
        instrumentSerialNumber="test_serial",
    )

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        legacy_project = LegacyProject(project)

    assert f"Project path '{test_path}' does not exist" in str(excinfo.value)
