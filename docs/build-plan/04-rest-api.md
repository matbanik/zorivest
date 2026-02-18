# Phase 4: REST API (FastAPI)

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) | Prerequisites: [Phase 3](03-service-layer.md) | Outputs: [Phase 5](05-mcp-server.md), [Phase 6](06-gui.md) ([Shell](06a-gui-shell.md), [Trades](06b-gui-trades.md), [Settings](06f-gui-settings.md))
>
> **Phase 2A routes**: Backup, config export/import, and settings resolver endpoints are defined in [Phase 2A](02a-backup-restore.md) and implemented here.

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
from zorivest_core.domain.settings_validator import SettingsValidationError

settings_router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class SettingResponse(BaseModel):
    key: str
    value: str
    value_type: str


class ResolvedSettingResponse(BaseModel):
    """Used by GET /settings/resolved (Phase 2A). Returns typed values."""
    key: str
    value: Any            # typed: bool, int, float, str — NOT string-only
    source: str           # "user" | "default" | "hardcoded"
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
    """Bulk upsert settings with validation.

    Returns 422 if any setting fails validation, with per-key error details.
    All-or-nothing: no settings are written if any key fails.
    Body: {"key1": "value1", "key2": "value2"}
    """
    try:
        service.bulk_upsert(body)
        return {"status": "updated", "count": len(body)}
    except SettingsValidationError as e:
        raise HTTPException(422, detail={"errors": e.per_key_errors})
```

#### Validation Error Tests

```python
# tests/e2e/test_settings_api.py

def test_invalid_setting_rejected(client):
    """PUT with out-of-range value returns 422 with per-key errors."""
    response = client.put("/api/v1/settings", json={"logging.rotation_mb": "-5"})
    assert response.status_code == 422
    assert "logging.rotation_mb" in response.json()["detail"]["errors"]

def test_path_traversal_rejected(client):
    """PUT with path traversal value returns 422 with security error."""
    response = client.put("/api/v1/settings", json={"display.percent_mode": "../../../etc/passwd"})
    assert response.status_code == 422
    assert "display.percent_mode" in response.json()["detail"]["errors"]

def test_unknown_key_rejected(client):
    """PUT with unknown key returns 422 with per-key error."""
    response = client.put("/api/v1/settings", json={"not.a.real.key": "value"})
    assert response.status_code == 422
    assert "not.a.real.key" in response.json()["detail"]["errors"]

def test_valid_setting_accepted(client):
    """PUT with valid values returns 200."""
    response = client.put("/api/v1/settings", json={"logging.rotation_mb": "20"})
    assert response.status_code == 200

def test_mixed_payload_all_or_nothing(client):
    """PUT with one valid and one invalid key returns 422 and persists nothing."""
    response = client.put("/api/v1/settings", json={
        "logging.rotation_mb": "20",       # valid
        "logging.backup_count": "-1",       # invalid (below min)
    })
    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert "logging.backup_count" in errors
    assert "logging.rotation_mb" not in errors
    # Verify valid key was NOT persisted
    get_resp = client.get("/api/v1/settings/logging.rotation_mb")
    assert get_resp.json()["value"] != "20"

def test_422_per_key_error_shape(client):
    """All 422 responses include detail.errors as dict[str, list[str]]."""
    response = client.put("/api/v1/settings", json={"display.percent_mode": "../hack"})
    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert isinstance(errors, dict)
    for key, msgs in errors.items():
        assert isinstance(key, str)
        assert isinstance(msgs, list)
        assert all(isinstance(m, str) for m in msgs)

def test_invalid_bool_rejected(client):
    """PUT with non-bool string for bool setting returns 422."""
    response = client.put("/api/v1/settings", json={"display.hide_dollars": "not-a-bool"})
    assert response.status_code == 422
    assert "display.hide_dollars" in response.json()["detail"]["errors"]
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

## Step 4.6: MCP Guard Routes

> Circuit breaker + panic button for MCP tool access.
> Model: [`McpGuardModel`](02-infrastructure.md) | GUI: [§6f.8](06f-gui-settings.md) | MCP middleware: [§5.6](05-mcp-server.md)

### Pydantic Schemas

```python
# zorivest_api/schemas/mcp_guard.py

class McpGuardStatus(BaseModel):
    is_enabled: bool
    is_locked: bool
    locked_at: datetime | None
    lock_reason: str | None
    calls_per_minute_limit: int
    calls_per_hour_limit: int
    recent_calls_1min: int          # live counter (in-memory)
    recent_calls_1hr: int           # live counter (in-memory)

class McpGuardConfigUpdate(BaseModel):
    is_enabled: bool | None = None
    calls_per_minute_limit: int | None = Field(None, ge=1, le=10000)
    calls_per_hour_limit: int | None = Field(None, ge=1, le=100000)

class McpGuardLockRequest(BaseModel):
    reason: str = Field("manual", description="Free-text reason. Convention: 'manual', 'rate_limit_exceeded', 'agent_self_lock'.")
```

### Routes

> All `/mcp-guard/*` routes require an active database session via `Depends(get_guard_service)`, consistent with trade/settings routes. Calls without an unlocked DB session return **403**.

```python
# zorivest_api/routes/mcp_guard.py

guard_router = APIRouter(prefix="/api/v1/mcp-guard", tags=["mcp-guard"])

@guard_router.get("/status", status_code=200)
async def guard_status(service: McpGuardService = Depends(get_guard_service)) -> McpGuardStatus:
    """Return current guard state, thresholds, and live call counters."""
    ...

@guard_router.put("/config", status_code=200)
async def update_guard_config(body: McpGuardConfigUpdate,
                              service: McpGuardService = Depends(get_guard_service)) -> McpGuardStatus:
    """Update guard thresholds and enabled toggle. Returns updated state."""
    ...

@guard_router.post("/lock", status_code=200)
async def lock_mcp(body: McpGuardLockRequest,
                   service: McpGuardService = Depends(get_guard_service)) -> McpGuardStatus:
    """Panic button — immediately lock all MCP tools."""
    ...

@guard_router.post("/unlock", status_code=200)
async def unlock_mcp(service: McpGuardService = Depends(get_guard_service)) -> McpGuardStatus:
    """Re-enable MCP tools. Requires active database session (same as all other routes)."""
    ...

@guard_router.post("/check", status_code=200)
async def guard_check(service: McpGuardService = Depends(get_guard_service)) -> dict:
    """Lightweight check endpoint called by MCP middleware on each tool call.
    Increments in-memory counter. Returns {"allowed": true/false, "reason": ...}.
    If threshold exceeded, auto-locks with reason 'rate_limit_exceeded' and returns allowed=false."""
    ...
```

### E2E Tests

```python
# tests/e2e/test_mcp_guard.py

def test_guard_status_returns_defaults(client):
    """GET /mcp-guard/status returns is_enabled=False, is_locked=False."""
    r = client.get("/api/v1/mcp-guard/status")
    assert r.status_code == 200
    assert r.json()["is_enabled"] is False
    assert r.json()["is_locked"] is False

def test_guard_lock_unlock_cycle(client):
    """POST lock → locked=True → POST unlock → locked=False."""
    client.post("/api/v1/mcp-guard/lock", json={"reason": "test"})
    assert client.get("/api/v1/mcp-guard/status").json()["is_locked"] is True
    client.post("/api/v1/mcp-guard/unlock")
    assert client.get("/api/v1/mcp-guard/status").json()["is_locked"] is False

def test_guard_config_update(client):
    """PUT new thresholds → GET reflects changes."""
    client.put("/api/v1/mcp-guard/config", json={"calls_per_minute_limit": 30})
    status = client.get("/api/v1/mcp-guard/status").json()
    assert status["calls_per_minute_limit"] == 30

def test_guard_lock_reason_persisted(client):
    """Lock reason is stored and returned in status."""
    client.post("/api/v1/mcp-guard/lock", json={"reason": "agent_self_lock"})
    assert client.get("/api/v1/mcp-guard/status").json()["lock_reason"] == "agent_self_lock"

def test_guard_routes_require_session(unauthenticated_client):
    """All guard routes return 403 without an unlocked DB session."""
    assert unauthenticated_client.get("/api/v1/mcp-guard/status").status_code == 403
    assert unauthenticated_client.post("/api/v1/mcp-guard/lock", json={}).status_code == 403
    assert unauthenticated_client.post("/api/v1/mcp-guard/unlock").status_code == 403

def test_guard_check_auto_locks_on_threshold(client):
    """Enable guard with limit=2. Third /check call triggers auto-lock."""
    client.put("/api/v1/mcp-guard/config", json={"is_enabled": True, "calls_per_minute_limit": 2})
    assert client.post("/api/v1/mcp-guard/check").json()["allowed"] is True
    assert client.post("/api/v1/mcp-guard/check").json()["allowed"] is True
    result = client.post("/api/v1/mcp-guard/check").json()
    assert result["allowed"] is False
    assert result["reason"] == "rate_limit_exceeded"
    assert client.get("/api/v1/mcp-guard/status").json()["is_locked"] is True
    assert client.get("/api/v1/mcp-guard/status").json()["lock_reason"] == "rate_limit_exceeded"

def test_guard_check_allowed_when_disabled(client):
    """Guard disabled: /check always returns allowed=true, never auto-locks."""
    client.put("/api/v1/mcp-guard/config", json={"is_enabled": False})
    for _ in range(10):
        assert client.post("/api/v1/mcp-guard/check").json()["allowed"] is True
    assert client.get("/api/v1/mcp-guard/status").json()["is_locked"] is False

def test_guard_check_counter_resets_after_window(client):
    """Call /check near limit, wait for window expiry, verify counter resets."""
    client.put("/api/v1/mcp-guard/config", json={"is_enabled": True, "calls_per_minute_limit": 2})
    client.post("/api/v1/mcp-guard/check")  # 1 of 2
    # ... (time.sleep or mock clock to advance past 60s window) ...
    result = client.post("/api/v1/mcp-guard/check").json()
    assert result["allowed"] is True  # counter reset
```

## Step 4.7: Version Route

> Exposes runtime version and resolution context for diagnostics (see [Phase 7 §7.1](07-distribution.md)). No authentication required (localhost-only).

```python
# packages/api/src/zorivest_api/routes/version.py

from fastapi import APIRouter
from pydantic import BaseModel
from zorivest_core.version import get_version, get_version_context

version_router = APIRouter(prefix="/api/v1/version", tags=["version"])


class VersionResponse(BaseModel):
    version: str        # SemVer string, e.g. "1.0.0"
    context: str        # "frozen" | "installed" | "dev"


@version_router.get("/", status_code=200)
async def get_app_version() -> VersionResponse:
    """Return application version and how it was resolved.

    Resolution order (see §7.1):
    1. Frozen executable (_VERSION constant)
    2. Installed package (importlib.metadata)
    3. Development (.version file in repo root)
    """
    return VersionResponse(version=get_version(), context=get_version_context())
```

### Step 4.7 Tests

```python
# tests/e2e/test_version_api.py

def test_version_endpoint_returns_200(client):
    """GET /api/v1/version/ returns version and context."""
    response = client.get("/api/v1/version/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["context"] in ("frozen", "installed", "dev")

def test_version_format_is_semver(client):
    """Version string matches SemVer pattern."""
    import re
    response = client.get("/api/v1/version/")
    version = response.json()["version"]
    assert re.match(r"^\d+\.\d+\.\d+", version)
```

## Exit Criteria

- All e2e tests pass with FastAPI `TestClient`
- Health endpoint returns 200
- Settings CRUD endpoints return correct values
- Log ingestion endpoint accepts and records frontend metrics
- Trade list supports `account_id` filter and `sort` parameter
- MCP guard lock/unlock cycle and threshold updates work end-to-end
- Version endpoint returns valid SemVer and resolution context

## Outputs

- FastAPI routes for trades, images, accounts, calculator
- Version route for diagnostics (`GET /api/v1/version/`)
- Settings routes for UI state and preference persistence
- Settings resolver routes (`GET /resolved`, `DELETE /{key}` for reset) — see [Phase 2A](02a-backup-restore.md)
- Backup routes (`POST/GET /backups`, `POST /backups/restore`, `POST /backups/verify`) — see [Phase 2A](02a-backup-restore.md)
- Config export/import routes (`GET /config/export`, `POST /config/import`) — see [Phase 2A](02a-backup-restore.md)
- MCP guard routes (`GET/PUT /mcp-guard/config`, `GET /mcp-guard/status`, `POST /mcp-guard/lock`, `POST /mcp-guard/unlock`, `POST /mcp-guard/check`)
- Logging route for frontend metric ingestion
- Full CRUD endpoints with pagination, filtering, and sorting
- E2E tests using `TestClient`
