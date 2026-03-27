"""JSONL formatter for structured log output.

Formats each log record as a single-line JSON object, using a deny-list
approach for extras — all non-reserved attributes are preserved.
"""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone

# Stdlib LogRecord attributes to exclude from extras
_RESERVED_ATTRS = frozenset(
    {
        "name",
        "msg",
        "args",
        "created",
        "relativeCreated",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "pathname",
        "filename",
        "module",
        "thread",
        "threadName",
        "process",
        "processName",
        "levelname",
        "levelno",
        "msecs",
        "message",
        "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects (JSONL).

    Uses a deny-list approach: ALL extra attributes are included
    except reserved stdlib ones. This preserves arbitrary structured
    data passed via extra={} (e.g., startup metrics, trade context).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "thread": record.threadName,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        # Include ALL non-reserved extras (deny-list, not whitelist)
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                log_entry[key] = value

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        return json.dumps(log_entry, default=str, ensure_ascii=False)
