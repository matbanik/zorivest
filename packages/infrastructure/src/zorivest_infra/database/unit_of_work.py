# pyright: reportArgumentType=false, reportReturnType=false, reportGeneralTypeIssues=false
# SQLAlchemy Column/Session types need suppression for Column[T] → T assignments.

"""SqlAlchemy Unit of Work implementation.

Source: 02-infrastructure.md §2.2, 09-scheduling.md §9.2j
Provides transactional boundary with 18 repository attributes.
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
from zorivest_infra.database.scheduling_repositories import (
    AuditLogRepository,
    DeliveryRepository,
    FetchCacheRepository,
    PipelineRunRepository,
    PipelineStateRepository,
    PolicyRepository,
    ReportRepository,
)
from zorivest_infra.database.watchlist_repository import (
    SqlAlchemyWatchlistRepository,
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
    # Scheduling repos (MEU-82)
    policies: PolicyRepository
    pipeline_runs: PipelineRunRepository
    reports: ReportRepository
    fetch_cache: FetchCacheRepository
    pipeline_state: PipelineStateRepository  # MEU-85
    audit_log: AuditLogRepository
    deliveries: DeliveryRepository  # MEU-88
    watchlists: SqlAlchemyWatchlistRepository  # MEU-90a

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._session_factory = sessionmaker(bind=engine)
        self._session: Session | None = None
        self._depth: int = 0

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._depth += 1
        if self._session is None:
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
            # Scheduling repos (MEU-82)
            self.policies = PolicyRepository(self._session)
            self.pipeline_runs = PipelineRunRepository(self._session)
            self.reports = ReportRepository(self._session)
            self.fetch_cache = FetchCacheRepository(self._session)
            self.pipeline_state = PipelineStateRepository(self._session)  # MEU-85
            self.audit_log = AuditLogRepository(self._session)
            self.deliveries = DeliveryRepository(self._session)  # MEU-88
            self.watchlists = SqlAlchemyWatchlistRepository(self._session)  # MEU-90a
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self._depth -= 1
        if self._session is not None:
            if exc_type is not None:
                self._session.rollback()  # Always rollback on exception
            if self._depth == 0:
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


def _set_sqlite_pragmas(dbapi_conn: Any, connection_record: Any) -> None:
    """Set WAL mode and NORMAL sync on SQLite connections.

    Module-level function (not a closure) so the engine remains picklable.
    APScheduler's SQLAlchemyJobStore pickles job callbacks that transitively
    reference the engine; closures like ``create_engine.<locals>.connect``
    are unpicklable.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=wal")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


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
    event.listens_for(engine, "connect")(_set_sqlite_pragmas)

    return engine
