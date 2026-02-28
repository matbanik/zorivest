# MEU Registry — Phase 1 + Phase 1A

> Manageable Execution Units for the Zorivest build plan.
> Each MEU is one session's worth of TDD work for Opus, followed by validation from Codex.

---

## Phase 1: Domain Layer (P0)

| MEU | Slug | Build Plan Ref | Description | Status |
|-----|------|---------------|-------------|--------|
| MEU-1 | `calculator` | [01 §1.3](../docs/build-plan/01-domain-layer.md) | PositionSizeCalculator + PositionSizeResult | ⬜ pending |
| MEU-2 | `enums` | [01 §1.2](../docs/build-plan/01-domain-layer.md) | All StrEnum definitions (15 enums) | ⬜ pending |
| MEU-3 | `entities` | [01 §1.4](../docs/build-plan/01-domain-layer.md) | Trade, Account, BalanceSnapshot, ImageAttachment | ⬜ pending |
| MEU-4 | `value-objects` | [01 §1.2](../docs/build-plan/01-domain-layer.md) | Money, PositionSize, Ticker, Conviction, ImageData | ⬜ pending |
| MEU-5 | `ports` | [01 §1.5](../docs/build-plan/01-domain-layer.md) | Protocol interfaces (TradeRepo, ImageRepo, UoW, BrokerPort) | ⬜ pending |
| MEU-6 | `commands-dtos` | [01 §1.2](../docs/build-plan/01-domain-layer.md) | Commands (CreateTrade, AttachImage) + DTOs | ⬜ pending |
| MEU-7 | `events` | [01 §1.2](../docs/build-plan/01-domain-layer.md) | Domain events (TradeCreated, BalanceUpdated, etc.) | ⬜ pending |
| MEU-8 | `analytics` | [01 §1.2](../docs/build-plan/01-domain-layer.md) | Pure analytics functions (expectancy, drawdown, SQN, MFE/MAE, PFOF, cost, strategy) | ⬜ pending |

## Phase 1A: Logging Infrastructure (P0, Parallel)

| MEU | Slug | Build Plan Ref | Description | Status |
|-----|------|---------------|-------------|--------|
| MEU-1A | `logging-manager` | [01a §1–3](../docs/build-plan/01a-logging.md) | LoggingManager, QueueHandler/Listener, JSONL format | ⬜ pending |
| MEU-2A | `logging-filters` | [01a §4](../docs/build-plan/01a-logging.md) | FeatureFilter (per-file routing) + JsonFormatter | ⬜ pending |
| MEU-3A | `logging-redaction` | [01a §4](../docs/build-plan/01a-logging.md) | RedactionFilter (API key masking, PII redaction) | ⬜ pending |

---

## Status Legend

| Icon | Meaning |
|------|---------|
| ⬜ | pending — not started |
| 🔵 | in_progress — Opus implementing |
| 🟡 | ready_for_review — awaiting Codex validation |
| 🔴 | changes_required — Codex found issues |
| ✅ | approved — both agents satisfied |
| 🚫 | blocked — escalated to human |

## Execution Order

### Recommended Start (Pilot)

```
MEU-1 (calculator) ← PILOT — validates entire dual-agent workflow
```

### After Pilot Validated

```
Track A (Phase 1):        Track B (Phase 1A):
  MEU-2 (enums)             MEU-1A (logging-manager)
  MEU-3 (entities)          MEU-2A (logging-filters)
  MEU-4 (value-objects)     MEU-3A (logging-redaction)
  MEU-5 (ports)
  MEU-6 (commands-dtos)
  MEU-7 (events)
  MEU-8 (analytics)
```

Track A and Track B can run in parallel — they have zero dependencies on each other.

## Phase-Exit Criterion

Phase 1 + 1A are complete when ALL MEUs in both tracks show ✅ status, and:
- `pytest -x --tb=short -m "unit"` passes (all tests green)
- `pyright packages/core/src/` passes (zero type errors)
- `ruff check packages/core/src/` passes (zero warnings)
- No banned patterns remain (`rg "TODO|FIXME|NotImplementedError" packages/`)
