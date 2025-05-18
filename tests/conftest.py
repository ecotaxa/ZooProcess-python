import sys
from pathlib import Path
import pytest
import unittest
import inspect

sys.path.append(str(Path(__file__).parent.parent))


# This hook will automatically convert unittest-style tests to pytest format
def pytest_collect_file(parent, path):
    if path.ext == ".py" and path.basename.startswith("test_"):
        return pytest.Module.from_parent(parent, fspath=path)


# This hook will automatically convert unittest.TestCase classes to pytest functions
def pytest_pycollect_makeitem(collector, name, obj):
    if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
        return [pytest.Class.from_parent(collector, name=name, obj=obj)]
    return None
