# Phase 2: Infrastructure — Database & Repositories

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 1](01-domain-layer.md) | Outputs: [Phase 3](03-service-layer.md)

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
    mime_type = Column(String(50), default="image/png")
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
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text)
    value_type = Column(String(20))
    updated_at = Column(DateTime)


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
        image_id = img_repo.save("TRADE1", make_image(b"\x89PNG_fake_data"))
        session.commit()
        
        retrieved = img_repo.get(image_id)
        assert retrieved is not None
        assert retrieved.data == b"\x89PNG_fake_data"

    def test_get_images_for_trade(self, session):
        trade_repo = SqlAlchemyTradeRepository(session)
        trade_repo.save(make_trade(exec_id="TRADE1"))
        img_repo = SqlAlchemyImageRepository(session)
        img_repo.save("TRADE1", make_image(b"\x89PNG_img1"))
        img_repo.save("TRADE1", make_image(b"\x89PNG_img2"))
        img_repo.save("TRADE1", make_image(b"\x89PNG_img3"))
        session.commit()

        images = img_repo.get_for_trade("TRADE1")
        assert len(images) == 3

    def test_thumbnail_generation(self, session):
        trade_repo = SqlAlchemyTradeRepository(session)
        trade_repo.save(make_trade(exec_id="TRADE1"))
        img_repo = SqlAlchemyImageRepository(session)
        original_data = b"\x89PNG_screenshot_data_here"
        image_id = img_repo.save("TRADE1", make_image(original_data))
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
- Repository implementations passing integration tests
- SQLCipher connection factory with Argon2 key derivation
- Unit of Work implementation
