---
meu: 1
slug: calculator
phase: 1
priority: P0
status: approved
agent: opus-4.6
iteration: 2
files_changed: 8
tests_added: 9
tests_passing: 9
---

# MEU-1: Calculator Pilot

## Scope

Position size calculator — the day-1 pilot validating the dual-agent TDD workflow, monorepo bootstrap, and handoff protocol. Implements `PositionSizeResult` (frozen dataclass, 7 fields) and `calculate_position_size()` as pure math with zero runtime dependencies.

Build plan reference: [01-domain-layer.md §1.3](../../docs/build-plan/01-domain-layer.md)

## Feature Intent Contract

### Intent Statement

The calculator accepts account balance, risk percentage, entry, stop, and target prices and returns a frozen result dataclass with seven computed fields using pure arithmetic only.

### Acceptance Criteria

- AC-1: Basic calculation matches spec values (balance=437,903.03, risk=1%, entry=619.61, stop=618.61, target=620.61)
- AC-2: Zero entry → zero shares, zero risk per share
- AC-3: Risk % out of range (≤0 or >100) → defaults to 1%
- AC-4: entry == stop → zero shares, zero reward/risk ratio
- AC-5: Zero balance → 0.0 for position_to_account_pct
- AC-6: `PositionSizeResult` is a frozen dataclass
- AC-7: Implementation imports only `__future__`, `math`, `dataclasses`

### Negative Cases

- Must NOT raise for any numeric inputs covered by the FIC
- Must NOT import from any other Zorivest module
- Must NOT change test assertions in Green phase to force a pass

### Test Mapping

| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-1 | tests/unit/test_calculator.py | test_basic_calculation |
| AC-2 | tests/unit/test_calculator.py | test_zero_entry_returns_zero_shares |
| AC-3 | tests/unit/test_calculator.py | test_risk_out_of_range_defaults_to_one_percent, test_risk_zero_defaults_to_one_percent, test_risk_negative_defaults_to_one_percent |
| AC-4 | tests/unit/test_calculator.py | test_entry_equals_stop |
| AC-5 | tests/unit/test_calculator.py | test_zero_balance |
| AC-6 | tests/unit/test_calculator.py | test_frozen_dataclass |
| AC-7 | tests/unit/test_calculator.py | test_import_surface |

## Design Decisions & Known Risks

- **Decision**: Used `hatchling.build` as the build backend for `packages/core` — **Reasoning**: Hatchling is lightweight, supports src-layout out of the box, and is recommended for Python packaging — **ADR**: inline (minor)
- **Decision**: Added `zorivest-core` as a workspace dependency with `[tool.uv.sources]` — **Reasoning**: Required for `import zorivest_core` to resolve in the venv during test execution — **ADR**: inline (minor)
- **Decision**: Used `math.floor()` for reward/risk truncation rather than rounding — **Reasoning**: Matches the build plan spec exactly (§1.3 reference implementation) — **ADR**: inline (spec-conformant)
- **Assumption**: The spec values in `01-domain-layer.md §1.3` are the golden reference for AC-1 assertions
- **Risk**: `tools/validate.ps1` was not run in this session (informational probe deferred to Codex validation)

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | Created | Root workspace with uv config, pytest markers, zorivest-core dependency |
| `packages/core/pyproject.toml` | Created | Core package with hatchling build backend, src layout |
| `packages/core/src/zorivest_core/__init__.py` | Created | Package init |
| `packages/core/src/zorivest_core/domain/__init__.py` | Created | Domain subpackage init |
| `packages/core/src/zorivest_core/domain/calculator.py` | Created | PositionSizeResult + calculate_position_size() |
| `tests/conftest.py` | Created | Minimal test config |
| `tests/unit/__init__.py` | Created | Unit test package marker |
| `tests/unit/test_calculator.py` | Created | 9 tests covering all 7 ACs |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `uv sync` | PASS | Workspace resolved with Python 3.12.12 |
| `uv add --dev pytest pyright ruff` | PASS | 10 packages installed |
| `uv run pytest tests/unit/test_calculator.py -x -v` (Red) | FAIL | ModuleNotFoundError — expected |
| `uv run pytest tests/unit/test_calculator.py -x -v` (Green) | PASS (9 tests) | 0.02s |
| `uv run pytest tests/unit/ -x --tb=short -v` | PASS (9 tests) | 0.03s |
| `uv run pyright packages/core/src` | PASS | 0 errors, 0 warnings |
| `uv run ruff check packages/core/src tests` | PASS | All checks passed |
| `rg "TODO\|FIXME\|NotImplementedError\|pass\s+#\s*placeholder" packages tests` | PASS | 0 matches |

## Revision 1 — AV-3 Fix

**Finding**: Codex AV-3 — `test_basic_calculation` did not assert `position_size` or `position_to_account_pct`.

**Fix**: Added 2 assertions to `test_basic_calculation`:
- `assert result.position_size == 2713273`
- `assert result.position_to_account_pct == pytest.approx(619.6, abs=0.01)`

**Re-verification**: All 4 MEU gate commands pass (pytest 9/9, pyright 0 errors, ruff clean, rg clean).

## FAIL_TO_PASS Evidence

| Test | Before (Red) | After (Green) |
|------|-------------|---------------|
| test_basic_calculation | FAIL (ModuleNotFoundError) | PASS |
| test_zero_entry_returns_zero_shares | FAIL (ModuleNotFoundError) | PASS |
| test_risk_out_of_range_defaults_to_one_percent | FAIL (ModuleNotFoundError) | PASS |
| test_risk_zero_defaults_to_one_percent | FAIL (ModuleNotFoundError) | PASS |
| test_risk_negative_defaults_to_one_percent | FAIL (ModuleNotFoundError) | PASS |
| test_entry_equals_stop | FAIL (ModuleNotFoundError) | PASS |
| test_zero_balance | FAIL (ModuleNotFoundError) | PASS |
| test_frozen_dataclass | FAIL (ModuleNotFoundError) | PASS |
| test_import_surface | FAIL (ModuleNotFoundError) | PASS |

---
## Codex Validation Report

**Date**: 2026-03-06
**MEU**: 1 — calculator
**Verdict**: approved

### Re-Validation Note

- Revision 1 added explicit AC-1 assertions for `position_size` and the nonzero `position_to_account_pct` path in `test_basic_calculation`.
- Codex reran the validation workflow against iteration 2 and confirmed the prior AV-3 finding is resolved.

### Retroactive Plan Intake

- Step 3 plan review was skipped before execution. Codex performed a retroactive intake against `docs/execution/plans/2026-03-06-implementation-plan.md`, `docs/execution/plans/2026-03-06-task.md`, and `docs/execution/prompts/2026-03-06-meu-1-calculator-pilot.md` before implementation validation.
- Result: implementation stayed within MEU-1 scope, stop conditions were respected, and the required artifacts exist (`meu-registry`, reflection, metrics, archived plan/task, and Pomera note `Memory/Session/Zorivest-MEU-1-2026-03-06`).

### Test Results

| Command | Result |
|---------|--------|
| `uv run pytest -x --tb=long -v` | PASS (9 tests) |
| `uv run pyright packages/core/src` | PASS (0 errors, 0 warnings, 0 informations) |
| `uv run ruff check packages/core/src tests` | PASS (All checks passed) |
| `.\tools\validate.ps1` | PASS (blocking checks); advisory note referenced an unrelated latest handoff |

### Adversarial Checklist

| Check | Result | Evidence |
|-------|--------|----------|
| AV-1 | PASS | `FAIL_TO_PASS Evidence` shows all 9 tests failed in Red with `ModuleNotFoundError` and passed in Green. |
| AV-2 | PASS | No monkeypatching, forced early returns, or mocked assertions in `packages/core/src/zorivest_core/domain/calculator.py` or `tests/unit/test_calculator.py`. |
| AV-3 | PASS | `tests/unit/test_calculator.py:29-35` now asserts `position_size`, `position_to_account_pct`, `reward_risk_ratio`, and `potential_profit`, directly covering the happy-path outputs computed in `packages/core/src/zorivest_core/domain/calculator.py:54,62-63`. |
| AV-4 | PASS | No `skip` / `xfail` usage in `tests/unit/test_calculator.py`. |
| AV-5 | PASS | Codex reran `rg "TODO|FIXME|NotImplementedError|pass\s+#\s*placeholder" packages/ tests/` and got no matches. |

### Banned Patterns

- `rg` output: clean

### FIC Coverage

| Criterion | Test(s) | Verified |
|-----------|---------|----------|
| AC-1 | `test_basic_calculation` | ✅ |
| AC-2 | `test_zero_entry_returns_zero_shares` | ✅ |
| AC-3 | `test_risk_out_of_range_defaults_to_one_percent`, `test_risk_zero_defaults_to_one_percent`, `test_risk_negative_defaults_to_one_percent` | ✅ |
| AC-4 | `test_entry_equals_stop` | ✅ |
| AC-5 | `test_zero_balance` | ✅ |
| AC-6 | `test_frozen_dataclass` | ✅ |
| AC-7 | `test_import_surface` | ✅ |

### Findings (if any)

- None.

### Verdict Rationale

All command-level validation passed, the implementation stayed within plan scope, and the Revision 1 assertions close the only previously reported proof gap. All AV items now pass and all FIC criteria are explicitly covered, so the MEU is approved.

### Verdict Confidence

- **Confidence**: HIGH
- **Justification**: The re-validation directly confirms the missing happy-path assertions were added and that the full scoped validation suite still passes. No unresolved correctness or architecture gaps remain in the reviewed scope.
