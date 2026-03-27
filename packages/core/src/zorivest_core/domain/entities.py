# packages/core/src/zorivest_core/domain/entities.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from zorivest_core.domain.enums import (
    AccountType,
    BalanceSource,
    ConvictionLevel,
    ImageOwnerType,
    PlanStatus,
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
    trade_id: str  # FK → Trade.exec_id (unique)
    setup_quality: int  # 1-5 rating
    execution_quality: int  # 1-5 rating
    followed_plan: bool
    emotional_state: str  # EmotionalState value
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
    notes: str = ""
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


@dataclass
class TradePlan:
    """Forward-looking trade thesis — plan before execution.

    MEU-66: FIC AC-1. Fields from domain-model-reference.md L78-96.
    """

    id: int
    ticker: str
    direction: TradeAction  # BOT = bullish, SLD = bearish
    conviction: ConvictionLevel
    strategy_name: str
    strategy_description: str  # Rich text — the thesis
    entry_price: float
    stop_loss: float
    target_price: float
    entry_conditions: str  # Technical indicators / triggers
    exit_conditions: str  # When to close regardless
    timeframe: str  # e.g., "intraday", "swing 2-5 days"
    risk_reward_ratio: float  # Computed from entry/stop/target
    status: PlanStatus
    created_at: datetime
    updated_at: datetime
    linked_trade_id: Optional[str] = None  # FK → Trade, nullable
    images: list[ImageAttachment] = field(default_factory=list)
    account_id: Optional[str] = None  # FK → Account, nullable
    executed_at: Optional[datetime] = None  # T5: when status → executed
    cancelled_at: Optional[datetime] = None  # T5: when status → cancelled

    @staticmethod
    def compute_risk_reward(
        entry_price: float,
        stop_loss: float,
        target_price: float,
    ) -> float:
        """Compute risk/reward ratio from entry, stop, and target prices."""
        risk = abs(entry_price - stop_loss)
        if risk == 0.0:
            return 0.0
        reward = abs(target_price - entry_price)
        return reward / risk


@dataclass(frozen=True)
class WatchlistItem:
    """Single ticker entry in a Watchlist.

    MEU-68: FIC AC-1. Fields from domain-model-reference.md L71-76.
    """

    id: int
    watchlist_id: int
    ticker: str
    added_at: datetime
    notes: str = ""


@dataclass
class Watchlist:
    """Named collection of tickers for forward-looking research.

    MEU-68: FIC AC-1. Fields from domain-model-reference.md L64-69.
    """

    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    tickers: list[WatchlistItem] = field(default_factory=list)
