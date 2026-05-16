# pyright: reportArgumentType=false, reportReturnType=false, reportAttributeAccessIssue=false, reportGeneralTypeIssues=false
# SQLAlchemy Column/Session types need suppression for Column[T] → T assignments.

"""SqlAlchemy Tax Repository implementations (MEU-123 + MEU-124).

Source: implementation-plan.md §MEU-123 AC-5, §MEU-124 AC-4.
Implements TaxLotRepository and TaxProfileRepository ports.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from zorivest_core.domain.entities import QuarterlyEstimate, TaxLot, TaxProfile
from zorivest_core.domain.enums import (
    AcquisitionSource,
    CostBasisMethod,
    FilingStatus,
    WashSaleMatchingMethod,
)
from zorivest_infra.database.models import (
    QuarterlyEstimateModel,
    TaxLotModel,
    TaxProfileModel,
)


class SqlTaxLotRepository:
    """SQL-backed TaxLot repository.

    Implements: get, save, update, delete, list_for_account,
    list_filtered, count_filtered.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, lot_id: str) -> Optional[TaxLot]:
        model = self._session.get(TaxLotModel, lot_id)
        if model is None:
            return None
        return _lot_model_to_entity(model)

    def save(self, lot: TaxLot) -> None:
        model = _lot_entity_to_model(lot)
        self._session.add(model)
        self._session.flush()

    def update(self, lot: TaxLot) -> None:
        model = self._session.get(TaxLotModel, lot.lot_id)
        if model is None:
            raise ValueError(f"TaxLot not found: {lot.lot_id}")
        model.account_id = lot.account_id
        model.ticker = lot.ticker
        model.open_date = lot.open_date
        model.close_date = lot.close_date
        model.quantity = lot.quantity
        model.cost_basis = lot.cost_basis
        model.proceeds = lot.proceeds
        model.wash_sale_adjustment = lot.wash_sale_adjustment
        model.is_closed = lot.is_closed
        model.linked_trade_ids = json.dumps(lot.linked_trade_ids)
        model.cost_basis_method = (
            lot.cost_basis_method.value if lot.cost_basis_method else None
        )
        model.realized_gain_loss = lot.realized_gain_loss
        model.acquisition_source = (
            lot.acquisition_source.value if lot.acquisition_source else None
        )
        # Phase 3F: Provenance tracking (MEU-216)
        model.materialized_at = lot.materialized_at
        model.is_user_modified = lot.is_user_modified
        model.source_hash = lot.source_hash
        model.sync_status = lot.sync_status
        self._session.flush()

    def delete(self, lot_id: str) -> None:
        model = self._session.get(TaxLotModel, lot_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()

    def list_for_account(self, account_id: str) -> list[TaxLot]:
        models = (
            self._session.query(TaxLotModel)
            .filter_by(account_id=account_id)
            .order_by(TaxLotModel.open_date)
            .all()
        )
        return [_lot_model_to_entity(m) for m in models]

    def list_filtered(
        self,
        limit: int = 100,
        offset: int = 0,
        account_id: str | None = None,
        ticker: str | None = None,
        is_closed: bool | None = None,
    ) -> list[TaxLot]:
        query = self._session.query(TaxLotModel)
        if account_id is not None:
            query = query.filter_by(account_id=account_id)
        if ticker is not None:
            query = query.filter_by(ticker=ticker)
        if is_closed is not None:
            query = query.filter_by(is_closed=is_closed)
        models = query.order_by(TaxLotModel.open_date).offset(offset).limit(limit).all()
        return [_lot_model_to_entity(m) for m in models]

    def list_all_filtered(
        self,
        account_id: str | None = None,
        ticker: str | None = None,
        is_closed: bool | None = None,
    ) -> list[TaxLot]:
        """Return ALL matching lots without pagination (for aggregate reporting)."""
        query = self._session.query(TaxLotModel)
        if account_id is not None:
            query = query.filter_by(account_id=account_id)
        if ticker is not None:
            query = query.filter_by(ticker=ticker)
        if is_closed is not None:
            query = query.filter_by(is_closed=is_closed)
        models = query.order_by(TaxLotModel.open_date).all()
        return [_lot_model_to_entity(m) for m in models]

    def count_filtered(
        self,
        account_id: str | None = None,
        ticker: str | None = None,
        is_closed: bool | None = None,
    ) -> int:
        query = self._session.query(TaxLotModel)
        if account_id is not None:
            query = query.filter_by(account_id=account_id)
        if ticker is not None:
            query = query.filter_by(ticker=ticker)
        if is_closed is not None:
            query = query.filter_by(is_closed=is_closed)
        return query.count()


class SqlTaxProfileRepository:
    """SQL-backed TaxProfile repository.

    Implements: get, save, update, get_for_year.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, profile_id: int) -> Optional[TaxProfile]:
        model = self._session.get(TaxProfileModel, profile_id)
        if model is None:
            return None
        return _profile_model_to_entity(model)

    def save(self, profile: TaxProfile) -> int:
        model = _profile_entity_to_model(profile)
        self._session.add(model)
        self._session.flush()
        return model.id

    def update(self, profile: TaxProfile) -> None:
        model = self._session.get(TaxProfileModel, profile.id)
        if model is None:
            raise ValueError(f"TaxProfile not found: {profile.id}")
        model.filing_status = profile.filing_status.value
        model.tax_year = profile.tax_year
        model.federal_bracket = profile.federal_bracket
        model.state_tax_rate = profile.state_tax_rate
        model.state = profile.state
        model.prior_year_tax = profile.prior_year_tax
        model.agi_estimate = profile.agi_estimate
        model.capital_loss_carryforward = profile.capital_loss_carryforward
        model.wash_sale_method = profile.wash_sale_method.value
        model.default_cost_basis = profile.default_cost_basis.value
        model.include_drip_wash_detection = profile.include_drip_wash_detection
        model.include_spousal_accounts = profile.include_spousal_accounts
        model.section_475_elected = profile.section_475_elected
        model.section_1256_eligible = profile.section_1256_eligible
        self._session.flush()

    def get_for_year(self, tax_year: int) -> Optional[TaxProfile]:
        model = (
            self._session.query(TaxProfileModel).filter_by(tax_year=tax_year).first()
        )
        if model is None:
            return None
        return _profile_model_to_entity(model)

    def list_all(self) -> list[TaxProfile]:
        """Return all tax profiles ordered by tax_year descending."""
        models = (
            self._session.query(TaxProfileModel)
            .order_by(TaxProfileModel.tax_year.desc())
            .all()
        )
        return [_profile_model_to_entity(m) for m in models]

    def delete(self, tax_year: int) -> bool:
        """Delete the tax profile for the given year.  Returns True if deleted."""
        model = (
            self._session.query(TaxProfileModel).filter_by(tax_year=tax_year).first()
        )
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True


# ── Mappers ──────────────────────────────────────────────────────────────


def _ensure_utc(dt: datetime) -> datetime:
    """Stamp UTC tzinfo on naive datetimes from SQLite storage.

    SQLAlchemy's DateTime column strips tzinfo on write (SQLite stores
    naive strings). This normalizer re-attaches UTC on read so that
    entity computed properties (holding_period_days) can safely mix
    with datetime.now(tz=timezone.utc).
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _lot_model_to_entity(model: TaxLotModel) -> TaxLot:
    linked_ids: list[str] = []
    if model.linked_trade_ids:
        linked_ids = json.loads(model.linked_trade_ids)
    return TaxLot(
        lot_id=model.lot_id,
        account_id=model.account_id,
        ticker=model.ticker,
        open_date=_ensure_utc(model.open_date),
        close_date=_ensure_utc(model.close_date) if model.close_date else None,
        quantity=model.quantity,
        cost_basis=Decimal(str(model.cost_basis)),
        proceeds=Decimal(str(model.proceeds)),
        wash_sale_adjustment=Decimal(str(model.wash_sale_adjustment)),
        is_closed=model.is_closed,
        linked_trade_ids=linked_ids,
        cost_basis_method=CostBasisMethod(model.cost_basis_method)
        if model.cost_basis_method
        else None,
        realized_gain_loss=Decimal(str(model.realized_gain_loss))
        if model.realized_gain_loss
        else Decimal("0.00"),
        acquisition_source=AcquisitionSource(model.acquisition_source)
        if model.acquisition_source
        else None,
        # Phase 3F: Provenance tracking (MEU-216)
        materialized_at=model.materialized_at,
        is_user_modified=bool(model.is_user_modified),
        source_hash=model.source_hash,
        sync_status=model.sync_status or "synced",
    )


def _lot_entity_to_model(lot: TaxLot) -> TaxLotModel:
    return TaxLotModel(
        lot_id=lot.lot_id,
        account_id=lot.account_id,
        ticker=lot.ticker,
        open_date=lot.open_date,
        close_date=lot.close_date,
        quantity=lot.quantity,
        cost_basis=lot.cost_basis,
        proceeds=lot.proceeds,
        wash_sale_adjustment=lot.wash_sale_adjustment,
        is_closed=lot.is_closed,
        linked_trade_ids=json.dumps(lot.linked_trade_ids),
        cost_basis_method=lot.cost_basis_method.value
        if lot.cost_basis_method
        else None,
        realized_gain_loss=lot.realized_gain_loss,
        acquisition_source=lot.acquisition_source.value
        if lot.acquisition_source
        else None,
        # Phase 3F: Provenance tracking (MEU-216)
        materialized_at=lot.materialized_at,
        is_user_modified=lot.is_user_modified,
        source_hash=lot.source_hash,
        sync_status=lot.sync_status,
    )


def _profile_model_to_entity(model: TaxProfileModel) -> TaxProfile:
    return TaxProfile(
        id=model.id,
        filing_status=FilingStatus(model.filing_status),
        tax_year=model.tax_year,
        federal_bracket=model.federal_bracket,
        state_tax_rate=model.state_tax_rate,
        state=model.state,
        prior_year_tax=Decimal(str(model.prior_year_tax)),
        agi_estimate=Decimal(str(model.agi_estimate)),
        capital_loss_carryforward=Decimal(str(model.capital_loss_carryforward)),
        wash_sale_method=WashSaleMatchingMethod(model.wash_sale_method),
        default_cost_basis=CostBasisMethod(model.default_cost_basis),
        include_drip_wash_detection=model.include_drip_wash_detection,
        include_spousal_accounts=model.include_spousal_accounts,
        section_475_elected=model.section_475_elected,
        section_1256_eligible=model.section_1256_eligible,
    )


def _profile_entity_to_model(profile: TaxProfile) -> TaxProfileModel:
    return TaxProfileModel(
        filing_status=profile.filing_status.value,
        tax_year=profile.tax_year,
        federal_bracket=profile.federal_bracket,
        state_tax_rate=profile.state_tax_rate,
        state=profile.state,
        prior_year_tax=profile.prior_year_tax,
        agi_estimate=profile.agi_estimate,
        capital_loss_carryforward=profile.capital_loss_carryforward,
        wash_sale_method=profile.wash_sale_method.value,
        default_cost_basis=profile.default_cost_basis.value,
        include_drip_wash_detection=profile.include_drip_wash_detection,
        include_spousal_accounts=profile.include_spousal_accounts,
        section_475_elected=profile.section_475_elected,
        section_1256_eligible=profile.section_1256_eligible,
    )


# ── QuarterlyEstimate Repository (MEU-148 AC-148.6) ─────────────────────


class SqlQuarterlyEstimateRepository:
    """SQL-backed QuarterlyEstimate repository.

    Implements: get, save, update, list_for_year, get_for_quarter.
    Follows QuarterlyEstimateRepository protocol (ports.py L446-468).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, estimate_id: int) -> Optional[QuarterlyEstimate]:
        model = self._session.get(QuarterlyEstimateModel, estimate_id)
        if model is None:
            return None
        return _estimate_model_to_entity(model)

    def save(self, estimate: QuarterlyEstimate) -> int:
        model = _estimate_entity_to_model(estimate)
        self._session.add(model)
        self._session.flush()
        return model.id

    def update(self, estimate: QuarterlyEstimate) -> None:
        model = self._session.get(QuarterlyEstimateModel, estimate.id)
        if model is None:
            raise ValueError(f"QuarterlyEstimate not found: {estimate.id}")
        model.tax_year = estimate.tax_year
        model.quarter = estimate.quarter
        model.due_date = estimate.due_date
        model.required_payment = estimate.required_payment
        model.actual_payment = estimate.actual_payment
        model.method = estimate.method
        model.cumulative_ytd_gains = estimate.cumulative_ytd_gains
        model.underpayment_penalty_risk = estimate.underpayment_penalty_risk
        self._session.flush()

    def list_for_year(self, tax_year: int) -> list[QuarterlyEstimate]:
        models = (
            self._session.query(QuarterlyEstimateModel)
            .filter_by(tax_year=tax_year)
            .order_by(QuarterlyEstimateModel.quarter)
            .all()
        )
        return [_estimate_model_to_entity(m) for m in models]

    def get_for_quarter(
        self, tax_year: int, quarter: int
    ) -> Optional[QuarterlyEstimate]:
        model = (
            self._session.query(QuarterlyEstimateModel)
            .filter_by(tax_year=tax_year, quarter=quarter)
            .first()
        )
        if model is None:
            return None
        return _estimate_model_to_entity(model)


def _estimate_model_to_entity(model: QuarterlyEstimateModel) -> QuarterlyEstimate:
    return QuarterlyEstimate(
        id=model.id,
        tax_year=model.tax_year,
        quarter=model.quarter,
        due_date=_ensure_utc(model.due_date),
        required_payment=Decimal(str(model.required_payment)),
        actual_payment=Decimal(str(model.actual_payment)),
        method=model.method,
        cumulative_ytd_gains=Decimal(str(model.cumulative_ytd_gains)),
        underpayment_penalty_risk=Decimal(str(model.underpayment_penalty_risk)),
    )


def _estimate_entity_to_model(estimate: QuarterlyEstimate) -> QuarterlyEstimateModel:
    return QuarterlyEstimateModel(
        tax_year=estimate.tax_year,
        quarter=estimate.quarter,
        due_date=estimate.due_date,
        required_payment=estimate.required_payment,
        actual_payment=estimate.actual_payment,
        method=estimate.method,
        cumulative_ytd_gains=estimate.cumulative_ytd_gains,
        underpayment_penalty_risk=estimate.underpayment_penalty_risk,
    )
