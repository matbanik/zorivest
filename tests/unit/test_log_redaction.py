"""Tests for log redaction utilities — MEU-62.

FIC-62 acceptance criteria (log redaction portion):
AC-5: mask_api_key always returns "[REDACTED]"
AC-6: sanitize_url_for_logging replaces all occurrences of the key
AC-7: sanitize_url_for_logging with empty or short key returns unchanged
"""

from __future__ import annotations

import pytest

from zorivest_infra.security.log_redaction import (
    mask_api_key,
    sanitize_url_for_logging,
)


class TestMaskApiKeyAC5:
    """AC-5: mask_api_key always returns '[REDACTED]'."""

    def test_masks_normal_key(self) -> None:
        assert mask_api_key("abc123xyz") == "[REDACTED]"

    def test_masks_empty_string(self) -> None:
        assert mask_api_key("") == "[REDACTED]"

    def test_masks_long_key(self) -> None:
        assert mask_api_key("a" * 100) == "[REDACTED]"

    def test_masks_short_key(self) -> None:
        assert mask_api_key("x") == "[REDACTED]"


class TestSanitizeUrlAC6:
    """AC-6: sanitize_url_for_logging replaces all occurrences of the key."""

    def test_replaces_key_in_url(self) -> None:
        url = "https://api.example.com/data?apikey=MYKEY123"
        result = sanitize_url_for_logging(url, "MYKEY123")
        assert "MYKEY123" not in result
        assert "[REDACTED]" in result

    def test_replaces_multiple_occurrences(self) -> None:
        text = "key=MYKEY123&verify=MYKEY123"
        result = sanitize_url_for_logging(text, "MYKEY123")
        assert result.count("[REDACTED]") == 2
        assert "MYKEY123" not in result

    def test_preserves_surrounding_text(self) -> None:
        url = "https://api.example.com/data?apikey=SECRET&symbol=AAPL"
        result = sanitize_url_for_logging(url, "SECRET")
        assert result == "https://api.example.com/data?apikey=[REDACTED]&symbol=AAPL"


class TestSanitizeUrlShortKeyAC7:
    """AC-7: sanitize_url_for_logging with empty or short key returns unchanged."""

    def test_empty_key_returns_unchanged(self) -> None:
        text = "https://api.example.com/data?key=abc"
        assert sanitize_url_for_logging(text, "") == text

    def test_short_key_4_chars_returns_unchanged(self) -> None:
        text = "https://api.example.com/data?key=abcd"
        assert sanitize_url_for_logging(text, "abcd") == text

    def test_short_key_3_chars_returns_unchanged(self) -> None:
        text = "https://api.example.com/data?key=abc"
        assert sanitize_url_for_logging(text, "abc") == text

    def test_short_key_1_char_returns_unchanged(self) -> None:
        text = "https://api.example.com/data?key=a"
        assert sanitize_url_for_logging(text, "a") == text

    @pytest.mark.parametrize("key", ["12345", "abcde"])
    def test_5_char_key_does_replace(self, key: str) -> None:
        """Keys with 5+ chars should be sanitized."""
        text = f"url?key={key}"
        result = sanitize_url_for_logging(text, key)
        assert key not in result
        assert "[REDACTED]" in result
