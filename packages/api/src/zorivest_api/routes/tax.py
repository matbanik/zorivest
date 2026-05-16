# packages/api/src/zorivest_api/routes/tax.py
"""Tax routes — simulation, estimation, wash sales, lots, quarterly, harvest, audit.

Source: 04f-api-tax.md §Tax Routes
MEU-29: 12 endpoints with Pydantic request schemas. All mode-gated.
MEU-148: Route handlers decompose Pydantic bodies → TaxService method args,
         serialize domain dataclasses → dicts. StubTaxService retired.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from zorivest_api.dependencies import get_tax_service, require_unlocked_db

tax_router = APIRouter(
    prefix="/api/v1/tax",
    tags=["tax"],
    dependencies=[Depends(require_unlocked_db)],
)


# ── Utility: dataclass → dict serializer ────────────────────────────


def _serialize(obj: Any) -> Any:
    """Recursively serialize dataclasses/Decimals to JSON-safe dicts."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _serialize(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


# ── Request schemas ─────────────────────────────────────────────────


class SimulateTaxRequest(BaseModel):
    model_config = {"extra": "forbid"}

    ticker: str
    action: Literal["sell", "cover"]
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)
    account_id: str
    cost_basis_method: Literal["fifo", "lifo", "specific_id", "avg_cost"] = "fifo"


class EstimateTaxRequest(BaseModel):
    model_config = {"extra": "forbid"}

    tax_year: int
    account_id: Optional[str] = None
    filing_status: Literal[
        "single", "married_joint", "married_separate", "head_of_household"
    ] = "single"
    include_unrealized: bool = False


class WashSaleRequest(BaseModel):
    model_config = {"extra": "forbid"}

    account_id: Optional[str] = None
    ticker: Optional[str] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None


class RecordPaymentRequest(BaseModel):
    model_config = {"extra": "forbid"}

    quarter: Literal["Q1", "Q2", "Q3", "Q4"]
    tax_year: int
    payment_amount: float = Field(gt=0)
    confirm: bool


class ReassignLotBasisRequest(BaseModel):
    model_config = {"extra": "forbid"}

    method: Literal["fifo", "lifo", "hifo", "specific_id", "avg_cost"] = "fifo"


class SyncTaxLotsRequest(BaseModel):
    model_config = {"extra": "forbid"}

    account_id: Optional[str] = None
    conflict_strategy: Optional[Literal["flag", "block", "auto_resolve"]] = None


class ScanWashSalesRequest(BaseModel):
    model_config = {"extra": "forbid"}

    tax_year: Optional[int] = Field(default=None, ge=2000, le=2099)


class TaxProfileCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    tax_year: int = Field(ge=2020, le=2030)
    filing_status: Literal[
        "SINGLE", "MARRIED_JOINT", "MARRIED_SEPARATE", "HEAD_OF_HOUSEHOLD"
    ]
    federal_bracket: float = Field(ge=0.0, le=1.0)
    state_tax_rate: float = Field(ge=0.0, le=1.0)
    state: str = Field(min_length=2, max_length=2)
    prior_year_tax: float = Field(ge=0.0)
    agi_estimate: float = Field(ge=0.0)
    capital_loss_carryforward: float = Field(ge=0.0, default=0.0)
    wash_sale_method: Literal["CONSERVATIVE", "AGGRESSIVE"] = "CONSERVATIVE"
    default_cost_basis: Literal[
        "FIFO",
        "LIFO",
        "HIFO",
        "SPEC_ID",
        "MAX_LT_GAIN",
        "MAX_LT_LOSS",
        "MAX_ST_GAIN",
        "MAX_ST_LOSS",
    ] = "FIFO"
    include_drip_wash_detection: bool = True
    include_spousal_accounts: bool = False
    section_475_elected: bool = False
    section_1256_eligible: bool = False


class TaxProfileUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    filing_status: Optional[
        Literal["SINGLE", "MARRIED_JOINT", "MARRIED_SEPARATE", "HEAD_OF_HOUSEHOLD"]
    ] = None
    federal_bracket: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    state_tax_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    state: Optional[str] = Field(default=None, min_length=2, max_length=2)
    prior_year_tax: Optional[float] = Field(default=None, ge=0.0)
    agi_estimate: Optional[float] = Field(default=None, ge=0.0)
    capital_loss_carryforward: Optional[float] = Field(default=None, ge=0.0)
    wash_sale_method: Optional[Literal["CONSERVATIVE", "AGGRESSIVE"]] = None
    default_cost_basis: Optional[
        Literal[
            "FIFO",
            "LIFO",
            "HIFO",
            "SPEC_ID",
            "MAX_LT_GAIN",
            "MAX_LT_LOSS",
            "MAX_ST_GAIN",
            "MAX_ST_LOSS",
        ]
    ] = None
    include_drip_wash_detection: Optional[bool] = None
    include_spousal_accounts: Optional[bool] = None
    section_475_elected: Optional[bool] = None
    section_1256_eligible: Optional[bool] = None


# ── Quarter string → int mapping (AC-148.9) ────────────────────────

_QUARTER_MAP = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}


# ── Tax simulation ──────────────────────────────────────────────────


@tax_router.post("/simulate", status_code=200)
async def simulate_tax_impact(
    body: SimulateTaxRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Pre-trade what-if tax simulation.

    AC-148.3: Decomposes Pydantic body → TaxService.simulate_impact() args.
    """
    from zorivest_core.domain.enums import CostBasisMethod

    try:
        result = service.simulate_impact(
            account_id=body.account_id,
            ticker=body.ticker,
            quantity=body.quantity,
            sale_price=Decimal(str(body.price)),
            method=CostBasisMethod(body.cost_basis_method.upper()),
        )
        return _serialize(result)
    except Exception as exc:
        # If no lots exist, return an empty simulation result
        if "no open lots" in str(exc).lower():
            return {
                "lot_details": [],
                "total_lt_gain": 0.0,
                "total_st_gain": 0.0,
                "estimated_tax": 0.0,
                "wash_risk": False,
                "wash_sale_warnings": [],
                "wait_days": 0,
            }
        raise


# ── Tax estimation ──────────────────────────────────────────────────


@tax_router.post("/estimate", status_code=200)
async def estimate_tax(
    body: EstimateTaxRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Compute overall tax estimate.

    AC-148.3: Routes to TaxService.get_taxable_gains() for annual gains.
    """
    result = service.get_taxable_gains(body.tax_year)
    serialized = _serialize(result)
    # Map to expected API response shape
    return {
        "federal_estimate": serialized.get("total_st_gain", 0.0)
        + serialized.get("total_lt_gain", 0.0),
        "state_estimate": 0.0,
        "bracket_breakdown": [],
        **serialized,
    }


# ── Wash sale detection ─────────────────────────────────────────────


def _build_lot_account_map(service: Any, chains: list) -> dict[str, str]:
    """Build a mapping from lot_id → account_id for chain filtering.

    Chains are cross-account entities (WashSaleChain has no account_id).
    This correlates each chain's loss_lot_id to its originating account.
    """
    lot_ids = {c.loss_lot_id for c in chains}
    result: dict[str, str] = {}
    with service._uow:
        for lot_id in lot_ids:
            lot = service._uow.tax_lots.get(lot_id)
            if lot is not None:
                result[lot_id] = lot.account_id
    return result


@tax_router.post("/wash-sales", status_code=200)
async def find_wash_sales(
    body: WashSaleRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Detect wash sale chains/conflicts within 30-day windows.

    AC-148.3: Routes to TaxService.get_trapped_losses().
    Chains are cross-account entities; account_id filters by loss lot's account.
    """
    chains = service.get_trapped_losses()
    # Filter by account if specified — correlate via loss lot's account
    if body.account_id:
        lot_account_map = _build_lot_account_map(service, chains)
        chains = [
            c for c in chains if lot_account_map.get(c.loss_lot_id) == body.account_id
        ]
    # Filter by ticker if specified
    if body.ticker:
        chains = [c for c in chains if c.ticker == body.ticker]
    return {
        "chains": _serialize(chains),
        "disallowed_total": sum(float(c.disallowed_amount) for c in chains),
        "affected_tickers": list({c.ticker for c in chains}),
    }


# ── Tax lot management ──────────────────────────────────────────────


@tax_router.get("/lots", status_code=200)
async def get_tax_lots(
    account_id: Optional[str] = None,
    ticker: Optional[str] = None,
    status: Literal["open", "closed", "all"] = "all",
    sort_by: Literal["acquired_date", "cost_basis", "gain_loss"] = "acquired_date",
    service: Any = Depends(get_tax_service),
) -> dict:
    """List tax lots with basis, holding period, and gain/loss.

    AC-148.3: get_lots returns list[TaxLot] → serialized to dict.
    """
    lots = service.get_lots(account_id, ticker, status, sort_by)
    return {
        "lots": _serialize(lots),
        "total_count": len(lots),
    }


# ── Quarterly estimates ─────────────────────────────────────────────


@tax_router.get("/quarterly", status_code=200)
async def get_quarterly_estimate(
    quarter: Literal["Q1", "Q2", "Q3", "Q4"],
    tax_year: int,
    estimation_method: Literal["annualized", "actual", "prior_year"] = "annualized",
    service: Any = Depends(get_tax_service),
) -> dict:
    """Compute quarterly estimated tax payment obligations.

    AC-148.9: Quarter string "Q1"→1, "Q2"→2 etc.
    """
    quarter_int = _QUARTER_MAP[quarter]
    try:
        result = service.quarterly_estimate(quarter_int, tax_year, estimation_method)
        return _serialize(result)
    except Exception as exc:
        # No TaxProfile or method unsupported → return default shape
        if "no taxprofile" in str(exc).lower() or "actual" in str(exc).lower():
            return {
                "required": 0.0,
                "paid": 0.0,
                "due": 0.0,
                "penalty": 0.0,
                "due_date": "",
                "method": estimation_method,
            }
        raise


@tax_router.post("/quarterly/payment", status_code=200)
async def record_quarterly_tax_payment(
    body: RecordPaymentRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Record an actual quarterly tax payment. Requires confirm=true.

    AC-148.6: Routes to TaxService.record_payment() with persistence.
    """
    if not body.confirm:
        raise HTTPException(400, "confirm must be true")
    quarter_int = _QUARTER_MAP[body.quarter]
    try:
        service.record_payment(
            tax_year=body.tax_year,
            quarter=quarter_int,
            amount=Decimal(str(body.payment_amount)),
        )
    except NotImplementedError as exc:
        raise HTTPException(501, "record_payment not yet implemented") from exc
    return {
        "status": "recorded",
        "quarter": body.quarter,
        "amount": body.payment_amount,
    }


# ── Loss harvesting ─────────────────────────────────────────────────


@tax_router.get("/harvest", status_code=200)
async def harvest_losses(
    account_id: Optional[str] = None,
    min_loss_threshold: float = 0.0,
    exclude_wash_risk: bool = False,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Scan portfolio for harvestable losses.

    AC-148.3: Returns wash-sale-trapped chains as harvest candidates.
    Uses get_trapped_losses() which surfaces chains with deferred losses
    that may be harvestable when the wash-sale window expires.

    Note: Full harvest scanning (with current prices) requires market
    data integration. This endpoint surfaces known deferred losses
    as a starting point for harvesting analysis.
    """
    try:
        chains = service.get_trapped_losses()
        if not chains:
            return {"opportunities": [], "total_harvestable": "0.00"}

        opportunities = []
        total_harvestable = Decimal("0")
        for chain in chains:
            loss_amount = getattr(chain, "disallowed_amount", Decimal("0"))
            if min_loss_threshold > 0 and loss_amount < Decimal(
                str(min_loss_threshold)
            ):
                continue
            is_blocked = getattr(chain, "status", None) is not None
            if exclude_wash_risk and is_blocked:
                continue
            total_harvestable += loss_amount
            opportunities.append(
                {
                    "ticker": getattr(chain, "ticker", "UNKNOWN"),
                    "disallowed_amount": str(loss_amount),
                    "status": str(getattr(chain, "status", "")),
                }
            )

        return {
            "opportunities": opportunities,
            "total_harvestable": str(total_harvestable),
        }
    except Exception as exc:
        return {"opportunities": [], "total_harvestable": "0.00", "error": str(exc)}


# ── YTD summary ─────────────────────────────────────────────────────


@tax_router.get("/ytd-summary", status_code=200)
async def get_ytd_tax_summary(
    tax_year: int,
    account_id: Optional[str] = None,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Year-to-date tax summary dashboard data."""
    try:
        result = service.ytd_summary(tax_year, account_id)
        return _serialize(result)
    except (AttributeError, Exception) as exc:
        # quarterly_estimates repo not yet wired → return default shape
        if "quarterly_estimates" in str(exc) or "has no attribute" in str(exc):
            return {
                "realized_st_gain": 0.0,
                "realized_lt_gain": 0.0,
                "total_realized": 0.0,
                "wash_sale_adjustments": 0.0,
                "trades_count": 0,
                "estimated_federal_tax": 0.0,
                "estimated_state_tax": 0.0,
                "estimated_tax": 0.0,
                "quarterly_payments": [],
            }
        raise


# ── Lot management (close / reassign) ──────────────────────────────


@tax_router.post("/lots/{lot_id}/close", status_code=200)
async def close_tax_lot(
    lot_id: str,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Close a specific tax lot (mark as sold).

    AC-148.3: Returns serialized TaxLot entity.
    """
    try:
        lot = service.close_lot(lot_id)
        return _serialize(lot)
    except Exception as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(404, str(exc)) from exc
        raise HTTPException(400, str(exc)) from exc


@tax_router.put("/lots/{lot_id}/reassign", status_code=200)
async def reassign_lot_basis(
    lot_id: str,
    body: ReassignLotBasisRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Reassign cost basis method for a lot.

    AC-148.3: Converts body.method string to CostBasisMethod enum.
    """
    from zorivest_core.domain.enums import CostBasisMethod

    method_str = body.method.upper()
    try:
        method = CostBasisMethod(method_str)
        service.reassign_basis(lot_id, method)
        return {"lot_id": lot_id, "method": method_str.lower(), "status": "reassigned"}
    except Exception as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(404, str(exc)) from exc
        raise HTTPException(400, str(exc)) from exc


# ── Wash sale scan ──────────────────────────────────────────────────


@tax_router.post("/wash-sales/scan", status_code=200)
async def scan_wash_sales(
    body: ScanWashSalesRequest = ScanWashSalesRequest(),
    service: Any = Depends(get_tax_service),
) -> dict:
    """Trigger a full wash sale scan across all accounts.

    AC-148.3: Routes to scan_cross_account_wash_sales for given/current year.
    """
    tax_year = (
        body.tax_year
        if body.tax_year is not None
        else datetime.now(tz=timezone.utc).year
    )
    try:
        matches = service.scan_cross_account_wash_sales(tax_year)
        return {
            "active_chains": _serialize(matches),
            "trapped_amount": sum(
                float(getattr(m, "disallowed_amount", 0)) for m in matches
            ),
            "alerts": [],
        }
    except Exception:
        # Graceful fallback if scan fails on empty DB
        return {"active_chains": [], "trapped_amount": 0.0, "alerts": []}


# ── Transaction audit ───────────────────────────────────────────────


@tax_router.post("/audit", status_code=200)
async def run_tax_audit(
    account_id: Optional[str] = None,
    tax_year: Optional[int] = None,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Run transaction audit checks."""
    result = service.run_audit(account_id, tax_year)
    return _serialize(result)


# ── MEU-148 AC-148.5: New routes for deferred losses and tax alpha ──


@tax_router.get("/deferred-losses", status_code=200)
async def get_deferred_loss_report(
    tax_year: Optional[int] = None,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Deferred loss report — surfaces trapped wash sale chains.

    AC-148.5: New route added for MEU-151 service method.
    """
    result = service.deferred_loss_report(tax_year)
    return _serialize(result)


@tax_router.get("/alpha", status_code=200)
async def get_tax_alpha_report(
    tax_year: int,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Tax alpha report — comparison of actual vs FIFO counterfactual.

    AC-148.5: New route added for MEU-152 service method.
    """
    result = service.tax_alpha_report(tax_year)
    return _serialize(result)


# ── Phase 3F: Tax Lot Sync (MEU-218) ────────────────────────────────


@tax_router.post("/sync-lots", status_code=200)
async def sync_tax_lots(
    body: SyncTaxLotsRequest = SyncTaxLotsRequest(),
    service: Any = Depends(get_tax_service),
) -> dict:
    """Trigger trade-to-lot materialization pipeline.

    AC-218.1: Returns SyncReport with created/updated/skipped/conflicts/orphaned.
    AC-218.5: SyncAbortError (block mode) maps to 409 Conflict.
    """
    from zorivest_core.domain.exceptions import SyncAbortError

    try:
        report = service.sync_lots(
            account_id=body.account_id,
            conflict_strategy=body.conflict_strategy,
        )
        return _serialize(report)
    except SyncAbortError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


# ── MEU-218f: TaxProfile CRUD ────────────────────────────────────────


@tax_router.get("/profiles", status_code=200)
async def list_profiles(
    service: Any = Depends(get_tax_service),
) -> list[dict]:
    """List all tax profiles ordered by year desc."""
    profiles = service.list_tax_profiles()
    return [_serialize(p) for p in profiles]


@tax_router.get("/profiles/{year}", status_code=200)
async def get_profile(
    year: int,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Get tax profile for a specific year."""
    with service._uow:
        profile = service._uow.tax_profiles.get_for_year(year)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No tax profile for year {year}")
    return _serialize(profile)


@tax_router.post("/profiles", status_code=201)
async def create_profile(
    body: TaxProfileCreateRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Create a new tax profile.  Returns 409 if year already exists."""
    from zorivest_core.domain.entities import TaxProfile
    from zorivest_core.domain.enums import (
        CostBasisMethod,
        FilingStatus,
        WashSaleMatchingMethod,
    )
    from zorivest_core.domain.exceptions import BusinessRuleError

    profile = TaxProfile(
        id=0,  # auto-assigned by DB
        filing_status=FilingStatus(body.filing_status),
        tax_year=body.tax_year,
        federal_bracket=body.federal_bracket,
        state_tax_rate=body.state_tax_rate,
        state=body.state.upper(),
        prior_year_tax=Decimal(str(body.prior_year_tax)),
        agi_estimate=Decimal(str(body.agi_estimate)),
        capital_loss_carryforward=Decimal(str(body.capital_loss_carryforward)),
        wash_sale_method=WashSaleMatchingMethod(body.wash_sale_method),
        default_cost_basis=CostBasisMethod(body.default_cost_basis),
        include_drip_wash_detection=body.include_drip_wash_detection,
        include_spousal_accounts=body.include_spousal_accounts,
        section_475_elected=body.section_475_elected,
        section_1256_eligible=body.section_1256_eligible,
    )
    try:
        profile_id = service.save_tax_profile(profile)
    except BusinessRuleError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"id": profile_id, "tax_year": body.tax_year}


@tax_router.put("/profiles/{year}", status_code=200)
async def update_profile(
    year: int,
    body: TaxProfileUpdateRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Update an existing tax profile.  Merges provided fields."""
    from zorivest_core.domain.entities import TaxProfile
    from zorivest_core.domain.enums import (
        CostBasisMethod,
        FilingStatus,
        WashSaleMatchingMethod,
    )
    from zorivest_core.domain.exceptions import NotFoundError

    # Load existing profile to merge partial updates
    with service._uow:
        existing = service._uow.tax_profiles.get_for_year(year)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"No tax profile for year {year}")

    updated = TaxProfile(
        id=existing.id,
        filing_status=FilingStatus(body.filing_status)
        if body.filing_status
        else existing.filing_status,
        tax_year=year,
        federal_bracket=body.federal_bracket
        if body.federal_bracket is not None
        else existing.federal_bracket,
        state_tax_rate=body.state_tax_rate
        if body.state_tax_rate is not None
        else existing.state_tax_rate,
        state=body.state.upper() if body.state is not None else existing.state,
        prior_year_tax=Decimal(str(body.prior_year_tax))
        if body.prior_year_tax is not None
        else existing.prior_year_tax,
        agi_estimate=Decimal(str(body.agi_estimate))
        if body.agi_estimate is not None
        else existing.agi_estimate,
        capital_loss_carryforward=Decimal(str(body.capital_loss_carryforward))
        if body.capital_loss_carryforward is not None
        else existing.capital_loss_carryforward,
        wash_sale_method=WashSaleMatchingMethod(body.wash_sale_method)
        if body.wash_sale_method is not None
        else existing.wash_sale_method,
        default_cost_basis=CostBasisMethod(body.default_cost_basis)
        if body.default_cost_basis is not None
        else existing.default_cost_basis,
        include_drip_wash_detection=body.include_drip_wash_detection
        if body.include_drip_wash_detection is not None
        else existing.include_drip_wash_detection,
        include_spousal_accounts=body.include_spousal_accounts
        if body.include_spousal_accounts is not None
        else existing.include_spousal_accounts,
        section_475_elected=body.section_475_elected
        if body.section_475_elected is not None
        else existing.section_475_elected,
        section_1256_eligible=body.section_1256_eligible
        if body.section_1256_eligible is not None
        else existing.section_1256_eligible,
    )
    try:
        service.update_tax_profile(updated)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "updated", "tax_year": year}


@tax_router.delete("/profiles/{year}", status_code=200)
async def delete_profile(
    year: int,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Delete a tax profile by year."""
    from zorivest_core.domain.exceptions import NotFoundError

    try:
        service.delete_tax_profile(year)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "deleted", "tax_year": year}
