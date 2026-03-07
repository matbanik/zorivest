# Project: commands-events-analytics (v3)

Application-layer commands, domain events, and pure analytics functions for the Zorivest trading journal.

**Project slug:** `commands-events-analytics`
**MEUs:** MEU-6 → MEU-7 → MEU-8
**Build plan:** [01-domain-layer.md](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) §1.1–§1.2
**Date:** 2026-03-07

---

## User Review Required

> [!IMPORTANT]
> **MEU-8 scope decision — strategy.py deferred.** The `breakdown_by_strategy()` function groups trades by `strategy_name` sourced from `TradeReport.tags` ([domain-model-reference.md line 58](file:///p:/zorivest/docs/build-plan/domain-model-reference.md), [04e-api-analytics.md line 44](file:///p:/zorivest/docs/build-plan/04e-api-analytics.md), [05c-mcp-trade-analytics.md lines 425/430](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md)). Since `TradeReport` is a P1 entity (not yet built), `strategy.py` **cannot be implemented** in MEU-8 without inventing behavior. It is deferred until TradeReport is available. MEU-8 implements: result types, `expectancy.py`, `sqn.py`.

> [!IMPORTANT]
> **Analytics result types align to Phase 3 canonical contract.** The result dataclasses in this plan match [03-service-layer.md lines 89–145](file:///p:/zorivest/docs/build-plan/03-service-layer.md) exactly — field names, types (`Decimal` throughout), and field order. No invention of alternate shapes. Out-of-scope result types (DrawdownResult, ExcursionResult, QualityResult, PFOFResult, CostResult) are included in `results.py` because they are pure type definitions with no implementation dependency.

## Standing Project Rules

Per human decision (2026-03-07, from domain-entities-ports v3 plan):

1. **Full contract always.** Entities/commands implement the complete field set from canonical docs. No narrowing, no P0 subsets, no deferrals.
2. **Validators always.** Dataclasses include validation sourced from canonical docs. Document each rule in the FIC with its source.

## Design Rules (from prior reflection)

Per `2026-03-07-domain-entities-ports-reflection.md`:

- **RULE-1:** Record per-MEU `tests_passing` count, not final project total.
- **RULE-2:** Mark reflection/metrics as "(provisional)" when created before Codex validation.
- **RULE-3:** Use `write_to_file` with `Overwrite=true` for small structured files to avoid CRLF/LF corruption.

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 0 | Gate: confirm all deps ✅ | orchestrator | MEU-1–5 approved in registry | `rg "✅ approved" .agent/context/meu-registry.md` — 5 matches | ⬜ |
| 1 | MEU-6 FIC + Red tests | coder | `tests/unit/test_commands_dtos.py` | `uv run pytest tests/unit/test_commands_dtos.py -x --tb=short -m "unit" -v` — all FAIL | ⬜ |
| 2 | MEU-6 Green implementation | coder | `commands.py`, `queries.py`, `dtos.py` | `uv run pytest tests/unit/test_commands_dtos.py -x --tb=short -m "unit" -v` — all PASS | ⬜ |
| 3 | MEU-6 quality gate | tester | Zero errors | `uv run pyright packages/core/src/zorivest_core/application/` + `uv run ruff check packages/core/src/zorivest_core/application/` + `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/application/ \|\| Write-Output "Anti-placeholder: clean"` | ⬜ |
| 4 | MEU-6 handoff | coder | `004-2026-03-07-commands-dtos-bp01s1.2.md` | `rg -c "^##" .agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md` — ≥7 sections | ⬜ |
| 5 | MEU-6 validation | reviewer | Codex appends to handoff 004 | `rg "approved\|changes_required" .agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md` — shows `approved` | ⬜ |
| 6 | MEU-7 FIC + Red tests | coder | `tests/unit/test_events.py` | `uv run pytest tests/unit/test_events.py -x --tb=short -m "unit" -v` — all FAIL | ⬜ |
| 7 | MEU-7 Green implementation | coder | `events.py` | `uv run pytest tests/unit/test_events.py -x --tb=short -m "unit" -v` — all PASS | ⬜ |
| 8 | MEU-7 quality gate | tester | Zero errors | `uv run pyright packages/core/src/zorivest_core/domain/events.py` + `uv run ruff check packages/core/src/zorivest_core/domain/events.py` + `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/domain/events.py \|\| Write-Output "Anti-placeholder: clean"` | ⬜ |
| 9 | MEU-7 handoff | coder | `005-2026-03-07-events-bp01s1.2.md` | `rg -c "^##" .agent/context/handoffs/005-2026-03-07-events-bp01s1.2.md` — ≥7 sections | ⬜ |
| 10 | MEU-7 validation | reviewer | Codex appends to handoff 005 | `rg "approved\|changes_required" .agent/context/handoffs/005-2026-03-07-events-bp01s1.2.md` — shows `approved` | ⬜ |
| 11 | MEU-8 FIC + Red tests | coder | `tests/unit/test_analytics.py` | `uv run pytest tests/unit/test_analytics.py -x --tb=short -m "unit" -v` — all FAIL | ⬜ |
| 12 | MEU-8 Green implementation | coder | `analytics/` module files | `uv run pytest tests/unit/test_analytics.py -x --tb=short -m "unit" -v` — all PASS | ⬜ |
| 13 | MEU-8 quality gate | tester | Zero errors | `uv run pyright packages/core/src/zorivest_core/domain/analytics/` + `uv run ruff check packages/core/src/zorivest_core/domain/analytics/` + `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/domain/analytics/ \|\| Write-Output "Anti-placeholder: clean"` | ⬜ |
| 14 | MEU-8 handoff | coder | `006-2026-03-07-analytics-bp01s1.2.md` | `rg -c "^##" .agent/context/handoffs/006-2026-03-07-analytics-bp01s1.2.md` — ≥7 sections | ⬜ |
| 15 | MEU-8 validation | reviewer | Codex appends to handoff 006 | `rg "approved\|changes_required" .agent/context/handoffs/006-2026-03-07-analytics-bp01s1.2.md` — shows `approved` | ⬜ |
| 16 | Post-project: reflection + metrics + session state | tester | Updated artifacts | `Test-Path docs/execution/reflections/2026-03-07-commands-events-analytics-reflection.md` + `rg "commands-events-analytics" docs/execution/metrics.md` + `pomera_notes search --search_term "Memory/Session/Zorivest-commands-events-analytics*"` | ⬜ |

**Role progression per MEU:** orchestrator (gate) → coder (FIC + Red + Green + handoff) → tester (quality gate) → reviewer/Codex (validation appended to handoff)

---

## Proposed Changes

### MEU-6: Commands & DTOs (bp01 §1.2)

#### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Command names (CreateTrade, AttachImage, CreateAccount, UpdateBalance) | Spec | [01-domain-layer.md §1.1 line 27](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) | ✅ | Explicit in build plan |
| Query names (GetTrade, ListTrades, GetImage) | Spec | [01-domain-layer.md §1.1 line 28](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) | ✅ | Explicit in build plan |
| DTO names and purpose | Spec | [01-domain-layer.md §1.1 line 28](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) | ✅ | "dtos.py — Data transfer objects" |
| Command/DTO field sets | Local Canon | [domain-model-reference.md lines 16–111](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Derived from entity definitions |
| Frozen dataclass convention | Spec | [01-domain-layer.md §Goal](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) + [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | ✅ | "Commands/DTOs use dataclasses" + "Frozen dataclasses" |
| Pydantic deferred to Phase 4 | Spec | [01-domain-layer.md §Goal](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) | ✅ | — |
| Query GetAccount/ListAccounts/ListImages | Local Canon | [ports.py `get_for_owner`](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py) | ✅ | Derived from Account entity + port interface |
| PK-must-not-be-blank validation | Local Canon | [domain-model-ref line 38](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | exec_id is PK; empty PKs structurally invalid |
| Quantity-must-be-positive validation | Local Canon | [domain-model-ref line 42](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Quantity represents shares traded |
| DTO binary exclusion | Local Canon | [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | ✅ | DTOs are wire-format; bytes not serializable |

No gaps require web research or human decision.

#### FIC — Feature Intent Contract

P0 commands/queries/DTOs derived from [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) + [01-domain-layer.md §1.1](file:///p:/zorivest/docs/build-plan/01-domain-layer.md). Build plan §Goal: "Commands/DTOs use `dataclasses` with manual validation in Phase 1; Pydantic validation is added in Phase 4."

**Commands** (`application/commands.py`):

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `CreateTrade` frozen dataclass: `exec_id` (str), `time` (datetime), `instrument` (str), `action` (TradeAction), `quantity` (float), `price` (float), `account_id` (str), `commission` (float, default 0.0), `realized_pnl` (float, default 0.0) | Spec: [01-domain-layer.md §1.1 line 27](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) "CreateTrade" + [domain-model-ref lines 37–48](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-2 | `CreateTrade` rejects empty `exec_id` (ValueError) | Local Canon: `exec_id` is Trade PK per [domain-model-ref line 38](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-3 | `CreateTrade` rejects non-positive `quantity` (ValueError) | Local Canon: Trade.quantity per [domain-model-ref line 42](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-4 | `AttachImage` frozen dataclass: `owner_type` (ImageOwnerType), `owner_id` (str), `data` (bytes), `mime_type` (str), `caption` (str, default ""), `width` (int), `height` (int) | Spec: [01-domain-layer.md §1.1 line 27](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) "AttachImage" + [domain-model-ref lines 100–111](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-5 | `AttachImage` enforces `mime_type == "image/webp"` (ValueError) | Local Canon: [domain-model-ref line 107](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) "All images standardized to WebP" |
| AC-6 | `CreateAccount` frozen dataclass: `account_id` (str), `name` (str), `account_type` (AccountType), `institution` (str, default ""), `currency` (str, default "USD"), `is_tax_advantaged` (bool, default False), `notes` (str, default ""), `balance_source` (BalanceSource, default MANUAL) | Local Canon: [domain-model-ref lines 16–27](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-7 | `CreateAccount` rejects empty `account_id` or `name` (ValueError) | Local Canon: `account_id` is Account PK per [domain-model-ref line 17](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-8 | `UpdateBalance` frozen dataclass: `account_id` (str), `balance` (Decimal), `snapshot_datetime` (datetime, default factory: now) | Local Canon: [domain-model-ref lines 29–33](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-9 | All commands are frozen dataclasses | Spec: [01-domain-layer.md §Goal](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) + Local Canon: [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |

**Queries** (`application/queries.py`):

| AC | Description | Source |
|----|-------------|--------|
| AC-10 | `GetTrade` frozen dataclass: `exec_id` (str) | Spec: [01-domain-layer.md §1.1 line 28](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) |
| AC-11 | `ListTrades` frozen dataclass: `limit` (int, default 100), `offset` (int, default 0), `account_id` (str \| None, default None) | Spec: [01-domain-layer.md §1.1 line 28](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) + Local Canon: [ports.py line 17](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py) |
| AC-12 | `GetAccount` frozen dataclass: `account_id` (str) | Local Canon: [domain-model-ref line 17](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-13 | `ListAccounts` frozen dataclass (no fields — list all) | Local Canon: Account entity pattern |
| AC-14 | `GetImage` frozen dataclass: `image_id` (int) | Spec: [01-domain-layer.md §1.1 line 28](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) |
| AC-15 | `ListImages` frozen dataclass: `owner_type` (ImageOwnerType), `owner_id` (str) | Local Canon: [ports.py lines 29–31](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py) |

**DTOs** (`application/dtos.py`):

| AC | Description | Source |
|----|-------------|--------|
| AC-16 | `TradeDTO` frozen dataclass: mirrors Trade fields; `images` list → `image_count` (int) | Local Canon: [domain-model-ref lines 37–48](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) + [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-17 | `AccountDTO` frozen dataclass: mirrors Account fields; `balance_snapshots` → `latest_balance` (Decimal \| None) | Local Canon: [domain-model-ref lines 16–27](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-18 | `BalanceSnapshotDTO` frozen dataclass: `id`, `account_id`, `datetime`, `balance` | Local Canon: [domain-model-ref lines 29–33](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-19 | `ImageAttachmentDTO` frozen dataclass: `id`, `owner_type`, `owner_id`, `mime_type`, `caption`, `width`, `height`, `file_size`, `created_at` — NO `data`/`thumbnail` | Local Canon: [domain-model-ref lines 100–111](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) + [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-20 | Module imports: `commands.py` from `enums`, `datetime`, `decimal`; `dtos.py` from `enums`, `datetime`, `decimal`; `queries.py` from `enums` | Local Canon: import surface pattern from MEU-1–5 |

#### [NEW] [commands.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/commands.py)

- `CreateTrade`, `AttachImage`, `CreateAccount`, `UpdateBalance` — frozen dataclasses with `__post_init__` validation

#### [NEW] [queries.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/queries.py)

- `GetTrade`, `ListTrades`, `GetAccount`, `ListAccounts`, `GetImage`, `ListImages`

#### [NEW] [dtos.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/dtos.py)

- `TradeDTO`, `AccountDTO`, `BalanceSnapshotDTO`, `ImageAttachmentDTO`

#### [NEW] [test_commands_dtos.py](file:///p:/zorivest/tests/unit/test_commands_dtos.py)

- ~25 test functions covering AC-1 through AC-20

---

### MEU-7: Domain Events (bp01 §1.2)

#### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Event names (TradeCreated, BalanceUpdated, ImageAttached, PlanCreated) | Spec | [01-domain-layer.md §1.1 line 31](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) | ✅ | Explicit in build plan |
| Event payload fields | Local Canon | [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Derived from entity definitions |
| Frozen dataclass convention | Spec | [01-domain-layer.md §Goal](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) + [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | ✅ | — |
| Base event with UUID + timestamp | Local Canon | [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | ✅ | Events are temporal records needing identity |
| PlanCreated references TradePlan fields | Local Canon | [domain-model-ref lines 78–96](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | — |

No gaps require web research or human decision.

#### FIC — Feature Intent Contract

Events sourced from [01-domain-layer.md §1.1 line 31](file:///p:/zorivest/docs/build-plan/01-domain-layer.md): `events.py # TradeCreated, BalanceUpdated, ImageAttached, PlanCreated`.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | Base `DomainEvent` frozen dataclass: `event_id` (str, UUID default), `occurred_at` (datetime, default factory: now) | Local Canon: [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) + [domain-model-ref "ANALYTICS & ENRICHMENT" section](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-2 | `TradeCreated(DomainEvent)`: `exec_id` (str), `instrument` (str), `action` (TradeAction), `quantity` (float), `price` (float), `account_id` (str) | Spec: [01-domain-layer.md §1.1 line 31](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) + Local Canon: [domain-model-ref lines 37–48](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-3 | `BalanceUpdated(DomainEvent)`: `account_id` (str), `new_balance` (Decimal), `snapshot_id` (int) | Spec: [01-domain-layer.md §1.1 line 31](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) + Local Canon: [domain-model-ref lines 29–33](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-4 | `ImageAttached(DomainEvent)`: `owner_type` (ImageOwnerType), `owner_id` (str), `image_id` (int) | Spec: [01-domain-layer.md §1.1 line 31](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) |
| AC-5 | `PlanCreated(DomainEvent)`: `plan_id` (int), `ticker` (str), `direction` (TradeAction), `conviction` (ConvictionLevel) | Spec: [01-domain-layer.md §1.1 line 31](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) + Local Canon: [domain-model-ref lines 78–96](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-6 | All events are frozen dataclasses | Spec: [01-domain-layer.md §Goal](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) + [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-7 | Module imports only from `__future__`, `dataclasses`, `datetime`, `decimal`, `uuid`, `zorivest_core.domain.enums` | Local Canon: import surface pattern from MEU-1–5 |

#### [NEW] [events.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/events.py)

- `DomainEvent` (base), `TradeCreated`, `BalanceUpdated`, `ImageAttached`, `PlanCreated` — all frozen

#### [NEW] [test_events.py](file:///p:/zorivest/tests/unit/test_events.py)

- ~10 test functions covering AC-1 through AC-7

---

### MEU-8: Analytics — Result Types + Expectancy + SQN (bp01 §1.2)

#### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Analytics module location (`domain/analytics/`) | Spec | [01-domain-layer.md §1.1 lines 38–48](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) | ✅ | Explicit in build plan |
| Result type field names and types (all 8 types) | Spec | [03-service-layer.md lines 89–145](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | ✅ | Canonical contract |
| `calculate_expectancy` function signature | Spec | [03-service-layer.md line 45](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | ✅ | — |
| `calculate_sqn` function signature | Spec | [03-service-layer.md line 47](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | ✅ | — |
| Expectancy formula | Research-backed | Van Tharp, *Trade Your Way to Financial Freedom*, 3rd ed., ch. 7 (https://www.vantharp.com/trade-your-way-to-financial-freedom) | ✅ | `(win_rate × avg_win) - (loss_rate × avg_loss)` |
| Profit factor | Research-backed | Van Tharp, *Trade Your Way to Financial Freedom*, 3rd ed., ch. 7 (https://www.vantharp.com/trade-your-way-to-financial-freedom) | ✅ | `gross_wins / abs(gross_losses)` |
| Kelly fraction | Research-backed | Kelly, J.L. Jr., *Bell System Technical Journal* 35(4):917–926, 1956 (https://doi.org/10.1002/j.1538-7305.1956.tb03809.x) | ✅ | `win_rate - (loss_rate / payoff_ratio)` |
| SQN formula | Research-backed | Van Tharp, ch. 15 (https://www.vantharp.com/trade-your-way-to-financial-freedom) | ✅ | `(mean_R / std_R) × √n` |
| SQN grade scale | Research-backed | Van Tharp (https://www.vantharp.com/sqn) | ✅ | 7-tier: Poor → Unicorn |
| Empty-trades edge case | Local Canon | [03-service-layer.md line 577](file:///p:/zorivest/docs/build-plan/03-service-layer.md) | ✅ | `test_empty_trades_returns_zero` |
| R-multiples from `realized_pnl` | Local Canon | [domain-model-ref line 46](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Trade.realized_pnl |
| strategy.py deferred | Local Canon | [domain-model-ref line 58](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Groups by TradeReport.tags; TradeReport is P1 |

No gaps remain. All Research-backed items have URLs above.

#### FIC — Feature Intent Contract

Analytics module sourced from [01-domain-layer.md §1.1 lines 38–48](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) and [03-service-layer.md lines 83–145](file:///p:/zorivest/docs/build-plan/03-service-layer.md) (canonical result type definitions).

**Result types** (`domain/analytics/results.py`) — field names and types match [03-service-layer.md lines 89–145](file:///p:/zorivest/docs/build-plan/03-service-layer.md) exactly:

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `ExpectancyResult` frozen: `expectancy` (Decimal), `win_rate` (Decimal), `avg_win` (Decimal), `avg_loss` (Decimal), `profit_factor` (Decimal), `kelly_fraction` (Decimal), `trade_count` (int) | Spec: [03-service-layer.md lines 89–96](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-2 | `SQNResult` frozen: `sqn` (Decimal), `grade` (str), `trade_count` (int), `mean_r` (Decimal), `std_r` (Decimal) | Spec: [03-service-layer.md lines 106–111](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-3 | `StrategyResult` frozen: `strategy_name` (str), `total_pnl` (Decimal), `trade_count` (int), `win_rate` (Decimal) | Spec: [03-service-layer.md lines 141–145](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-4 | `DrawdownResult` frozen: `probability_table` (dict), `max_drawdown_median` (Decimal), `recommended_risk_pct` (Decimal), `simulations_run` (int) | Spec: [03-service-layer.md lines 99–103](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-5 | `ExcursionResult` frozen: `mfe` (Decimal), `mae` (Decimal), `bso` (Decimal), `holding_bars` (int) | Spec: [03-service-layer.md lines 114–118](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-6 | `QualityResult` frozen: `score` (Decimal), `grade` (str), `slippage_estimate` (Decimal) | Spec: [03-service-layer.md lines 121–124](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-7 | `PFOFResult` frozen: `estimated_cost` (Decimal), `routing_type` (str), `confidence` (str), `period` (str) | Spec: [03-service-layer.md lines 127–131](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-8 | `CostResult` frozen: `total_hidden_cost` (Decimal), `pfof_component` (Decimal), `fee_component` (Decimal), `period` (str) | Spec: [03-service-layer.md lines 134–138](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-9 | All result types are frozen dataclasses | Spec: [03-service-layer.md line 18](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |

**Expectancy function** (`domain/analytics/expectancy.py`):

| AC | Description | Source |
|----|-------------|--------|
| AC-10 | `calculate_expectancy(trades: list[Trade]) → ExpectancyResult` — formula: `(win_rate × avg_win) - (loss_rate × avg_loss)` | Research-backed: Van Tharp, *Trade Your Way to Financial Freedom*, 3rd ed., McGraw-Hill, 2006, ch. 7 (https://www.vantharp.com/trade-your-way-to-financial-freedom) |
| AC-11 | `profit_factor = gross_wins / abs(gross_losses)` (Decimal("0") if no losses) | Research-backed: Van Tharp, *Trade Your Way to Financial Freedom*, 3rd ed., ch. 7 (https://www.vantharp.com/trade-your-way-to-financial-freedom) |
| AC-12 | `kelly_fraction = win_rate - (loss_rate / payoff_ratio)` (Decimal("0") if payoff_ratio is 0) | Research-backed: Kelly, J.L. Jr., "A New Interpretation of Information Rate," *Bell System Technical Journal* 35(4):917–926, 1956 (https://doi.org/10.1002/j.1538-7305.1956.tb03809.x) |
| AC-13 | Returns zero-value result with `trade_count=0` for empty trades list | Local Canon: [03-service-layer.md line 577](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |

**SQN function** (`domain/analytics/sqn.py`):

| AC | Description | Source |
|----|-------------|--------|
| AC-14 | `calculate_sqn(trades: list[Trade]) → SQNResult` — formula: `(mean_R / std_R) × √n` | Research-backed: https://www.vantharp.com/trade-your-way-to-financial-freedom |
| AC-15 | R-multiples derived from `realized_pnl` on each trade | Local Canon: [domain-model-ref line 46](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-16 | Grade: `< 1.6` "Poor", `1.6–1.9` "Average", `2.0–2.4` "Good", `2.5–2.9` "Excellent", `3.0–5.0` "Superb", `5.0–6.9` "Holy Grail", `≥ 7.0` "Unicorn" | Research-backed: https://www.vantharp.com/sqn + [03-service-layer.md line 108](file:///p:/zorivest/docs/build-plan/03-service-layer.md) |
| AC-17 | Returns zero-value result if fewer than 2 trades or std_R is 0 | Local Canon: need ≥2 data points for standard deviation |

**Module imports:**

| AC | Description | Source |
|----|-------------|--------|
| AC-18 | `results.py` imports only from `__future__`, `dataclasses`, `decimal` | Local Canon: import surface pattern from MEU-1–5 |
| AC-19 | Function modules import only from `__future__`, `decimal`, `math`, `analytics.results`, `zorivest_core.domain.entities` | Local Canon: same pattern |

**Out-of-scope** (deferred):

| Item | Reason |
|------|--------|
| `strategy.py` + `breakdown_by_strategy()` | Groups by `strategy_name` from `TradeReport.tags` ([domain-model-ref line 58](file:///p:/zorivest/docs/build-plan/domain-model-reference.md), [04e line 44](file:///p:/zorivest/docs/build-plan/04e-api-analytics.md), [05c lines 425/430](file:///p:/zorivest/docs/build-plan/05c-mcp-trade-analytics.md)). `TradeReport` is P1. |
| `drawdown.py` | Requires Monte Carlo + numpy/scipy — P2.75 item 66e |
| `excursion.py` | Requires market bar data — P2.75 item 59e |
| `execution_quality.py` | Requires NBBO quotes — P2.75 item 62e |
| `pfof.py` | Requires market data — P2.75 item 63e |
| `cost_of_free.py` | Requires TransactionLedger (P1) — P2.75 item 68.3e |

#### [NEW] [analytics/__init__.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/analytics/__init__.py)

#### [NEW] [analytics/results.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/analytics/results.py)

- All 8 frozen result dataclasses matching [03-service-layer.md](file:///p:/zorivest/docs/build-plan/03-service-layer.md) exactly

#### [NEW] [analytics/expectancy.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/analytics/expectancy.py)

- `calculate_expectancy(trades: list[Trade]) → ExpectancyResult`

#### [NEW] [analytics/sqn.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/analytics/sqn.py)

- `calculate_sqn(trades: list[Trade]) → SQNResult`

#### [NEW] [test_analytics.py](file:///p:/zorivest/tests/unit/test_analytics.py)

- ~18 test functions covering AC-1 through AC-19

---

### State Management

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

- MEU-6, MEU-7, MEU-8 status updates as each completes

---

## Plan Location

Per `create-plan.md` §4:

```
docs/execution/plans/2026-03-07-commands-events-analytics/
├── implementation-plan.md   ← this file (source of truth)
└── task.md
```

## Handoff Naming

Continuing from highest existing sequence (003):

| Seq | Handoff Path |
|-----|-------------|
| 004 | `.agent/context/handoffs/004-2026-03-07-commands-dtos-bp01s1.2.md` |
| 005 | `.agent/context/handoffs/005-2026-03-07-events-bp01s1.2.md` |
| 006 | `.agent/context/handoffs/006-2026-03-07-analytics-bp01s1.2.md` |

## Post-Project Artifacts

| Artifact | Path | Owner | Timing |
|----------|------|-------|--------|
| Reflection | `docs/execution/reflections/2026-03-07-commands-events-analytics-reflection.md` | tester | After Codex validation (per `execution-session.md` §5) |
| Metrics row | `docs/execution/metrics.md` (append row) | tester | After Codex validation |
| Session state | `pomera_notes` title: `Memory/Session/Zorivest-commands-events-analytics-2026-03-07` | orchestrator | End of session |

---

## Verification Plan

### Per-MEU Gate

```powershell
# MEU-6
uv run pytest tests/unit/test_commands_dtos.py -x --tb=short -m "unit" -v
uv run pytest tests/unit/ -x --tb=short -m "unit"
uv run pyright packages/core/src/zorivest_core/application/
uv run ruff check packages/core/src/zorivest_core/application/
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/application/ || Write-Output "Anti-placeholder: clean"

# MEU-7
uv run pytest tests/unit/test_events.py -x --tb=short -m "unit" -v
uv run pytest tests/unit/ -x --tb=short -m "unit"
uv run pyright packages/core/src/zorivest_core/domain/events.py
uv run ruff check packages/core/src/zorivest_core/domain/events.py
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/events.py || Write-Output "Anti-placeholder: clean"

# MEU-8
uv run pytest tests/unit/test_analytics.py -x --tb=short -m "unit" -v
uv run pytest tests/unit/ -x --tb=short -m "unit"
uv run pyright packages/core/src/zorivest_core/domain/analytics/
uv run ruff check packages/core/src/zorivest_core/domain/analytics/
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/analytics/ || Write-Output "Anti-placeholder: clean"
```

### Phase Gate (NOT run — Phase 1 incomplete)

Phase gate (`.\tools\validate.ps1`) runs only when ALL Phase 1 MEUs are complete.

---

## Stop Conditions

- ❌ Do NOT commit or push
- ❌ Do NOT start Track B (logging MEUs)
- ❌ Do NOT modify existing `calculator.py`, `enums.py`, `entities.py`, `value_objects.py`, or `ports.py`
- ❌ Do NOT create analytics functions requiring external data (drawdown, excursion, execution_quality, pfof, cost_of_free)
- ❌ Do NOT create `strategy.py` — requires P1 TradeReport entity
- ❌ Do NOT use Pydantic validation (Phase 4)
- ✅ Save session state to `pomera_notes` at end
- ✅ Present commit messages to human
