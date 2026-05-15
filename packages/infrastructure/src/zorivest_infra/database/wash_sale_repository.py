# pyright: reportArgumentType=false, reportReturnType=false, reportAttributeAccessIssue=false, reportGeneralTypeIssues=false
# SQLAlchemy Column/Session types need suppression for Column[T] → T assignments.

"""SqlAlchemy Wash Sale Chain Repository (MEU-130 AC-130.10).

Source: implementation-plan.md §MEU-130 AC-130.10.
Implements WashSaleChainRepository port.
"""

from __future__ import annotations

from datetime import timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from zorivest_core.domain.enums import WashSaleEventType, WashSaleStatus
from zorivest_core.domain.tax.wash_sale import WashSaleChain, WashSaleEntry
from zorivest_infra.database.wash_sale_models import (
    WashSaleChainModel,
    WashSaleEntryModel,
)


class SqlWashSaleChainRepository:
    """SQL-backed WashSaleChain repository.

    Implements: get, save, update, list_for_ticker, list_active.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, chain_id: str) -> Optional[WashSaleChain]:
        model = self._session.get(WashSaleChainModel, chain_id)
        if model is None:
            return None
        return _chain_model_to_entity(model)

    def save(self, chain: WashSaleChain) -> None:
        model = _chain_entity_to_model(chain)
        self._session.add(model)
        self._session.flush()

    def update(self, chain: WashSaleChain) -> None:
        model = self._session.get(WashSaleChainModel, chain.chain_id)
        if model is None:
            raise ValueError(f"WashSaleChain not found: {chain.chain_id}")
        model.ticker = chain.ticker
        model.loss_lot_id = chain.loss_lot_id
        model.loss_date = chain.loss_date
        model.loss_amount = chain.loss_amount
        model.disallowed_amount = chain.disallowed_amount
        model.status = chain.status.value
        model.loss_open_date = chain.loss_open_date

        # Sync entries: delete existing, re-add current
        for existing in model.entries[:]:
            self._session.delete(existing)
        self._session.flush()
        # Expunge deleted entries from identity map to avoid PK collision
        # when re-adding entries with the same entry_id
        self._session.expire_all()
        for entry in chain.entries:
            entry_model = _entry_entity_to_model(entry)
            self._session.merge(entry_model)
        self._session.flush()

    def list_for_ticker(self, ticker: str) -> list[WashSaleChain]:
        models = (
            self._session.query(WashSaleChainModel)
            .filter_by(ticker=ticker)
            .order_by(WashSaleChainModel.loss_date)
            .all()
        )
        return [_chain_model_to_entity(m) for m in models]

    def list_active(self, status: WashSaleStatus | None = None) -> list[WashSaleChain]:
        query = self._session.query(WashSaleChainModel)
        if status is not None:
            query = query.filter_by(status=status.value)
        else:
            # "Active" = not yet released or destroyed
            query = query.filter(
                WashSaleChainModel.status.in_(
                    [
                        WashSaleStatus.DISALLOWED.value,
                        WashSaleStatus.ABSORBED.value,
                    ]
                )
            )
        models = query.order_by(WashSaleChainModel.loss_date).all()
        return [_chain_model_to_entity(m) for m in models]


# ── Mappers ──────────────────────────────────────────────────────────────


def _ensure_utc(dt):  # noqa: ANN001, ANN201
    """Stamp UTC tzinfo on naive datetimes from SQLite storage."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _chain_model_to_entity(model: WashSaleChainModel) -> WashSaleChain:
    entries = [_entry_model_to_entity(e) for e in model.entries]
    return WashSaleChain(
        chain_id=model.chain_id,
        ticker=model.ticker,
        loss_lot_id=model.loss_lot_id,
        loss_date=_ensure_utc(model.loss_date),
        loss_amount=Decimal(str(model.loss_amount)),
        disallowed_amount=Decimal(str(model.disallowed_amount)),
        status=WashSaleStatus(model.status),
        loss_open_date=_ensure_utc(model.loss_open_date)
        if model.loss_open_date
        else None,
        entries=entries,
    )


def _entry_model_to_entity(model: WashSaleEntryModel) -> WashSaleEntry:
    return WashSaleEntry(
        entry_id=model.entry_id,
        chain_id=model.chain_id,
        event_type=WashSaleEventType(model.event_type),
        lot_id=model.lot_id,
        amount=Decimal(str(model.amount)),
        event_date=_ensure_utc(model.event_date),
        account_id=model.account_id,
    )


def _chain_entity_to_model(chain: WashSaleChain) -> WashSaleChainModel:
    chain_model = WashSaleChainModel(
        chain_id=chain.chain_id,
        ticker=chain.ticker,
        loss_lot_id=chain.loss_lot_id,
        loss_date=chain.loss_date,
        loss_amount=chain.loss_amount,
        disallowed_amount=chain.disallowed_amount,
        status=chain.status.value,
        loss_open_date=chain.loss_open_date,
    )
    chain_model.entries = [_entry_entity_to_model(e) for e in chain.entries]
    return chain_model


def _entry_entity_to_model(entry: WashSaleEntry) -> WashSaleEntryModel:
    return WashSaleEntryModel(
        entry_id=entry.entry_id,
        chain_id=entry.chain_id,
        event_type=entry.event_type.value,
        lot_id=entry.lot_id,
        amount=entry.amount,
        event_date=entry.event_date,
        account_id=entry.account_id,
    )
