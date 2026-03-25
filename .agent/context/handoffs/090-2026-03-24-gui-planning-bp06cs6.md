---
meu: 70
slug: gui-planning-fix
phase: 6C
priority: P1
status: ready_for_review
agent: claude-opus-4-6
iteration: 1
files_changed: 2
tests_added: 0
tests_passing: 25
---

# MEU-70: Planning GUI — Fix Failures & Sign Off

## Scope

Resolved all pre-existing failures in the Planning GUI test suite and confirmed E2E Wave 4 gate passes. The `PositionCalculatorModal.tsx` was missing a `data-testid="calc-copy-shares-btn"` attribute on the copy-shares button (AC-C2); the test existed but the implementation was incomplete. No test assertions were modified.

Build plan reference: [06c-gui-planning.md](../../../../docs/build-plan/06c-gui-planning.md)

## Feature Intent Contract

### Intent Statement
All Planning GUI acceptance criteria are verifiably met in CI: test suite passes without modification of assertions, and the E2E position-size Wave 4 gate passes.

### Acceptance Criteria
- AC-C2 (Source: 06c-gui-planning.md): `data-testid="calc-copy-shares-btn"` present on copy-shares button in `PositionCalculatorModal.tsx`
- AC-SUITE: All 25+ planning test suites pass
- AC-E2E: `position-size.test.ts` E2E Wave 4 passes (2 tests)

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-C2 copy button | `planning/__tests__/planning.test.tsx` | `PositionCalculatorModal > copy-shares-btn present` |
| AC-SUITE | `planning/__tests__/planning.test.tsx` | All 25+ suites |
| AC-E2E Wave 4 | `tests/e2e/position-size.test.ts` | 2 tests |

## Design Decisions & Known Risks

- **Decision**: Added `data-testid` attribute only — no logic change — **Reasoning**: The button already existed and functioned; only the testid was missing. **ADR**: inline.
- **Source Basis**: `docs/build-plan/06c-gui-planning.md §C2`

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx` | Modified | Added `data-testid="calc-copy-shares-btn"` to copy-shares button |
| `.agent/context/meu-registry.md` | Modified | MEU-90a, MEU-90b, MEU-90d marked ✅ 2026-03-24 (status updates from same session) |

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `npx vitest run src/renderer/src/features/planning/__tests__/ --reporter=verbose` | PASS | All 25+ planning suites pass |
| `npx playwright test tests/e2e/position-size.test.ts --reporter=list` | PASS | 2/2 E2E tests pass |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `PositionCalculatorModal > copy-shares-btn testid` | FAIL (missing data-testid) | PASS |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
