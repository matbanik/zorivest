---
project: "2026-04-20-pipeline-e2e-harness"
source: "docs/execution/plans/2026-04-20-pipeline-e2e-harness/implementation-plan.md"
meus: ["MEU-PW8"]
status: "complete"
template_version: "2.0"
---

# Task — Pipeline E2E Test Harness

> **Project:** `2026-04-20-pipeline-e2e-harness`
> **Type:** Infrastructure/Tests + Bug Fixes + Diagnostic Analysis
> **Estimate:** 5 files changed (4 new, 1 modified) + 2 production fixes + 2 gap analysis reports

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Create `tests/fixtures/__init__.py` | coder | Empty package init | `Test-Path tests/fixtures/__init__.py` | `[x]` |
| 2 | Create `tests/fixtures/policies.py` with 7 policy fixtures | coder | 7 named dict constants matching §9B.6b | `uv run python -c "from tests.fixtures.policies import SMOKE_POLICY_BASIC; print('OK')" *> C:\Temp\zorivest\fixtures-import.txt; Get-Content C:\Temp\zorivest\fixtures-import.txt` | `[x]` |
| 3 | Create `tests/fixtures/mock_steps.py` with 6 mock step classes | coder | 6 RegisteredStep subclasses matching §9B.6c | `uv run python -c "from tests.fixtures.mock_steps import MockFetchStep; print('OK')" *> C:\Temp\zorivest\mocksteps-import.txt; Get-Content C:\Temp\zorivest\mocksteps-import.txt` | `[x]` |
| 4 | Add pipeline service stack fixtures to `tests/conftest.py` | coder | UoW + adapters + SchedulingService + PipelineRunner fixtures with mock step cleanup | `uv run pytest tests/integration/test_pipeline_e2e.py --collect-only *> C:\Temp\zorivest\collect.txt; Get-Content C:\Temp\zorivest\collect.txt \| Select-Object -Last 20` | `[x]` |
| 5 | Write FIC-based tests (RED phase) in `tests/integration/test_pipeline_e2e.py` | coder | 19 tests across 8 classes (AC-4 through AC-22) | `uv run pytest tests/integration/test_pipeline_e2e.py -v *> C:\Temp\zorivest\e2e-red.txt; Get-Content C:\Temp\zorivest\e2e-red.txt \| Select-Object -Last 30` | `[x]` |
| 6 | Implement test logic (GREEN phase) — make all tests pass | coder | 19/19 passing. Fixed 3 production bugs: (1) ref paths `ctx.X.output.Y` → `ctx.X.Y`, (2) `logger.log(str)` → `getattr(logger, severity)()`, (3) `_safe_json_output({})` None → `'{}'` | `uv run pytest tests/integration/test_pipeline_e2e.py -v *> C:\Temp\zorivest\e2e-green.txt; Get-Content C:\Temp\zorivest\e2e-green.txt \| Select-Object -Last 30` | `[x]` |
| 7 | Run full regression suite | tester | 2087 passed, 15 skipped, 0 failed | `uv run pytest tests/ -x --tb=short -q *> C:\Temp\zorivest\regression.txt; Get-Content C:\Temp\zorivest\regression.txt \| Select-Object -Last 20` | `[x]` |
| 8 | Run type check | tester | 0 errors, 0 warnings (`pyright packages/` — MEU scope) | `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30` | `[x]` |
| 9 | Run lint | tester | 0 errors (after F1 corrections: 4 unused import/variable fixes) | `uv run ruff check packages/ tests/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` | `[x]` |
| 10 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | Update MEU-PW8 status ⬜→🟡 | `rg "MEU-PW8" docs/BUILD_PLAN.md` | `[x]` |
| 11 | Run MEU gate | tester | 8/8 blocking checks passed (pyright, ruff, pytest, tsc, eslint, vitest, anti-placeholder, anti-deferral) | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 12 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-pipeline-e2e-harness-2026-04-20` (Note ID: 858) | `pomera_notes(action="search", search_term="Zorivest-pipeline-e2e*")` | `[x]` |
| 13 | Create handoff | reviewer | [121-2026-04-20-pipeline-e2e-harness-bp09bs9B.6.md](file:///p:/zorivest/.agent/context/handoffs/121-2026-04-20-pipeline-e2e-harness-bp09bs9B.6.md) | `Test-Path .agent/context/handoffs/121-2026-04-20-pipeline-e2e-harness-bp09bs9B.6.md` | `[x]` |
| 14 | Create reflection | orchestrator | [2026-04-20-pipeline-e2e-harness-reflection.md](file:///p:/zorivest/docs/execution/reflections/2026-04-20-pipeline-e2e-harness-reflection.md) | `Test-Path docs/execution/reflections/2026-04-20-pipeline-e2e-harness-reflection.md` | `[x]` |
| 15 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` (line 56) | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[x]` |

## Bug Fixes Completed (Discovered During Live GUI Testing)

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| BF-1 | Fix dedup key fallback when `snapshot_hash` is absent | coder | `send_step.py:124-133` — fallback to `context.run_id` when `snapshot_hash` missing | TDD: `test_dedup_key_fallback_to_run_id` passes | `[x]` |
| BF-2 | Wire SMTP `security` field into runtime config | coder | `email_provider_service.py` + `test_smtp_runtime_config.py` + `test_pipeline_wiring.py` — include `security` in config dict keys | TDD: `test_smtp_config_includes_security_field` passes | `[x]` |

## Diagnostic Reports (Requested by User)

| # | Task | Owner | Deliverable | Status |
|---|------|-------|-------------|--------|
| DA-1 | Template rendering gap analysis | researcher | [template_rendering_gap_analysis.md](file:///p:/zorivest/.agent/context/scheduling/template_rendering_gap_analysis.md) — identified 3-layer disconnection: `EMAIL_TEMPLATES` registry unused, `template_engine` unread by SendStep, `body_template` treated as literal string | `[x]` |
| DA-2 | Data flow gap analysis (fetch → transform → store) | researcher | [data_flow_gap_analysis.md](file:///p:/zorivest/.agent/context/scheduling/data_flow_gap_analysis.md) — mapped full pipeline trigger flow, catalogued 48 planned use cases, identified 8 test coverage gaps | `[x]` |
| DA-3 | Register new discoveries in `known-issues.md` | orchestrator | 4 new issues: TEMPLATE-RENDER, PIPE-E2E-CHAIN, PIPE-CACHEUPSERT, PIPE-CURSORS | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
