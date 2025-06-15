import random
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import requests

from Models import MultiplesSeparatorRsp
from ZooProcess_lib.img_tools import load_image, saveimage
from logger import logger

BGR_RED_COLOR = (0, 0, 255)

LS_PATH = Path(
    "/mnt/pgssd2t/zooscan_lov/Zooscan_apero_tha_bioness_2_sn033/Zooscan_scan/_work/apero2023_tha_bioness_013_st46_d_n5_d2_2_sur_2_1/multiples_to_separate"
)
SERVER = "https://inference-walton.cloud.imagine-ai.eu/system/services/zooprocess-multiple-separator/exposed/main/"  # Timeout on zip submission
SERVER = "http://localhost:55000/"  # Docker image from instructions at https://github.com/ai4os-hub/zooprocess-multiple-separator
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

        apply_separations(path, separation_response)

    logger.info(f"Processed {len(results)} images")
    return results


def separate_all_images_from(
    path: Path,
) -> Tuple[Optional[MultiplesSeparatorRsp], Optional[str]]:
    """
    Process multiple images using the separator service and parse the JSON responses.

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
    separation_response, error = call_separate_server(zip_path)

    if not separation_response:
        logger.error(f"Failed to process {zip_path}: {error}")
        return separation_response, error

    logger.info(f"Successfully processed {zip_path}")
    nb_predictions = len(separation_response.predictions)
    logger.info(f"Found {nb_predictions} predictions")
    apply_separations(path, separation_response)

    logger.info(f"Got {nb_predictions} predictions")
    return separation_response, error


def apply_separations(
    base_dir: Path, separation_response: MultiplesSeparatorRsp
) -> List[Path]:
    ret = []
    predictions = separation_response.predictions
    for a_prediction in predictions:
        coords = a_prediction.separation_coordinates
        filename = a_prediction.name

        # Construct the full path from base_dir and filename
        full_path = base_dir / filename

        # Open the image from the constructed path
        image = load_image(full_path)

        # Convert grayscale image to color for drawing
        if len(image.shape) == 2:
            color_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            color_image = image.copy()

        # Draw coords in the image
        # coords is a list of two lists: [x-coords], [y-coords]
        assert len(coords) == 2
        x_coords = coords[0]
        y_coords = coords[1]

        # Create a list of points from the coordinates
        points = list(zip(y_coords, x_coords))

        # Draw individual points
        for y, x in points:
            cv2.circle(color_image, (y, x), 1, BGR_RED_COLOR, -1)

        # Create 'separated' subdirectory if it doesn't exist
        separated_dir = base_dir / "separated"
        if not separated_dir.exists():
            separated_dir.mkdir(parents=False)

        # Save the result in subdirectory 'separated' of base directory
        png_filename = filename.replace(".jpg", ".png")
        output_path = separated_dir / png_filename
        saveimage(color_image, png_filename, path=str(separated_dir))

        logger.info(f"Saved separated image to {output_path}")
        ret.append(output_path)
    return ret


def call_separate_server(
    image_or_zip_path: Path, min_mask_score: float = 0.9, bottom_crop: int = 0
) -> Tuple[Optional[MultiplesSeparatorRsp], Optional[str]]:
    """
    Send an image to the separator service using the BASE_URL and parse the JSON response.

    Args:
        image_or_zip_path: Path to the single image file, or zip with images, to send
        min_mask_score: Minimum score for mask detection (default: 0.9)
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
            url = f"{SERVER}{BASE_URI}?min_mask_score={min_mask_score}&bottom_crop={bottom_crop}"

            headers = {
                "accept": "application/json",
            }

            logger.info("Request to separator service")
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
                    separation_response = MultiplesSeparatorRsp(**response_data)

                    # Log success
                    logger.info(
                        f"Successfully parsed separation response for {image_or_zip_path}"
                    )
                    logger.info(
                        f"Found {len(separation_response.predictions)} predictions"
                    )

                    return separation_response, None

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


def zip_images_to_tempfile(directory_path: Path) -> Path:
    """
    Zips all images inside a given directory to a temporary zip file.

    Args:
        directory_path: Path to the directory containing images

    Returns:
        Path to the temporary zip file
    """
    logger.info(f"Zipping images from directory: {directory_path}")

    # Create a temporary file with .zip extension
    temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    temp_zip_path = Path(temp_zip.name)
    temp_zip.close()

    try:
        # Find all jpg files in the directory
        image_paths = list(directory_path.glob("*.jpg"))

        if not image_paths:
            logger.warning(f"No jpg images found in {directory_path}")
            return temp_zip_path

        # Create a zip file
        with zipfile.ZipFile(temp_zip_path, "w") as zip_file:
            # Add each image to the zip file
            for image_path in image_paths:
                logger.info(f"Adding {image_path.name} to zip file")
                zip_file.write(image_path, arcname=image_path.name)

        logger.info(
            f"Successfully created zip file with {len(image_paths)} images at {temp_zip_path}"
        )
        return temp_zip_path

    except Exception as e:
        logger.error(f"Error creating zip file: {str(e)}")
        # If an error occurs, return the path anyway so the caller can handle it
        return temp_zip_path


def main():
    # results = do_sep_file_by_file(LS_PATH)
    # # Print summary of results
    # print(f"\nProcessed {len(results)} images:")
    # for filename, response, error in results:
    #     if response:
    #         print(f"  ✓ {filename}: {len(response.predictions)} predictions")
    #     else:
    #         print(f"  ✗ {filename}: {error}")
    results = separate_all_images_from(LS_PATH)


if __name__ == "__main__":
    main()
