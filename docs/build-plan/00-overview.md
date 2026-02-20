# Phase 0: Build Order Overview

> Part of [Zorivest Build Plan](../BUILD_PLAN.md)

---

## Dependency Rule

The architecture's dependency rule dictates the build order: **inner layers first, outer layers last**. Each layer is fully testable before the next one starts.

```
BUILD ORDER (left to right):

  ┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐
  │ Phase 1 │────▶│Phase 1A  │────▶│   Phase 2    │────▶│  Phase 2A    │────▶│   Phase 3   │────▶│  Phase 4-6  │────▶│  Phase 7  │
  │ Domain  │     │ LOGGING  │     │ Infrastructure│     │ Backup/Restore│     │  Services   │     │ Entry Points│     │  Release  │
  │ + Ports │     │          │     │  (DB, Repos) │     │  & Defaults  │     │ (Use Cases) │     │API/MCP(TS)/ │     │EB/PyPI/npm│
  └─────────┘     └──────────┘     └──────────────┘     └──────────────┘     └──────┬──────┘     │   GUI(TS)   │     └───────────┘
    0 deps          0 deps           depends on 1        depends on 2        depends on 1,2,2A  └─────────────┘       packaging
    pure Python     stdlib only      sqlcipher3           pyzipper             orchestration      depends on 3         distribution
    100% unit       100% unit        integration tests    integration tests    mock repos         REST → TS wrappers   installers
                                                                                    │
                                                                                    ▼
                                                                            ┌──────────────┐
                                                                            │   Phase 8    │
                                                                            │ Market Data  │
                                                                            │ Aggregation  │
                                                                            └──────┬───────┘
                                                                            depends on 2,3,4
                                                                            9 API providers
                                                                                   │
                                                                                   ▼
                                                                            ┌──────────────┐
                                                                            │   Phase 9    │
                                                                            │ Scheduling & │
                                                                            │  Pipelines   │
                                                                            └──────────────┘
                                                                            depends on 2–5,8
                                                                            policy engine,
                                                                            5 pipeline stages,
                                                                            6 MCP tools

  Phase 1A (Logging) has zero dependencies and can be built in parallel
  with Phase 1. All subsequent phases benefit from structured logging.

  Phase 2A (Backup/Restore & Defaults) depends on Phase 2 and must
  complete before Phase 3, which uses SettingsResolver and BackupService.

  Phases 4 (REST API) and 5 (TS MCP) are numbered in build order:
  REST first, then MCP wrappers, then GUI. All TypeScript packages
  communicate with Python via REST on localhost.

  Phase 8 (Market Data) depends on Phases 2–4 and provides market
  data tools consumed by Phase 5 (MCP) and Phase 6 (GUI).

  Phase 9 (Scheduling & Pipelines) depends on Phases 2–5,8 and provides
  the pipeline engine consumed by Phase 6e (GUI Scheduling).
```

## Phase Summary

| Phase | Name | Depends On | Key Deliverables |
|-------|------|-----------|------------------|
| 1 | [Domain Layer](01-domain-layer.md) | Nothing | Entities, calculator, ports, enums |
| **1A** | [**Logging**](01a-logging.md) | **Nothing** | **QueueHandler/Listener, JSONL, per-feature routing, redaction** |
| 2 | [Infrastructure](02-infrastructure.md) | Phase 1 | DB schema, repos, SQLCipher |
| **2A** | [**Backup/Restore & Defaults**](02a-backup-restore.md) | **Phase 2** | **Encrypted backup, settings resolver, config export** |
| 3 | [Service Layer](03-service-layer.md) | Phase 1, 2, 2A | Use cases, service orchestration |
| 4 | [REST API](04-rest-api.md) | Phase 3 | FastAPI routes, e2e tests |
| 5 | [MCP Server](05-mcp-server.md) | Phase 4, 8 | TypeScript MCP tools (calls REST) |
| 6 | [GUI](06-gui.md) ([Shell](06a-gui-shell.md), [Trades](06b-gui-trades.md), [Planning](06c-gui-planning.md), [Accounts](06d-gui-accounts.md), [Scheduling](06e-gui-scheduling.md), [Settings](06f-gui-settings.md), [Tax](06g-gui-tax.md), [Calculator](06h-gui-calculator.md)) | Phase 4, 8 | Electron + React desktop app |
| 7 | [Distribution](07-distribution.md) | All | Versioning architecture, CI/CD pipelines (ci/release/publish/test-release), code signing, auto-update, OIDC publishing, rollback procedures |
| 8 | [Market Data](08-market-data.md) | Phase 2, 3, 4 | 9-provider aggregation, encryption, MCP tools |
| 9 | [Scheduling & Pipelines](09-scheduling.md) | Phase 2, 3, 4, 5, 8 | Policy engine, pipeline runner, APScheduler, 5 stages, 6 MCP tools |

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
| [Backup/Restore Architecture](../_backup-restore-architecture.md) | Two-manager backup design, GFS rotation, restore flow |
| [Dependency Manifest](dependency-manifest.md) | Install order, package versions |
| [Build Priority Matrix](build-priority-matrix.md) | P0–P3 sequenced build order (106 items) |
| [Input Index](input-index.md) | Every human, agent, and programmatic input with test strategies |
| [Security Architecture](../_security-architecture.md) | Encryption, sensitive data detection, MCP circuit breaker (reference) |
| [Scheduling Integration Roadmap](../../_inspiration/scheduling_research/scheduling-integration-roadmap.md) | Research synthesis, resolved decisions, library stack |
