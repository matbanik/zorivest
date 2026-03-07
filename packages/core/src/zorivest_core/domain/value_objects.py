# packages/core/src/zorivest_core/domain/value_objects.py

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from zorivest_core.domain.enums import ConvictionLevel


@dataclass(frozen=True)
class Money:
    """Monetary amount with currency.  Always non-negative."""

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < 0:
            msg = f"amount must not be negative, got {self.amount}"
            raise ValueError(msg)
        if not self.currency:
            msg = "currency must not be empty"
            raise ValueError(msg)


@dataclass(frozen=True)
class PositionSize:
    """Computed position sizing result — wraps calculator output."""

    share_size: int
    position_size: Decimal
    risk_per_share: Decimal

    def __post_init__(self) -> None:
        if self.share_size < 0:
            msg = f"share_size must not be negative, got {self.share_size}"
            raise ValueError(msg)


@dataclass(frozen=True)
class Ticker:
    """Equity ticker symbol — normalized to uppercase."""

    symbol: str

    def __post_init__(self) -> None:
        stripped = self.symbol.strip()
        if not stripped:
            msg = "symbol must not be empty or whitespace-only"
            raise ValueError(msg)
        # Frozen dataclass requires object.__setattr__ for mutation in __post_init__
        object.__setattr__(self, "symbol", stripped.upper())


@dataclass(frozen=True)
class Conviction:
    """Trade conviction level wrapper."""

    level: ConvictionLevel


@dataclass(frozen=True)
class ImageData:
    """Raw image payload with dimensions."""

    data: bytes
    mime_type: str
    width: int
    height: int

    def __post_init__(self) -> None:
        if not self.data:
            msg = "data must not be empty"
            raise ValueError(msg)
        if self.width <= 0:
            msg = f"width must be positive, got {self.width}"
            raise ValueError(msg)
        if self.height <= 0:
            msg = f"height must be positive, got {self.height}"
            raise ValueError(msg)
