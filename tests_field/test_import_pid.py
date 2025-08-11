import json
import pytest
from legacy_to_remote.importe import pid2json


@pytest.mark.skip(
    reason="Not really a test, but permits to see the result of the conversion"
)
def test_pid_import():
    """
    Test the import of a PID file and conversion to JSON.
    Not really a test, but permit to see the result of the conversion
    """

    pid_filepath = "/Volumes/sgalvagno/plankton/zooscan_zooprocess_test/Zooscan_apero_pp_2023_wp2_sn002/Zooscan_scan/_work/apero2023_pp_wp2_001_st01_d_d1_1/apero2023_pp_wp2_001_st01_d_d1_1_dat1.pid"

    json_data = pid2json(pid_filepath)

    print("json: ", json_data)

    json_filepath = pid_filepath.replace(".pid", ".json")

    # Save to JSON file
    with open(json_filepath, "w") as f:
        json.dump(json_data, f, indent=4)
