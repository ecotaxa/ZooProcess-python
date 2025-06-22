from pathlib import Path


def generate_separator_gif(
    src_image_dir: Path, template_img_path: Path, dst_path: Path
):
    # Sanity checks
    if not src_image_dir.is_dir():
        raise ValueError(
            f"Source image directory does not exist or is not a directory: {src_image_dir}"
        )

    if not template_img_path.exists():
        raise ValueError(f"Template image does not exist: {template_img_path}")

    pass
