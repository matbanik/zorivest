# packages/core/src/zorivest_core/application/queries.py

from __future__ import annotations

from dataclasses import dataclass

from zorivest_core.domain.enums import ImageOwnerType


@dataclass(frozen=True)
class GetTrade:
    """Query to retrieve a single trade by exec_id."""

    exec_id: str


@dataclass(frozen=True)
class ListTrades:
    """Query to list trades with pagination and optional account filter."""

    limit: int = 100
    offset: int = 0
    account_id: str | None = None


@dataclass(frozen=True)
class GetAccount:
    """Query to retrieve a single account by account_id."""

    account_id: str


@dataclass(frozen=True)
class ListAccounts:
    """Query to list all accounts."""


@dataclass(frozen=True)
class GetImage:
    """Query to retrieve a single image by id."""

    image_id: int


@dataclass(frozen=True)
class ListImages:
    """Query to list images for a given owner."""

    owner_type: ImageOwnerType
    owner_id: str
