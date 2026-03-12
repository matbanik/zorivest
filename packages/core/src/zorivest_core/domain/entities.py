# packages/core/src/zorivest_core/domain/entities.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from zorivest_core.domain.enums import (
    AccountType,
    BalanceSource,
    ImageOwnerType,
    TradeAction,
)


@dataclass(frozen=True)
class BalanceSnapshot:
    """Point-in-time balance record for an account."""

    id: int
    account_id: str
    datetime: datetime
    balance: Decimal


@dataclass(frozen=True)
class ImageAttachment:
    """Polymorphic image — attached to Trade, TradeReport, or TradePlan.

    All images are standardized to WebP format. The ``mime_type`` field
    is enforced to be ``"image/webp"`` at construction time.
    """

    id: int
    owner_type: ImageOwnerType
    owner_id: str
    data: bytes
    width: int
    height: int
    file_size: int
    created_at: datetime
    thumbnail: bytes = b""
    mime_type: str = "image/webp"
    caption: str = ""

    def __post_init__(self) -> None:
        if self.mime_type != "image/webp":
            msg = f"mime_type must be 'image/webp', got '{self.mime_type}'"
            raise ValueError(msg)


@dataclass
class TradeReport:
    """Post-trade review and meta-analysis for a completed trade.

    MEU-52: FIC AC-1. Fields from domain-model-reference.md L50-60.
    """

    id: int
    trade_id: str               # FK → Trade.exec_id (unique)
    setup_quality: int          # 1-5 rating
    execution_quality: int      # 1-5 rating
    followed_plan: bool
    emotional_state: str        # EmotionalState value
    created_at: datetime
    lessons_learned: str = ""
    tags: list[str] = field(default_factory=list)
    images: list[ImageAttachment] = field(default_factory=list)


@dataclass
class Trade:
    """A single execution (buy or sell) record."""

    exec_id: str
    time: datetime
    instrument: str
    action: TradeAction
    quantity: float
    price: float
    account_id: str
    commission: float = 0.0
    realized_pnl: float = 0.0
    images: list[ImageAttachment] = field(default_factory=list)
    report: Optional[TradeReport] = None  # MEU-52: typed reference

    def attach_image(self, img: ImageAttachment) -> None:
        """Append an ImageAttachment to this trade's image list."""
        self.images.append(img)


@dataclass
class Account:
    """A financial account (brokerage, bank, credit, retirement)."""

    account_id: str
    name: str
    account_type: AccountType
    institution: str = ""
    currency: str = "USD"
    is_tax_advantaged: bool = False
    notes: str = ""
    sub_accounts: list[str] = field(default_factory=list)
    balance_source: BalanceSource = BalanceSource.MANUAL
    balance_snapshots: list[BalanceSnapshot] = field(default_factory=list)
