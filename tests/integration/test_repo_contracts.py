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

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from zorivest_core.domain.entities import (
    Account,
    BalanceSnapshot,
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
    SqlAlchemyBalanceSnapshotRepository,
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
            quantity=200.0,  # Changed
            price=155.00,  # Changed
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

    def test_fk_rejects_orphan_account_id(self) -> None:
        """AC-7: Trade with non-existent account_id raises IntegrityError.

        SQLite PRAGMA foreign_keys must be set at connection time, before
        any transaction. We create a dedicated engine with FK enforcement
        enabled from the start, bypassing the shared test fixture.
        """
        from sqlalchemy import create_engine, event as sa_event
        from zorivest_infra.database.models import Base as _Base

        fk_engine = create_engine(
            "sqlite://", echo=False, connect_args={"check_same_thread": False}
        )

        @sa_event.listens_for(fk_engine, "connect")
        def _enable_fk(dbapi_conn, _rec):  # type: ignore[no-untyped-def]
            dbapi_conn.execute("PRAGMA foreign_keys = ON")

        _Base.metadata.create_all(fk_engine)

        with fk_engine.connect() as conn:
            session = Session(bind=conn)
            # Create the parent account first (ACC001 exists for other trades)
            # Intentionally do NOT create NONEXISTENT_ACCOUNT
            repo = SqlAlchemyTradeRepository(session)
            orphan_trade = _trade("E999", account_id="NONEXISTENT_ACCOUNT")
            repo.save(orphan_trade)
            with pytest.raises(IntegrityError):
                session.flush()
            session.rollback()
            session.close()
        fk_engine.dispose()


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


# ── BalanceSnapshot Repository Contract (MEU-71) ────────────────────────


class TestBalanceSnapshotRepoContract:
    """Contract tests for SqlAlchemyBalanceSnapshotRepository (MEU-71 AC-4, AC-7)."""

    @pytest.fixture(autouse=True)
    def _setup(self, db_session: Session, _with_account: None) -> None:
        self.session = db_session
        self.repo = SqlAlchemyBalanceSnapshotRepository(db_session)

    def _snap(
        self, account_id: str = "ACC001", month: int = 1, balance: float = 50000.0
    ) -> BalanceSnapshot:
        from decimal import Decimal

        return BalanceSnapshot(
            id=0,
            account_id=account_id,
            datetime=datetime(2025, month, 15),
            balance=Decimal(str(balance)),
        )

    def test_save_and_list_roundtrip(self) -> None:
        """AC-4: save + list_for_account preserves data."""
        self.repo.save(self._snap(month=1, balance=50000.0))
        self.repo.save(self._snap(month=2, balance=52000.0))
        self.session.flush()

        snapshots = self.repo.list_for_account("ACC001")
        assert len(snapshots) == 2
        # Newest first
        assert float(snapshots[0].balance) == 52000.0
        assert float(snapshots[1].balance) == 50000.0

    def test_get_latest_returns_most_recent(self) -> None:
        """AC-4: get_latest returns the most recent snapshot."""
        self.repo.save(self._snap(month=1, balance=50000.0))
        self.repo.save(self._snap(month=3, balance=55000.0))
        self.repo.save(self._snap(month=2, balance=52000.0))
        self.session.flush()

        latest = self.repo.get_latest("ACC001")
        assert latest is not None
        assert float(latest.balance) == 55000.0

    def test_get_latest_returns_none_when_empty(self) -> None:
        """AC-4: get_latest returns None for account with no snapshots."""
        latest = self.repo.get_latest("ACC001")
        assert latest is None

    def test_list_for_account_pagination(self) -> None:
        """AC-7: list_for_account respects limit/offset."""
        for month in range(1, 6):
            self.repo.save(self._snap(month=month, balance=50000.0 + month * 1000))
        self.session.flush()

        page1 = self.repo.list_for_account("ACC001", limit=2, offset=0)
        assert len(page1) == 2
        # Newest first — months 5, 4
        assert float(page1[0].balance) == 55000.0
        assert float(page1[1].balance) == 54000.0

        page2 = self.repo.list_for_account("ACC001", limit=2, offset=2)
        assert len(page2) == 2
        # Months 3, 2
        assert float(page2[0].balance) == 53000.0
        assert float(page2[1].balance) == 52000.0

    def test_count_for_account(self) -> None:
        """AC-7: count_for_account returns total count."""
        for month in range(1, 4):
            self.repo.save(self._snap(month=month))
        self.session.flush()

        assert self.repo.count_for_account("ACC001") == 3
        assert self.repo.count_for_account("NONEXISTENT") == 0

    def test_list_for_account_isolates_accounts(self) -> None:
        """AC-7: snapshots are isolated per account."""
        # Add second account
        acct_repo = SqlAlchemyAccountRepository(self.session)
        acct_repo.save(
            Account(
                account_id="ACC002",
                name="Other",
                account_type=AccountType.BANK,
            )
        )
        self.session.flush()

        self.repo.save(self._snap(account_id="ACC001", month=1))
        self.repo.save(self._snap(account_id="ACC002", month=2))
        self.session.flush()

        acc1 = self.repo.list_for_account("ACC001")
        acc2 = self.repo.list_for_account("ACC002")
        assert len(acc1) == 1
        assert len(acc2) == 1
        assert acc1[0].account_id == "ACC001"
        assert acc2[0].account_id == "ACC002"


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
