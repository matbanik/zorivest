# MEU-1: Calculator Pilot — Implementation Plan

> **Date**: 2026-03-06
> **MEU**: 1 — `calculator`
> **Build Plan Reference**: [01-domain-layer.md §1.3](file:///p:/zorivest/docs/build-plan/01-domain-layer.md)
> **Prompt**: [2026-03-06-meu-1-calculator-pilot.md](file:///p:/zorivest/docs/execution/prompts/2026-03-06-meu-1-calculator-pilot.md)

---

## Goal

Implement `PositionSizeResult` and `calculate_position_size()` as the day-1 pilot — validating the dual-agent TDD workflow, monorepo bootstrap, and handoff protocol. Pure math with zero runtime dependencies.

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 1 | Bootstrap monorepo workspace | coder | `pyproject.toml`, `packages/core/pyproject.toml`, `__init__.py` files | `uv sync` succeeds | ⬜ |
| 2 | Add dev tooling | coder | pytest, pyright, ruff installed | `uv run pytest --version` succeeds | ⬜ |
| 3 | Write FIC | coder | FIC documented in handoff artifact | 7 ACs, 3 negative cases listed | ⬜ |
| 4 | Red Phase — write failing tests | tester | `tests/unit/test_calculator.py` | `uv run pytest tests/unit/test_calculator.py -x -v` → all FAIL | ⬜ |
| 5 | Green Phase — implement | coder | `packages/core/src/zorivest_core/domain/calculator.py` | `uv run pytest tests/unit/test_calculator.py -x -v` → all PASS | ⬜ |
| 6 | Verification gate | tester | All 4 gate commands pass | See §Verification Commands | ⬜ |
| 7 | Create handoff artifact | coder | `.agent/context/handoffs/2026-03-06-meu-1-calculator.md` | 7/7 sections filled | ⬜ |
| 8 | Update MEU registry | coder | `meu-registry.md` → MEU-1 = `ready_for_review` | Registry status updated | ⬜ |
| 9 | Save session state | coder | `pomera_notes` entry | Entry exists with title `Memory/Session/Zorivest-MEU-1-2026-03-06` | ⬜ |
| 10 | Post-execution reflection | coder | `docs/execution/reflections/2026-03-06-reflection.md` | Reflection created from TEMPLATE | ⬜ |
| 11 | Update metrics | coder | `docs/execution/metrics.md` row filled | Day 1 row has concrete values | ⬜ |
| 12 | Present Codex trigger + commit msg | coder | Final summary to human | Human receives text | ⬜ |

---

## Files To Create

| File | Purpose |
|------|---------|
| `pyproject.toml` | Root workspace with uv workspace config |
| `packages/core/pyproject.toml` | Core package build config |
| `packages/core/src/zorivest_core/__init__.py` | Package init |
| `packages/core/src/zorivest_core/domain/__init__.py` | Domain subpackage init |
| `packages/core/src/zorivest_core/domain/calculator.py` | Calculator implementation |
| `tests/conftest.py` | Shared test config (minimal — no entity fixtures for MEU-1) |
| `tests/unit/__init__.py` | Unit test package init |
| `tests/unit/test_calculator.py` | Calculator tests (7 ACs + frozen + import surface) |

## Files To Modify

| File | Change |
|------|--------|
| `.agent/context/meu-registry.md` | Set MEU-1 status to `🟡 ready_for_review` |
| `docs/execution/metrics.md` | Fill Day 1 row with concrete values |

---

## Feature Intent Contract

### Intent Statement

The calculator accepts account balance, risk percentage, entry, stop, and target prices and returns a frozen result dataclass with seven computed fields using pure arithmetic only.

### Acceptance Criteria

| AC | Criterion | Test |
|----|-----------|------|
| AC-1 | Basic calculation matches build plan spec values (balance=437,903.03, risk=1%, entry=619.61, stop=618.61, target=620.61) | `test_basic_calculation` |
| AC-2 | Zero entry → zero shares, zero risk per share | `test_zero_entry_returns_zero_shares` |
| AC-3 | Risk % out of range (≤0 or >100) → defaults to 1% | `test_risk_out_of_range_defaults_to_one_percent` |
| AC-4 | entry == stop → zero shares, zero reward/risk ratio | `test_entry_equals_stop` |
| AC-5 | Zero balance → 0.0 for position_to_account_pct | `test_zero_balance` |
| AC-6 | `PositionSizeResult` is a frozen dataclass | `test_frozen_dataclass` |
| AC-7 | Implementation imports only `__future__`, `math`, `dataclasses` | `test_import_surface` |

### Negative Cases

- Must not raise for any numeric inputs covered by the FIC
- Must not import from any other Zorivest module
- Must not change test assertions in Green phase to force a pass

---

## Verification Commands

Run after Green phase — all four must pass for MEU-1 completion:

```powershell
# 1. Unit tests
uv run pytest tests/unit/ -x --tb=short -v

# 2. Type checking
uv run pyright packages/core/src

# 3. Linting
uv run ruff check packages/core/src tests

# 4. Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError|pass\s+#\s*placeholder" packages tests
```

Then run `.\tools\validate.ps1` as an **informational probe only** — do not widen scope if it fails on unrelated surfaces.

---

## Stop Conditions

- ✅ Stop after MEU-1 is complete — do NOT proceed to MEU-2 or other modules
- ✅ Do NOT create `entities.py`, `value_objects.py`, `enums.py`, `events.py`, `ports.py`, `commands.py`, `dtos.py`, `services/`, or any infrastructure/api/ui/mcp code
- ✅ Do NOT create placeholder stubs for future work
- ✅ Do NOT auto-commit — propose exact conventional commit message(s) instead
- ✅ If any repo rule conflicts with the prompt, stop and ask the human

## Handoff File Path

```
.agent/context/handoffs/2026-03-06-meu-1-calculator.md
```

---

## Verification Plan

### Automated Tests

All verification is automated via the 4 gate commands above:

1. **`uv run pytest tests/unit/ -x --tb=short -v`** — runs all unit tests including the 9 test functions in `test_calculator.py`
2. **`uv run pyright packages/core/src`** — validates type annotations
3. **`uv run ruff check packages/core/src tests`** — lints all source and test code
4. **`rg "TODO|FIXME|NotImplementedError|pass\s+#\s*placeholder" packages tests`** — scans for banned patterns

### Manual Verification

- Human reviews the handoff artifact for self-containedness (7/7 Handoff Score sections filled)
- Human reviews proposed commit message(s)
- Human triggers Codex validation via the provided trigger text in a separate session
