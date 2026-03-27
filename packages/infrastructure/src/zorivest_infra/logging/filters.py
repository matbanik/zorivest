"""Feature routing and catchall filters for JSONL log file routing.

FeatureFilter routes records to per-feature log files by logger name prefix.
CatchallFilter routes unmatched records to misc.jsonl, preventing silent loss.
"""

from __future__ import annotations

import logging


class FeatureFilter(logging.Filter):
    """Routes log records to the correct feature file by logger name prefix."""

    def __init__(self, prefix: str) -> None:
        super().__init__()
        self.prefix = prefix

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith(self.prefix)


class CatchallFilter(logging.Filter):
    """Accepts records NOT matched by any feature prefix.

    Prevents silent log loss from __name__-based loggers.
    Records matching a known feature prefix are rejected (they go
    to that feature's dedicated handler instead).
    """

    def __init__(self, known_prefixes: list[str]) -> None:
        super().__init__()
        self.known_prefixes = known_prefixes

    def filter(self, record: logging.LogRecord) -> bool:
        return not any(record.name.startswith(prefix) for prefix in self.known_prefixes)
