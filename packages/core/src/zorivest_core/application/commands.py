# packages/core/src/zorivest_core/application/commands.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from zorivest_core.domain.enums import (
    AccountType,
    BalanceSource,
    ImageOwnerType,
    TradeAction,
)


@dataclass(frozen=True)
class CreateTrade:
    """Command to create a new trade execution record."""

    exec_id: str
    time: datetime
    instrument: str
    action: TradeAction
    quantity: float
    price: float
    account_id: str
    commission: float = 0.0
    realized_pnl: float = 0.0
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.exec_id or not self.exec_id.strip():
            msg = "exec_id must not be empty"
            raise ValueError(msg)
        if self.quantity <= 0:
            msg = f"quantity must be positive, got {self.quantity}"
            raise ValueError(msg)


@dataclass(frozen=True)
class AttachImage:
    """Command to attach an image to a trade, report, or plan."""

    owner_type: ImageOwnerType
    owner_id: str
    data: bytes
    mime_type: str
    width: int
    height: int
    caption: str = ""
    thumbnail: bytes = b""

    def __post_init__(self) -> None:
        if self.mime_type != "image/webp":
            msg = f"mime_type must be 'image/webp', got '{self.mime_type}'"
            raise ValueError(msg)


@dataclass(frozen=True)
class CreateAccount:
    """Command to create a new financial account."""

    account_id: str
    name: str
    account_type: AccountType
    institution: str = ""
    currency: str = "USD"
    is_tax_advantaged: bool = False
    notes: str = ""
    balance_source: BalanceSource = BalanceSource.MANUAL

    def __post_init__(self) -> None:
        if not self.account_id or not self.account_id.strip():
            msg = "account_id must not be empty"
            raise ValueError(msg)
        if not self.name or not self.name.strip():
            msg = "name must not be empty"
            raise ValueError(msg)


@dataclass(frozen=True)
class UpdateBalance:
    """Command to record a balance snapshot for an account."""

    account_id: str
    balance: Decimal
    snapshot_datetime: datetime = field(default_factory=datetime.now)
