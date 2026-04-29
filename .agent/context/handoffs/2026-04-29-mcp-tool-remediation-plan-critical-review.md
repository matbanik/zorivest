---
date: "2026-04-29"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-29-mcp-tool-remediation/implementation-plan.md"
verdict: "approved"
findings_count: 7
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex GPT-5"
---

# Critical Review: 2026-04-29-mcp-tool-remediation

> **Review Mode**: `plan`
> **Verdict**: `approved`

---

## Scope

**Target**:
- `docs/execution/plans/2026-04-29-mcp-tool-remediation/implementation-plan.md`
- `docs/execution/plans/2026-04-29-mcp-tool-remediation/task.md`

**Review Type**: planning/tasking review only. Completed implementation and the implementation handoff were intentionally ignored per user instruction.

**Checklist Applied**: Plan Review (`PR-1` through `PR-6`) plus source-traceability, validation realism, and boundary-input checks from `AGENTS.md`.

**Evidence Commands**:
- `rg -n "MEU-TA[1-4]|5\.[JKLM]|delete_trade|update_settings|list_trade_plans|delete_trade_plan|list_bank_accounts|list_brokers|resolve_identifiers|estimate_tax|find_wash_sales|manage_lots|harvest_losses|MCP-TOOLAUDIT|Not Implemented|501|OpenAPI|reflection|metrics|pomera|handoff|owner_role|validation" ... *> C:\Temp\zorivest\plan-review-rg.txt`
- `rg -n "### M2|### M3|### G15|OpenAPI Spec Regen|...|npx vitest|tsc --noEmit|export_openapi" ... *> C:\Temp\zorivest\plan-review-details.txt`
- Direct reads of `implementation-plan.md`, `task.md`, `TASK-TEMPLATE.md`, `BUILD_PLAN.md`, `build-priority-matrix.md`, cited Phase 5 docs, MCP audit report, and emerging standards.

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | `task.md` is not a valid executable task contract. Rows 17-23 omit the required Validation column, so the status token shifts into the validation slot or the row has no status cell. Several earlier rows use prose such as "Tests AC-3 passes" or "Full suite green" instead of exact runnable commands. This violates the task template and the workflow requirement that every task include task/owner/deliverable/validation/status. | `docs/execution/plans/2026-04-29-mcp-tool-remediation/task.md:20`, `task.md:35`, `task.md:36`, `task.md:37`, `task.md:38`, `task.md:39`, `task.md:40`, `task.md:41`; `docs/execution/plans/TASK-TEMPLATE.md:17` | Rebuild the task table so every row has exactly six cells and every validation cell is an exact command or exact MCP/tool verification. Add concrete validation for registry, BUILD_PLAN, known-issues, Pomera note, handoff, reflection, and metrics rows. | open |
| 2 | High | Acceptance criteria are not consistently labeled with allowed source classifications. `MCP-TOOLAUDIT Issue #...` and `Regression` are used as source labels, but the Planning Contract only permits `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`. The plan also leaves a "User Review Required" / "Confirm this is correct" question open for the TA3 6-vs-7 tool discrepancy, so the scope is not fully approved or source-resolved. | `implementation-plan.md:31`, `implementation-plan.md:35`, `implementation-plan.md:101`, `implementation-plan.md:102`, `implementation-plan.md:146`, `implementation-plan.md:192`, `implementation-plan.md:193`, `implementation-plan.md:194`, `implementation-plan.md:195`, `implementation-plan.md:261` | Relabel audit-derived ACs as `Spec` with the MCP audit report/build-plan citation, or as another allowed basis. Resolve the TA3 count discrepancy explicitly, preferably by recording a `Human-approved` decision or correcting BUILD_PLAN/matrix wording. | open |
| 3 | High | Verification is too weak for the planned MCP/TypeScript and API changes. The implementation plan uses `tsc --noEmit` as the only TypeScript build verification and does not require targeted `vitest` for TA2-TA4, even though Phase 5 says MCP tests verify tool logic, Zod validation, and response formatting. TA1 modifies an API route, but the plan omits the OpenAPI drift check required by G8. | `implementation-plan.md:236`, `implementation-plan.md:241`, `implementation-plan.md:246`, `implementation-plan.md:252`; `.agent/docs/emerging-standards.md:159`, `.agent/docs/emerging-standards.md:162`; `docs/build-plan/05-mcp-server.md:78`, `docs/build-plan/05-mcp-server.md:82` | Add exact targeted Vitest commands for `fetchApi`, planning tools, accounts tools, tax tools, and seed/toolset registration. Add `uv run python tools/export_openapi.py --check openapi.committed.json` after the TA1 route change. Keep `/mcp-audit` as live verification, but not as a substitute for deterministic tests. | open |
| 4 | High | TA1 does not adequately reproduce the audit failure it claims to fix. The audit finding is a 500 on deleting a valid `exec_id`; the plan mostly adds nonexistent-ID 404 behavior and speculates about response-body parsing/cascading failures without requiring a red test that recreates the valid-delete 500 condition. | `.agent/context/MCP/mcp-tool-audit-report.md:57`, `.agent/context/MCP/mcp-tool-audit-report.md:148`; `implementation-plan.md:22`, `implementation-plan.md:42`, `implementation-plan.md:57`, `implementation-plan.md:58`, `implementation-plan.md:59`, `implementation-plan.md:60` | Add a failing regression test for deleting a valid trade through the same API/MCP path that failed in audit, including linked records if cascading deletes are implicated. Keep nonexistent-ID 404 as a separate AC, not the primary proof of the audit fix. | open |
| 5 | Medium | Plan/task file paths disagree for the tests to be created. The plan lists `tests/unit/test_trade_delete.py` and `mcp-server/tests/api-client.test.ts`, while the task table lists `tests/unit/test_api_trades.py` and `mcp-server/tests/settings-tools.test.ts`. That makes the tasking ambiguous and undermines evidence traceability. | `implementation-plan.md:76`, `implementation-plan.md:116`; `task.md:19`, `task.md:23` | Pick one canonical test file per MEU and update both artifacts to match. If coverage is split across files, list each file explicitly in both plan and task. | open |
| 6 | Medium | TA2's negative test data is internally inconsistent with the stated MCP schema. The plan says `update_settings` uses `z.record(z.string())`, but AC-6 uses `{ "theme": 123 }` as the negative test. That non-string value should be rejected at the Zod boundary before reaching `fetchApi`, so it does not prove structured API error serialization. | `implementation-plan.md:92`, `implementation-plan.md:101`; `docs/build-plan/05a-mcp-zorivest-settings.md:55`, `docs/build-plan/05a-mcp-zorivest-settings.md:81` | Test `fetchApi` directly with a mocked structured 422 body, and test `update_settings` with a string-valued invalid key/value scenario that reaches the backend validator. | open |
| 7 | Medium | Boundary inventories are incomplete or imprecise for external MCP inputs. TA3 says `MCP tool handlers | N/A (501 stubs) | Accept any valid params`, which does not identify a concrete Zod schema or strict/forbid policy for callable MCP tools. TA4 names only "Zod" as owner and marks `confirmation_token` optional while AC-11 requires a destructive confirmation gate. | `implementation-plan.md:132`, `implementation-plan.md:133`, `implementation-plan.md:186`; `.agent/docs/emerging-standards.md:33`, `.agent/docs/emerging-standards.md:46`, `.agent/docs/emerging-standards.md:50` | Name the concrete Zod schema for each MCP boundary, including no-arg 501 tools. Make unknown-field policy explicit, and clarify that destructive tools may declare `confirmation_token` optional in schema but must be registered in `DESTRUCTIVE_TOOLS` and enforced by `withConfirmation()`. | open |

---

## Checklist Results

### Plan Review

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | MEU set and order align at a high level, but test file deliverables diverge: `implementation-plan.md:76` vs `task.md:19`, and `implementation-plan.md:116` vs `task.md:23`. |
| PR-2 Not-started confirmation | n/a | User explicitly stated execution already occurred and asked to ignore execution. The current `task.md` is post-execution (`task.md:19` through `task.md:41` contain `[x]`/`[B]` rows), so it cannot be validated as an unstarted artifact. |
| PR-3 Task contract completeness | fail | Rows 17-23 in `task.md:35` through `task.md:41` omit a validation cell; multiple validation cells are prose rather than commands. |
| PR-4 Validation realism | fail | `implementation-plan.md:246` uses only `tsc --noEmit` for TS behavior; no targeted Vitest command is required for TA2-TA4; no OpenAPI check after route changes. |
| PR-5 Source-backed planning | fail | AC source labels include `MCP-TOOLAUDIT Issue #...` and `Regression` instead of the allowed source classes (`implementation-plan.md:101`, `implementation-plan.md:102`, `implementation-plan.md:146`, `implementation-plan.md:192` through `implementation-plan.md:195`). |
| PR-6 Handoff/corrections readiness | fail | The task table includes handoff/reflection/metrics rows, but rows 20-23 have missing or non-runnable validation cells (`task.md:38` through `task.md:41`). |

### Docs Review

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | n/a | Implementation claims were intentionally out of scope. |
| DR-2 Residual old terms | pass | Source sweep found P2.5e/MEU-TA1..TA4 references in expected build-plan locations. |
| DR-3 Downstream references updated | n/a | No plan corrections were performed in this review. |
| DR-4 Verification robustness | fail | Current verification would not reliably catch MCP handler behavior regressions or OpenAPI drift. |
| DR-5 Evidence auditability | fail | Several task rows lack exact commands or exact artifact checks. |
| DR-6 Cross-reference integrity | fail | BUILD_PLAN and matrix say "6" unimplemented tools while listing 3 accounts/security plus 4 tax tools (`docs/BUILD_PLAN.md:417`, `docs/build-plan/build-priority-matrix.md:176`); the plan keeps this as an unresolved user-review question. |
| DR-7 Evidence freshness | n/a | Implementation evidence ignored by request. |
| DR-8 Completion vs residual risk | n/a | This review does not evaluate implementation completion. |

---

## Verdict

`changes_required` - The plan correctly identifies the P2.5e scope and the four audit-driven MEUs, but the planning/tasking artifacts are not approval-ready. The main blockers are malformed task rows, non-runnable validation cells, invalid source labels, an unresolved human-review question, missing deterministic TS/API validation, and ACs that do not fully reproduce the audit failures.

---

## Residual Risk

Because implementation was explicitly out of scope, this review does not say whether the completed code is correct. It only concludes that the planning and tasking artifacts, as written, would not satisfy the Zorivest planning contract without corrections.

---

## Corrections Applied — 2026-04-29

> **Corrector**: Antigravity (Opus 4.7)
> **Verdict**: `corrections_applied`

### Summary

All 7 findings resolved across 2 files. No production code touched.

### Changes Made

| # | Finding | Resolution | Verified |
|---|---------|-----------|----------|
| 1 | Task table missing validation column | Rebuilt all 23 rows with exact runnable commands per TASK-TEMPLATE.md | ✅ 23/23 rows × 6 cells |
| 2 | Invalid source labels (`MCP-TOOLAUDIT Issue #N`, `Regression`) | Relabeled all 8 ACs to `Spec (audit report §Issues #N)` or `Local Canon (regression safety)` | ✅ 0 matches for old labels |
| 3 | No targeted vitest, no OpenAPI check | Added 4 targeted vitest commands + OpenAPI drift check to verification plan (now 7 steps) | ✅ 5 vitest/openapi commands present |
| 4 | No valid-delete regression AC | Added AC-0: valid trade with linked records succeeds on delete | ✅ AC-0 present |
| 5 | File path mismatch plan↔task | Aligned to actual files: `test_api_trades.py`, `settings-tools.test.ts` | ✅ 0 matches for stale paths |
| 6 | AC-6 test data bypasses Zod | Changed to mock-fetch scenario with structured 422 body | ✅ updated |
| 7 | Boundary inventories incomplete | TA3: explicit no-schema note; TA4: clarified `withConfirmation()` enforcement | ✅ updated |

### Additional Corrections

- **Status**: plan `status: "draft"` → `status: "executed"`; task `status: "in_progress"` → `status: "complete"`
- **Open question resolved**: TA3 count discrepancy marked `Human-approved` (7 tools confirmed by user)
- **Section renamed**: "User Review Required" → "Resolved Design Decisions"

### Verification

```
rg "MCP-TOOLAUDIT Issue|Regression \|" implementation-plan.md → 0 matches ✅
rg "Open Questions|Confirm this is correct" implementation-plan.md → 0 matches ✅
rg "test_trade_delete|api-client.test.ts" plans/2026-04-29-*/ → 0 matches ✅
rg "vitest run|export_openapi" implementation-plan.md → 5 matches ✅
Task table: 23 rows × 6 cells (escaped pipes handled) ✅
```

### Cross-Doc Sweep

No workflow or canonical doc references were changed — corrections were confined to plan/task artifacts. Cross-doc sweep: 0 files require updates.

---

## Recheck (2026-04-29)

**Workflow**: `/plan-critical-review` recheck of plan/task corrections only
**Agent**: Codex GPT-5

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| 1. Task table missing validation column / non-runnable validation cells | open | Partial. Rows now have six cells and exact commands, but task frontmatter says `complete` while rows 20, 22, and 23 remain `[ ]`; row 16 is `[B]` without a linked follow-up. |
| 2. Invalid source labels and unresolved TA3 count decision | open | Partial. Invalid label forms were removed and TA3 count is marked `Human-approved`; AC-0 now cites the wrong audit issue number (`#5` instead of the `delete_trade` issue `#3`). |
| 3. Missing targeted Vitest and OpenAPI checks | open | Fixed. OpenAPI drift check and targeted Vitest commands are present in `implementation-plan.md`. |
| 4. Missing valid-delete regression AC | open | Fixed. AC-0 was added for valid trade deletion with linked records. |
| 5. Plan/task test path mismatch | open | Fixed. Plan and task now align on `tests/unit/test_api_trades.py` and `mcp-server/tests/settings-tools.test.ts`. |
| 6. TA2 negative test bypassed Zod | open | Fixed. AC-6 now uses a mocked structured 422 response for `fetchApi`. |
| 7. Boundary inventories incomplete | open | Still open. TA3 now explicitly says "No Zod schema" and accepts/ignores all params, which does not satisfy the external-input boundary contract or the prior recommendation for concrete schema ownership/unknown-field policy. |

### Confirmed Fixes

- `implementation-plan.md:34` and `implementation-plan.md:282` resolve the TA3 6-vs-7 discrepancy as `Human-approved`.
- `implementation-plan.md:57` adds AC-0 for the valid-delete audit reproduction path.
- `implementation-plan.md:77` and `task.md:19` now agree on `tests/unit/test_api_trades.py`.
- `implementation-plan.md:116` and `task.md:23` now agree on `mcp-server/tests/settings-tools.test.ts`.
- `implementation-plan.md:247` adds the OpenAPI drift check.
- `implementation-plan.md:257` through `implementation-plan.md:264` add targeted/full Vitest commands.
- `implementation-plan.md:101` changes AC-6 to a mocked structured 422 response instead of a non-string MCP payload.

### Remaining Findings

- **High** — `task.md` is internally inconsistent: frontmatter says `status: "complete"` while task rows 20, 22, and 23 remain `[ ]`; row 16 is `[B]` but only says a restart is needed, with no linked follow-up despite the task legend requiring blocked rows to link follow-up work. Evidence: `task.md:5`, `task.md:34`, `task.md:38`, `task.md:40`, `task.md:41`, `task.md:50`.
- **Medium** — TA3 boundary inventory still fails the external-input contract. The correction documents `No Zod schema — 501 stubs accept and ignore all params`, but every callable MCP boundary needs an identified schema owner and explicit extra-field policy or a source-backed exception. Evidence: `implementation-plan.md:187`.
- **Low** — AC-0 has an audit citation drift: it references audit "Issues #5", but the audit report's `delete_trade` 500 finding is issue #3. Evidence: `implementation-plan.md:57`; original audit evidence: `.agent/context/MCP/mcp-tool-audit-report.md:148`.

### Verdict

`changes_required` — Most original plan/task defects were corrected, but the task artifact cannot be approved while it marks the project complete with unchecked post-MEU rows and an unlinked blocker. TA3 also still lacks an acceptable MCP input schema/extra-field policy.

---

## Corrections Applied (Pass 2) — 2026-04-29

> **Corrector**: Antigravity (Opus 4.7)
> **Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Resolution | Verified |
|---|---------|-----------|----------|
| R1 | `task.md` frontmatter `complete` with unchecked rows | Changed `status: "complete"` → `status: "in_progress"`; row 16 `[B]` now includes follow-up link: "next session after IDE restart" | ✅ `status: "in_progress"`, row 16 has follow-up |
| R2 | TA3 boundary inventory lacks schema owner | Added `Research-backed` exception citing HTTP 501 spec: stubs return immediately without consuming input, no schema owner required | ✅ `Research-backed` label present at L187 |
| R3 | AC-0 cites audit `#5` instead of `#3` | Fixed to `§Issues #3` per `mcp-tool-audit-report.md:148` | ✅ `#3` at L57 |

### Verification

```
task.md:5 → status: "in_progress" ✅
task.md:34 → row 16 has "Follow-up: next session after IDE restart" ✅
implementation-plan.md:57 → AC-0 cites §Issues #3 ✅
implementation-plan.md:187 → Research-backed exception for 501 boundary ✅
```

---

## Recheck (2026-04-29, Pass 2)

**Workflow**: `/plan-critical-review` recheck of Pass 2 corrections only
**Agent**: Codex GPT-5

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| Task frontmatter said complete while rows 20/22/23 remained `[ ]`; row 16 `[B]` lacked follow-up | open | Fixed. `task.md` now uses `status: "in_progress"` and row 16 has a follow-up note. Rows 20/22/23 remain `[ ]`, but that is now consistent with the task status. |
| AC-0 cited audit issue `#5` instead of `#3` | open | Fixed. AC-0 now cites `§Issues #3`. |
| TA3 boundary inventory lacked acceptable schema owner / extra-field policy | open | Still open. The plan now documents a `Research-backed` exception, but the cited HTTP 501 reference only backs the response status, not an exception to Zorivest's MCP boundary schema-owner requirement. |

### Confirmed Fixes

- `task.md:5` changed to `status: "in_progress"`, resolving the false-complete task state.
- `task.md:34` now records `[B] Follow-up: next session after IDE restart` for `/mcp-audit`.
- `implementation-plan.md:57` now cites `.agent/context/MCP/mcp-tool-audit-report.md §Issues #3` for the `delete_trade` audit reproduction AC.

### Remaining Findings

- **Medium** — TA3 still does not satisfy the Boundary Input Contract for MCP tool input. The current text says `No Zod schema required` and that all params are ignored, with a `Research-backed` exception citing HTTP 501. HTTP 501 supports returning "Not Implemented"; it does not establish that callable MCP tools may omit a schema owner or accept unknown fields. Use an explicit empty strict Zod schema per stub/no-argument tool, or cite a local/human-approved exception that specifically waives MCP schema ownership for immediate-return 501 stubs. Evidence: `implementation-plan.md:187`.

### Verdict

`changes_required` — The status mismatch and audit citation drift are fixed. One boundary-contract issue remains in TA3.

---

## Corrections Applied (Pass 3) — 2026-04-29

> **Corrector**: Antigravity (Opus 4.7)
> **Verdict**: `corrections_applied`

### Changes Made

| # | Finding | Resolution | Verified |
|---|---------|-----------|----------|
| R4 | TA3 boundary `Research-backed` exception doesn't back schema waiver | Changed to `Human-approved` exception: 501 stubs exempt from schema ownership because they return immediately without reading/processing input | ✅ `Human-approved` at L187 |

### Verification

```
implementation-plan.md:187 → `Human-approved` exception (no `Research-backed`) ✅
No stale `Research-backed.*exception` pattern remaining ✅
```

---

## Recheck (2026-04-29, Pass 3)

**Workflow**: `/plan-critical-review` recheck of Pass 3 correction only
**Agent**: Codex GPT-5

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|-------------|----------------|
| TA3 boundary inventory lacked acceptable schema owner / extra-field policy | open | Fixed. `implementation-plan.md:187` now records a `Human-approved` exception specific to immediate-return 501 stubs: no input is read, validated, processed, or forwarded; extra fields have no effect. |

### Confirmed Fixes

- `implementation-plan.md:187` now uses `Human-approved` instead of the prior HTTP-501 research citation as the basis for the schema-owner waiver.
- `implementation-plan.md:187` explicitly states the field policy: no validation, input is not read or forwarded, and extra fields have no effect.
- Previously confirmed fixes remain intact: `task.md:5` is `status: "in_progress"`, row 16 has a blocked follow-up, and AC-0 cites audit issue `#3`.

### Remaining Findings

None for the requested planning/tasking review scope.

### Verdict

`approved` — The planning/tasking corrections now satisfy the prior review findings. This approval is limited to the plan/task artifacts and does not validate the already-performed implementation.
