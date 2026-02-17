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
                            │   bytes (PNG/JPG)│
                            │ • Check size     │
                            │   (<10MB limit)  │
                            │ • Extract dims   │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Generate thumb   │
                            │ • Pillow resize  │
                            │ • max 200×200    │
                            │ • Keep aspect    │
                            │ • Save as PNG    │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Store in DB      │
                            │ • data (original)│
                            │ • thumbnail      │
                            │ • mime_type      │
                            │ • width, height  │
                            │ • file_size      │
                            │ • caption        │
                            │ • owner_type     │
                            │ • owner_id (FK)  │
                            └─────────────────┘
```

## Thumbnail Generation (Using Pillow)

```python
# packages/infrastructure/src/zorivest_infra/image_processing.py

from PIL import Image
import io

def generate_thumbnail(image_data: bytes, max_size: int = 200) -> bytes:
    """Generate a thumbnail from raw image bytes.
    
    Args:
        image_data: Raw PNG/JPEG bytes
        max_size: Maximum dimension (width or height)
    
    Returns:
        PNG bytes of the thumbnail
    """
    img = Image.open(io.BytesIO(image_data))
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def validate_image(data: bytes) -> tuple[str, int, int]:
    """Validate image data and return (mime_type, width, height).
    
    Raises ValueError if not a valid image or exceeds size limit.
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
