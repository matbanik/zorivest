"""Tests for JsonFormatter — MEU-2A (AC-5 through AC-10)."""

from __future__ import annotations

import json
import logging




from zorivest_infra.logging.formatters import JsonFormatter


def _make_record(
    name: str = "zorivest.trades",
    level: int = logging.INFO,
    msg: str = "test message",
    exc_info: tuple | None = None,
    **extras: object,
) -> logging.LogRecord:
    """Create a LogRecord with optional extras."""
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="test_file.py",
        lineno=42,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    for k, v in extras.items():
        setattr(record, k, v)
    return record


class TestJsonFormatter:
    """AC-5 through AC-10: JSONL output format."""

    def setup_method(self) -> None:
        self.formatter = JsonFormatter()

    def test_output_is_valid_json(self) -> None:
        """AC-5: format() returns valid JSON string (parseable by json.loads)."""
        record = _make_record()
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)
        # Value: verify it contains the message we logged
        assert parsed["message"] == "test message"

    def test_output_is_single_line(self) -> None:
        """AC-5 continued: output is a single line (JSONL compatible)."""
        record = _make_record()
        output = self.formatter.format(record)
        assert "\n" not in output
        # Value: verify length is reasonable (not empty or trivially small)
        assert len(output) > 50

    def test_contains_all_standard_fields(self) -> None:
        """AC-6: Output JSON contains all 8 standard fields."""
        record = _make_record()
        output = self.formatter.format(record)
        parsed = json.loads(output)
        required_fields = {
            "timestamp", "level", "logger", "thread",
            "module", "funcName", "lineno", "message",
        }
        assert required_fields.issubset(parsed.keys())

    def test_non_reserved_extras_included(self) -> None:
        """AC-7: Non-reserved extras (e.g., record.trade_id) appear in output."""
        record = _make_record(trade_id="TRD-001", portfolio="growth")
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert parsed["trade_id"] == "TRD-001"
        assert parsed["portfolio"] == "growth"

    def test_reserved_attrs_excluded(self) -> None:
        """AC-8: Reserved attrs and underscore-prefixed attrs excluded."""
        record = _make_record()
        output = self.formatter.format(record)
        parsed = json.loads(output)
        # Reserved attrs that should NOT appear as top-level keys
        for reserved_key in ("msg", "args", "created", "exc_info", "pathname"):
            assert reserved_key not in parsed
        # Value: verify that standard fields ARE present
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed

    def test_underscore_prefixed_excluded(self) -> None:
        """AC-8 continued: underscore-prefixed attrs excluded."""
        record = _make_record(_internal="hidden")
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert "_internal" not in parsed
        # Value: verify message still present (not over-filtered)
        assert parsed["message"] == "test message"

    def test_exception_info_serialized(self) -> None:
        """AC-9: Exception info serialized as exception.{type, message, traceback}."""
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = _make_record(exc_info=exc_info)
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert parsed["exception"]["message"] == "test error"
        assert isinstance(parsed["exception"]["traceback"], list)

    def test_no_exception_key_when_no_exception(self) -> None:
        """No exception key when exc_info is None."""
        record = _make_record()
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert "exception" not in parsed
        # Value: verify all 8 standard fields are still present
        assert len(parsed) >= 8

    def test_timestamp_is_utc_iso8601(self) -> None:
        """AC-10: Timestamp uses UTC timezone in ISO-8601 format."""
        record = _make_record()
        output = self.formatter.format(record)
        parsed = json.loads(output)
        timestamp = parsed["timestamp"]
        # ISO-8601 UTC timestamps end with +00:00 or Z
        assert "+00:00" in timestamp or timestamp.endswith("Z")
        # Value: verify timestamp has valid format (contains T separator)
        assert "T" in timestamp

    def test_level_is_string_name(self) -> None:
        """Level field uses string name (INFO, WARNING, etc.)."""
        record = _make_record(level=logging.WARNING)
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "WARNING"

    def test_message_uses_getMessage(self) -> None:
        """Message field uses record.getMessage() (formatted message)."""
        record = _make_record(msg="hello world")
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "hello world"
