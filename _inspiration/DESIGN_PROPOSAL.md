# Hybrid TypeScript + Python architecture: a complete blueprint

**The optimal foundation for Zorivest combines a TypeScript UI (Electron + React) with a Python backend (FastAPI + SQLCipher + ibapi), connected via REST on localhost.** The Python backend uses hexagonal architecture with a shared service layer, encrypted SQLite via SQLCipher, and FastAPI serving both the TypeScript UI and a TypeScript MCP server. A TypeScript MCP server (using the reference SDK) provides AI agent access via IDE, calling the same REST endpoints as the UI. Python's `typing.Protocol` and manual dependency injection provide hexagonal architecture without framework overhead, while `structlog` with `contextvars` gives unified observability across every Python layer. The Electron shell manages the Python backend as a child process — two runtimes, one clean REST boundary.

---

## How to structure the project and monorepo

The **src layout** is the consensus standard endorsed by PyPA, pyOpenSci, and every major Python tooling project. It prevents accidental imports of local files over installed packages and ensures tests run against the installed version. Combined with `uv` workspaces, a monorepo cleanly separates each component while sharing a single lockfile.

```
zorivest/
├── pyproject.toml              # Root Python workspace config (uv)
├── uv.lock                     # Single lockfile for all Python packages
├── package.json                # Root TypeScript workspace config (npm/pnpm)
├── CLAUDE.md                   # AI agent context
├── AGENTS.md                   # Universal AI agent instructions
├── docs/
│   └── decisions/              # ADRs (ADR-0001.md, ADR-0002.md...)
│
│   ═══ PYTHON PACKAGES (managed by uv) ═══════════════════════════
│
├── packages/
│   ├── core/                   # Domain + application layer (shared)
│   │   ├── pyproject.toml
│   │   └── src/zorivest_core/
│   │       ├── domain/         # Entities, value objects, events
│   │       ├── application/    # Use cases, ports (Protocol ABCs), DTOs
│   │       └── services/       # Service layer orchestration
│   ├── infrastructure/         # Adapters for DB, external APIs, logging
│   │   ├── pyproject.toml
│   │   └── src/zorivest_infra/
│   │       ├── database/       # SQLAlchemy repos, UoW, migrations
│   │       ├── external_apis/  # httpx adapters for third-party APIs
│   │       └── logging/        # structlog configuration
│   └── api/                    # FastAPI REST layer (serves UI + MCP)
│       ├── pyproject.toml
│       └── src/zorivest_api/
│           ├── routes/
│           ├── middleware/
│           └── bootstrap.py    # DI wiring
│
│   ═══ TYPESCRIPT PACKAGES (managed by npm/pnpm) ═════════════════
│
├── ui/                         # Electron + React desktop application
│   ├── package.json
│   ├── electron/
│   │   ├── main.ts             # Electron main process + Python manager
│   │   └── preload.ts          # Context bridge
│   └── src/
│       ├── App.tsx             # React root
│       ├── pages/              # Dashboard, Trades, Plans, Reports
│       ├── components/         # Trade table, charts, screenshot panel
│       ├── hooks/              # useApi(), useTrades(), useAccounts()
│       └── styles/             # CSS / Tailwind
├── mcp-server/                 # TypeScript MCP server (calls REST API)
│   ├── package.json
│   ├── src/
│   │   ├── index.ts            # MCP server setup
│   │   └── tools/              # MCP tool definitions (REST wrappers)
│   └── tsconfig.json
│
└── tests/
    ├── python/                 # pytest (unit, integration, e2e)
    │   ├── unit/
    │   ├── integration/
    │   └── e2e/
    └── typescript/             # Vitest (UI + MCP)
        ├── ui/
        └── mcp/
```

The root `pyproject.toml` configures `uv` workspaces for the **Python packages**:

```toml
[project]
name = "zorivest"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
zorivest-core = { workspace = true }
zorivest-infra = { workspace = true }
```

The root `package.json` configures npm/pnpm workspaces for the **TypeScript packages**:

```json
{
  "name": "zorivest",
  "private": true,
  "workspaces": ["ui", "mcp-server"]
}
```

Each Python package's `pyproject.toml` declares dependencies on sibling packages via `tool.uv.sources`. Running `uv sync` resolves everything into a single `uv.lock`, and `uv run --package zorivest-api uvicorn zorivest_api.main:app` launches the backend. The TypeScript packages use standard npm/pnpm workspaces. Both sides operate independently — `uv` for Python, `npm` for TypeScript — orchestrated by root-level scripts or a `Makefile`.

---

## Hexagonal architecture and how layers connect

The architecture follows the **dependency rule**: dependencies point inward only. Infrastructure depends on application, which depends on domain. Domain never imports from infrastructure. Python's `typing.Protocol` makes this practical without framework overhead.

**Domain layer** contains pure business objects — dataclasses, value objects, domain events — with zero external dependencies. **Application layer** defines ports (interfaces via `Protocol`) and use cases that orchestrate domain logic. **Infrastructure layer** provides concrete adapters: SQLAlchemy repositories, httpx API clients, file handlers. **Entry points** (GUI, API, MCP) are thin wrappers that call the application layer.

```python
# application/ports.py — defines WHAT the app needs
from typing import Protocol

class ItemRepository(Protocol):
    def get(self, item_id: int) -> Item: ...
    def save(self, item: Item) -> None: ...
    def list_all(self, limit: int = 100) -> list[Item]: ...

# infrastructure/database/repositories.py — HOW it's done
class SqlAlchemyItemRepository:
    def __init__(self, session: Session):
        self._session = session
    def get(self, item_id: int) -> Item:
        return self._session.get(ItemModel, item_id)
```

The **service layer** is where all entry points converge. GUI button clicks, API endpoints, and MCP tool calls all invoke the same service methods through a **Unit of Work** pattern that wraps database transactions in Python context managers:

```python
class ItemService:
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def create_item(self, cmd: CreateItemCommand) -> Item:
        with self.uow:
            item = Item(name=cmd.name, price=cmd.price)
            self.uow.items.save(item)
            self.uow.commit()
            return item
```

For **dependency injection**, the most Pythonic approach is manual constructor injection with a bootstrap/composition root — no framework needed. Each entry point (GUI, API, MCP) has a `bootstrap.py` that wires dependencies. For larger applications, `dependency-injector` (4k+ GitHub stars, Cython-optimized) provides declarative containers with provider overriding for tests. The key reference is *Architecture Patterns with Python* at cosmicpython.com, which covers Repository, Unit of Work, Service Layer, Domain Events, and DI with working code.

**Event-driven patterns** add value for side effects and cross-module communication. A lightweight message bus maps domain events to handlers: when an item is created, the bus can trigger notifications, update read models, or log audit events without coupling those concerns to the core logic. For the event bus, either build a custom `MessageBus` following the Cosmic Python pattern or use **blinker** (fast in-process signals, used by Flask). For a plugin/extension system, **pluggy** (v1.6, used by pytest) provides hook-based extensibility with clearly defined extension points.

---

## Encrypted SQLite with user-supplied passphrase

**`sqlcipher3`** (v0.6.2) is the recommended Python binding for SQLCipher. It ships self-contained binary wheels for Windows, macOS, and Linux — no system-level SQLCipher installation required. It's DB-API 2.0 compliant, a drop-in replacement for `sqlite3`, and the driver SQLAlchemy's `sqlite+pysqlcipher://` dialect auto-selects for Python 3.

SQLCipher 4.7.x provides transparent **AES-256 encryption** with PBKDF2-HMAC-SHA512 (256,000 iterations) by default. However, for stronger security, use **application-level Argon2id** to derive the encryption key, then pass a raw hex key that bypasses SQLCipher's internal PBKDF2:

```python
from argon2.low_level import hash_secret_raw, Type
import os

def derive_key(passphrase: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret=passphrase.encode('utf-8'),
        salt=salt,
        time_cost=2, memory_cost=19456,  # 19 MiB — OWASP minimum
        parallelism=1, hash_len=32, type=Type.ID
    )

# On first run: salt = os.urandom(16), stored in bootstrap.json
# On each open: user provides passphrase → derive key → open DB
raw_key = derive_key(user_passphrase, salt)
conn.execute(f"PRAGMA key=\"x'{raw_key.hex()}'\"")
```

**Argon2id** (via `argon2-cffi` v25.1.0) is the OWASP #1 recommendation for password hashing in 2025, offering memory-hardness that defeats GPU/ASIC attacks. The salt is not secret — store it in a minimal unencrypted `bootstrap.json` alongside the database path and KDF parameters. This solves the chicken-and-egg problem: the app reads bootstrap config, prompts for the passphrase, derives the key, and unlocks the encrypted database.

For **SQLAlchemy 2.0+ integration**, use a custom `creator` function with `StaticPool` to avoid repeated expensive KDF on each connection:

```python
engine = create_engine("sqlite://", creator=create_connection,
                       poolclass=StaticPool,
                       connect_args={"check_same_thread": False})
```

**All application settings** belong in a key-value table inside the encrypted database: `(key TEXT PK, value TEXT, value_type TEXT, updated_at TEXT)`. Load all settings into an in-memory cache on startup. Since no native async SQLCipher driver exists, wrap synchronous operations in `asyncio.to_thread()` for async contexts. For schema migrations, **Alembic** with `render_as_batch=True` is essential — SQLite's limited `ALTER TABLE` support requires batch mode. For backups, SQLite's backup API creates encrypted copies; `sqlcipher_export()` enables plaintext export/import; `PRAGMA rekey` changes the passphrase.

---

## TypeScript MCP server (reference SDK)

The MCP (Model Context Protocol) specification reached version **2025-06-18**, now governed by the Linux Foundation's Agentic AI Foundation. The **TypeScript SDK** (`@modelcontextprotocol/sdk`) is the reference implementation — bugs are found and fixed here first, community examples are overwhelmingly TypeScript, and edge-case solutions are easier to find. MCP servers are now classified as **OAuth 2.0 Resource Servers** under the latest auth specification.

In the hybrid architecture, the MCP server runs as a **separate TypeScript package** (`mcp-server/`) that calls the Python REST API via `fetch()`. Each MCP tool is a thin wrapper around a REST endpoint:

```typescript
// mcp-server/src/tools/trade-tools.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

const API_BASE = 'http://localhost:8765/api/v1';

export function registerTradeTools(server: McpServer) {
  server.tool(
    'create_trade',
    'Record a new trade execution. Deduplicates by exec_id.',
    {
      exec_id: { type: 'string' },
      instrument: { type: 'string' },
      action: { type: 'string', enum: ['BOT', 'SLD'] },
      quantity: { type: 'number' },
      price: { type: 'number' },
      account: { type: 'string' },
    },
    async ({ exec_id, instrument, action, quantity, price, account }) => {
      const res = await fetch(`${API_BASE}/trades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exec_id, instrument, action, quantity, price, account }),
      });
      return { content: [{ type: 'text', text: JSON.stringify(await res.json()) }] };
    }
  );

  server.tool(
    'list_trades',
    'List recent trade executions with pagination.',
    { limit: { type: 'number' }, offset: { type: 'number' } },
    async ({ limit = 50, offset = 0 }) => {
      const res = await fetch(`${API_BASE}/trades?limit=${limit}&offset=${offset}`);
      return { content: [{ type: 'text', text: JSON.stringify(await res.json()) }] };
    }
  );
}
```

The MCP server uses **Streamable HTTP** transport (the current MCP standard — SSE is deprecated) and can run in two modes:

| Mode | When | Transport | Auth |
|---|---|---|---|
| **Embedded** | GUI running | Streamable HTTP on `:8766` (within Electron process) | Session-inherited (GUI already authenticated) |
| **Standalone** | IDE-only, no GUI | Streamable HTTP on `:8766` (separate process) | Bearer token (API key: `zrv_sk_...`) |

Both modes expose a single MCP endpoint at `POST http://localhost:8766/mcp` with `MCP-Protocol-Version: 2025-06-18` and `Mcp-Session-Id` headers. In standalone mode, the MCP server authenticates via Bearer token and forwards the API key to the Python backend's `/api/v1/auth/unlock` endpoint for database access via envelope encryption (see `02-infrastructure.md`).

For IDE integration, Cursor connects via `.cursor/mcp.json`, Windsurf via its MCP configuration, and Claude Code via `claude mcp add`:

```json
// .cursor/mcp.json (or equivalent IDE config)
{
  "mcpServers": {
    "zorivest": {
      "url": "http://localhost:8766/mcp",
      "headers": {
        "Authorization": "Bearer zrv_sk_..."
      }
    }
  }
}
```

The **MCP Inspector** (`npx @modelcontextprotocol/inspector`) provides visual testing during development.

Both the MCP tools and the Electron UI call the **same REST API**, ensuring consistent business logic regardless of the access path. Tool descriptions are critical — LLMs use them to decide when and how to call tools, so write clear, specific descriptions.

---

## REST API with FastAPI and external API patterns

**FastAPI 0.115+** with **Pydantic v2** is the clear choice for the REST layer. Structure routers by domain module (not by file type): each module gets its own `router.py`, `schemas.py`, `service.py`, and `dependencies.py`. FastAPI's `Depends()` injects the service layer into route handlers, keeping routes thin:

```python
@router.get("/reports/{report_id}")
async def get_report(report_id: int,
                     service: ReportService = Depends(get_report_service)):
    return await service.get_report(report_id)
```

For authentication, **API key auth** is simplest for a local/service application; use **JWT with PyJWT + pwdlib** (FastAPI's current recommendation, replacing passlib) for user-level auth with roles. Password hashing should use Argon2 via pwdlib. Rate limiting with **slowapi** prevents abuse, and Pydantic v2's Rust-based validation provides **4–17x faster** input validation than v1.

**REST is the clear recommendation** over GraphQL for a DB management and reporting application. REST provides natural CRUD mapping, built-in HTTP caching, and mature tooling. GraphQL adds unnecessary complexity for this use case. If complex querying needs emerge later, **Strawberry** is the modern Python GraphQL framework with native type-hint support and FastAPI integration.

For **external API connections**, the adapter/gateway pattern wraps each external service behind a `Protocol` interface. The real adapter uses **httpx** (the modern standard — sync+async, HTTP/2, Requests-like API) while a fake adapter enables testing without network calls. Layer **tenacity** for retry with exponential backoff inside **pybreaker** for circuit breaking:

```python
@retry(stop=stop_after_attempt(3),
       wait=wait_exponential_jitter(initial=1, max=10),
       retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)))
@api_breaker  # Opens after 5 failures, resets after 60s
async def call_external_api(client: httpx.AsyncClient, url: str):
    response = await client.get(url)
    response.raise_for_status()
    return response.json()
```

Manage `httpx.AsyncClient` as a singleton with connection pooling (up to 100 connections, 20 keepalive) via FastAPI's dependency injection, and clean up in the app's lifespan handler.

---

## Electron + React is the right GUI for a modern trading desktop

**Electron** (Chromium + Node.js) combined with **React** provides a modern, polished UI with the richest component ecosystem available. While PySide6's QTableView offers powerful model/view architecture, the Electron + React stack delivers modern aesthetics — dark mode, glassmorphism, micro-animations, smooth transitions — with significantly faster iteration via Vite HMR. Memory overhead (~200MB) is a non-issue on 32GB+ developer machines.

The GUI communicates with the Python backend exclusively via **REST on localhost** — no IPC, no shared memory, no native modules crossing the boundary. Clean HTTP JSON:

```typescript
// ui/src/hooks/useApi.ts
const API_BASE = 'http://localhost:8765/api/v1';

export async function fetchTrades(limit = 50, offset = 0) {
  const res = await fetch(`${API_BASE}/trades?limit=${limit}&offset=${offset}`);
  return res.json();
}
```

**Key technology choices for the UI:**

- **TanStack Table v8** for the trades table — headless, lightweight (~15KB), full control over styling. Supports sorting, filtering, pagination, and virtual scrolling via `@tanstack/react-virtual` for 10K+ rows. Simpler than QTableView — you own the rendering.
- **Lightweight Charts** (TradingView's OSS library) for financial charts — purpose-built for candlesticks, equity curves, and time series.
- **Shadcn/ui** or **Radix** for accessible, unstyled UI primitives — dialogs, dropdowns, tabs, tooltips.
- **TanStack Query** for API caching, refetching, and loading states — eliminates manual fetch boilerplate.
- **Zustand** or **Jotai** for lightweight state management.

The **privacy toggle system** ($ hide, % hide, % mode) is implemented via CSS class toggling — trivially simple:

```css
.privacy-dollar-hidden [data-dollar] { filter: blur(8px); }
.privacy-percent-hidden [data-percent] { filter: blur(8px); }
```

**Electron process management** — the main process spawns the Python backend as a child process on startup, waits for a health check, and gracefully shuts it down on exit:

```typescript
// ui/electron/main.ts — simplified
import { spawn } from 'child_process';
import { app } from 'electron';

function startBackend() {
  const cmd = app.isPackaged
    ? path.join(process.resourcesPath, 'backend', 'zorivest-api.exe')
    : 'python';
  const args = app.isPackaged
    ? ['--port', '8765']
    : ['-m', 'zorivest_api', '--port', '8765'];
  pythonProcess = spawn(cmd, args, { stdio: 'pipe', shell: false });
  return waitForHealth('http://localhost:8765/health', { timeout: 10000 });
}

app.on('before-quit', () => {
  fetch('http://localhost:8765/api/v1/shutdown', { method: 'POST' })
    .finally(() => pythonProcess?.kill());
});
```

For **per-UI settings**, use a namespaced key-value approach in the encrypted database: `(ui_type TEXT, setting_key TEXT, setting_value TEXT)` with composite primary key `(ui_type, setting_key)`. The Electron UI stores window geometry, column widths, theme, and font preferences via REST calls to a `/api/v1/settings` endpoint.

Other frameworks considered: **PySide6** has powerful QTableView but dated UI aesthetics and slower UI iteration. **Tauri** (Rust + webview) is lighter (~10MB) but younger ecosystem with fewer data-table components. **DearPyGUI** excels at real-time GPU visualization but lacks model/view architecture. Electron + React is the right choice for a modern-looking trading desktop with simple tables and rich charts.

---

## Structured logging with structlog across all layers

**structlog** is the right choice over loguru for a multi-layer application. Its native key-value structured logging, `contextvars`-based context propagation, and `ProcessorFormatter` integration with stdlib logging make it uniquely suited for tracing operations across GUI → Service → DB → API boundaries.

The critical configuration pattern: use **shared processors** for both structlog and stdlib logging, with **dual rendering** — colorized console for development, JSON for production files:

```python
import structlog, logging

shared_processors = [
    structlog.contextvars.merge_contextvars,  # Correlation IDs
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
]

structlog.configure(
    processors=shared_processors + [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

**Correlation IDs** tie together every log line from a single operation. At the start of any user action, API request, or MCP call, bind a UUID via `structlog.contextvars.bind_contextvars(correlation_id=str(uuid.uuid4()))`. All subsequent logs across the entire call chain — including third-party libraries like SQLAlchemy — automatically include this ID through the `ProcessorFormatter`. This is invaluable for debugging: grep one correlation ID and see the complete operation trace.

Use `RotatingFileHandler` with **50 MB max, 5 backups** for general logs and a separate error-only log file. For GUI apps, use stdlib's `QueueHandler` → `QueueListener` pattern to offload file writes to a dedicated thread, ensuring logging never blocks the UI.

---

## Dependency management with uv and release automation

**`uv`** (by Astral, written in Rust) is the definitive Python project manager in 2025–2026, replacing pip, virtualenv, pip-tools, and pyenv in a single tool that's **10–100x faster**. Its workspace support handles monorepos natively with a single `uv.lock` ensuring consistent dependency versions across all Python components. The TypeScript side uses **npm/pnpm workspaces** with a shared `package-lock.json` or `pnpm-lock.yaml`.

Key `uv` features for this project: `uv run --package myapp-api` executes in specific package context, `uv python install 3.12` manages Python versions, and `uvx` runs one-off tools in ephemeral environments. For security, `exclude-newer = "P7D"` in `pyproject.toml` delays adopting packages newer than 7 days. Use `pip-audit` for vulnerability scanning until native `uv audit` ships.

For **versioning**, use **SemVer** with **python-semantic-release** (v10.5+). Its `conventional-monorepo` commit parser filters commits by path, enabling independent versioning per package. Combined with **conventional commits** (`feat:`, `fix:`, `breaking:`) and GitHub Actions, every merge to main automatically bumps versions, generates changelogs, and creates releases. **Ruff** (also by Astral) replaces flake8, black, and isort as a single linter/formatter.

---

## AI agent workflow and context management

Effective AI-assisted development requires deliberate context architecture. Three complementary files serve different tools:

**`CLAUDE.md`** (repo root) is loaded automatically by Claude Code at session start. Keep it minimal — Anthropic's own testing shows manually curated files significantly outperform auto-generated ones. Include: project purpose, architecture overview, technology stack, coding conventions, common commands, and pointers to deeper docs. Don't duplicate what linters enforce. Tell Claude *how to find* information rather than dumping everything.

**`.cursor/rules/*.mdc`** files replace the deprecated `.cursorrules`. Each `.mdc` file targets specific file patterns via globs in frontmatter (`globs: packages/api/**/*.py`), auto-attaching relevant rules when editing matching files. Create focused files per concern: testing conventions, API development patterns, security requirements.

**`AGENTS.md`** is an open standard supported by Cursor, Zed, GitHub Copilot, and 60k+ open-source projects. Place at repo root for project-wide instructions and inside each package directory for package-specific guidance.

**Architectural Decision Records** live in `docs/decisions/` using the Nygard template (Status, Context, Decision, Consequences). Reference them from CLAUDE.md: *"Consult docs/decisions/ before making architectural changes. Create a new ADR for architectural decisions."* AI agents excel at generating draft ADRs — use them as starting points, then human-review.

For the **agentic IDE ↔ MCP backend workflow**, the AI agent in the IDE connects to the TypeScript MCP server via stdio transport. The developer types a natural language request; the agent's MCP client communicates with the TypeScript MCP server, which calls the Python REST API via `fetch()`. The tool handler returns results as MCP tool responses. Write tool descriptions carefully — they're the agent's primary decision-making input. Test tools with `vitest` and the MCP Inspector during development.

---

## Testing strategy and security hardening

Test each layer independently using the architecture's natural boundaries. **Domain layer** tests are pure unit tests — no mocking needed. **Repository** tests run against real SQLite (in-memory for speed). **Service layer** tests mock repositories to verify business logic in isolation. **API tests** use FastAPI's `TestClient` with overridden dependencies. **TypeScript MCP tests** use `vitest` with mocked `fetch()` to verify tool logic without a live backend. **UI tests** use React Testing Library for component tests and Playwright for E2E:

```typescript
// tests/typescript/mcp/trade-tools.test.ts
import { describe, it, expect, vi } from 'vitest';

describe('create_trade tool', () => {
  it('sends POST to /api/v1/trades', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ exec_id: 'T001', status: 'created' }))
    );
    // ... call tool handler, verify fetch args
  });
});
```

Use `pytest` with `pytest-asyncio` (auto mode), `pytest-mock`, `factory_boy` for test data factories, and `pytest-xdist` for parallel execution. Mark Python tests with `@pytest.mark.unit`, `@pytest.mark.integration`, and `@pytest.mark.e2e` for selective running.

For security beyond encryption: validate all inputs with Pydantic v2's strict mode and custom validators. Run `pip-audit` for dependency vulnerabilities and `bandit` for static code analysis in CI. Store the database encryption key derivation parameters (not the key) in the bootstrap file. For API keys stored in the encrypted database, they're protected at rest by SQLCipher and decrypted only in memory when needed. Use OS-level **keyring** integration for any secrets that must persist outside the encrypted database.

---

## Conclusion

The recommended stack crystallizes around a **hybrid TypeScript + Python architecture**. **`uv` workspaces** manage the Python monorepo (core/infra/api); **npm workspaces** manage the TypeScript side (ui/mcp-server). **Hexagonal architecture with manual DI** keeps the Python domain pure and testable. **`sqlcipher3` + Argon2id** handles encryption without complex dependencies. **FastAPI** serves the REST API on localhost, consumed by both the **Electron + React** UI and the **TypeScript MCP server**. **structlog** unifies observability across every Python layer.

The single most important architectural decision is the **shared REST API boundary** — every entry point (Electron UI, TypeScript MCP, future CLI) calls the same Python backend through the same service layer and Unit of Work. This eliminates code duplication, ensures consistent behavior, and makes testing straightforward. Start by building core + infrastructure packages with a solid service layer and repository pattern, then add the REST API, then the TypeScript entry points.

### Release & distribution strategy

| Channel | What ships | Tool | Audience |
|---------|-----------|------|----------|
| **Desktop app** | Electron + bundled PyInstaller backend | Electron Builder (`.exe`, `.dmg`, `.AppImage`) | End users |
| **PyPI** | `zorivest-core` (domain + services + infra) | `uv publish` | Python developers |
| **npm** | `@zorivest/mcp-server` (standalone MCP) | `npm publish` | AI agent users |
| **GitHub Releases** | Desktop installers + changelogs | GitHub Actions | All users |

The Cosmic Python book at cosmicpython.com remains the definitive implementation guide for the Python architectural patterns used in this project.