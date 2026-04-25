---
project: "2026-04-25-pipeline-security-hardening"
source: "docs/execution/plans/2026-04-25-pipeline-security-hardening/implementation-plan.md"
meus: ["MEU-PH1", "MEU-PH2", "MEU-PH3"]
status: "in_progress"
template_version: "2.0"
---

# Task — P2.5c Pipeline Security Hardening

> **Project:** `2026-04-25-pipeline-security-hardening`
> **Type:** Domain
> **Estimate:** ~15 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | **PH1 FIC**: Write Feature Intent Contract with AC-1.1 through AC-1.9 | coder | FIC section in test file header docstring | Visual review of AC labels + source tags | `[x]` |
| 2 | **PH1 Tests (Red)**: Write 9 tests for StepContext isolation (AC-1.1–AC-1.9) | coder | `tests/unit/test_stepcontext_isolation.py` | `uv run pytest tests/unit/test_stepcontext_isolation.py -x --tb=short -v *> C:\Temp\zorivest\ph1-red.txt; Get-Content C:\Temp\zorivest\ph1-red.txt \| Select-Object -Last 40` — expect 9 FAILED | `[x]` |
| 3 | **PH1 Implement (Green)**: Create `safe_copy.py`, modify `pipeline.py` get_output/put_output | coder | `packages/core/src/zorivest_core/services/safe_copy.py`, modified `pipeline.py` | `uv run pytest tests/unit/test_stepcontext_isolation.py -x --tb=short -v *> C:\Temp\zorivest\ph1-green.txt; Get-Content C:\Temp\zorivest\ph1-green.txt \| Select-Object -Last 40` — expect 9 passed | `[x]` |
| 4 | **PH1 Runner migration**: Replace `context.outputs[x] = y` with `context.put_output(x, y)` at pipeline_runner.py L201, L240 | coder | Modified `pipeline_runner.py` | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\ph1-runner.txt; Get-Content C:\Temp\zorivest\ph1-runner.txt \| Select-Object -Last 40` — no regressions | `[x]` |
| 5 | **PH1 MEU gate** | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\ph1-gate.txt; Get-Content C:\Temp\zorivest\ph1-gate.txt \| Select-Object -Last 50` | `[x]` |
| 6 | **PH2 FIC**: Write Feature Intent Contract with AC-2.1 through AC-2.18 | coder | FIC section in test file header docstring | Visual review of AC labels + source tags | `[x]` |
| 7 | **PH2 Tests (Red)**: Write 22 tests for SQL sandbox, secrets scanning, content IDs (AC-2.1–AC-2.18) | coder | `tests/unit/test_sql_sandbox.py` | `uv run pytest tests/unit/test_sql_sandbox.py -x --tb=short -v *> C:\Temp\zorivest\ph2-red.txt; Get-Content C:\Temp\zorivest\ph2-red.txt \| Select-Object -Last 40` — expect 22 FAILED | `[x]` |
| 8 | **PH2 Implement (Green)**: Create `sql_sandbox.py`, add `open_sandbox_connection()` to `connection.py`, add secrets scan + content ID to `policy_validator.py` | coder | New/modified files per plan | `uv run pytest tests/unit/test_sql_sandbox.py -x --tb=short -v *> C:\Temp\zorivest\ph2-green.txt; Get-Content C:\Temp\zorivest\ph2-green.txt \| Select-Object -Last 40` — expect 22 passed | `[x]` |
| 9 | **PH2 Callsite migration**: Migrate `store_report_step.py`, `criteria_resolver.py`, `fetch_step.py` to use `sql_sandbox` | coder | Modified callsite files | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\ph2-callsites.txt; Get-Content C:\Temp\zorivest\ph2-callsites.txt \| Select-Object -Last 40` — no regressions | `[x]` |
| 10 | **PH2 Dependency**: Add `sqlglot` to `packages/core/pyproject.toml` | coder | Modified `packages/core/pyproject.toml` | `rg sqlglot packages/core/pyproject.toml *> C:\Temp\zorivest\ph2-dep.txt; Get-Content C:\Temp\zorivest\ph2-dep.txt` | `[x]` |
| 11 | **PH2 MEU gate** | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\ph2-gate.txt; Get-Content C:\Temp\zorivest\ph2-gate.txt \| Select-Object -Last 50` | `[x]` |
| 12 | **PH3 FIC**: Write Feature Intent Contract with AC-3.1 through AC-3.9 | coder | FIC section in test file header docstring | Visual review of AC labels + source tags | `[x]` |
| 13 | **PH3 Tests (Red)**: Write 9 tests for confirmation gates + content guards (AC-3.1–AC-3.9) | coder | `tests/unit/test_confirmation_gates.py` | `uv run pytest tests/unit/test_confirmation_gates.py -x --tb=short -v *> C:\Temp\zorivest\ph3-red.txt; Get-Content C:\Temp\zorivest\ph3-red.txt \| Select-Object -Last 40` — expect 9 FAILED | `[x]` |
| 14 | **PH3 Implement (Green)**: Create `approval_snapshot.py`, modify `send_step.py`, `fetch_step.py`, `pipeline_runner.py`, `pipeline.py` | coder | New/modified files per plan | `uv run pytest tests/unit/test_confirmation_gates.py -x --tb=short -v *> C:\Temp\zorivest\ph3-green.txt; Get-Content C:\Temp\zorivest\ph3-green.txt \| Select-Object -Last 40` — expect 9 passed | `[x]` |
| 15 | **PH3 MEU gate** | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\ph3-gate.txt; Get-Content C:\Temp\zorivest\ph3-gate.txt \| Select-Object -Last 50` | `[x]` |
| 16 | **Full regression** | tester | All tests pass, pyright clean, ruff clean | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt \| Select-Object -Last 40` | `[x]` |
| 17 | **Type check** | tester | 0 errors | `uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt \| Select-Object -Last 30` | `[x]` |
| 18 | **Lint** | tester | 0 warnings | `uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt \| Select-Object -Last 20` | `[x]` |
| 19 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | Evidence of clean grep | `rg "MEU-PH[123]" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-audit.txt; Get-Content C:\Temp\zorivest\buildplan-audit.txt` | `[x]` |
| 20 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-pipeline-security-2026-04-25` | MCP: `pomera_notes(action="search", search_term="Zorivest-pipeline-security*")` returns ≥1 result | `[x]` |
| 21 | Create handoff | reviewer | `.agent/context/handoffs/{SEQ}-2026-04-25-pipeline-security-bp09cs1-3.md` | `Test-Path .agent/context/handoffs/*pipeline-security*.md *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt` | `[x]` |
| 22 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-25-pipeline-security-reflection.md` | `Test-Path docs/execution/reflections/2026-04-25-pipeline-security-reflection.md *> C:\Temp\zorivest\reflection-check.txt; Get-Content C:\Temp\zorivest\reflection-check.txt` | `[x]` |
| 23 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md *> C:\Temp\zorivest\metrics.txt; Get-Content C:\Temp\zorivest\metrics.txt \| Select-Object -Last 3` | `[x]` |
| 24 | Update MEU registry status for PH1, PH2, PH3 | orchestrator | `.agent/context/meu-registry.md` rows updated to `done` | `rg "MEU-PH[123]" .agent/context/meu-registry.md *> C:\Temp\zorivest\meu-registry.txt; Get-Content C:\Temp\zorivest\meu-registry.txt` | `[x]` |
| 25 | Update `docs/build-plan/09c-pipeline-security-hardening.md` exit criteria for §9C.1d, §9C.2f, §9C.4d | orchestrator | No `- [ ]` remains in L109-115, L316-325, L419-425 | `rg "- \[ \]" docs/build-plan/09c-pipeline-security-hardening.md *> C:\Temp\zorivest\09c-unchecked.txt; Get-Content C:\Temp\zorivest\09c-unchecked.txt` — expect 0 matches in PH1-PH3 sections (PH4+ unchecked lines are acceptable) | `[x]` |
| 26 | Update `docs/BUILD_PLAN.md` PH1-PH3 index row status from `⬜` to `✅` | orchestrator | Rows at L372-374 show `✅` | `rg "MEU-PH[123]" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-index.txt; Get-Content C:\Temp\zorivest\buildplan-index.txt` | `[x]` |
| 27 | Update `.agent/context/current-focus.md` with session outcome | orchestrator | Current Priority and Next Steps reflect PH1-PH3 completion | `Get-Content .agent/context/current-focus.md *> C:\Temp\zorivest\current-focus.txt; Get-Content C:\Temp\zorivest\current-focus.txt` | `[x]` |

## Ad-Hoc: Pipeline Scheduling UX (out of MEU scope)

> Unplanned work completed during the PH3 session to resolve user-reported scheduling GUI issues.

| # | Task | Deliverable | Status |
|---|------|-------------|--------|
| B1 | Fix 422 on `+ New Policy` — add required `provider`/`data_type` to default template | Modified `SchedulingLayout.tsx` | `[x]` |
| B2 | Replace cycling status pill with 3-button segmented selector (Draft/Ready/Scheduled) | Modified `PolicyDetail.tsx`, `SchedulingLayout.tsx` | `[x]` |
| B3 | Rename `+ New` → `+ New Policy` | Modified `PolicyList.tsx` | `[x]` |
| B4 | Replace `window.confirm()` with themed dark modal via `createPortal` | Modified `PolicyDetail.tsx` | `[x]` |
| B5 | Normalize approval/scheduling lifecycle (decouple `enabled` from content hash) | Modified `scheduling_service.py` | `[x]` |
| B6 | Audit all GUI for remaining `window.confirm/alert/prompt` — 0 production hits | `rg` output | `[x]` |
| B7 | Add standards G20, G21, G22 to `emerging-standards.md` | Modified `.agent/docs/emerging-standards.md` | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
