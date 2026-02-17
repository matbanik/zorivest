# Phase 4: REST API (FastAPI)

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 3](03-service-layer.md) | Outputs: [Phase 5](05-mcp-server.md), [Phase 6](06-gui.md) ([Shell](06a-gui-shell.md), [Trades](06b-gui-trades.md), [Settings](06f-gui-settings.md))

---

## Goal

Thin REST layer that delegates to the same service layer. Test with FastAPI's `TestClient`.

## Step 4.1: Route Definitions

```python
# packages/api/src/zorivest_api/routes/trades.py

from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
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
        mime_type=file.content_type, caption=caption,
    ))
    return {"image_id": result.image_id}
```

## Step 4.1b: Image Routes (Global Access)

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
    return Response(content=thumb_bytes, media_type="image/png")

@image_router.get("/{image_id}/full")
async def get_image_full(image_id: int,
                         service: ImageService = Depends(get_image_service)):
    img = service.get_image(image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    return Response(content=img.data, media_type=img.mime_type)
```

## Step 4.2: E2E Tests

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
        files={"file": ("screenshot.png", b"\x89PNG...", "image/png")},
        data={"caption": "Entry screenshot"},
    )
    assert response.status_code == 200
    image_id = response.json()["image_id"]

    # Get thumbnail
    response = client.get(f"/api/v1/images/{image_id}/thumbnail?max_size=150")  # global image route
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
```

## Step 4.3: Settings Routes

> Settings routes expose the `SettingModel` key-value store (see [Phase 2](02-infrastructure.md)) via REST. Consumed by the GUI for UI state persistence, notification preferences, and display mode toggles.

```python
# packages/api/src/zorivest_api/routes/settings.py

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from zorivest_core.services.settings_service import SettingsService

settings_router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class SettingResponse(BaseModel):
    key: str
    value: str
    value_type: str


@settings_router.get("/")
async def get_all_settings(service: SettingsService = Depends(get_settings_service)):
    """Bulk read all settings as key-value dict."""
    return service.get_all()


@settings_router.get("/{key}")
async def get_setting(key: str, service: SettingsService = Depends(get_settings_service)):
    """Read a single setting by key."""
    result = service.get(key)
    if result is None:
        raise HTTPException(404, f"Setting '{key}' not found")
    return result


@settings_router.put("/")
async def update_settings(body: dict[str, Any],
                          service: SettingsService = Depends(get_settings_service)):
    """Bulk upsert settings. Body: {"key1": "value1", "key2": "value2"}"""
    service.bulk_upsert(body)
    return {"status": "updated", "count": len(body)}
```

### Step 4.3 Tests

```python
# tests/e2e/test_settings_api.py

def test_settings_roundtrip(client):
    """PUT bulk → GET single → GET all."""
    response = client.put("/api/v1/settings", json={"ui.theme": "dark", "notification.info.enabled": "false"})
    assert response.status_code == 200
    assert response.json()["count"] == 2

    response = client.get("/api/v1/settings/ui.theme")
    assert response.status_code == 200
    assert response.json()["value"] == "dark"

    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    assert "ui.theme" in response.json()

def test_setting_not_found(client):
    response = client.get("/api/v1/settings/nonexistent.key")
    assert response.status_code == 404
```

## Step 4.4: Logging Route

> Append-only log ingestion from the Electron renderer. Used by startup performance metrics (see [Phase 6](06-gui.md)) and future frontend error reporting. No authentication required (localhost-only).
>
> The `zorivest.frontend` logger used below routes through the [Phase 1A](01a-logging.md) QueueHandler/Listener system, writing to the `frontend.jsonl` feature log file.

```python
# packages/api/src/zorivest_api/routes/logs.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Literal, Optional
import logging

log_router = APIRouter(prefix="/api/v1/logs", tags=["logs"])
logger = logging.getLogger("zorivest.frontend")

_LEVEL_MAP = {
    "debug": logger.debug,
    "info": logger.info,
    "warning": logger.warning,
    "error": logger.error,
    "critical": logger.critical,
}


class LogEntry(BaseModel):
    level: Literal["debug", "info", "warning", "error", "critical"] = "info"
    component: str = "unknown"  # e.g. "startup", "renderer"
    message: str
    data: Optional[dict[str, Any]] = None


@log_router.post("/", status_code=204)
async def ingest_log(entry: LogEntry):
    """Append-only log ingestion from Electron renderer."""
    log_fn = _LEVEL_MAP[entry.level]  # Safe: Literal constraint guarantees valid key
    log_fn(f"[{entry.component}] {entry.message}",
           extra={"data": entry.data})
```

## Step 4.5: Auth / Unlock Routes (Envelope Encryption)

Database unlock endpoint for MCP standalone mode. Uses envelope encryption: API key → Argon2id KDF → KEK → unwrap DEK → `PRAGMA key`.

```python
# packages/api/src/zorivest_api/routes/auth.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── Request / Response schemas ──────────────────────────────

class UnlockRequest(BaseModel):
    api_key: str           # e.g. "zrv_sk_..."

class UnlockResponse(BaseModel):
    session_token: str     # Bearer token for subsequent requests
    role: str              # "read-only" | "read-write" | "admin"
    scopes: list[str]      # Permitted MCP tools/routes
    expires_in: int        # Seconds until token expires (default 3600)

class KeyCreateRequest(BaseModel):
    label: str             # Human-readable label
    role: str              # "read-only" | "read-write" | "admin"
    expires_in: Optional[int] = None  # Seconds; None = no expiry

class KeyInfo(BaseModel):
    key_id: str            # Unique identifier
    label: str
    role: str
    created_at: str        # ISO 8601
    last_used_at: Optional[str] = None
    masked_key: str        # "zrv_sk_...a1b2"


# ── Unlock / Lock ───────────────────────────────────────────

@auth_router.post("/unlock", status_code=200)
async def unlock_database(request: UnlockRequest) -> UnlockResponse:
    """Unlock encrypted DB using API key (envelope encryption).
    
    Flow:
    1. Hash API key → lookup wrapped DEK in bootstrap.json
    2. Derive KEK from API key via Argon2id
    3. Unwrap DEK with KEK (Fernet)
    4. Open SQLCipher with DEK → PRAGMA key
    5. Return session token for subsequent requests
    
    Errors:
    - 401: Invalid or unknown API key
    - 403: API key revoked
    - 423: DB already locked by another session
    """
    ...

@auth_router.post("/lock", status_code=200)
async def lock_database() -> dict:
    """Lock the database and invalidate session tokens."""
    ...

@auth_router.get("/status", status_code=200)
async def auth_status() -> dict:
    """Return current auth state: locked/unlocked, active sessions, role."""
    ...


# ── API Key Management (admin only) ────────────────────────

@auth_router.post("/keys", status_code=201)
async def create_api_key(request: KeyCreateRequest) -> dict:
    """Generate new API key. Returns the key ONCE (never stored in plain).
    
    Flow:
    1. Generate random key: zrv_sk_<32 random chars>
    2. Hash key → store for lookup
    3. Derive KEK from key → wrap DEK → store in bootstrap.json
    4. Return plain key to caller (display once)
    """
    ...

@auth_router.delete("/keys/{key_id}", status_code=204)
async def revoke_api_key(key_id: str) -> None:
    """Revoke an API key. Removes its wrapped DEK entry."""
    ...

@auth_router.get("/keys", status_code=200)
async def list_api_keys() -> list[KeyInfo]:
    """List all active API keys (masked, never plain)."""
    ...
```

## Exit Criteria

- All e2e tests pass with FastAPI `TestClient`
- Health endpoint returns 200
- Settings CRUD endpoints return correct values
- Log ingestion endpoint accepts and records frontend metrics
- Trade list supports `account_id` filter and `sort` parameter

## Outputs

- FastAPI routes for trades, images, accounts, calculator
- Settings routes for UI state and preference persistence
- Logging route for frontend metric ingestion
- Full CRUD endpoints with pagination, filtering, and sorting
- E2E tests using `TestClient`
