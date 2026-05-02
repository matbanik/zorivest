# Reflection — Market Data Builders & Extractors

**Project:** Phase 8a Layer 2–3 (URL Builders + Extractors + Field Mappings)
**MEUs:** MEU-185, MEU-186, MEU-187, MEU-188
**Date:** 2026-05-02
**Completed:** 2026-05-02T16:54:00Z

---

## Session Summary

Implemented 9 new URL builder classes and 15+ response extractors with 30+ field mapping tuples across 4 MEUs in a single continuous TDD session. All 187 market-data-specific tests pass; full suite regression clean at 2654 passed.

## What Went Well

- **TDD rhythm was efficient**: Red-phase tests for each MEU caught real bugs (UnboundLocalError in CSV fallback path) before they could propagate.
- **Registry pattern scales cleanly**: Adding new providers follows a predictable pattern — builder class + extractor function + field mapping tuples.
- **Slug normalization**: The `_PROVIDER_SLUG_MAP` abstraction cleanly bridges display names to registry keys.

## What Could Improve

- **Slug computation ordering**: The `slug` variable was initially computed after the try/except block but referenced inside the except handler. Moving it before the block was a simple fix but could have been caught earlier with a more careful review of the control flow.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| CSV fallback in `extract_records` | Alpha Vantage earnings endpoint returns CSV, not JSON — parser must handle both |
| Prefix stripping helper | AV JSON keys have inconsistent `1.`/`01.` prefixes that must be normalized |
| Hoisting slug computation | Required for the CSV fallback path to know the provider identity |

---

## Addendum: Pipeline Approval Drift Fix (Ad-Hoc)

> Discovered during GUI testing of pipeline execution (2026-05-02T20:00Z–20:40Z). Not part of original MEU scope.

### What Happened

Two bugs prevented manual pipeline execution from the GUI:
1. **Missing CSRF token**: `triggerRun()` in `api.ts` didn't send `X-Approval-Token`, while `approvePolicy()` did.
2. **Content hash drift**: `compute_content_hash()` included `trigger.enabled` in the hash, causing `approved_hash ≠ content_hash` when toggling Draft→Ready→Scheduled.

### Decisions Made

| Decision | Rationale |
|----------|-----------|
| Centralize `enabled` normalization in `compute_content_hash()` | Single source of truth — every caller gets consistent hashes. The `patch_schedule()` method had its own ad-hoc normalization that diverged from the canonical function. |
| Normalize `enabled=True` (not strip it) | Preserves deterministic hash output. Stripping the field entirely would change hash semantics for all existing policies. |
| 8-point MCP + API security verification | Confirms the human-in-the-loop gate holds: no MCP, direct API, or fake token can approve or run a policy. |

### Files Changed

| File | Change |
|------|--------|
| `ui/src/renderer/src/features/scheduling/api.ts` | `triggerRun()` → IPC approval token |
| `packages/core/.../domain/policy_validator.py` | `compute_content_hash()` → normalize `trigger.enabled` |
| `packages/core/.../services/scheduling_service.py` | `patch_schedule()` → remove redundant normalization |

---

## Instruction Coverage Reflection

```yaml
schema: v1
session:
  id: 58efb12f-c094-412f-8331-5613f5d7a52b
  task_class: tdd
  outcome: success
  tokens_in: 0
  tokens_out: 0
  turns: 5
sections:
  - id: testing_tdd_protocol
    cited: true
    influence: 3
  - id: execution_contract
    cited: true
    influence: 3
  - id: session_discipline
    cited: true
    influence: 2
  - id: operating_model
    cited: true
    influence: 2
  - id: planning_contract
    cited: false
    influence: 1
loaded:
  workflows: [execution_session, create_plan]
  roles: [coder, tester, orchestrator, reviewer]
  skills: [terminal_preflight]
  refs: []
decisive_rules:
  - "P1:tests-first-implementation-after"
  - "P0:never-modify-tests-to-pass"
  - "P0:redirect-to-file-pattern"
  - "P1:evidence-first-completion"
  - "P1:anti-placeholder-enforcement"
conflicts: []
note: "4-MEU project completed in single session. Registry pattern made each MEU additive. Ad-hoc pipeline approval drift fix added post-completion."
```
