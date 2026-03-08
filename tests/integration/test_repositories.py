# tests/integration/test_repositories.py
"""Integration tests for SQLAlchemy repository implementations (MEU-14)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from zorivest_core.domain.entities import (
    Account,
    BalanceSnapshot,
    ImageAttachment,
    Trade,
)
from zorivest_core.domain.enums import (
    AccountType,
    ImageOwnerType,
    TradeAction,
)
from zorivest_core.domain.trades.identity import trade_fingerprint
from zorivest_infra.database.models import Base
from zorivest_infra.database.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyBalanceSnapshotRepository,
    SqlAlchemyImageRepository,
    SqlAlchemyRoundTripRepository,
    SqlAlchemyTradeRepository,
)


@pytest.fixture()
def session():
    """In-memory SQLite for fast integration tests."""
    engine = create_engine(
        "sqlite://", echo=False, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    with Session(engine) as sess:
        yield sess


def _make_trade(exec_id: str = "E001", instrument: str = "AAPL") -> Trade:
    return Trade(
        exec_id=exec_id,
        time=datetime.now(),  # must be recent for fingerprint lookback
        instrument=instrument,
        action=TradeAction.BOT,
        quantity=100.0,
        price=150.50,
        account_id="ACC001",
    )


def _make_account(account_id: str = "ACC001") -> Account:
    return Account(
        account_id=account_id,
        name="Test Account",
        account_type=AccountType.BROKER,
    )


def _make_image() -> ImageAttachment:
    return ImageAttachment(
        id=0,
        owner_type=ImageOwnerType.TRADE,
        owner_id="E001",
        data=b"\x00" * 100,
        width=800,
        height=600,
        file_size=100,
        created_at=datetime(2025, 1, 15),
    )


class TestTradeRepository:
    """AC-14.1 through AC-14.4."""

    def test_save_and_get(self, session: Session) -> None:
        """AC-14.1: save + get round-trip."""
        # First create account (FK dependency)
        acct_repo = SqlAlchemyAccountRepository(session)
        acct_repo.save(_make_account())
        session.flush()

        repo = SqlAlchemyTradeRepository(session)
        repo.save(_make_trade())
        session.commit()

        found = repo.get("E001")
        assert found is not None
        assert found.exec_id == "E001"
        assert found.instrument == "AAPL"

    def test_exists(self, session: Session) -> None:
        """AC-14.2: exists check."""
        acct_repo = SqlAlchemyAccountRepository(session)
        acct_repo.save(_make_account())
        session.flush()

        repo = SqlAlchemyTradeRepository(session)
        assert not repo.exists("E001")
        repo.save(_make_trade())
        session.commit()
        assert repo.exists("E001")

    def test_list_all(self, session: Session) -> None:
        acct_repo = SqlAlchemyAccountRepository(session)
        acct_repo.save(_make_account())
        session.flush()

        repo = SqlAlchemyTradeRepository(session)
        repo.save(_make_trade("E001"))
        repo.save(_make_trade("E002"))
        session.commit()

        trades = repo.list_all()
        assert len(trades) == 2

    def test_list_for_account(self, session: Session) -> None:
        """AC-14.3: list_for_account filters by account_id."""
        acct_repo = SqlAlchemyAccountRepository(session)
        acct_repo.save(_make_account("ACC001"))
        acct_repo.save(_make_account("ACC002"))
        session.flush()

        repo = SqlAlchemyTradeRepository(session)
        t1 = _make_trade("E001")
        t2 = Trade(
            exec_id="E002", time=datetime(2025, 1, 16),
            instrument="MSFT", action=TradeAction.BOT,
            quantity=50.0, price=300.0, account_id="ACC002",
        )
        repo.save(t1)
        repo.save(t2)
        session.commit()

        acc1_trades = repo.list_for_account("ACC001")
        assert len(acc1_trades) == 1
        assert acc1_trades[0].exec_id == "E001"

    def test_exists_by_fingerprint_since(self, session: Session) -> None:
        """AC-14.4: fingerprint dedup within lookback window."""
        acct_repo = SqlAlchemyAccountRepository(session)
        acct_repo.save(_make_account())
        session.flush()

        repo = SqlAlchemyTradeRepository(session)
        trade = _make_trade()
        fp = trade_fingerprint(trade)

        assert not repo.exists_by_fingerprint_since(fp)
        repo.save(trade)
        session.commit()
        assert repo.exists_by_fingerprint_since(fp)


class TestImageRepository:
    """AC-14.5, AC-14.6."""

    def test_save_and_get(self, session: Session) -> None:
        """AC-14.5: save + get image round-trip."""
        repo = SqlAlchemyImageRepository(session)
        image_id = repo.save("trade", "E001", _make_image())
        session.commit()

        found = repo.get(image_id)
        assert found is not None
        assert found.data == b"\x00" * 100

    def test_get_for_owner(self, session: Session) -> None:
        """AC-14.6: get_for_owner returns images for owner."""
        repo = SqlAlchemyImageRepository(session)
        repo.save("trade", "E001", _make_image())
        repo.save("trade", "E001", _make_image())
        session.commit()

        images = repo.get_for_owner("trade", "E001")
        assert len(images) == 2

    def test_delete(self, session: Session) -> None:
        repo = SqlAlchemyImageRepository(session)
        image_id = repo.save("trade", "E001", _make_image())
        session.commit()

        repo.delete(image_id)
        session.commit()

        assert repo.get(image_id) is None

    def test_get_thumbnail(self, session: Session) -> None:
        repo = SqlAlchemyImageRepository(session)
        image_id = repo.save("trade", "E001", _make_image())
        session.commit()

        thumb = repo.get_thumbnail(image_id, max_size=50)
        assert len(thumb) > 0
        assert len(thumb) <= 100  # at most full data size


class TestAccountRepository:
    """AC-14.7."""

    def test_save_and_get(self, session: Session) -> None:
        repo = SqlAlchemyAccountRepository(session)
        repo.save(_make_account())
        session.commit()

        found = repo.get("ACC001")
        assert found is not None
        assert found.name == "Test Account"
        assert found.account_type == AccountType.BROKER

    def test_list_all(self, session: Session) -> None:
        repo = SqlAlchemyAccountRepository(session)
        repo.save(_make_account("ACC001"))
        repo.save(_make_account("ACC002"))
        session.commit()

        accounts = repo.list_all()
        assert len(accounts) == 2


class TestBalanceSnapshotRepository:
    """AC-14.8."""

    def test_save_and_list_for_account(self, session: Session) -> None:
        acct_repo = SqlAlchemyAccountRepository(session)
        acct_repo.save(_make_account())
        session.flush()

        repo = SqlAlchemyBalanceSnapshotRepository(session)
        snapshot = BalanceSnapshot(
            id=0,
            account_id="ACC001",
            datetime=datetime(2025, 1, 15),
            balance=Decimal("50000.00"),
        )
        repo.save(snapshot)
        session.commit()

        results = repo.list_for_account("ACC001")
        assert len(results) == 1
        assert results[0].balance == Decimal("50000")


class TestRoundTripRepository:
    """AC-14.9."""

    def test_save_and_list_for_account(self, session: Session) -> None:
        acct_repo = SqlAlchemyAccountRepository(session)
        acct_repo.save(_make_account())
        session.flush()

        repo = SqlAlchemyRoundTripRepository(session)
        rt = {
            "account_id": "ACC001",
            "instrument": "AAPL",
            "direction": "BOT",
            "trades": ["E001", "E002"],
        }
        repo.save(rt)
        session.commit()

        results = repo.list_for_account("ACC001")
        assert len(results) == 1
        assert results[0].instrument == "AAPL"
