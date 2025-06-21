import os
import random
from logging import Logger
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import requests

from Models import MultiplesSeparatorRsp
from ZooProcess_lib.img_tools import load_image, saveimage
from logger import logger
from providers.ImageList import ImageList
from config_rdr import config

BGR_RED_COLOR = (0, 0, 255)
RGB_RED_COLOR = (255, 0, 0)

BASE_URI = "v2/models/zooprocess_multiple_separator/predict/"


def separate_each_image_from(
    path: Path,
) -> List[Tuple[str, Optional[MultiplesSeparatorRsp], Optional[str]]]:
    """
    Process multiple images using the separator service, one call per file.

    Args:
        path: Directory containing the images

    Returns:
        List of tuples, each containing:
        - Filename
        - SeparationResponse object parsed from the JSON response
        - Error message if any, None otherwise
    """
    logger.info(f"Processing images in: {path}")

    results = []

    # Use Path.glob to find all jpg files in the directory and convert to list
    file_paths = list(path.glob("*.jpg"))
    # Shuffle the list to process files in random order
    random.shuffle(file_paths)

    for file_path in file_paths:
        name = file_path.name
        logger.info(f"Processing file: {name}")

        # Get JSON response
        separation_response, error = call_separate_server(file_path)

        results.append((name, separation_response, error))

        if separation_response:
            logger.info(f"Successfully processed {name}")
            logger.info(f"Found {len(separation_response.predictions)} predictions")
        else:
            logger.error(f"Failed to process {name}: {error}")
            continue

    logger.info(f"Processed {len(results)} images")
    return results


def separate_all_images_from(
    logger: Logger,
    image_list: ImageList,
) -> Tuple[Optional[MultiplesSeparatorRsp], Optional[str]]:
    """
    Process multiple images using the separator service and parse the JSON responses.

    Args:
        logger: Logger instance
        image_list: ImageList containing the images to process

    Returns:
        List of tuples, each containing:
        - SeparationResponse object parsed from the JSON response
        - Error message if any, None otherwise
    """
    # Create a zip file of images from the ImageList
    zip_path = image_list.zipped(logger)

    # Get JSON response
    separation_response, error = call_separate_server(zip_path)

    if not separation_response:
        logger.error(f"Failed to process {zip_path}: {error}")
        return separation_response, error

    logger.info(f"Successfully processed {zip_path}")
    nb_predictions = len(separation_response.predictions)
    logger.info(f"Got {nb_predictions} predictions")
    os.unlink(zip_path)
    return separation_response, error


def show_separations_in_images(
    base_dir: Path, separation_response: MultiplesSeparatorRsp, separated_dir: Path
) -> List[Path]:
    ret = []

    predictions = separation_response.predictions
    for a_prediction in predictions:
        coords = a_prediction.separation_coordinates
        filename = a_prediction.name

        output_path = build_separated_image(base_dir, coords, filename, separated_dir)

        if output_path is not None:
            logger.info(f"Saved separated image to {output_path}")
            ret.append(output_path)
    return ret


def build_separated_image(
    base_dir: Path, coords: List[List[int]], filename: str, separated_dir: Path
) -> Optional[Path]:
    # Construct the full path from base_dir and filename
    full_path = base_dir / filename
    # Open the image from the constructed path
    color_image = load_image(full_path, cv2.IMREAD_COLOR_BGR)
    # Draw coords in the image
    # coords is a list of two lists: [x-coords], [y-coords]
    assert len(coords) == 2
    x_coords = coords[0]
    y_coords = coords[1]
    assert len(x_coords) == len(y_coords)
    if len(x_coords) == 0:
        # Nothing found to separate
        return None
    # Create a list of points from the coordinates
    points = list(zip(y_coords, x_coords))
    # Draw individual points
    for y, x in points:
        cv2.circle(color_image, (y, x), 1, BGR_RED_COLOR, -1)
    # Save the result in subdirectory 'separated' of base directory
    png_filename = filename.replace(".jpg", ".png")
    output_path = separated_dir / png_filename
    saveimage(color_image, png_filename, path=str(separated_dir))
    return output_path


def call_separate_server(
    image_or_zip_path: Path, bottom_crop: int = 31
) -> Tuple[Optional[MultiplesSeparatorRsp], Optional[str]]:
    """
    Send an image to the separator service using the BASE_URL and parse the JSON response.

    Args:
        image_or_zip_path: Path to the single image file, or zip with images, to send
        bottom_crop: Number of pixels to crop from the bottom (default: 0)

    Returns:
        Tuple containing:
        - SeparationResponse object parsed from the JSON response
        - Error message if any, None otherwise
    """
    mime_type = (
        "image/jpeg" if image_or_zip_path.suffix == ".jpg" else "application/zip"
    )
    try:
        with open(image_or_zip_path, "rb") as images_data:
            file_dict = {
                "images": (image_or_zip_path.name, images_data, mime_type),
            }

            # Construct URL with query parameters
            url = f"{config.SEPARATOR_SERVER}{BASE_URI}?bottom_crop={bottom_crop}"

            headers = {
                "accept": "application/json",
            }

            logger.info("Request to separator service")
            logger.debug(f"url: {url}")
            logger.debug(f"headers: {headers}")

            # Make POST request with multipart/form-data
            response = requests.post(
                url, files=file_dict, headers=headers, timeout=(10, 1200)
            )
            logger.info(f"Response status: {response.status_code}")

            if not response.ok:
                error_msg = (
                    f"Request failed: {response.status_code} - {response.reason}"
                )
                logger.error(error_msg)
                return None, error_msg
            try:
                # Parse the JSON response
                response_data = response.json()

                # Create a SeparationResponse object from the JSON
                separation_response = MultiplesSeparatorRsp(**response_data)

                # Log success
                logger.info(
                    f"Successfully parsed separation response for {image_or_zip_path}"
                )
                logger.info(f"Found {len(separation_response.predictions)} predictions")

                return separation_response, None

            except Exception as e:
                error_msg = f"Error parsing JSON response: {str(e)}"
                logger.error(error_msg)
                return None, error_msg

    except Exception as e:
        error_msg = f"Error sending request: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def do_separation_file_by_file(
    to_separate: Path,
) -> List[Tuple[str, Optional[MultiplesSeparatorRsp], Optional[str]]]:
    """
    Process all jpg files in a directory using the separator service and parse the JSON responses.

    Args:
        to_separate: Path to the directory containing the images

    Returns:
        List of tuples, each containing:
        - Filename
        - SeparationResponse model parsed from the JSON response
        - Error message if any, None otherwise
    """
    logger.info(f"Processing files in: {to_separate}")

    # Process the images
    results = separate_each_image_from(to_separate)

    # Log summary
    success_count = sum(1 for _, resp, _ in results if resp is not None)
    logger.info(f"Successfully processed {success_count} out of {len(results)} images")

    return results
