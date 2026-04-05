---
name: Backend Startup
description: Canonical commands for starting the Zorivest backend API server. Covers port, env vars, and startup modes to prevent misconfiguration.
---

# Backend Startup Skill

## Quick Start

```powershell
# Start backend only (most common during MCP/GUI dev)
$env:ZORIVEST_DEV_UNLOCK = "1"
uv run uvicorn zorivest_api.main:app --host 127.0.0.1 --port 17787
```

## Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| **Port** | `17787` | MCP server hardcoded in `mcp-server/.env` as `ZORIVEST_API_URL=http://localhost:17787/api/v1` |
| **API prefix** | `/api/v1` | All endpoints live under this prefix |
| **Dev unlock** | `ZORIVEST_DEV_UNLOCK=1` | Bypasses auth/lock — required for local dev and MCP testing |

## Startup Modes

### Backend Only (for MCP testing)

Use when the GUI is already running or you only need the API:

```powershell
$env:ZORIVEST_DEV_UNLOCK = "1"
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

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Starting on wrong port (8000) | Always use `--port 17787` — MCP server expects this |
| Missing dev unlock → DB locked | Set `$env:ZORIVEST_DEV_UNLOCK = "1"` before starting |
| Using `python -m uvicorn` | Use `uv run uvicorn` — the project uses uv workspace |
| Editing MCP source but changes don't take effect | MCP server runs from `dist/` — run `cd mcp-server && npm run build` then restart IDE (see MCP-DIST-REBUILD in `known-issues.md`) |

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
