# packages/api/src/zorivest_api/routes/analytics.py
"""Analytics stub routes — expectancy, drawdown, SQN, execution quality, etc.

Source: 04e-api-analytics.md §Analytics Routes
MEU-28: 10 stub endpoints (services built in Phase 2.75).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from zorivest_api.dependencies import get_analytics_service, get_review_service, require_unlocked_db

analytics_router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_unlocked_db)],
)


@analytics_router.get("/expectancy")
async def get_expectancy(
    account_id: str | None = None,
    period: str = "all",
    service: Any = Depends(get_analytics_service),
) -> dict:
    """Win rate, avg win/loss, expectancy per trade, Kelly %."""
    return service.get_expectancy(account_id, period)


@analytics_router.get("/drawdown")
async def get_drawdown_table(
    account_id: str | None = None,
    simulations: int = 10000,
    service: Any = Depends(get_analytics_service),
) -> dict:
    """Monte Carlo drawdown probability table."""
    return service.get_drawdown(account_id, simulations)


@analytics_router.get("/execution-quality")
async def get_execution_quality(
    trade_id: str | None = None,
    service: Any = Depends(get_analytics_service),
) -> dict:
    """Execution quality scores."""
    return service.get_execution_quality(trade_id)


@analytics_router.get("/pfof-report")
async def get_pfof_report(
    account_id: str,
    period: str = "ytd",
    service: Any = Depends(get_analytics_service),
) -> dict:
    """PFOF impact analysis report — labeled as ESTIMATE."""
    return service.get_pfof_report(account_id, period)


@analytics_router.get("/strategy-breakdown")
async def get_strategy_breakdown(
    account_id: str | None = None,
    service: Any = Depends(get_analytics_service),
) -> dict:
    """P&L breakdown by strategy name."""
    return service.get_strategy_breakdown(account_id)


@analytics_router.get("/sqn")
async def get_sqn(
    account_id: str | None = None,
    period: str = "all",
    service: Any = Depends(get_analytics_service),
) -> dict:
    """System Quality Number (SQN)."""
    return service.get_sqn(account_id, period)


@analytics_router.get("/cost-of-free")
async def get_cost_of_free(
    account_id: str | None = None,
    period: str = "ytd",
    service: Any = Depends(get_analytics_service),
) -> dict:
    """'Cost of Free' report — hidden costs estimate."""
    return service.get_cost_of_free(account_id, period)


@analytics_router.post("/ai-review")
async def ai_review_trade(
    body: dict,
    service: Any = Depends(get_review_service),
) -> dict:
    """Multi-persona AI trade review. Opt-in with budget cap."""
    return service.ai_review(body)


@analytics_router.post("/excursion/{trade_exec_id}")
async def enrich_trade_excursion(
    trade_exec_id: str,
    service: Any = Depends(get_analytics_service),
) -> dict:
    """Compute MFE/MAE/BSO metrics for a trade."""
    return service.enrich_trade(trade_exec_id)


@analytics_router.post("/options-strategy")
async def detect_options_strategy(
    body: dict,
    service: Any = Depends(get_analytics_service),
) -> dict:
    """Auto-detect multi-leg options strategy type."""
    return service.detect_strategy(body.get("leg_exec_ids", []))
