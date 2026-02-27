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
```

## Step 4.1c: Trade Plan Routes

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
                             service = Depends(get_trade_plan_service)):
    """Create forward-looking TradePlan with computed risk_reward_ratio."""
    return service.create(body.model_dump())
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
    return Response(content=thumb_bytes, media_type="image/webp")

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

Database unlock endpoint for the MCP server. Uses envelope encryption: API key → Argon2id KDF → KEK → unwrap DEK → `PRAGMA key`.

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

> [!NOTE]
> **MCP Discovery & Toolset tools** (`list_available_toolsets`, `describe_toolset`, `enable_toolset`, `get_confirmation_token`) operate entirely within the TypeScript MCP server layer and do not call any Python REST endpoints. They are defined in [05j-mcp-discovery.md](05j-mcp-discovery.md). The `ToolsetRegistry` is an in-memory TypeScript module with no backend persistence.

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

## Step 4.8: Build Plan Expansion Routes

> Source: [Build Plan Expansion Ideas](../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) §1–§26

### Route Summary Table

| Route Group | Prefix | Source §§ | Methods |
|-------------|--------|----------|---------|
| Brokers | `/api/v1/brokers` | §1, §2, §24, §25 | `GET /`, `POST /{id}/sync`, `GET /{id}/positions` |
| Analytics | `/api/v1/analytics` | §10–§15, §21, §22 | `GET /expectancy`, `/drawdown`, `/sqn`, `/execution-quality`, `/pfof-report`, `/strategy-breakdown`, `/cost-of-free` |
| Round-Trips | `/api/v1/round-trips` | §3 | `GET /`, `GET /{id}` |
| Identifiers | `/api/v1/identifiers` | §5 | `POST /resolve` (batch) |
| Import | `/api/v1/import` | §18, §19 | `POST /csv`, `POST /pdf` |
| Banking | `/api/v1/banking` | §26 | `POST /import`, `GET /accounts`, `POST /transactions`, `PUT /accounts/{id}/balance` |
| Mistakes | `/api/v1/mistakes` | §17 | `POST /`, `GET /?trade_id=`, `GET /summary` |
| Fees | `/api/v1/fees` | §9 | `GET /summary?account_id=&period=` |

### Broker Routes (§1, §2, §24, §25)

```python
# packages/api/src/zorivest_api/routes/brokers.py

broker_router = APIRouter(prefix="/api/v1/brokers", tags=["brokers"])

@broker_router.get("/")
async def list_brokers(service = Depends(get_broker_service)):
    """List configured broker adapters with sync status."""
    ...

@broker_router.post("/{broker_id}/sync", status_code=200)
async def sync_broker(broker_id: str, service = Depends(get_broker_service)):
    """Trigger full account sync from broker API."""
    ...

@broker_router.get("/{broker_id}/positions")
async def get_broker_positions(broker_id: str, service = Depends(get_broker_service)):
    """Fetch current positions from broker."""
    ...
```

### Analytics Routes (§10–§15, §21, §22)

```python
# packages/api/src/zorivest_api/routes/analytics.py

analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@analytics_router.get("/expectancy")
async def get_expectancy(account_id: str | None = None, period: str = "all",
                         service = Depends(get_expectancy_service)):
    """Win rate, avg win/loss, expectancy per trade, Kelly %."""
    ...

@analytics_router.get("/drawdown")
async def get_drawdown_table(account_id: str | None = None,
                             simulations: int = 10000,
                             service = Depends(get_drawdown_service)):
    """Monte Carlo drawdown probability table."""
    ...

@analytics_router.get("/execution-quality")
async def get_execution_quality(trade_id: str | None = None,
                                 service = Depends(get_eq_service)):
    """Execution quality scores (gated on NBBO data availability)."""
    ...

@analytics_router.get("/pfof-report")
async def get_pfof_report(account_id: str, period: str = "ytd",
                           service = Depends(get_pfof_service)):
    """PFOF impact analysis report — labeled as ESTIMATE."""
    ...

@analytics_router.get("/strategy-breakdown")
async def get_strategy_breakdown(account_id: str | None = None,
                                  service = Depends(get_strategy_service)):
    """P&L breakdown by strategy name."""
    ...

@analytics_router.get("/sqn")
async def get_sqn(account_id: str | None = None,
                   period: str = "all",
                   service = Depends(get_sqn_service)):
    """System Quality Number (SQN) — Van Tharp metric. Grade: Holy Grail/Excellent/Good/Average/Poor."""
    ...

@analytics_router.get("/cost-of-free")
async def get_cost_of_free(account_id: str | None = None,
                             period: str = "ytd",
                             service = Depends(get_cost_service)):
    """'Cost of Free' report — total hidden costs of PFOF routing + fees."""
    ...

@analytics_router.post("/ai-review")
async def ai_review_trade(body: dict,
                           service = Depends(get_ai_review_service)):
    """Multi-persona AI trade review. Opt-in with budget cap."""
    ...
```

### Trade Journal Linking Route (§16)

```python
# packages/api/src/zorivest_api/routes/trades.py  (additions)

@trade_router.post("/{exec_id}/journal-link")
async def link_trade_journal(exec_id: str, body: dict,
                              service = Depends(get_trade_report_service)):
    """Bidirectional trade ↔ journal entry link."""
    ...
```

### Banking Routes (§26)

```python
# packages/api/src/zorivest_api/routes/banking.py

banking_router = APIRouter(prefix="/api/v1/banking", tags=["banking"])

@banking_router.post("/import")
async def import_bank_statement(file: UploadFile = File(...),
                                 account_id: str = Form(...),
                                 format_hint: str = Form("auto"),
                                 service = Depends(get_bank_service)):
    """Import bank statement file (CSV, OFX, QIF). Returns import summary."""
    ...

@banking_router.get("/accounts")
async def list_bank_accounts(service = Depends(get_bank_service)):
    """List bank accounts with balance and last updated."""
    ...

@banking_router.post("/transactions")
async def submit_bank_transactions(body: list,
                                    service = Depends(get_bank_service)):
    """Submit bank transactions (agent bypass path)."""
    ...

@banking_router.put("/accounts/{account_id}/balance")
async def update_bank_balance(account_id: str, body: dict,
                               service = Depends(get_bank_service)):
    """Manual balance update for bank account."""
    ...
```

### Import, Mistakes, Fees Routes (§18, §19, §17, §9)

```python
# packages/api/src/zorivest_api/routes/import_.py

import_router = APIRouter(prefix="/api/v1/import", tags=["import"])

@import_router.post("/csv")
async def import_broker_csv(file: UploadFile = File(...),
                             broker_hint: str = Form("auto"),
                             account_id: str = Form(...),
                             service = Depends(get_import_service)):
    """Import broker CSV file. Auto-detects broker format."""
    ...

@import_router.post("/pdf")
async def import_broker_pdf(file: UploadFile = File(...),
                              account_id: str = Form(...),
                              service = Depends(get_pdf_service)):
    """Import broker PDF statement. Extracts tables via pdfplumber."""
    ...

# packages/api/src/zorivest_api/routes/mistakes.py

mistakes_router = APIRouter(prefix="/api/v1/mistakes", tags=["mistakes"])

@mistakes_router.post("/", status_code=201)
async def track_mistake(body: dict, service = Depends(get_mistake_service)):
    """Tag a trade with a mistake category and estimated cost."""
    ...

@mistakes_router.get("/summary")
async def mistake_summary(account_id: str | None = None,
                           period: str = "ytd",
                           service = Depends(get_mistake_service)):
    """Summary: mistakes by category, total cost, trend."""
    ...

# packages/api/src/zorivest_api/routes/fees.py

fees_router = APIRouter(prefix="/api/v1/fees", tags=["fees"])

@fees_router.get("/summary")
async def fee_summary(account_id: str | None = None,
                       period: str = "ytd",
                       service = Depends(get_ledger_service)):
    """Fee breakdown by type, broker, and % of P&L."""
    ...
```

## Step 4.9: Tax Routes

> Tax computation and lot management endpoints consumd by MCP tools in [05h-mcp-tax.md](05h-mcp-tax.md).

```python
# packages/api/src/zorivest_api/routes/tax.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal

tax_router = APIRouter(prefix="/api/v1/tax", tags=["tax"])


# ── Request / Response schemas ──────────────────────────────

class SimulateTaxRequest(BaseModel):
    ticker: str
    action: Literal["sell", "cover"]
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)
    account_id: str
    cost_basis_method: Literal["fifo", "lifo", "specific_id", "avg_cost"] = "fifo"

class EstimateTaxRequest(BaseModel):
    tax_year: int
    account_id: Optional[str] = None
    filing_status: Literal["single", "married_joint", "married_separate", "head_of_household"] = "single"
    include_unrealized: bool = False

class WashSaleRequest(BaseModel):
    account_id: str
    ticker: Optional[str] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None

class RecordPaymentRequest(BaseModel):
    quarter: Literal["Q1", "Q2", "Q3", "Q4"]
    tax_year: int
    payment_amount: float = Field(gt=0)
    confirm: bool


# ── Tax simulation ──────────────────────────────────────────

@tax_router.post("/simulate", status_code=200)
async def simulate_tax_impact(body: SimulateTaxRequest,
                               service = Depends(get_tax_service)):
    """Pre-trade what-if tax simulation.
    Returns lot-level close preview, ST/LT split, estimated tax, wash risk, hold-savings."""
    return service.simulate_impact(body)


# ── Tax estimation ──────────────────────────────────────────

@tax_router.post("/estimate", status_code=200)
async def estimate_tax(body: EstimateTaxRequest,
                        service = Depends(get_tax_service)):
    """Compute overall tax estimate from profile + trading data.
    Returns federal + state estimate with bracket breakdown."""
    return service.estimate(body)


# ── Wash sale detection ─────────────────────────────────────

@tax_router.post("/wash-sales", status_code=200)
async def find_wash_sales(body: WashSaleRequest,
                           service = Depends(get_tax_service)):
    """Detect wash sale chains/conflicts within 30-day windows.
    Returns wash sale chains with disallowed amounts and affected tickers."""
    return service.find_wash_sales(body)


# ── Tax lot management ──────────────────────────────────────

@tax_router.get("/lots", status_code=200)
async def get_tax_lots(account_id: str,
                       ticker: Optional[str] = None,
                       status: Literal["open", "closed", "all"] = "all",
                       sort_by: Literal["acquired_date", "cost_basis", "gain_loss"] = "acquired_date",
                       service = Depends(get_tax_service)):
    """List tax lots with basis, holding period, and gain/loss fields."""
    return service.get_lots(account_id, ticker, status, sort_by)


# ── Quarterly estimates ─────────────────────────────────────

@tax_router.get("/quarterly", status_code=200)
async def get_quarterly_estimate(quarter: Literal["Q1", "Q2", "Q3", "Q4"],
                                  tax_year: int,
                                  estimation_method: Literal["annualized", "actual", "prior_year"] = "annualized",
                                  service = Depends(get_tax_service)):
    """Compute quarterly estimated tax payment obligations (read-only).
    Returns required/paid/due/penalty/due_date."""
    return service.quarterly_estimate(quarter, tax_year, estimation_method)

@tax_router.post("/quarterly/payment", status_code=200)
async def record_quarterly_tax_payment(body: RecordPaymentRequest,
                                        service = Depends(get_tax_service)):
    """Record an actual quarterly tax payment. Requires confirm=true."""
    if not body.confirm:
        raise HTTPException(400, "confirm must be true")
    return service.record_payment(body)


# ── Loss harvesting ─────────────────────────────────────────

@tax_router.get("/harvest", status_code=200)
async def harvest_losses(account_id: Optional[str] = None,
                          min_loss_threshold: float = 0.0,
                          exclude_wash_risk: bool = False,
                          service = Depends(get_tax_service)):
    """Scan portfolio for harvestable losses.
    Returns ranked opportunities + wash-risk annotations + totals."""
    return service.harvest_scan(account_id, min_loss_threshold, exclude_wash_risk)


# ── YTD summary ─────────────────────────────────────────────

@tax_router.get("/ytd-summary", status_code=200)
async def get_ytd_tax_summary(tax_year: int,
                               account_id: Optional[str] = None,
                               service = Depends(get_tax_service)):
    """Year-to-date tax summary dashboard data.
    Returns aggregated ST/LT, wash adjustments, estimated tax."""
    return service.ytd_summary(tax_year, account_id)
```

### Step 4.9 Tests

```python
# tests/e2e/test_tax_api.py

def test_simulate_tax_impact(client):
    response = client.post("/api/v1/tax/simulate", json={
        "ticker": "SPY", "action": "sell", "quantity": 100,
        "price": 500.0, "account_id": "DU123", "cost_basis_method": "fifo"
    })
    assert response.status_code == 200
    data = response.json()
    assert "estimated_tax" in data
    assert "lots" in data

def test_get_tax_lots(client):
    response = client.get("/api/v1/tax/lots?account_id=DU123")
    assert response.status_code == 200

def test_quarterly_estimate(client):
    response = client.get("/api/v1/tax/quarterly?quarter=Q1&tax_year=2026")
    assert response.status_code == 200
    assert "required" in response.json()

def test_record_payment_requires_confirm(client):
    response = client.post("/api/v1/tax/quarterly/payment", json={
        "quarter": "Q1", "tax_year": 2026, "payment_amount": 5000, "confirm": False
    })
    assert response.status_code == 400

def test_harvest_losses(client):
    response = client.get("/api/v1/tax/harvest")
    assert response.status_code == 200
    assert "opportunities" in response.json()

def test_ytd_summary(client):
    response = client.get("/api/v1/tax/ytd-summary?tax_year=2026")
    assert response.status_code == 200
```

## Exit Criteria

- All e2e tests pass with FastAPI `TestClient`
- Health endpoint returns 200
- Settings CRUD endpoints return correct values
- Log ingestion endpoint accepts and records frontend metrics
- Trade list supports `account_id` filter and `sort` parameter
- MCP guard lock/unlock cycle and threshold updates work end-to-end
- Version endpoint returns valid SemVer and resolution context
- Service status endpoint returns process metrics (PID, uptime, memory, CPU)
- Graceful shutdown endpoint triggers backend restart via OS service wrapper

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
- Service routes (`GET /service/status`, `POST /service/graceful-shutdown`) — see [Phase 10](10-service-daemon.md)

### Build Plan Expansion Routes

- Broker adapter routes (`GET /brokers`, `POST /brokers/{id}/sync`, `GET /brokers/{id}/positions`) — §1, §2, §24, §25
- Analytics routes (expectancy, drawdown, SQN, execution quality, PFOF, strategy breakdown, cost-of-free, AI review) — §10–§15, §21, §22
- Round-trip routes (`GET /round-trips`) — §3
- Identifier resolution route (`POST /identifiers/resolve`) — §5
- Trade journal linking route (`POST /trades/{exec_id}/journal-link`) — §16
- CSV/PDF import routes (`POST /import/csv`, `POST /import/pdf`) — §18, §19
- Banking routes (import, accounts, transactions, balance update) — §26
- Mistake tracking routes (`POST /mistakes`, `GET /summary`) — §17
- Fee summary route (`GET /fees/summary`) — §9


