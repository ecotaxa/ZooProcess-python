


from pathlib import Path
from src.Project import Project

import unittest

from src.LegacyProject import LegacyProject

class Test_LegacyProject(unittest.TestCase):


    # Initialize LegacyProject with a valid Project object containing an existing path
    # def test_init_with_valid_project_path(self):
    #     # Arrange
    
    #     test_path = Path(__file__).parent / "test_project"
    #     test_path.mkdir(exist_ok=True)
    
    #     project = Project.Project(
    #         path=str(test_path),
    #         bearer="test_bearer",
    #         db="test_db",
    #         instrumentSerialNumber="test_serial"
    #     )
    
    #     # Act
    #     legacy_project = LegacyProject(project)
    
    #     # Assert
    #     assert legacy_project.project_name == test_path.name
    #     assert legacy_project.folder == test_path
    #     assert Path(legacy_project.folder).exists()
    
    #     # Cleanup
    #     test_path.rmdir()

    # Initialize LegacyProject with a valid Project object containing an existing path
    def test_init_with_valid_project_path(self):
    
        # Create a test path that exists
        test_path = Path.cwd()
        project = Project(
            path=str(test_path),
            bearer="test_bearer",
            db="test_db",
            instrumentSerialNumber="test_serial"
        )
    
        # Act
        legacy_project = LegacyProject(project)
    
        # Assert
        self.assertEqual(legacy_project.project_name, test_path.name)
        self.assertEqual(legacy_project.piqvhome, test_path.name.parent)
        self.assertEqual(legacy_project.home, Path(test_path.name.parent))
        self.assertEqual(legacy_project.folder, test_path)


    # Initialize with a Project object containing a non-existent path
    def test_init_with_nonexistent_project_path(self):
    
        # Create a test path that doesn't exist
        test_path = Path.cwd() / "nonexistent_directory"
        project = Project(
            path=str(test_path),
            bearer="test_bearer",
            db="test_db",
            instrumentSerialNumber="test_serial"
        )
    
        # Act & Assert
        with self.assertRaises(Exception) as context:
            legacy_project = LegacyProject(project)
    
        self.assertIn(f"Project path '{test_path}' does not exist", str(context.exception))