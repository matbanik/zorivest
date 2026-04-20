---
project: "2026-04-20-pipeline-template-cursor"
date: "2026-04-20"
source: "docs/build-plan/09-scheduling.md"
meus: ["MEU-PW9", "MEU-PW11", "MEU-72a"]
status: "approved"
template_version: "2.0"
---

# Implementation Plan: Pipeline Template Rendering + Cursor Tracking

> **Project**: `2026-04-20-pipeline-template-cursor`
> **Build Plan Section(s)**: 09 §9.8a (SendStep impl), 09 §9.4b (CriteriaResolver incremental), 06e Schedule Detail Fields (timezone)
> **Status**: `approved`

---

## Goal

Three pipeline gaps prevent production-ready email delivery and incremental fetching:

1. **[TEMPLATE-RENDER]** — `SendStep` treats `body_template` as a raw literal string instead of performing `EMAIL_TEMPLATES` registry lookup + Jinja2 rendering. All pipeline emails arrive as plain text.
2. **[PIPE-CURSORS]** — `FetchStep` ignores `PipelineStateModel` cursors; every fetch is a full pull, increasing API costs and latency.
3. **[SCHED-TZDISPLAY]** — `PolicyList.formatNextRun()` uses browser-local `toLocaleString` instead of the shared `formatTimestamp` utility with IANA timezone support.

---

## User Review Required

> [!IMPORTANT]
> **No breaking changes.** All three MEUs are backward-compatible. New behavior activates only when `body_template` matches a registered template name (PW9) or when criteria use `type: "incremental"` (PW11).

> [!IMPORTANT]
> **MEU-72a is TypeScript-only (UI).** No backend changes. Verification: `npx tsc --noEmit` (type safety) + E2E Playwright test asserting timezone-aware timestamp display in `PolicyList` (extends existing `ui/tests/e2e/scheduling.test.ts`).

---

## Proposed Changes

### MEU-PW9: Template Rendering Wiring

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Pipeline step params | `SendStep.Params` (Pydantic) | `body_template: str`, `html_body: Optional[str]` | Inherited from MEU-88 |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `body_template="daily_quote_summary"` → rendered HTML with `<table>`, `Zorivest Daily Quote Report` | Local Canon (template registry design) | N/A (positive) |
| AC-2 | `body_template="generic_report"` → rendered HTML with template title | Local Canon (template registry design) | N/A (positive) |
| AC-3 | `body_template="nonexistent_template"` → body = raw string fallback | Local Canon (graceful degradation) | N/A (graceful fallback) |
| AC-4 | `html_body` provided alongside `body_template` → `html_body` takes priority | Local Canon (priority chain not in spec) | N/A (priority test) |
| AC-5 | No `body_template`, no `html_body` → fallback `"<p>Report attached</p>"` | Local Canon | N/A (fallback) |
| AC-6 | Missing `template_engine` in context → default Environment, no crash | Research-backed (Jinja2 docs) | N/A (graceful degradation) |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| `body_template` field exists on SendStep.Params | Spec 09 §9.8a line 2211 | Field exists; rendering logic is Local Canon |
| Template registry lookup | Local Canon | `EMAIL_TEMPLATES` dict keyed by name |
| Priority: html_body > template > raw > fallback | Local Canon | Explicit priority chain in `_resolve_body()` |
| Template context variables | Local Canon | `generated_at`, `policy_id`, `run_id` + context outputs |
| Graceful fallback on missing engine | Research-backed | Create default `Environment()` if not injected |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/pipeline_steps/send_step.py` | modify | Add `_resolve_body()` method; replace inline html_body resolution |
| `tests/unit/test_send_step_template.py` | new | 6 TDD tests for template resolution + fallback paths |

---

### MEU-PW11: Pipeline Cursor Tracking

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| PipelineStateModel write | `PipelineStateRepository.upsert()` | `last_cursor: str` (ISO datetime), `last_hash: str` (SHA-256 hex) | N/A (internal write) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | Successful fetch → `upsert()` called with correct `policy_id`, `provider_id`, `data_type`, `entity_key`, `last_hash` | Local Canon (cursor *write* not specified in spec; spec §9.4b only specifies *read*) | N/A (positive) |
| AC-2 | No `pipeline_state_repo` in context → no error, no call | Local Canon | N/A (optional dep) |
| AC-3 | Cache hit → pipeline state NOT updated | Research-backed | N/A (skip path) |
| AC-4 | `last_cursor` = valid ISO datetime string parsable by `fromisoformat` | Spec 09 §9.4b line 1499 (reads `state.last_cursor`) | Invalid cursor → `fromisoformat` ValueError |
| AC-5 | Round-trip: fetch writes cursor → CriteriaResolver reads cursor → `start_date` = cursor timestamp | Spec 09 §9.4b lines 1491-1499 (incremental resolve) | N/A (integration) |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Cursor read = ISO timestamp | Spec 09 §9.4b line 1499 | `CriteriaResolver._resolve_incremental` parses via `fromisoformat` |
| Cursor write after fetch | Local Canon | Symmetric design: if spec reads cursor, something must write it |
| Hash = SHA-256 of content | Local Canon (PipelineStateModel.last_hash exists) | Reuse `FetchResult.content_hash` |
| Entity key computation | Local Canon | Reuse `_compute_entity_key()` from fetch_step.py |
| Write after cache upsert only | Research-backed | Ensures cache+state consistency |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py` | modify | Add `pipeline_state_repo.upsert()` after cache upsert |
| `tests/unit/test_fetch_step_cursor.py` | new | 5 TDD tests for cursor write/skip/round-trip |

---

### MEU-72a: Scheduling GUI Timezone Polish

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `PolicyList` timestamps display in each policy's configured IANA timezone | Local Canon (known issue [SCHED-TZDISPLAY]; 06e line 112 defines timezone input field, display behavior is local canon) | N/A |
| AC-2 | Consistent with `RunHistory` and `PolicyDetail` formatting | Local Canon | N/A |
| AC-3 | Naive ISO strings from SQLAlchemy (no `Z` suffix) parse as UTC, not browser-local time | Research-backed (JS `Date` spec; MDN `Date.parse`; SQLAlchemy `DateTime(timezone=False)` behavior) | Naive `"2026-04-20T18:00:00"` renders same as `"2026-04-20T18:00:00Z"` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `ui/src/renderer/src/features/scheduling/PolicyList.tsx` | modify | Replace `toLocaleString` with `formatTimestamp` from `@/lib/formatDate`; extract `trigger.timezone` |
| `ui/src/renderer/src/features/scheduling/RunHistory.tsx` | modify | Add `timezone` to `useMemo` dependency array (ESLint `react-hooks/exhaustive-deps` fix) |
| `ui/src/renderer/src/lib/formatDate.ts` | modify | Add `normalizeUtc()` helper — appends `Z` to naive ISO strings; apply to `formatTimestamp()` and `formatDate()` |
| `ui/src/renderer/src/lib/__tests__/formatDate.test.ts` | new | 10 regression tests for UTC normalization (4 ISO variants × naive/explicit-Z/offset) |
| `ui/src/renderer/src/features/scheduling/__tests__/scheduling.test.tsx` | modify | 3 new AC-72a tests (timezone rendering, paused display, test ID presence) |
| `ui/src/renderer/src/features/scheduling/test-ids.ts` | modify | Add `POLICY_NEXT_RUN_TIME` test ID |
| `ui/tests/e2e/test-ids.ts` | modify | Add `POLICY_NEXT_RUN_TIME` test ID |
| `ui/tests/e2e/scheduling-tz.test.ts` | new | E2E test for timezone display — **blocked by [E2E-ELECTRONLAUNCH]** |

---

## Out of Scope

- MEU-PW10 (E2E integration tests) — gated by Codex approval
- URL builder fixes ([PIPE-URLBUILD]) — separate MEU-PW6 (already approved)
- GUI cancel button ([PIPE-NOCANCEL]) — separate MEU scope

---

## BUILD_PLAN.md Audit

MEU-PW9, PW11, 72a entries were added to `BUILD_PLAN.md` §P2.5b and `.agent/context/meu-registry.md` as part of plan corrections (2026-04-20).

```powershell
rg "PW9|PW11|72a" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-audit.txt; Get-Content C:\Temp\zorivest\bp-audit.txt  # Expected: 3+ matches
```

---

## Verification Plan

### 1. Unit Tests (per MEU)
```powershell
uv run pytest tests/unit/test_send_step_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw9.txt; Get-Content C:\Temp\zorivest\pytest-pw9.txt | Select-Object -Last 40
uv run pytest tests/unit/test_fetch_step_cursor.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw11.txt; Get-Content C:\Temp\zorivest\pytest-pw11.txt | Select-Object -Last 40
```

### 2. Full Regression
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt | Select-Object -Last 40
```

### 3. Type Checks
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 4. Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 5. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### 6. TypeScript (MEU-72a)
```powershell
cd p:\zorivest\ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 30
```

### 7. ESLint (MEU-72a)
```powershell
cd p:\zorivest\ui; npx eslint src/renderer/src/features/scheduling --max-warnings 0 *> C:\Temp\zorivest\eslint.txt; Get-Content C:\Temp\zorivest\eslint.txt | Select-Object -Last 20
```

### 8. Vitest Unit (MEU-72a)
```powershell
cd p:\zorivest\ui; npx vitest run src/renderer/src/features/scheduling/__tests__/PolicyList.test.tsx *> C:\Temp\zorivest\vitest-72a.txt; Get-Content C:\Temp\zorivest\vitest-72a.txt | Select-Object -Last 30
```

### 9. E2E Scheduling Timezone (MEU-72a)
```powershell
cd p:\zorivest\ui; npx playwright test tests/e2e/scheduling-tz.test.ts *> C:\Temp\zorivest\e2e-tz.txt; Get-Content C:\Temp\zorivest\e2e-tz.txt | Select-Object -Last 30
```

### 10. UI Production Build (MEU-72a)
```powershell
cd p:\zorivest\ui; npm run build *> C:\Temp\zorivest\ui-build.txt; Get-Content C:\Temp\zorivest\ui-build.txt | Select-Object -Last 20
```

---

## Open Questions

None — all three MEUs are well-scoped with clear acceptance criteria.

---

## Research References

- [Template rendering gap analysis](file:///p:/zorivest/.agent/context/scheduling/template_rendering_gap_analysis.md)
- [Data flow gap analysis](file:///p:/zorivest/.agent/context/scheduling/data_flow_gap_analysis.md)
- [Pipeline E2E harness reflection](file:///p:/zorivest/docs/execution/reflections/2026-04-20-pipeline-e2e-harness-reflection.md)
