import os
import shutil
from logging import Logger
from pathlib import Path
from typing import Tuple, Optional, List, NamedTuple

import requests

from Models import MultiplesClassifierRsp
from providers.ImageList import ImageList
from config_rdr import config

BASE_URI = "v2/models/zooprocess_multiple_classifier/predict/"


class NameAndScore(NamedTuple):
    name: str
    score: float


def classify_all_images_from(
    logger: Logger,
    img_path: Path,
    min_score: float,
    image_names: Optional[List[str]] = None,
) -> Tuple[List[NameAndScore], Optional[str]]:
    """
    Process multiple images using the classifier service and parse the JSON responses.

    Args:
        logger: Logger instance
        min_score: Minimum classification score, images above this score are discarded
        img_path: Directory containing the images
        image_names: Only use specified images, by file name. If not provided, all PNGs in img_path are used

    Returns:
        A tuple with:
        - list of (Vignette name, Vignette score)
        - Error message if any, None otherwise
    """
    logger.info(f"Classifying images for multiples in: {img_path}")

    # Create a zip file of images in a directory
    image_list = ImageList(img_path, images=image_names)
    zip_path = image_list.zipped(logger)

    # Get JSON response from classifier
    separation_response, error = call_classify_server(logger, zip_path)

    if not separation_response:
        logger.error(f"Failed to process {zip_path}: {error}")
        return [], error

    logger.info(f"Successfully processed {zip_path}")
    nb_predictions = len(separation_response.scores)
    logger.info(f"Found {nb_predictions} predictions")
    above_threshold = [
        NameAndScore(assoc[0], assoc[1])
        for assoc in zip(separation_response.names, separation_response.scores)
        if assoc[1] > min_score
    ]
    os.unlink(zip_path)
    return above_threshold, error


def use_classifications(
    base_dir: Path, multiples_dir: Path, selected_names: list[str]
) -> None:
    for a_name in selected_names:
        # Construct the full target path from base_dir and filename
        full_path = base_dir / a_name
        shutil.copy(full_path, multiples_dir / a_name)
    return


def call_classify_server(
    logger: Logger, image_or_zip_path: Path, bottom_crop: int = 31
) -> Tuple[Optional[MultiplesClassifierRsp], Optional[str]]:
    """
    Send an image to the classifier service using the BASE_URL and parse the JSON response.

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
            url = f"{config.CLASSIFIER_SERVER}{BASE_URI}?bottom_crop={bottom_crop}"

            headers = {
                "accept": "application/json",
            }

            logger.info("Request to multiples classifier service")
            logger.debug(f"url: {url}")
            logger.debug(f"headers: {headers}")

            # Make POST request with multipart/form-data
            response = requests.post(
                url, files=file_dict, headers=headers, timeout=(10, 600)
            )
            logger.debug(f"Response status: {response.status_code}")

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
                classification_response = MultiplesClassifierRsp(**response_data)

                # Log success
                logger.info(
                    f"Successfully parsed separation response for {image_or_zip_path}"
                )
                logger.info(f"Found {len(classification_response.scores)} predictions")

                return classification_response, None

            except Exception as e:
                error_msg = f"Error parsing JSON response: {str(e)}"
                logger.error(error_msg)
                return None, error_msg

    except Exception as e:
        error_msg = f"Error sending request: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
