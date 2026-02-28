# Phase 4f: REST API — Tax

> Part of [Phase 4: REST API](04-rest-api.md) | Tag: `tax`
>
> Tax computation, lot management, quarterly estimates, wash sale detection, loss harvesting, YTD summary, and audit endpoints.

---

## Tax Routes

> Tax computation and lot management endpoints consumed by MCP tools in [05h-mcp-tax.md](05h-mcp-tax.md).

```python
# packages/api/src/zorivest_api/routes/tax.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal

tax_router = APIRouter(prefix="/api/v1/tax", tags=["tax"])


# ── Request / Response schemas ──────────────────────────────

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


# ── Tax simulation ──────────────────────────────────────────

@tax_router.post("/simulate", status_code=200)
async def simulate_tax_impact(body: SimulateTaxRequest,
                               service = Depends(get_tax_service)):
    """Pre-trade what-if tax simulation.
    Returns lot-level close preview, ST/LT split, estimated tax, wash risk, hold-savings."""
    return service.simulate_impact(body)


# ── Tax estimation ──────────────────────────────────────────

@tax_router.post("/estimate", status_code=200)
async def estimate_tax(body: EstimateTaxRequest,
                        service = Depends(get_tax_service)):
    """Compute overall tax estimate from profile + trading data.
    Returns federal + state estimate with bracket breakdown."""
    return service.estimate(body)


# ── Wash sale detection ─────────────────────────────────────

@tax_router.post("/wash-sales", status_code=200)
async def find_wash_sales(body: WashSaleRequest,
                           service = Depends(get_tax_service)):
    """Detect wash sale chains/conflicts within 30-day windows.
    Returns wash sale chains with disallowed amounts and affected tickers."""
    return service.find_wash_sales(body)


# ── Tax lot management ──────────────────────────────────────

@tax_router.get("/lots", status_code=200)
async def get_tax_lots(account_id: str,
                       ticker: Optional[str] = None,
                       status: Literal["open", "closed", "all"] = "all",
                       sort_by: Literal["acquired_date", "cost_basis", "gain_loss"] = "acquired_date",
                       service = Depends(get_tax_service)):
    """List tax lots with basis, holding period, and gain/loss fields."""
    return service.get_lots(account_id, ticker, status, sort_by)


# ── Quarterly estimates ─────────────────────────────────────

@tax_router.get("/quarterly", status_code=200)
async def get_quarterly_estimate(quarter: Literal["Q1", "Q2", "Q3", "Q4"],
                                  tax_year: int,
                                  estimation_method: Literal["annualized", "actual", "prior_year"] = "annualized",
                                  service = Depends(get_tax_service)):
    """Compute quarterly estimated tax payment obligations (read-only).
    Returns required/paid/due/penalty/due_date."""
    return service.quarterly_estimate(quarter, tax_year, estimation_method)

@tax_router.post("/quarterly/payment", status_code=200)
async def record_quarterly_tax_payment(body: RecordPaymentRequest,
                                        service = Depends(get_tax_service)):
    """Record an actual quarterly tax payment. Requires confirm=true."""
    if not body.confirm:
        raise HTTPException(400, "confirm must be true")
    return service.record_payment(body)


# ── Loss harvesting ─────────────────────────────────────────

@tax_router.get("/harvest", status_code=200)
async def harvest_losses(account_id: Optional[str] = None,
                          min_loss_threshold: float = 0.0,
                          exclude_wash_risk: bool = False,
                          service = Depends(get_tax_service)):
    """Scan portfolio for harvestable losses.
    Returns ranked opportunities + wash-risk annotations + totals."""
    return service.harvest_scan(account_id, min_loss_threshold, exclude_wash_risk)


# ── YTD summary ─────────────────────────────────────────────

@tax_router.get("/ytd-summary", status_code=200)
async def get_ytd_tax_summary(tax_year: int,
                               account_id: Optional[str] = None,
                               service = Depends(get_tax_service)):
    """Year-to-date tax summary dashboard data.
    Returns aggregated ST/LT, wash adjustments, estimated tax."""
    return service.ytd_summary(tax_year, account_id)


# ── Lot management (close / reassign) ──────────────────────

@tax_router.post("/lots/{lot_id}/close", status_code=200)
async def close_tax_lot(lot_id: str,
                        service = Depends(get_tax_service)):
    """Close a specific tax lot (mark as sold).
    Returns updated lot with realized gain/loss."""
    return service.close_lot(lot_id)

@tax_router.put("/lots/{lot_id}/reassign", status_code=200)
async def reassign_lot_basis(lot_id: str, body: dict,
                              service = Depends(get_tax_service)):
    """Reassign cost basis method for a lot (T+1 window).
    body: {method: 'fifo'|'lifo'|'hifo'|'specific_id'}."""
    return service.reassign_basis(lot_id, body)


# ── Wash sale scan ──────────────────────────────────────────

@tax_router.post("/wash-sales/scan", status_code=200)
async def scan_wash_sales(account_id: Optional[str] = None,
                           service = Depends(get_tax_service)):
    """Trigger a full wash sale scan across all accounts.
    Returns active chains, trapped amounts, and prevention alerts."""
    return service.scan_wash_sales(account_id)


# ── Transaction audit ───────────────────────────────────────

@tax_router.post("/audit", status_code=200)
async def run_tax_audit(account_id: Optional[str] = None,
                         tax_year: Optional[int] = None,
                         service = Depends(get_tax_service)):
    """Run transaction audit checks (missing basis, dupes, orphaned lots, etc.).
    Returns categorized findings with severity levels."""
    return service.run_audit(account_id, tax_year)
```

## E2E Tests

```python
# tests/e2e/test_tax_api.py

def test_simulate_tax_impact(client):
    response = client.post("/api/v1/tax/simulate", json={
        "ticker": "SPY", "action": "sell", "quantity": 100,
        "price": 500.0, "account_id": "DU123", "cost_basis_method": "fifo"
    })
    assert response.status_code == 200
    data = response.json()
    assert "estimated_tax" in data
    assert "lots" in data

def test_get_tax_lots(client):
    response = client.get("/api/v1/tax/lots?account_id=DU123")
    assert response.status_code == 200

def test_quarterly_estimate(client):
    response = client.get("/api/v1/tax/quarterly?quarter=Q1&tax_year=2026")
    assert response.status_code == 200
    assert "required" in response.json()

def test_record_payment_requires_confirm(client):
    response = client.post("/api/v1/tax/quarterly/payment", json={
        "quarter": "Q1", "tax_year": 2026, "payment_amount": 5000, "confirm": False
    })
    assert response.status_code == 400

def test_harvest_losses(client):
    response = client.get("/api/v1/tax/harvest")
    assert response.status_code == 200
    assert "opportunities" in response.json()

def test_ytd_summary(client):
    response = client.get("/api/v1/tax/ytd-summary?tax_year=2026")
    assert response.status_code == 200
```

## Consumer Notes

- **MCP tools:** `simulate_tax_impact`, `estimate_tax`, `find_wash_sales`, `get_tax_lots`, `get_quarterly_estimate`, `record_quarterly_tax_payment`, `harvest_losses`, `get_ytd_tax_summary` ([05h](05h-mcp-tax.md))
- **GUI pages:** [06g-gui-tax.md](06g-gui-tax.md) — tax dashboard, lot viewer, wash sale scanner, quarterly tracker
