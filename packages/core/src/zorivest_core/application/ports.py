# packages/core/src/zorivest_core/application/ports.py

from __future__ import annotations

from typing import Optional, Protocol

from zorivest_core.domain.entities import ImageAttachment, Trade


class TradeRepository(Protocol):
    """Repository for Trade entities."""

    def get(self, exec_id: str) -> Optional[Trade]: ...

    def save(self, trade: Trade) -> None: ...

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Trade]: ...

    def exists(self, exec_id: str) -> bool: ...


class ImageRepository(Protocol):
    """Repository for ImageAttachment entities."""

    def save(self, owner_type: str, owner_id: str, image: ImageAttachment) -> int: ...

    def get(self, image_id: int) -> Optional[ImageAttachment]: ...

    def get_for_owner(
        self, owner_type: str, owner_id: str
    ) -> list[ImageAttachment]: ...

    def delete(self, image_id: int) -> None: ...

    def get_thumbnail(self, image_id: int, max_size: int = 200) -> bytes: ...


class UnitOfWork(Protocol):
    """Transactional unit of work wrapping repository access."""

    trades: TradeRepository
    images: ImageRepository

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
