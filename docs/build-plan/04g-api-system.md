# Phase 4g: REST API — System & Infrastructure

> Part of [Phase 4: REST API](04-rest-api.md) | Tag: `system`
>
> Health check, version diagnostics, logging ingestion, MCP guard circuit breaker, service lifecycle.

---

## Logging Route

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

## MCP Guard Routes

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

> `GET /mcp-guard/status` is available **before unlock** (used by `zorivest_diagnose` to report guard state). All other `/mcp-guard/*` routes require an active database session via `Depends(get_guard_service)`. Calls without an unlocked DB session return **403**.

```python
# zorivest_api/routes/mcp_guard.py

guard_router = APIRouter(prefix="/api/v1/mcp-guard", tags=["mcp-guard"])

@guard_router.get("/status", status_code=200)
async def guard_status() -> McpGuardStatus:
    """Return current guard state, thresholds, and live call counters.
    Available before DB unlock (used by zorivest_diagnose)."""
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

def test_guard_status_available_pre_unlock(unauthenticated_client):
    """GET /mcp-guard/status returns 200 even without an unlocked DB session."""
    assert unauthenticated_client.get("/api/v1/mcp-guard/status").status_code == 200

def test_guard_mutation_routes_require_session(unauthenticated_client):
    """Config/lock/unlock routes return 403 without an unlocked DB session."""
    assert unauthenticated_client.post("/api/v1/mcp-guard/lock", json={}).status_code == 403
    assert unauthenticated_client.post("/api/v1/mcp-guard/unlock").status_code == 403
    assert unauthenticated_client.put("/api/v1/mcp-guard/config", json={}).status_code == 403

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
> **MCP Discovery & Toolset tools** (`list_available_toolsets`, `describe_toolset`, `enable_toolset`) operate entirely within the TypeScript MCP server layer and do not call any Python REST endpoints. They are defined in [05j-mcp-discovery.md](05j-mcp-discovery.md). The `ToolsetRegistry` is an in-memory TypeScript module with no backend persistence. **Exception:** `get_confirmation_token` calls `POST /api/v1/confirmation-tokens` (see [04c-api-auth.md](04c-api-auth.md)) for server-side token generation — the token is validated at the REST layer when the destructive action executes.

## Health & Service Lifecycle Routes

> Canonical endpoint paths match [Phase 10 §10.3](10-service-daemon.md). Health is top-level (no auth, no prefix). Service routes require authentication.

### Health Endpoint (no auth)

```python
# packages/api/src/zorivest_api/routes/health.py

from fastapi import APIRouter
from pydantic import BaseModel

health_router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str              # "ok"
    version: str
    uptime_seconds: int
    database: dict           # {"unlocked": bool}


@health_router.get("/api/v1/health", status_code=200)
async def health_check() -> HealthResponse:
    """Lightweight liveness probe. No auth required.
    Used by Electron to detect if backend is running,
    and by MCP tools (zorivest_diagnose, zorivest_service_restart) for polling."""
    ...
```

### Service Routes (auth required)

```python
# packages/api/src/zorivest_api/routes/service.py

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
import os, signal, psutil

service_router = APIRouter(prefix="/api/v1/service", tags=["service"])


class ServiceStatusResponse(BaseModel):
    pid: int
    uptime_seconds: float
    memory_mb: float
    cpu_percent: float
    python_version: str


@service_router.get("/status", status_code=200)
async def service_status(_user = Depends(get_current_user)) -> ServiceStatusResponse:
    """Process metrics: PID, uptime, memory, CPU, Python version.
    Requires active database session."""
    ...

@service_router.post("/graceful-shutdown", status_code=202)
async def graceful_shutdown(background_tasks: BackgroundTasks,
                            _user = Depends(get_current_user)):
    """Trigger backend restart via OS service wrapper.
    Flushes logs, closes DB connections, then exits.
    Service wrapper (systemd/launchd/NSSM) auto-restarts.
    Requires admin role."""
    ...
```

### Health & Service Tests

```python
def test_health_returns_200_pre_unlock(unauthenticated_client):
    """GET /health returns 200 even before DB unlock."""
    r = unauthenticated_client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_service_status_returns_pid(client):
    """GET /service/status returns PID and uptime (requires auth)."""
    r = client.get("/api/v1/service/status")
    assert r.status_code == 200
    assert r.json()["pid"] > 0

def test_service_status_requires_auth(unauthenticated_client):
    """GET /service/status returns 403 without auth."""
    r = unauthenticated_client.get("/api/v1/service/status")
    assert r.status_code == 403

def test_graceful_shutdown_requires_admin(client_read_only):
    """POST /service/graceful-shutdown returns 403 for non-admin role."""
    r = client_read_only.post("/api/v1/service/graceful-shutdown")
    assert r.status_code == 403
```

## Version Route

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

### Version Tests

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

## Consumer Notes

- **MCP tools:** `zorivest_emergency_stop` (guard lock) ([05a](05a-mcp-zorivest-settings.md)), `zorivest_service_restart` (graceful shutdown), `zorivest_service_status` ([05b](05b-mcp-zorivest-diagnostics.md))
- **GUI pages:** [06f-gui-settings.md](06f-gui-settings.md) — MCP guard panel, version info
