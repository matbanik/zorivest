# Phase 4c: REST API — Auth & Security

> Part of [Phase 4: REST API](04-rest-api.md) | Tag: `auth`
>
> Database unlock/lock, API key management, session management, confirmation tokens for destructive MCP operations.

---

## Auth / Unlock Routes (Envelope Encryption)

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

## Confirmation Token Route

> Server-side token generation for the 2-step destructive operation pattern. Used by annotation-unaware MCP clients (Cursor, etc.) as a safety gate before executing state-mutating tools. See [Phase 5 §5.13 Pattern E](05-mcp-server.md) and [Phase 5j `get_confirmation_token`](05j-mcp-discovery.md).

```python
# packages/api/src/zorivest_api/routes/confirmation.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import secrets
from zorivest_core.auth import get_auth_context

confirm_router = APIRouter(prefix="/api/v1/confirmation-tokens", tags=["auth"])

VALID_DESTRUCTIVE_ACTIONS = {
    "zorivest_emergency_stop",
    "create_trade",
    "sync_broker",
    "disconnect_market_provider",
    "zorivest_service_restart",
}

class ConfirmationRequest(BaseModel):
    action: str
    params_summary: str

class ConfirmationResponse(BaseModel):
    token: str
    action: str
    params_summary: str
    expires_in_seconds: int = 60

@confirm_router.post("/", status_code=201, response_model=ConfirmationResponse)
async def create_confirmation_token(body: ConfirmationRequest,
                                     auth = Depends(get_auth_context)):
    """Generate a time-limited confirmation token for destructive MCP operations.
    Token expires after 60s. Stored in TTL cache and validated by destructive route handlers."""
    if body.action not in VALID_DESTRUCTIVE_ACTIONS:
        raise HTTPException(400, f"Unknown destructive action: {body.action}")
    token = f"ctk_{secrets.token_urlsafe(16)}"
    # Store in in-memory TTL cache with 60s expiry — validated by destructive handlers
    return ConfirmationResponse(
        token=token, action=body.action,
        params_summary=body.params_summary, expires_in_seconds=60
    )
```

### E2E Tests

```python
def test_create_confirmation_token(client):
    """POST /confirmation-tokens returns a token for valid destructive action."""
    resp = client.post("/api/v1/confirmation-tokens", json={
        "action": "zorivest_emergency_stop",
        "params_summary": "Lock all tools due to suspected loop",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["token"].startswith("ctk_")
    assert data["expires_in_seconds"] == 60
    assert data["action"] == "zorivest_emergency_stop"

def test_reject_unknown_destructive_action(client):
    """POST /confirmation-tokens rejects unknown action names."""
    resp = client.post("/api/v1/confirmation-tokens", json={
        "action": "not_a_real_action",
        "params_summary": "test",
    })
    assert resp.status_code == 400
```

## Consumer Notes

- **MCP tools:** `get_confirmation_token` ([05j](05j-mcp-discovery.md)), auth unlock/lock ([05a](05a-mcp-zorivest-settings.md))
- **GUI pages:** [06a-gui-shell.md](06a-gui-shell.md) — unlock screen, API key manager
