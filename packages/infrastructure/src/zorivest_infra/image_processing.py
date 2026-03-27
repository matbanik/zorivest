# packages/infrastructure/src/zorivest_infra/image_processing.py
"""Image processing pipeline — validate, standardize, thumbnail.

Source: image-architecture.md §image-processing

Responsibilities:
- Validate images by magic bytes (PNG, JPEG, GIF, WebP)
- Enforce 10MB size limit
- Convert any supported image to WebP (quality=85)
- Generate WebP thumbnails (200×200 max, LANCZOS, quality=80)
- Preserve alpha channels for transparent images
"""

from __future__ import annotations

import io

from PIL import Image

# Supported formats: magic-byte prefix → MIME type
_MAGIC_MAP: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),  # PNG
    (b"\xff\xd8\xff", "image/jpeg"),  # JPEG
    (b"GIF87a", "image/gif"),  # GIF87a
    (b"GIF89a", "image/gif"),  # GIF89a
    (b"RIFF", "image/webp"),  # WebP (RIFF container)
]

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
THUMBNAIL_MAX = 200  # px
WEBP_QUALITY = 85
THUMBNAIL_QUALITY = 80


def validate_image(data: bytes) -> tuple[str, int, int]:
    """Validate image data and extract metadata.

    Checks magic bytes for supported formats (PNG, JPEG, GIF, WebP)
    and enforces the 10MB size limit.

    Args:
        data: Raw image bytes.

    Returns:
        Tuple of (mime_type, width, height).

    Raises:
        ValueError: If the image exceeds 10MB or has an unsupported format.
    """
    if len(data) > MAX_IMAGE_SIZE:
        raise ValueError(f"Image size {len(data)} bytes exceeds 10 MB limit")

    mime = _detect_mime(data)
    if mime is None:
        raise ValueError("Unsupported image format")

    # WebP needs special handling: verify RIFF+WEBP container
    if data[:4] == b"RIFF" and (len(data) < 12 or data[8:12] != b"WEBP"):
        raise ValueError("Unsupported image format")

    try:
        img = Image.open(io.BytesIO(data))
        img.verify()  # Verify it's actually a valid image
        # Re-open after verify (verify can invalidate state)
        img = Image.open(io.BytesIO(data))
        width, height = img.size
    except Exception as e:
        raise ValueError(f"Invalid image data: {e}") from e

    return mime, width, height


def standardize_to_webp(data: bytes) -> bytes:
    """Convert image to WebP format (quality=85).

    - Preserves alpha channel for RGBA images
    - Converts palette (P) and other modes to RGB/RGBA

    Args:
        data: Raw image bytes (PNG, JPEG, GIF, or WebP).

    Returns:
        WebP-encoded image bytes.
    """
    img = Image.open(io.BytesIO(data))

    # Handle mode conversion
    if (
        img.mode == "RGBA"
        or (img.mode == "PA")
        or (img.mode == "P" and "transparency" in img.info)
    ):
        img = img.convert("RGBA")
    elif img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=WEBP_QUALITY)
    return buf.getvalue()


def generate_thumbnail(data: bytes) -> bytes:
    """Generate a WebP thumbnail capped at 200×200, preserving aspect ratio.

    Uses LANCZOS resampling and quality=80.

    Args:
        data: Raw image bytes.

    Returns:
        WebP-encoded thumbnail bytes.
    """
    img = Image.open(io.BytesIO(data))

    # Convert mode if needed
    if img.mode not in ("RGB", "RGBA"):
        if "transparency" in img.info or img.mode == "PA":
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

    # thumbnail() modifies in-place, respects aspect ratio, never upscales
    img.thumbnail((THUMBNAIL_MAX, THUMBNAIL_MAX), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=THUMBNAIL_QUALITY)
    return buf.getvalue()


def _detect_mime(data: bytes) -> str | None:
    """Detect MIME type by magic bytes.

    Returns:
        MIME type string or None if unrecognized.
    """
    for magic, mime in _MAGIC_MAP:
        if data[: len(magic)] == magic:
            return mime
    return None
