# packages/api/src/zorivest_api/routes/reports.py
"""Trade Report REST endpoints.

Source: 04a-api-trades.md L126-151
Nested under /api/v1/trades/{exec_id}/report (singular — one report per trade).
Grade conversion: API accepts letter grades (A-F), domain stores ints (1-5).
"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from zorivest_api.dependencies import get_report_service, require_unlocked_db
from zorivest_core.domain.enums import QUALITY_GRADE_MAP, QUALITY_INT_MAP

report_router = APIRouter(prefix="/api/v1/trades", tags=["reports"])


# ── Request/Response schemas ────────────────────────────────────────────


class CreateReportRequest(BaseModel):
    setup_quality: Literal["A", "B", "C", "D", "F"]
    execution_quality: Literal["A", "B", "C", "D", "F"]
    followed_plan: bool
    emotional_state: str = "neutral"
    lessons_learned: str = ""
    tags: list[str] = []


class UpdateReportRequest(BaseModel):
    setup_quality: Optional[Literal["A", "B", "C", "D", "F"]] = None
    execution_quality: Optional[Literal["A", "B", "C", "D", "F"]] = None
    followed_plan: Optional[bool] = None
    emotional_state: Optional[str] = None
    lessons_learned: Optional[str] = None
    tags: Optional[list[str]] = None


class ReportResponse(BaseModel):
    id: int
    trade_id: str
    setup_quality: str  # Letter grade A-F
    execution_quality: str  # Letter grade A-F
    followed_plan: bool
    emotional_state: str
    lessons_learned: str = ""
    tags: list[str] = []
    created_at: str  # ISO format

    model_config = {"from_attributes": True}


# ── Grade boundary conversion helpers ──────────────────────────────────


def _grade_to_int(grade: str) -> int:
    """Convert letter grade to integer for domain storage."""
    return QUALITY_INT_MAP.get(grade, 3)  # Default C=3


def _int_to_grade(value: int) -> str:
    """Convert integer to letter grade for API response."""
    return QUALITY_GRADE_MAP.get(value, "C")  # Default C


# ── Report routes ───────────────────────────────────────────────────────


@report_router.post(
    "/{exec_id}/report",
    status_code=201,
    dependencies=[Depends(require_unlocked_db)],
)
async def create_report(
    exec_id: str,
    body: CreateReportRequest,
    service=Depends(get_report_service),
):
    """Create a post-trade report."""
    try:
        data = body.model_dump()
        # Convert letter grades → ints for domain
        data["setup_quality"] = _grade_to_int(data["setup_quality"])
        data["execution_quality"] = _grade_to_int(data["execution_quality"])
        report = service.create(exec_id, data)
        return _to_response(report)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg:
            raise HTTPException(404, msg)
        if "already exists" in msg:
            raise HTTPException(409, msg)
        raise HTTPException(422, msg)


@report_router.get(
    "/{exec_id}/report",
    dependencies=[Depends(require_unlocked_db)],
)
async def get_report(
    exec_id: str,
    service=Depends(get_report_service),
):
    """Get the report for a trade."""
    report = service.get_for_trade(exec_id)
    if report is None:
        raise HTTPException(404, f"Report not found for trade: {exec_id}")
    return _to_response(report)


@report_router.put(
    "/{exec_id}/report",
    dependencies=[Depends(require_unlocked_db)],
)
async def update_report(
    exec_id: str,
    body: UpdateReportRequest,
    service=Depends(get_report_service),
):
    """Update the report for a trade."""
    try:
        updates = body.model_dump(exclude_unset=True)
        # Convert letter grades → ints if present
        if "setup_quality" in updates:
            updates["setup_quality"] = _grade_to_int(updates["setup_quality"])
        if "execution_quality" in updates:
            updates["execution_quality"] = _grade_to_int(updates["execution_quality"])
        report = service.update(exec_id, updates)
        return _to_response(report)
    except ValueError as e:
        raise HTTPException(404, str(e))


@report_router.delete(
    "/{exec_id}/report",
    status_code=204,
    dependencies=[Depends(require_unlocked_db)],
)
async def delete_report(
    exec_id: str,
    service=Depends(get_report_service),
):
    """Delete the report for a trade."""
    try:
        service.delete(exec_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Helpers ─────────────────────────────────────────────────────────────


def _to_response(report: object) -> dict:
    """Convert TradeReport entity to response dict with letter grades."""
    return {
        "id": report.id,  # type: ignore[attr-defined]
        "trade_id": report.trade_id,  # type: ignore[attr-defined]
        "setup_quality": _int_to_grade(report.setup_quality),  # type: ignore[attr-defined]
        "execution_quality": _int_to_grade(report.execution_quality),  # type: ignore[attr-defined]
        "followed_plan": report.followed_plan,  # type: ignore[attr-defined]
        "emotional_state": report.emotional_state,  # type: ignore[attr-defined]
        "lessons_learned": report.lessons_learned,  # type: ignore[attr-defined]
        "tags": report.tags,  # type: ignore[attr-defined]
        "created_at": report.created_at.isoformat() if report.created_at else "",  # type: ignore[attr-defined]
    }
