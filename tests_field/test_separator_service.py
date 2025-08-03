import importlib
import os
from pathlib import Path

import pytest

import config_rdr
from helpers.logger import logger

HERE = Path(__file__).parent

base_dir = Path(
    "/mnt/zooscan_pool/zooscan/remote/complex/piqv/plankton/zooscan_lov/Zooscan_apero_tha_bioness_sn033/Zooscan_scan/_work"
)
out_dir = Path("/tmp")


def test_separate_auto_big_image():
    os.environ["APP_ENV"] = "dev"
    os.chdir(HERE.parent)
    importlib.reload(config_rdr)
    from providers.ML_multiple_separator import (
        call_separate_server,
        build_separated_image,
    )

    filename = "apero2023_tha_bioness_006_st20_n_n7_d1_2_sur_2_1_12.jpg"
    big_shrimp = base_dir / scan_dirs[0] / filename
    separation_response, _ = call_separate_server(big_shrimp)
    prediction = separation_response.predictions[0]
    output_path = build_separated_image(
        base_dir, prediction.separation_coordinates, filename, out_dir
    )
    print(output_path)


scan_dirs = [
    "apero2023_tha_bioness_006_st20_n_n7_d1_2_sur_2_1",
    "apero2023_tha_bioness_006_st20_n_n7_d2_1_sur_4_1",
    "apero2023_tha_bioness_006_st20_n_n7_d3_1",
]


@pytest.mark.parametrize("scan_dir", scan_dirs)
def test_separate_auto_directory_with_various_images(scan_dir):
    os.environ["APP_ENV"] = "dev"
    os.chdir(HERE.parent)
    importlib.reload(config_rdr)
    from providers.ImageList import ImageList
    from providers.ML_multiple_classifier import classify_all_images_from
    from providers.ML_multiple_separator import (
        separate_all_images_from,
        show_separations_in_images,
    )

    subsample_dir = base_dir / scan_dir

    all_jpgs = sorted([a_path.name for a_path in subsample_dir.glob("*_1_*.jpg")])
    all_grey_jpgs = [e for e in all_jpgs if "_color_" not in e]
    # all_grey_jpgs = [e for e in all_grey_jpgs if "_136" in e]  # dans d2_1_sur_4_1
    # all_grey_jpgs = [e for e in all_grey_jpgs if "_84.jpg" in e]  # dans n7_d3_1
    # all_grey_jpgs = [e for e in all_grey_jpgs if "_450.jpg" in e]  # dans n7_d3_1
    quite_large = "n7_d1_2_sur_2_1_5.jpgXXXX"
    very_large_jpgs = [
        e for e in all_grey_jpgs if quite_large in e
    ]  # Largest images, fails on my GPU
    all_grey_jpgs = very_large_jpgs + [e for e in all_grey_jpgs if quite_large not in e]
    maybe_multiples, error = classify_all_images_from(
        logger, subsample_dir, 0.4, image_list=all_grey_jpgs
    )
    to_sep = [mm.name for mm in maybe_multiples]
    a_chunk = ImageList(subsample_dir, to_sep)
    results, error = separate_all_images_from(logger, a_chunk)
    assert error is None, error
    assert results is not None  # mypy
    show_separations_in_images(subsample_dir, results, out_dir)
