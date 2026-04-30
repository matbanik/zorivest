---
project: "2026-04-29-mcp-consolidation"
type: "execution-corrections"
source: ".agent/context/handoffs/2026-04-29-mcp-consolidation-implementation-critical-review.md"
status: "complete"
findings_addressed: [1, 2, 3, 4, 5, 6, 7, 8]
verbosity: "standard"
---

# Execution Corrections Handoff — MCP Consolidation

## Findings Addressed

### Finding 1: zorivest_plan toolset misalignment ✅
**Change:** Relocated `zorivest_plan` from `trade` to `ops` toolset in `seed.ts`.

**Files changed:**
- `mcp-server/src/toolsets/seed.ts` — moved plan registration
- `mcp-server/tests/tool-count-gate.test.ts` — updated counts (trade 4→3, ops 3→4)
- `mcp-server/tests/scheduling-tools.test.ts` — ops count 3→4
- `mcp-server/tests/pipeline-security-tools.test.ts` — ops count 3→4

### Finding 2: v3.1 action name standardization ✅
**6 renames applied:**

| Tool | Old Action | New Action (v3.1) |
|------|-----------|-------------------|
| analytics | `fees` | `fee_breakdown` |
| analytics | `pfof` | `pfof_impact` |
| analytics | `strategy` | `strategy_breakdown` |
| market | `sec_filings` | `filings` |
| market | `disconnect_provider` | `disconnect` |
| report | `get_for_trade` | `get` |

**Files changed:**
- `mcp-server/src/compound/analytics-tool.ts` — 3 router key + ACTIONS array renames
- `mcp-server/src/compound/market-tool.ts` — 2 router key + ACTIONS array renames
- `mcp-server/src/compound/report-tool.ts` — 1 router key + ACTIONS array rename

### Finding 3: Comprehensive behavior tests ✅
**Created 12 new test files** covering all 13 compound tools under `tests/compound/`.

### Finding 4: /mcp-audit validation gate ✅
**Executed 2026-04-29.** Results: 46 tested, 44 pass, 0 fail, 2 skip (news/filings — no API keys). CRUD lifecycles verified. DDL injection blocked. Consolidation score 1.08 (Excellent). Report: `.agent/context/MCP/mcp-tool-audit-report.md`.

### Finding 5: delete_email_template confirmation gate bypass ✅
**TDD fix applied 2026-04-29.**

**Red phase:** 3 tests written in `tests/compound/template-tool.test.ts`:
- `blocks delete without token in static mode` — FAILED (delete passed through)
- `can mint a token for delete_email_template` — FAILED (`Unknown destructive action`)
- `allows delete with valid token in static mode` — FAILED (same throw)

**Green phase:** Added `"delete_email_template"` to `DESTRUCTIVE_TOOLS` in `mcp-server/src/middleware/confirmation.ts:30`. All 3 tests pass.

**Files changed:**
- `mcp-server/src/middleware/confirmation.ts` — added `delete_email_template` to `DESTRUCTIVE_TOOLS` set
- `mcp-server/tests/compound/template-tool.test.ts` — 3 new confirmation regression tests

### Finding 6: Handoff evidence inconsistencies ✅
**Reconciled 2026-04-29.**

**Changes to primary handoff** (`.agent/context/handoffs/2026-04-29-mcp-consolidation-handoff.md`):
- AC-4.10: "defaults → 5 tools" → "defaults → 4 tools"
- AC-4.13: "enable ops → 8 tools" → "enable ops → 5 tools (core+ops)"
- FAIL_TO_PASS: "expected 32 to be 5" → "expected 32 to be 4"
- Changed files: `get_for_trade` → `get`
- Test counts: 274/26 → 376/38

**Changes to corrections handoff** (this file):
- Removed `finding_4_status: "deferred-to-next-session"` frontmatter
- Updated Finding 4 from deferred → resolved with audit evidence
- Added Findings 5 and 6 with evidence

<!-- CACHE BOUNDARY -->

## Evidence

### FAIL_TO_PASS

| Test | Red Output (snippet) | Green Output | File:Line |
|------|---------------------|--------------|-----------|
| `template delete confirmation > blocks delete without token in static mode` | Expected `text.error` to be "Confirmation required" but delete passed through | ✓ Returns `{"error":"Confirmation required","tool":"delete_email_template"}` | `tests/compound/template-tool.test.ts:105` |
| `template delete confirmation > can mint a token for delete_email_template` | `Error: Unknown destructive action: delete_email_template` | ✓ Returns `ctk_` token with 60s expiry | `tests/compound/template-tool.test.ts:122` |
| `template delete confirmation > allows delete with valid token in static mode` | `Error: Unknown destructive action: delete_email_template` | ✓ DELETE sent to `/scheduling/templates/test-tmpl` | `tests/compound/template-tool.test.ts:129` |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `npx vitest run tests/compound/template-tool.test.ts` (Red) | 1 | 3 failed, 8 passed (11 total) |
| `npx vitest run tests/compound/template-tool.test.ts` (Green) | 0 | 11 passed (11 total) |
| `npx vitest run` | 0 | 376 passed (38 files), 3.62s |
| `npx tsc --noEmit` | 0 | Clean (0 errors) |
| `npx eslint src --max-warnings 0` | 0 | Clean (0 errors, 0 warnings) |

### Finding 7: task.md stale MC4 tool counts ✅
**Change:** Updated task row 18 from `defaults=5, toolset_enable(ops)=8` to `defaults=4, toolset_enable(ops)=5` matching corrected runtime/test contract.

**Files changed:**
- `docs/execution/plans/2026-04-29-mcp-consolidation/task.md` — row 18 corrected

### Finding 8: Pipeline-run CSRF security hardening (SEC-1) ✅
**Vulnerability:** `POST /policies/{id}/run` had no auth dependency, allowing AI agents to bypass the MCP `ctk_` confirmation gate by calling the REST API directly. Discovered during live MCP audit when an approved policy was triggered via `Invoke-RestMethod` without any token.

**Fix:** Added `validate_approval_token` FastAPI dependency to `trigger_pipeline` endpoint in `scheduling.py`. This reuses the same Electron CSRF gate that already protects `/approve` — only the GUI can now trigger pipeline runs.

**TDD evidence:**
- `test_run_rejects_without_csrf_token` — new regression test proving direct API calls without CSRF token get 403
- `test_live_manual_run_route` — updated to bypass CSRF for service-wiring validation (CSRF tested separately)
- All 42 scheduling tests pass, pyright 0 errors

**Files changed:**
- `packages/api/src/zorivest_api/routes/scheduling.py` — `_token: None = Depends(validate_approval_token)` added to `trigger_pipeline`
- `tests/unit/test_api_scheduling.py` — 1 new regression test + live wiring test CSRF override

<!-- CACHE BOUNDARY -->

## Quality Gates
- **vitest**: 38/38 files, 376/376 tests ✅
- **tsc**: 0 errors ✅
- **eslint**: 0 errors, 0 warnings ✅
- **pytest**: 42/42 scheduling tests ✅
- **pyright**: 0 errors ✅
- **Confirmation gate**: delete_email_template now gated ✅
- **CSRF gate**: /run endpoint now requires X-Approval-Token ✅
- **Action name alignment**: 6/6 renames verified ✅
- **Toolset relocation**: plan in ops confirmed ✅
- **/mcp-audit**: 46 tested, 44 pass, 0 fail ✅

---

## Codex Validation Report

_Left blank for reviewer agent._
