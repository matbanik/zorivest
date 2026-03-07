# packages/core/src/zorivest_core/domain/events.py
"""Domain events emitted when aggregate state changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from zorivest_core.domain.enums import (
    ConvictionLevel,
    ImageOwnerType,
    TradeAction,
)


@dataclass(frozen=True)
class DomainEvent:
    """Base event — all domain events inherit from this."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class TradeCreated(DomainEvent):
    """Emitted when a new trade execution is recorded."""

    exec_id: str = ""
    instrument: str = ""
    action: TradeAction = TradeAction.BOT
    quantity: float = 0.0
    price: float = 0.0
    account_id: str = ""


@dataclass(frozen=True)
class BalanceUpdated(DomainEvent):
    """Emitted when an account balance snapshot is recorded."""

    account_id: str = ""
    new_balance: Decimal = Decimal("0")
    snapshot_id: int = 0


@dataclass(frozen=True)
class ImageAttached(DomainEvent):
    """Emitted when an image is attached to a trade, report, or plan."""

    owner_type: ImageOwnerType = ImageOwnerType.TRADE
    owner_id: str = ""
    image_id: int = 0


@dataclass(frozen=True)
class PlanCreated(DomainEvent):
    """Emitted when a new trade plan is created."""

    plan_id: int = 0
    ticker: str = ""
    direction: TradeAction = TradeAction.BOT
    conviction: ConvictionLevel = ConvictionLevel.LOW
