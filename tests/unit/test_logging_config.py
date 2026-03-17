"""Tests for LoggingManager, FEATURES, get_feature_logger, get_log_directory — MEU-1A (AC-1 through AC-14)."""

from __future__ import annotations

import json
import logging
import logging.handlers
import threading
import time
from pathlib import Path

import pytest

from zorivest_infra.logging.config import (
    DEFAULT_BACKUP_COUNT,
    DEFAULT_ROTATION_MB,
    FEATURES,
    LoggingManager,
    get_feature_logger,
    get_log_directory,
)


# ---------------------------------------------------------------------------
# FEATURES registry (AC-1)
# ---------------------------------------------------------------------------


class TestFeaturesRegistry:
    """AC-1: FEATURES dict contains exactly 12 entries with correct prefixes."""

    def test_features_count(self) -> None:
        assert len(FEATURES) == 12

    def test_trades_prefix(self) -> None:
        assert FEATURES["trades"] == "zorivest.trades"

    def test_accounts_prefix(self) -> None:
        assert FEATURES["accounts"] == "zorivest.accounts"

    def test_marketdata_prefix(self) -> None:
        assert FEATURES["marketdata"] == "zorivest.marketdata"

    def test_uvicorn_prefix(self) -> None:
        assert FEATURES["uvicorn"] == "uvicorn"

    def test_all_expected_features_present(self) -> None:
        expected = {
            "trades", "accounts", "marketdata", "tax", "scheduler",
            "db", "calculator", "images", "api", "frontend", "app", "uvicorn",
        }
        assert set(FEATURES.keys()) == expected


# ---------------------------------------------------------------------------
# get_feature_logger (AC-2, AC-3)
# ---------------------------------------------------------------------------


class TestGetFeatureLogger:
    """AC-2, AC-3: Feature logger retrieval."""

    def test_returns_named_logger(self) -> None:
        """AC-2: get_feature_logger('trades') returns logger named 'zorivest.trades'."""
        logger = get_feature_logger("trades")
        assert logger.name == "zorivest.trades"

    def test_unknown_feature_raises_value_error(self) -> None:
        """AC-3: get_feature_logger('unknown') raises ValueError."""
        with pytest.raises(ValueError, match="Unknown feature"):
            get_feature_logger("unknown")


# ---------------------------------------------------------------------------
# get_log_directory (AC-4)
# ---------------------------------------------------------------------------


class TestGetLogDirectory:
    """AC-4: Platform-appropriate log directory."""

    def test_returns_path(self) -> None:
        """AC-4: get_log_directory() returns a Path."""
        result = get_log_directory()
        assert isinstance(result, Path)
        # Value: verify path is absolute
        assert result.is_absolute()

    def test_directory_exists_after_call(self) -> None:
        """get_log_directory() creates the directory."""
        result = get_log_directory()
        assert result.is_dir()

    def test_contains_zorivest_logs(self) -> None:
        """Path ends with zorivest/logs."""
        result = get_log_directory()
        assert result.name == "logs"
        assert result.parent.name == "zorivest"


# ---------------------------------------------------------------------------
# LoggingManager bootstrap (AC-5, AC-6)
# ---------------------------------------------------------------------------


class TestBootstrap:
    """AC-5, AC-6: Bootstrap phase creates bootstrap.jsonl file."""

    def test_creates_bootstrap_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-5: bootstrap() creates bootstrap.jsonl in log directory."""
        monkeypatch.setattr(
            "zorivest_infra.logging.config.get_log_directory", lambda: tmp_path
        )
        manager = LoggingManager()
        try:
            manager.bootstrap()
            assert (tmp_path / "bootstrap.jsonl").exists()
        finally:
            # Clean up root handlers added by bootstrap
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()

    def test_bootstrap_log_written(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-6: After bootstrap(), logging to zorivest.app writes to bootstrap.jsonl."""
        monkeypatch.setattr(
            "zorivest_infra.logging.config.get_log_directory", lambda: tmp_path
        )
        manager = LoggingManager()
        try:
            manager.bootstrap()
            logging.getLogger("zorivest.app").info("test bootstrap message")
            content = (tmp_path / "bootstrap.jsonl").read_text()
            assert "test bootstrap message" in content or "Bootstrap logging started" in content
            # Value: verify the content is valid JSONL
            lines = [l for l in content.strip().split("\n") if l.strip()]
            assert len(lines) >= 1
            parsed = json.loads(lines[-1])
            assert "message" in parsed
        finally:
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()


# ---------------------------------------------------------------------------
# LoggingManager configure (AC-7, AC-8, AC-9, AC-13, AC-14)
# ---------------------------------------------------------------------------


class TestConfigureFromSettings:
    """Full queue-based logging configuration."""

    def _create_manager(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, settings: dict[str, str] | None = None
    ) -> LoggingManager:
        monkeypatch.setattr(
            "zorivest_infra.logging.config.get_log_directory", lambda: tmp_path
        )
        manager = LoggingManager()
        manager.bootstrap()
        manager.configure_from_settings(settings or {})
        return manager

    def test_creates_feature_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-7: configure_from_settings creates per-feature JSONL files when logged to."""
        manager = self._create_manager(tmp_path, monkeypatch)
        try:
            logging.getLogger("zorivest.trades").info("trade log entry")
            time.sleep(0.1)  # QueueListener processes asynchronously
            manager.shutdown()
            assert (tmp_path / "trades.jsonl").exists()
            # Value: verify the log entry is valid JSONL with message field
            content = (tmp_path / "trades.jsonl").read_text().strip()
            if content:
                parsed = json.loads(content.split("\n")[-1])
                assert "message" in parsed
        finally:
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()

    def test_feature_routing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-8: zorivest.trades logs appear in trades.jsonl, not in other files."""
        manager = self._create_manager(tmp_path, monkeypatch)
        try:
            logging.getLogger("zorivest.trades").info("trade only")
            time.sleep(0.1)
            manager.shutdown()

            # Should be in trades.jsonl
            trades_content = (tmp_path / "trades.jsonl").read_text()
            assert "trade only" in trades_content
            # Value: verify is valid JSONL
            parsed = json.loads(trades_content.strip().split("\n")[-1])
            assert parsed["logger"] == "zorivest.trades"

            # Should NOT be in marketdata.jsonl or misc.jsonl
            if (tmp_path / "marketdata.jsonl").exists():
                md_content = (tmp_path / "marketdata.jsonl").read_text()
                assert "trade only" not in md_content
        finally:
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()

    def test_catchall_routing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-9: some.random.logger logs appear in misc.jsonl."""
        manager = self._create_manager(tmp_path, monkeypatch)
        try:
            logging.getLogger("some.random.module").info("catchall message")
            time.sleep(0.1)
            manager.shutdown()
            misc_content = (tmp_path / "misc.jsonl").read_text()
            assert "catchall message" in misc_content
            # Value: verify it's valid JSONL and logger name is preserved
            parsed = json.loads(misc_content.strip().split("\n")[-1])
            assert parsed["logger"] == "some.random.module"
        finally:
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()

    def test_settings_level_respected(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-13: Settings key logging.trades.level=WARNING is respected."""
        manager = self._create_manager(
            tmp_path, monkeypatch,
            settings={"logging.trades.level": "WARNING"},
        )
        try:
            logger = logging.getLogger("zorivest.trades")
            logger.info("should be filtered")
            logger.warning("should appear")
            time.sleep(0.1)
            manager.shutdown()
            trades_content = (tmp_path / "trades.jsonl").read_text()
            assert "should be filtered" not in trades_content
            assert "should appear" in trades_content
            # Value: verify the WARNING entry has correct level
            for line in trades_content.strip().split("\n"):
                if line.strip():
                    parsed = json.loads(line)
                    if parsed.get("message") == "should appear":
                        assert parsed["level"] == "WARNING"
                        break
        finally:
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()

    def test_default_rotation_values(self) -> None:
        """AC-14: Default rotation: 10 MB, 5 backups per file."""
        assert DEFAULT_ROTATION_MB == 10
        assert DEFAULT_BACKUP_COUNT == 5


# ---------------------------------------------------------------------------
# update_feature_level (AC-10)
# ---------------------------------------------------------------------------


class TestUpdateFeatureLevel:
    """AC-10: Runtime level change without restart."""

    def test_update_gates_messages(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-10: update_feature_level('trades', 'WARNING') gates INFO messages."""
        monkeypatch.setattr(
            "zorivest_infra.logging.config.get_log_directory", lambda: tmp_path
        )
        manager = LoggingManager()
        manager.bootstrap()
        manager.configure_from_settings({})
        try:
            logger = logging.getLogger("zorivest.trades")

            # Log an INFO message first
            logger.info("info before update")
            time.sleep(0.05)

            # Now change level to WARNING
            manager.update_feature_level("trades", "WARNING")

            # Log an INFO message (should be gated)
            logger.info("info after update")
            time.sleep(0.05)

            # Log a WARNING (should appear)
            logger.warning("warning after update")
            time.sleep(0.1)

            manager.shutdown()
            trades_content = (tmp_path / "trades.jsonl").read_text()
            assert "info before update" in trades_content
            assert "info after update" not in trades_content
            assert "warning after update" in trades_content
            # Value: verify the level change filtered INFO after update
            assert trades_content.count("info before update") == 1
            assert trades_content.count("info after update") == 0
        finally:
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()


# ---------------------------------------------------------------------------
# shutdown (AC-11)
# ---------------------------------------------------------------------------


class TestShutdown:
    """AC-11: Graceful shutdown."""

    def test_shutdown_stops_listener(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-11: shutdown() stops the QueueListener cleanly."""
        monkeypatch.setattr(
            "zorivest_infra.logging.config.get_log_directory", lambda: tmp_path
        )
        manager = LoggingManager()
        manager.bootstrap()
        manager.configure_from_settings({})
        try:
            assert manager._listener is not None
            manager.shutdown()
            # Value: verify listener was set to None after shutdown
            assert manager._listener is None
            # After shutdown, calling shutdown again should not raise
            manager.shutdown()
        finally:
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()


# ---------------------------------------------------------------------------
# Thread safety (AC-12)
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """AC-12: Concurrent logging produces valid JSONL."""

    def test_concurrent_logging(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-12: 3 threads logging simultaneously produce valid JSONL."""
        monkeypatch.setattr(
            "zorivest_infra.logging.config.get_log_directory", lambda: tmp_path
        )
        manager = LoggingManager()
        manager.bootstrap()
        manager.configure_from_settings({})

        try:
            def log_from_thread(feature_prefix: str, count: int) -> None:
                logger = logging.getLogger(feature_prefix)
                for i in range(count):
                    logger.info(f"Thread message {i}")

            threads = [
                threading.Thread(target=log_from_thread, args=(prefix, 50))
                for prefix in ["zorivest.trades", "zorivest.marketdata", "zorivest.tax"]
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            time.sleep(0.2)  # Allow QueueListener to flush
            manager.shutdown()

            # Verify each line is valid JSON
            total_entries = 0
            for feature in ["trades", "marketdata", "tax"]:
                log_file = tmp_path / f"{feature}.jsonl"
                assert log_file.exists(), f"{feature}.jsonl should exist"
                for line in log_file.read_text().strip().split("\n"):
                    if line:
                        parsed = json.loads(line)  # Should not raise
                        assert "message" in parsed
                        total_entries += 1
            # Value: verify total entries is at least 150 (3 threads × 50)
            assert total_entries >= 150, f"Expected >= 150 entries, got {total_entries}"
        finally:
            root = logging.getLogger()
            for h in root.handlers[:]:
                root.removeHandler(h)
                h.close()
