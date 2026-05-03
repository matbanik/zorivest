# Reflection: GUI UX Hardening — 2026-05-02

## Project Scope
MEU-196 (shared infra), MEU-197 (settings guard), MEU-198 (CRUD guard)

## What Went Well
- Shared hook + modal architecture enabled rapid rollout across 6 modules
- forwardRef/useImperativeHandle pattern cleanly solved the parent-child save orchestration
- All 522 tests green, 0 TSC errors after full rollout + corrections + page-level guard tests + E2E dirty-guard scenarios

## What Could Improve
- Implementation preceded tests for module wiring (tasks 10-20). TDD inversion means test tasks can't demonstrate RED→GREEN.
- Task tracking fell behind — 11 tasks were done before any were marked `[x]` in task.md
- Task 7 (shared component refactor for Scheduling) was superseded by 7a, then restored during corrections (F2) — refactored to shared `useFormGuard` + `UnsavedChangesModal`

## Key Metrics
- **Files created**: 5 (hook, modal, CSS, 2 test files)
- **Files modified**: 11 (6 feature pages, 4 detail panels, test-ids)
- **Tests**: 522 passed / 0 failed (20 G22/G23 dirty-guard vitest + 3 E2E Playwright dirty-guard scenarios)
- **TSC**: 0 errors

## Instruction Coverage
```yaml
instruction_coverage:
  version: v1
  session_date: "2026-05-02"
  project: gui-ux-hardening
  coverage:
    - rule: "TDD first"
      status: partial
      note: "Hook + modal tests written first. Module wiring tests deferred."
    - rule: "Anti-premature-stop"
      status: compliant
    - rule: "Redirect-to-file"
      status: compliant
    - rule: "No unsourced best-practice"
      status: compliant
    - rule: "Evidence-first completion"
      status: compliant
      note: "All [x] tasks have validation evidence"
```
