import shutil
from logging import Logger
from pathlib import Path
from typing import Tuple, Optional

import requests

from Models import MultiplesClassifierRsp
from logger import logger
from providers.utils import zip_images_to_tempfile

LS_VIGNETTES_PATH = Path(
    "/mnt/pgssd2t/zooscan_lov/Zooscan_apero_tha_bioness_2_sn033/Zooscan_scan/_work/apero2023_tha_bioness_013_st46_d_n5_d2_2_sur_2_1"
)
SERVER = "https://inference-walton.cloud.imagine-ai.eu/system/services/zooprocess-multiple-classifier/exposed/main/"
SERVER = "http://localhost:55001/"  # Docker image from instructions at https://github.com/ai4os-hub/zooprocess-multiple-classifier
BASE_URI = "v2/models/zooprocess_multiple_classifier/predict/"


def classify_all_images_from(
    logger: Logger, img_path: Path, min_score: float, multiples_path: Path
) -> Tuple[Optional[MultiplesClassifierRsp], Optional[str]]:
    """
    Process multiple images using the classifier service and parse the JSON responses.

    Args:
        logger: Logger instance
        min_score: Minimum classification score, images above this score are discarded
        img_path: Directory containing the images
        multiples_path: Directory where images considered as probable multiples will be copied

    Returns:
        List of tuples, each containing:
        - SeparationResponse object parsed from the JSON response
        - Error message if any, None otherwise
    """
    logger.info(f"Classifying images for multiples in: {img_path}")

    # Create a zip file of images in a directory
    zip_path = zip_images_to_tempfile(logger, img_path)

    # Get JSON response from classifier
    separation_response, error = call_classify_server(logger, zip_path)

    if not separation_response:
        logger.error(f"Failed to process {zip_path}: {error}")
        return separation_response, error

    logger.info(f"Successfully processed {zip_path}")
    nb_predictions = len(separation_response.scores)
    logger.info(f"Found {nb_predictions} predictions")
    above_threshold = [
        assoc[1]
        for assoc in zip(separation_response.scores, separation_response.names)
        if assoc[0] > min_score
    ]
    use_classifications(img_path, multiples_path, above_threshold)

    logger.info(f"Copied {len(above_threshold)} images into {multiples_path}")
    return separation_response, error


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
            url = f"{SERVER}{BASE_URI}?bottom_crop={bottom_crop}"

            headers = {
                "accept": "application/json",
            }

            logger.info("Request to multiples classifier service")
            logger.info(f"url: {url}")
            logger.info(f"headers: {headers}")

            # Make POST request with multipart/form-data
            response = requests.post(url, files=file_dict, headers=headers)
            logger.info(f"Response status: {response.status_code}")

            if response.ok:
                try:
                    # Parse the JSON response
                    response_data = response.json()

                    # Create a SeparationResponse object from the JSON
                    classification_response = MultiplesClassifierRsp(**response_data)

                    # Log success
                    logger.info(
                        f"Successfully parsed separation response for {image_or_zip_path}"
                    )
                    logger.info(
                        f"Found {len(classification_response.scores)} predictions"
                    )

                    return classification_response, None

                except Exception as e:
                    error_msg = f"Error parsing JSON response: {str(e)}"
                    logger.error(error_msg)
                    return None, error_msg
            else:
                error_msg = (
                    f"Request failed: {response.status_code} - {response.reason}"
                )
                logger.error(error_msg)
                return None, error_msg

    except Exception as e:
        error_msg = f"Error sending request: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def main():
    results = classify_all_images_from(logger, LS_VIGNETTES_PATH, 0.5, Path("/tmp"))


if __name__ == "__main__":
    main()
