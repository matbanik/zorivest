# tests/unit/test_image_processing.py
"""Unit tests for image processing pipeline (MEU-22).

AC-22.1: validate_image accepts PNG/JPEG/GIF/WebP by magic bytes, returns (mime, width, height)
AC-22.2: validate_image raises ValueError for images > 10MB
AC-22.3: validate_image raises ValueError for unsupported formats
AC-22.4: standardize_to_webp converts to WebP quality=85
AC-22.5: standardize_to_webp preserves alpha (transparency)
AC-22.6: standardize_to_webp converts non-RGB/RGBA to RGB
AC-22.7: generate_thumbnail creates WebP ≤200×200 preserving aspect
AC-22.8: generate_thumbnail uses LANCZOS, quality=80
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from zorivest_infra.image_processing import (
    generate_thumbnail,
    standardize_to_webp,
    validate_image,
)

MAX_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Test Helpers ─────────────────────────────────────────────────────────


def _make_image(
    fmt: str = "PNG",
    width: int = 100,
    height: int = 80,
    mode: str = "RGB",
) -> bytes:
    """Create an in-memory image in the given format."""
    img = Image.new(mode, (width, height), color=(128, 64, 32))
    buf = io.BytesIO()
    save_kwargs: dict = {}
    if fmt.upper() == "GIF":
        # GIF doesn't support RGBA, convert if needed
        if mode == "RGBA":
            img = img.convert("P")
    if fmt.upper() == "WEBP":
        save_kwargs["quality"] = 85
    img.save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()


def _make_rgba_png(width: int = 100, height: int = 80) -> bytes:
    """Create a PNG with an alpha channel."""
    img = Image.new("RGBA", (width, height), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_palette_image() -> bytes:
    """Create a palette (P) mode image."""
    img = Image.new("P", (100, 80))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── AC-22.1: validate_image —accept valid formats ────────────────────────


class TestValidateImage:
    """Tests for validate_image()."""

    def test_accept_png(self) -> None:
        """AC-22.1: PNG accepted by magic bytes."""
        data = _make_image("PNG", 200, 150)
        mime, w, h = validate_image(data)
        assert mime == "image/png"
        assert w == 200
        assert h == 150

    def test_accept_jpeg(self) -> None:
        """AC-22.1: JPEG accepted by magic bytes."""
        data = _make_image("JPEG", 300, 200)
        mime, w, h = validate_image(data)
        assert mime == "image/jpeg"
        assert w == 300
        assert h == 200

    def test_accept_gif(self) -> None:
        """AC-22.1: GIF accepted by magic bytes."""
        data = _make_image("GIF", 64, 64)
        mime, w, h = validate_image(data)
        assert mime == "image/gif"
        assert w == 64
        assert h == 64

    def test_accept_webp(self) -> None:
        """AC-22.1: WebP accepted by magic bytes."""
        data = _make_image("WEBP", 400, 300)
        mime, w, h = validate_image(data)
        assert mime == "image/webp"
        assert w == 400
        assert h == 300

    def test_size_limit_exceeded(self) -> None:
        """AC-22.2: Raises ValueError for images > 10MB."""
        # Create a minimal valid PNG header, then pad to exceed 10MB
        data = _make_image("PNG", 100, 100)
        oversized = data + b"\x00" * (MAX_SIZE + 1 - len(data))
        with pytest.raises(ValueError, match="10.*MB|size"):
            validate_image(oversized)

    def test_unsupported_format(self) -> None:
        """AC-22.3: Raises ValueError for unsupported formats."""
        data = b"RIFF\x00\x00\x00\x00AVI "  # AVI-like header
        with pytest.raises(ValueError):
            validate_image(data)

    def test_invalid_data(self) -> None:
        """AC-22.3: Raises ValueError for completely invalid data."""
        with pytest.raises(ValueError):
            validate_image(b"not an image at all")


# ── AC-22.4/22.5/22.6: standardize_to_webp ──────────────────────────────


class TestStandardizeToWebp:
    """Tests for standardize_to_webp()."""

    def test_png_to_webp(self) -> None:
        """AC-22.4: PNG → WebP conversion."""
        data = _make_image("PNG", 200, 150)
        result = standardize_to_webp(data)
        # Verify output is WebP
        img = Image.open(io.BytesIO(result))
        assert img.format == "WEBP"
        assert img.size == (200, 150)

    def test_jpeg_to_webp(self) -> None:
        """AC-22.4: JPEG → WebP conversion."""
        data = _make_image("JPEG", 300, 200)
        result = standardize_to_webp(data)
        img = Image.open(io.BytesIO(result))
        assert img.format == "WEBP"

    def test_preserves_alpha(self) -> None:
        """AC-22.5: Alpha channel preserved."""
        data = _make_rgba_png()
        result = standardize_to_webp(data)
        img = Image.open(io.BytesIO(result))
        assert img.mode == "RGBA"

    def test_converts_palette_to_rgb(self) -> None:
        """AC-22.6: Palette (P) mode → RGB before WebP."""
        data = _make_palette_image()
        result = standardize_to_webp(data)
        img = Image.open(io.BytesIO(result))
        assert img.mode in ("RGB", "RGBA")

    def test_webp_passthrough(self) -> None:
        """AC-22.4: WebP → WebP re-encoded."""
        data = _make_image("WEBP", 100, 100)
        result = standardize_to_webp(data)
        img = Image.open(io.BytesIO(result))
        assert img.format == "WEBP"


# ── AC-22.7/22.8: generate_thumbnail ────────────────────────────────────


class TestGenerateThumbnail:
    """Tests for generate_thumbnail()."""

    def test_thumbnail_within_bounds(self) -> None:
        """AC-22.7: Thumbnail ≤ 200×200."""
        data = _make_image("PNG", 800, 600)
        result = generate_thumbnail(data)
        img = Image.open(io.BytesIO(result))
        assert img.width <= 200
        assert img.height <= 200

    def test_thumbnail_preserves_aspect(self) -> None:
        """AC-22.7: Aspect ratio preserved (800×600 → 200×150)."""
        data = _make_image("PNG", 800, 600)
        result = generate_thumbnail(data)
        img = Image.open(io.BytesIO(result))
        ratio = img.width / img.height
        assert abs(ratio - (800 / 600)) < 0.05  # Within 5% tolerance

    def test_thumbnail_is_webp(self) -> None:
        """AC-22.7: Thumbnail output is WebP format."""
        data = _make_image("PNG", 400, 300)
        result = generate_thumbnail(data)
        img = Image.open(io.BytesIO(result))
        assert img.format == "WEBP"

    def test_thumbnail_small_image(self) -> None:
        """AC-22.7: Image smaller than 200×200 stays at original size."""
        data = _make_image("PNG", 50, 40)
        result = generate_thumbnail(data)
        img = Image.open(io.BytesIO(result))
        assert img.width == 50
        assert img.height == 40
