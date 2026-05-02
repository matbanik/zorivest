"""SQLAlchemy ORM models for Zorivest database schema.

Source: 02-infrastructure.md §2.1, 09-scheduling.md §9.2

Contains all 39 model classes + Base. Financial columns use Numeric(15,6)
per the precision warning in the spec. Display-only columns use Float.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    text,
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
    notes = Column(Text, nullable=True, default="")

    images = relationship(
        "ImageModel",
        primaryjoin="and_(ImageModel.owner_type=='trade', "
        "foreign(ImageModel.owner_id)==TradeModel.exec_id)",
        viewonly=True,
    )
    report = relationship(
        "TradeReportModel",
        back_populates="trade",
        uselist=False,
        cascade="all, delete-orphan",
    )
    account_rel = relationship("AccountModel", back_populates="trades")


class ImageModel(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_type = Column(
        String(20), nullable=False, index=True
    )  # "trade", "report", "plan"
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
    is_archived = Column(Boolean, default=False)  # MEU-37 AC-1: Soft-delete flag
    is_system = Column(
        Boolean, default=False
    )  # MEU-37 AC-2: System-seeded, undeletable

    trades = relationship("TradeModel", back_populates="account_rel")
    balance_snapshots = relationship(
        "BalanceSnapshotModel",
        back_populates="account_rel",
        cascade="all, delete-orphan",
    )


# ── Report/Plan/Watchlist Models ──────────────────────────────────────────


class TradeReportModel(Base):
    __tablename__ = "trade_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(
        String,
        ForeignKey("trades.exec_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
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
    risk_reward_ratio = Column(Float, nullable=True, default=0.0)  # MEU-66
    status = Column(String(15), default="draft")  # PlanStatus
    linked_trade_id = Column(String, ForeignKey("trades.exec_id"), nullable=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=True)
    shares_planned = Column(Integer, nullable=True)  # Position size (shares/contracts)
    position_size = Column(
        Float, nullable=True
    )  # Total dollar value (shares × entry_price)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)  # T5: timestamp when → executed
    cancelled_at = Column(DateTime, nullable=True)  # T5: timestamp when → cancelled


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


class EmailProviderModel(Base):
    """Email SMTP provider configuration — singleton row (id=1).

    Source: 06f-gui-settings.md §Email Provider
    """

    __tablename__ = "email_provider"

    id = Column(Integer, primary_key=True, default=1)
    provider_preset = Column(String(50), nullable=True)
    smtp_host = Column(String(256), nullable=True)
    port = Column(Integer, nullable=True)
    security = Column(String(10), nullable=True)  # "STARTTLS" | "SSL"
    username = Column(String(256), nullable=True)
    password_encrypted = Column(LargeBinary, nullable=True)  # Fernet-encrypted
    from_email = Column(String(256), nullable=True)
    updated_at = Column(DateTime, nullable=True)


# ── Email Template Models (§9E.1c) ────────────────────────────────────────


class EmailTemplateModel(Base):
    """User-managed email templates for pipeline SendStep (§9E.1c)."""

    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    subject_template = Column(String(256), nullable=True)
    body_html = Column(Text, nullable=False)
    body_format = Column(
        String(20), nullable=False, default="html"
    )  # "html" | "markdown"
    required_variables = Column(Text, nullable=True)  # JSON list
    sample_data_json = Column(Text, nullable=True)  # JSON dict for preview
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    created_by = Column(String(128), nullable=True)


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
    trade_exec_id = Column(
        String, ForeignKey("trades.exec_id"), nullable=False, index=True
    )
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
    account_id = Column(
        String, ForeignKey("accounts.account_id"), nullable=False, index=True
    )
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


# ── Scheduling & Pipeline Models (Phase 9, §9.2) ─────────────────────────────


class PolicyModel(Base):
    """Persisted pipeline policy document (§9.2c)."""

    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), unique=True, nullable=False)
    schema_version = Column(Integer, nullable=False, default=1)
    policy_json = Column(Text, nullable=False)  # Full PolicyDocument JSON
    content_hash = Column(String(64), nullable=False)
    enabled = Column(Boolean, default=True)
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)
    approved_hash = Column(String(64), nullable=True)  # Hash that was approved
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    created_by = Column(String(128), default="")

    runs = relationship(
        "PipelineRunModel", back_populates="policy", cascade="all, delete-orphan"
    )
    states = relationship(
        "PipelineStateModel", back_populates="policy", cascade="all, delete-orphan"
    )


class PipelineRunModel(Base):
    """A single execution of a pipeline policy (§9.2a)."""

    __tablename__ = "pipeline_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(
        String(36), ForeignKey("policies.id"), nullable=False, index=True
    )
    status = Column(String(20), nullable=False, default="pending")  # PipelineStatus
    trigger_type = Column(String(20), nullable=False)  # "scheduled" | "manual" | "mcp"
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    dry_run = Column(Boolean, default=False)
    created_by = Column(String(128), default="")
    content_hash = Column(String(64), nullable=False)  # Policy hash at execution time

    steps = relationship(
        "PipelineStepModel", back_populates="run", cascade="all, delete-orphan"
    )
    policy = relationship("PolicyModel", back_populates="runs")


class PipelineStepModel(Base):
    """Execution record for a single step within a pipeline run (§9.2b)."""

    __tablename__ = "pipeline_steps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(
        String(36), ForeignKey("pipeline_runs.id"), nullable=False, index=True
    )
    step_id = Column(String(64), nullable=False)  # Matches PolicyStep.id
    step_type = Column(String(64), nullable=False)  # e.g. "fetch", "transform"
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    output_json = Column(Text, nullable=True)  # JSON-serialized step output
    error = Column(Text, nullable=True)
    attempt = Column(Integer, default=1)

    run = relationship("PipelineRunModel", back_populates="steps")


class PipelineStateModel(Base):
    """Incremental state for fetch steps — high-water marks, cursors (§9.2d)."""

    __tablename__ = "pipeline_state"
    __table_args__ = (
        UniqueConstraint(
            "policy_id",
            "provider_id",
            "data_type",
            "entity_key",
            name="uq_pipeline_state",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False)
    policy = relationship("PolicyModel", back_populates="states")
    provider_id = Column(String(64), nullable=False)
    data_type = Column(String(64), nullable=False)
    entity_key = Column(String(128), nullable=False)
    last_cursor = Column(String(256), nullable=True)
    last_hash = Column(String(64), nullable=True)
    updated_at = Column(DateTime, nullable=False)


class ReportModel(Base):
    """Current version of a generated report (§9.2e)."""

    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False)
    version = Column(Integer, default=1)
    spec_json = Column(Text, nullable=False)  # ReportSpec JSON
    snapshot_json = Column(Text, nullable=True)  # Frozen query results
    snapshot_hash = Column(String(64), nullable=True)  # SHA-256 of snapshot
    format = Column(String(10), nullable=False, default="html")  # "html" | "markdown"
    rendered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(String(128), default="")

    versions = relationship(
        "ReportVersionModel", back_populates="report", cascade="all, delete-orphan"
    )
    deliveries = relationship(
        "ReportDeliveryModel", back_populates="report", cascade="all, delete-orphan"
    )


class ReportVersionModel(Base):
    """Historical versions of a report — populated by trigger (§9.2e)."""

    __tablename__ = "report_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    spec_json = Column(Text, nullable=False)
    snapshot_json = Column(Text, nullable=True)
    snapshot_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False)

    report = relationship("ReportModel", back_populates="versions")


class ReportDeliveryModel(Base):
    """Delivery tracking for rendered reports (§9.2f)."""

    __tablename__ = "report_delivery"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False, index=True)
    channel = Column(String(20), nullable=False)  # "email" | "local_file"
    recipient = Column(String(256), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    dedup_key = Column(String(64), unique=True, nullable=False)  # SHA-256 idempotency

    report = relationship("ReportModel", back_populates="deliveries")


class FetchCacheModel(Base):
    """HTTP response cache for fetch steps (§9.2g)."""

    __tablename__ = "fetch_cache"
    __table_args__ = (
        UniqueConstraint("provider", "data_type", "entity_key", name="uq_fetch_cache"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(64), nullable=False)
    data_type = Column(String(64), nullable=False)
    entity_key = Column(String(128), nullable=False)
    payload_json = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    etag = Column(String(256), nullable=True)
    last_modified = Column(String(128), nullable=True)
    fetched_at = Column(DateTime, nullable=False)
    ttl_seconds = Column(Integer, nullable=False)


class AuditLogModel(Base):
    """Append-only audit trail for pipeline operations (§9.2i)."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(128), nullable=False)  # "scheduler", "mcp:agent", "gui:user"
    action = Column(String(64), nullable=False)  # "policy.create", "pipeline.run"
    resource_type = Column(String(64), nullable=False)  # "policy", "pipeline_run"
    resource_id = Column(String(36), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)


# ── Market Data Models (§9.5a–c, MEU-PW3) ─────────────────────────────────


class MarketOHLCVModel(Base):
    """Historical OHLCV price bars (§9.5a)."""

    __tablename__ = "market_ohlcv"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "timestamp", "provider", name="uq_ohlcv_ticker_ts_provider"
        ),
        Index("ix_ohlcv_ticker_timestamp", "ticker", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Numeric(15, 6), nullable=False)
    high = Column(Numeric(15, 6), nullable=False)
    low = Column(Numeric(15, 6), nullable=False)
    close = Column(Numeric(15, 6), nullable=False)
    volume = Column(Integer, nullable=False)
    vwap = Column(Numeric(15, 6), nullable=True)
    trade_count = Column(Integer, nullable=True)
    adjusted_close = Column(Numeric(15, 6), nullable=True)
    provider = Column(String(32), nullable=False)
    data_type = Column(String(32), nullable=True)
    fetched_at = Column(DateTime, nullable=True)


class MarketQuoteModel(Base):
    """Real-time / delayed quotes (§9.5a)."""

    __tablename__ = "market_quotes"
    __table_args__ = (Index("ix_quote_ticker_timestamp", "ticker", "timestamp"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=False)
    bid = Column(Numeric(15, 6), nullable=True)
    ask = Column(Numeric(15, 6), nullable=True)
    last = Column(Numeric(15, 6), nullable=False)
    volume = Column(Integer, nullable=True)
    change = Column(Numeric(15, 6), nullable=True)
    change_pct = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    provider = Column(String(32), nullable=False)


class MarketNewsModel(Base):
    """Market news articles (§9.5a)."""

    __tablename__ = "market_news"
    __table_args__ = (
        UniqueConstraint("url", "provider", name="uq_news_url_provider"),
        Index("ix_news_ticker_published", "ticker", "published_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=True)
    headline = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String(128), nullable=False)
    url = Column(String(2048), nullable=False)
    published_at = Column(DateTime, nullable=False)
    sentiment = Column(Float, nullable=True)
    provider = Column(String(32), nullable=False)


class MarketFundamentalsModel(Base):
    """Fundamental financial metrics (§9.5a)."""

    __tablename__ = "market_fundamentals"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "metric",
            "period",
            "provider",
            name="uq_fund_ticker_metric_period_provider",
        ),
        Index("ix_fund_ticker_metric", "ticker", "metric"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=False)
    metric = Column(String(64), nullable=False)
    value = Column(Numeric(15, 6), nullable=False)
    period = Column(String(16), nullable=False)
    provider = Column(String(32), nullable=False)
    fetched_at = Column(DateTime, nullable=True)


# ── Market Data Expansion Tables (§8a.2, MEU-183) ────────────────────────


class MarketEarningsModel(Base):
    """Quarterly / annual earnings reports (§8a.2, MEU-183)."""

    __tablename__ = "market_earnings"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "fiscal_period",
            "fiscal_year",
            name="uq_earnings_ticker_period_year",
        ),
        Index("ix_earnings_ticker", "ticker"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=False)
    fiscal_period = Column(String(4), nullable=False)  # Q1, Q2, Q3, Q4, FY
    fiscal_year = Column(Integer, nullable=False)
    report_date = Column(Date, nullable=False)
    eps_actual = Column(Numeric(18, 8), nullable=True)
    eps_estimate = Column(Numeric(18, 8), nullable=True)
    eps_surprise = Column(Numeric(18, 8), nullable=True)
    revenue_actual = Column(Numeric(18, 8), nullable=True)
    revenue_estimate = Column(Numeric(18, 8), nullable=True)
    provider = Column(String(32), nullable=False)


class MarketDividendsModel(Base):
    """Dividend payment records (§8a.2, MEU-183)."""

    __tablename__ = "market_dividends"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "ex_date",
            name="uq_dividends_ticker_exdate",
        ),
        Index("ix_dividends_ticker", "ticker"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=False)
    dividend_amount = Column(Numeric(18, 8), nullable=False)
    currency = Column(String(8), nullable=False)
    ex_date = Column(Date, nullable=False)
    record_date = Column(Date, nullable=True)
    pay_date = Column(Date, nullable=True)
    declaration_date = Column(Date, nullable=True)
    frequency = Column(String(16), nullable=True)  # quarterly, semi-annual, annual
    provider = Column(String(32), nullable=False)


class MarketSplitsModel(Base):
    """Stock split events (§8a.2, MEU-183)."""

    __tablename__ = "market_splits"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "execution_date",
            name="uq_splits_ticker_execdate",
        ),
        Index("ix_splits_ticker", "ticker"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=False)
    execution_date = Column(Date, nullable=False)
    ratio_from = Column(Integer, nullable=False)
    ratio_to = Column(Integer, nullable=False)
    provider = Column(String(32), nullable=False)


class MarketInsiderModel(Base):
    """Insider buy/sell transactions (§8a.2, MEU-183)."""

    __tablename__ = "market_insider"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "name",
            "transaction_date",
            "transaction_code",
            name="uq_insider_ticker_name_date_code",
        ),
        Index("ix_insider_ticker", "ticker"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=False)
    name = Column(String(128), nullable=False)
    title = Column(String(128), nullable=True)
    transaction_date = Column(Date, nullable=False)
    transaction_code = Column(String(4), nullable=False)  # P, S, etc.
    shares = Column(Integer, nullable=False)
    price = Column(Numeric(18, 8), nullable=True)
    value = Column(Numeric(18, 8), nullable=True)
    shares_owned_after = Column(Integer, nullable=True)
    provider = Column(String(32), nullable=False)


# ── Scheduling Triggers (§9.2h, §9.2i) ───────────────────────────────────


def _install_scheduling_triggers(
    target,  # noqa: ANN001
    connection,  # noqa: ANN001
    **_kw,  # noqa: ANN003
) -> None:
    """Install report-versioning and audit-append-only triggers.

    Connected via event.listen(Base.metadata, 'after_create') — Local Canon
    precedent from 2026-03-08-settings-backup plan (no Alembic infrastructure).
    """
    # §9.2h: Report versioning trigger
    connection.execute(
        text(
            """CREATE TRIGGER IF NOT EXISTS reports_version_on_update
            BEFORE UPDATE ON reports
            FOR EACH ROW
            BEGIN
                INSERT INTO report_versions (
                    id, report_id, version, spec_json, snapshot_json,
                    snapshot_hash, created_at
                ) VALUES (
                    lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
                          substr(hex(randomblob(2)),2) || '-' ||
                          substr('89ab', abs(random()) % 4 + 1, 1) ||
                          substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6))),
                    OLD.id, OLD.version, OLD.spec_json, OLD.snapshot_json,
                    OLD.snapshot_hash, datetime('now')
                );
            END;"""
        )
    )

    # §9.2i: Audit log append-only triggers
    connection.execute(
        text(
            """CREATE TRIGGER IF NOT EXISTS audit_no_update
            BEFORE UPDATE ON audit_log
            BEGIN
                SELECT RAISE(ABORT, 'audit_log is append-only: UPDATE not allowed');
            END;"""
        )
    )
    connection.execute(
        text(
            """CREATE TRIGGER IF NOT EXISTS audit_no_delete
            BEFORE DELETE ON audit_log
            BEGIN
                SELECT RAISE(ABORT, 'audit_log is append-only: DELETE not allowed');
            END;"""
        )
    )


event.listen(Base.metadata, "after_create", _install_scheduling_triggers)
