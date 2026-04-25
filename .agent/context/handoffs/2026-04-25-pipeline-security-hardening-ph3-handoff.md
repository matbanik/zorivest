# Pipeline Security Hardening — PH3 Handoff

**Date**: 2026-04-25
**Project**: P2.5c Pipeline Security Hardening (MEU-PH1 → PH3)
**Build Plan Ref**: `docs/build-plan/09c-pipeline-security-hardening.md` §9C.3–9C.4

---

## Scope

MEU-PH3 (`send-fetch-guards`): SendStep confirmation gate + FetchStep MIME/fan-out validation.

## Changed Files

```diff
+ packages/core/src/zorivest_core/domain/approval_snapshot.py  [NEW]
  packages/core/src/zorivest_core/domain/pipeline.py           [MODIFY: StepContext PH3 fields]
  packages/core/src/zorivest_core/pipeline_steps/send_step.py  [MODIFY: PolicyExecutionError + gate]
  packages/core/src/zorivest_core/pipeline_steps/fetch_step.py [MODIFY: MIME/size/URL guards]
  packages/core/src/zorivest_core/services/pipeline_runner.py  [MODIFY: URL cap + policy_hash injection]
+ tests/unit/test_confirmation_gates.py                         [NEW: 9 tests]
  docs/BUILD_PLAN.md                                           [MODIFY: MEU-PH1/2/3 → ✅]
```

## Evidence Bundle

| Check | Result | Command |
|-------|--------|---------|
| PH3 unit tests | 9 passed | `pytest tests/unit/test_confirmation_gates.py` |
| Full regression | 2227 passed, 23 skipped | `pytest tests/` |
| Pyright | 0 errors | `pyright packages/` |
| Ruff | All checks passed | `ruff check packages/` |
| Anti-placeholder | Clean (abstract base only) | `rg "TODO\|FIXME\|NotImplementedError" packages/` |

## Design Decisions

1. **Backward-compatible gate**: `requires_confirmation=False` + no snapshot = legacy pass (no gate enforcement). This preserves existing integration test behavior while enforcing the gate when approval snapshots are injected by PipelineRunner.

2. **PolicyExecutionError**: New exception class in `send_step.py` — distinct from Pydantic `ValidationError` and `SecurityError`. Used exclusively for confirmation gate violations.

3. **Pydantic `max_length=5`**: FetchStep `urls` field uses Pydantic's `max_length` constraint for immediate validation at params parse time, plus a redundant runtime check for defense-in-depth.

## Residual Risk

- None for PH3 scope. All ACs verified.
- MEU-PH4 through PH10 remain in P2.5c backlog.

---

## Ad-Hoc: Pipeline Scheduling UX (out of MEU scope)

> Unplanned fixes completed during this session to resolve user-reported scheduling GUI issues.

### Changed Files

```diff
  ui/src/renderer/src/features/scheduling/SchedulingLayout.tsx  [MODIFY: default template params + state selector]
  ui/src/renderer/src/features/scheduling/PolicyDetail.tsx       [MODIFY: portal modal + segmented selector]
  ui/src/renderer/src/features/scheduling/PolicyList.tsx         [MODIFY: button rename]
  packages/core/src/zorivest_core/services/scheduling_service.py [MODIFY: enabled/approval decoupling]
  .agent/docs/emerging-standards.md                              [MODIFY: +G20, +G21, +G22]
```

### Fixes Applied

| # | Fix | Root Cause |
|---|-----|------------|
| B1 | 422 on `+ New Policy` creation | Default template `params: {}` missing required `provider`/`data_type` fields |
| B2 | Cycling status pill → 3-button direct selector | Cycling UX confused users; couldn't select desired state directly |
| B3 | `+ New` → `+ New Policy` | Label too generic |
| B4 | `window.confirm()` → themed portal modal | Native OS dialog ignores dark theme |
| B5 | `enabled` decoupled from content hash | Toggling scheduling reset approval state |

### Native Dialog Audit

```
rg "window.confirm|window.alert|window.prompt" ui/src/
→ 0 production hits (1 test-only reference in scheduling.test.tsx:595)
```

### Standards Added

- **G20**: Themed portaled modals, not native dialogs
- **G21**: Direct selection, not cycling, for segmented state controls
- **G22**: Default templates must satisfy backend validation schemas
