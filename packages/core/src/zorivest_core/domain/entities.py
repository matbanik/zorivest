# packages/core/src/zorivest_core/domain/entities.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from zorivest_core.domain.enums import (
    AccountType,
    AcquisitionSource,
    BalanceSource,
    ConvictionLevel,
    CostBasisMethod,
    FilingStatus,
    ImageOwnerType,
    PlanStatus,
    TradeAction,
    WashSaleMatchingMethod,
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
    is_archived: bool = False  # MEU-37 AC-1: Soft-delete flag
    is_system: bool = False  # MEU-37 AC-2: System-seeded, immutable/undeletable


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
    shares_planned: Optional[int] = None  # Position size (shares/contracts)
    position_size: Optional[float] = None  # Total dollar value (shares × entry_price)
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


# ── Phase 3A: Tax Foundation ─────────────────────────────────────────────


@dataclass
class TaxLot:
    """Individual purchase lot for cost basis tracking.

    MEU-123: FIC AC-2. 13 stored fields + 2 computed properties.
    Spec: domain-model-reference.md L353-366.
    """

    lot_id: str  # PK
    account_id: str  # FK → Account
    ticker: str
    open_date: datetime  # Purchase date
    close_date: Optional[datetime]  # None = still open
    quantity: float
    cost_basis: Decimal  # Per-share, adjusted for wash sales
    proceeds: Decimal  # Per-share, populated on close
    wash_sale_adjustment: Decimal  # Deferred loss added to basis
    is_closed: bool
    linked_trade_ids: list[str] = field(default_factory=list)  # FK → Trade.exec_id
    cost_basis_method: Optional[CostBasisMethod] = (
        None  # Per-lot override (None = use TaxProfile default)
    )
    realized_gain_loss: Decimal = Decimal(
        "0.00"
    )  # Computed on close via calculate_realized_gain
    acquisition_source: AcquisitionSource | None = None  # MEU-134: DRIP detection
    # ── Phase 3F: Provenance tracking (MEU-216) ──────────────────────────
    materialized_at: Optional[str] = None  # ISO timestamp of last sync
    is_user_modified: bool = False  # User override protection flag
    source_hash: Optional[str] = None  # SHA-256 of source trade data
    sync_status: str = "synced"  # synced | conflict | orphaned

    @property
    def holding_period_days(self) -> int:
        """Computed holding period in days.

        Open lots: days from open_date to today (UTC).
        Closed lots: days from open_date to close_date.
        Returns 0 if open_date is in the future.
        """
        end = self.close_date if self.close_date else datetime.now(tz=timezone.utc)
        delta = (end - self.open_date).days
        return max(delta, 0)

    @property
    def is_long_term(self) -> bool:
        """True when holding_period >= 366 days (IRS long-term threshold)."""
        return self.holding_period_days >= 366


@dataclass
class TaxProfile:
    """User's tax configuration — stored as a settings entity.

    MEU-124: FIC AC-3. 14 spec fields + 1 PK (id).
    Spec: domain-model-reference.md L381-401.
    """

    id: int  # PK (auto-increment with unique tax_year constraint)
    filing_status: FilingStatus
    tax_year: int  # e.g., 2026
    federal_bracket: float  # Marginal rate, e.g. 0.37
    state_tax_rate: float  # e.g., 0.05 for 5%
    state: str  # e.g., "NY", "TX"
    prior_year_tax: Decimal  # For safe harbor calculation
    agi_estimate: Decimal  # For NIIT threshold check
    capital_loss_carryforward: Decimal  # From prior year
    wash_sale_method: WashSaleMatchingMethod
    default_cost_basis: CostBasisMethod
    include_drip_wash_detection: bool = True
    include_spousal_accounts: bool = False
    section_475_elected: bool = False  # Mark-to-Market
    section_1256_eligible: bool = False  # Futures 60/40


# ── Phase 3D: Quarterly Estimates ────────────────────────────────────────


@dataclass
class QuarterlyEstimate:
    """Estimated tax payment tracking per quarter.

    MEU-143: FIC AC-143.1. 9 fields per domain-model-reference.md L403-413.
    Spec: domain-model-reference.md L403-413.
    """

    id: int  # PK (auto-increment)
    tax_year: int  # e.g., 2026
    quarter: int  # 1-4
    due_date: datetime  # Apr 15, Jun 15, Sep 15, Jan 15
    required_payment: Decimal  # Computed via safe harbor / annualized method
    actual_payment: Decimal  # User-entered payment amount
    method: (
        str  # "safe_harbor_100" | "safe_harbor_110" | "current_year_90" | "annualized"
    )
    cumulative_ytd_gains: Decimal  # At time of calculation
    underpayment_penalty_risk: Decimal  # Estimated penalty if short
