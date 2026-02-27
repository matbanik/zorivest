# Image Storage & Display Architecture

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) — Referenced by [Phase 2](02-infrastructure.md), [Phase 5](05-mcp-server.md), [Phase 6](06-gui.md) ([Trades](06b-gui-trades.md))

---

## Design Decision: Store Images in the Encrypted Database

**Why in-database (BLOB) rather than filesystem?**

| Factor | BLOB in DB | Files on disk |
|--------|-----------|---------------|
| **Encryption** | Automatic (SQLCipher encrypts everything) | Must encrypt each file separately |
| **Backup** | Single file backup includes images | Must backup DB + image directory |
| **Integrity** | Foreign keys ensure trade↔image consistency | Orphaned files possible |
| **Portability** | Move one `.db` file | Move DB + image folder |
| **Transaction safety** | Image save + trade update are atomic | Not atomic |
| **Performance for screenshots** | Good for <5MB images (typical screenshots) | Better for >10MB files |

**Screenshots are typically 100KB–2MB (PNG) or 30KB–500KB (JPEG)**, well within SQLite's comfort zone. SQLite handles BLOBs up to 1GB, and SQLCipher adds negligible overhead for these sizes.

**All images are standardized to WebP on ingestion**, which typically reduces PNG screenshot sizes by ~30% and JPEG by ~20%, further improving database storage efficiency.

## Image Processing Pipeline

```
User Action                  Processing                    Storage
─────────────                ──────────                    ───────
                             
[Paste from clipboard] ──►  Read QImage from clipboard
        or                           │
[Open file dialog]     ──►  Read file bytes
        or                           │
[MCP: base64 input]   ──►  Decode base64
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Validate image   │
                            │ • Check magic    │
                            │   bytes (PNG/JPG│
                            │   /GIF/WebP)    │
                            │ • Check size     │
                            │   (<10MB limit)  │
                            │ • Extract dims   │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Standardize      │
                            │ • Convert to     │
                            │   WebP format    │
                            │ • Pillow save    │
                            │ • quality=85     │
                            │ • Preserve alpha │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Generate thumb   │
                            │ • Pillow resize  │
                            │ • max 200×200    │
                            │ • Keep aspect    │
                            │ • Save as WebP   │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Store in DB      │
                            │ • data (WebP)    │
                            │ • thumbnail      │
                            │ • mime_type      │
                            │   (image/webp)   │
                            │ • width, height  │
                            │ • file_size      │
                            │ • caption        │
                            │ • owner_type     │
                            │ • owner_id (FK)  │
                            └─────────────────┘
```

## WebP Standardization

All imported images (PNG, JPEG, GIF, WebP) are converted to WebP before storage. This ensures a single consistent format in the database and reduces BLOB sizes.

**Why WebP over AVIF or JPEG XL?**

| Factor | WebP | AVIF | JPEG XL |
|--------|------|------|---------|
| **Compression vs JPEG** | ~30% smaller | ~50% smaller | ~35-60% smaller |
| **Chromium/Electron support** | ✅ Universal since 2012 | ✅ Since Chrome 100 | ⚠️ Re-added Jan 2026, not stable in Electron |
| **Pillow support** | ✅ Native (read + write) | ✅ Native as of 11.2+ | ❌ Requires third-party plugin |
| **Encoding speed** | Fast | Slow (AV1 codec) | Moderate |
| **Max dimensions** | 16384×16384 | Unlimited | Unlimited |

WebP wins for Zorivest because screenshots are small (<5MB), encoding speed matters for interactive paste/upload, and Pillow handles it natively with no extra dependencies.

### MIME Normalization Contract

After `standardize_to_webp()`, the persisted `mime_type` is **always** `"image/webp"`. The client-supplied MIME type (from upload `Content-Type` or MCP `mime_type` parameter) is advisory — used only for input validation logging. The service layer overwrites the MIME type unconditionally after WebP conversion. This prevents content-type/data mismatches at the REST response layer (`GET /images/{id}/full` serves `img.mime_type`).

```python
# packages/infrastructure/src/zorivest_infra/image_processing.py

from PIL import Image
import io


def standardize_to_webp(image_data: bytes, quality: int = 85) -> bytes:
    """Convert any supported image format to WebP.
    
    Args:
        image_data: Raw PNG/JPEG/GIF/WebP bytes
        quality: WebP quality (0-100, default 85)
    
    Returns:
        WebP bytes of the standardized image
    """
    img = Image.open(io.BytesIO(image_data))
    
    # Preserve transparency if present, otherwise convert to RGB
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if img.has_transparency_data else "RGB")
    
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=quality, method=4)
    return buffer.getvalue()


def generate_thumbnail(image_data: bytes, max_size: int = 200) -> bytes:
    """Generate a thumbnail from raw image bytes.
    
    Args:
        image_data: Raw image bytes (any supported format)
        max_size: Maximum dimension (width or height)
    
    Returns:
        WebP bytes of the thumbnail
    """
    img = Image.open(io.BytesIO(image_data))
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=80)
    return buffer.getvalue()


def validate_image(data: bytes) -> tuple[str, int, int]:
    """Validate image data and return (mime_type, width, height).
    
    Raises ValueError if not a valid image or exceeds size limit.
    Returns the *original* mime_type for logging/auditing — the image
    will be standardized to WebP after validation.
    """
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    if len(data) > MAX_IMAGE_SIZE:
        raise ValueError(f"Image exceeds {MAX_IMAGE_SIZE // (1024*1024)}MB limit ({len(data)} bytes)")

    MAGIC_BYTES = {
        b"\x89PNG": "image/png",
        b"\xff\xd8\xff": "image/jpeg",
        b"GIF87a": "image/gif",
        b"GIF89a": "image/gif",
    }
    
    # Check standard magic bytes
    for magic, mime in MAGIC_BYTES.items():
        if data[:len(magic)] == magic:
            img = Image.open(io.BytesIO(data))
            return mime, img.width, img.height
    
    # WebP: RIFF header + WEBP at bytes 8-12
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        img = Image.open(io.BytesIO(data))
        return "image/webp", img.width, img.height
    
    raise ValueError("Unsupported image format. Supported: PNG, JPEG, GIF, WebP")
```
