"""Trade CRUD REST endpoints.

Source: 04a-api-trades.md §Trade CRUD, §Image Routes (nested)
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional

from zorivest_core.application.commands import AttachImage, CreateTrade
from zorivest_core.domain.enums import ImageOwnerType, TradeAction
from zorivest_core.domain.exceptions import BusinessRuleError, NotFoundError
from zorivest_api.dependencies import get_trade_service, get_image_service, require_unlocked_db
from zorivest_api.schemas.common import PaginatedResponse

trade_router = APIRouter(prefix="/api/v1/trades", tags=["trades"])


# ── Request/Response schemas ────────────────────────────────────────────

class CreateTradeRequest(BaseModel):
    exec_id: str
    time: datetime
    instrument: str
    action: str  # "BOT" | "SLD"
    quantity: float
    price: float
    account_id: str
    commission: float = 0.0
    realized_pnl: float = 0.0
    notes: Optional[str] = None


class UpdateTradeRequest(BaseModel):
    instrument: Optional[str] = None
    action: Optional[str] = None  # "BOT" | "SLD"
    quantity: Optional[float] = None
    price: Optional[float] = None
    account_id: Optional[str] = None
    time: Optional[datetime] = None
    commission: Optional[float] = None
    realized_pnl: Optional[float] = None
    notes: Optional[str] = None


class TradeResponse(BaseModel):
    exec_id: str
    time: datetime
    instrument: str
    action: str
    quantity: float
    price: float
    account_id: str
    commission: float
    realized_pnl: float
    notes: str = ""

    model_config = {"from_attributes": True}


# ── Trade CRUD routes ───────────────────────────────────────────────────

@trade_router.post("", status_code=201, dependencies=[Depends(require_unlocked_db)])
async def create_trade(
    body: CreateTradeRequest,
    service=Depends(get_trade_service),
):
    """Create a new trade."""
    try:
        cmd = CreateTrade(
            exec_id=body.exec_id,
            time=body.time,
            instrument=body.instrument,
            action=TradeAction(body.action),
            quantity=body.quantity,
            price=body.price,
            account_id=body.account_id,
            commission=body.commission,
            realized_pnl=body.realized_pnl,
            notes=body.notes or "",
        )
        trade = service.create_trade(cmd)
        return TradeResponse.model_validate(trade)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except BusinessRuleError as e:
        raise HTTPException(409, str(e))


@trade_router.get("", dependencies=[Depends(require_unlocked_db)])
async def list_trades(
    limit: int = 50,
    offset: int = 0,
    account_id: str | None = None,
    search: str | None = None,
    sort: str = "-time",
    service=Depends(get_trade_service),
):
    """List trades with optional account filter, search, and sort."""
    trades = service.list_trades(
        limit=limit, offset=offset, account_id=account_id, sort=sort,
        search=search,
    )
    items = [TradeResponse.model_validate(t) for t in trades]
    return PaginatedResponse(
        items=items, total=len(items), limit=limit, offset=offset,
    )


@trade_router.get("/{exec_id}", dependencies=[Depends(require_unlocked_db)])
async def get_trade(exec_id: str, service=Depends(get_trade_service)):
    """Get a single trade by exec_id."""
    try:
        trade = service.get_trade(exec_id)
        return TradeResponse.model_validate(trade)
    except NotFoundError:
        raise HTTPException(404, f"Trade not found: {exec_id}")


@trade_router.put("/{exec_id}", dependencies=[Depends(require_unlocked_db)])
async def update_trade(
    exec_id: str,
    body: UpdateTradeRequest,
    service=Depends(get_trade_service),
):
    """Update trade fields."""
    try:
        kwargs = body.model_dump(exclude_unset=True)
        trade = service.update_trade(exec_id, **kwargs)
        return TradeResponse.model_validate(trade)
    except NotFoundError:
        raise HTTPException(404, f"Trade not found: {exec_id}")
    except ValueError as e:
        raise HTTPException(422, str(e))


@trade_router.delete("/{exec_id}", status_code=204, dependencies=[Depends(require_unlocked_db)])
async def delete_trade(exec_id: str, service=Depends(get_trade_service)):
    """Delete a trade."""
    service.delete_trade(exec_id)


# ── Trade image routes (nested) ─────────────────────────────────────────

@trade_router.get("/{exec_id}/images", dependencies=[Depends(require_unlocked_db)])
async def list_trade_images(exec_id: str, service=Depends(get_image_service)):
    """List all images attached to a trade."""
    images = service.get_images_for_owner("trade", exec_id)
    return [
        {
            "id": img.id,
            "caption": img.caption,
            "mime_type": img.mime_type,
            "file_size": img.file_size,
            "created_at": img.created_at.isoformat() if img.created_at else None,
        }
        for img in images
    ]


@trade_router.post("/{exec_id}/images", status_code=201, dependencies=[Depends(require_unlocked_db)])
async def upload_trade_image(
    exec_id: str,
    file: UploadFile = File(...),
    caption: str = Form(""),
    service=Depends(get_image_service),
):
    """Upload an image and attach it to a trade.

    Source: 04a-api-trades.md §Image Upload
    The service layer normalizes to image/webp after standardization.
    """
    data = await file.read()
    try:
        image_id = service.attach_image(AttachImage(
            owner_type=ImageOwnerType.TRADE,
            owner_id=exec_id,
            data=data,
            mime_type=file.content_type or "image/webp",
            width=0,   # service layer extracts dimensions after WebP conversion
            height=0,
            caption=caption,
        ))
    except NotFoundError:
        raise HTTPException(404, f"Trade not found: {exec_id}")
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"image_id": image_id}
