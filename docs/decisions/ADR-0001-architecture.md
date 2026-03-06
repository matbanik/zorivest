# ADR-0001: Architecture — Clean Architecture with Layered Monorepo

> Status: accepted
> Date: 2026-02-28
> Deciders: Mat (human) + Opus 4.6 (Agent B)

## Context

Zorivest is a personal trading journal and portfolio analysis tool. It needs to safely manage sensitive financial data (SQLCipher encryption), serve a local REST API, expose tools to AI agents via MCP, and provide a desktop GUI. The system must be modular enough for AI agents to implement incrementally via MEU-scoped sessions.

## Decision

Adopt a Clean Architecture approach with a layered Python monorepo:

- **Domain layer** (`packages/core`) — pure Python entities, value objects, ports (abstract interfaces), and the position calculator. No external dependencies.
- **Infrastructure layer** (`packages/infrastructure`) — SQLAlchemy + SQLCipher repositories, Unit of Work, file I/O. Implements domain ports.
- **API layer** (`packages/api`) — FastAPI REST endpoints on localhost. Depends on infrastructure via dependency injection.
- **MCP layer** (`mcp-server/`) — TypeScript MCP server exposing AI tool interface.
- **UI layer** (`ui/`) — Electron + React desktop GUI.

Dependency rule: Domain → Application → Infrastructure. Never import infra from core.

## Consequences

### Positive
- AI agents can implement one layer at a time without cross-boundary coupling
- Domain logic is testable in isolation (no database, no framework)
- SQLCipher encryption is isolated in the infrastructure layer

### Negative
- More boilerplate (ports, adapters, dependency injection)
- Requires discipline to maintain layer boundaries

### Risks
- Agents may inadvertently violate the dependency rule when expedient

## References

- Build plan section: `docs/build-plan/01-domain-layer.md`
- Related ADRs: none (seed ADR)
- Handoff: initial architecture established during project bootstrap
