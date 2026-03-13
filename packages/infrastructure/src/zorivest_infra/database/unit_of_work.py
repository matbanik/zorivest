# pyright: reportArgumentType=false, reportReturnType=false, reportGeneralTypeIssues=false
# SQLAlchemy Column/Session types need suppression for Column[T] → T assignments.

"""SqlAlchemy Unit of Work implementation.

Source: 02-infrastructure.md §2.2, ports.py UnitOfWork Protocol
Provides transactional boundary with 5 repository attributes.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from zorivest_infra.database.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyAppDefaultsRepository,
    SqlAlchemyBalanceSnapshotRepository,
    SqlAlchemyImageRepository,
    SqlAlchemyRoundTripRepository,
    SqlAlchemySettingsRepository,
    SqlAlchemyTradePlanRepository,
    SqlAlchemyTradeReportRepository,
    SqlAlchemyTradeRepository,
    SqlMarketProviderSettingsRepository,
)


class SqlAlchemyUnitOfWork:
    """Concrete UnitOfWork backed by SQLAlchemy Session.

    Usage::

        uow = SqlAlchemyUnitOfWork(engine)
        with uow:
            uow.trades.save(trade)
            uow.commit()
    """

    trades: SqlAlchemyTradeRepository
    images: SqlAlchemyImageRepository
    accounts: SqlAlchemyAccountRepository
    balance_snapshots: SqlAlchemyBalanceSnapshotRepository
    round_trips: SqlAlchemyRoundTripRepository
    settings: SqlAlchemySettingsRepository
    app_defaults: SqlAlchemyAppDefaultsRepository
    market_provider_settings: SqlMarketProviderSettingsRepository
    trade_reports: SqlAlchemyTradeReportRepository  # MEU-52
    trade_plans: SqlAlchemyTradePlanRepository      # MEU-66

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._session_factory = sessionmaker(bind=engine)
        self._session: Session | None = None

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.trades = SqlAlchemyTradeRepository(self._session)
        self.images = SqlAlchemyImageRepository(self._session)
        self.accounts = SqlAlchemyAccountRepository(self._session)
        self.balance_snapshots = SqlAlchemyBalanceSnapshotRepository(self._session)
        self.round_trips = SqlAlchemyRoundTripRepository(self._session)
        self.settings = SqlAlchemySettingsRepository(self._session)
        self.app_defaults = SqlAlchemyAppDefaultsRepository(self._session)
        self.market_provider_settings = SqlMarketProviderSettingsRepository(self._session)
        self.trade_reports = SqlAlchemyTradeReportRepository(self._session)  # MEU-52
        self.trade_plans = SqlAlchemyTradePlanRepository(self._session)      # MEU-66
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self._session is not None:
            if exc_type is not None:
                self._session.rollback()
            self._session.close()
            self._session = None

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session is not None:
            self._session.rollback()


def create_engine_with_wal(url: str, **kwargs: Any) -> Engine:
    """Create a SQLAlchemy engine with WAL mode enabled.

    Per 02-infrastructure.md spec:
    - WAL journaling for concurrent read/write
    - NORMAL synchronous for performance
    - check_same_thread=False for multi-thread access
    """
    connect_args = kwargs.pop("connect_args", {})
    connect_args.setdefault("check_same_thread", False)

    engine = create_engine(url, connect_args=connect_args, **kwargs)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(dbapi_conn: Any, connection_record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=wal")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    return engine
