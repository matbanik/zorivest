---
project: "2026-04-30-mcp-token-refresh"
source: "docs/execution/plans/2026-04-30-mcp-token-refresh/implementation-plan.md"
meus: ["MEU-PH14"]
status: "complete"
template_version: "2.0"
---

# Task — MCP Token Refresh Manager (MEU-PH14)

> **Project:** `2026-04-30-mcp-token-refresh`
> **Type:** MCP
> **Estimate:** 15 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write FIC tests: create `token-refresh-manager.test.ts` with 9+ test cases covering AC-1 through AC-10 | coder | `mcp-server/tests/token-refresh-manager.test.ts` | See V1 below → all tests FAIL (Red phase) | `[x]` |
| 2 | Create `ITokenProvider` interface + `TokenRefreshManager` class with singleton, promise coalescing, proactive expiry (30s skew), stored API key for re-auth | coder | `mcp-server/src/utils/token-refresh-manager.ts` | See V2 below → all tests PASS (Green phase) | `[x]` |
| 3 | Refactor `api-client.ts`: remove module-level `authState`/`bootstrapAuth`; `getAuthHeaders()` → async, delegates to `TokenRefreshManager.getValidAccessToken()`; update `fetchApi()`/`fetchApiBinary()` to `await` auth headers | coder | Modified `mcp-server/src/utils/api-client.ts` | See V3 below → 0 errors | `[x]` |
| 4 | Update `index.ts`: initialize `TokenRefreshManager` with API key instead of calling `bootstrapAuth()` directly | coder | Modified `mcp-server/src/index.ts` | Covered by V3 (tsc) + V5 (integration tests) | `[x]` |
| 5 | Update direct `getAuthHeaders()` callers: `system-tool.ts`, `mcp-guard.ts`, `diagnostics-tools.ts` → `await getAuthHeaders()` | coder | Modified 3 source files | See V3 below → 0 errors | `[x]` |
| 6 | Write AC-10 integration tests: mock manager, assert sentinel token in `fetchApi`, `fetchApiBinary`, guard check, diagnostics safe-fetch, startup init | coder | Tests in `integration.test.ts` or `token-refresh-manager.test.ts` | See V5 below → integration tests pass | `[x]` |
| 7 | Update existing test mocks (`integration.test.ts`, `system-tool.test.ts`, other affected tests) for async auth API | coder | Modified test files | See V4 below → all tests pass | `[x]` |
| 8 | AC-7 enforcement: verify no compound tool file imports `bootstrapAuth` directly | tester | Grep evidence | See V6 below → 0 matches | `[x]` |
| 9 | Build dist/ (M4 compliance) | coder | Clean build | See V7 below → success | `[x]` |
| 10 | Lint check (ESLint) | tester | Clean lint | See V8 below → 0 warnings | `[x]` |
| 11 | Anti-placeholder scan | tester | 0 matches | See V9 below → 0 matches | `[x]` |
| 12 | Add §5.X to `05-mcp-server.md` — Token Refresh Infrastructure + update stale `bootstrapAuth`/`getAuthHeaders` snippets (L119,122,241,259,1015) | orchestrator | Updated build plan section | See V10 below → 0 stale refs | `[x]` |
| 13 | Add P2.5g entry to `build-priority-matrix.md` | orchestrator | New row | See V11 below → 1+ matches | `[x]` |
| 14 | Update `docs/BUILD_PLAN.md`: add P2.5g section (MEU-PH14 row), update Phase 9 tracker, update MEU Summary | orchestrator | Updated BUILD_PLAN.md | See V12 below → 3+ matches | `[x]` |
| 15 | Update `.agent/context/meu-registry.md`: add MEU-PH14 entry | orchestrator | New registry row | See V13 below → 1+ matches | `[x]` |
| 16 | Archive [MCP-AUTHRACE] in `known-issues.md` → `known-issues-archive.md` | orchestrator | Issue archived | See V14 below → 1+ matches | `[x]` |
| 17 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-mcp-token-refresh-2026-04-30` | MCP: `pomera_notes(action="search", search_term="Zorivest-mcp-token-refresh*")` returns ≥1 result | `[x]` |
| 18 | Create handoff | reviewer | `.agent/context/handoffs/2026-04-30-mcp-token-refresh-handoff.md` | `Test-Path .agent/context/handoffs/2026-04-30-mcp-token-refresh-handoff.md` | `[x]` |
| 19 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-30-mcp-token-refresh-reflection.md` | `Test-Path docs/execution/reflections/2026-04-30-mcp-token-refresh-reflection.md` | `[x]` |
| 20 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md` last 3 lines show new row | `[x]` |

## Validation Commands

Exact runnable PowerShell commands referenced by the task table above.

```powershell
# V1 — Red phase (FIC tests fail before implementation)
cd mcp-server; npx vitest run tests/token-refresh-manager.test.ts *> C:\Temp\zorivest\vitest-trm-red.txt; Get-Content C:\Temp\zorivest\vitest-trm-red.txt | Select-Object -Last 20

# V2 — Green phase (FIC tests pass after implementation)
cd mcp-server; npx vitest run tests/token-refresh-manager.test.ts *> C:\Temp\zorivest\vitest-trm-green.txt; Get-Content C:\Temp\zorivest\vitest-trm-green.txt | Select-Object -Last 20

# V3 — TypeScript type check
cd mcp-server; npx tsc --noEmit *> C:\Temp\zorivest\tsc-api.txt; Get-Content C:\Temp\zorivest\tsc-api.txt | Select-Object -Last 20

# V4 — Full MCP test suite (regression)
cd mcp-server; npx vitest run *> C:\Temp\zorivest\vitest-full.txt; Get-Content C:\Temp\zorivest\vitest-full.txt | Select-Object -Last 40

# V5 — Integration tests (AC-10 proof)
cd mcp-server; npx vitest run tests/token-refresh-manager.test.ts tests/integration.test.ts *> C:\Temp\zorivest\vitest-integ.txt; Get-Content C:\Temp\zorivest\vitest-integ.txt | Select-Object -Last 30

# V6 — AC-7 enforcement (no direct bootstrapAuth imports in compound tools)
rg "import.*bootstrapAuth" mcp-server/src/compound/ *> C:\Temp\zorivest\ac7.txt; Get-Content C:\Temp\zorivest\ac7.txt

# V7 — Build dist (M4 compliance)
cd mcp-server; npm run build *> C:\Temp\zorivest\build.txt; Get-Content C:\Temp\zorivest\build.txt | Select-Object -Last 10

# V8 — ESLint
cd mcp-server; npx eslint src/ --max-warnings 0 *> C:\Temp\zorivest\eslint.txt; Get-Content C:\Temp\zorivest\eslint.txt | Select-Object -Last 20

# V9 — Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError" mcp-server/src/utils/token-refresh-manager.ts *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt

# V10 — Stale auth terms removed from 05-mcp-server.md
rg "bootstrapAuth\(\)|getAuthHeaders\(\): Record" docs/build-plan/05-mcp-server.md *> C:\Temp\zorivest\stale-auth.txt; Get-Content C:\Temp\zorivest\stale-auth.txt

# V11 — P2.5g in build-priority-matrix
rg "P2.5g" docs/build-plan/build-priority-matrix.md *> C:\Temp\zorivest\bpm.txt; Get-Content C:\Temp\zorivest\bpm.txt

# V12 — BUILD_PLAN.md updates
rg "P2.5g|MEU-PH14" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-audit.txt; Get-Content C:\Temp\zorivest\bp-audit.txt

# V13 — MEU registry
rg "MEU-PH14" .agent/context/meu-registry.md *> C:\Temp\zorivest\reg.txt; Get-Content C:\Temp\zorivest\reg.txt

# V14 — AUTHRACE archived
rg "MCP-AUTHRACE" .agent/context/known-issues-archive.md *> C:\Temp\zorivest\archive.txt; Get-Content C:\Temp\zorivest\archive.txt
```

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
