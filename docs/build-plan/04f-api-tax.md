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
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime

tax_router = APIRouter(prefix="/api/v1/tax", tags=["tax"])


# ── Request / Response schemas ──────────────────────────────

class SimulateTaxRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str
    action: Literal["sell", "cover"]
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)
    account_id: str
    cost_basis_method: Literal["fifo", "lifo", "specific_id", "avg_cost"] = "fifo"

class EstimateTaxRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tax_year: int
    account_id: Optional[str] = None
    filing_status: Literal["single", "married_joint", "married_separate", "head_of_household"] = "single"
    include_unrealized: bool = False

class WashSaleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_id: str
    ticker: Optional[str] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None

class RecordPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quarter: Literal["Q1", "Q2", "Q3", "Q4"]
    tax_year: int
    payment_amount: float = Field(gt=0)
    confirm: bool

class ReassignBasisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method: Literal["fifo", "lifo", "hifo", "specific_id"]


class TaxResponseEnvelope(BaseModel):
    """All tax endpoints return data inside this envelope.
    Tax data is informational only — not tax advice."""
    disclaimer: str = (
        "This output is for informational purposes only and does not constitute "
        "tax advice. Consult a qualified tax professional for your specific situation."
    )
    data: dict  # The actual response payload
    computed_at: datetime


# ── Tax simulation ──────────────────────────────────────────

@tax_router.post("/simulate", status_code=200)
async def simulate_tax_impact(body: SimulateTaxRequest,
                               service = Depends(get_tax_service)):
    """Pre-trade what-if tax simulation.
    Returns lot-level close preview, ST/LT split, estimated tax, wash risk, hold-savings."""
    result = service.simulate_impact(body)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── Tax estimation ──────────────────────────────────────────

@tax_router.post("/estimate", status_code=200)
async def estimate_tax(body: EstimateTaxRequest,
                        service = Depends(get_tax_service)):
    """Compute overall tax estimate from profile + trading data.
    Returns federal + state estimate with bracket breakdown."""
    result = service.estimate(body)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── Wash sale detection ─────────────────────────────────────

@tax_router.post("/wash-sales", status_code=200)
async def find_wash_sales(body: WashSaleRequest,
                           service = Depends(get_tax_service)):
    """Detect wash sale chains/conflicts within 30-day windows.
    Returns wash sale chains with disallowed amounts and affected tickers."""
    result = service.find_wash_sales(body)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── Tax lot management ──────────────────────────────────────

@tax_router.get("/lots", status_code=200)
async def get_tax_lots(account_id: str,
                       ticker: Optional[str] = None,
                       status: Literal["open", "closed", "all"] = "all",
                       sort_by: Literal["acquired_date", "cost_basis", "gain_loss"] = "acquired_date",
                       service = Depends(get_tax_service)):
    """List tax lots with basis, holding period, and gain/loss fields."""
    result = service.get_lots(account_id, ticker, status, sort_by)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── Quarterly estimates ─────────────────────────────────────

@tax_router.get("/quarterly", status_code=200)
async def get_quarterly_estimate(quarter: Literal["Q1", "Q2", "Q3", "Q4"],
                                  tax_year: int,
                                  estimation_method: Literal["annualized", "actual", "prior_year"] = "annualized",
                                  service = Depends(get_tax_service)):
    """Compute quarterly estimated tax payment obligations (read-only).
    Returns required/paid/due/penalty/due_date."""
    result = service.quarterly_estimate(quarter, tax_year, estimation_method)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())

@tax_router.post("/quarterly/payment", status_code=200)
async def record_quarterly_tax_payment(body: RecordPaymentRequest,
                                        service = Depends(get_tax_service)):
    """Record an actual quarterly tax payment. Requires confirm=true."""
    if not body.confirm:
        raise HTTPException(400, "confirm must be true")
    result = service.record_payment(body)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── Loss harvesting ─────────────────────────────────────────

@tax_router.get("/harvest", status_code=200)
async def harvest_losses(account_id: Optional[str] = None,
                          min_loss_threshold: float = 0.0,
                          exclude_wash_risk: bool = False,
                          service = Depends(get_tax_service)):
    """Scan portfolio for harvestable losses.
    Returns ranked opportunities + wash-risk annotations + totals."""
    result = service.harvest_scan(account_id, min_loss_threshold, exclude_wash_risk)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── YTD summary ─────────────────────────────────────────────

@tax_router.get("/ytd-summary", status_code=200)
async def get_ytd_tax_summary(tax_year: int,
                               account_id: Optional[str] = None,
                               service = Depends(get_tax_service)):
    """Year-to-date tax summary dashboard data.
    Returns aggregated ST/LT, wash adjustments, estimated tax."""
    result = service.ytd_summary(tax_year, account_id)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── Lot management (close / reassign) ──────────────────────

@tax_router.post("/lots/{lot_id}/close", status_code=200)
async def close_tax_lot(lot_id: str,
                        service = Depends(get_tax_service)):
    """Close a specific tax lot (mark as sold).
    Returns updated lot with realized gain/loss."""
    result = service.close_lot(lot_id)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())

@tax_router.put("/lots/{lot_id}/reassign", status_code=200)
async def reassign_lot_basis(lot_id: str, body: ReassignBasisRequest,
                              service = Depends(get_tax_service)):
    """Reassign cost basis method for a lot (T+1 window)."""
    result = service.reassign_basis(lot_id, body)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── Wash sale scan ──────────────────────────────────────────

@tax_router.post("/wash-sales/scan", status_code=200)
async def scan_wash_sales(account_id: Optional[str] = None,
                           service = Depends(get_tax_service)):
    """Trigger a full wash sale scan across all accounts.
    Returns active chains, trapped amounts, and prevention alerts."""
    result = service.scan_wash_sales(account_id)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())


# ── Transaction audit ───────────────────────────────────────

@tax_router.post("/audit", status_code=200)
async def run_tax_audit(account_id: Optional[str] = None,
                         tax_year: Optional[int] = None,
                         service = Depends(get_tax_service)):
    """Run transaction audit checks (missing basis, dupes, orphaned lots, etc.).
    Returns categorized findings with severity levels."""
    result = service.run_audit(account_id, tax_year)
    return TaxResponseEnvelope(data=result, computed_at=datetime.utcnow())
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

## Service Wiring (MEU-148)

> [!IMPORTANT]
> MEU-148 (`tax-api`) defines route contracts and wires only the route groups
> whose prerequisite `TaxService` methods are implemented (Phase 3A initially).
> Later route groups activate in their owning MEUs as the tax engine expands.

### Prerequisites

MEU-148 depends on the core tax engine being implemented first.
Routes are staged by prerequisite — only register routes when their upstream service MEU is complete:

| Routes | Required MEUs | Phase | Capability |
|--------|---------------|-------|------------|
| `/simulate`, `/lots`, `/lots/{id}/close`, `/lots/{id}/reassign` | MEU-123–126 | 3A | Lot management, gains calc |
| `/wash-sales`, `/wash-sales/scan` | MEU-130–131 | 3B | Wash sale detection |
| `/harvest` | MEU-138 | 3C | Loss harvesting scanner |
| `/quarterly`, `/quarterly/payment` | MEU-143, 145 | 3D | Quarterly estimates |
| `/estimate`, `/ytd-summary`, `/audit` | All above | 3A–D | Full tax engine |

> [!NOTE]
> Implement incrementally: routes go live as their prerequisite MEUs land.
> Do not register routes whose backing `TaxService` methods are not yet implemented.

### Wiring Tasks

1. **Create `TaxService`** in `packages/core/src/zorivest_core/services/tax_service.py`
   - Constructor takes `uow: UnitOfWork` (for tax lot persistence, trade lookups)
   - Initially implements Phase 3A methods only: `simulate_impact`, `get_lots`, `close_lot`, `reassign_basis`
   - Later phases add methods incrementally: `find_wash_sales` (3B), `harvest_scan` (3C), `quarterly_estimate`, `record_payment`, `ytd_summary`, `estimate` (3D)
2. **Wire into lifespan** (`main.py`)
   - Replace `app.state.tax_service = StubTaxService()` with `app.state.tax_service = TaxService(uow)`
   - Import from `zorivest_core.services.tax_service`
3. **Remove `StubTaxService`** from `stubs.py`
4. **Update `Depends(get_tax_service)`** — Verify the route dependency injection resolves to the real service
5. **Add integration tests** — Test the full route → service → UoW → DB path:
   - `tests/integration/test_tax_service.py` — Service-level tests with real UoW
   - Update `tests/e2e/test_tax_api.py` — Route-level tests with real DB

### Verification

```bash
# Tax-specific tests
uv run pytest tests/ -k "tax" -v

# Full regression (no regressions from wiring change)
uv run pytest tests/ --tb=no -q

# Type checking
uv run pyright packages/api/src/zorivest_api/main.py
```

## Consumer Notes

- **MCP tools:** `simulate_tax_impact`, `estimate_tax`, `find_wash_sales`, `get_tax_lots`, `get_quarterly_estimate`, `record_quarterly_tax_payment`, `harvest_losses`, `get_ytd_tax_summary` ([05h](05h-mcp-tax.md))
- **GUI pages:** [06g-gui-tax.md](06g-gui-tax.md) — tax dashboard, lot viewer, wash sale scanner, quarterly tracker
