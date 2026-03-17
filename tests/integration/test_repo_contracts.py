# tests/integration/test_repo_contracts.py
"""Repository contract tests — abstract CRUD + edge-case suite.

Each concrete repository is tested against a shared contract that verifies:
1. save + get round-trip preserves all fields
2. get(missing_id) returns None
3. list_all returns all saved entities
4. delete removes the entity
5. delete(nonexistent) is a no-op (no exception)
6. update replaces field values

These complement the existing test_repositories.py by using a structured,
parameterized pattern that's easy to extend for new repositories.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from sqlalchemy.orm import Session

from zorivest_core.domain.entities import (
    Account,
    ImageAttachment,
    Trade,
    TradePlan,
    TradeReport,
)
from zorivest_core.domain.enums import (
    AccountType,
    ImageOwnerType,
    TradeAction,
)
from zorivest_core.domain.market_provider_settings import MarketProviderSettings
from zorivest_infra.database.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyImageRepository,
    SqlAlchemyTradePlanRepository,
    SqlAlchemyTradeReportRepository,
    SqlAlchemyTradeRepository,
    SqlMarketProviderSettingsRepository,
)


# ── Entity factories ────────────────────────────────────────────────────


def _account(account_id: str = "ACC001") -> Account:
    return Account(
        account_id=account_id,
        name="Test Account",
        account_type=AccountType.BROKER,
    )


def _trade(exec_id: str = "E001", account_id: str = "ACC001") -> Trade:
    return Trade(
        exec_id=exec_id,
        time=datetime(2026, 3, 15, 10, 30, 0),
        instrument="AAPL",
        action=TradeAction.BOT,
        quantity=100.0,
        price=150.50,
        account_id=account_id,
    )


def _plan(ticker: str = "AAPL") -> TradePlan:
    return TradePlan(
        id=0,
        ticker=ticker,
        direction="BOT",
        conviction="high",
        strategy_name="Gap & Go",
        strategy_description="Long after gap up",
        entry_price=200.0,
        stop_loss=195.0,
        target_price=215.0,
        entry_conditions="Gap > 2%",
        exit_conditions="Target hit or EOD",
        timeframe="intraday",
        risk_reward_ratio=3.0,
        status="draft",
        created_at=datetime(2026, 3, 12),
        updated_at=datetime(2026, 3, 12),
    )


def _report(trade_id: str = "E001") -> TradeReport:
    return TradeReport(
        id=0,
        trade_id=trade_id,
        setup_quality=4,
        execution_quality=3,
        followed_plan=True,
        emotional_state="confident",
        created_at=datetime(2026, 3, 12, 10, 30, 0),
        lessons_learned="Good entry timing",
    )


def _market_settings(name: str = "Alpha Vantage") -> MarketProviderSettings:
    return MarketProviderSettings(
        provider_name=name,
        encrypted_api_key="ENC:abc123",
        rate_limit=5,
        timeout=30,
        is_enabled=True,
        created_at=datetime(2026, 3, 12),
    )


def _image() -> ImageAttachment:
    return ImageAttachment(
        id=0,
        owner_type=ImageOwnerType.TRADE,
        owner_id="E001",
        data=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
        width=800,
        height=600,
        file_size=108,
        created_at=datetime(2026, 3, 12),
    )


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def _with_account(db_session: Session) -> None:
    """Ensure an account exists for FK constraints."""
    repo = SqlAlchemyAccountRepository(db_session)
    repo.save(_account("ACC001"))
    db_session.flush()


@pytest.fixture()
def _with_trade(db_session: Session, _with_account: None) -> None:
    """Ensure a trade exists for FK constraints."""
    repo = SqlAlchemyTradeRepository(db_session)
    repo.save(_trade("E001"))
    db_session.flush()


# ── Trade Repository Contract ───────────────────────────────────────────


class TestTradeRepoContract:
    """Contract tests for SqlAlchemyTradeRepository."""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session: Session, _with_account: None) -> None:
        self.session = db_session
        self.repo = SqlAlchemyTradeRepository(db_session)

    def test_save_and_get_roundtrip(self) -> None:
        trade = _trade("E010")
        self.repo.save(trade)
        self.session.flush()

        found = self.repo.get("E010")
        assert found is not None
        assert found.exec_id == "E010"
        assert found.instrument == "AAPL"
        assert found.action == TradeAction.BOT
        assert found.quantity == 100.0
        assert found.price == 150.50
        assert found.account_id == "ACC001"

    def test_get_missing_returns_none(self) -> None:
        assert self.repo.get("NONEXISTENT") is None

    def test_list_all(self) -> None:
        self.repo.save(_trade("E010"))
        self.repo.save(_trade("E011"))
        self.repo.save(_trade("E012"))
        self.session.flush()

        trades = self.repo.list_all()
        assert len(trades) == 3
        exec_ids = {t.exec_id for t in trades}
        assert exec_ids == {"E010", "E011", "E012"}

    def test_delete_removes(self) -> None:
        self.repo.save(_trade("E010"))
        self.session.flush()

        self.repo.delete("E010")
        self.session.flush()
        assert self.repo.get("E010") is None

    def test_delete_nonexistent_noop(self) -> None:
        self.repo.delete("NONEXISTENT")  # Should not raise

    def test_update_replaces(self) -> None:
        self.repo.save(_trade("E010"))
        self.session.flush()

        updated = Trade(
            exec_id="E010",
            time=datetime(2026, 3, 15, 10, 30, 0),
            instrument="AAPL",
            action=TradeAction.SLD,  # Changed
            quantity=200.0,          # Changed
            price=155.00,            # Changed
            account_id="ACC001",
        )
        self.repo.update(updated)
        self.session.flush()

        found = self.repo.get("E010")
        assert found is not None
        assert found.action == TradeAction.SLD
        assert found.quantity == 200.0
        assert found.price == 155.00

    def test_list_filtered_by_account(self) -> None:
        acct_repo = SqlAlchemyAccountRepository(self.session)
        acct_repo.save(_account("ACC002"))
        self.session.flush()

        self.repo.save(_trade("E010", account_id="ACC001"))
        self.repo.save(_trade("E011", account_id="ACC002"))
        self.session.flush()

        acc1 = self.repo.list_for_account("ACC001")
        assert len(acc1) == 1
        assert acc1[0].exec_id == "E010"

    def test_exists_true_and_false(self) -> None:
        assert not self.repo.exists("E010")
        self.repo.save(_trade("E010"))
        self.session.flush()
        assert self.repo.exists("E010")


# ── Account Repository Contract ─────────────────────────────────────────


class TestAccountRepoContract:
    """Contract tests for SqlAlchemyAccountRepository."""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session: Session) -> None:
        self.session = db_session
        self.repo = SqlAlchemyAccountRepository(db_session)

    def test_save_and_get_roundtrip(self) -> None:
        self.repo.save(_account("ACC010"))
        self.session.flush()

        found = self.repo.get("ACC010")
        assert found is not None
        assert found.account_id == "ACC010"
        assert found.name == "Test Account"
        assert found.account_type == AccountType.BROKER

    def test_get_missing_returns_none(self) -> None:
        assert self.repo.get("NONEXISTENT") is None

    def test_list_all(self) -> None:
        self.repo.save(_account("ACC010"))
        self.repo.save(_account("ACC011"))
        self.session.flush()

        accounts = self.repo.list_all()
        assert len(accounts) == 2
        ids = {a.account_id for a in accounts}
        assert ids == {"ACC010", "ACC011"}

    def test_delete_removes(self) -> None:
        self.repo.save(_account("ACC010"))
        self.session.flush()

        self.repo.delete("ACC010")
        self.session.flush()
        assert self.repo.get("ACC010") is None

    def test_delete_nonexistent_noop(self) -> None:
        self.repo.delete("NONEXISTENT")  # Should not raise

    def test_update_replaces(self) -> None:
        self.repo.save(_account("ACC010"))
        self.session.flush()

        updated = Account(
            account_id="ACC010",
            name="Updated Account",
            account_type=AccountType.BANK,
        )
        self.repo.update(updated)
        self.session.flush()

        found = self.repo.get("ACC010")
        assert found is not None
        assert found.name == "Updated Account"
        assert found.account_type == AccountType.BANK


# ── TradePlan Repository Contract ───────────────────────────────────────


class TestTradePlanRepoContract:
    """Contract tests for SqlAlchemyTradePlanRepository."""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session: Session) -> None:
        self.session = db_session
        self.repo = SqlAlchemyTradePlanRepository(db_session)

    def test_save_and_get_roundtrip(self) -> None:
        plan = _plan("AAPL")
        self.repo.save(plan)
        self.session.flush()

        found = self.repo.get(plan.id)
        assert found is not None
        assert found.ticker == "AAPL"
        assert found.direction == "BOT"
        assert found.conviction == "high"
        assert found.entry_price == 200.0
        assert found.stop_loss == 195.0
        assert found.target_price == 215.0
        assert found.risk_reward_ratio == 3.0
        assert found.status == "draft"

    def test_get_missing_returns_none(self) -> None:
        assert self.repo.get(99999) is None

    def test_list_all(self) -> None:
        for ticker in ["AAPL", "MSFT", "GOOG"]:
            self.repo.save(_plan(ticker))
        self.session.flush()

        plans = self.repo.list_all()
        assert len(plans) == 3

    def test_delete_removes(self) -> None:
        plan = _plan("SPY")
        self.repo.save(plan)
        self.session.flush()
        plan_id = plan.id

        self.repo.delete(plan_id)
        self.session.flush()
        assert self.repo.get(plan_id) is None

    def test_delete_nonexistent_noop(self) -> None:
        self.repo.delete(99999)  # Should not raise

    def test_update_replaces(self) -> None:
        plan = _plan("AAPL")
        self.repo.save(plan)
        self.session.flush()

        from dataclasses import replace
        updated = replace(plan, status="active", conviction="max")
        self.repo.update(updated)
        self.session.flush()

        found = self.repo.get(plan.id)
        assert found is not None
        assert found.status == "active"
        assert found.conviction == "max"


# ── TradeReport Repository Contract ─────────────────────────────────────


class TestTradeReportRepoContract:
    """Contract tests for SqlAlchemyTradeReportRepository."""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session: Session, _with_trade: None) -> None:
        self.session = db_session
        self.repo = SqlAlchemyTradeReportRepository(db_session)

    def test_save_and_get_roundtrip(self) -> None:
        report = _report("E001")
        self.repo.save(report)
        self.session.flush()

        found = self.repo.get_for_trade("E001")
        assert found is not None
        assert found.trade_id == "E001"
        assert found.setup_quality == 4
        assert found.execution_quality == 3
        assert found.followed_plan is True
        assert found.emotional_state == "confident"
        assert found.lessons_learned == "Good entry timing"

    def test_get_missing_returns_none(self) -> None:
        assert self.repo.get_for_trade("NONEXISTENT") is None

    def test_delete_removes(self) -> None:
        report = _report("E001")
        self.repo.save(report)
        self.session.flush()

        saved = self.repo.get_for_trade("E001")
        assert saved is not None
        self.repo.delete(saved.id)
        self.session.flush()

        assert self.repo.get_for_trade("E001") is None

    def test_update_replaces(self) -> None:
        report = _report("E001")
        self.repo.save(report)
        self.session.flush()

        saved = self.repo.get_for_trade("E001")
        assert saved is not None

        updated = TradeReport(
            id=saved.id,
            trade_id="E001",
            setup_quality=5,
            execution_quality=5,
            followed_plan=False,
            emotional_state="anxious",
            created_at=saved.created_at,
            lessons_learned="Updated after review",
        )
        self.repo.update(updated)
        self.session.flush()

        found = self.repo.get_for_trade("E001")
        assert found is not None
        assert found.setup_quality == 5
        assert found.followed_plan is False
        assert found.lessons_learned == "Updated after review"


# ── MarketProviderSettings Repository Contract ──────────────────────────


class TestMarketProviderSettingsRepoContract:
    """Contract tests for SqlMarketProviderSettingsRepository."""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session: Session) -> None:
        self.session = db_session
        self.repo = SqlMarketProviderSettingsRepository(db_session)

    def test_save_and_get_roundtrip(self) -> None:
        self.repo.save(_market_settings("Alpha Vantage"))
        self.session.flush()

        found = self.repo.get("Alpha Vantage")
        assert found is not None
        assert found.provider_name == "Alpha Vantage"
        assert found.encrypted_api_key == "ENC:abc123"
        assert found.rate_limit == 5
        assert found.timeout == 30
        assert found.is_enabled is True

    def test_get_missing_returns_none(self) -> None:
        assert self.repo.get("Nonexistent") is None

    def test_list_all(self) -> None:
        for name in ["Alpha Vantage", "Finnhub", "Tradier"]:
            self.repo.save(_market_settings(name))
        self.session.flush()

        results = self.repo.list_all()
        assert len(results) == 3
        names = {r.provider_name for r in results}
        assert names == {"Alpha Vantage", "Finnhub", "Tradier"}

    def test_delete_removes(self) -> None:
        self.repo.save(_market_settings("Finnhub"))
        self.session.flush()

        self.repo.delete("Finnhub")
        self.session.flush()
        assert self.repo.get("Finnhub") is None

    def test_delete_nonexistent_noop(self) -> None:
        self.repo.delete("Nonexistent")  # Should not raise

    def test_save_updates_existing(self) -> None:
        """Save with same PK should upsert (merge semantics)."""
        self.repo.save(_market_settings("Alpha Vantage"))
        self.session.flush()

        updated = MarketProviderSettings(
            provider_name="Alpha Vantage",
            encrypted_api_key="ENC:xyz789",
            rate_limit=60,
            timeout=60,
            is_enabled=False,
            created_at=datetime(2026, 3, 12),
        )
        self.repo.save(updated)
        self.session.flush()

        found = self.repo.get("Alpha Vantage")
        assert found is not None
        assert found.encrypted_api_key == "ENC:xyz789"
        assert found.rate_limit == 60
        assert found.is_enabled is False


# ── Image Repository Contract ───────────────────────────────────────────


class TestImageRepoContract:
    """Contract tests for SqlAlchemyImageRepository."""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session: Session) -> None:
        self.session = db_session
        self.repo = SqlAlchemyImageRepository(db_session)

    def test_save_and_get_roundtrip(self) -> None:
        img = _image()
        image_id = self.repo.save("trade", "E001", img)
        self.session.flush()

        found = self.repo.get(image_id)
        assert found is not None
        assert found.data == img.data
        assert found.width == 800
        assert found.height == 600
        assert found.file_size == 108

    def test_get_missing_returns_none(self) -> None:
        assert self.repo.get(99999) is None

    def test_get_for_owner(self) -> None:
        self.repo.save("trade", "E001", _image())
        self.repo.save("trade", "E001", _image())
        self.repo.save("trade", "E002", _image())
        self.session.flush()

        images = self.repo.get_for_owner("trade", "E001")
        assert len(images) == 2

    def test_delete_removes(self) -> None:
        image_id = self.repo.save("trade", "E001", _image())
        self.session.flush()

        self.repo.delete(image_id)
        self.session.flush()
        assert self.repo.get(image_id) is None

    def test_delete_nonexistent_noop(self) -> None:
        self.repo.delete(99999)  # Should not raise

    def test_thumbnail_returns_data(self) -> None:
        image_id = self.repo.save("trade", "E001", _image())
        self.session.flush()

        thumb = self.repo.get_thumbnail(image_id, max_size=50)
        assert len(thumb) > 0

    def test_full_data_returns_bytes(self) -> None:
        img = _image()
        image_id = self.repo.save("trade", "E001", img)
        self.session.flush()

        data = self.repo.get_full_data(image_id)
        assert data == img.data
