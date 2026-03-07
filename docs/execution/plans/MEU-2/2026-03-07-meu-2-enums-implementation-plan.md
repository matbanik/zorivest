# MEU-2: StrEnum Definitions

Implement the 14 `StrEnum` classes defined in [01-domain-layer.md §1.2](file:///p:/zorivest/docs/build-plan/01-domain-layer.md#L154-L270) as a pure enum module with comprehensive TDD coverage.

## User Review Required

> [!IMPORTANT]
> **MEU registry says "15 enums" but build plan §1.2 defines exactly 14 classes.**
> The prompt explicitly states AC-4: *"exactly the 14 enum classes"* and out-of-scope: *"do not invent a missing 15th class."*
> Plan follows the prompt: **14 enum classes**.
> If you want 15, please specify which class to add.

## Feature Intent Contract

**Intent:** The domain exposes the exact `StrEnum` definitions listed in `docs/build-plan/01-domain-layer.md` §1.2, with exact class names and string values, and no extra enum classes.

| AC | Description |
|----|-------------|
| AC-1 | 6 core enums: `AccountType`, `TradeAction`, `ConvictionLevel`, `PlanStatus`, `ImageOwnerType`, `DisplayModeFlag` |
| AC-2 | 8 expansion enums: `RoundTripStatus`, `IdentifierType`, `FeeType`, `StrategyType`, `MistakeCategory`, `RoutingType`, `TransactionCategory`, `BalanceSource` |
| AC-3 | Every class subclasses `StrEnum`, every member value matches build plan exactly |
| AC-4 | Module contains exactly 14 enum classes — no more, no fewer |
| AC-5 | Module imports only `StrEnum` from `enum` — no Zorivest cross-imports |

---

## Proposed Changes

### Domain Package

#### [NEW] [enums.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py)

- 14 `StrEnum` classes copied verbatim from build plan §1.2 (lines 156–270)
- Single import: `from enum import StrEnum`
- No docstrings beyond what's in the build plan

#### [MODIFY] [__init__.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/__init__.py)

- Only if deterministic import wiring is needed (e.g., `from zorivest_core.domain import AccountType`)
- Likely no change — tests import directly from `zorivest_core.domain.enums`

---

### Test Suite

#### [NEW] [test_enums.py](file:///p:/zorivest/tests/unit/test_enums.py)

Tests covering all 5 acceptance criteria:

| Test | AC |
|------|----|
| `test_module_has_exactly_14_enum_classes` | AC-4 |
| `test_all_enums_subclass_strenum` | AC-3 |
| `test_account_type_members` | AC-1 |
| `test_trade_action_members` | AC-1 |
| `test_conviction_level_members` | AC-1 |
| `test_plan_status_members` | AC-1 |
| `test_image_owner_type_members` | AC-1 |
| `test_display_mode_flag_members` | AC-1 |
| `test_round_trip_status_members` | AC-2 |
| `test_identifier_type_members` | AC-2 |
| `test_fee_type_members` | AC-2 |
| `test_strategy_type_members` | AC-2 |
| `test_mistake_category_members` | AC-2 |
| `test_routing_type_members` | AC-2 |
| `test_transaction_category_members` | AC-2 |
| `test_balance_source_members` | AC-2 |
| `test_import_surface_only_enum` | AC-5 |

Each member test asserts: correct member count, each member's `.value` matches the build plan string exactly.

The module **must** include `pytestmark = pytest.mark.unit` at module level (per prompt §C and existing pattern in `test_calculator.py:11`).

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 1 | Write FIC | orchestrator | FIC in plan | Human review | ⬜ |
| 2 | Write `test_enums.py` (Red) | coder | Test file | `uv run pytest tests/unit/test_enums.py -x --tb=short -v` → all FAIL | ⬜ |
| 3 | Capture FAIL_TO_PASS evidence | coder | Terminal output | Screenshot/copy of failures | ⬜ |
| 4 | Implement `enums.py` (Green) | coder | Source file | Same pytest command → all PASS | ⬜ |
| 5 | `uv sync --reinstall-package` | coder | Package rebuild | No errors | ⬜ |
| 6 | MEU verification gate | tester | Gate results | 4 commands below → all pass | ⬜ |
| 7 | `tools\validate.ps1` probe | tester | Informational | Record result in handoff | ⬜ |
| 8 | Create handoff artifact | coder | Handoff .md | Self-contained per template | ⬜ |
| 9 | Update MEU registry status | coder | Registry update | MEU-2 → `ready_for_review` | ⬜ |
| 9a | Fix MEU registry description | coder | Registry text fix | Change "15 enums" → "14 enums" | ⬜ |
| 10 | Save pomera notes | coder | Note entry | `Memory/Session/Zorivest-MEU-2-2026-03-07` | ⬜ |
| 11 | Create reflection | coder | Reflection .md | from TEMPLATE.md | ⬜ |
| 12 | Update metrics | coder | metrics.md row | New row appended | ⬜ |
| 13 | Propose commit message | coder | Text | Conventional format | ⬜ |
| 14 | Provide Codex trigger text | coder | Text | Exact block from prompt | ⬜ |

---

## Files Summary

| Action | Path |
|--------|------|
| CREATE | `packages/core/src/zorivest_core/domain/enums.py` |
| CREATE | `tests/unit/test_enums.py` |
| MAYBE MODIFY | `packages/core/src/zorivest_core/domain/__init__.py` |
| CREATE | `.agent/context/handoffs/2026-03-07-meu-2-enums.md` |
| UPDATE | `.agent/context/meu-registry.md` |
| CREATE | `docs/execution/reflections/2026-03-07-reflection.md` |
| UPDATE | `docs/execution/metrics.md` |
| ARCHIVE | `docs/execution/plans/MEU-2/2026-03-07-meu-2-enums-implementation-plan.md` |
| ARCHIVE | `docs/execution/plans/MEU-2/2026-03-07-meu-2-enums-task.md` |

---

## Verification Plan

### Automated Tests

All commands run from repo root `p:\zorivest`:

```powershell
# 1. Red phase — tests must FAIL (module doesn't exist yet)
uv run pytest tests/unit/test_enums.py -x --tb=short -v

# 2. Green phase — tests must PASS after implementation
uv run pytest tests/unit/test_enums.py -x --tb=short -v

# 3. MEU verification gate (all must pass)
uv run pytest tests/unit/ -x --tb=short -v
uv run pyright packages/core/src
uv run ruff check packages/core/src tests
rg "TODO|FIXME|NotImplementedError|pass\s+#\s*placeholder" packages tests

# 4. Informational full-repo probe (may fail for out-of-scope reasons)
.\tools\validate.ps1
```

### Stop Conditions

- ✅ All MEU gate commands pass
- ✅ Handoff exists and is self-contained
- ✅ MEU registry updated to `ready_for_review`
- ✅ Pomera note saved
- ✅ Reflection and metrics updated
- ✅ Commit message and Codex trigger text proposed
- 🛑 Do NOT widen scope if `validate.ps1` fails on unrelated surfaces
