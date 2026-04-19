# tests/unit/test_structlog_utf8.py
"""Tests for MEU-PW4: Structlog UTF-8 configuration and bytes-safe JSON.

Covers:
- AC-1: configure_structlog_utf8() configures structlog with UnicodeDecoder,
         TimeStamper, and PrintLoggerFactory using UTF-8 TextIOWrapper
- AC-2: sys.stderr is reconfigured with encoding="utf-8", errors="replace"
- AC-4: _safe_json_output() serializes bytes and datetime safely
- AC-5: _persist_step() uses _safe_json_output() instead of raw json.dumps
- AC-6: Structlog output is JSON when stderr is not a TTY, ConsoleRenderer when it is

Source: 09b-pipeline-hardening.md §9B.2
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
import structlog

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_structlog():
    """Reset structlog configuration between tests."""
    yield
    # Reset structlog to defaults so each test starts clean
    structlog.reset_defaults()


# ── AC-1: configure_structlog_utf8() configures structlog properly ──────


class TestConfigureStructlogUtf8:
    """AC-1: structlog is configured with UnicodeDecoder, TimeStamper,
    and PrintLoggerFactory using UTF-8 TextIOWrapper on stderr."""

    def test_function_exists_and_is_callable(self) -> None:
        """configure_structlog_utf8() must exist and be callable."""
        from zorivest_api.logging_config import configure_structlog_utf8

        assert callable(configure_structlog_utf8)

    def test_configures_structlog_processors(self) -> None:
        """After calling configure_structlog_utf8(), structlog config
        must include UnicodeDecoder and TimeStamper processors."""
        from zorivest_api.logging_config import configure_structlog_utf8

        configure_structlog_utf8()

        config = structlog.get_config()
        processor_types = [type(p) for p in config["processors"]]

        assert structlog.processors.UnicodeDecoder in processor_types
        assert structlog.processors.TimeStamper in processor_types

    def test_logger_factory_is_print_logger(self) -> None:
        """Logger factory must be PrintLoggerFactory."""
        from zorivest_api.logging_config import configure_structlog_utf8

        configure_structlog_utf8()

        config = structlog.get_config()
        assert isinstance(config["logger_factory"], structlog.PrintLoggerFactory)

    def test_logger_factory_uses_utf8_stream(self) -> None:
        """PrintLoggerFactory file must have UTF-8 encoding.

        After reconfigure(), sys.stderr is the UTF-8 stream passed directly
        to PrintLoggerFactory (no separate TextIOWrapper needed).
        """
        from zorivest_api.logging_config import configure_structlog_utf8

        configure_structlog_utf8()

        config = structlog.get_config()
        factory = config["logger_factory"]
        file_obj = factory._file  # type: ignore[attr-defined]
        assert hasattr(file_obj, "encoding")
        assert file_obj.encoding.lower().replace("-", "") == "utf8"


# ── AC-2: sys.stderr is reconfigured with UTF-8 ────────────────────────


class TestStderrReconfiguration:
    """AC-2: sys.stderr is reconfigured with encoding='utf-8', errors='replace'
    if .reconfigure() is available."""

    def test_stderr_reconfigure_called(self) -> None:
        """If sys.stderr has .reconfigure(), it must be called with
        encoding='utf-8' and errors='replace'."""
        from zorivest_api.logging_config import configure_structlog_utf8

        mock_stderr = MagicMock(spec=sys.stderr)
        mock_stderr.isatty.return_value = False
        mock_stderr.buffer = sys.stderr.buffer
        mock_stderr.reconfigure = MagicMock()

        with patch.object(sys, "stderr", mock_stderr):
            configure_structlog_utf8()

        mock_stderr.reconfigure.assert_called_once_with(
            encoding="utf-8", errors="replace"
        )

    def test_non_ascii_logging_does_not_crash(self) -> None:
        """Logging non-ASCII characters must not raise UnicodeEncodeError."""
        from zorivest_api.logging_config import configure_structlog_utf8

        configure_structlog_utf8()

        # This must not raise — verifies the charmap fix
        log = structlog.get_logger()
        log.info("test_unicode", msg="Résumé: ñ, ü, ™, 日本語, 🎉")


# ── AC-6: JSON vs ConsoleRenderer depending on TTY ─────────────────────


class TestTtyAwareRenderer:
    """AC-6: Structlog output is JSON when stderr is not a TTY,
    and ConsoleRenderer when it is."""

    def test_non_tty_uses_json_renderer(self) -> None:
        """When stderr is not a TTY, the last processor should be JSONRenderer."""
        from zorivest_api.logging_config import configure_structlog_utf8

        mock_stderr = MagicMock(spec=sys.stderr)
        mock_stderr.isatty.return_value = False
        mock_stderr.buffer = sys.stderr.buffer

        with patch.object(sys, "stderr", mock_stderr):
            configure_structlog_utf8()

        config = structlog.get_config()
        last_processor = config["processors"][-1]
        assert isinstance(last_processor, structlog.processors.JSONRenderer)

    def test_tty_uses_console_renderer(self) -> None:
        """When stderr is a TTY, the last processor should be ConsoleRenderer."""
        from zorivest_api.logging_config import configure_structlog_utf8

        mock_stderr = MagicMock(spec=sys.stderr)
        mock_stderr.isatty.return_value = True
        mock_stderr.buffer = sys.stderr.buffer

        with patch.object(sys, "stderr", mock_stderr):
            configure_structlog_utf8()

        config = structlog.get_config()
        last_processor = config["processors"][-1]
        assert isinstance(last_processor, structlog.dev.ConsoleRenderer)


# ── AC-4: _safe_json_output() handles bytes and datetime ───────────────


class TestSafeJsonOutput:
    """AC-4: _safe_json_output() serializes bytes via decode('utf-8', errors='replace')
    and datetime via .isoformat()."""

    def test_none_output_returns_none(self) -> None:
        """Empty or None output returns None."""
        from zorivest_core.services.pipeline_runner import _safe_json_output

        assert _safe_json_output({}) is None
        assert _safe_json_output(None) is None  # type: ignore[arg-type]

    def test_bytes_values_decoded(self) -> None:
        """bytes values are decoded to UTF-8 strings with replacement."""
        from zorivest_core.services.pipeline_runner import _safe_json_output

        output = {"data": b"Hello \xff World"}
        result = _safe_json_output(output)
        assert result is not None
        parsed = json.loads(result)
        assert "Hello" in parsed["data"]
        # \xff should be replaced, not crash
        assert isinstance(parsed["data"], str)

    def test_datetime_values_isoformat(self) -> None:
        """datetime values are serialized via .isoformat()."""
        from zorivest_core.services.pipeline_runner import _safe_json_output

        dt = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
        output = {"timestamp": dt}
        result = _safe_json_output(output)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["timestamp"] == "2026-04-19T12:00:00+00:00"

    def test_normal_dict_serialized(self) -> None:
        """Normal dict output is serialized correctly."""
        from zorivest_core.services.pipeline_runner import _safe_json_output

        output = {"result": "ok", "count": 42}
        result = _safe_json_output(output)
        assert result is not None
        parsed = json.loads(result)
        assert parsed == {"result": "ok", "count": 42}

    def test_unsupported_type_raises_typeerror(self) -> None:
        """Types other than bytes/datetime raise TypeError."""
        from zorivest_core.services.pipeline_runner import _safe_json_output

        output = {"obj": object()}
        with pytest.raises(TypeError, match="not JSON serializable"):
            _safe_json_output(output)


# ── AC-5: _persist_step() uses _safe_json_output() ────────────────────


class TestPersistStepUsesSafeJson:
    """AC-5: _persist_step() must use _safe_json_output() instead of
    raw json.dumps(result.output), so bytes in output don't crash."""

    def test_persist_step_handles_bytes_output(self) -> None:
        """A step result with bytes in output must not crash _persist_step()."""
        import asyncio
        from zorivest_core.services.pipeline_runner import PipelineRunner
        from zorivest_core.services.ref_resolver import RefResolver
        from zorivest_core.services.condition_evaluator import ConditionEvaluator
        from zorivest_core.domain.pipeline import PolicyStep, StepResult
        from zorivest_core.domain.enums import PipelineStatus, StepErrorMode

        # Create a runner with a mock UoW that has a mock session
        mock_session = MagicMock()
        mock_uow = MagicMock()
        mock_uow._session = mock_session

        runner = PipelineRunner(
            uow=mock_uow,
            ref_resolver=RefResolver(),
            condition_evaluator=ConditionEvaluator(),
        )

        step_def = PolicyStep(
            id="test_step",
            type="fetch",
            params={},
            on_error=StepErrorMode.FAIL_PIPELINE,
        )

        # StepResult with bytes in output — this must NOT crash
        result_with_bytes = StepResult(
            status=PipelineStatus.SUCCESS,
            output={"response_body": b"binary data \xff\xfe"},
        )

        # This should not raise TypeError
        asyncio.run(
            runner._persist_step("run-123", step_def, result_with_bytes, attempt=1)
        )

        # Verify session.add was called (step was persisted)
        assert mock_session.add.called
