"""
Helper functions for matrix operations.
"""

import gzip
import struct
import zlib

import numpy as np


def save_matrix_as_gzip(matrix: np.ndarray, filename: str) -> None:
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


def _construct_matrix_from_data(data: bytes) -> np.ndarray:
    """
    Construct a matrix from decompressed binary data.

    Args:
        data: Decompressed binary data containing the matrix

    Returns:
        A 2D numpy array containing the matrix data
    """
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


def load_matrix_from_gzip(filename: str) -> np.ndarray:
    """
    Load a binary matrix from a gzip-compressed file.

    Args:
        filename: The name of the input file

    Returns:
        A 2D numpy array containing the matrix data
    """
    with gzip.open(filename, "rb") as f:
        data = f.read()

    return _construct_matrix_from_data(data)


def is_valid_compressed_matrix(content: bytes) -> bool:
    """
    Check if the given content is a valid gzip or zip-encoded matrix.

    Args:
        content: Bytes content to validate

    Returns:
        True if the content is a valid gzip or zip-encoded matrix, False otherwise
    """
    try:
        # Use zlib.decompressobj with wbits=0 (auto)
        decompressor = zlib.decompressobj(wbits=0)
        data: bytes = decompressor.decompress(content)

        # Check if we have at least 8 bytes (for width and height)
        if len(data) >= 8:
            # Try to extract width and height
            width, height = struct.unpack_from("<II", data, 0)

            # Calculate expected size based on dimensions
            row_bytes = (width + 7) // 8
            expected_size = 8 + height * row_bytes

            # Check if the data size matches exactly the expected size
            if len(data) == expected_size:
                return True
    except Exception as e:
        # Not a valid gzip matrix, try zip next
        pass

    return False


def load_matrix_from_compressed(content: bytes) -> np.ndarray:
    """
    Load a binary matrix from compressed bytes content.

    Args:
        content: Compressed bytes content containing the matrix data

    Returns:
        A 2D numpy array containing the matrix data

    This function decompresses the content and extracts the matrix data.
    The content should be in the same format as expected by is_valid_compressed_matrix:
    - First 4 bytes: width (uint32, little endian)
    - Next 4 bytes: height (uint32, little endian)
    - Remaining bytes: matrix data, where each bit represents a cell in the matrix
      (1 for true/set, 0 for false/unset), packed into bytes row by row
    """
    # Try to decompress the content using different methods
    data = None

    # Try gzip first
    try:
        data = gzip.decompress(content)
    except Exception:
        pass

    # If gzip failed, try zlib with different window bits
    if data is None:
        try:
            # Try with gzip header (wbits=16+15)
            decompressor = zlib.decompressobj(wbits=16 + 15)
            data = decompressor.decompress(content)
        except Exception:
            # Try with raw deflate (wbits=-15)
            try:
                decompressor = zlib.decompressobj(wbits=-15)
                data = decompressor.decompress(content)
            except Exception:
                # Try with auto-detect (wbits=0)
                decompressor = zlib.decompressobj(wbits=0)
                data = decompressor.decompress(content)

    return _construct_matrix_from_data(data)
