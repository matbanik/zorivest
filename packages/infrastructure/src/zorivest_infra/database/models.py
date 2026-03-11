"""SQLAlchemy ORM models for Zorivest database schema.

Source: 02-infrastructure.md §2.1

Contains all 21 model classes + Base. Financial columns use Numeric(15,6)
per the precision warning in the spec. Display-only columns use Float.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Declarative base for all Zorivest ORM models."""


# ── Core Trade/Account/Image Models ───────────────────────────────────────


class TradeModel(Base):
    __tablename__ = "trades"

    exec_id = Column(String, primary_key=True)
    time = Column(DateTime, nullable=False)
    instrument = Column(String, nullable=False)
    action = Column(String(3), nullable=False)  # BOT or SLD
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    commission = Column(Numeric(15, 6), default=0.0)
    realized_pnl = Column(Numeric(15, 6), default=0.0)

    images = relationship(
        "ImageModel",
        primaryjoin="and_(ImageModel.owner_type=='trade', "
        "foreign(ImageModel.owner_id)==TradeModel.exec_id)",
        viewonly=True,
    )
    report = relationship("TradeReportModel", back_populates="trade", uselist=False)
    account_rel = relationship("AccountModel", back_populates="trades")


class ImageModel(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_type = Column(String(20), nullable=False, index=True)  # "trade", "report", "plan"
    owner_id = Column(String, nullable=False, index=True)
    data = Column(LargeBinary, nullable=False)
    thumbnail = Column(LargeBinary, nullable=True)
    mime_type = Column(String(50), default="image/webp")
    caption = Column(Text, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)


class AccountModel(Base):
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    account_type = Column(String(20), nullable=False)
    institution = Column(String, nullable=True)
    currency = Column(String(3), default="USD")
    is_tax_advantaged = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)

    trades = relationship("TradeModel", back_populates="account_rel")
    balance_snapshots = relationship("BalanceSnapshotModel", back_populates="account_rel")


# ── Report/Plan/Watchlist Models ──────────────────────────────────────────


class TradeReportModel(Base):
    __tablename__ = "trade_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String, ForeignKey("trades.exec_id"), unique=True, nullable=False)
    setup_quality = Column(Integer, nullable=True)  # 1-5
    execution_quality = Column(Integer, nullable=True)  # 1-5
    followed_plan = Column(Boolean, nullable=True)
    emotional_state = Column(String, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array of strings
    created_at = Column(DateTime, nullable=False)

    trade = relationship("TradeModel", back_populates="report")


class TradePlanModel(Base):
    """Forward-looking trade thesis with conviction and strategy."""

    __tablename__ = "trade_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    direction = Column(String(3), nullable=False)  # BOT or SLD
    conviction = Column(String(10), nullable=False)  # ConvictionLevel
    strategy_name = Column(String, nullable=True)
    strategy_description = Column(Text, nullable=True)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    entry_conditions = Column(Text, nullable=True)
    exit_conditions = Column(Text, nullable=True)
    timeframe = Column(String, nullable=True)
    status = Column(String(15), default="draft")  # PlanStatus
    linked_trade_id = Column(String, ForeignKey("trades.exec_id"), nullable=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class WatchlistModel(Base):
    """Named collections of tickers to monitor."""

    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    items = relationship(
        "WatchlistItemModel", back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItemModel(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    ticker = Column(String, nullable=False)
    added_at = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    watchlist = relationship("WatchlistModel", back_populates="items")


# ── Balance/Settings Models ───────────────────────────────────────────────


class BalanceSnapshotModel(Base):
    __tablename__ = "balance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    datetime = Column(DateTime, nullable=False)
    balance = Column(Numeric(15, 6), nullable=False)

    account_rel = relationship("AccountModel", back_populates="balance_snapshots")


class SettingModel(Base):
    """User-level setting overrides."""

    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text)
    value_type = Column(String(20))
    updated_at = Column(DateTime)


class AppDefaultModel(Base):
    """Application-level setting defaults."""

    __tablename__ = "app_defaults"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False)


class MarketProviderSettingModel(Base):
    """Market data API provider credentials and configuration."""

    __tablename__ = "market_provider_settings"

    provider_name = Column(String, primary_key=True)
    encrypted_api_key = Column(Text, nullable=True)
    encrypted_api_secret = Column(Text, nullable=True)  # dual-key (Alpaca)
    rate_limit = Column(Integer, default=5)
    timeout = Column(Integer, default=30)
    is_enabled = Column(Boolean, default=False)
    last_tested_at = Column(DateTime, nullable=True)
    last_test_status = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


# ── Guard/Circuit Breaker ─────────────────────────────────────────────────


class McpGuardModel(Base):
    """Singleton row — circuit breaker state for MCP tool access."""

    __tablename__ = "mcp_guard"

    id = Column(Integer, primary_key=True, default=1)
    is_enabled = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime, nullable=True)
    lock_reason = Column(String(100), nullable=True)
    calls_per_minute_limit = Column(Integer, default=60)
    calls_per_hour_limit = Column(Integer, default=500)
    updated_at = Column(DateTime, nullable=True)


# ── Build Plan Expansion Models ───────────────────────────────────────────


class RoundTripModel(Base):
    """Groups entry/exit executions into complete round-trips (§3)."""

    __tablename__ = "round_trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    instrument = Column(String, nullable=False, index=True)
    direction = Column(String(3), nullable=False)  # BOT or SLD
    entry_exec_ids = Column(Text, nullable=False)  # JSON list
    exit_exec_ids = Column(Text, nullable=True)  # JSON list (null if open)
    entry_avg_price = Column(Float, nullable=False)
    exit_avg_price = Column(Float, nullable=True)
    total_quantity = Column(Float, nullable=False)
    realized_pnl = Column(Numeric(15, 6), nullable=True)
    total_commission = Column(Numeric(15, 6), default=0.0)
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    status = Column(String(10), default="open")  # RoundTripStatus
    holding_period_seconds = Column(Integer, nullable=True)


class ExcursionMetricsModel(Base):
    """MFE/MAE/BSO auto-enrichment — 1:1 with Trade (§7)."""

    __tablename__ = "excursion_metrics"

    trade_exec_id = Column(String, ForeignKey("trades.exec_id"), primary_key=True)
    mfe_dollars = Column(Numeric(15, 6), nullable=True)
    mfe_pct = Column(Float, nullable=True)
    mae_dollars = Column(Numeric(15, 6), nullable=True)
    mae_pct = Column(Float, nullable=True)
    bso_pct = Column(Float, nullable=True)
    data_source = Column(String, nullable=True)
    computed_at = Column(DateTime, nullable=True)


class IdentifierCacheModel(Base):
    """CUSIP/ISIN/SEDOL → ticker resolution cache (§5)."""

    __tablename__ = "identifier_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_type = Column(String(10), nullable=False, index=True)
    id_value = Column(String(20), nullable=False, index=True)
    ticker = Column(String, nullable=False)
    exchange = Column(String, nullable=True)
    security_type = Column(String, nullable=True)
    source = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    resolved_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)


class TransactionLedgerModel(Base):
    """Per-trade fee decomposition (§9)."""

    __tablename__ = "transaction_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_exec_id = Column(String, ForeignKey("trades.exec_id"), nullable=False, index=True)
    fee_type = Column(String(20), nullable=False)
    amount = Column(Numeric(15, 6), nullable=False)
    currency = Column(String(3), default="USD")
    description = Column(Text, nullable=True)


class OptionsStrategyModel(Base):
    """Multi-leg options grouping (§8)."""

    __tablename__ = "options_strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    strategy_type = Column(String(20), nullable=False)
    underlying = Column(String, nullable=False, index=True)
    leg_exec_ids = Column(Text, nullable=False)  # JSON list
    net_debit_credit = Column(Numeric(15, 6), nullable=True)
    max_profit = Column(Numeric(15, 6), nullable=True)
    max_loss = Column(Numeric(15, 6), nullable=True)
    breakeven_prices = Column(Text, nullable=True)  # JSON list
    created_at = Column(DateTime, nullable=False)


class MistakeEntryModel(Base):
    """Trade mistake categorization with cost attribution (§17)."""

    __tablename__ = "mistake_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String, ForeignKey("trades.exec_id"), nullable=False, index=True)
    category = Column(String(30), nullable=False)
    estimated_cost = Column(Numeric(15, 6), nullable=True)
    notes = Column(Text, nullable=True)
    auto_detected = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)


class BrokerConfigModel(Base):
    """Broker constraint and configuration storage (§23)."""

    __tablename__ = "broker_configs"

    broker_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    pdt_rule = Column(Boolean, default=True)
    pdt_threshold = Column(Numeric(15, 6), default=25000.0)
    settlement_days = Column(Integer, default=1)
    max_leverage = Column(Text, nullable=True)  # JSON dict
    routing_type = Column(String(10), nullable=True)
    commission_schedule = Column(Text, nullable=True)  # JSON dict
    supported_order_types = Column(Text, nullable=True)  # JSON list
    supported_asset_classes = Column(Text, nullable=True)  # JSON list
    trading_hours = Column(Text, nullable=True)  # JSON dict
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class BankTransactionModel(Base):
    """Imported bank statement transaction (§26)."""

    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    post_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 6), nullable=False)
    category = Column(String(30), nullable=True)
    reference_id = Column(String, nullable=True)
    dedup_hash = Column(String(32), nullable=False, index=True)
    source = Column(String(20), nullable=False)
    import_batch_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False)


class BankImportConfigModel(Base):
    """Bank-specific CSV/OFX column mapping configuration (§26)."""

    __tablename__ = "bank_import_configs"

    bank_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String(2), default="US")
    config = Column(Text, nullable=False)  # YAML or JSON
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
