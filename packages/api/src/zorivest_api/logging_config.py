# packages/api/src/zorivest_api/logging_config.py
"""Structlog UTF-8 configuration (MEU-PW4, §9B.2b).

Addresses [PIPE-CHARMAP]: Windows cp1252 encoding crash.
Configures structlog with UTF-8 safe output processors.
Must be called once during FastAPI lifespan startup.
"""

from __future__ import annotations

import sys

import structlog


def configure_structlog_utf8() -> None:
    """Configure structlog with UTF-8 safe output.

    Addresses [PIPE-CHARMAP]: Windows cp1252 encoding crash.
    After calling this:
    - sys.stderr is reconfigured to UTF-8 (if .reconfigure() exists)
    - structlog uses UnicodeDecoder, TimeStamper, and TTY-aware renderer
    - PrintLoggerFactory writes to sys.stderr (now UTF-8)

    Must be called once during FastAPI lifespan startup.
    """
    # Force UTF-8 on stderr if not already (Windows default is cp1252)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),  # Decode bytes → str
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if sys.stderr.isatty()
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
