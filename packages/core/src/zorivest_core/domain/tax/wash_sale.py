# packages/core/src/zorivest_core/domain/tax/wash_sale.py
"""Wash sale entities — WashSaleChain and WashSaleEntry.

MEU-130 AC-130.1 (mutable chain), AC-130.2 (frozen entry).
Spec: domain-model-reference.md B1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from zorivest_core.domain.enums import WashSaleEventType, WashSaleStatus


@dataclass(frozen=True)
class WashSaleEntry:
    """Single event in a wash sale chain's audit trail.

    AC-130.2: frozen dataclass with 7 fields.
    """

    entry_id: str
    chain_id: str
    event_type: WashSaleEventType
    lot_id: str
    amount: Decimal
    event_date: datetime
    account_id: str


@dataclass
class WashSaleChain:
    """Mutable wash sale chain tracking disallowed losses across lots.

    AC-130.1: mutable dataclass with 8 fields.
    Lifecycle: DISALLOWED → ABSORBED → RELEASED (or DESTROYED).
    """

    chain_id: str
    ticker: str
    loss_lot_id: str
    loss_date: datetime
    loss_amount: Decimal
    disallowed_amount: Decimal
    status: WashSaleStatus
    loss_open_date: datetime | None = None  # For holding period tacking (AC-131.4)
    entries: list[WashSaleEntry] = field(default_factory=list)
