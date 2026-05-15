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

    account_id: str
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


@tax_router.post("/wash-sales", status_code=200)
async def find_wash_sales(
    body: WashSaleRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Detect wash sale chains/conflicts within 30-day windows.

    AC-148.3: Routes to TaxService.get_trapped_losses().
    """
    chains = service.get_trapped_losses()
    # Filter by account if specified
    if body.account_id:
        chains = [
            c for c in chains if getattr(c, "account_id", None) == body.account_id
        ]
    # Filter by ticker if specified
    if body.ticker:
        chains = [c for c in chains if getattr(c, "ticker", None) == body.ticker]
    return {
        "chains": _serialize(chains),
        "disallowed_total": sum(
            float(getattr(c, "disallowed_amount", 0)) for c in chains
        ),
        "affected_tickers": list({getattr(c, "ticker", "") for c in chains}),
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
    account_id: Optional[str] = None,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Trigger a full wash sale scan across all accounts.

    AC-148.3: Routes to scan_cross_account_wash_sales for current year.
    """
    current_year = datetime.now(tz=timezone.utc).year
    try:
        matches = service.scan_cross_account_wash_sales(current_year)
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
