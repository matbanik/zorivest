"""API key log redaction utilities — MEU-62.

Functions for masking API keys in log output.
Source: docs/build-plan/08-market-data.md §8.2d.
"""

from __future__ import annotations

_MIN_KEY_LENGTH_FOR_REDACTION = 5


def mask_api_key(key: str) -> str:
    """Fully mask an API key for log display.

    Always returns ``"[REDACTED]"`` regardless of key content or length.

    Args:
        key: The API key to mask.

    Returns:
        ``"[REDACTED]"``
    """
    return "[REDACTED]"


def sanitize_url_for_logging(text: str, api_key: str) -> str:
    """Replace all occurrences of an API key in text with ``"[REDACTED]"``.

    Keys with 4 or fewer characters are considered too short to be
    meaningful API keys and are left unchanged to avoid false-positive
    replacements in URLs.

    Args:
        text: The text (typically a URL) to sanitize.
        api_key: The API key to replace.

    Returns:
        The sanitized text with keys replaced, or the original text
        if the key is empty or too short.
    """
    if not api_key or len(api_key) <= (_MIN_KEY_LENGTH_FOR_REDACTION - 1):
        return text
    return text.replace(api_key, "[REDACTED]")
