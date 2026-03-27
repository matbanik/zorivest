# packages/infrastructure/src/zorivest_infra/broker_adapters/csv_base.py
"""CSV parser framework — base class for broker-specific CSV parsers.

Implements encoding detection (chardet) and BOM handling.
Provides the CSVBrokerAdapter protocol contract.
"""

from __future__ import annotations

import csv
import io
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import chardet

from zorivest_core.domain.enums import BrokerType, ImportStatus
from zorivest_core.domain.import_types import (
    ImportError as ImportErr,
    ImportResult,
    RawExecution,
)

logger = logging.getLogger(__name__)


class CSVParserBase(ABC):
    """Abstract base for CSV-based broker adapters.

    Subclasses implement ``detect()`` for header fingerprinting
    and ``parse_rows()`` for row-level parsing. This base class
    handles encoding detection, BOM removal, CSV reading, and
    ImportResult aggregation.
    """

    @property
    @abstractmethod
    def broker_type(self) -> BrokerType: ...

    @abstractmethod
    def detect(self, headers: list[str]) -> bool:
        """Return True if headers match this broker's fingerprint."""
        ...

    @abstractmethod
    def parse_rows(self, rows: list[dict[str, str]]) -> list[RawExecution]:
        """Parse CSV rows into RawExecution records."""
        ...

    def parse_file(self, file_path: Path) -> ImportResult:
        """Detect encoding → read CSV → parse rows → aggregate result."""
        try:
            encoding = self._detect_encoding(file_path)
            raw_content = file_path.read_text(encoding=encoding, errors="replace")
            content = self._strip_bom(raw_content)

            if not content.strip():
                return ImportResult(
                    status=ImportStatus.SUCCESS,
                    broker=self.broker_type,
                    total_rows=0,
                    parsed_rows=0,
                )

            # Find the data section (some CSVs have header/footer sections)
            lines = self._extract_data_lines(content)

            if not lines:
                return ImportResult(
                    status=ImportStatus.SUCCESS,
                    broker=self.broker_type,
                    total_rows=0,
                    parsed_rows=0,
                )

            reader = csv.DictReader(io.StringIO("\n".join(lines)))
            rows = list(reader)

            if not rows:
                return ImportResult(
                    status=ImportStatus.SUCCESS,
                    broker=self.broker_type,
                    total_rows=0,
                    parsed_rows=0,
                )

            executions: list[RawExecution] = []
            errors: list[ImportErr] = []

            try:
                executions = self.parse_rows(rows)
            except Exception as exc:
                logger.warning("Batch parse error in %s: %s", file_path, exc)
                errors.append(ImportErr(field="parse", message=str(exc)))

            total = len(rows)
            parsed = len(executions)

            if parsed == 0 and errors:
                status = ImportStatus.FAILED
            elif errors:
                status = ImportStatus.PARTIAL
            else:
                status = ImportStatus.SUCCESS

            return ImportResult(
                status=status,
                broker=self.broker_type,
                executions=executions,
                errors=errors,
                total_rows=total,
                parsed_rows=parsed,
                skipped_rows=total - parsed,
            )

        except Exception as exc:
            logger.warning("Failed to parse CSV from %s: %s", file_path, exc)
            return ImportResult(
                status=ImportStatus.FAILED,
                broker=self.broker_type,
                errors=[ImportErr(field="file", message=f"CSV read error: {exc}")],
            )

    def _extract_data_lines(self, content: str) -> list[str]:
        """Extract data-relevant lines from CSV content.

        Override in subclasses that have multi-section CSVs (e.g., TOS).
        Default: return all non-empty lines.
        """
        return [line for line in content.splitlines() if line.strip()]

    @staticmethod
    def _detect_encoding(file_path: Path) -> str:
        """Detect file encoding using chardet."""
        raw_bytes = file_path.read_bytes()
        if not raw_bytes:
            return "utf-8"
        result = chardet.detect(raw_bytes)
        encoding = result.get("encoding") or "utf-8"
        return encoding

    @staticmethod
    def _strip_bom(content: str) -> str:
        """Remove UTF-8 BOM if present."""
        if content.startswith("\ufeff"):
            return content[1:]
        return content
