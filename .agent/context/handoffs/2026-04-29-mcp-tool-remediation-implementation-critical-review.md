---
date: "2026-04-29"
review_mode: "handoff"
target_plan: "docs/execution/plans/2026-04-29-mcp-tool-remediation/implementation-plan.md"
verdict: "approved"
findings_count: 5
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-04-29-mcp-tool-remediation

> **Review Mode**: `handoff`
> **Verdict**: `approved_after_recheck`

---

## Scope

**Target**: `.agent/context/handoffs/2026-04-29-mcp-tool-remediation-handoff.md`
**Review Type**: implementation handoff review
**Checklist Applied**: execution-critical-review IR/DR/PR + reviewer AV checklist

Correlation rationale: user explicitly supplied the work handoff. Frontmatter and path correlate to `docs/execution/plans/2026-04-29-mcp-tool-remediation/`. The correlated project contains TA1-TA4 in one plan folder and one work handoff, so no sibling work handoff expansion was needed.

Commands executed:

| Command | Result |
|---------|--------|
| `git status --short *> C:\Temp\zorivest\review-git-status.txt; Get-Content C:\Temp\zorivest\review-git-status.txt` | Claimed MCP/API/test/docs changes present; review file did not exist before this pass |
| `git diff -- <claimed files> *> C:\Temp\zorivest\review-claimed-diff.txt; Get-Content C:\Temp\zorivest\review-claimed-diff.txt` | Verified actual code/test changes |
| `rg -n 'list_trade_plans\|delete_trade_plan\|estimate_tax\|find_wash_sales\|manage_lots\|harvest_losses\|registerTaxTools\|delete_trade_with_linked_records\|TradeModel\.report\|ondelete' mcp-server/tests mcp-server/src packages tests *> C:\Temp\zorivest\review-target-rg2.txt; Get-Content C:\Temp\zorivest\review-target-rg2.txt` | New plan tools only appear in source/seed, not tests |
| `uv run pytest tests/unit/test_api_trades.py::TestDeleteTrade tests/unit/test_service_extensions.py::TestDeleteTrade -q *> C:\Temp\zorivest\review-pytest-delete.txt; Get-Content C:\Temp\zorivest\review-pytest-delete.txt` | 5 passed, 1 warning |
| `cd mcp-server; npx vitest run tests/planning-tools.test.ts tests/accounts-tools.test.ts tests/settings-tools.test.ts *> C:\Temp\zorivest\review-vitest-targeted.txt; Get-Content C:\Temp\zorivest\review-vitest-targeted.txt` | 40 passed |
| `uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\review-validate-meu.txt; Get-Content C:\Temp\zorivest\review-validate-meu.txt` | 8/8 blocking checks passed; evidence bundle advisory remains |

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | `delete_trade_plan` is not actually protected by the M3 confirmation gate. The tool wraps its handler in `withConfirmation("delete_trade_plan", ...)`, but `withConfirmation()` immediately passes through when the tool name is absent from `DESTRUCTIVE_TOOLS`. `createConfirmationToken("delete_trade_plan")` would also reject the action for static clients. This breaks TA4 AC-11 despite the handoff claiming a confirmation-gated destructive tool. | `mcp-server/src/tools/planning-tools.ts:453`; `mcp-server/src/middleware/confirmation.ts:23`; `mcp-server/src/middleware/confirmation.ts:131` | Add `delete_trade_plan` to `DESTRUCTIVE_TOOLS`; add confirmation middleware tests and an MCP tool test proving static-mode calls without token are rejected and valid-token calls execute. | open |
| 2 | High | TA1 AC-0 is not implemented but the project is marked complete. The plan requires `DELETE /trades/{exec_id}` to succeed for a valid trade with linked report/images, yet the handoff's live audit records `delete_trade(E001 with linked report)` as 500. Current model state still lacks report cascade and FK cascade, and `TradeService.delete_trade()` only checks existence before deleting the trade. | `.agent/context/handoffs/2026-04-29-mcp-tool-remediation-handoff.md:52`; `packages/infrastructure/src/zorivest_infra/database/models.py:53`; `packages/infrastructure/src/zorivest_infra/database/models.py:59`; `packages/infrastructure/src/zorivest_infra/database/models.py:112`; `packages/core/src/zorivest_core/services/trade_service.py:193` | Do not mark TA1 complete until linked-record deletion is fixed and covered by a real repository/API test with a linked `TradeReportModel` and image records. | open |
| 3 | Medium | The “linked records” regression test is weak and does not reproduce the failure. `test_delete_trade_with_linked_records` uses a mocked service that simply returns `None`; it creates no trade, report, image, FK constraint, or SQLAlchemy unit of work. It would pass even if the real linked-record deletion still fails, which it does per the live audit. | `tests/unit/test_api_trades.py:217`; `tests/unit/test_api_trades.py:226`; `tests/unit/test_api_trades.py:231` | Replace or supplement this with an integration/API test using real persistence, or move the claim out of TA1 and mark AC-0 blocked by `[TRADE-CASCADE]`. | open |
| 4 | Medium | TA4 added `list_trade_plans` and `delete_trade_plan` without direct tests. The targeted `planning-tools.test.ts` run passed 14 existing tests, but `rg` found `list_trade_plans` and `delete_trade_plan` only in source/seed files, not in `mcp-server/tests`. This leaves AC-8 through AC-14 largely unproven, including pagination, DELETE path, 404 handling, and stale-plan cleanup flow. | `mcp-server/src/tools/planning-tools.ts:398`; `mcp-server/src/tools/planning-tools.ts:453`; `C:\Temp\zorivest\review-target-rg2.txt` | Add tests for `list_trade_plans`, `delete_trade_plan`, confirmation behavior, API error propagation, and seed/toolset registration. | open |
| 5 | Medium | The work handoff is not evidence-compliant. It has no `CACHE BOUNDARY`, no acceptance-criteria table, no `FAIL_TO_PASS` evidence, and no commands/Codex validation section. The reproduced MEU gate passes blocking checks but reports: `2026-04-29-mcp-tool-remediation-handoff.md missing: Evidence/FAIL_TO_PASS, Pass-fail/Commands, Commands/Codex Report`. | `.agent/context/handoffs/2026-04-29-mcp-tool-remediation-handoff.md:1`; `C:\Temp\zorivest\review-validate-meu.txt` | Rewrite/update the work handoff from `TEMPLATE.md`, include compressed red-phase evidence and exact command outputs, and rerun the MEU gate until the advisory clears. | open |

---

## Checklist Results

### Information Retrieval (IR)

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | fail | Handoff live audit shows linked-record delete still 500 at `.agent/context/handoffs/2026-04-29-mcp-tool-remediation-handoff.md:52`. No real persistence regression test exists for that path. |
| IR-2 Stub behavioral compliance | partial | Accounts 501 tests assert no fetch and structured 501. Tax tools now register callable 501 stubs, but direct tests for the tax tool handlers are absent. |
| IR-3 Error mapping completeness | partial | `delete_trade` not-found maps to 404 and targeted tests pass. Linked-record valid-delete still becomes 500. |
| IR-4 Fix generalization | fail | Confirmation gate pattern was not generalized to the shared destructive registry for `delete_trade_plan`. |
| IR-5 Test rigor audit | fail | `test_delete_trade_with_linked_records` is Weak. New TA4 tools have no direct tests. Settings serialization test is Strong; account 501 tests are Adequate/Strong; service not-found test is Strong. |
| IR-6 Boundary validation coverage | partial | New Zod schemas exist for plan tools and tax stubs, but delete confirmation behavior is not enforced because the shared destructive-tool registry omits `delete_trade_plan`. |

### Design Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| Naming convention followed | pass | Work handoff and plan folder use `2026-04-29-mcp-tool-remediation`. Canonical review path derived from plan folder. |
| Template version present | partial | Work handoff has frontmatter but not the required template sections or cache marker. |
| YAML frontmatter well-formed | pass | Handoff frontmatter parsed visually and file is readable. |
| Cross-file state consistency | partial | `BUILD_PLAN.md` marks TA1-TA4 rows done, but the completion summary still reports `P2.5e — Tool Remediation | 4 | 0`; this is secondary to runtime blockers. |

### Post-Implementation Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| Evidence bundle complete | fail | MEU gate advisory reports missing evidence sections in the work handoff. |
| FAIL_TO_PASS table present | fail | Marker check found no `FAIL_TO_PASS` or `Evidence bundle location` in the work handoff. |
| Commands independently runnable | partial | Reproduced targeted pytest/vitest and MEU gate. Handoff's own command evidence is too compressed and missing exact receipt references. |
| Anti-placeholder scan clean | pass | MEU gate anti-placeholder and anti-deferral scans passed. |
| No product files modified by review | pass | This review created only the canonical implementation-critical-review handoff. |

---

## Verdict

`changes_required` — The codebase passes broad blocking checks, but the implementation is not approvable. A destructive MCP tool is not actually confirmation-gated, a claimed linked-record delete AC is demonstrably unresolved, TA4 lacks direct tests, and the handoff does not satisfy the project evidence contract.

Concrete follow-up actions:

1. Route fixes through `/execution-corrections`; do not patch under this review workflow.
2. Add `delete_trade_plan` to the confirmation destructive registry and prove token behavior with tests.
3. Fix or explicitly split out TA1 AC-0 linked-record deletion, with real persistence/API regression coverage.
4. Add direct tests for `list_trade_plans` and `delete_trade_plan`.
5. Rewrite the work handoff evidence sections and rerun the MEU gate.

---

## Corrections Applied (2026-04-29)

> **Verdict**: `corrections_applied` — 4 of 5 findings resolved. Finding 2 was already resolved by the TRADE-CASCADE fix applied before this corrections pass.

**Findings resolved**: 4/5 (1 was pre-resolved)

| # | Finding | Fix Applied | Verification |
|---|---------|-------------|--------------|
| 1 | `delete_trade_plan` not in `DESTRUCTIVE_TOOLS` | Added to `DESTRUCTIVE_TOOLS` set in `confirmation.ts:24` | RED: `delete_trade_plan requires confirmation on static clients` — handler was called (gate bypass). GREEN: 41 passed (confirmation.test.ts + planning-tools.test.ts) |
| 2 | TA1 AC-0 linked-record cascade delete | **Pre-resolved** by TRADE-CASCADE fix: `cascade="all, delete-orphan"` on `TradeModel.report`, `ondelete="CASCADE"` on FK, `delete_for_owner()` in service | 2423 passed, 0 failed (integration tests `test_delete_trade_with_linked_report`, `test_delete_trade_with_linked_images`) |
| 3 | Overclaimed docstring on mock test | Updated `test_delete_trade_with_linked_records` docstring to reflect route-layer scope, not FK reproduction | 33 passed in `test_api_trades.py` |
| 4 | Missing TA4 tool tests | Added 7 vitest tests: `list_trade_plans` (3), `delete_trade_plan` (3), confirmation list (+5 tools) | 258 passed (full vitest), 20 passed in `planning-tools.test.ts` |
| 5 | Work handoff template non-compliance | Rewrote handoff with CACHE BOUNDARY, AC table, FAIL_TO_PASS evidence, Commands, Quality Gate sections | Visual inspection against TEMPLATE.md |

### Fresh Quality Gate (post-corrections)

```
pytest: 2423 passed, 23 skipped, 0 failed
vitest: 258 passed, 0 failed (23 test files)
pyright: 0 errors
ruff: 0 violations
tsc --noEmit: clean
```

### Changed Files (this corrections pass)

| File | Change |
|------|--------|
| `mcp-server/src/middleware/confirmation.ts` | Added `delete_trade_plan` to `DESTRUCTIVE_TOOLS` |
| `mcp-server/tests/confirmation.test.ts` | Expanded destructive tools test list (+5 tools) |
| `mcp-server/tests/planning-tools.test.ts` | Added 7 tests for `list_trade_plans` and `delete_trade_plan` |
| `tests/unit/test_api_trades.py` | Fixed overclaimed docstring on mock test |
| `.agent/context/handoffs/2026-04-29-mcp-tool-remediation-handoff.md` | Rewritten to template compliance |

---

## Recheck (2026-04-29)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: GPT-5.5 Codex

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| 1. `delete_trade_plan` not in `DESTRUCTIVE_TOOLS` | fixed claim | Fixed. Source now includes `delete_trade_plan` in `DESTRUCTIVE_TOOLS`; static-client confirmation test covers it. |
| 2. TA1 AC-0 linked-record cascade delete unresolved | fixed claim | Fixed. Source now has report cascade, FK `ondelete="CASCADE"`, image cleanup port/impl, and real integration coverage. |
| 3. Weak linked-record route test overclaimed FK coverage | fixed claim | Fixed. Route-level test docstring no longer claims to reproduce the FK path; integration tests cover the real persistence path. |
| 4. TA4 list/delete MCP tools lacked direct tests | fixed claim | Fixed for the reviewed defect. Direct tests now cover `list_trade_plans`, `delete_trade_plan`, API failure/404 handling, and confirmation registry coverage. |
| 5. Work handoff evidence noncompliant | fixed claim | Fixed. Handoff now has cache boundary, AC table, `FAIL_TO_PASS`, command evidence, and quality gate evidence. |

### Commands Executed

| Command | Result |
|---------|--------|
| `git status --short` | Confirmed corrected files are present in the working tree. |
| `rg -n "delete_trade_plan|DESTRUCTIVE_TOOLS|createConfirmationToken|withConfirmation" ...` | Confirmed destructive registry entry, wrapper usage, and tests. |
| `rg -n "cascade=|ondelete|delete_for_owner|delete_trade_with_linked_report|delete_trade_with_linked_images" packages tests` | Confirmed cascade cleanup code and integration tests. |
| `uv run pytest tests/integration/test_api_roundtrip.py tests/unit/test_api_trades.py::TestDeleteTrade tests/unit/test_service_extensions.py::TestDeleteTrade tests/unit/test_ports.py -q` | 47 passed, 1 warning. |
| `cd mcp-server; npx vitest run tests/planning-tools.test.ts tests/confirmation.test.ts tests/accounts-tools.test.ts tests/settings-tools.test.ts` | 4 files passed, 67 tests passed. |
| `uv run python tools/validate_codebase.py --scope meu` | 8/8 blocking checks passed; Evidence Bundle advisory reports all evidence fields present. |

### Confirmed Fixes

- `mcp-server/src/middleware/confirmation.ts:29` includes `delete_trade_plan` in the destructive tool registry.
- `mcp-server/tests/confirmation.test.ts:156` verifies `delete_trade_plan` requires confirmation on static clients.
- `packages/infrastructure/src/zorivest_infra/database/models.py:63` and `:119` now cover report cascade and FK cascade.
- `packages/core/src/zorivest_core/services/trade_service.py:205-221` performs explicit report/image cleanup before trade delete.
- `tests/integration/test_api_roundtrip.py:175` and `:211` cover delete-with-report and delete-with-images round trips.
- `mcp-server/tests/planning-tools.test.ts:440-556` directly covers `list_trade_plans` and `delete_trade_plan`.
- `.agent/context/handoffs/2026-04-29-mcp-tool-remediation-handoff.md:46-72` contains cache boundary, `FAIL_TO_PASS`, commands, and quality gate sections.

### Remaining Findings

None blocking in this recheck. Residual risk: this pass did not run a live IDE/MCP audit after rebuilding `dist/`; it verified source, tests, and the MEU gate.

### Verdict

`approved` - The previously reported blocking findings are corrected in the current working tree, and the reproduced validation commands pass.
