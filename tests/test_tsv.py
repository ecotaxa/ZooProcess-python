import json
from src.legacy_to_remote.importe import parse_tsv

import pytest


@pytest.mark.skip("")
def test_meta_sample():
    """
    Test the parse_tsv function to transform meta about sample into json.
    Not really a test, but permit to see the result
    """
    meta_path = "/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_meta/zooscan_sample_header_table.csv"

    json_data = parse_tsv(meta_path)

    print("json: ", json_data)

    json_filepath = meta_path.replace(".csv", ".json")

    # Save to JSON file
    with open(json_filepath, "w") as f:
        json.dump(json_data, f, indent=4)


@pytest.mark.skip("")
def test_meta_scan():
    """
    Test the parse_tsv function to transform meta about scan into json.
    Not really a test, but permit to see the result
    """

    meta_path = "/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_meta/zooscan_scan_header_table.csv"

    json_data = parse_tsv(meta_path)

    print("json: ", json_data)

    json_filepath = meta_path.replace(".csv", ".json")

    # Save to JSON file
    with open(json_filepath, "w") as f:
        json.dump(json_data, f, indent=4)
