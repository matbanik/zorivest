# packages/api/src/zorivest_api/routes/calculator.py
"""Position size calculator route — pure calculation, no auth required.

Source: 04e-api-analytics.md §Calculator Routes
MEU-28: POST /position-size. Uses real PositionSizeCalculator from MEU-1.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from zorivest_core.domain.calculator import PositionSizeResult, calculate_position_size

calculator_router = APIRouter(prefix="/api/v1/calculator", tags=["calculator"])


class PositionSizeRequest(BaseModel):
    """Calculator request schema."""

    balance: float
    risk_pct: float
    entry_price: float
    stop_loss: float
    target_price: float


@calculator_router.post("/position-size")
async def calculate_position(body: PositionSizeRequest) -> dict:
    """Calculate position size based on risk parameters.
    Pure calculation — no auth or DB required."""
    result: PositionSizeResult = calculate_position_size(
        balance=body.balance,
        risk_pct=body.risk_pct,
        entry=body.entry_price,
        stop=body.stop_loss,
        target=body.target_price,
    )
    return {
        "shares": result.share_size,
        "risk_amount": result.account_risk_1r,
        "position_size": result.position_size,
        "position_to_account_pct": result.position_to_account_pct,
        "reward_risk_ratio": result.reward_risk_ratio,
        "risk_per_share": result.risk_per_share,
        "potential_profit": result.potential_profit,
    }
