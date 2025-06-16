"""
Helper functions for matrix operations.
"""

import numpy as np
import struct
import gzip
from pathlib import Path


def save_matrix_as_binary(matrix: np.ndarray, filename: str) -> None:
    """
    Save a binary matrix to a gzip-compressed file.

    Args:
        matrix: A 2D numpy array containing the matrix data (0s and 1s)
        filename: The name of the output file

    This function encodes the matrix as a binary file with the following format:
    - First 4 bytes: width (uint32, little endian)
    - Next 4 bytes: height (uint32, little endian)
    - Remaining bytes: matrix data, where each bit represents a cell in the matrix
      (1 for true/set, 0 for false/unset), packed into bytes row by row

    The entire file is compressed using gzip.
    """
    height, width = matrix.shape
    row_bytes = (
        width + 7
    ) // 8  # Ceiling division to get number of bytes needed per row

    # Create a buffer to hold the data
    buffer = bytearray(8 + height * row_bytes)

    # Store dimensions (4 bytes for width, 4 for height)
    struct.pack_into("<II", buffer, 0, width, height)

    # Encode the bits row by row
    for y in range(height):
        for x in range(width):
            if matrix[y, x]:
                byte_index = (
                    8 + y * row_bytes + (x >> 3)
                )  # x >> 3 is equivalent to x // 8
                bit = 7 - (x % 8)  # Bit position within the byte (MSB first)
                buffer[byte_index] |= 1 << bit

    # Write the buffer to a gzip-compressed file
    with gzip.open(filename, "wb") as f:
        f.write(buffer)


def load_matrix_from_binary(filename: str) -> np.ndarray:
    """
    Load a binary matrix from a gzip-compressed file.

    Args:
        filename: The name of the input file

    Returns:
        A 2D numpy array containing the matrix data
    """
    with gzip.open(filename, "rb") as f:
        data = f.read()

    # Extract dimensions
    width, height = struct.unpack_from("<II", data, 0)

    # Create an empty matrix
    matrix = np.zeros((height, width), dtype=bool)

    # Calculate row bytes
    row_bytes = (width + 7) // 8

    # Decode the bits
    for y in range(height):
        for x in range(width):
            byte_index = 8 + y * row_bytes + (x >> 3)
            bit = 7 - (x % 8)
            if byte_index < len(data) and (data[byte_index] & (1 << bit)):
                matrix[y, x] = True

    return matrix
