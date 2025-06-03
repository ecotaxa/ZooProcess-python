import pytest
from modern.from_legacy import from_legacy_meta
from modern.utils import convert_ddm_to_decimal_degrees


def test_basic_key_conversion():
    """Test basic key conversion from legacy to modern format."""
    # Create a sample legacy metadata dictionary
    legacy_meta = {
        "sampleid": "apero2023_tha_bioness_sup2000_017_st66_d_n1",
        "ship": "thalassa",
        "scientificprog": "apero",
        "stationid": "66",
        "depth": "99999",
        "nettype": "bioness",
        "netmesh": "2000",
    }

    # Convert to modern format
    modern_meta = from_legacy_meta(legacy_meta)

    # Verify the conversion
    assert modern_meta["sample_id"] == "apero2023_tha_bioness_sup2000_017_st66_d_n1"
    assert modern_meta["ship_name"] == "thalassa"
    assert modern_meta["scientific_program"] == "apero"
    assert modern_meta["station_id"] == "66"
    assert modern_meta["bottom_depth"] == "99999"
    assert modern_meta["net_sampling_type"] == "bioness"
    assert modern_meta["net_mesh"] == "2000"


def test_latitude_longitude_transformation():
    """Test the special transformation of latitude and longitude values."""
    # Create a sample legacy metadata dictionary with latitude and longitude
    legacy_meta = {
        "latitude": "48.27162",
        "longitude": "22.30036",
        "latitude_end": "48.27162",
        "longitude_end": "22.30039",
    }

    # Convert to modern format
    modern_meta = from_legacy_meta(legacy_meta)

    # Verify the conversion
    # Latitude should be converted to decimal degrees
    assert modern_meta["latitude_start"] == convert_ddm_to_decimal_degrees("48.27162")
    assert modern_meta["latitude_start"] == 48.4527

    # Longitude should be converted to decimal degrees and negated
    assert modern_meta["longitude_start"] == -convert_ddm_to_decimal_degrees("22.30036")
    assert modern_meta["longitude_start"] == -22.50060

    # Same for end coordinates
    assert modern_meta["latitude_end"] == convert_ddm_to_decimal_degrees("48.27162")
    assert modern_meta["latitude_end"] == 48.4527

    assert modern_meta["longitude_end"] == -convert_ddm_to_decimal_degrees("22.30039")
    assert modern_meta["longitude_end"] == -22.50065


def test_fracid_special_case():
    """Test the special handling of fracid which maps to multiple modern keys."""
    # Test with fracid containing an underscore
    legacy_meta = {
        "fracid": "d1_1_sur_1",
    }

    modern_meta = from_legacy_meta(legacy_meta)

    # Verify the conversion
    assert modern_meta["fraction_id"] == "d1"
    assert modern_meta["fraction_id_suffix"] == "1_sur_1"

    # Test with fracid not containing an underscore
    legacy_meta = {
        "fracid": "d1",
    }

    modern_meta = from_legacy_meta(legacy_meta)

    # Verify the conversion
    assert modern_meta["fraction_id"] == "d1"
    assert modern_meta["fraction_id_suffix"] == ""


def test_missing_keys():
    """Test handling of missing keys in the input dictionary."""
    # Create a sample legacy metadata dictionary with some keys missing
    legacy_meta = {
        "sampleid": "apero2023_tha_bioness_sup2000_017_st66_d_n1",
        # ship is missing
        "scientificprog": "apero",
        # stationid is missing
    }

    # Convert to modern format
    modern_meta = from_legacy_meta(legacy_meta)

    # Verify the conversion
    assert modern_meta["sample_id"] == "apero2023_tha_bioness_sup2000_017_st66_d_n1"
    assert modern_meta["scientific_program"] == "apero"

    # Missing keys should not be in the result
    assert "ship_name" not in modern_meta
    assert "station_id" not in modern_meta


def test_keys_not_in_mapping():
    """Test that keys not in the mapping are not included in the result."""
    # Create a sample legacy metadata dictionary with keys not in the mapping
    legacy_meta = {
        "sampleid": "apero2023_tha_bioness_sup2000_017_st66_d_n1",
        "unknown_key": "some value",
        "another_unknown_key": "another value",
    }

    # Convert to modern format
    modern_meta = from_legacy_meta(legacy_meta)

    # Verify the conversion
    assert modern_meta["sample_id"] == "apero2023_tha_bioness_sup2000_017_st66_d_n1"

    # Keys not in the mapping should not be in the result
    assert "unknown_key" not in modern_meta
    assert "another_unknown_key" not in modern_meta


def test_empty_input():
    """Test with an empty input dictionary."""
    # Convert an empty dictionary
    modern_meta = from_legacy_meta({})

    # Verify the result is an empty dictionary
    assert modern_meta == {}


def test_none_input():
    """Test with None input."""
    # This should raise an AttributeError since None doesn't have an items attribute
    with pytest.raises(AttributeError):
        from_legacy_meta(None)
