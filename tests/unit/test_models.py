# tests/unit/test_models.py
"""Tests for SQLAlchemy ORM models (MEU-13, AC-13.1 through AC-13.4)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from zorivest_infra.database.models import (
    AccountModel,
    Base,
    ImageModel,
    TradeModel,
    WatchlistItemModel,
    WatchlistModel,
)

# Expected 40 table names from the spec (21 original + 9 scheduling + 1 email_provider + 1 email_templates + 4 market data + 4 Phase 8a market)
EXPECTED_TABLES = {
    "trades",
    "images",
    "accounts",
    "trade_reports",
    "trade_plans",
    "watchlists",
    "watchlist_items",
    "balance_snapshots",
    "settings",
    "app_defaults",
    "market_provider_settings",
    "mcp_guard",
    "round_trips",
    "excursion_metrics",
    "identifier_cache",
    "transaction_ledger",
    "options_strategies",
    "mistake_entries",
    "broker_configs",
    "bank_transactions",
    "bank_import_configs",
    # Phase 9 scheduling tables
    "policies",
    "pipeline_runs",
    "pipeline_steps",
    "pipeline_state",
    "reports",
    "report_versions",
    "report_delivery",
    "fetch_cache",
    "audit_log",
    # MEU-73 email provider
    "email_provider",
    # MEU-PW3 market data
    "market_ohlcv",
    "market_quotes",
    "market_news",
    "market_fundamentals",
    # MEU-PH6 email templates
    "email_templates",
    # Phase 8a market data expansion (MEU-183)
    "market_earnings",
    "market_dividends",
    "market_splits",
    "market_insider",
}


def _engine():
    """Create a fresh in-memory SQLite engine with all tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


class TestSchemaCreation:
    """AC-13.1: All 40 tables are created without errors."""

    def test_create_all_tables(self) -> None:
        engine = _engine()
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())
        assert EXPECTED_TABLES == actual_tables

    def test_exactly_40_tables(self) -> None:
        engine = _engine()
        inspector = inspect(engine)
        assert len(inspector.get_table_names()) == 40


class TestColumnTypes:
    """AC-13.2: Financial columns use Numeric, display columns use Float."""

    def test_trade_commission_is_numeric(self) -> None:
        engine = _engine()
        inspector = inspect(engine)
        cols = {c["name"]: c for c in inspector.get_columns("trades")}
        assert str(cols["commission"]["type"]).startswith("NUMERIC")

    def test_trade_price_is_float(self) -> None:
        engine = _engine()
        inspector = inspect(engine)
        cols = {c["name"]: c for c in inspector.get_columns("trades")}
        assert str(cols["price"]["type"]) == "FLOAT"

    def test_balance_snapshot_balance_is_numeric(self) -> None:
        engine = _engine()
        inspector = inspect(engine)
        cols = {c["name"]: c for c in inspector.get_columns("balance_snapshots")}
        assert str(cols["balance"]["type"]).startswith("NUMERIC")


class TestModelInsert:
    """AC-13.3: Models can be inserted and read back."""

    def test_insert_account_and_trade(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            account = AccountModel(
                account_id="ACC001",
                name="Test Account",
                account_type="broker",
                created_at=datetime(2025, 1, 1),
            )
            session.add(account)

            trade = TradeModel(
                exec_id="E001",
                time=datetime(2025, 1, 15, 10, 30),
                instrument="AAPL",
                action="BOT",
                quantity=100.0,
                price=150.50,
                account_id="ACC001",
            )
            session.add(trade)
            session.commit()

            loaded = session.get(TradeModel, "E001")
            assert loaded is not None
            assert loaded.instrument == "AAPL"  # type: ignore[reportGeneralTypeIssues]
            assert loaded.account_id == "ACC001"  # type: ignore[reportGeneralTypeIssues]

    def test_insert_image(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            img = ImageModel(
                owner_type="trade",
                owner_id="E001",
                data=b"\x00" * 100,
                mime_type="image/webp",
                width=800,
                height=600,
                file_size=100,
                created_at=datetime(2025, 1, 15),
            )
            session.add(img)
            session.commit()
            assert img.id is not None
            # Value: verify fields persisted correctly
            loaded = session.get(ImageModel, img.id)
            assert loaded is not None
            assert loaded.owner_type == "trade"  # type: ignore[reportGeneralTypeIssues]
            assert loaded.owner_id == "E001"  # type: ignore[reportGeneralTypeIssues]
            assert loaded.mime_type == "image/webp"  # type: ignore[reportGeneralTypeIssues]
            assert loaded.width == 800  # type: ignore[reportGeneralTypeIssues]
            assert loaded.height == 600  # type: ignore[reportGeneralTypeIssues]


class TestRelationships:
    """AC-13.4: Relationships are correctly defined."""

    def test_account_trades_relationship(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            account = AccountModel(
                account_id="ACC001",
                name="Test",
                account_type="broker",
                created_at=datetime(2025, 1, 1),
            )
            trade = TradeModel(
                exec_id="E001",
                time=datetime(2025, 1, 15),
                instrument="AAPL",
                action="BOT",
                quantity=100.0,
                price=150.0,
                account_id="ACC001",
            )
            session.add_all([account, trade])
            session.commit()

            loaded_account = session.get(AccountModel, "ACC001")
            assert loaded_account is not None
            assert len(loaded_account.trades) == 1
            assert loaded_account.trades[0].exec_id == "E001"

    def test_watchlist_items_cascade(self) -> None:
        engine = _engine()
        with Session(engine) as session:
            wl = WatchlistModel(
                name="Tech Stocks",
                created_at=datetime(2025, 1, 1),
            )
            wl.items.append(
                WatchlistItemModel(
                    ticker="AAPL",
                    added_at=datetime(2025, 1, 1),
                )
            )
            session.add(wl)
            session.commit()

            loaded = session.get(WatchlistModel, wl.id)
            assert loaded is not None
            assert len(loaded.items) == 1
            assert loaded.items[0].ticker == "AAPL"


class TestMarketProviderSettingModel:
    """MEU-58: MarketProviderSettingModel has encrypted_api_secret column."""

    def test_market_provider_has_encrypted_api_secret_column(self) -> None:
        engine = _engine()
        inspector = inspect(engine)
        cols = {c["name"]: c for c in inspector.get_columns("market_provider_settings")}
        assert "encrypted_api_secret" in cols, (
            f"Missing encrypted_api_secret column, found: {list(cols.keys())}"
        )
        assert cols["encrypted_api_secret"]["nullable"] is True

    def test_market_provider_insert_with_api_secret(self) -> None:
        from zorivest_infra.database.models import MarketProviderSettingModel

        engine = _engine()
        with Session(engine) as session:
            provider = MarketProviderSettingModel(
                provider_name="alpaca",
                encrypted_api_key="ENC:key-data",
                encrypted_api_secret="ENC:secret-data",
                rate_limit=200,
                timeout=30,
                is_enabled=True,
                created_at=datetime(2026, 3, 11),
            )
            session.add(provider)
            session.commit()

            loaded = session.get(MarketProviderSettingModel, "alpaca")
            assert loaded is not None
            assert loaded.encrypted_api_secret == "ENC:secret-data"  # type: ignore[reportGeneralTypeIssues]
