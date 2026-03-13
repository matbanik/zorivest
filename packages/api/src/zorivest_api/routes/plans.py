# packages/api/src/zorivest_api/routes/plans.py
"""Trade Plan REST endpoints (MEU-66).

Source: 04a-api-trades.md §TradePlan endpoints (nested under /api/v1/trade-plans).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, model_validator

from zorivest_api.dependencies import get_report_service, require_unlocked_db

plan_router = APIRouter(prefix="/api/v1/trade-plans", tags=["trade-plans"])


# ── Request/Response schemas ────────────────────────────────────────────


class CreatePlanRequest(BaseModel):
    ticker: str
    direction: str = "BOT"
    conviction: str = "medium"
    strategy_name: str
    strategy_description: str = ""
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    entry_conditions: str = ""
    exit_conditions: str = ""
    timeframe: str = "intraday"
    account_id: Optional[str] = None
    # MCP short-name aliases (05d-mcp-trade-planning.md)
    entry: Optional[float] = None
    stop: Optional[float] = None
    target: Optional[float] = None
    conditions: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _map_mcp_aliases(cls, data: dict) -> dict:  # type: ignore[override]
        """Accept MCP compact names and map to long names."""
        if isinstance(data, dict):
            if "entry" in data and "entry_price" not in data:
                data["entry_price"] = data.pop("entry")
            if "stop" in data and "stop_loss" not in data:
                data["stop_loss"] = data.pop("stop")
            if "target" in data and "target_price" not in data:
                data["target_price"] = data.pop("target")
            if "conditions" in data and "entry_conditions" not in data:
                data["entry_conditions"] = data.pop("conditions")
        return data


class UpdatePlanRequest(BaseModel):
    ticker: Optional[str] = None
    direction: Optional[str] = None
    conviction: Optional[str] = None
    strategy_name: Optional[str] = None
    strategy_description: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    entry_conditions: Optional[str] = None
    exit_conditions: Optional[str] = None
    timeframe: Optional[str] = None
    status: Optional[str] = None
    linked_trade_id: Optional[str] = None
    account_id: Optional[str] = None


class PlanResponse(BaseModel):
    id: int
    ticker: str
    direction: str
    conviction: str
    strategy_name: str
    strategy_description: str
    entry_price: float
    stop_loss: float
    target_price: float
    entry_conditions: str
    exit_conditions: str
    timeframe: str
    risk_reward_ratio: float
    status: str
    linked_trade_id: Optional[str] = None
    account_id: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ── Plan routes ─────────────────────────────────────────────────────────


@plan_router.post(
    "", status_code=201,
    dependencies=[Depends(require_unlocked_db)],
)
async def create_plan(
    body: CreatePlanRequest,
    service=Depends(get_report_service),
):
    """Create a new trade plan."""
    data = body.model_dump(exclude={"entry", "stop", "target", "conditions"})
    try:
        plan = service.create_plan(data)
        return _to_response(plan)
    except ValueError as e:
        msg = str(e)
        if "duplicate" in msg.lower():
            raise HTTPException(409, msg)
        raise HTTPException(422, msg)


@plan_router.get(
    "",
    dependencies=[Depends(require_unlocked_db)],
)
async def list_plans(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service=Depends(get_report_service),
):
    """List trade plans with pagination."""
    plans = service.list_plans(limit=limit, offset=offset)
    return [_to_response(p) for p in plans]


@plan_router.get(
    "/{plan_id}",
    dependencies=[Depends(require_unlocked_db)],
)
async def get_plan(
    plan_id: int,
    service=Depends(get_report_service),
):
    """Get a trade plan by ID."""
    plan = service.get_plan(plan_id)
    if plan is None:
        raise HTTPException(404, f"Plan {plan_id} not found")
    return _to_response(plan)


@plan_router.put(
    "/{plan_id}",
    dependencies=[Depends(require_unlocked_db)],
)
async def update_plan(
    plan_id: int,
    body: UpdatePlanRequest,
    service=Depends(get_report_service),
):
    """Update a trade plan."""
    try:
        updates = body.model_dump(exclude_unset=True)
        # F2: Route linking through validation when setting linked_trade_id + executed
        linked_tid = updates.get("linked_trade_id")
        status_val = updates.get("status")
        if linked_tid and status_val == "executed":
            plan = service.link_plan_to_trade(plan_id, linked_tid)
        else:
            plan = service.update_plan(plan_id, updates)
        return _to_response(plan)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(404, msg)
        raise HTTPException(422, msg)


class PatchStatusRequest(BaseModel):
    status: str
    linked_trade_id: Optional[str] = None


@plan_router.patch(
    "/{plan_id}/status",
    dependencies=[Depends(require_unlocked_db)],
)
async def patch_plan_status(
    plan_id: int,
    body: PatchStatusRequest,
    service=Depends(get_report_service),
):
    """Transition plan status (DRAFT→ACTIVE→EXECUTED)."""
    try:
        if body.status == "executed" and body.linked_trade_id:
            plan = service.link_plan_to_trade(plan_id, body.linked_trade_id)
        else:
            plan = service.update_plan(plan_id, {"status": body.status})
        return _to_response(plan)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(404, msg)
        raise HTTPException(422, msg)


@plan_router.delete(
    "/{plan_id}", status_code=204,
    dependencies=[Depends(require_unlocked_db)],
)
async def delete_plan(
    plan_id: int,
    service=Depends(get_report_service),
):
    """Delete a trade plan."""
    try:
        service.delete_plan(plan_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Helpers ─────────────────────────────────────────────────────────────


def _to_response(plan: object) -> dict:
    """Convert TradePlan entity to response dict."""
    return {
        "id": plan.id,                                   # type: ignore[attr-defined]
        "ticker": plan.ticker,                           # type: ignore[attr-defined]
        "direction": str(plan.direction),                # type: ignore[attr-defined]
        "conviction": str(plan.conviction),              # type: ignore[attr-defined]
        "strategy_name": plan.strategy_name,             # type: ignore[attr-defined]
        "strategy_description": plan.strategy_description,  # type: ignore[attr-defined]
        "entry_price": plan.entry_price,                 # type: ignore[attr-defined]
        "stop_loss": plan.stop_loss,                     # type: ignore[attr-defined]
        "target_price": plan.target_price,               # type: ignore[attr-defined]
        "entry_conditions": plan.entry_conditions,       # type: ignore[attr-defined]
        "exit_conditions": plan.exit_conditions,         # type: ignore[attr-defined]
        "timeframe": plan.timeframe,                     # type: ignore[attr-defined]
        "risk_reward_ratio": plan.risk_reward_ratio,     # type: ignore[attr-defined]
        "status": str(plan.status),                      # type: ignore[attr-defined]
        "linked_trade_id": plan.linked_trade_id,         # type: ignore[attr-defined]
        "account_id": plan.account_id,                   # type: ignore[attr-defined]
        "created_at": plan.created_at.isoformat() if plan.created_at else "",  # type: ignore[attr-defined]
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",  # type: ignore[attr-defined]
    }
