# packages/core/src/zorivest_core/domain/precision.py
"""Financial precision utilities (§9.5e).

Avoids floating-point precision errors for monetary values by
converting to integer micros (1 unit = 1,000,000 micros) and
using Decimal for parsing.

Spec: 09-scheduling.md §9.5e
MEU: 86
"""

from __future__ import annotations

from decimal import Decimal

# 1 unit = 1,000,000 micros (6 decimal places of precision)
MICROS_FACTOR = 1_000_000


def to_micros(value: float | Decimal | str) -> int:
    """Convert a monetary value to integer micros.

    Args:
        value: Monetary value (e.g., 123.456789).

    Returns:
        Integer micros (e.g., 123456789).
    """
    d = Decimal(str(value))
    return int(d * MICROS_FACTOR)


def from_micros(micros: int) -> float:
    """Convert integer micros back to a float.

    Args:
        micros: Integer micros value.

    Returns:
        Float value with up to 6 decimal places.
    """
    d = Decimal(micros) / Decimal(MICROS_FACTOR)
    return float(d)


def parse_monetary(value: str) -> Decimal:
    """Parse a monetary string to Decimal without float precision errors.

    Args:
        value: String representation of a monetary value.

    Returns:
        Decimal value.
    """
    return Decimal(value)
