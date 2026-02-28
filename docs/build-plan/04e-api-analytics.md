# Phase 4e: REST API — Analytics

> Part of [Phase 4: REST API](04-rest-api.md) | Tag: `analytics`
>
> Quantitative analysis endpoints: expectancy, drawdown, SQN, execution quality, PFOF, strategy breakdown, cost-of-free, AI review, excursion, options strategy detection, mistakes, fees, calculator.

---

## Analytics Routes (§10–§15, §21, §22)

```python
# packages/api/src/zorivest_api/routes/analytics.py

analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@analytics_router.get("/expectancy")
async def get_expectancy(account_id: str | None = None, period: str = "all",
                         service = Depends(get_analytics_service)):
    """Win rate, avg win/loss, expectancy per trade, Kelly %."""
    ...

@analytics_router.get("/drawdown")
async def get_drawdown_table(account_id: str | None = None,
                             simulations: int = 10000,
                             service = Depends(get_analytics_service)):
    """Monte Carlo drawdown probability table."""
    ...

@analytics_router.get("/execution-quality")
async def get_execution_quality(trade_id: str | None = None,
                                 service = Depends(get_analytics_service)):
    """Execution quality scores (gated on NBBO data availability)."""
    ...

@analytics_router.get("/pfof-report")
async def get_pfof_report(account_id: str, period: str = "ytd",
                           service = Depends(get_analytics_service)):
    """PFOF impact analysis report — labeled as ESTIMATE."""
    ...

@analytics_router.get("/strategy-breakdown")
async def get_strategy_breakdown(account_id: str | None = None,
                                  service = Depends(get_analytics_service)):
    """P&L breakdown by strategy name."""
    ...

@analytics_router.get("/sqn")
async def get_sqn(account_id: str | None = None,
                   period: str = "all",
                   service = Depends(get_analytics_service)):
    """System Quality Number (SQN) — Van Tharp metric. Grade: Holy Grail/Excellent/Good/Average/Poor."""
    ...

@analytics_router.get("/cost-of-free")
async def get_cost_of_free(account_id: str | None = None,
                             period: str = "ytd",
                             service = Depends(get_analytics_service)):
    """'Cost of Free' report — total hidden costs of PFOF routing + fees."""
    ...

@analytics_router.post("/ai-review")
async def ai_review_trade(body: dict,
                           service = Depends(get_review_service)):
    """Multi-persona AI trade review. Opt-in with budget cap."""
    ...


# ── Excursion analysis ──────────────────────────────────────

@analytics_router.post("/excursion/{trade_exec_id}")
async def enrich_trade_excursion(trade_exec_id: str,
                                  service = Depends(get_analytics_service)):
    """Compute MFE/MAE/BSO metrics for a trade using historical bar data.
    Writes computed excursion data to the trade record."""
    return service.enrich_trade(trade_exec_id)


# ── Options strategy detection ──────────────────────────────

@analytics_router.post("/options-strategy")
async def detect_options_strategy(body: dict,
                                   service = Depends(get_analytics_service)):
    """Auto-detect multi-leg options strategy type from execution IDs."""
    return service.detect_strategy(body.get("leg_exec_ids", []))
```

## Mistake Tracking Routes (§17)

```python
# packages/api/src/zorivest_api/routes/mistakes.py

mistakes_router = APIRouter(prefix="/api/v1/mistakes", tags=["mistakes"])

@mistakes_router.post("/", status_code=201)
async def track_mistake(body: dict, service = Depends(get_review_service)):
    """Tag a trade with a mistake category and estimated cost."""
    ...

@mistakes_router.get("/summary")
async def mistake_summary(account_id: str | None = None,
                           period: str = "ytd",
                           service = Depends(get_review_service)):
    """Summary: mistakes by category, total cost, trend."""
    ...
```

## Fee Summary Routes (§9)

```python
# packages/api/src/zorivest_api/routes/fees.py

fees_router = APIRouter(prefix="/api/v1/fees", tags=["fees"])

@fees_router.get("/summary")
async def fee_summary(account_id: str | None = None,
                       period: str = "ytd",
                       service = Depends(get_analytics_service)):
    """Fee breakdown by type, broker, and % of P&L."""
    ...
```

## Calculator Routes

> Source: [GUI Calculator](06h-gui-calculator.md), [MCP Server](05-mcp-server.md)

```python
# packages/api/src/zorivest_api/routes/calculator.py

from fastapi import APIRouter
from pydantic import BaseModel

calculator_router = APIRouter(prefix="/api/v1/calculator", tags=["calculator"])

class PositionSizeRequest(BaseModel):
    balance: float
    risk_pct: float
    entry_price: float
    stop_loss: float
    target_price: float

@calculator_router.post("/position-size")
async def calculate_position_size(body: PositionSizeRequest):
    """Calculate position size based on risk parameters."""
    ...
```

## Consumer Notes

- **MCP tools:** `get_expectancy_metrics`, `simulate_drawdown`, `get_sqn`, `enrich_trade_excursion`, `detect_options_strategy`, `ai_review_trade`, `estimate_pfof_impact`, `get_fee_breakdown`, `score_execution_quality`, `get_cost_of_free` ([05c](05c-mcp-trade-analytics.md))
- **GUI pages:** [06-gui.md](06-gui.md) — analytics dashboard, strategy breakdown, fee/mistake reports
