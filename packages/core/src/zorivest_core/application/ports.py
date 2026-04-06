# packages/core/src/zorivest_core/application/ports.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Protocol

from zorivest_core.domain.enums import BrokerType
from zorivest_core.domain.import_types import ImportResult, RawExecution

from zorivest_core.application.market_dtos import (
    MarketNewsItem,
    MarketQuote,
    SecFiling,
    TickerSearchResult,
)

from zorivest_core.domain.entities import (
    Account,
    BalanceSnapshot,
    ImageAttachment,
    Trade,
    TradePlan,
    TradeReport,
    Watchlist,
    WatchlistItem,
)
from zorivest_core.domain.market_provider_settings import MarketProviderSettings


class TradeRepository(Protocol):
    """Repository for Trade entities."""

    def get(self, exec_id: str) -> Optional[Trade]: ...

    def save(self, trade: Trade) -> None: ...

    def update(self, trade: Trade) -> None:
        """Update an existing trade (upsert-safe)."""
        ...

    def delete(self, exec_id: str) -> None:
        """Delete a trade by exec_id."""
        ...

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Trade]: ...

    def list_filtered(
        self,
        limit: int = 100,
        offset: int = 0,
        account_id: str | None = None,
        sort: str = "-time",
        search: str | None = None,
    ) -> list[Trade]:
        """List trades with optional account filter, search, and sort."""
        ...

    def count_filtered(
        self,
        account_id: str | None = None,
        search: str | None = None,
    ) -> int:
        """Return total count of trades matching filters (ignoring limit/offset)."""
        ...

    def exists(self, exec_id: str) -> bool: ...

    def exists_by_fingerprint_since(
        self, fingerprint: str, lookback_days: int = 30
    ) -> bool:
        """Check if a trade with this fingerprint exists within lookback window."""
        ...

    def list_for_account(self, account_id: str) -> list[Trade]:
        """Return all trades belonging to the given account."""
        ...


class ImageRepository(Protocol):
    """Repository for ImageAttachment entities."""

    def save(self, owner_type: str, owner_id: str, image: ImageAttachment) -> int: ...

    def get(self, image_id: int) -> Optional[ImageAttachment]: ...

    def get_for_owner(
        self, owner_type: str, owner_id: str
    ) -> list[ImageAttachment]: ...

    def delete(self, image_id: int) -> None: ...

    def get_thumbnail(self, image_id: int, max_size: int = 200) -> bytes: ...

    def get_full_data(self, image_id: int) -> bytes:
        """Return raw image bytes without thumbnail processing."""
        ...


class AccountRepository(Protocol):
    """Repository for Account entities."""

    def get(self, account_id: str) -> Optional[Account]: ...

    def save(self, account: Account) -> None: ...

    def update(self, account: Account) -> None:
        """Update an existing account (upsert-safe)."""
        ...

    def delete(self, account_id: str) -> None:
        """Delete an account by account_id."""
        ...

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        include_archived: bool = False,
        include_system: bool = False,
    ) -> list[Account]:
        """List accounts with optional archived/system filtering."""
        ...

    def count_all(
        self,
        include_archived: bool = False,
        include_system: bool = False,
    ) -> int:
        """Count accounts with optional archived/system filtering."""
        ...

    def reassign_trades_to(self, source_id: str, target_id: str) -> int:
        """Reassign all trades from source account to target.

        Returns the number of trades reassigned.
        """
        ...


class BalanceSnapshotRepository(Protocol):
    """Repository for BalanceSnapshot entities."""

    def save(self, snapshot: BalanceSnapshot) -> None: ...

    def get_latest(self, account_id: str) -> BalanceSnapshot | None:
        """Return the most recent balance snapshot for an account, or None."""
        ...

    def list_for_account(
        self,
        account_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BalanceSnapshot]:
        """Return balance snapshots for an account with pagination, newest first."""
        ...

    def count_for_account(self, account_id: str) -> int:
        """Return total count of balance snapshots for an account."""
        ...


class RoundTripRepository(Protocol):
    """Repository for RoundTrip entities.

    Uses ``Any`` for entity type since RoundTrip entity is defined in Phase 3.
    Concrete implementations will use the actual RoundTrip dataclass.
    """

    def save(self, round_trip: Any) -> None: ...

    def list_for_account(
        self, account_id: str, status: str | None = None
    ) -> list[Any]: ...


class SettingsRepository(Protocol):
    """Repository for user setting overrides (SettingModel)."""

    def get(self, key: str) -> Optional[Any]: ...

    def get_all(self) -> list[Any]: ...

    def bulk_upsert(self, settings: dict[str, Any]) -> None: ...

    def delete(self, key: str) -> None: ...


class AppDefaultsRepository(Protocol):
    """Repository for application default settings (AppDefaultModel)."""

    def get(self, key: str) -> Optional[Any]: ...

    def get_all(self) -> list[Any]: ...


class MarketProviderSettingsRepository(Protocol):
    """Repository for market provider settings entities."""

    def get(self, provider_name: str) -> MarketProviderSettings | None: ...

    def save(self, settings: MarketProviderSettings) -> None: ...

    def list_all(self) -> list[MarketProviderSettings]: ...

    def delete(self, provider_name: str) -> None: ...


class TradeReportRepository(Protocol):
    """Repository for TradeReport entities."""

    def get(self, report_id: int) -> Optional[TradeReport]: ...

    def save(self, report: TradeReport) -> None: ...

    def get_for_trade(self, trade_id: str) -> Optional[TradeReport]: ...

    def update(self, report: TradeReport) -> None:
        """Update an existing report (upsert-safe)."""
        ...

    def delete(self, report_id: int) -> None:
        """Delete a report by ID."""
        ...


class TradePlanRepository(Protocol):
    """Repository for TradePlan entities (MEU-66)."""

    def get(self, plan_id: int) -> Optional[TradePlan]: ...

    def save(self, plan: TradePlan) -> None: ...

    def list_all(self, limit: int = 100, offset: int = 0) -> list[TradePlan]: ...

    def update(self, plan: TradePlan) -> None:
        """Update an existing plan (upsert-safe)."""
        ...

    def delete(self, plan_id: int) -> None:
        """Delete a plan by ID."""
        ...

    def count_for_account(self, account_id: str) -> int:
        """Count plans referencing a specific account."""
        ...


class WatchlistRepository(Protocol):
    """Repository for Watchlist entities (MEU-68)."""

    def get(self, watchlist_id: int) -> Optional[Watchlist]: ...

    def save(self, watchlist: Watchlist) -> None: ...

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Watchlist]: ...

    def update(self, watchlist: Watchlist) -> None:
        """Update an existing watchlist (upsert-safe)."""
        ...

    def delete(self, watchlist_id: int) -> None:
        """Delete a watchlist by ID (cascades items)."""
        ...

    def exists_by_name(self, name: str) -> bool:
        """Check if a watchlist with this name already exists."""
        ...

    def add_item(self, item: WatchlistItem) -> None:
        """Add an item (ticker) to a watchlist."""
        ...

    def remove_item(self, watchlist_id: int, ticker: str) -> None:
        """Remove an item (ticker) from a watchlist."""
        ...

    def get_items(self, watchlist_id: int) -> list[WatchlistItem]: ...


class EmailProviderRepository(Protocol):
    """Repository for email provider configuration (single-row). MEU-73."""

    def get(self) -> Optional[Any]: ...

    def save(self, config: Any) -> None: ...


class UnitOfWork(Protocol):
    """Transactional unit of work wrapping repository access."""

    trades: TradeRepository
    images: ImageRepository
    accounts: AccountRepository
    balance_snapshots: BalanceSnapshotRepository
    round_trips: RoundTripRepository
    settings: SettingsRepository
    app_defaults: AppDefaultsRepository
    market_provider_settings: MarketProviderSettingsRepository
    trade_reports: TradeReportRepository  # MEU-52
    trade_plans: TradePlanRepository  # MEU-66
    watchlists: WatchlistRepository  # MEU-68
    email_provider: EmailProviderRepository  # MEU-73

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, *args: object) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


# ── Build Plan Expansion ports ──────────────────────────────────────────


class BrokerPort(Protocol):
    """Abstract broker adapter — all brokers implement this protocol."""

    def get_account(self) -> dict: ...  # type: ignore[type-arg]

    def get_positions(self) -> list[dict]: ...  # type: ignore[type-arg]

    def get_orders(self, status: str = "closed") -> list[dict]: ...  # type: ignore[type-arg]

    def get_bars(
        self, symbol: str, timeframe: str, start: str, end: str
    ) -> list[dict]: ...  # type: ignore[type-arg]

    def get_order_history(self, start: str, end: str) -> list[dict]: ...  # type: ignore[type-arg]


class BankImportPort(Protocol):
    """Abstract parser for bank statement files."""

    def detect_format(self, file_path: str) -> str: ...

    def parse_statement(
        self,
        file_path: str,
        config: dict | None = None,  # type: ignore[type-arg]
    ) -> dict: ...  # type: ignore[type-arg]

    def detect_bank(self, headers: list[str]) -> str | None: ...


class IdentifierResolverPort(Protocol):
    """Resolve CUSIP/ISIN/SEDOL to ticker symbol."""

    def resolve(
        self, id_type: str, id_value: str, exchange_hint: str | None = None
    ) -> dict | None: ...  # type: ignore[type-arg]

    def batch_resolve(self, identifiers: list[dict]) -> list[dict]: ...  # type: ignore[type-arg]


# ── Phase 2.75: Broker Import Protocols ──────────────────────────────────


class BrokerFileAdapter(Protocol):
    """Abstract adapter for file-based broker data import.

    Handles structured file formats (XML, proprietary).
    The existing ``BrokerPort`` handles live API operations;
    ``BrokerFileAdapter`` handles offline file imports.
    """

    @property
    def broker_type(self) -> BrokerType: ...

    def parse_file(self, file_path: Path) -> ImportResult: ...


class CSVBrokerAdapter(BrokerFileAdapter, Protocol):
    """Extended adapter for CSV-based broker imports.

    Adds header fingerprint detection for auto-detection routing.
    """

    def detect(self, headers: list[str]) -> bool: ...

    def parse_rows(self, rows: list[dict[str, str]]) -> list[RawExecution]: ...


class MarketDataPort(Protocol):
    """Abstract interface for market data queries."""

    async def get_quote(self, ticker: str) -> MarketQuote: ...

    async def get_news(
        self, ticker: str | None, count: int
    ) -> list[MarketNewsItem]: ...

    async def search_ticker(self, query: str) -> list[TickerSearchResult]: ...

    async def get_sec_filings(self, ticker: str) -> list[SecFiling]: ...
