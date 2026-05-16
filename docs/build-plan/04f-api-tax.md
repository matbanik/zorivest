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

## TaxProfile CRUD (MEU-148a)

> [!IMPORTANT]
> MEU-148a (`tax-profile-api`) exposes the `TaxProfile` entity as a dedicated REST resource.
> Persistence is backed by `SettingsRegistry` — the 12 TaxProfile fields are registered as
> typed settings keys, then surfaced via a thin `/tax/profile` endpoint that reads/writes
> the settings as a single JSON object.

### Prerequisites

| Dependency | MEU | Status | What It Provides |
|-----------|-----|--------|-----------------|
| SettingsRegistry + Resolver | MEU-18 | ✅ | Key-value storage, type coercion, validation |
| TaxProfile entity | MEU-124 | ✅ | Domain model with 12 fields |
| Tax API router | MEU-148 | ✅ | `/api/v1/tax` prefix and router |

### Request / Response Schemas

```python
# Addition to packages/api/src/zorivest_api/routes/tax.py

class TaxProfileResponse(BaseModel):
    """Current TaxProfile configuration as a flat JSON object."""
    filing_status: Literal["single", "married_joint", "married_separate", "head_of_household"] = "single"
    tax_year: int = 2026
    federal_bracket: float = Field(ge=0, le=1, default=0.22)
    state_tax_rate: float = Field(ge=0, le=1, default=0.05)
    state: str = "TX"
    prior_year_tax: float = Field(ge=0, default=0.0)
    agi_estimate: float = Field(ge=0, default=0.0)
    capital_loss_carryforward: float = Field(ge=0, default=0.0)
    wash_sale_method: Literal["conservative", "aggressive"] = "conservative"
    default_cost_basis: Literal["fifo", "lifo", "hifo", "specific_id", "max_lt_gain", "max_lt_loss", "max_st_gain", "max_st_loss"] = "fifo"
    section_475_elected: bool = False
    section_1256_eligible: bool = False

class TaxProfileUpdateRequest(BaseModel):
    """Partial update — only include fields you want to change."""
    model_config = ConfigDict(extra="forbid")
    filing_status: Optional[Literal["single", "married_joint", "married_separate", "head_of_household"]] = None
    tax_year: Optional[int] = None
    federal_bracket: Optional[float] = Field(None, ge=0, le=1)
    state_tax_rate: Optional[float] = Field(None, ge=0, le=1)
    state: Optional[str] = None
    prior_year_tax: Optional[float] = Field(None, ge=0)
    agi_estimate: Optional[float] = Field(None, ge=0)
    capital_loss_carryforward: Optional[float] = Field(None, ge=0)
    wash_sale_method: Optional[Literal["conservative", "aggressive"]] = None
    default_cost_basis: Optional[Literal["fifo", "lifo", "hifo", "specific_id", "max_lt_gain", "max_lt_loss", "max_st_gain", "max_st_loss"]] = None
    section_475_elected: Optional[bool] = None
    section_1256_eligible: Optional[bool] = None
```

### Endpoints

```python
# ── TaxProfile CRUD ─────────────────────────────────────────

@tax_router.get("/profile", status_code=200)
async def get_tax_profile(settings_service = Depends(get_settings_service)):
    """Return the current TaxProfile as a single JSON object.
    All 12 fields are returned with their current values (or defaults)."""
    profile = settings_service.get_tax_profile()
    return TaxProfileResponse(**profile)

@tax_router.put("/profile", status_code=200)
async def update_tax_profile(body: TaxProfileUpdateRequest,
                              settings_service = Depends(get_settings_service)):
    """Partial update of TaxProfile fields.
    Only non-null fields in the request body are written.
    Returns the updated profile."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(422, "No fields to update — all values were null")
    settings_service.update_tax_profile(updates)
    profile = settings_service.get_tax_profile()
    return TaxProfileResponse(**profile)
```

### Settings Key Registration

The following 12 keys must be registered in `SettingsRegistry` (via `seed_defaults` or migration):

| Key | Type | Default | Validation |
|-----|------|---------|-----------|
| `tax.filing_status` | `str` | `"single"` | Enum: single, married_joint, married_separate, head_of_household |
| `tax.tax_year` | `int` | `2026` | ≥ 2020 |
| `tax.federal_bracket` | `float` | `0.22` | 0–1 |
| `tax.state_tax_rate` | `float` | `0.05` | 0–1 |
| `tax.state` | `str` | `"TX"` | 2-letter US state code |
| `tax.prior_year_tax` | `float` | `0.0` | ≥ 0 |
| `tax.agi_estimate` | `float` | `0.0` | ≥ 0 |
| `tax.capital_loss_carryforward` | `float` | `0.0` | ≥ 0 |
| `tax.wash_sale_method` | `str` | `"conservative"` | Enum: conservative, aggressive |
| `tax.default_cost_basis` | `str` | `"fifo"` | Enum: fifo, lifo, hifo, specific_id, max_lt_gain, max_lt_loss, max_st_gain, max_st_loss |
| `tax.section_475_elected` | `bool` | `false` | — |
| `tax.section_1256_eligible` | `bool` | `false` | — |

### Tests

```python
# tests/unit/test_tax_profile_api.py

def test_get_tax_profile_returns_defaults(client):
    response = client.get("/api/v1/tax/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["filing_status"] == "single"
    assert data["section_475_elected"] is False

def test_update_tax_profile_partial(client):
    response = client.put("/api/v1/tax/profile", json={
        "filing_status": "married_joint",
        "section_475_elected": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["filing_status"] == "married_joint"
    assert data["section_475_elected"] is True
    # Unchanged fields retain defaults
    assert data["state_tax_rate"] == 0.05

def test_update_tax_profile_rejects_empty(client):
    response = client.put("/api/v1/tax/profile", json={})
    assert response.status_code == 422

def test_update_tax_profile_rejects_unknown_fields(client):
    response = client.put("/api/v1/tax/profile", json={
        "unknown_field": "value"
    })
    assert response.status_code == 422
```

### MCP Actions (MEU-148a scope)

> [!IMPORTANT]
> The MCP spec in [05h-mcp-tax.md](05h-mcp-tax.md) does **not** include TaxProfile actions.
> MEU-148a must add `get_profile` and `update_profile` as new actions on `zorivest_tax`
> (compound tool, see [mcp-consolidation-proposal-v3.md](../../.agent/context/MCP/mcp-consolidation-proposal-v3.md)).

The TaxProfile CRUD is surfaced via two new `zorivest_tax` compound tool actions:

```typescript
// Addition to mcp-server/src/compound/tax-tool.ts

// ── get_profile ──────────────────────────────────────────────
get_profile: {
    schema: z.object({}).strict(),
    handler: async (): Promise<ToolResult> => {
        return textResult(await fetchApi("/tax/profile"));
    },
},

// ── update_profile ───────────────────────────────────────────
update_profile: {
    schema: z.object({
        filing_status: z.enum(["single", "married_joint", "married_separate", "head_of_household"]).optional(),
        tax_year: z.number().int().min(2020).optional(),
        federal_bracket: z.number().min(0).max(1).optional(),
        state_tax_rate: z.number().min(0).max(1).optional(),
        state: z.string().length(2).optional().describe("2-letter US state code"),
        prior_year_tax: z.number().min(0).optional(),
        agi_estimate: z.number().min(0).optional(),
        capital_loss_carryforward: z.number().min(0).optional(),
        wash_sale_method: z.enum(["conservative", "aggressive"]).optional(),
        default_cost_basis: z.enum(["fifo", "lifo", "hifo", "specific_id", "max_lt_gain", "max_lt_loss", "max_st_gain", "max_st_loss"]).optional(),
        section_475_elected: z.boolean().optional(),
        section_1256_eligible: z.boolean().optional(),
    }).strict(),
    handler: async (params): Promise<ToolResult> => {
        return textResult(await fetchApi("/tax/profile", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(params),
        }));
    },
},
```

**TAX_ACTIONS update:** Add `"get_profile"`, `"update_profile"` to TAX_ACTIONS array (9 → 11 actions).

**MCP tool description update:** Append `"get/update tax profile"` to the `zorivest_tax` description.

**Annotations for `update_profile`:**
- `readOnlyHint`: false
- `destructiveHint`: true — overwrites user's tax configuration
- `idempotentHint`: true — PUT semantics, same input = same state

### Downstream Consumers of TaxProfile

The following features read TaxProfile fields at runtime. When MEU-148a lands,
these consumers should switch from hardcoded defaults to SettingsRegistry lookups:

| Consumer | Field(s) Used | Current Behavior |
|----------|--------------|------------------|
| `TaxService.quarterly_estimate()` | `filing_status`, `federal_bracket`, `state_tax_rate`, `prior_year_tax` | Reads from TaxProfile entity in DB (if exists) |
| `TaxService.estimate()` | All bracket/rate fields | Reads from TaxProfile entity |
| `TaxService.simulate_impact()` | `default_cost_basis`, `wash_sale_method` | Falls back to FIFO/CONSERVATIVE defaults |
| `TaxService.scan_cross_account_wash_sales()` (MEU-218c) | `wash_sale_method` | Falls back to CONSERVATIVE default |
| `TaxService.harvest_scan()` | `section_475_elected` (excludes MTM positions) | Falls back to False |
| MEU-156 (Section toggles GUI) | `section_475_elected`, `section_1256_eligible` | **Blocked** — cannot persist without MEU-148a |

### Implementation Gap Analysis (2026-05-15)

> [!WARNING]
> **Current state:** TaxProfile CRUD has zero implementation at any layer.
> - `GET /api/v1/tax/profile` — endpoint does not exist
> - `PUT /api/v1/tax/profile` — endpoint does not exist
> - `zorivest_tax(action:"get_profile")` — MCP action does not exist
> - `zorivest_tax(action:"update_profile")` — MCP action does not exist
> - 12 `tax.*` SettingsRegistry keys — not registered
> - `SettingsService.get_tax_profile()` / `update_tax_profile()` — methods do not exist
>
> **Impact:** Features that depend on TaxProfile use hardcoded defaults or fall back to
> empty TaxProfile entities. This is functional but prevents users from configuring their
> tax situation (filing status, brackets, state rate) and prevents MEU-156 from persisting
> Section 475/1256 elections.
>
> **Priority:** Should be implemented before Phase 3 can be fully closed.
> The wash sale scan (MEU-218c) will read `wash_sale_method` from TaxProfile;
> until MEU-148a lands, it defaults to CONSERVATIVE.

### Verification

```bash
# TaxProfile-specific tests
uv run pytest tests/ -k "tax_profile" -v

# MCP action verification
# zorivest_tax(action:"get_profile") → returns 12-field TaxProfile JSON
# zorivest_tax(action:"update_profile", filing_status:"married_joint") → updates filing_status

# Full regression
uv run pytest tests/ --tb=no -q
```

---

## Consumer Notes

- **MCP tools (existing):** `simulate`, `estimate`, `wash_sales`, `lots`, `quarterly`, `record_payment`, `harvest`, `ytd_summary`, `sync_lots` — 9 actions on `zorivest_tax` ([05h](05h-mcp-tax.md))
- **MCP tools (MEU-148a):** `get_profile`, `update_profile` — 2 new actions on `zorivest_tax` (spec in this file §MCP Actions)
- **MCP tools (MEU-218c):** `scan_wash_sales` — 1 new action on `zorivest_tax` (ad-hoc, spec in execution plan)
- **GUI pages:** [06g-gui-tax.md](06g-gui-tax.md) — tax dashboard, lot viewer, wash sale scanner, quarterly tracker
- **GUI settings:** [06f-gui-settings.md](06f-gui-settings.md) `TaxProfilePage` (P3) — consumes `GET`/`PUT /api/v1/tax/profile` (MEU-148a)
- **Toggle persistence:** MEU-156 (`tax-section-toggles`) depends on MEU-148a for `section_475_elected` and `section_1256_eligible` write-back
- **Wash sale orchestration:** MEU-218c reads `TaxProfile.wash_sale_method` during cross-account scan; defaults to CONSERVATIVE until MEU-148a registers the `tax.wash_sale_method` setting key
