# Architecture — Zorivest

## Overview

Zorivest is a hybrid TypeScript + Python desktop application for active traders. It uses hexagonal architecture in Python with an Electron + React GUI communicating via REST on localhost.

## Agent Operating Model

Role-driven execution is the default operating model for implementation sessions.

- Workflow: `.agent/workflows/orchestrated-delivery.md`
- Required roles: `.agent/roles/orchestrator.md`, `.agent/roles/coder.md`, `.agent/roles/tester.md`, `.agent/roles/reviewer.md`
- Optional roles: `.agent/roles/researcher.md`, `.agent/roles/guardrail.md`
- Task handoffs: `.agent/context/handoffs/TEMPLATE.md`

All merge/release/deploy actions require explicit human approval.

## System Diagram

```
┌─────────────────────────────────────────────────┐
│  Electron + React GUI (TypeScript)              │
│  └─ TanStack Table, Lightweight Charts, Shadcn  │
├──────────────┬──────────────────────────────────┤
│  MCP Server  │  REST API (localhost:8000)       │
│  (TypeScript)│  ← httpx / fetch →               │
├──────────────┴──────────────────────────────────┤
│              FastAPI (Python)                    │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │  Domain  │  │ Services │  │Infrastructure │ │
│  │ Entities │→ │  Ports   │← │  Repos, UoW   │ │
│  │Calculator│  │ Protocols│  │  SQLCipher DB  │ │
│  └──────────┘  └──────────┘  └───────────────┘ │
└─────────────────────────────────────────────────┘
```

## Package Structure

| Package | Language | Path | Purpose |
|---------|----------|------|---------|
| **core** | Python | `packages/core/` | Domain entities, value objects, ports (Protocol interfaces), PositionSizeCalculator. Zero dependencies on infrastructure. |
| **infrastructure** | Python | `packages/infrastructure/` | SQLAlchemy ORM models, SQLCipher connection, repository implementations, Unit of Work. Depends on core. |
| **api** | Python | `packages/api/` | FastAPI REST endpoints. Routes, schemas, dependency injection. Depends on core + infrastructure. |
| **ui** | TypeScript | `ui/` | Electron + React. TanStack Table v8, Lightweight Charts, Shadcn/ui, Zustand state. |
| **mcp-server** | TypeScript | `mcp-server/` | MCP tool definitions for AI agent access. Calls REST API via fetch. |

## Hexagonal Architecture (Dependency Rule)

```
Domain (innermost) → Application (ports) → Infrastructure (outermost)
```

- **Domain** (`packages/core/domain/`): Pure Python. Entities, value objects, calculator. No imports from infrastructure or external libraries (except stdlib + dataclasses).
- **Application** (`packages/core/application/`): Ports defined as `typing.Protocol`. Contracts for `TradeRepository`, `ImageRepository`, `AbstractUnitOfWork`.
- **Infrastructure** (`packages/infrastructure/`): Implements ports. SQLAlchemy models, repository classes, database connection with SQLCipher encryption.

**Rule:** Core NEVER imports from infrastructure. Infrastructure implements core's Protocol interfaces.

## Database

- **Engine:** SQLite + SQLCipher (encrypted at rest)
- **Key derivation:** Argon2id from user passphrase
- **ORM:** SQLAlchemy 2.0 with declarative models
- **Migrations:** Alembic (planned)

## Communication

- **UI ↔ API:** REST over `localhost:8000`. UI uses `fetch`/`httpx`. No authentication needed (local-only).
- **MCP ↔ API:** Same REST endpoints. MCP server is a thin wrapper that translates MCP tool calls → REST requests.
- **API ↔ TWS:** `ibapi` library for Interactive Brokers TWS/Gateway connection.

## Logging

- **Library:** `structlog` with `contextvars` for correlation IDs
- **Format:** Dual output — human-readable console + JSON file
- **No `print()` or `console.log`** — always use structured loggers

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python + TypeScript hybrid | Separate strengths | Python for finance/data, TypeScript for modern UI |
| Hexagonal architecture | Testability | Domain logic tested without DB |
| SQLCipher | Privacy | All data encrypted at rest |
| REST (not IPC) | Simplicity | Standard HTTP, easy to test with TestClient |
| MCP in TypeScript | SDK maturity | Official MCP SDK is TypeScript-first |
| Electron + React | Desktop | Native feel, web tech flexibility |
