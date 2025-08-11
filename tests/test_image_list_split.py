import sys
from pathlib import Path

from providers.ImageList import ImageList


def test_image_list_split():
    """
    Test the split method of the ImageList class.
    """
    # Create a temporary directory for testing
    test_dir = Path("test_dir")
    test_dir.mkdir(exist_ok=True)

    # Create some dummy image paths (we won't actually create the files)
    dummy_images = []
    for i in range(20):
        dummy_path = f"image_{i}.png"
        dummy_images.append(dummy_path)

    # Create an ImageList instance with the dummy images
    image_list = ImageList(test_dir, images=dummy_images)

    # Test splitting with different sizes
    test_sizes = [3, 5, 7, 10, 20, 30]

    for size in test_sizes:
        print(f"\nTesting split with size {size}:")
        sublists = list(image_list.split(size))

        # Check the number of sublists
        expected_num_sublists = (
            len(dummy_images) + size - 1
        ) // size  # Ceiling division
        assert (
            len(sublists) == expected_num_sublists
        ), f"Expected {expected_num_sublists} sublists, got {len(sublists)}"
        print(f"  Number of sublists: {len(sublists)} (correct)")

        # Check the size of each sublist
        for i, sublist in enumerate(sublists):
            expected_size = min(size, len(dummy_images) - i * size)
            assert (
                sublist.count() == expected_size
            ), f"Sublist {i} has {sublist.count()} images, expected {expected_size}"
            print(f"  Sublist {i} size: {sublist.count()} (correct)")

            # Check that the images in the sublist are correct
            start_idx = i * size
            end_idx = min(start_idx + size, len(dummy_images))
            expected_images = dummy_images[start_idx:end_idx]
            assert (
                sublist.get_images() == expected_images
            ), f"Sublist {i} has incorrect images"
            print(f"  Sublist {i} images: correct")

    # Test with invalid size
    try:
        list(image_list.split(0))
        assert False, "Expected ValueError for size=0"
    except ValueError:
        print("\nCorrectly raised ValueError for size=0")

    try:
        list(image_list.split(-5))
        assert False, "Expected ValueError for size=-5"
    except ValueError:
        print("Correctly raised ValueError for size=-5")

    # Clean up
    test_dir.rmdir()
    print("\nAll tests passed!")


if __name__ == "__main__":
    test_image_list_split()
