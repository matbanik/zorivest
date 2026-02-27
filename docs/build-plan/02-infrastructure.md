# Phase 2: Infrastructure — Database & Repositories

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 1](01-domain-layer.md), [Phase 1A](01a-logging.md) | Outputs: [Phase 2A](02a-backup-restore.md), [Phase 3](03-service-layer.md)

---

## Goal

Implement concrete SQLCipher database, SQLAlchemy models (including image storage), repository implementations, and the Unit of Work. Test against real SQLite (in-memory for speed).

## Step 2.1: Database Schema (Including Images)

```python
# packages/infrastructure/src/zorivest_infra/database/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, LargeBinary, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class TradeModel(Base):
    __tablename__ = "trades"

    exec_id = Column(String, primary_key=True)
    time = Column(DateTime, nullable=False)
    instrument = Column(String, nullable=False)
    action = Column(String(3), nullable=False)  # BOT or SLD
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    commission = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)

    images = relationship("ImageModel", primaryjoin="and_(ImageModel.owner_type=='trade', foreign(ImageModel.owner_id)==TradeModel.exec_id)", viewonly=True)
    report = relationship("TradeReportModel", back_populates="trade", uselist=False)
    account_rel = relationship("AccountModel", back_populates="trades")


class ImageModel(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_type = Column(String(20), nullable=False, index=True)  # "trade", "report", "plan"
    owner_id = Column(String, nullable=False, index=True)        # FK varies by owner_type
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
    account_type = Column(String(20), nullable=False)    # AccountType enum value
    institution = Column(String, nullable=True)
    currency = Column(String(3), default="USD")
    is_tax_advantaged = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)

    trades = relationship("TradeModel", back_populates="account_rel")
    balance_snapshots = relationship("BalanceSnapshotModel", back_populates="account_rel")


class TradeReportModel(Base):
    __tablename__ = "trade_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String, ForeignKey("trades.exec_id"), unique=True, nullable=False)
    setup_quality = Column(Integer, nullable=True)       # 1-5
    execution_quality = Column(Integer, nullable=True)   # 1-5
    followed_plan = Column(Boolean, nullable=True)
    emotional_state = Column(String, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)                   # JSON array of strings
    created_at = Column(DateTime, nullable=False)

    trade = relationship("TradeModel", back_populates="report")


class TradePlanModel(Base):
    """Future: Forward-looking trade thesis with conviction and strategy."""
    __tablename__ = "trade_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    direction = Column(String(3), nullable=False)         # BOT or SLD
    conviction = Column(String(10), nullable=False)       # ConvictionLevel
    strategy_name = Column(String, nullable=True)
    strategy_description = Column(Text, nullable=True)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    entry_conditions = Column(Text, nullable=True)
    exit_conditions = Column(Text, nullable=True)
    timeframe = Column(String, nullable=True)
    status = Column(String(15), default="draft")          # PlanStatus
    linked_trade_id = Column(String, ForeignKey("trades.exec_id"), nullable=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class WatchlistModel(Base):
    """Future: Named collections of tickers to monitor."""
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)

    items = relationship("WatchlistItemModel", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItemModel(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    ticker = Column(String, nullable=False)
    added_at = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    watchlist = relationship("WatchlistModel", back_populates="items")


class BalanceSnapshotModel(Base):
    __tablename__ = "balance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    datetime = Column(DateTime, nullable=False)
    balance = Column(Float, nullable=False)

    account_rel = relationship("AccountModel", back_populates="balance_snapshots")


class SettingModel(Base):
    """User-level setting overrides (writable by user actions)."""
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text)
    value_type = Column(String(20))
    updated_at = Column(DateTime)

    # Key convention (namespaced dot notation):
    # ui.theme, ui.activePage, ui.panel.*.collapsed, ui.sidebar.width
    # notification.{category}.enabled  (success|info|warning|confirmation)
    # display.dollar_visible, display.percent_visible, display.percent_mode


class AppDefaultModel(Base):
    """Application-level setting defaults. Seeded from code registry during migration.
    See Phase 2A (02a-backup-restore.md) for full default values and resolution logic.
    """
    __tablename__ = "app_defaults"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False)     # "str", "int", "float", "bool", "json"
    category = Column(String(50), nullable=False)        # "dialog", "logging", "display", "backup"
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False)


class MarketProviderSettingModel(Base):
    """Market data API provider credentials and configuration (Phase 8)."""
    __tablename__ = "market_provider_settings"

    provider_name = Column(String, primary_key=True)       # e.g., "Alpha Vantage"
    encrypted_api_key = Column(Text, nullable=True)        # Fernet-encrypted, "ENC:" prefix
    rate_limit = Column(Integer, default=5)                # requests per minute
    timeout = Column(Integer, default=30)                  # seconds
    is_enabled = Column(Boolean, default=False)
    last_tested_at = Column(DateTime, nullable=True)
    last_test_status = Column(String(50), nullable=True)   # "success" | "failed" | "untested"
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
```

### McpGuardModel (MCP Circuit Breaker State)

```python
# zorivest_infra/database/models.py  (continued)

class McpGuardModel(Base):
    """Singleton row — circuit breaker state for MCP tool access."""
    __tablename__ = "mcp_guard"

    id = Column(Integer, primary_key=True, default=1)        # singleton
    is_enabled = Column(Boolean, default=False)               # opt-in; disabled by default
    is_locked = Column(Boolean, default=False)                # True = all MCP tools blocked
    locked_at = Column(DateTime, nullable=True)
    lock_reason = Column(String(100), nullable=True)          # free-text; convention: "manual", "rate_limit_exceeded", "agent_self_lock"
    calls_per_minute_limit = Column(Integer, default=60)
    calls_per_hour_limit = Column(Integer, default=500)
    updated_at = Column(DateTime, nullable=True)
```

> The guard row is seeded during `AppDefaultModel` migration (see [Phase 2A](02a-backup-restore.md)).
> When `is_enabled=False`, the guard middleware is a no-op.

> [!NOTE]
> **Toolset registry state** is managed entirely within the TypeScript MCP server (in-memory `ToolsetRegistry` module). It is **not** persisted in the Python-side database. See [05j-mcp-discovery.md](05j-mcp-discovery.md) for the toolset architecture.

### Build Plan Expansion Models

```python
# zorivest_infra/database/models.py  (continued — Build Plan Expansion entities)

class RoundTripModel(Base):  # §3
    """Groups entry/exit executions into complete round-trips."""
    __tablename__ = "round_trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    instrument = Column(String, nullable=False, index=True)
    direction = Column(String(3), nullable=False)              # BOT (long) or SLD (short)
    entry_exec_ids = Column(Text, nullable=False)              # JSON list of exec_ids
    exit_exec_ids = Column(Text, nullable=True)                # JSON list of exec_ids (null if open)
    entry_avg_price = Column(Float, nullable=False)
    exit_avg_price = Column(Float, nullable=True)
    total_quantity = Column(Float, nullable=False)
    realized_pnl = Column(Float, nullable=True)
    total_commission = Column(Float, default=0.0)
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    status = Column(String(10), default="open")                # RoundTripStatus
    holding_period_seconds = Column(Integer, nullable=True)


class ExcursionMetricsModel(Base):  # §7
    """MFE/MAE/BSO auto-enrichment — 1:1 with Trade."""
    __tablename__ = "excursion_metrics"

    trade_exec_id = Column(String, ForeignKey("trades.exec_id"), primary_key=True)
    mfe_dollars = Column(Float, nullable=True)
    mfe_pct = Column(Float, nullable=True)
    mae_dollars = Column(Float, nullable=True)
    mae_pct = Column(Float, nullable=True)
    bso_pct = Column(Float, nullable=True)
    data_source = Column(String, nullable=True)
    computed_at = Column(DateTime, nullable=True)


class IdentifierCacheModel(Base):  # §5
    """CUSIP/ISIN/SEDOL → ticker resolution cache."""
    __tablename__ = "identifier_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_type = Column(String(10), nullable=False, index=True)   # IdentifierType
    id_value = Column(String(20), nullable=False, index=True)
    ticker = Column(String, nullable=False)
    exchange = Column(String, nullable=True)
    security_type = Column(String, nullable=True)
    source = Column(String, nullable=False)                    # "openfigi", "finnhub", "manual"
    confidence = Column(Float, default=1.0)
    resolved_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)


class TransactionLedgerModel(Base):  # §9
    """Per-trade fee decomposition."""
    __tablename__ = "transaction_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_exec_id = Column(String, ForeignKey("trades.exec_id"), nullable=False, index=True)
    fee_type = Column(String(20), nullable=False)              # FeeType
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    description = Column(Text, nullable=True)


class OptionsStrategyModel(Base):  # §8
    """Multi-leg options grouping."""
    __tablename__ = "options_strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    strategy_type = Column(String(20), nullable=False)         # StrategyType
    underlying = Column(String, nullable=False, index=True)
    leg_exec_ids = Column(Text, nullable=False)                # JSON list of exec_ids
    net_debit_credit = Column(Float, nullable=True)
    max_profit = Column(Float, nullable=True)
    max_loss = Column(Float, nullable=True)
    breakeven_prices = Column(Text, nullable=True)             # JSON list of decimals
    created_at = Column(DateTime, nullable=False)


class MistakeEntryModel(Base):  # §17
    """Trade mistake categorization with cost attribution."""
    __tablename__ = "mistake_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String, ForeignKey("trades.exec_id"), nullable=False, index=True)
    category = Column(String(30), nullable=False)              # MistakeCategory
    estimated_cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    auto_detected = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)


class BrokerConfigModel(Base):  # §23
    """Broker constraint and configuration storage."""
    __tablename__ = "broker_configs"

    broker_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    pdt_rule = Column(Boolean, default=True)
    pdt_threshold = Column(Float, default=25000.0)
    settlement_days = Column(Integer, default=1)               # T+1 for US equities
    max_leverage = Column(Text, nullable=True)                 # JSON dict
    routing_type = Column(String(10), nullable=True)           # RoutingType
    commission_schedule = Column(Text, nullable=True)          # JSON dict
    supported_order_types = Column(Text, nullable=True)        # JSON list
    supported_asset_classes = Column(Text, nullable=True)      # JSON list
    trading_hours = Column(Text, nullable=True)                # JSON dict
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class BankTransactionModel(Base):  # §26
    """Imported bank statement transaction."""
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    post_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(30), nullable=True)               # TransactionCategory
    reference_id = Column(String, nullable=True)
    dedup_hash = Column(String(32), nullable=False, index=True)
    source = Column(String(20), nullable=False)                # BalanceSource
    import_batch_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False)


class BankImportConfigModel(Base):  # §26
    """Bank-specific CSV/OFX column mapping configuration."""
    __tablename__ = "bank_import_configs"

    bank_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String(2), default="US")
    config = Column(Text, nullable=False)                      # YAML or JSON config
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
```

## Step 2.2: Repository Integration Tests

```python
# tests/integration/test_repositories.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from zorivest_infra.database.models import Base, TradeModel, ImageModel
from zorivest_infra.database.repositories import SqlAlchemyTradeRepository, SqlAlchemyImageRepository

@pytest.fixture
def session():
    """In-memory SQLite for fast integration tests."""
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

class TestTradeRepository:
    def test_save_and_get(self, session):
        repo = SqlAlchemyTradeRepository(session)
        trade = make_trade(exec_id="TEST001")
        repo.save(trade)
        session.commit()
        
        found = repo.get("TEST001")
        assert found is not None
        assert found.exec_id == "TEST001"

    def test_duplicate_exec_id_detected(self, session):
        repo = SqlAlchemyTradeRepository(session)
        assert not repo.exists("TEST001")
        repo.save(make_trade(exec_id="TEST001"))
        session.commit()
        assert repo.exists("TEST001")


class TestImageRepository:
    def test_save_and_retrieve_image(self, session):
        trade_repo = SqlAlchemyTradeRepository(session)
        trade_repo.save(make_trade(exec_id="TRADE1"))
        
        img_repo = SqlAlchemyImageRepository(session)
        image_id = img_repo.save("TRADE1", make_stored_image(b"RIFF\x00\x00\x00\x00WEBP_data"))
        session.commit()
        
        retrieved = img_repo.get(image_id)
        assert retrieved is not None
        assert retrieved.data == b"RIFF\x00\x00\x00\x00WEBP_data"
        assert retrieved.data[:4] == b"RIFF"  # WebP magic bytes

    def test_get_images_for_trade(self, session):
        trade_repo = SqlAlchemyTradeRepository(session)
        trade_repo.save(make_trade(exec_id="TRADE1"))
        img_repo = SqlAlchemyImageRepository(session)
        img_repo.save("TRADE1", make_stored_image(b"RIFF\x00\x00\x00\x00WEBP_img1"))
        img_repo.save("TRADE1", make_stored_image(b"RIFF\x00\x00\x00\x00WEBP_img2"))
        img_repo.save("TRADE1", make_stored_image(b"RIFF\x00\x00\x00\x00WEBP_img3"))
        session.commit()

        images = img_repo.get_for_trade("TRADE1")
        assert len(images) == 3

    def test_thumbnail_generation(self, session):
        trade_repo = SqlAlchemyTradeRepository(session)
        trade_repo.save(make_trade(exec_id="TRADE1"))
        img_repo = SqlAlchemyImageRepository(session)
        original_data = b"RIFF\x00\x00\x00\x00WEBP_screenshot_data_here"
        image_id = img_repo.save("TRADE1", make_stored_image(original_data))
        session.commit()
        # get thumbnail
        thumbnail = img_repo.get_thumbnail(image_id, max_size=200)
        assert len(thumbnail) > 0
        assert len(thumbnail) < len(original_data)  # smaller than original
```

## Step 2.3: SQLCipher Connection Factory

```python
# tests/integration/test_database_connection.py

class TestSqlCipherConnection:
    def test_create_encrypted_database(self, tmp_path):
        db_path = tmp_path / "test.db"
        conn = create_encrypted_connection(str(db_path), passphrase="test123")
        # Write something
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        
        # Verify: opening without passphrase fails
        import sqlite3
        raw_conn = sqlite3.connect(str(db_path))
        with pytest.raises(Exception):
            raw_conn.execute("SELECT * FROM test")

    def test_argon2_key_derivation(self):
        key1 = derive_key("password", salt=b"0123456789abcdef")
        key2 = derive_key("password", salt=b"0123456789abcdef")
        assert key1 == key2  # deterministic
        assert len(key1) == 32  # 256-bit
```

## Exit Criteria

**Run `pytest tests/unit/ tests/integration/` — all should pass.**

## Test Plan

| Test File | What It Tests |
|-----------|--------------|
| `tests/integration/test_repositories.py` | Trade + Image repos with in-memory SQLite |
| `tests/integration/test_database_connection.py` | SQLCipher encryption, Argon2 KDF |
| `tests/integration/test_unit_of_work.py` | Transaction commit/rollback |

## Outputs

- All SQLAlchemy models defined (trades, images, accounts, reports, plans, watchlists, settings)
- **Build Plan Expansion models**: round_trips, excursion_metrics, identifier_cache, transaction_ledger, options_strategies, mistake_entries, broker_configs, bank_transactions, bank_import_configs
- Repository implementations passing integration tests
- SQLCipher connection factory with Argon2 key derivation
- Unit of Work implementation

