"""Central logging configuration — FEATURES registry, LoggingManager, log directory.

This module provides the core logging infrastructure for Zorivest:
- FEATURES registry mapping feature names to logger prefixes
- get_feature_logger() for type-safe logger retrieval
- get_log_directory() for platform-appropriate log file placement
- LoggingManager for QueueHandler/QueueListener lifecycle management
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import queue
import sys
from pathlib import Path
from typing import Optional

from .filters import CatchallFilter, FeatureFilter
from .formatters import JsonFormatter
from .redaction import RedactionFilter

# Feature registry: maps feature name → logger prefix
FEATURES: dict[str, str] = {
    "trades": "zorivest.trades",
    "accounts": "zorivest.accounts",
    "marketdata": "zorivest.marketdata",
    "tax": "zorivest.tax",
    "scheduler": "zorivest.scheduler",
    "db": "zorivest.db",
    "calculator": "zorivest.calculator",
    "images": "zorivest.images",
    "api": "zorivest.api",
    "frontend": "zorivest.frontend",
    "app": "zorivest.app",
    "uvicorn": "uvicorn",
}

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ROTATION_MB = 10
DEFAULT_BACKUP_COUNT = 5


def get_feature_logger(feature: str) -> logging.Logger:
    """Get a logger for a registered feature name."""
    if feature not in FEATURES:
        raise ValueError(f"Unknown feature: {feature}. Register in FEATURES first.")
    return logging.getLogger(FEATURES[feature])


def get_log_directory() -> Path:
    """Resolve platform-appropriate log directory."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    log_dir = base / "zorivest" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


class LoggingManager:
    """Manages the QueueHandler/QueueListener logging lifecycle."""

    def __init__(self) -> None:
        self._log_dir: Optional[Path] = None
        self._queue: Optional[queue.Queue[logging.LogRecord]] = None
        self._listener: Optional[logging.handlers.QueueListener] = None
        self._handlers: dict[str, logging.handlers.RotatingFileHandler] = {}
        self._formatter = JsonFormatter()
        self._redaction_filter = RedactionFilter()

    def bootstrap(self) -> None:
        """Phase 1: Minimal file logging before DB is available."""
        self._log_dir = get_log_directory()
        handler = logging.FileHandler(self._log_dir / "bootstrap.jsonl")
        handler.setFormatter(self._formatter)
        handler.addFilter(self._redaction_filter)

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(handler)
        logging.getLogger("zorivest.app").info(
            "Bootstrap logging started", extra={"phase": "bootstrap"}
        )

    def configure_from_settings(self, settings: dict[str, str]) -> None:
        """Phase 2: Build full queue-based logging from DB settings."""
        self._queue = queue.Queue(-1)  # Unbounded

        # Global rotation policy (applies to all feature files)
        rotation_mb = int(settings.get("logging.rotation_mb", str(DEFAULT_ROTATION_MB)))
        backup_count = int(
            settings.get("logging.backup_count", str(DEFAULT_BACKUP_COUNT))
        )

        # Create per-feature handlers
        handlers: list[logging.Handler] = []
        for feature, logger_prefix in FEATURES.items():
            level_str = settings.get(f"logging.{feature}.level", DEFAULT_LOG_LEVEL)

            handler = logging.handlers.RotatingFileHandler(
                filename=self._log_dir / f"{feature}.jsonl",  # type: ignore[operator]
                maxBytes=rotation_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setLevel(getattr(logging, level_str.upper(), logging.INFO))
            handler.setFormatter(self._formatter)
            handler.addFilter(FeatureFilter(logger_prefix))
            handler.addFilter(self._redaction_filter)
            self._handlers[feature] = handler
            handlers.append(handler)

        # Catchall handler for __name__-based loggers → misc.jsonl
        catchall_handler = logging.handlers.RotatingFileHandler(
            filename=self._log_dir / "misc.jsonl",  # type: ignore[operator]
            maxBytes=rotation_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8",
            mode="a",
        )
        catchall_handler.setLevel(logging.DEBUG)
        catchall_handler.setFormatter(self._formatter)
        catchall_handler.addFilter(CatchallFilter(list(FEATURES.values())))
        catchall_handler.addFilter(self._redaction_filter)
        handlers.append(catchall_handler)

        # Start listener
        self._listener = logging.handlers.QueueListener(
            self._queue, *handlers, respect_handler_level=True
        )
        self._listener.start()

        # Replace root handler with QueueHandler
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)
        root.addHandler(logging.handlers.QueueHandler(self._queue))
        root.setLevel(logging.DEBUG)

        logging.getLogger("zorivest.app").info(
            "Full queue-based logging configured",
            extra={"phase": "configured", "features": list(FEATURES.keys())},
        )

    def update_feature_level(self, feature: str, level: str) -> None:
        """Runtime level change for a single feature (no restart)."""
        if feature in self._handlers:
            self._handlers[feature].setLevel(
                getattr(logging, level.upper(), logging.INFO)
            )

    def shutdown(self) -> None:
        """Graceful shutdown: stop listener, flush handlers."""
        if self._listener:
            self._listener.stop()
            self._listener = None
