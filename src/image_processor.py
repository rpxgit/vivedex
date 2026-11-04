import io
from typing import Tuple
from PIL import Image, ImageOps

SUPPORTED_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB


class ImageValidationError(ValueError):
    """Raised when an uploaded image fails validation."""
    pass


def validate_image(image_bytes: bytes, mime_type: str) -> str:
    """
    Validate image file format, size, and integrity.
    
    Returns the normalized format string (JPEG, PNG, WEBP) if valid.
    Raises ImageValidationError if invalid.
    """
    if not image_bytes:
        raise ImageValidationError("Image file is empty.")

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ImageValidationError(
            f"Image size exceeds 8 MB limit. Current size: {len(image_bytes)} bytes."
        )

    norm_mime = mime_type.lower().strip()
    if norm_mime not in SUPPORTED_MIME_TYPES:
        raise ImageValidationError(
            f"Unsupported image type: '{mime_type}'. Supported types: JPG, JPEG, PNG, WebP."
        )

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
    except Exception as e:
        raise ImageValidationError(f"Invalid or corrupted image data: {str(e)}")

    return SUPPORTED_MIME_TYPES[norm_mime]


def preprocess_image(image_bytes: bytes) -> Tuple[bytes, str]:
    """
    Preprocess image:
    1. Corrects EXIF orientation so image pixels are right side up.
    2. Strips all EXIF/metadata.
    3. Keeps everything in memory (no disk saving).
    
    Returns:
        Tuple of (clean_bytes, mime_type)
    """
    with Image.open(io.BytesIO(image_bytes)) as img:
        img_format = img.format or "JPEG"
        
        # Transpose according to EXIF orientation then discard EXIF
        try:
            transposed = ImageOps.exif_transpose(img)
            if transposed is not None:
                img = transposed
        except Exception:
            pass

        # If RGBA and saving as JPEG, convert to RGB
        if img_format.upper() in ("JPEG", "JPG"):
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            save_format = "JPEG"
            out_mime = "image/jpeg"
        elif img_format.upper() == "PNG":
            save_format = "PNG"
            out_mime = "image/png"
        elif img_format.upper() == "WEBP":
            save_format = "WEBP"
            out_mime = "image/webp"
        else:
            save_format = "JPEG"
            out_mime = "image/jpeg"

        out_buffer = io.BytesIO()
        # Saving without passing exif parameter strips EXIF
        img.save(out_buffer, format=save_format)
        clean_bytes = out_buffer.getvalue()

    return clean_bytes, out_mime

