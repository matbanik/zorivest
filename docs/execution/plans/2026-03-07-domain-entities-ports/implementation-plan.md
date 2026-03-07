# Project: domain-entities-ports (v3)

Domain model foundation — entities, value objects, and port interfaces for the Zorivest trading journal.

**Project slug:** `domain-entities-ports`
**MEUs:** MEU-3 → MEU-4 → MEU-5
**Build plan:** [01-domain-layer.md](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) §1.2, §1.4, §1.5
**Date:** 2026-03-07

---

## User Review Required

> [!CAUTION]
> **MEU-2 dependency gate.** MEU-3 imports enums. MEU-2 is 🟡 `ready_for_review` — not yet ✅ `approved`. Per `create-plan.md` §Step 2: *"only MEUs whose dependencies are satisfied by approved MEUs are unblocked."* This plan **cannot begin execution until MEU-2 reaches ✅ approved**. If MEU-2 gets `changes_required`, the entity imports may need adaptation.

## Standing Project Rules

Per human decision (2026-03-07):

1. **Full contract always.** Entities implement the complete field set from `domain-model-reference.md`. No narrowing, no P0 subsets, no deferrals.
2. **Validators always.** Value objects include best-practice validation. When the build plan doesn't specify rules, follow domain best practices and document each rule in the FIC.

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 0 | **Gate: Confirm MEU-2 ✅** | orchestrator | MEU-2 approved in registry | Check `meu-registry.md` | ⬜ |
| 1 | MEU-3 FIC + Red tests | coder | `tests/unit/test_entities.py` | `pytest` — all FAIL | ⬜ |
| 2 | MEU-3 Green implementation | coder | `entities.py` | `pytest` — all PASS | ⬜ |
| 3 | MEU-3 quality gate | tester | Zero errors | `pyright`, `ruff check`, anti-placeholder | ⬜ |
| 4 | MEU-3 handoff | coder | `001-2026-03-07-entities-bp01s1.4.md` | Self-contained, all 7 sections | ⬜ |
| 5 | MEU-4 FIC + Red tests | coder | `tests/unit/test_value_objects.py` | `pytest` — all FAIL | ⬜ |
| 6 | MEU-4 Green implementation | coder | `value_objects.py` | `pytest` — all PASS | ⬜ |
| 7 | MEU-4 quality gate | tester | Zero errors | `pyright`, `ruff check`, anti-placeholder | ⬜ |
| 8 | MEU-4 handoff | coder | `002-2026-03-07-value-objects-bp01s1.2.md` | Self-contained, all 7 sections | ⬜ |
| 9 | MEU-5 FIC + Red tests | coder | `tests/unit/test_ports.py` | `pytest` — all FAIL | ⬜ |
| 10 | MEU-5 Green implementation | coder | `ports.py` + `application/__init__.py` | `pytest` — all PASS | ⬜ |
| 11 | MEU-5 quality gate | tester | Zero errors | `pyright`, `ruff check`, anti-placeholder | ⬜ |
| 12 | MEU-5 handoff | coder | `003-2026-03-07-ports-bp01s1.5.md` | Self-contained, all 7 sections | ⬜ |
| 13 | Phase gate + reflection + metrics | tester | Updated reflection, metrics, pomera | Consistency check | ⬜ |

**Role progression per MEU:** orchestrator (gate) → coder (FIC + Red + Green + handoff) → tester (quality gate) → Codex reviewer (validation appended to handoff)

---

## Proposed Changes

### MEU-3: Domain Entities (bp01 §1.4)

#### FIC — Feature Intent Contract

Fields sourced from [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) lines 16–111.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `Trade` dataclass: `exec_id` (str, PK), `time` (datetime), `instrument` (str), `action` (TradeAction), `quantity` (float), `price` (float), `account_id` (str), `commission` (float, default 0.0), `realized_pnl` (float, default 0.0), `images` (list[ImageAttachment], default []), `report` (Optional[TradeReport], default None) | domain-model-ref lines 37–48 |
| AC-2 | `Trade.attach_image(img)` appends an `ImageAttachment` to `trade.images` | 01-domain-layer §1.4 |
| AC-3 | `Account` dataclass: `account_id` (str, PK), `name` (str), `account_type` (AccountType), `institution` (str, default ""), `currency` (str, default "USD"), `is_tax_advantaged` (bool, default False), `notes` (str, default ""), `sub_accounts` (list[str], default []), `balance_source` (BalanceSource, default MANUAL), `balance_snapshots` (list[BalanceSnapshot], default []) | domain-model-ref lines 16–27 |
| AC-4 | `BalanceSnapshot` frozen dataclass: `id` (int), `account_id` (str), `datetime` (datetime), `balance` (Decimal) | domain-model-ref lines 29–33 |
| AC-5 | `ImageAttachment` frozen dataclass: `id` (int), `owner_type` (ImageOwnerType), `owner_id` (str), `data` (bytes), `thumbnail` (bytes, default b""), `mime_type` (str, literal `"image/webp"`), `caption` (str, default ""), `width` (int), `height` (int), `file_size` (int), `created_at` (datetime, auto) | domain-model-ref lines 100–111 |
| AC-6 | `mime_type` is always `"image/webp"` — enforced at construction | domain-model-ref line 107 |
| AC-7 | Module imports only from `__future__`, `dataclasses`, `datetime`, `decimal`, `typing`, `zorivest_core.domain.enums` | Pattern from MEU-1/MEU-2 |

> **Note:** `TradeReport` is P1 (not in MEU-3 scope). The `report` field on Trade is typed as `Optional` and defaults to `None`.

#### [NEW] [entities.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py)

- `Trade` (mutable — `attach_image`), `Account` (mutable), `BalanceSnapshot` (frozen), `ImageAttachment` (frozen)

#### [NEW] [test_entities.py](file:///p:/zorivest/tests/unit/test_entities.py)

- ~12 test functions covering AC-1 through AC-7
- Pattern: `pytestmark = pytest.mark.unit`, inline imports, AST import surface check

---

### MEU-4: Value Objects (bp01 §1.2)

#### FIC — Feature Intent Contract

All value objects sourced from [01-domain-layer.md §1.2](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) line 29: `value_objects.py # Money, PositionSize, Ticker, ImageData, Conviction`. Validation rules per Standing Project Rule #2.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `Money` frozen dataclass with `amount` (Decimal) and `currency` (str, default "USD") | build-plan §1.2 |
| AC-2 | `Money` rejects negative `amount` (raises `ValueError`). Zero is allowed. | best practice: money can't be negative |
| AC-3 | `Money` rejects empty `currency` (raises `ValueError`) | best practice: currency always required |
| AC-4 | `PositionSize` frozen dataclass wrapping `share_size` (int), `position_size` (Decimal), `risk_per_share` (Decimal) | build-plan §1.2 + calculator output |
| AC-5 | `PositionSize` rejects negative `share_size` (raises `ValueError`) | best practice |
| AC-6 | `Ticker` frozen dataclass with `symbol` (str). Normalizes to uppercase at construction. | best practice: tickers are always uppercase |
| AC-7 | `Ticker` rejects empty or whitespace-only `symbol` (raises `ValueError`) | best practice |
| AC-8 | `Conviction` frozen dataclass with `level` (ConvictionLevel enum) | build-plan §1.2 |
| AC-9 | `ImageData` frozen dataclass with `data` (bytes), `mime_type` (str), `width` (int), `height` (int) | build-plan §1.2 |
| AC-10 | `ImageData` rejects non-positive `width` or `height` (raises `ValueError`) | best practice |
| AC-11 | `ImageData` rejects empty `data` (raises `ValueError`) | best practice |
| AC-12 | All value objects are frozen. Attribute assignment raises `FrozenInstanceError`. | dataclass convention |
| AC-13 | Module imports only from `__future__`, `dataclasses`, `decimal`, `zorivest_core.domain.enums` | Pattern from MEU-1/MEU-2 |

#### [NEW] [value_objects.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/value_objects.py)

- `Money`, `PositionSize`, `Ticker`, `Conviction`, `ImageData` — all frozen dataclasses with `__post_init__` validation

#### [NEW] [test_value_objects.py](file:///p:/zorivest/tests/unit/test_value_objects.py)

- ~15 test functions covering AC-1 through AC-13 (construction, validation, immutability, import surface)

---

### MEU-5: Port Interfaces (bp01 §1.5)

#### FIC — Feature Intent Contract

All protocols sourced from [01-domain-layer.md §1.5](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) lines 452–507.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `TradeRepository` Protocol: `get`, `save`, `list_all`, `exists` | §1.5 lines 461–465 |
| AC-2 | `ImageRepository` Protocol: `save`, `get`, `get_for_owner`, `delete`, `get_thumbnail` | §1.5 lines 468–473 |
| AC-3 | `UnitOfWork` Protocol: `trades`, `images`, `__enter__`/`__exit__`, `commit`, `rollback` | §1.5 lines 476–482 |
| AC-4 | `BrokerPort` Protocol: `get_account`, `get_positions`, `get_orders`, `get_bars`, `get_order_history` | §1.5 lines 487–493 |
| AC-5 | `BankImportPort` Protocol: `detect_format`, `parse_statement`, `detect_bank` | §1.5 lines 496–500 |
| AC-6 | `IdentifierResolverPort` Protocol: `resolve`, `batch_resolve` | §1.5 lines 503–506 |
| AC-7 | All are `Protocol` subclasses (not `runtime_checkable`) | §1.5 pattern |
| AC-8 | Module imports only from `__future__`, `typing`, `zorivest_core.domain.entities` | Pattern from prior MEUs |

#### [NEW] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

- 6 Protocol classes + `application/__init__.py`

#### [NEW] [test_ports.py](file:///p:/zorivest/tests/unit/test_ports.py)

- Module integrity test (AST import surface, protocol class count)
- ~4 test functions

---

### State Management

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

- MEU-3, MEU-4, MEU-5 status updates as each completes

---

## Plan Location

Per `create-plan.md` §4 — files written directly to:

```
docs/execution/plans/2026-03-07-domain-entities-ports/
├── implementation-plan.md   ← this file (source of truth)
└── task.md
```

## Handoff Naming

No sequenced handoffs exist → start at `001`.

| Seq | Handoff Path |
|-----|-------------|
| 001 | `.agent/context/handoffs/001-2026-03-07-entities-bp01s1.4.md` |
| 002 | `.agent/context/handoffs/002-2026-03-07-value-objects-bp01s1.2.md` |
| 003 | `.agent/context/handoffs/003-2026-03-07-ports-bp01s1.5.md` |

## Post-Project Artifacts

| Artifact | Path | Owner |
|----------|------|-------|
| Reflection | `docs/execution/reflections/2026-03-07-domain-entities-ports-reflection.md` | tester |
| Metrics row | `docs/execution/metrics.md` (append row) | tester |
| Session state | `pomera_notes` title: `Memory/Session/Zorivest-domain-entities-ports-2026-03-07` | orchestrator |

---

## Verification Plan

### Per-MEU Gate

```powershell
uv run pytest tests/unit/test_{module}.py -x --tb=short -m "unit" -v
uv run pytest tests/unit/ -x --tb=short -m "unit"
uv run pyright packages/core/src/
uv run ruff check packages/core/src/
rg "TODO|FIXME|NotImplementedError" packages/
```

### Phase Gate (after all 3 MEUs)

```powershell
.\tools\validate.ps1
```

---

## Stop Conditions

- ❌ Do NOT begin execution until MEU-2 is ✅ approved
- ❌ Do NOT commit or push
- ❌ Do NOT start MEU-6, MEU-7, or MEU-8
- ❌ Do NOT touch Track B (logging)
- ❌ Do NOT modify existing `calculator.py` or `enums.py`
- ✅ Save session state to `pomera_notes` at end
- ✅ Present commit messages to human
