---
project: "2026-04-28-pipeline-remediation"
source: "docs/execution/plans/2026-04-28-pipeline-remediation/implementation-plan.md"
meus: ["MEU-PW14", "MEU-72b"]
status: "complete"
template_version: "2.0"
---

# Task — Pipeline Markdown Migration + Email Templates GUI

> **Project:** `2026-04-28-pipeline-remediation`
> **Type:** Infrastructure + GUI
> **Estimate:** ~19 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | **MEU-PW14 FIC**: Write Feature Intent Contract with ACs for markdown migration | coder | `tests/unit/test_pipeline_markdown_migration.py` with all test stubs | `uv run pytest tests/unit/test_pipeline_markdown_migration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw14-red.txt; Get-Content C:\Temp\zorivest\pytest-pw14-red.txt \| Select-Object -Last 40` — all tests FAIL (Red) | `[x]` |
| 2 | **Delete `pdf_renderer.py`** and remove Playwright dependency | coder | File deleted, `pyproject.toml` updated | `Test-Path packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py *> C:\Temp\zorivest\pdf-deleted.txt; Get-Content C:\Temp\zorivest\pdf-deleted.txt` → False | `[x]` |
| 3 | **Modify `render_step.py`**: Remove `_render_pdf()`, add `_render_markdown()`, constrain `output_format` | coder | Updated `render_step.py` | `uv run pytest tests/unit/test_store_render_step.py tests/unit/test_pipeline_markdown_migration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-render.txt; Get-Content C:\Temp\zorivest\pytest-render.txt \| Select-Object -Last 40` | `[x]` |
| 4 | **Modify `send_step.py`**: Rename `pdf_path`→`attachment_path`, update `_save_local()` for `.md`, update email call | coder | Updated `send_step.py` | `uv run pytest tests/unit/test_send_step.py tests/unit/test_pipeline_markdown_migration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-send.txt; Get-Content C:\Temp\zorivest\pytest-send.txt \| Select-Object -Last 40` | `[x]` |
| 5 | **Modify `email_sender.py`**: Rename `pdf_path`→`attachment_path`, replace PDF MIME with generic file attachment | coder | Updated `email_sender.py` | `uv run pytest tests/unit/test_send_step.py -x --tb=short -v *> C:\Temp\zorivest\pytest-email.txt; Get-Content C:\Temp\zorivest\pytest-email.txt \| Select-Object -Last 40` | `[x]` |
| 6 | **Update defaults**: `ReportModel.format` + `ReportRepository.create()` default `"pdf"`→`"html"` | coder | Updated `models.py` + `scheduling_repositories.py` | `rg "pdf" packages/infrastructure/src/zorivest_infra/database/models.py packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py *> C:\Temp\zorivest\pdf-defaults.txt; Get-Content C:\Temp\zorivest\pdf-defaults.txt` → 0 matches | `[x]` |
| 7 | **Update existing tests**: Fix `test_store_render_step.py`, `test_send_step.py`, `test_send_step_db_lookup.py` for API changes | coder | All existing tests pass | `uv run pytest tests/unit/ -x --tb=short -v -k "render_step or send_step" *> C:\Temp\zorivest\pytest-existing.txt; Get-Content C:\Temp\zorivest\pytest-existing.txt \| Select-Object -Last 40` | `[x]` |
| 8 | **MEU-PW14 Green**: All PW14 tests pass | tester | Green test run | `uv run pytest tests/unit/test_pipeline_markdown_migration.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw14-green.txt; Get-Content C:\Temp\zorivest\pytest-pw14-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| 9 | **MEU-PW14 cleanup**: Verify zero PDF references remain | tester | Clean grep | `rg "pdf_renderer\|render_pdf\|_render_pdf\|pdf_path" packages/ *> C:\Temp\zorivest\pdf-cleanup.txt; Get-Content C:\Temp\zorivest\pdf-cleanup.txt` → 0 matches | `[x]` |
| 10 | **MEU-72b FIC Red**: Write Vitest tests for template hooks, CRUD behavior, default protection, preview | coder | `ui/src/renderer/src/features/scheduling/__tests__/email-templates.test.tsx` | `cd ui; npx vitest run src/renderer/src/features/scheduling/__tests__/email-templates.test.tsx --reporter=verbose *> C:\Temp\zorivest\vitest-72b-red.txt; Get-Content C:\Temp\zorivest\vitest-72b-red.txt \| Select-Object -Last 40` — all tests FAIL (Red) | `[x]` |
| 11 | **MEU-72b**: Create `template-api.ts` with API functions for template CRUD + preview | coder | New file | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\ui-typecheck-api.txt; Get-Content C:\Temp\zorivest\ui-typecheck-api.txt \| Select-Object -Last 30` | `[x]` |
| 12 | **MEU-72b**: Create `template-hooks.ts` with React Query hooks | coder | New file | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\ui-typecheck-hooks.txt; Get-Content C:\Temp\zorivest\ui-typecheck-hooks.txt \| Select-Object -Last 30` | `[x]` |
| 13 | **MEU-72b**: Create `EmailTemplateList.tsx` with list sidebar, `is_default` badge, selection | coder | New component | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\ui-typecheck-list.txt; Get-Content C:\Temp\zorivest\ui-typecheck-list.txt \| Select-Object -Last 30` | `[x]` |
| 14 | **MEU-72b**: Create `EmailTemplateDetail.tsx` with editor, default protection, save/duplicate/delete | coder | New component | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\ui-typecheck-detail.txt; Get-Content C:\Temp\zorivest\ui-typecheck-detail.txt \| Select-Object -Last 30` | `[x]` |
| 15 | **MEU-72b**: Create `EmailTemplatePreview.tsx` with sandboxed iframe | coder | New component | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\ui-typecheck-preview.txt; Get-Content C:\Temp\zorivest\ui-typecheck-preview.txt \| Select-Object -Last 30` | `[x]` |
| 16 | **MEU-72b**: Modify `SchedulingLayout.tsx` to add tab bar + wire tab content | coder | Tab bar with "Report Policies" (default) + "Email Templates" | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\ui-typecheck-layout.txt; Get-Content C:\Temp\zorivest\ui-typecheck-layout.txt \| Select-Object -Last 30` | `[x]` |
| 17 | **MEU-72b**: Update `test-ids.ts` with template test IDs from §6K.9 | coder | All 11 test IDs present | `rg "scheduling-tab-\|template-" ui/src/renderer/src/features/scheduling/test-ids.ts *> C:\Temp\zorivest\testids-check.txt; Get-Content C:\Temp\zorivest\testids-check.txt` | `[x]` |
| 18 | **MEU-72b Vitest Green**: All Vitest component tests pass | tester | Green Vitest run | `cd ui; npx vitest run src/renderer/src/features/scheduling/__tests__/email-templates.test.tsx --reporter=verbose *> C:\Temp\zorivest\vitest-72b-green.txt; Get-Content C:\Temp\zorivest\vitest-72b-green.txt \| Select-Object -Last 40` — all PASS | `[x]` |
| 19 | **MEU-72b E2E**: Write Wave 8 E2E tests (3 tests per §6K.10) | coder | `ui/tests/e2e/email-templates.test.ts` | `cd ui; npx playwright test tests/e2e/email-templates.test.ts --reporter=list *> C:\Temp\zorivest\e2e-72b.txt; Get-Content C:\Temp\zorivest\e2e-72b.txt \| Select-Object -Last 30` — 3 tests pass | `[B]` Blocked: requires Electron runtime — [E2E-ELECTRONLAUNCH] |
| 20 | **MEU-72b UI quality gate**: TypeScript + Vitest + ESLint | tester | All checks pass | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\ui-typecheck.txt; npx vitest run --reporter=verbose *>> C:\Temp\zorivest\ui-typecheck.txt; npm run lint *>> C:\Temp\zorivest\ui-typecheck.txt; Get-Content C:\Temp\zorivest\ui-typecheck.txt \| Select-Object -Last 50` | `[x]` |
| 21 | **MEU gate**: Run scoped validation | tester | All checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt \| Select-Object -Last 50` | `[x]` |
| 22 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected; evidence of clean grep | `rg "pipeline-remediation" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-audit.txt; Get-Content C:\Temp\zorivest\buildplan-audit.txt` (expect 0 matches) | `[x]` |
| 23 | Run verification plan | tester | All checks pass | All 9 verification commands from implementation-plan.md (§1–§7 incl. §3b, §3c) | `[x]` |
| 24 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-pipeline-remediation-2026-04-28` | MCP: `pomera_notes(action="search", search_term="Zorivest-pipeline*")` returns ≥1 result | `[x]` |
| 25 | Create handoff | reviewer | `.agent/context/handoffs/` | `Test-Path .agent/context/handoffs/*pipeline-remediation* *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt` | `[x]` |
| 26 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-28-pipeline-remediation-reflection.md` | `Test-Path docs/execution/reflections/2026-04-28-pipeline-remediation-reflection.md *> C:\Temp\zorivest\reflection-check.txt; Get-Content C:\Temp\zorivest\reflection-check.txt` | `[x]` |
| 27 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md *> C:\Temp\zorivest\metrics-check.txt; Get-Content C:\Temp\zorivest\metrics-check.txt \| Select-Object -Last 3` | `[x]` |
| | | | | | |
| | **Ad-Hoc GUI Hardening (post-MEU)** | | | | |
| AH-1 | MCP execution status indicator: lock/unlock icon + text based on policy state | coder | `PolicyDetail.tsx` updated | `cd ui; npx tsc --noEmit` — clean | `[x]` |
| AH-2 | Template save button fix for non-default templates with dirty-state gating | coder | `EmailTemplateDetail.tsx` updated | Visual + Vitest green | `[x]` |
| AH-3 | Template preview rendering wired to POST preview endpoint | coder | `SchedulingLayout.tsx` + `EmailTemplateDetail.tsx` | Visual | `[x]` |
| AH-4 | Template name inline pencil-edit (rename = create-new + delete-old) | coder | `EmailTemplateDetail.tsx` + `SchedulingLayout.tsx` | Vitest 469/469 pass | `[x]` |
| AH-5 | Unsaved changes navigation guard with portal confirmation modal | coder | `SchedulingLayout.tsx`, `PolicyDetail.tsx`, `EmailTemplateDetail.tsx` | Vitest 469/469 pass | `[x]` |
| AH-6 | Portal rendering fix: Tailwind → inline styles for Electron compatibility | coder | `SchedulingLayout.tsx`, `PolicyDetail.tsx` | Visual + Vitest green | `[x]` |
| AH-7 | Interactive variable autocomplete dropdown with template body parsing + 20 curated suggestions | coder | `EmailTemplateDetail.tsx` | `cd ui; npx tsc --noEmit` — clean, Vitest 469/469 pass | `[x]` |
| AH-8 | Collapsible Run History with +/− toggle icon | coder | `SchedulingLayout.tsx` | Visual + tsc + Vitest green | `[x]` |
| AH-9 | Action buttons always visible (never hidden behind Run History) | coder | `SchedulingLayout.tsx` | Visual | `[x]` |
| AH-10 | Settings nav moved to bottom above Collapse | coder | `NavRail.tsx` | tsc + Vitest 469/469 pass | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
