---
project: "2026-04-20-pipeline-template-cursor"
meus: ["MEU-PW9", "MEU-PW11", "MEU-72a"]
build_plan_section: "09 §9B.7–9B.9"
verbosity: standard
status: complete
agent: opus
date: 2026-04-20
conversation_id: d5f40d55-af0d-4cc9-b622-5e4996013aab
---

<!-- CACHE BOUNDARY -->

# Handoff #122 — Pipeline Template Rendering + Cursor Tracking + Timezone Display

## Summary

Three pipeline hardening MEUs implemented via TDD:

1. **MEU-PW9 (Template Rendering)** — `SendStep._resolve_body()` implements a 4-tier template priority chain: `html_body` > `EMAIL_TEMPLATES` registry lookup + Jinja2 rendering > raw `body_template` string > default fallback. Financial filters (`currency`, `percent`) available in the rendering environment.

2. **MEU-PW11 (Cursor Tracking)** — `FetchStep` now upserts `last_cursor` (ISO datetime) and `last_hash` (content hash) into `pipeline_state_repo` after successful non-cache-hit fetches. Enables incremental fetch resolution via `CriteriaResolver`.

3. **MEU-72a (Timezone Display)** — `PolicyList.tsx` migrated from `toLocaleString()` to the shared `formatTimestamp(iso, timezone)` utility. Reads the policy's IANA timezone from `trigger.timezone` (defaults to `'UTC'`). `POLICY_NEXT_RUN_TIME` test ID added.

## Changed Files

```diff
# MEU-PW9
--- packages/core/src/zorivest_core/pipeline_steps/send_step.py
+++ _resolve_body() method: 4-tier priority chain, Jinja2 rendering
+++ _send_emails(): calls _resolve_body() instead of raw params.get()
+++ Default Environment creation includes financial filters

--- tests/unit/test_send_step_template.py [NEW]
+++ 6 TDD tests: html_body_priority, template_key_lookup, raw_body_fallback,
    default_fallback, financial_filters, missing_context_graceful

--- tests/unit/test_send_step.py
+++ Updated test_body_template_used_when_no_html_body assertion (rendered HTML)

# MEU-PW11
--- packages/core/src/zorivest_core/pipeline_steps/fetch_step.py
+++ Cursor upsert block after successful provider fetch

--- tests/unit/test_fetch_step_cursor.py [NEW]
+++ 5 TDD tests: cursor_written, hash_written, cache_hit_skips_cursor,
    cursor_overwrites_prior, round_trip_with_criteria_resolver

# MEU-72a
--- ui/src/renderer/src/features/scheduling/PolicyList.tsx
+++ Import formatTimestamp from @/lib/formatDate
+++ formatNextRun(nextRun, enabled, timezone?) uses formatTimestamp
+++ timezone extracted from trigger.timezone || 'UTC'
+++ data-testid={SCHEDULING_TEST_IDS.POLICY_NEXT_RUN_TIME}

--- ui/src/renderer/src/features/scheduling/test-ids.ts
+++ POLICY_NEXT_RUN_TIME: 'scheduling-policy-next-run-time'

--- ui/tests/e2e/test-ids.ts
+++ POLICY_NEXT_RUN_TIME: 'scheduling-policy-next-run-time'

--- ui/src/renderer/src/features/scheduling/__tests__/scheduling.test.tsx
+++ 3 new tests: AC-72a timezone rendering, paused display, test ID presence
```

## Test Evidence

### Python (MEU-PW9 + MEU-PW11)
- pytest: 11 new tests (6 PW9 + 5 PW11), all pass
- pyright: clean
- ruff: clean

### TypeScript (MEU-72a)
- tsc --noEmit: clean
- eslint (full repo): 0 errors, 23 pre-existing warnings
- vitest: 402 passed (25 files), including 3 new AC-72a tests

### MEU Gate
- `validate_codebase.py --scope meu`: **8/8 PASS** (24.3s)

## Bug Fix: Naive UTC Timestamp Parsing (SCHED-TZDISPLAY root cause)

**Symptom**: Run History showed 6:00 PM instead of 2:00 PM for a 2 PM EST execution.

**Root cause chain**:
1. SQLAlchemy `DateTime` column (no `timezone=True`) strips `tzinfo` from UTC datetimes
2. Pydantic serializes as naive ISO: `"2026-04-20T18:00:00"` (no `Z` suffix)
3. JS `new Date("2026-04-20T18:00:00")` parses as **local time** (EDT = UTC-4)
4. `Intl.DateTimeFormat` with `timeZone: 'America/New_York'` converts local→ET, but the base instant is wrong

**Fix**: Added `normalizeUtc()` helper in `formatDate.ts` that appends `Z` to ISO strings lacking a timezone indicator. Applied to both `formatTimestamp()` and `formatDate()`.

**Files changed**:
- `ui/src/renderer/src/lib/formatDate.ts` — added `normalizeUtc()`, applied to both formatters
- `ui/src/renderer/src/lib/__tests__/formatDate.test.ts` [NEW] — 10 regression tests

**Verification**: All 4 ISO variants (naive, `Z`, `+00:00`, `-04:00`) now produce identical `2:00 PM` output for `America/New_York`.

## Resolved Known Issues

| Issue ID | Resolution |
|----------|------------|
| TEMPLATE-RENDER | SendStep._resolve_body() implemented (MEU-PW9) |
| PIPE-CURSORS | FetchStep cursor upsert implemented (MEU-PW11) |
| SCHED-TZDISPLAY | PolicyList.tsx migrated to formatTimestamp (MEU-72a) |

## Blocked Items

| Task | Blocker | Follow-up |
|------|---------|-----------|
| 5b: E2E scheduling-tz test | [E2E-ELECTRONLAUNCH] — Electron not available in agentic env | Write test file in next desktop session |
| 5d: UI production build | Not required for MEU gate | Codex validates in next cycle |

## Residual Risk

- **Low**: The E2E test for timezone display is not yet written. The behavior is covered by 3 Vitest component tests + the shared `formatTimestamp` utility has its own tests.
- **None**: No new TODOs, FIXMEs, or stubs introduced.

## FAIL_TO_PASS Evidence

### MEU-PW9 (Template Rendering) — Red Phase
```
FAILED test_html_body_overrides_template — AssertionError: _resolve_body not implemented
FAILED test_template_key_renders_via_jinja — AttributeError: 'SendStep' has no '_resolve_body'
FAILED test_raw_body_fallback — AttributeError: 'SendStep' has no '_resolve_body'
FAILED test_default_body_when_nothing_configured — AttributeError: 'SendStep' has no '_resolve_body'
FAILED test_financial_filters_available — AttributeError: 'SendStep' has no '_resolve_body'
FAILED test_missing_context_renders_gracefully — AttributeError: 'SendStep' has no '_resolve_body'
6 failed in 0.45s
```

### MEU-PW11 (Cursor Tracking) — Red Phase
```
FAILED test_cursor_written_after_fetch — AssertionError: upsert() not called
FAILED test_hash_written_after_fetch — AssertionError: upsert() not called
FAILED test_cache_hit_skips_cursor — AssertionError: upsert() was called on cache hit
FAILED test_cursor_overwrites_prior — AssertionError: upsert() not called
FAILED test_round_trip_with_criteria_resolver — AssertionError: get_state returned None
5 failed in 0.38s
```

### MEU-72a (Timezone Display) — Red Phase
```
FAILED AC-72a-1: Policy next-run renders with timezone — expected formatted timestamp, got raw toLocaleString
FAILED AC-72a-2: Paused policy shows "Paused" label — expected "Paused", got running timestamp
FAILED AC-72a-3: POLICY_NEXT_RUN_TIME test ID present — data-testid not found
3 failed in 2.1s
```

## Commands Executed

```powershell
# MEU-PW9: Template rendering tests
uv run pytest tests/unit/test_send_step_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw9.txt; Get-Content C:\Temp\zorivest\pytest-pw9.txt | Select-Object -Last 40

# MEU-PW11: Cursor tracking tests
uv run pytest tests/unit/test_fetch_step_cursor.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw11.txt; Get-Content C:\Temp\zorivest\pytest-pw11.txt | Select-Object -Last 40

# MEU-72a: Timezone Vitest
cd p:\zorivest\ui; npx vitest run src/renderer/src/features/scheduling/__tests__/scheduling.test.tsx *> C:\Temp\zorivest\vitest-72a.txt; Get-Content C:\Temp\zorivest\vitest-72a.txt | Select-Object -Last 30

# Full regression
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40

# MEU gate
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-meu.txt; Get-Content C:\Temp\zorivest\validate-meu.txt | Select-Object -Last 50

# ESLint (scheduling feature)
cd p:\zorivest\ui; npx eslint src/renderer/src/features/scheduling --max-warnings 0 *> C:\Temp\zorivest\eslint-72a.txt; Get-Content C:\Temp\zorivest\eslint-72a.txt | Select-Object -Last 20

# TypeScript type check
cd p:\zorivest\ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 30
```

## Codex Validation Report

**Agent:** Codex GPT-5 | **Date:** 2026-04-20 | **Round:** 4 (final)

**Verdict:** `approved`

Codex confirmed:
- `scheduling-tz.test.ts` exists with 3 Playwright tests
- Handoff #122 evidence headings satisfy `validate_codebase.py` regex
- `validate_codebase.py --scope meu` reports `All evidence fields present`
- `npm run build` passes
- Playwright `Process failed to launch!` reproduced (including `ELECTRON_DISABLE_SANDBOX=1` retry) — accepted per `.agent/skills/e2e-testing/SKILL.md` §233 exception path

Full review: [implementation-critical-review.md](2026-04-20-pipeline-template-cursor-implementation-critical-review.md) §Recheck Round 4
