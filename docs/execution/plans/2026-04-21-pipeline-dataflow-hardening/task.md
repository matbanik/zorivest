---
project: "2026-04-21-pipeline-dataflow-hardening"
source: "docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/implementation-plan.md"
meus: ["MEU-PW12", "MEU-PW13"]
status: "complete"
template_version: "2.0"
---

# Task — Pipeline Data-Flow Hardening

> **Project:** `2026-04-21-pipeline-dataflow-hardening`
> **Type:** Infrastructure
> **Estimate:** 11 files changed (5 production, 6 test)

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | TDD: Write tests for response_extractors (AC-2) | coder | `tests/unit/test_response_extractors.py` [NEW] | `uv run pytest tests/unit/test_response_extractors.py -x --tb=short -v` — all FAIL (Red) | `[x]` |
| 2 | Implement response_extractors (AC-2) | coder | `packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py` [NEW] | `uv run pytest tests/unit/test_response_extractors.py -x --tb=short -v` — all PASS (Green) | `[x]` |
| 3 | TDD: Write tests for provider slug normalization + extended mappings (AC-3, AC-4) | coder | `tests/unit/test_field_mappings.py` [MODIFY] | `uv run pytest tests/unit/test_field_mappings.py -x --tb=short -v` — new tests FAIL | `[x]` |
| 4 | Implement field_mappings changes (AC-3, AC-4) | coder | `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py` [MODIFY] | `uv run pytest tests/unit/test_field_mappings.py -x --tb=short -v` — all PASS | `[x]` |
| 5 | TDD: Write tests for TransformStep param changes (AC-1, AC-5, AC-6, AC-8) | coder | `tests/unit/test_transform_step_pw12.py` [NEW] | `uv run pytest tests/unit/test_transform_step_pw12.py -x --tb=short -v` — all FAIL (Red) | `[x]` |
| 6 | Implement TransformStep changes (AC-1, AC-5, AC-6, AC-8) | coder | `packages/core/src/zorivest_core/pipeline_steps/transform_step.py` [MODIFY] | `uv run pytest tests/unit/test_transform_step_pw12.py tests/unit/test_transform_step.py -x --tb=short -v` — all PASS | `[x]` |
| 7 | TDD: Write tests for SendStep template context promotion (AC-7) | coder | `tests/unit/test_send_step_template.py` [MODIFY] | `uv run pytest tests/unit/test_send_step_template.py -x --tb=short -v` — new tests FAIL | `[x]` |
| 8 | Implement SendStep two-level merge (AC-7) | coder | `packages/core/src/zorivest_core/pipeline_steps/send_step.py` [MODIFY] | `uv run pytest tests/unit/test_send_step_template.py -x --tb=short -v` — all PASS | `[x]` |
| 9 | TDD: Write tests for boundary param validation (AC-9) | coder | `tests/unit/test_policy_validator.py` [MODIFY] | `uv run pytest tests/unit/test_policy_validator.py -x --tb=short -v` — new tests FAIL | `[x]` |
| 10 | Implement policy_validator rule 7: per-step param validation (AC-9) | coder | `packages/core/src/zorivest_core/domain/policy_validator.py` [MODIFY] | `uv run pytest tests/unit/test_policy_validator.py -x --tb=short -v` — all PASS | `[x]` |
| 11 | Run existing test regression | tester | No regressions | `uv run pytest tests/unit/test_transform_step.py tests/unit/test_field_mappings.py tests/unit/test_send_step_template.py tests/unit/test_policy_validator.py -x --tb=short -v` — all PASS | `[x]` |
| 12 | TDD: Write integration tests (AC-E2E-1 through AC-E2E-6) — Red phase | coder | `tests/integration/test_pipeline_dataflow.py` [NEW] | `uv run pytest tests/integration/test_pipeline_dataflow.py -x --tb=short -v` — all FAIL (Red) | `[x]` |
| 13 | Green phase: verify chain passes with PW12 fixes + 3 production bug fixes | tester | Same file | `uv run pytest tests/integration/test_pipeline_dataflow.py -x --tb=short -v` — 7 PASS | `[x]` |
| 14 | Pyright clean | tester | 0 errors | `uv run pyright packages/` — 0 errors, 0 warnings, 0 informations | `[x]` |
| 15 | Ruff clean | tester | 0 errors | `uv run ruff check packages/` — All checks passed! | `[x]` |
| 16 | Anti-placeholder scan | tester | 0 matches | `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/pipeline_steps/ packages/infrastructure/src/zorivest_infra/market_data/` — 0 matches | `[x]` |
| 17 | MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu` — 8/8 blocking checks passed (24.98s) | `[x]` |
| 18 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | PW12/PW13 updated from ⬜ to ✅ in BUILD_PLAN.md L335-336 | Verified: `rg "MEU-PW12\|MEU-PW13" docs/BUILD_PLAN.md` shows ✅ | `[x]` |
| 19 | Update `meu-registry.md` | orchestrator | MEU-PW12 + MEU-PW13 rows added | `rg "MEU-PW12\|MEU-PW13" .agent/context/meu-registry.md` — 2 matches | `[x]` |
| 20 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-dataflow-hardening-2026-04-21` (ID: 880) | Pomera note saved | `[x]` |
| 21 | Create handoff for MEU-PW12 + MEU-PW13 | reviewer | `123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md` | `Test-Path .agent/context/handoffs/123-*` — True | `[x]` |
| 22 | _(merged with #21 — combined handoff)_ | — | — | — | `[x]` |
| 23 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-21-pipeline-dataflow-hardening-reflection.md` | File exists | `[x]` |
| 24 | Append metrics row | orchestrator | Row 57 appended to `docs/execution/metrics.md` | Row present | `[x]` |
| 25 | Prepare commit messages | orchestrator | See below | N/A | `[x]` |

### Commit Messages

```
feat(pipeline): fix data-flow chain — slug normalization, WARNING output persistence

- response_extractors: add _PROVIDER_SLUG_MAP to resolve display names to registry keys
- pipeline_runner: store output for WARNING + SUCCESS statuses (downstream steps need data)
- transform_step: remove unused json import (ruff F401)
- response_extractors: remove unused logging import (ruff F401)
- test_scheduling_service: make _DummyParams a BaseModel with extra="allow" for PW12 compat

7 integration tests verify full Fetch→Transform→Send chain (email channel, mocked SMTP)
2154 tests pass, 0 pyright errors, 0 ruff violations

MEU-PW12, MEU-PW13
```

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |

## Production Bug Fixes Discovered During PW13 Integration Testing

Three production bugs were discovered and fixed during the PW13 Green phase:

1. **WARNING output not stored in pipeline context** — `pipeline_runner.py` only stored step output for `SUCCESS`, causing TransformStep WARNING results to be invisible to downstream steps. Fixed by including `PipelineStatus.WARNING` in the output storage condition.

2. **Response extractor slug normalization missing** — `response_extractors.py:extract_records()` used raw provider display names (e.g., "Yahoo Finance") for registry lookups, but extractors were registered under slugs (e.g., "yahoo"). Added `_PROVIDER_SLUG_MAP` normalization before lookup.

3. **Scheduling test fixture incompatible with PW12 boundary validation** — `test_scheduling_service.py::_DummyParams` was a plain class that couldn't accept constructor kwargs, causing `TypeError` when `policy_validator._check_step_params()` tried to instantiate it. Fixed by making it a Pydantic `BaseModel` with `extra="allow"`.
