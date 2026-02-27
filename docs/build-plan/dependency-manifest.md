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
uv add --package zorivest-infra sqlalchemy sqlcipher3 argon2-cffi alembic "pillow>=11.1"

# Phase 2A: Backup/Restore & Settings Defaults
uv add --package zorivest-infra pyzipper

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
npm install @modelcontextprotocol/sdk@^1.26.0 zod
npm install -D typescript vitest @types/node tsx
# Discovery meta-tools (05j) require no additional packages — uses existing sdk + zod
cd ..

# Phase 6: GUI (Electron + React)
cd ui
npm init -y
npm install react react-dom @tanstack/react-table @tanstack/react-query lightweight-charts fuse.js sonner electron-store
npm install -D electron electron-builder vite @vitejs/plugin-react typescript vitest
npm install -D @testing-library/react playwright
cd ..

# Phase 7: Distribution & Release
uv add --dev pyinstaller                    # Bundle Python backend (must be in uv lockfile for `uv run`)
uv add --dev pip-audit twine                # Dependency audit + package validation
# electron-builder already installed as dev dep in ui/
# NOTE: npm >= 11.5.1 required for OIDC trusted publishing

# Phase 8: Market Data Aggregation
uv add --package zorivest-infra cryptography httpx

# Phase 9: Scheduling & Pipeline Engine
uv add --package zorivest-core apscheduler aiolimiter tenacity structlog pandera
uv add --package zorivest-infra weasyprint plotly kaleido jinja2 aiosmtplib

# Phase 10: Service Daemon
uv add --package zorivest-api psutil               # Process metrics for /service/status
cd ui && npm install @vscode/sudo-prompt && cd ..   # Windows UAC elevation for service start/stop
# WinSW binary bundled as extraResources (no npm/pip install needed)
```

## Dependency Mapping by Phase

| Phase | Package | Key Dependencies |
|-------|---------|-----------------|
| 0 | tooling | `uv` |
| 1 | `zorivest-core` | None (pure Python) |
| 1 (dev) | testing | `pytest`, `pytest-asyncio`, `pytest-mock`, `factory-boy` |
| 2 | `zorivest-infra` | `sqlalchemy`, `sqlcipher3`, `argon2-cffi`, `alembic`, `pillow>=11.1` |
| 2A | `zorivest-infra` (backup) | `pyzipper` |
| 3 | `zorivest-core` (services) | No new deps |
| 4 | `zorivest-api` | `fastapi`, `uvicorn`, `pydantic`, `httpx` |
| 5 | `mcp-server` (TS) | `@modelcontextprotocol/sdk@^1.26.0`, `zod` |
| 6 | `ui` (TS) | `react`, `electron`, `@tanstack/react-table`, `@tanstack/react-query`, `lightweight-charts`, `fuse.js`, `sonner`, `electron-store` |
| 7 | distribution | `pyinstaller`, `electron-builder`, `pip-audit`, `twine` (check only), npm ≥ 11.5.1 |
| 8 | `zorivest-infra` (market) | `cryptography`, `httpx` |
| 9 | `zorivest-core` (scheduling) | `apscheduler`, `aiolimiter`, `tenacity`, `structlog`, `pandera` |
| 9 | `zorivest-infra` (pipeline) | `weasyprint`, `plotly`, `kaleido`, `jinja2`, `aiosmtplib` |
| 10 | `zorivest-api` (service) | `psutil` |
| 10 | `ui` (TS, service) | `@vscode/sudo-prompt` |
| 10 | bundled binary | WinSW (`zorivest-service.exe`) — no package manager install |
| 1A | zorivest-infra (logging) | *(none — stdlib only)* |
| * | cross-cutting | `ruff`, `bandit`, `pyright` |

### Build Plan Expansion Dependencies

| Phase | Package | Key Dependencies | Source §§ |
|-------|---------|-----------------|----------|
| 3 | `zorivest-core` (services) | `numpy`, `scipy` | §7, §14 (MFE/MAE, Monte Carlo) |
| 2 | `zorivest-infra` (import) | `ofxtools`, `quiffen`, `chardet`, `lxml` | §26 (bank statement parsing) |
| 2 | `zorivest-infra` (import) | `pdfplumber` | §19 (PDF statement parsing) |
| 3 | `zorivest-core` (broker) | `alpaca-py` | §24 (Alpaca adapter) |
| 3 | `zorivest-core` (identifier) | `httpx` | §5 (OpenFIGI API calls) |

```bash
# Build Plan Expansion dependencies
uv add --package zorivest-infra ofxtools quiffen chardet lxml pdfplumber
uv add --package zorivest-core numpy scipy alpaca-py
```

> [!NOTE]
> **Omitted dependencies (CR2-6):** `tabula-py` omitted because it requires a JRE; `pdfplumber` covers the same PDF table extraction use case without Java. `pikepdf` omitted because encrypted bank PDFs are a niche edge case; deferred until user demand is confirmed.

