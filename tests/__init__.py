import sys
from pathlib import Path
import unittest

sys.path.append(str(Path(__file__).parent.parent))

class BaseTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
