

import json
from pathlib import Path
from src.importe import parse_tsv


import unittest
from unittest.mock import Mock, patch


class Test_MetaFile(unittest.TestCase):

    def test_meta_sample(self):
        """
            Test the parse_tsv function to transform meta about sample into json.
            Not really a test, but permit to see the result
        """

        meta_path = '/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_meta/zooscan_sample_header_table.csv'

        json_data = parse_tsv(meta_path)

        print("json: ", json_data)

        json_filepath = meta_path.replace('.csv', '.json')
    
        # Save to JSON file
        with open(json_filepath, 'w') as f:
            json.dump(json_data, f, indent=4)

    def test_meta_scan(self):
        """
            Test the parse_tsv function to transform meta about scan into json.
            Not really a test, but permit to see the result
        """

        meta_path = '/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_meta/zooscan_scan_header_table.csv'

        json_data = parse_tsv(meta_path)

        print("json: ", json_data)

        json_filepath = meta_path.replace('.csv', '.json')
    
        # Save to JSON file
        with open(json_filepath, 'w') as f:
            json.dump(json_data, f, indent=4)

        