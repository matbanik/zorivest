# packages/core/src/zorivest_core/services/import_service.py
"""Import orchestrator — routes files to the correct broker adapter.

Layer note: ImportService stays in core/services/ because it orchestrates
domain logic (adapter selection, result aggregation). The concrete
file-parsing adapters live in infrastructure/broker_adapters/.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from zorivest_core.application.ports import BrokerFileAdapter, CSVBrokerAdapter
from zorivest_core.domain.enums import BrokerType
from zorivest_core.domain.import_types import ImportResult

logger = logging.getLogger(__name__)


class UnknownBrokerFormat(Exception):
    """Raised when auto-detection cannot identify the broker format."""


class ImportService:
    """Orchestrates file import by routing to the correct adapter.

    Supports:
    - Explicit broker_hint for direct routing
    - Auto-detection via file extension and header fingerprinting
    """

    def __init__(self, adapters: list[BrokerFileAdapter]) -> None:
        self._adapters = {a.broker_type: a for a in adapters}
        # Filter to adapters that also implement CSVBrokerAdapter
        self._csv_adapters: Sequence[CSVBrokerAdapter] = [
            cast(CSVBrokerAdapter, a)
            for a in adapters
            if hasattr(a, "detect") and hasattr(a, "parse_rows")
        ]

    def import_file(
        self, file_path: Path, broker_hint: BrokerType | None = None
    ) -> ImportResult:
        """Import a broker export file.

        Args:
            file_path: Path to the export file (XML or CSV).
            broker_hint: If provided, route directly to that adapter.

        Returns:
            ImportResult with parsed executions and any errors.

        Raises:
            UnknownBrokerFormat: If auto-detection fails.
        """
        if broker_hint is not None:
            adapter = self._adapters.get(broker_hint)
            if adapter is None:
                raise UnknownBrokerFormat(
                    f"No adapter registered for broker: {broker_hint}"
                )
            return adapter.parse_file(file_path)

        # Auto-detect by file extension
        suffix = file_path.suffix.lower()

        if suffix == ".xml":
            # Try IBKR FlexQuery
            ibkr = self._adapters.get(BrokerType.IBKR)
            if ibkr is not None:
                return ibkr.parse_file(file_path)
            raise UnknownBrokerFormat("XML file but no IBKR adapter registered")

        if suffix == ".csv":
            broker = self.auto_detect_csv_broker(file_path)
            adapter = self._adapters.get(broker)
            if adapter is None:
                raise UnknownBrokerFormat(f"Detected {broker} but no adapter found")
            return adapter.parse_file(file_path)

        raise UnknownBrokerFormat(f"Unsupported file extension: {suffix}")

    def auto_detect_csv_broker(self, file_path: Path) -> BrokerType:
        """Read CSV headers and try each parser's detect() method.

        Reads up to 10 lines for header detection.

        Raises:
            UnknownBrokerFormat: If no parser matches.
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Strip BOM
            if content.startswith("\ufeff"):
                content = content[1:]

            lines = [line for line in content.splitlines() if line.strip()]
            if not lines:
                raise UnknownBrokerFormat("Empty CSV file")

            # Try to find headers in first 10 lines
            for line in lines[:10]:
                headers = [h.strip() for h in line.split(",")]
                for csv_adapter in self._csv_adapters:
                    if csv_adapter.detect(headers):
                        return csv_adapter.broker_type

        except UnknownBrokerFormat:
            raise
        except Exception as exc:
            raise UnknownBrokerFormat(f"CSV read error: {exc}") from exc

        # Collect headers we tried for the error message
        tried_headers: list[str] = []
        for line in lines[:3]:
            tried_headers.append(line.strip()[:200])

        raise UnknownBrokerFormat(
            f"No registered CSV parser matched the file headers: {tried_headers}"
        )
