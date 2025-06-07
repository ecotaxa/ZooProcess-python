import pytest
from Models import SubSampleData


def test_subsample_data_validation_success():
    """Test that SubSampleData validation succeeds when all fields are valid"""
    # This should succeed
    subsample_data = SubSampleData(
        scanning_operator="Test Operator",
        scan_id="test_scan_id",
        fraction_id="d1",
        fraction_id_suffix="01",
        fraction_min_mesh=200,
        fraction_max_mesh=300,
        spliting_ratio=4,
        observation="Test observation",
        submethod="Test submethod",
    )
    assert subsample_data.fraction_max_mesh > subsample_data.fraction_min_mesh
    assert subsample_data.scanning_operator == "Test Operator"
    assert subsample_data.scan_id == "test_scan_id"
    assert subsample_data.fraction_id == "d1"
    assert subsample_data.fraction_id_suffix == "01"
    assert subsample_data.observation == "Test observation"
    assert subsample_data.submethod == "Test submethod"


def test_subsample_data_validation_failure_mesh():
    """Test that SubSampleData validation fails when fraction_max_mesh <= fraction_min_mesh"""
    # This should fail because fraction_max_mesh is equal to fraction_min_mesh
    with pytest.raises(
        ValueError, match="fraction_max_mesh must be larger than fraction_min_mesh"
    ):
        SubSampleData(
            scanning_operator="Test Operator",
            scan_id="test_scan_id",
            fraction_id="d1",
            fraction_id_suffix="01",
            fraction_min_mesh=300,
            fraction_max_mesh=300,
            spliting_ratio=4,
            observation="Test observation",
            submethod="Test submethod",
        )

    # This should fail because fraction_max_mesh is less than fraction_min_mesh
    with pytest.raises(
        ValueError, match="fraction_max_mesh must be larger than fraction_min_mesh"
    ):
        SubSampleData(
            scanning_operator="Test Operator",
            scan_id="test_scan_id",
            fraction_id="d1",
            fraction_id_suffix="01",
            fraction_min_mesh=400,
            fraction_max_mesh=300,
            spliting_ratio=4,
            observation="Test observation",
            submethod="Test submethod",
        )


def test_subsample_data_validation_failure_empty_strings():
    """Test that SubSampleData validation fails when string fields are empty"""
    # Test each string field with empty string
    non_empty_string_fields = [
        "scanning_operator",
        "scan_id",
        "fraction_id",
        # "fraction_id_suffix",
        "observation",
        "submethod",
    ]

    for field in non_empty_string_fields:
        with pytest.raises(ValueError, match="String fields cannot be empty"):
            # Create a dictionary with valid values for all fields
            valid_data = {
                "scanning_operator": "Test Operator",
                "scan_id": "test_scan_id",
                "fraction_id": "d1",
                "fraction_id_suffix": "01",
                "fraction_min_mesh": 200,
                "fraction_max_mesh": 300,
                "spliting_ratio": 4,
                "observation": "Test observation",
                "submethod": "Test submethod",
            }
            # Set the current field to empty string
            valid_data[field] = ""
            # Try to create the model with the empty string
            SubSampleData(**valid_data)

    # Test with whitespace-only strings
    for field in non_empty_string_fields:
        with pytest.raises(ValueError, match="String fields cannot be empty"):
            valid_data = {
                "scanning_operator": "Test Operator",
                "scan_id": "test_scan_id",
                "fraction_id": "d1",
                "fraction_id_suffix": "01",
                "fraction_min_mesh": 200,
                "fraction_max_mesh": 300,
                "spliting_ratio": 4,
                "observation": "Test observation",
                "submethod": "Test submethod",
            }
            valid_data[field] = "   "
            SubSampleData(**valid_data)
