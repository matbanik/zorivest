# 09g — Approval Security & MCP Scheduling Completeness

> Phase: P2.5d · MEU-PH11 (CSRF token), MEU-PH12 (MCP gap fill)
> Prerequisites: Phase 4 ✅, Phase 5 ✅, Phase 6 ✅, Phase 9c ✅
> Unblocks: Secure agent-first policy lifecycle, MCP-only policy management
> Resolves: [MCP-APPROVBYPASS], [MCP-POLICYGAP]
> Status: ✅ complete (2026-04-29)

---

## 9G.1 CSRF Approval Token Architecture (MEU-PH11)

### 9G.1a Problem Statement

`POST /api/v1/scheduling/policies/{id}/approve` has no mechanism to verify the caller is the GUI. An AI agent with HTTP access can approve its own policies by calling the REST endpoint directly, bypassing the human-in-the-loop approval gate. The MCP server correctly does NOT expose an `approve_policy` tool, but the unprotected REST endpoint makes this meaningless.

**Attack path:** Agent creates policy via MCP → calls REST approve → runs pipeline via MCP. All 3 steps succeed without human review.

### 9G.1b Design

**CSRF Challenge Token Flow:**

```
┌─────────────────┐     IPC: generate-approval-token     ┌──────────────────┐
│  Electron Main  │ ◄──────────────────────────────────── │  Renderer (GUI)  │
│   Process        │ ─────────────────────────────────────►│  Approve Button  │
│                  │     IPC: returns { token, expires }   │                  │
└────────┬─────────┘                                       └────────┬─────────┘
         │                                                          │
         │  In-memory token store                                   │
         │  Map<token, { policy_id, expires_at }>                   │
         │                                                          │
         │                                                          ▼
         │                                               POST /policies/{id}/approve
         │                                               Header: X-Approval-Token: <token>
         │                                                          │
         │                                                          ▼
         │                                               ┌──────────────────┐
         └──────────────────────────────────────────────►│  FastAPI Server  │
                    Validates token via IPC                │  Token Validator │
                    or shared-memory check                 └──────────────────┘
```

### 9G.1c Implementation

#### Electron Main Process

New file: `ui/src/main/approval-token-manager.ts`

```typescript
import { ipcMain, BrowserWindow } from 'electron';
import crypto from 'node:crypto';

const TOKEN_TTL_MS = 5 * 60 * 1000; // 5 minutes
const tokenStore = new Map<string, { policyId: string; expiresAt: number }>();

export function registerApprovalTokenHandlers(): void {
  ipcMain.handle('generate-approval-token', (_event, policyId: string) => {
    const token = crypto.randomBytes(32).toString('hex');
    const expiresAt = Date.now() + TOKEN_TTL_MS;
    tokenStore.set(token, { policyId, expiresAt });
    return { token, expiresAt };
  });

  ipcMain.handle('validate-approval-token', (_event, token: string, policyId: string) => {
    const entry = tokenStore.get(token);
    if (!entry) return { valid: false, reason: 'TOKEN_NOT_FOUND' };
    if (Date.now() > entry.expiresAt) {
      tokenStore.delete(token);
      return { valid: false, reason: 'TOKEN_EXPIRED' };
    }
    if (entry.policyId !== policyId) {
      return { valid: false, reason: 'POLICY_MISMATCH' };
    }
    // Single-use: delete after validation
    tokenStore.delete(token);
    return { valid: true };
  });
}

// Periodic cleanup of expired tokens
setInterval(() => {
  const now = Date.now();
  for (const [token, entry] of tokenStore) {
    if (now > entry.expiresAt) tokenStore.delete(token);
  }
}, 60_000);
```

#### FastAPI Middleware

New file: `packages/api/src/zorivest_api/middleware/approval_token.py`

```python
from fastapi import Request, HTTPException

async def validate_approval_token(request: Request) -> None:
    """Dependency for approval endpoints. Validates CSRF token from Electron IPC."""
    token = request.headers.get("X-Approval-Token")
    if not token:
        raise HTTPException(
            status_code=403,
            detail="Approval requires a CSRF token from the GUI. "
                   "This endpoint cannot be called directly by AI agents."
        )
    # Validate token via IPC bridge or shared-memory
    # Implementation depends on chosen IPC mechanism
    validator = request.app.state.approval_token_validator
    result = await validator.validate(token, request.path_params["policy_id"])
    if not result["valid"]:
        raise HTTPException(
            status_code=403,
            detail=f"Invalid approval token: {result['reason']}"
        )
```

#### API Route Update

```python
# In scheduling.py
@router.post("/policies/{policy_id}/approve", dependencies=[Depends(validate_approval_token)])
async def approve_policy(policy_id: str, ...):
    ...
```

### 9G.1d Security Properties

| Property | Guarantee |
|----------|-----------|
| **Single-use** | Token deleted after validation — no replay |
| **Time-limited** | 5-minute TTL — no stale token accumulation |
| **Policy-scoped** | Token bound to specific `policy_id` — no reuse across policies |
| **Process-bound** | Token generated in Electron main process — AI agents cannot forge |
| **Audit** | Token generation and validation logged to scheduling audit trail |

### 9G.1e IPC Bridge Design Options

Two implementation approaches (choose during execution):

1. **HTTP callback** — Electron main process exposes a local-only endpoint (e.g., `http://localhost:17788/internal/validate-token`) that the FastAPI server calls. Pros: simple, no shared memory. Cons: extra port, must be firewalled.

2. **File-based token exchange** — Electron writes tokens to a temp file with restrictive permissions, FastAPI reads and validates. Pros: no network dependency. Cons: filesystem race conditions.

> [!IMPORTANT]
> The chosen approach must be documented in an ADR before implementation.

---

## 9G.2 MCP Scheduling Gap Fill (MEU-PH12)

### 9G.2a Problem Statement

During iterative policy development, the agent needs to delete and recreate policies. No MCP tools exist for `delete_policy` or `update_policy`, forcing direct REST calls that bypass MCP guards, confirmation tokens, and audit logging.

### 9G.2b New MCP Tools

#### `delete_policy`

Delete a pipeline policy. **Destructive action** — requires confirmation token.

```typescript
server.tool(
  'delete_policy',
  'Delete a pipeline policy. This is a destructive action requiring confirmation.',
  {
    policy_id: z.string().describe('Policy UUID to delete'),
    confirmation_token: z.string().describe(
      'Confirmation token from get_confirmation_token. Required for destructive actions.'
    ),
  },
  async ({ policy_id, confirmation_token }) => {
    // Validate confirmation token first (follows delete_trade pattern)
    const tokenValid = confirmationStore.validate(confirmation_token, `delete_policy:${policy_id}`);
    if (!tokenValid) {
      return { content: [{ type: 'text' as const, text: 'Invalid or expired confirmation token.' }], isError: true };
    }
    const res = await fetch(`${API_BASE}/scheduling/policies/${policy_id}`, { method: 'DELETE' });
    if (!res.ok) {
      const data = await res.json();
      return { content: [{ type: 'text' as const, text: `Delete failed: ${JSON.stringify(data)}` }], isError: true };
    }
    return { content: [{ type: 'text' as const, text: `Policy ${policy_id} deleted.` }] };
  }
);
```

**Annotations:**
- `readOnlyHint`: false
- `destructiveHint`: true
- `idempotentHint`: false
- `toolset`: scheduling

#### `update_policy`

In-place update of a policy's JSON document (without delete+recreate).

```typescript
server.tool(
  'update_policy',
  'Update a policy\'s JSON document in-place. Resets approval status (re-approval required).',
  {
    policy_id: z.string().describe('Policy UUID to update'),
    policy_json: z.record(z.unknown()).describe('Updated PolicyDocument JSON'),
  },
  async ({ policy_id, policy_json }) => {
    const res = await fetch(`${API_BASE}/scheduling/policies/${policy_id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ policy_json }),
    });
    const data = await res.json();
    if (!res.ok) {
      return { content: [{ type: 'text' as const, text: `Update failed:\n${JSON.stringify(data, null, 2)}` }], isError: true };
    }
    return { content: [{ type: 'text' as const, text: `Policy updated (approval reset):\n${JSON.stringify(data, null, 2)}` }] };
  }
);
```

**Annotations:**
- `readOnlyHint`: false
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: scheduling

#### `get_email_config`

Check SMTP configuration readiness before creating policies with email send steps.

```typescript
server.tool(
  'get_email_config',
  'Check if SMTP email is configured and ready for pipeline send steps. Returns provider name and connection status without exposing credentials.',
  {},
  async () => {
    const res = await fetch(`${API_BASE}/settings/email/status`);
    const data = await res.json();
    return { content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }] };
  }
);
```

**Annotations:**
- `readOnlyHint`: true
- `destructiveHint`: false
- `idempotentHint`: true
- `toolset`: scheduling

### 9G.2c Backend Support

| Endpoint | Exists? | Notes |
|----------|---------|-------|
| `DELETE /scheduling/policies/{id}` | ✅ Yes | Already implemented |
| `PUT /scheduling/policies/{id}` | ✅ Yes | Already implemented |
| `GET /settings/email/status` | ⬜ New | Return `{configured: bool, provider: str, host: str}` without credentials |

---

## 9G.3 Tests

### CSRF Token Tests

New files:
- `ui/src/main/__tests__/approval-token-manager.test.ts` (Vitest)
- `tests/unit/test_approval_token_middleware.py` (pytest)

| Test | Assertion |
|------|-----------|
| `test_token_generation` | Returns 64-char hex token with valid expiry |
| `test_token_single_use` | Second validation of same token fails |
| `test_token_expiry` | Token invalid after TTL |
| `test_token_policy_scope` | Token for policy A rejected for policy B |
| `test_approve_without_token_403` | `POST /approve` without `X-Approval-Token` returns 403 |
| `test_approve_with_invalid_token_403` | Random token returns 403 |
| `test_approve_with_valid_token_200` | Valid token + correct policy_id succeeds |

### MCP Gap Fill Tests

New file: `mcp-server/src/__tests__/scheduling-gap-fill.test.ts` (Vitest)

| Test | Assertion |
|------|-----------|
| `test_delete_policy_requires_confirmation` | Missing token → error response |
| `test_delete_policy_valid_token` | Valid token + existing policy → success |
| `test_delete_policy_not_found` | Valid token + missing policy → 404 error |
| `test_update_policy_success` | Valid policy_json → updated response |
| `test_update_policy_validation_error` | Invalid policy_json → validation errors |
| `test_get_email_config_configured` | SMTP configured → returns status |
| `test_get_email_config_not_configured` | No SMTP → `configured: false` |

---

## 9G.4 Exit Criteria

- [ ] Electron IPC `generate-approval-token` + `validate-approval-token` handlers exist
- [ ] `ApprovalTokenManager` with TTL, single-use, policy-scoped tokens
- [ ] `POST /policies/{id}/approve` requires valid `X-Approval-Token` header
- [ ] AI agent calling `POST /approve` without token receives 403
- [ ] `delete_policy` MCP tool registered with destructive annotation + confirmation token
- [ ] `update_policy` MCP tool registered in scheduling toolset
- [ ] `get_email_config` MCP tool returns SMTP readiness without credentials
- [ ] `GET /settings/email/status` endpoint exists
- [ ] All 14 tests pass (7 CSRF + 7 MCP gap fill)
- [ ] ADR documenting IPC bridge approach
