# packages/core/src/zorivest_core/application/ports.py

from __future__ import annotations

from typing import Any, Optional, Protocol

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
)


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
    ) -> list[Trade]:
        """List trades with optional account filter and sort."""
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

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Account]: ...


class BalanceSnapshotRepository(Protocol):
    """Repository for BalanceSnapshot entities."""

    def save(self, snapshot: BalanceSnapshot) -> None: ...

    def list_for_account(self, account_id: str) -> list[BalanceSnapshot]: ...


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
    """Repository for MarketProviderSettingModel entities."""

    def get(self, provider_name: str) -> Any: ...  # MarketProviderSettingModel | None

    def save(self, model: Any) -> None: ...  # MarketProviderSettingModel

    def list_all(self) -> list[Any]: ...  # list[MarketProviderSettingModel]

    def delete(self, provider_name: str) -> None: ...


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
        self, file_path: str, config: dict | None = None  # type: ignore[type-arg]
    ) -> dict: ...  # type: ignore[type-arg]

    def detect_bank(self, headers: list[str]) -> str | None: ...


class IdentifierResolverPort(Protocol):
    """Resolve CUSIP/ISIN/SEDOL to ticker symbol."""

    def resolve(
        self, id_type: str, id_value: str, exchange_hint: str | None = None
    ) -> dict | None: ...  # type: ignore[type-arg]

    def batch_resolve(self, identifiers: list[dict]) -> list[dict]: ...  # type: ignore[type-arg]


class MarketDataPort(Protocol):
    """Abstract interface for market data queries."""

    async def get_quote(self, ticker: str) -> MarketQuote: ...

    async def get_news(self, ticker: str | None, count: int) -> list[MarketNewsItem]: ...

    async def search_ticker(self, query: str) -> list[TickerSearchResult]: ...

    async def get_sec_filings(self, ticker: str) -> list[SecFiling]: ...
