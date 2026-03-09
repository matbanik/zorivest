# packages/api/src/zorivest_api/routes/tax.py
"""Tax routes — simulation, estimation, wash sales, lots, quarterly, harvest, audit.

Source: 04f-api-tax.md §Tax Routes
MEU-29: 12 endpoints with Pydantic request schemas. All mode-gated.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from zorivest_api.dependencies import get_tax_service, require_unlocked_db

tax_router = APIRouter(
    prefix="/api/v1/tax",
    tags=["tax"],
    dependencies=[Depends(require_unlocked_db)],
)


# ── Request schemas ─────────────────────────────────────────────────


class SimulateTaxRequest(BaseModel):
    ticker: str
    action: Literal["sell", "cover"]
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)
    account_id: str
    cost_basis_method: Literal["fifo", "lifo", "specific_id", "avg_cost"] = "fifo"


class EstimateTaxRequest(BaseModel):
    tax_year: int
    account_id: Optional[str] = None
    filing_status: Literal["single", "married_joint", "married_separate", "head_of_household"] = "single"
    include_unrealized: bool = False


class WashSaleRequest(BaseModel):
    account_id: str
    ticker: Optional[str] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None


class RecordPaymentRequest(BaseModel):
    quarter: Literal["Q1", "Q2", "Q3", "Q4"]
    tax_year: int
    payment_amount: float = Field(gt=0)
    confirm: bool


# ── Tax simulation ──────────────────────────────────────────────────


@tax_router.post("/simulate", status_code=200)
async def simulate_tax_impact(
    body: SimulateTaxRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Pre-trade what-if tax simulation."""
    return service.simulate_impact(body)


# ── Tax estimation ──────────────────────────────────────────────────


@tax_router.post("/estimate", status_code=200)
async def estimate_tax(
    body: EstimateTaxRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Compute overall tax estimate."""
    return service.estimate(body)


# ── Wash sale detection ─────────────────────────────────────────────


@tax_router.post("/wash-sales", status_code=200)
async def find_wash_sales(
    body: WashSaleRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Detect wash sale chains/conflicts within 30-day windows."""
    return service.find_wash_sales(body)


# ── Tax lot management ──────────────────────────────────────────────


@tax_router.get("/lots", status_code=200)
async def get_tax_lots(
    account_id: str,
    ticker: Optional[str] = None,
    status: Literal["open", "closed", "all"] = "all",
    sort_by: Literal["acquired_date", "cost_basis", "gain_loss"] = "acquired_date",
    service: Any = Depends(get_tax_service),
) -> dict:
    """List tax lots with basis, holding period, and gain/loss."""
    return service.get_lots(account_id, ticker, status, sort_by)


# ── Quarterly estimates ─────────────────────────────────────────────


@tax_router.get("/quarterly", status_code=200)
async def get_quarterly_estimate(
    quarter: Literal["Q1", "Q2", "Q3", "Q4"],
    tax_year: int,
    estimation_method: Literal["annualized", "actual", "prior_year"] = "annualized",
    service: Any = Depends(get_tax_service),
) -> dict:
    """Compute quarterly estimated tax payment obligations."""
    return service.quarterly_estimate(quarter, tax_year, estimation_method)


@tax_router.post("/quarterly/payment", status_code=200)
async def record_quarterly_tax_payment(
    body: RecordPaymentRequest,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Record an actual quarterly tax payment. Requires confirm=true."""
    if not body.confirm:
        raise HTTPException(400, "confirm must be true")
    return service.record_payment(body)


# ── Loss harvesting ─────────────────────────────────────────────────


@tax_router.get("/harvest", status_code=200)
async def harvest_losses(
    account_id: Optional[str] = None,
    min_loss_threshold: float = 0.0,
    exclude_wash_risk: bool = False,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Scan portfolio for harvestable losses."""
    return service.harvest_scan(account_id, min_loss_threshold, exclude_wash_risk)


# ── YTD summary ─────────────────────────────────────────────────────


@tax_router.get("/ytd-summary", status_code=200)
async def get_ytd_tax_summary(
    tax_year: int,
    account_id: Optional[str] = None,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Year-to-date tax summary dashboard data."""
    return service.ytd_summary(tax_year, account_id)


# ── Lot management (close / reassign) ──────────────────────────────


@tax_router.post("/lots/{lot_id}/close", status_code=200)
async def close_tax_lot(
    lot_id: str,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Close a specific tax lot (mark as sold)."""
    return service.close_lot(lot_id)


@tax_router.put("/lots/{lot_id}/reassign", status_code=200)
async def reassign_lot_basis(
    lot_id: str,
    body: dict,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Reassign cost basis method for a lot."""
    return service.reassign_basis(lot_id, body)


# ── Wash sale scan ──────────────────────────────────────────────────


@tax_router.post("/wash-sales/scan", status_code=200)
async def scan_wash_sales(
    account_id: Optional[str] = None,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Trigger a full wash sale scan across all accounts."""
    return service.scan_wash_sales(account_id)


# ── Transaction audit ───────────────────────────────────────────────


@tax_router.post("/audit", status_code=200)
async def run_tax_audit(
    account_id: Optional[str] = None,
    tax_year: Optional[int] = None,
    service: Any = Depends(get_tax_service),
) -> dict:
    """Run transaction audit checks."""
    return service.run_audit(account_id, tax_year)
