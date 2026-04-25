# P2.5c Security Hardening — Reflection

**Date**: 2026-04-25
**MEUs Completed**: PH1 (stepcontext-safety), PH2 (sql-sandbox), PH3 (send-fetch-guards)

## What Went Well

1. **TDD cycle was clean**: Red → Green → Refactor worked smoothly. All 9 tests failed in Red, all 9 passed in Green, and no test assertions were modified.

2. **Backward compatibility awareness**: Catching the integration test regression early (within 2 minutes of implementation) prevented a cascade. The legacy-mode design decision was the right call.

3. **StepContext dataclass fields**: Adding PH3 fields directly to the dataclass (rather than dynamic `setattr`) gave immediate pyright coverage and clean test construction.

## What Could Be Improved

1. **Async test pattern**: Initial tests used deprecated `asyncio.get_event_loop().run_until_complete()`, which caused ordering-dependent failures in the full suite. Should have used `@pytest.mark.asyncio` from the start — this is the established pattern in the codebase.

2. **AC-3.4 spec interpretation**: The original FIC specified "requires_confirmation=False + no snapshot → error", but this broke backward compatibility. The spec was adjusted to "legacy pass" mode. Future FICs should include a backward-compatibility analysis for any gate that affects existing callers.

3. **Default template validation**: The `+ New Policy` button shipped with empty `params: {}` that failed backend validation (422). Default templates should be validated against the backend schema before shipping — this is now codified as standard G22.

## Ad-Hoc Fixes (Out of MEU Scope)

During PH3 implementation, the user exercised the scheduling GUI and surfaced 5 UX issues. These were resolved in-session:

| Fix | Summary | Standard Added |
|-----|---------|----------------|
| B1 | 422 on policy creation — default template missing required `FetchStep.Params` fields | G22 |
| B2 | Status cycling pill replaced with 3-button direct-select segmented selector | G21 |
| B3 | `+ New` renamed to `+ New Policy` | — |
| B4 | Native `window.confirm()` replaced with themed portal-based modal | G20 |
| B5 | `enabled` flag decoupled from content hash to prevent approval resets | — |

**Native dialog audit**: `rg "window.confirm\|window.alert\|window.prompt" ui/src/` confirmed 0 production hits (1 test-only reference remains in `scheduling.test.tsx:595`).

## Metrics

| Metric | Value |
|--------|-------|
| Tests written (PH3) | 9 |
| Tests passed (PH3) | 9/9 |
| Files created | 2 |
| Files modified (PH3 core) | 4 |
| Files modified (ad-hoc UX) | 4 |
| Full suite | 2227 passed |
| Pyright errors | 0 |
| Ruff warnings | 0 |
| Standards added | G20, G21, G22 |
