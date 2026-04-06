# packages/api/src/zorivest_api/routes/plans.py
"""Trade Plan REST endpoints (MEU-66).

Source: 04a-api-trades.md §TradePlan endpoints (nested under /api/v1/trade-plans).
"""

from __future__ import annotations

from typing import Annotated, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from pydantic.functional_validators import BeforeValidator

from zorivest_api.dependencies import get_report_service, require_unlocked_db
from zorivest_core.domain.enums import ConvictionLevel, PlanStatus, TradeAction


def _strip_whitespace(v: object) -> object:
    """Strip leading/trailing whitespace so min_length=1 rejects blank strings."""
    return v.strip() if isinstance(v, str) else v


StrippedStr = Annotated[str, BeforeValidator(_strip_whitespace)]

plan_router = APIRouter(prefix="/api/v1/trade-plans", tags=["trade-plans"])


# Direction alias normalizer: accept MCP names (long/short) and enum values (BOT/SLD)
_DIRECTION_ALIASES: dict[str, str] = {
    "long": "BOT",
    "short": "SLD",
}


def _normalize_direction(v: object) -> object:
    if isinstance(v, str):
        return _DIRECTION_ALIASES.get(v.lower(), v)
    return v


CIDirection = Annotated[TradeAction, BeforeValidator(_normalize_direction)]


# ── Request/Response schemas ────────────────────────────────────────────


class CreatePlanRequest(BaseModel):
    model_config = {"extra": "forbid"}

    ticker: StrippedStr = Field(min_length=1)
    direction: CIDirection = TradeAction.BOT
    conviction: ConvictionLevel = ConvictionLevel.MEDIUM
    strategy_name: StrippedStr = Field(min_length=1)
    strategy_description: str = ""
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    entry_conditions: str = ""
    exit_conditions: str = ""
    timeframe: str = "intraday"
    account_id: Optional[str] = None
    shares_planned: Optional[int] = None
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
    model_config = {"extra": "forbid"}

    ticker: Optional[StrippedStr] = Field(default=None, min_length=1)
    direction: Optional[CIDirection] = None
    conviction: Optional[ConvictionLevel] = None
    strategy_name: Optional[StrippedStr] = Field(default=None, min_length=1)
    strategy_description: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    entry_conditions: Optional[str] = None
    exit_conditions: Optional[str] = None
    timeframe: Optional[str] = None
    status: Optional[PlanStatus] = None
    linked_trade_id: Optional[str] = None
    account_id: Optional[str] = None
    shares_planned: Optional[int] = None


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
    shares_planned: Optional[int] = None
    created_at: str
    updated_at: str
    executed_at: Optional[str] = None  # T5: when status → executed
    cancelled_at: Optional[str] = None  # T5: when status → cancelled

    model_config = {"from_attributes": True}


# ── Plan routes ─────────────────────────────────────────────────────────


@plan_router.post(
    "",
    status_code=201,
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
    model_config = {"extra": "forbid"}

    status: PlanStatus
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
        update_data: dict = {"status": body.status}
        # T5: auto-set status timestamps
        if body.status == "executed":
            update_data["executed_at"] = datetime.now(timezone.utc)
        elif body.status == "cancelled":
            update_data["cancelled_at"] = datetime.now(timezone.utc)

        if body.status == "executed" and body.linked_trade_id:
            # link_plan_to_trade handles linking, status=executed, and executed_at persistence
            plan = service.link_plan_to_trade(plan_id, body.linked_trade_id)
        else:
            plan = service.update_plan(plan_id, update_data)
        return _to_response(plan)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(404, msg)
        raise HTTPException(422, msg)


@plan_router.delete(
    "/{plan_id}",
    status_code=204,
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
        "id": plan.id,  # type: ignore[attr-defined]
        "ticker": plan.ticker,  # type: ignore[attr-defined]
        "direction": str(plan.direction),  # type: ignore[attr-defined]
        "conviction": str(plan.conviction),  # type: ignore[attr-defined]
        "strategy_name": plan.strategy_name,  # type: ignore[attr-defined]
        "strategy_description": plan.strategy_description,  # type: ignore[attr-defined]
        "entry_price": plan.entry_price,  # type: ignore[attr-defined]
        "stop_loss": plan.stop_loss,  # type: ignore[attr-defined]
        "target_price": plan.target_price,  # type: ignore[attr-defined]
        "entry_conditions": plan.entry_conditions,  # type: ignore[attr-defined]
        "exit_conditions": plan.exit_conditions,  # type: ignore[attr-defined]
        "timeframe": plan.timeframe,  # type: ignore[attr-defined]
        "risk_reward_ratio": plan.risk_reward_ratio,  # type: ignore[attr-defined]
        "status": str(plan.status),  # type: ignore[attr-defined]
        "linked_trade_id": plan.linked_trade_id,  # type: ignore[attr-defined]
        "account_id": plan.account_id,  # type: ignore[attr-defined]
        "shares_planned": getattr(plan, "shares_planned", None),  # type: ignore[attr-defined]
        "created_at": plan.created_at.isoformat() if plan.created_at else "",  # type: ignore[attr-defined]
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",  # type: ignore[attr-defined]
        "executed_at": plan.executed_at.isoformat()  # type: ignore[attr-defined]
        if getattr(plan, "executed_at", None)
        else None,
        "cancelled_at": plan.cancelled_at.isoformat()  # type: ignore[attr-defined]
        if getattr(plan, "cancelled_at", None)
        else None,
    }
