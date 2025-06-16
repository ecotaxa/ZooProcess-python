"""
Test script for matrix helper functions.
"""

import os

import numpy as np

from src.helpers.matrix import save_matrix_as_binary, load_matrix_from_binary


def test_save_and_load_matrix():
    """Test saving and loading a binary matrix."""
    # Create a test matrix
    test_matrix = np.zeros((10, 20), dtype=bool)
    test_matrix[0, 0] = True
    test_matrix[5, 10] = True
    test_matrix[9, 19] = True

    # Save the matrix to a file
    test_file = "test_matrix.bin"
    save_matrix_as_binary(test_matrix, test_file)

    # Load the matrix from the file
    loaded_matrix = load_matrix_from_binary(test_file)

    # Check that the loaded matrix matches the original
    assert loaded_matrix.shape == test_matrix.shape
    assert np.array_equal(loaded_matrix, test_matrix)

    # Clean up
    os.remove(test_file)
    print("Test passed!")


def test_different_sizes():
    """Test matrices of different sizes."""
    # Test a small matrix
    small_matrix = np.zeros((3, 3), dtype=bool)
    small_matrix[1, 1] = True

    # Test a large matrix
    large_matrix = np.zeros((100, 200), dtype=bool)
    large_matrix[50, 100] = True

    # Test matrices with different dimensions
    wide_matrix = np.zeros((10, 100), dtype=bool)
    wide_matrix[5, 50] = True

    tall_matrix = np.zeros((100, 10), dtype=bool)
    tall_matrix[50, 5] = True

    for matrix, name in [
        (small_matrix, "small"),
        (large_matrix, "large"),
        (wide_matrix, "wide"),
        (tall_matrix, "tall"),
    ]:
        test_file = f"test_{name}_matrix.bin"
        save_matrix_as_binary(matrix, test_file)
        loaded_matrix = load_matrix_from_binary(test_file)
        assert loaded_matrix.shape == matrix.shape
        assert np.array_equal(loaded_matrix, matrix)
        os.remove(test_file)

    print("Size tests passed!")


if __name__ == "__main__":
    test_save_and_load_matrix()
    test_different_sizes()
    print("All tests passed!")
