---
project: "2026-04-27-approval-security"
source: "docs/execution/plans/2026-04-27-approval-security/implementation-plan.md"
meus: ["MEU-PH11", "MEU-PH12", "MEU-PH13"]
status: "in_progress"
template_version: "2.0"
---

# Task — Approval Security & Validation Hardening

> **Project:** `2026-04-27-approval-security`
> **Type:** Infrastructure / MCP / API
> **Estimate:** ~15 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write FIC for MEU-PH11 (CSRF token) | orchestrator | AC-1..AC-12 documented in implementation-plan.md | Review AC table completeness | `[x]` |
| 2 | Write FIC for MEU-PH12 (MCP gap fill) | orchestrator | AC-13..AC-25 documented | Review AC table | `[x]` |
| 3 | Write FIC for MEU-PH13 (emulator hardening) | orchestrator | AC-26..AC-33 documented | Review AC table | `[x]` |
| 4 | **RED**: Write `approval-token-manager.test.ts` (AC-1..AC-4, AC-8) | coder | 5 failing Vitest tests | `cd ui; npx vitest run src/main/__tests__/approval-token-manager.test.ts *> C:\Temp\zorivest\vitest-ph11-red.txt; Get-Content C:\Temp\zorivest\vitest-ph11-red.txt \| Select-Object -Last 20` → 5 FAIL | `[x]` |
| 5 | **RED**: Write `test_approval_token_middleware.py` (AC-5..AC-7) | coder | 3 failing pytest tests | `uv run pytest tests/unit/test_approval_token_middleware.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ph11-red.txt; Get-Content C:\Temp\zorivest\pytest-ph11-red.txt \| Select-Object -Last 20` → 3 FAIL | `[x]` |
| 6 | **RED**: Write `approval-flow.test.tsx` (AC-10, AC-11) | coder | 2 failing Vitest tests | `cd ui; npx vitest run src/renderer/src/features/scheduling/__tests__/approval-flow.test.tsx *> C:\Temp\zorivest\vitest-ph11-renderer-red.txt; Get-Content C:\Temp\zorivest\vitest-ph11-renderer-red.txt \| Select-Object -Last 20` → 2 FAIL | `[x]` |
| 7 | Create ADR for IPC bridge choice | coder | `docs/decisions/adr-approval-ipc-bridge.md` | `Test-Path docs/decisions/adr-approval-ipc-bridge.md` → True | `[x]` |
| 8 | **GREEN**: Implement `approval-token-manager.ts` | coder | IPC handlers + HTTP callback server | AC-1..AC-4, AC-8 tests pass (rerun task 4 command → 5 PASS) | `[x]` |
| 9 | **GREEN**: Implement `approval_token.py` middleware | coder | FastAPI dependency | AC-5..AC-7 tests pass (rerun task 5 command → 3 PASS) | `[x]` |
| 10 | Wire approve endpoint with token dependency | coder | `scheduling.py` updated | `uv run pytest tests/unit/test_approval_token_middleware.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ph11-wire.txt; Get-Content C:\Temp\zorivest\pytest-ph11-wire.txt \| Select-Object -Last 20` → 3 PASS | `[x]` |
| 11 | Wire Electron main: register IPC handlers + start internal HTTP | coder | `index.ts` updated | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc-ph11.txt; Get-Content C:\Temp\zorivest\tsc-ph11.txt \| Select-Object -Last 20` → 0 errors | `[x]` |
| 12 | Wire preload: expose `generate-approval-token` | coder | `preload/index.ts` updated | `cd ui; npx tsc --noEmit *> C:\Temp\zorivest\tsc-ph11-preload.txt; Get-Content C:\Temp\zorivest\tsc-ph11-preload.txt \| Select-Object -Last 20` → 0 errors | `[x]` |
| 13 | **GREEN**: Wire renderer `approvePolicy()` to call IPC and inject token header | coder | `api.ts` updated | `cd ui; npx vitest run src/renderer/src/features/scheduling/__tests__/approval-flow.test.tsx *> C:\Temp\zorivest\vitest-ph11-renderer.txt; Get-Content C:\Temp\zorivest\vitest-ph11-renderer.txt \| Select-Object -Last 20` → 2 PASS | `[x]` |
| 14 | Run MEU gate (PH11) | tester | 8/8 blocking checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-ph11.txt; Get-Content C:\Temp\zorivest\validate-ph11.txt \| Select-Object -Last 50` | `[x]` |
| 15 | **RED**: Write `scheduling-gap-fill.test.ts` (AC-13..AC-20, AC-25) | coder | 8 failing Vitest tests | `cd mcp-server; npx vitest run src/__tests__/scheduling-gap-fill.test.ts *> C:\Temp\zorivest\vitest-ph12-red.txt; Get-Content C:\Temp\zorivest\vitest-ph12-red.txt \| Select-Object -Last 20` → 8 FAIL | `[x]` |
| 16 | Add `delete_policy` to DESTRUCTIVE_TOOLS | coder | `confirmation.ts` updated | `rg "delete_policy" mcp-server/src/middleware/confirmation.ts` → match found | `[x]` |
| 17 | **RED**: Write `test_email_status_endpoint.py` (AC-20) | coder | 2 failing pytest tests | `uv run pytest tests/unit/test_email_status_endpoint.py -x --tb=short -v *> C:\Temp\zorivest\pytest-email-status-red.txt; Get-Content C:\Temp\zorivest\pytest-email-status-red.txt \| Select-Object -Last 20` → 2 FAIL | `[x]` |
| 18 | **GREEN**: Implement `GET /settings/email/status` endpoint | coder | `email_settings.py` updated | `uv run pytest tests/unit/test_email_status_endpoint.py -x --tb=short -v *> C:\Temp\zorivest\pytest-email-status.txt; Get-Content C:\Temp\zorivest\pytest-email-status.txt \| Select-Object -Last 20` → 2 PASS | `[x]` |
| 19 | **GREEN**: Implement 3 MCP tools in `scheduling-tools.ts` with `.strict()` | coder | `delete_policy`, `update_policy`, `get_email_config` | AC-13..AC-25 tests pass (rerun task 15 command → 8 PASS) | `[x]` |
| 20 | Build MCP dist/ (M4) | coder | `npm run build` succeeds | `cd mcp-server; npm run build *> C:\Temp\zorivest\mcp-build.txt; Get-Content C:\Temp\zorivest\mcp-build.txt \| Select-Object -Last 20` → clean | `[x]` |
| 21 | Run MEU gate (PH12) | tester | 8/8 blocking checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-ph12.txt; Get-Content C:\Temp\zorivest\validate-ph12.txt \| Select-Object -Last 50` | `[x]` |
| 22 | **RED**: Write `test_emulator_validate_hardening.py` (AC-26..AC-33) | coder | 8 failing pytest tests | `uv run pytest tests/unit/test_emulator_validate_hardening.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ph13-red.txt; Get-Content C:\Temp\zorivest\pytest-ph13-red.txt \| Select-Object -Last 20` → 8 FAIL | `[x]` |
| 23 | **GREEN**: Extend `_run_validate()` with 3 new checks | coder | EXPLAIN SQL + SMTP check + wiring validation | AC-26..AC-33 tests pass (rerun task 22 command → 8 PASS) | `[x]` |
| 24 | Wire email config status into emulator constructor | coder | `dependencies.py` updated | `uv run pytest tests/unit/test_emulator_validate_hardening.py tests/unit/test_policy_emulator.py -x --tb=short -v *> C:\Temp\zorivest\pytest-ph13-wire.txt; Get-Content C:\Temp\zorivest\pytest-ph13-wire.txt \| Select-Object -Last 20` → all PASS | `[x]` |
| 25 | Run MEU gate (PH13) | tester | 8/8 blocking checks pass | `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate-ph13.txt; Get-Content C:\Temp\zorivest\validate-ph13.txt \| Select-Object -Last 50` | `[x]` |
| 26 | OpenAPI spec regenerate (G8) | tester | No drift detected | `uv run python tools/export_openapi.py -o openapi.committed.json *> C:\Temp\zorivest\openapi-regen.txt; Get-Content C:\Temp\zorivest\openapi-regen.txt` | `[x]` |
| 27 | Anti-placeholder scan | tester | No forbidden markers | `rg "TODO\|FIXME\|NotImplementedError" packages/ mcp-server/src/ *> C:\Temp\zorivest\placeholder-scan.txt; Get-Content C:\Temp\zorivest\placeholder-scan.txt` | `[x]` |
| 28 | Full verification plan | tester | All 8 verification checks pass | `uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest-full.txt; Get-Content C:\Temp\zorivest\pytest-full.txt \| Select-Object -Last 40` → 0 failures | `[x]` |
| 29 | Review and update `docs/BUILD_PLAN.md` | orchestrator | Status column updated for PH11/PH12/PH13 | `rg "MEU-PH1[123]" docs/BUILD_PLAN.md *> C:\Temp\zorivest\buildplan-check.txt; Get-Content C:\Temp\zorivest\buildplan-check.txt` | `[x]` |
| 30 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-approval-security-2026-04-27` | `pomera_notes(action="search", search_term="Zorivest-approval*")` returns ≥1 | `[x]` |
| 31 | Create handoff | reviewer | `.agent/context/handoffs/2026-04-27-approval-security-handoff.md` | `Test-Path .agent/context/handoffs/2026-04-27-approval-security-handoff.md` → True | `[x]` |
| 32 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-27-approval-security-reflection.md` | `Test-Path docs/execution/reflections/2026-04-27-approval-security-reflection.md` → True | `[x]` |
| 33 | Append metrics row | orchestrator | Row in `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` → new row visible | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
