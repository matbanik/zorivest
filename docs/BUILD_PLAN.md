# Zorivest — Build Plan & Test-Driven Development Guide

> **Hub file** — This document is the index for the complete build plan. Each phase and reference section lives in its own file under [`build-plan/`](build-plan/).

---

## Architecture Dependency Rule

The build order follows the **dependency rule**: inner layers first, outer layers last. Each layer is fully testable before the next one starts.

```
Domain → Infrastructure → Services → REST API → MCP Server → GUI → Distribution
  (1)        (2)            (3)         (4)         (5)        (6)       (7)
```

---

## Build Phases

| Phase | Name | File | Depends On | Key Deliverables |
|-------|------|------|------------|-----------------|
| 0 | [Build Order Overview](build-plan/00-overview.md) | `00-overview.md` | — | Dependency diagram, golden rules |
| 1 | [Domain Layer](build-plan/01-domain-layer.md) | `01-domain-layer.md` | Nothing | Entities, calculator, ports, enums |
| 2 | [Infrastructure](build-plan/02-infrastructure.md) | `02-infrastructure.md` | Phase 1 | SQLCipher DB, SQLAlchemy repos, UoW |
| 3 | [Service Layer](build-plan/03-service-layer.md) | `03-service-layer.md` | Phases 1–2 | Trade/Image/Account services |
| 4 | [REST API](build-plan/04-rest-api.md) | `04-rest-api.md` | Phase 3 | FastAPI routes, TestClient tests |
| 5 | [MCP Server](build-plan/05-mcp-server.md) | `05-mcp-server.md` | Phase 4 | TypeScript MCP tools, Vitest |
| 6 | [GUI](build-plan/06-gui.md) | `06-gui.md` | Phase 4 | Electron + React desktop app |
| 7 | [Distribution](build-plan/07-distribution.md) | `07-distribution.md` | All | Electron Builder, PyPI, npm |
| 8 | [Market Data](build-plan/08-market-data.md) | `08-market-data.md` | Phases 2–4 | 9 market data providers, API key encryption, MCP tools |

---

## Reference Documents

| Document | File | Purpose |
|----------|------|---------|
| [Domain Model Reference](build-plan/domain-model-reference.md) | `domain-model-reference.md` | Complete entity map, relationships, enum definitions |
| [Testing Strategy](build-plan/testing-strategy.md) | `testing-strategy.md` | MCP testing approaches, `conftest.py`, test configuration |
| [Image Architecture](build-plan/image-architecture.md) | `image-architecture.md` | BLOB vs filesystem, processing pipeline, validation |
| [Dependency Manifest](build-plan/dependency-manifest.md) | `dependency-manifest.md` | Install order by phase, version requirements |
| [Build Priority Matrix](build-plan/build-priority-matrix.md) | `build-priority-matrix.md` | P0–P3 tables with P1.5 market data, complete 68-item build order |
| [Market Data API Reference](../_inspiration/_market_tools_api-architecture.md) | `_inspiration/` | Source patterns for 9-provider connectivity |

---

## Phase Status Tracker

| Phase | Status | Last Updated |
|-------|--------|--------------|
| 1 — Domain Layer | 🟡 In Progress | 2026-02-14 |
| 2 — Infrastructure | ⚪ Not Started | — |
| 3 — Service Layer | ⚪ Not Started | — |
| 4 — REST API | ⚪ Not Started | — |
| 5 — MCP Server | ⚪ Not Started | — |
| 6 — GUI | ⚪ Not Started | — |
| 7 — Distribution | ⚪ Not Started | — |
| 8 — Market Data | ⚪ Not Started | — |

---

## Golden Rules

1. **At every phase**, you should be able to run `pytest` and have all tests pass before moving to the next phase.
2. **Inner layers know nothing about outer layers.** Domain never imports from infrastructure.
3. **Write tests FIRST** — the test file defines the interface before the implementation exists.
4. **Every entity gets a test.** No "it's just a dataclass" exceptions.
5. **Commit after each green test run.** Small, atomic commits.

---

## Quick Start

**The first line of code you write is `test_calculator.py`. The first line of production code is `calculator.py`. Everything flows from there.**

Start here → [Phase 1: Domain Layer](build-plan/01-domain-layer.md)

---

## Validation

Run the build plan validator to check cross-references, numbering, and completeness:

```bash
python tools/validate_build_plan.py
```
