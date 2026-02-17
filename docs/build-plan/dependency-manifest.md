# Dependency Installation Order

> Part of [Zorivest Build Plan](../BUILD_PLAN.md) — Install dependencies in the same order as the build phases.

---

## Installation Commands

```bash
# Phase 0: Project tooling
pip install uv                              # or: curl -LsSf https://astral.sh/uv/install.sh | sh
uv init --name zorivest

# Phase 1: Core (zero external deps for domain)
# Only pytest for testing
uv add --dev pytest pytest-asyncio pytest-mock factory-boy

# Phase 2: Infrastructure
uv add --package zorivest-infra sqlalchemy sqlcipher3 argon2-cffi alembic pillow

# Phase 3: Services (no new deps — uses core + infra)

# Phase 4: REST API
uv add --package zorivest-api fastapi uvicorn pydantic httpx

# Cross-cutting (Python)
# Phase 1A (Logging): zero external dependencies — stdlib only
uv add --dev ruff bandit pip-audit

# ── TypeScript side (npm/pnpm) ──────────────────────────────

# Phase 5: MCP Server (TypeScript)
cd mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
npm install -D typescript vitest @types/node tsx
cd ..

# Phase 6: GUI (Electron + React)
cd ui
npm init -y
npm install react react-dom @tanstack/react-table @tanstack/react-query lightweight-charts fuse.js sonner electron-store
npm install -D electron electron-builder vite @vitejs/plugin-react typescript vitest
npm install -D @testing-library/react playwright
cd ..

# Phase 7: Distribution
pip install pyinstaller                     # Bundle Python backend
# electron-builder already installed as dev dep in ui/

# Phase 8: Market Data Aggregation
uv add --package zorivest-infra cryptography httpx
```

## Dependency Mapping by Phase

| Phase | Package | Key Dependencies |
|-------|---------|-----------------|
| 0 | tooling | `uv` |
| 1 | `zorivest-core` | None (pure Python) |
| 1 (dev) | testing | `pytest`, `pytest-asyncio`, `pytest-mock`, `factory-boy` |
| 2 | `zorivest-infra` | `sqlalchemy`, `sqlcipher3`, `argon2-cffi`, `alembic`, `pillow` |
| 3 | `zorivest-core` (services) | No new deps |
| 4 | `zorivest-api` | `fastapi`, `uvicorn`, `pydantic`, `httpx` |
| 5 | `mcp-server` (TS) | `@modelcontextprotocol/sdk`, `zod` |
| 6 | `ui` (TS) | `react`, `electron`, `@tanstack/react-table`, `@tanstack/react-query`, `lightweight-charts`, `fuse.js`, `sonner`, `electron-store` |
| 7 | distribution | `pyinstaller`, `electron-builder` |
| 8 | `zorivest-infra` (market) | `cryptography`, `httpx` |
| 1A | zorivest-infra (logging) | *(none — stdlib only)* |
| * | cross-cutting | `ruff`, `bandit` |
