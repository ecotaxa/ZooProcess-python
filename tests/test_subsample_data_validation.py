import pytest
from Models import SubSampleData


def test_subsample_data_validation_success():
    """Test that SubSampleData validation succeeds when fraction_max_mesh > fraction_min_mesh"""
    # This should succeed
    subsample_data = SubSampleData(
        scanning_operator="Test Operator",
        scan_id="test_scan_id",
        fraction_number="d1",
        fraction_id_suffix="01",
        fraction_min_mesh=200,
        fraction_max_mesh=300,
        spliting_ratio=4,
        observation="Test observation",
    )
    assert subsample_data.fraction_max_mesh > subsample_data.fraction_min_mesh


def test_subsample_data_validation_failure():
    """Test that SubSampleData validation fails when fraction_max_mesh <= fraction_min_mesh"""
    # This should fail because fraction_max_mesh is equal to fraction_min_mesh
    with pytest.raises(
        ValueError, match="fraction_max_mesh must be larger than fraction_min_mesh"
    ):
        SubSampleData(
            scanning_operator="Test Operator",
            scan_id="test_scan_id",
            fraction_number="d1",
            fraction_id_suffix="01",
            fraction_min_mesh=300,
            fraction_max_mesh=300,
            spliting_ratio=4,
            observation="Test observation",
        )

    # This should fail because fraction_max_mesh is less than fraction_min_mesh
    with pytest.raises(
        ValueError, match="fraction_max_mesh must be larger than fraction_min_mesh"
    ):
        SubSampleData(
            scanning_operator="Test Operator",
            scan_id="test_scan_id",
            fraction_number="d1",
            fraction_id_suffix="01",
            fraction_min_mesh=400,
            fraction_max_mesh=300,
            spliting_ratio=4,
            observation="Test observation",
        )
