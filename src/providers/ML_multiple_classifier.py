import shutil
from pathlib import Path
from typing import List, Tuple, Optional

import requests

from Models import MultiplesClassifierRsp
from logger import logger
from providers.ML_multiple_separator import zip_images_to_tempfile

LS_VIGNETTES_PATH = Path(
    "/mnt/pgssd2t/zooscan_lov/Zooscan_apero_tha_bioness_2_sn033/Zooscan_scan/_work/apero2023_tha_bioness_013_st46_d_n5_d2_2_sur_2_1"
)
SERVER = "https://inference-walton.cloud.imagine-ai.eu/system/services/zooprocess-multiple-classifier/exposed/main/"  # Timeout on zip submission
SERVER = "http://localhost:55001/"  # Docker image from instructions at https://github.com/ai4os-hub/zooprocess-multiple-classifier
BASE_URI = "v2/models/zooprocess_multiple_classifier/predict/"


def classify_all_images_from(
    path: Path,
) -> Tuple[Optional[MultiplesClassifierRsp], Optional[str]]:
    """
    Process multiple images using the classifier service and parse the JSON responses.

    Args:
        path: Directory containing the images

    Returns:
        List of tuples, each containing:
        - SeparationResponse object parsed from the JSON response
        - Error message if any, None otherwise
    """
    logger.info(f"Processing images in: {path}")

    # Example 2: Create a zip file of images in a directory
    print("\nCreating a zip file of images...")
    zip_path = zip_images_to_tempfile(path)
    print(f"Created zip file at: {zip_path}")

    # Get JSON response
    separation_response, error = call_classify_server(zip_path)

    if not separation_response:
        logger.error(f"Failed to process {zip_path}: {error}")
        return separation_response, error

    logger.info(f"Successfully processed {zip_path}")
    nb_predictions = len(separation_response.scores)
    logger.info(f"Found {nb_predictions} predictions")
    potentials_ones = use_classifications(path, separation_response)

    logger.info(f"Copied {len(potentials_ones)} images: {potentials_ones}")
    return separation_response, error


def use_classifications(
    base_dir: Path, classification_response: MultiplesClassifierRsp
) -> List[Tuple[str, float]]:
    ret = []
    # Create an empty 'v10' subdirectory
    multiples_dir = base_dir / "multiples_to_separate" / "v10"
    if multiples_dir.exists():
        shutil.rmtree(multiples_dir)
    multiples_dir.mkdir(parents=False)

    for a_name, a_score in zip(
        classification_response.names, classification_response.scores
    ):
        if a_score <= 0.5:
            continue
        # Construct the full target path from base_dir and filename
        full_path = base_dir / a_name
        shutil.copy(full_path, multiples_dir / a_name)
        ret.append((a_name, a_score))
    return ret


def call_classify_server(
    image_or_zip_path: Path, bottom_crop: int = 31
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
    results = classify_all_images_from(LS_VIGNETTES_PATH)


if __name__ == "__main__":
    main()
