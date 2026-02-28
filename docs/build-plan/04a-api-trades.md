# Phase 4a: REST API — Trades

> Part of [Phase 4: REST API](04-rest-api.md) | Tag: `trades`
>
> Trade lifecycle endpoints: CRUD, reports, plans, images (nested + global), journal linking, round-trips.

---

## Route Definitions

```python
# packages/api/src/zorivest_api/routes/trades.py

from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Literal, Optional
from zorivest_core.services.trade_service import TradeService
from zorivest_core.services.image_service import ImageService
from zorivest_core.application.commands import CreateTradeCommand, UpdateTradeCommand, AttachImageCommand

trade_router = APIRouter(prefix="/api/v1/trades", tags=["trades"])


# ── Request / Response schemas ──────────────────────────────

class CreateTradeRequest(BaseModel):
    exec_id: str
    instrument: str
    action: str            # "BOT" | "SLD"
    quantity: float
    price: float
    account_id: str
    commission: float = 0.0
    realized_pnl: float = 0.0
    notes: Optional[str] = None

class UpdateTradeRequest(BaseModel):
    notes: Optional[str] = None
    commission: Optional[float] = None
    realized_pnl: Optional[float] = None

class TradeImageResponse(BaseModel):
    id: int
    caption: str
    mime_type: str
    file_size: int
    thumbnail_url: str
    created_at: datetime


# ── Trade CRUD routes ───────────────────────────────────────

@trade_router.get("/")
async def list_trades(limit: int = 50, offset: int = 0,
                      account_id: str | None = None,
                      sort: str = "-created_at",
                      service: TradeService = Depends(get_trade_service)):
    """List trades with optional account filter and sort.

    Query params:
      - account_id: filter to a specific account (optional)
      - sort: sort field, prefix '-' for descending (default: '-created_at')
              allowed fields: created_at, instrument, price
    """
    return service.list_trades(limit=limit, offset=offset,
                               account_id=account_id, sort=sort)

@trade_router.post("/", status_code=201)
async def create_trade(body: CreateTradeRequest,
                       service: TradeService = Depends(get_trade_service)):
    result = service.create_trade(CreateTradeCommand(**body.model_dump()))
    return {"status": "created", "exec_id": result.exec_id}

@trade_router.get("/{exec_id}")
async def get_trade(exec_id: str,
                    service: TradeService = Depends(get_trade_service)):
    trade = service.get_trade(exec_id)
    if not trade:
        raise HTTPException(404, "Trade not found")
    return trade

@trade_router.put("/{exec_id}")
async def update_trade(exec_id: str, body: UpdateTradeRequest,
                       service: TradeService = Depends(get_trade_service)):
    service.update_trade(exec_id, UpdateTradeCommand(**body.model_dump(exclude_none=True)))
    return {"status": "updated", "exec_id": exec_id}

@trade_router.delete("/{exec_id}", status_code=204)
async def delete_trade(exec_id: str,
                       service: TradeService = Depends(get_trade_service)):
    service.delete_trade(exec_id)


# ── Trade image routes ──────────────────────────────────────

@trade_router.get("/{exec_id}/images", response_model=list[TradeImageResponse])
async def get_trade_images(exec_id: str,
                           service: ImageService = Depends(get_image_service)):
    return service.get_images_for_owner("trade", exec_id)

@trade_router.post("/{exec_id}/images")
async def upload_image(exec_id: str, file: UploadFile = File(...),
                       caption: str = Form(""),
                       service: ImageService = Depends(get_image_service)):
    data = await file.read()
    result = service.attach_image(AttachImageCommand(
        owner_type="trade", owner_id=exec_id, image_data=data,
        mime_type=file.content_type, caption=caption,  # advisory — service normalizes to image/webp after standardization
    ))
    return {"image_id": result.image_id}


# ── Trade report routes ──────────────────────────────────────

class CreateReportRequest(BaseModel):
    setup_quality: Literal["A", "B", "C", "D", "F"]
    execution_quality: Literal["A", "B", "C", "D", "F"]
    followed_plan: bool
    emotional_state: str
    lessons_learned: Optional[str] = None
    tags: list[str] = []

@trade_router.post("/{exec_id}/report", status_code=201)
async def create_report(exec_id: str, body: CreateReportRequest,
                        service = Depends(get_report_service)):
    """Create post-trade TradeReport for a trade."""
    return service.create(exec_id, body.model_dump())

@trade_router.get("/{exec_id}/report")
async def get_report_for_trade(exec_id: str,
                                service = Depends(get_report_service)):
    """Fetch TradeReport linked to a specific trade."""
    report = service.get_for_trade(exec_id)
    if not report:
        raise HTTPException(404, "Report not found for this trade")
    return report

@trade_router.put("/{exec_id}/report")
async def update_report(exec_id: str, body: CreateReportRequest,
                        service = Depends(get_report_service)):
    """Update an existing TradeReport."""
    return service.update(exec_id, body.model_dump())

@trade_router.delete("/{exec_id}/report", status_code=204)
async def delete_report(exec_id: str,
                        service = Depends(get_report_service)):
    """Delete TradeReport linked to a trade."""
    service.delete(exec_id)
```

## Trade Plan Routes

```python
# packages/api/src/zorivest_api/routes/trade_plans.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Literal, Optional

plan_router = APIRouter(prefix="/api/v1/trade-plans", tags=["trade-plans"])

class CreateTradePlanRequest(BaseModel):
    ticker: str
    direction: Literal["long", "short"]
    conviction: Literal["high", "medium", "low"]
    strategy_name: str
    entry: float = Field(gt=0)
    stop: float = Field(gt=0)
    target: float = Field(gt=0)
    conditions: str
    timeframe: str
    account_id: Optional[str] = None

@plan_router.post("/", status_code=201)
async def create_trade_plan(body: CreateTradePlanRequest,
                             service = Depends(get_report_service)):
    """Create forward-looking TradePlan with computed risk_reward_ratio."""
    return service.create(body.model_dump())
```

## Image Routes (Global Access)

```python
# packages/api/src/zorivest_api/routes/images.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from zorivest_core.services.image_service import ImageService

image_router = APIRouter(prefix="/api/v1/images", tags=["images"])

@image_router.get("/{image_id}")
async def get_image_metadata(image_id: int,
                             service: ImageService = Depends(get_image_service)):
    meta = service.get_image(image_id)
    if not meta:
        raise HTTPException(404, "Image not found")
    return meta

@image_router.get("/{image_id}/thumbnail")
async def get_image_thumbnail(image_id: int, max_size: int = 200,
                              service: ImageService = Depends(get_image_service)):
    thumb_bytes = service.get_thumbnail(image_id, max_size)
    return Response(content=thumb_bytes, media_type="image/webp")

@image_router.get("/{image_id}/full")
async def get_image_full(image_id: int,
                         service: ImageService = Depends(get_image_service)):
    img = service.get_image(image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    return Response(content=img.data, media_type=img.mime_type)
```

## Trade Journal Linking Route (§16)

```python
# packages/api/src/zorivest_api/routes/trades.py  (additions)

@trade_router.post("/{exec_id}/journal-link")
async def link_trade_journal(exec_id: str, body: dict,
                              service = Depends(get_report_service)):
    """Bidirectional trade ↔ journal entry link."""
    ...
```

## E2E Tests

```python
# tests/e2e/test_api_endpoints.py

def test_list_trades(client):
    response = client.get("/api/v1/trades/")
    assert response.status_code == 200

def test_upload_and_retrieve_image(client):
    # Create a trade first
    # Upload image
    response = client.post(
        "/api/v1/trades/T001/images",
        files={"file": ("screenshot.webp", b"RIFF\x00\x00WEBP...", "image/webp")},
        data={"caption": "Entry screenshot"},
    )
    assert response.status_code == 200
    image_id = response.json()["image_id"]

    # Get thumbnail
    response = client.get(f"/api/v1/images/{image_id}/thumbnail?max_size=150")  # global image route
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
```

## Round-Trip Routes

> Entry→exit pair analysis consumed by `get_round_trips` MCP tool ([05c](05c-mcp-trade-analytics.md):222).

```python
# packages/api/src/zorivest_api/routes/round_trips.py

from fastapi import APIRouter, Depends
from typing import Literal, Optional

round_trip_router = APIRouter(prefix="/api/v1/round-trips", tags=["trades"])


@round_trip_router.get("/", status_code=200)
async def list_round_trips(
    account_id: Optional[str] = None,
    status: Literal["open", "closed", "all"] = "all",
    ticker: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service = Depends(get_trade_service),
):
    """List round-trips (entry→exit pairs) with P&L.
    A round-trip is one or more opening executions matched
    against one or more closing executions for the same ticker/account.
    Returns: legs, net_pnl, holding_period, is_open."""
    return service.list_round_trips(
        account_id=account_id, status=status, ticker=ticker,
        limit=limit, offset=offset,
    )
```

### Round-Trip Tests

```python
def test_list_round_trips(client):
    """GET /round-trips returns list with P&L fields."""
    r = client.get("/api/v1/round-trips")
    assert r.status_code == 200
    assert isinstance(r.json(), list) or "items" in r.json()

def test_round_trips_filter_by_status(client):
    """GET /round-trips?status=closed returns only closed pairs."""
    r = client.get("/api/v1/round-trips?status=closed")
    assert r.status_code == 200
```

## Consumer Notes

- **MCP tools:** `create_trade`, `list_trades`, `attach_screenshot`, `get_round_trips` ([05c](05c-mcp-trade-analytics.md)), `create_trade_plan` ([05d](05d-mcp-trade-planning.md))
- **GUI pages:** [06b-gui-trades.md](06b-gui-trades.md) — trade table, detail view, image gallery, journal linking
