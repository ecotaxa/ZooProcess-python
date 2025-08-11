"""
Drawing utilities for image processing.
"""

import cv2
import numpy as np

from providers.ML_multiple_separator import RGB_RED_COLOR


def apply_matrix_onto(image: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    Apply a binary matrix onto an image by drawing red points where the matrix has True values.

    Args:
        image: A numpy array representing the image (RGB format)
        matrix: A 2D numpy array containing binary values (True/False or 1/0)

    Returns:
        A numpy array representing the image with red points drawn on it

    Raises:
        ValueError: If the dimensions of the image and matrix don't match
    """
    # Check if the dimensions match
    if image.shape[:2] != matrix.shape[:2]:
        raise ValueError(
            f"Image dimensions {image.shape[:2]} don't match matrix dimensions {matrix.shape}"
        )

    # Create a copy of the image to avoid modifying the original
    result_image = image.copy()

    # If the image is grayscale, convert it to BGR
    if len(result_image.shape) == 2:
        result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2RGB)

    # Draw red points at matrix "True" coordinates
    result_image[np.where(matrix)] = RGB_RED_COLOR

    return result_image
