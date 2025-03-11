

import json
from pathlib import Path
from src.importe import list_background, pid2json


import unittest
from unittest.mock import Mock, patch


class Test_Background_list(unittest.TestCase):

    @unittest.skip("")
    def test_Background_list(self):
        """
            Test the Background_list function.
            Not really a test, but permit to see the result
        """

        background_path = '/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_back'

        json_data = list_background(background_path)

        print("json: ", json_data)

        json_filepath = Path(background_path).joinpath('background_list.json').absolute()
    
        # Save to JSON file
        with open(json_filepath, 'w') as f:
            json.dump(json_data, f, indent=4)

        