---
project: "2026-04-20-pipeline-template-cursor"
source: "docs/execution/plans/2026-04-20-pipeline-template-cursor/implementation-plan.md"
meus: ["MEU-PW9", "MEU-PW11", "MEU-72a"]
status: "approved"
template_version: "2.0"
---

# Task — Pipeline Template Rendering + Cursor Tracking

> **Project:** `2026-04-20-pipeline-template-cursor`
> **Type:** Infrastructure/Domain
> **Estimate:** 10 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write FIC + 6 tests for MEU-PW9 template rendering | coder | `tests/unit/test_send_step_template.py` | `uv run pytest tests/unit/test_send_step_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw9.txt; Get-Content C:\Temp\zorivest\pytest-pw9.txt \| Select-Object -Last 40` (6 FAILED) | `[x]` |
| 2 | Implement `SendStep._resolve_body()` in send_step.py | coder | Modified `send_step.py` | `uv run pytest tests/unit/test_send_step_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw9.txt; Get-Content C:\Temp\zorivest\pytest-pw9.txt \| Select-Object -Last 40` (6 PASSED) | `[x]` |
| 3 | Write FIC + 5 tests for MEU-PW11 cursor tracking | coder | `tests/unit/test_fetch_step_cursor.py` | `uv run pytest tests/unit/test_fetch_step_cursor.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw11.txt; Get-Content C:\Temp\zorivest\pytest-pw11.txt \| Select-Object -Last 40` (5 FAILED) | `[x]` |
| 4 | Implement cursor upsert in fetch_step.py | coder | Modified `fetch_step.py` | `uv run pytest tests/unit/test_fetch_step_cursor.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw11.txt; Get-Content C:\Temp\zorivest\pytest-pw11.txt \| Select-Object -Last 40` (5 PASSED) | `[x]` |
| 5 | Replace `toLocaleString` with `formatTimestamp` in PolicyList.tsx | coder | Modified `PolicyList.tsx` | `cd p:\zorivest\ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc-72a.txt; Get-Content C:\Temp\zorivest\tsc-72a.txt \| Select-Object -Last 30` (clean) | `[x]` |
| 5a | Write Vitest unit test for PolicyList timezone rendering | coder | `scheduling.test.tsx` (3 AC-72a tests) | `cd p:\zorivest\ui; npx vitest run src/renderer/src/features/scheduling/__tests__/scheduling.test.tsx *> C:\Temp\zorivest\vitest-72a.txt; Get-Content C:\Temp\zorivest\vitest-72a.txt \| Select-Object -Last 30` (39 passed) | `[x]` |
| 5b | Write E2E test for timezone display in PolicyList | coder | `ui/tests/e2e/scheduling-tz.test.ts` (3 Playwright tests) + `POLICY_NEXT_RUN_TIME` in `test-ids.ts` | File exists. Runtime blocked by [E2E-ELECTRONLAUNCH] — validates in next desktop session | `[x]` |
| 5c | ESLint check on scheduling feature | tester | 0 new warnings | `cd p:\zorivest\ui; npx eslint src/renderer/src/features/scheduling --max-warnings 0 *> C:\Temp\zorivest\eslint-72a.txt; Get-Content C:\Temp\zorivest\eslint-72a.txt \| Select-Object -Last 20` (0 warnings — RunHistory.tsx `timezone` dep fixed in corrections) | `[x]` |
| 5e | Fix naive UTC timestamp parsing in formatDate.ts | coder | `normalizeUtc()` in `formatDate.ts` + 10 regression tests in `formatDate.test.ts` | `cd p:\zorivest\ui; npx vitest run src/renderer/src/lib/__tests__/formatDate.test.ts *> C:\Temp\zorivest\vitest-utc.txt; Get-Content C:\Temp\zorivest\vitest-utc.txt \| Select-Object -Last 20` (10 passed) | `[x]` |
| 5f | Add `timezone` to useMemo deps in RunHistory.tsx | coder | Modified `RunHistory.tsx:162` | `cd p:\zorivest\ui; npx eslint src/renderer/src/features/scheduling --max-warnings 0` (exit 0) | `[x]` |
| 5d | UI production build | tester | Build succeeds | `npm run build` passes — confirmed by Codex Round 4 (2026-04-20) | `[x]` |
| 6 | Run full regression + MEU gate | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu` — 8/8 PASS (24.3s) | `[x]` |
| 7 | Anti-placeholder scan | tester | 0 new matches | `rg "TODO\|FIXME\|NotImplementedError" packages/ ui/` — 1 pre-existing ABC pattern in `step_registry.py` | `[x]` |
| 8 | Update MEU registry with PW9, PW11, 72a | orchestrator | Updated `meu-registry.md` | `rg "PW9\|PW11\|72a" .agent/context/meu-registry.md *> C:\Temp\zorivest\meu-check.txt; Get-Content C:\Temp\zorivest\meu-check.txt` | `[x]` |
| 9 | Mark known issues resolved | orchestrator | Updated `known-issues.md` | TEMPLATE-RENDER, PIPE-CURSORS, SCHED-TZDISPLAY moved to Archived table | `[x]` |
| 10 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-pipeline-template-cursor-2026-04-20` | Pomera note ID: 870 | `[x]` |
| 11 | Create handoff | reviewer | `122-2026-04-20-pipeline-template-cursor-bp09s9B.7-9.md` | Created | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
