# packages/core/src/zorivest_core/application/dtos.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from zorivest_core.domain.enums import (
    AccountType,
    BalanceSource,
    ImageOwnerType,
    TradeAction,
)


@dataclass(frozen=True)
class TradeDTO:
    """Data transfer object for Trade — no binary data."""

    exec_id: str
    time: datetime
    instrument: str
    action: TradeAction
    quantity: float
    price: float
    account_id: str
    commission: float
    realized_pnl: float
    image_count: int


@dataclass(frozen=True)
class AccountDTO:
    """Data transfer object for Account — no nested collections."""

    account_id: str
    name: str
    account_type: AccountType
    institution: str
    currency: str
    is_tax_advantaged: bool
    notes: str
    balance_source: BalanceSource
    latest_balance: Decimal | None


@dataclass(frozen=True)
class BalanceSnapshotDTO:
    """Data transfer object for BalanceSnapshot."""

    id: int
    account_id: str
    datetime: datetime
    balance: Decimal


@dataclass(frozen=True)
class ImageAttachmentDTO:
    """Data transfer object for ImageAttachment — no binary data/thumbnail."""

    id: int
    owner_type: ImageOwnerType
    owner_id: str
    mime_type: str
    caption: str
    width: int
    height: int
    file_size: int
    created_at: datetime
