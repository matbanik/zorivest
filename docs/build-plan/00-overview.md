# Phase 0: Build Order Overview

> Part of [Zorivest Build Plan](../BUILD_PLAN.md)

---

## Dependency Rule

The architecture's dependency rule dictates the build order: **inner layers first, outer layers last**. Each layer is fully testable before the next one starts.

```
BUILD ORDER (left to right):

  ┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐
  │ Phase 1 │────▶│Phase 1A  │────▶│   Phase 2    │────▶│   Phase 3   │────▶│  Phase 4-6  │────▶│  Phase 7  │
  │ Domain  │     │ LOGGING  │     │ Infrastructure│     │  Services   │     │ Entry Points│     │  Release  │
  │ + Ports │     │          │     │  (DB, Repos) │     │ (Use Cases) │     │API/MCP(TS)/ │     │EB/PyPI/npm│
  └─────────┘     └──────────┘     └──────────────┘     └──────┬──────┘     │   GUI(TS)   │     └───────────┘
    0 deps          0 deps           depends on 1        depends on 1,2    └─────────────┘       packaging
    pure Python     stdlib only      sqlcipher3           orchestration      depends on 3         distribution
    100% unit       100% unit        integration tests    mock repos         REST → TS wrappers   installers
                                                                │
                                                                ▼
                                                        ┌──────────────┐
                                                        │   Phase 8    │
                                                        │ Market Data  │
                                                        │ Aggregation  │
                                                        └──────────────┘
                                                        depends on 2,3,4
                                                        9 API providers

  Phase 1A (Logging) has zero dependencies and can be built in parallel
  with Phase 1. All subsequent phases benefit from structured logging.

  Phases 4 (REST API) and 5 (TS MCP) are numbered in build order:
  REST first, then MCP wrappers, then GUI. All TypeScript packages
  communicate with Python via REST on localhost.

  Phase 8 (Market Data) depends on Phases 2–4 and provides market
  data tools consumed by Phase 5 (MCP) and Phase 6 (GUI).
```

## Phase Summary

| Phase | Name | Depends On | Key Deliverables |
|-------|------|-----------|------------------|
| 1 | [Domain Layer](01-domain-layer.md) | Nothing | Entities, calculator, ports, enums |
| **1A** | [**Logging**](01a-logging.md) | **Nothing** | **QueueHandler/Listener, JSONL, per-feature routing, redaction** |
| 2 | [Infrastructure](02-infrastructure.md) | Phase 1 | DB schema, repos, SQLCipher |
| 3 | [Service Layer](03-service-layer.md) | Phase 1, 2 | Use cases, service orchestration |
| 4 | [REST API](04-rest-api.md) | Phase 3 | FastAPI routes, e2e tests |
| 5 | [MCP Server](05-mcp-server.md) | Phase 4, 8 | TypeScript MCP tools (calls REST) |
| 6 | [GUI](06-gui.md) ([Shell](06a-gui-shell.md), [Trades](06b-gui-trades.md), [Planning](06c-gui-planning.md), [Accounts](06d-gui-accounts.md), [Scheduling](06e-gui-scheduling.md), [Settings](06f-gui-settings.md), [Tax](06g-gui-tax.md), [Calculator](06h-gui-calculator.md)) | Phase 4, 8 | Electron + React desktop app |
| 7 | [Distribution](07-distribution.md) | All | Installers, PyPI, npm |
| 8 | [Market Data](08-market-data.md) | Phase 2, 3, 4 | 9-provider aggregation, encryption, MCP tools |

## Golden Rules

1. **At every phase**, you should be able to run `pytest` and have all tests pass before moving to the next phase.
2. **The first lines of code you write** are `test_calculator.py` and `test_logging_config.py`. Phase 1 (Domain) and Phase 1A (Logging) start in parallel — both have zero dependencies.
3. **Inner layers never depend on outer layers.** Domain doesn't import infrastructure. Services don't import REST routes.

## Cross-References

| Reference Document | What It Contains |
|-------------------|------------------|
| [Domain Model Reference](domain-model-reference.md) | Complete entity map (Account, Trade, TradePlan, Tax, etc.) |
| [Logging Infrastructure](01a-logging.md) | QueueHandler/Listener, JSONL, per-feature routing, redaction |
| [Testing Strategy](testing-strategy.md) | MCP testing approaches, test infra, conftest |
| [Image Architecture](image-architecture.md) | Image storage, processing pipeline, thumbnails |
| [Dependency Manifest](dependency-manifest.md) | Install order, package versions |
| [Build Priority Matrix](build-priority-matrix.md) | P0–P3 sequenced build order (68 items) |
| [Input Index](input-index.md) | Every human, agent, and programmatic input with test strategies |
