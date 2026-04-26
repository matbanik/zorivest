---
name: Backend Startup
description: Canonical commands for starting the Zorivest backend API server. Covers port, env vars, database path, and startup modes to prevent misconfiguration.
---

# Backend Startup Skill

## Quick Start

```powershell
# Start backend only (most common during MCP/GUI dev)
# CRITICAL: Must start from packages/api to use the correct database
$env:ZORIVEST_DEV_UNLOCK = "1"
cd packages/api
uv run uvicorn zorivest_api.main:app --host 127.0.0.1 --port 17787
```

## Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| **Port** | `17787` | MCP server hardcoded in `mcp-server/.env` as `ZORIVEST_API_URL=http://localhost:17787/api/v1` |
| **API prefix** | `/api/v1` | All endpoints live under this prefix |
| **Dev unlock** | `ZORIVEST_DEV_UNLOCK=1` | Bypasses auth/lock — required for local dev and MCP testing |
| **Database** | `sqlite:///zorivest.db` | **Relative path** — resolves from CWD. See §Database Path below. |

## Database Path

> [!CAUTION]
> **The database URL is a relative path.** `sqlite:///zorivest.db` creates or opens `zorivest.db` in the **current working directory**. Starting from the wrong directory creates a separate empty database — all user data will be missing.

| Startup Method | CWD | Database File | Contains |
|---|---|---|---|
| `npm run dev` from `ui/` | `packages/api/` | ✅ `packages/api/zorivest.db` | User's real data |
| `uv run uvicorn ...` from `p:\zorivest` | `p:\zorivest\` | ❌ `zorivest.db` (repo root) | Empty seed data |
| `uv run uvicorn ...` from `packages/api` | `packages/api/` | ✅ `packages/api/zorivest.db` | User's real data |

**The canonical database is `packages/api/zorivest.db`.** Always start from `packages/api/` or set the env var explicitly:

```powershell
# Option A: Start from correct directory (preferred)
$env:ZORIVEST_DEV_UNLOCK = "1"
cd packages/api
uv run uvicorn zorivest_api.main:app --host 127.0.0.1 --port 17787

# Option B: Set explicit absolute path
$env:ZORIVEST_DEV_UNLOCK = "1"
$env:ZORIVEST_DB_URL = "sqlite:///P:/zorivest/packages/api/zorivest.db"
uv run uvicorn zorivest_api.main:app --host 127.0.0.1 --port 17787
```

## Startup Modes

### Backend Only (for MCP testing)

Use when the GUI is already running or you only need the API:

```powershell
$env:ZORIVEST_DEV_UNLOCK = "1"
cd packages/api
uv run uvicorn zorivest_api.main:app --host 127.0.0.1 --port 17787
```

### Full Stack (Backend + GUI)

Starts both the API and the Electron GUI:

```powershell
cd ui
npm run dev
```

> [!CAUTION]
> `npm run dev` starts the backend on port 17787. If the port is already occupied (e.g., you started the backend manually first), it will fail. Stop the manual backend first.

### GUI Only (backend already running)

```powershell
$env:ZORIVEST_BACKEND_URL = "http://127.0.0.1:17787"
cd ui
npx electron-vite dev
```

## MCP Interaction Policy

> [!CAUTION]
> **AI agents MUST use MCP tools exclusively.** Never bypass the MCP layer by calling REST endpoints directly. The MCP server is the authorized interface for AI agent interaction with Zorivest. Direct REST calls circumvent security gates (MCP guard, confirmation tokens, approval requirements).
>
> **Policy approval is GUI-only.** There is no MCP tool for `approve_policy` by design — it is a human-in-the-loop gate. If a policy needs approval, inform the user and wait for them to approve via the GUI. Never call the REST approve endpoint directly.

### Missing MCP Tools (Known Gaps)

If you encounter an operation that requires direct REST and no MCP tool exists, **document the gap** rather than bypassing. Known gaps as of 2026-04-26:

| Operation | REST Endpoint | MCP Tool | Status |
|-----------|---------------|----------|--------|
| Approve policy | `POST /policies/{id}/approve` | None (intentional) | GUI-only by design |
| Delete policy | `DELETE /policies/{id}` | None | **Gap** — needs MCP tool with confirmation token |
| Get email config | `GET /settings/email` | None | **Gap** — agent can't check if SMTP is configured |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Starting from wrong directory → empty DB | Always `cd packages/api` first or set `ZORIVEST_DB_URL` |
| Starting on wrong port (8000) | Always use `--port 17787` — MCP server expects this |
| Missing dev unlock → DB locked | Set `$env:ZORIVEST_DEV_UNLOCK = "1"` before starting |
| Using `python -m uvicorn` | Use `uv run uvicorn` — the project uses uv workspace |
| Editing MCP source but changes don't take effect | MCP server runs from `dist/` — run `cd mcp-server && npm run build` then restart IDE (see MCP-DIST-REBUILD in `known-issues.md`) |
| Calling REST API directly to bypass MCP | Use MCP tools only. Document gaps, don't work around them. |
| Approving policies via REST API | NEVER do this. Approval is a GUI-only human gate. |

## Health Check

```powershell
# Verify backend is up
Invoke-RestMethod http://127.0.0.1:17787/api/v1/health
```

Expected: JSON with `status`, `uptime_seconds`, and `version` fields.

## API Spec Sync

After any changes to API routes, regenerate the committed OpenAPI spec:

```bash
uv run python tools/export_openapi.py -o openapi.committed.json
```

Verify with `--check` mode before committing:

```bash
uv run python tools/export_openapi.py --check openapi.committed.json
```
