from io import BytesIO
from PIL import Image, ImageDraw


# Global variable to cache the generated favicon
_cached_favicon = None


def create_plankton_favicon():
    """
    Creates a simple plankton-inspired favicon.
    Uses a cached version if available to avoid regenerating on every request.

    Returns:
        BytesIO: A BytesIO object containing the favicon image data.
    """
    global _cached_favicon

    # Return cached favicon if available
    if _cached_favicon is not None:
        # Create a new BytesIO object with the cached content
        # This ensures the position is reset to 0 for each request
        cached_copy = BytesIO(_cached_favicon.getvalue())
        cached_copy.seek(0)
        return cached_copy
    # Create a 32x32 transparent image
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a simple plankton-like shape (diatom)
    # Center circle
    draw.ellipse((8, 8, 24, 24), fill=(0, 128, 192, 255))

    # Spikes (like a diatom)
    draw.line((16, 0, 16, 8), fill=(0, 128, 192, 255), width=2)
    draw.line((16, 24, 16, 32), fill=(0, 128, 192, 255), width=2)
    draw.line((0, 16, 8, 16), fill=(0, 128, 192, 255), width=2)
    draw.line((24, 16, 32, 16), fill=(0, 128, 192, 255), width=2)

    # Diagonal spikes
    draw.line((4, 4, 10, 10), fill=(0, 128, 192, 255), width=2)
    draw.line((22, 10, 28, 4), fill=(0, 128, 192, 255), width=2)
    draw.line((4, 28, 10, 22), fill=(0, 128, 192, 255), width=2)
    draw.line((22, 22, 28, 28), fill=(0, 128, 192, 255), width=2)

    # Convert to bytes
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="ICO")
    img_byte_arr.seek(0)

    # Cache the favicon for future requests
    global _cached_favicon
    _cached_favicon = BytesIO(img_byte_arr.getvalue())
    _cached_favicon.seek(0)

    return img_byte_arr
