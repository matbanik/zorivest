---
date: "2026-04-25"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-04-25-pipeline-security-hardening/implementation-plan.md"
verdict: "changes_required"
findings_count: 8
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-04-25-pipeline-security-hardening

> **Review Mode**: `plan`
> **Verdict**: `changes_required`

---

## Scope

**Target**:
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/implementation-plan.md`
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/task.md`

**Review Type**: Plan review before implementation.

**Checklist Applied**: Plan Review (PR-1 through PR-6), Docs Review applicability checks, Zorivest FIC/TDD planning contract, P0 terminal validation contract.

**Canonical sources checked**:
- `docs/build-plan/09c-pipeline-security-hardening.md`
- `docs/execution/plans/TASK-TEMPLATE.md`
- `AGENTS.md`
- `.agent/workflows/plan-critical-review.md`
- `.agent/workflows/tdd-implementation.md`
- Current touchpoint files under `packages/core/` and `packages/infrastructure/`

**Status readiness**: Plan-review mode is valid. The PH1/PH2/PH3 product and test files do not exist yet, and no correlated implementation handoff exists. `task.md` has all task rows unchecked.

---

## Commands Executed

All terminal commands used redirect-to-file receipts under `C:\Temp\zorivest\`.

| Purpose | Command / Evidence |
|---|---|
| Session start | `pomera_diagnose(verbose=false)` succeeded; `pomera_notes(search_term="Zorivest")` succeeded; `text-editor` reads succeeded |
| Required context | Read `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/workflows/plan-critical-review.md`, target plan, target task |
| Spec and roles | Read `docs/build-plan/09c-pipeline-security-hardening.md`, `TASK-TEMPLATE.md`, orchestrator/tester/reviewer roles, review template |
| File-state sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-sweeps.txt` |
| Targeted grep sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-targeted.txt` |
| FIC/TDD contract sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-tdd.txt` |
| Approval provenance sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-approval.txt` |

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|---|---|---|---|---|
| 1 | High | The task order violates the mandatory FIC/TDD contract. Zorivest requires a source-backed FIC before code, then all tests first and a red-phase failure. The task starts by writing `safe_copy.py`, updating `pipeline.py`, adding `sqlglot`, and writing `sql_sandbox.py` before writing PH1/PH2/PH3 tests. | `AGENTS.md:227`, `AGENTS.md:232-234`; `task.md:19-34` | Add per-MEU FIC tasks with AC labels first, then write all tests, run and save failing output, then implementation tasks. | open |
| 2 | Critical | The plan narrows the PH2 SQLCipher security boundary without an approved source. The spec requires SQLCipher-aware `open_sandbox_connection(db_path, key, read_only=True)` and a `connection.py` change, but the plan proposes a standard `sqlite3` connection and asks for confirmation while the task table proceeds as executable work. | `docs/build-plan/09c-pipeline-security-hardening.md:149`, `docs/build-plan/09c-pipeline-security-hardening.md:167-168`, `docs/build-plan/09c-pipeline-security-hardening.md:220`; `implementation-plan.md:71`, `implementation-plan.md:173`, `task.md:23-29` | Treat this as blocked until human-approved or revise PH2 to implement SQLCipher read-only connection support in the proper layer. | open |
| 3 | High | PH2 scope omits required schema-discovery filtering and tests. The spec requires backend filtering of `SqlSandbox.DENY_TABLES` for `GET /scheduling/db-schema` and schema-discovery tests; the plan only includes 18 sandbox tests and no API/MCP schema-discovery work. | `docs/build-plan/09c-pipeline-security-hardening.md:267-279`, `docs/build-plan/09c-pipeline-security-hardening.md:311-324`; `implementation-plan.md:110-131`, `task.md:29` | Resolve the spec ambiguity about MEU-PH9 ownership, then either include these tasks/tests in PH2 or explicitly mark them blocked with a source-backed deferral. | open |
| 4 | High | PH2 omits co-delivered secrets scanning and policy content IDs. The spec says `9C.5 Secrets Scanning` and `9C.6 Content-Addressable Policy IDs` are co-delivered with MEU-PH2; neither appears in the plan or task table. | `docs/build-plan/09c-pipeline-security-hardening.md:429-456`, `docs/build-plan/09c-pipeline-security-hardening.md:456-468`; `implementation-plan.md:51-131`, `task.md:22-29` | Add source-backed FIC criteria, tests, and tasks for `scan_for_secrets()` and the content-addressable policy ID contract, or document that existing `compute_content_hash()` fully satisfies 9C.6 with evidence. | open |
| 5 | High | PH3 verification is incomplete. The spec requires MIME mismatch and fan-out tests, and the exit criteria require both 5 URLs/step and 10 URLs/policy. The plan’s PH3 tests omit `test_fetch_rejects_mime_mismatch` and `test_fetch_fan_out_cap`, and the open question proposes deferring the policy-level cap. | `docs/build-plan/09c-pipeline-security-hardening.md:404-424`; `implementation-plan.md:156-166`, `implementation-plan.md:176`, `task.md:32-34` | Add explicit tests and implementation tasks for MIME mismatch, per-step fan-out, and per-policy fan-out, or block on human decision before approval. | open |
| 6 | High | StepContext isolation does not cover the actual write path. The plan adds `put_output()`, but current `PipelineRunner` writes `context.outputs[step_def.id] = step_result.output` directly. Without a task to replace direct writes with the new safe API, the core mutation bug remains in real runs. | `packages/core/src/zorivest_core/services/pipeline_runner.py:201`, `packages/core/src/zorivest_core/services/pipeline_runner.py:240`; `implementation-plan.md:31-33`, `task.md:20` | Add explicit runner migration tasks and tests proving real `PipelineRunner` execution stores isolated copies, not just direct `StepContext.put_output()` unit tests. | open |
| 7 | Medium | The new dependency target is underspecified and likely wrong for packaging. `sql_sandbox.py` is planned under `zorivest_core`, but the task says add `sqlglot` to `pyproject.toml`; the root `pyproject.toml` only depends on workspace packages, while `packages/core/pyproject.toml` owns core runtime dependencies. | `implementation-plan.md:106-108`, `task.md:22`; `pyproject.toml:5-9`, `packages/core/pyproject.toml:5-10` | Specify `packages/core/pyproject.toml` as the dependency owner and validate package metadata, not only root-workspace importability. | open |
| 8 | Medium | Validation commands in the plan/task are not P0-compliant receipts. The plan lists raw `pytest`, `pyright`, `ruff`, and `validate_codebase.py` commands, but Zorivest P0 requires all terminal execution to redirect all streams to `C:\Temp\zorivest\` and then read the receipt. | `AGENTS.md:25-46`; `implementation-plan.md:185-204`, `task.md:35-38` | Rewrite validation cells with the mandatory redirect-to-file command forms so implementation can execute the plan without violating P0. | open |

---

## Checklist Results

### Plan Review

| Check | Result | Evidence |
|---|---|---|
| PR-1 Plan/task alignment | fail | Both files name PH1-PH3, but task order and omitted work do not match the 09c source contract. |
| PR-2 Not-started confirmation | pass | New PH files/tests were absent; no correlated handoff exists; all task rows unchecked. |
| PR-3 Task contract completeness | mixed | Rows have task/owner/deliverable/validation/status fields, but FIC/red-phase tasks are missing. |
| PR-4 Validation realism | fail | Raw validation commands violate P0 receipt pattern and miss required PH2/PH3 tests. |
| PR-5 Source-backed planning | fail | SQLCipher and fan-out deferrals are open human decisions but the task table proceeds. |
| PR-6 Handoff/corrections readiness | pass | Canonical correction route is `/plan-corrections`; no product changes made in this review. |

### Docs Review Applicability

| Check | Result | Evidence |
|---|---|---|
| DR-1 Claim-to-state match | pass | File-state sweep confirms implementation not started. |
| DR-3 Downstream references | fail | Plan does not include required PH2 schema-discovery API/MCP filter follow-through or MEU registry update task. |
| DR-4 Verification robustness | fail | Missing tests for schema discovery, secrets scan, MIME mismatch, and fan-out caps. |
| DR-5 Evidence auditability | fail | Planned validation commands lack P0 receipts and red-phase evidence capture. |
| DR-8 Completion vs residual risk | fail | Open questions are material blockers, not residual risk for an approvable plan. |

---

## Open Questions / Assumptions

- The spec has an internal ownership ambiguity: schema-discovery tests are marked "Owner: MEU-PH9" but PH2 exit criteria also require them. This must be resolved explicitly before PH2 approval.
- Existing scheduling approval fields and `PipelineGuardrails` may satisfy part of the new approval provenance contract, but the plan does not explain how `StepContext.policy_approval` and `policy_hash` are populated from that existing state.
- I did not run product tests because this was a review-only workflow and implementation has not started.

---

## Open Questions Investigation (2026-04-25)

### Q1. Is standard `sqlite3` acceptable for PH2, with SQLCipher deferred?

**Answer:** No. PH2 should implement a SQLCipher-aware sandbox connection now, while preserving a plain `sqlite3` fallback for environments where `sqlcipher3` is unavailable.

**Reasoning:**
- `09c` defines SQLCipher-aware `open_sandbox_connection(db_path, key, read_only=True)` as part of PH2, and lists the `connection.py` factory as an explicit file change.
- The existing infrastructure already treats SQLCipher as the encrypted production path and plain `sqlite3` as a logged fallback in `create_encrypted_connection()`.
- A plain `sqlite3` sandbox is not equivalent in production: it cannot open SQLCipher-encrypted DB files when SQLCipher is active, and it sidesteps the encrypted-at-rest boundary already delivered by Phase 2.
- The domain dependency rule still matters. The clean implementation is to keep core sandbox logic connection-source agnostic, and add the SQLCipher/read-only connection factory in infrastructure. Core should not import infrastructure.

**Correction guidance:** PH2 should add:
- Core: `SecurityError`, SQL AST validation, `SqlSandbox`/connection-wrapper behavior over a connection-like protocol.
- Infrastructure: `open_sandbox_connection(...)` that opens SQLCipher read-only when available and mirrors the existing plain `sqlite3` fallback with clear logging.
- API/runtime wiring: instantiate the sandbox from the infra factory and inject only `sql_sandbox` into step context.

### Q2. Who owns schema-discovery filtering and tests: PH2 or PH9?

**Answer:** PH9 owns the route/resource/tool implementation and the four schema-discovery tests. PH2 owns the security primitive that PH9 must reuse: `SqlSandbox.DENY_TABLES` and SQL execution denial.

**Reasoning:**
- `09c` has conflicting language: the schema-discovery tests are explicitly marked "Owner: MEU-PH9", while PH2 exit criteria also say "All 20 tests pass" and require `GET /scheduling/db-schema`.
- `05g-mcp-scheduling.md` is more specific for MCP/schema-discovery surfaces: it assigns `pipeline://db-schema`, `list_db_tables`, and `get_db_row_samples` to MEU-PH9 and says they fetch `GET /scheduling/db-schema`.
- PH9 is also listed in the build-priority matrix as the owner of "11 new MCP tools: emulator, schema discovery, template CRUD".

**Correction guidance:** Do not implement PH9 API/MCP schema discovery inside the PH1-PH3 plan. Instead:
- Fix the plan/task to say PH2 has 18 sandbox tests plus a source-backed PH9 follow-up contract.
- Fix or annotate the 09c PH2 exit criteria so "All 20 tests" is not used as the PH2 gate unless PH9 is also in scope.
- Keep a PH2 test proving `DENY_TABLES` includes the sensitive tables, because that is the contract PH9 consumes.

### Q3. How should `StepContext.policy_approval` and `policy_hash` be populated?

**Answer:** Use the existing policy approval state; do not introduce a second persistent approval store for PH3.

**Reasoning:**
- Existing `PolicyModel` already stores `content_hash`, `approved`, `approved_at`, and `approved_hash`.
- Existing `SchedulingService.approve_policy()` sets `approved=True`, `approved_at=now`, and `approved_hash=content_hash`.
- Existing `PipelineGuardrails.check_policy_approved()` blocks unapproved policies and hash mismatches before `PipelineRunner.run()` starts.
- The missing link is runtime propagation into `StepContext`, not persistence.

**Correction guidance:** Add a lightweight runtime approval snapshot and pass it through the run path:
- Define a core dataclass, e.g. `PolicyApproval`, with `policy_id`, `content_hash`, `approved_at`, and `approved_by`.
- In `SchedulingService.trigger_run()`, after guardrails pass, construct `PolicyApproval(policy_id=policy_id, content_hash=policy["approved_hash"], approved_at=policy["approved_at"], approved_by=policy.get("created_by") or "system")`.
- Extend `PipelineRunner.run(..., policy_approval=None, has_user_confirmation=False)` and set `StepContext.policy_approval`, `StepContext.policy_hash=content_hash`, and `StepContext.has_user_confirmation`.
- `SendStep` should allow `requires_confirmation=False` only when `context.policy_approval.content_hash == context.policy_hash`.

**Important distinction:** `approved` is not the same as interactive confirmation. `has_user_confirmation=True` should only come from an explicit UI/manual confirmation path. Existing policy approval should satisfy the opt-out provenance path, not silently mark every send step as interactively confirmed.

### Q4. Should the 10 URLs/policy fan-out cap be deferred to PH4?

**Answer:** No. The 10 URLs/policy cap belongs in PH3 because it is part of `09c` FetchStep content/fan-out hardening.

**Reasoning:**
- `09c §9C.4b` states "max 5 URLs per step, max 10 per policy execution"; `9C.4d` repeats that FetchStep enforces both.
- PH4 has its own QueryStep fan-out contract: max 5 queries per step and global pool max 10 per policy. That is a separate SQL-query budget, not a reason to defer FetchStep URL limits.
- Current adapter behavior makes this enforceable: multi-ticker fetches call one provider request per ticker in `_fetch_multi_ticker()`, so the URL count can be computed as `max(1, len(tickers))` for the current FetchStep path.

**Correction guidance:** PH3 should implement both:
- Per-step cap in `FetchStep` after criteria resolution and before provider calls.
- Per-policy cap in the runner/context path, e.g. `StepContext.fetch_url_count` or a runner-owned counter incremented before each fetch executes.

### Additional Conflict Found

`p2.5c_security_hardening_analysis.md` says FetchStep uses a 10 MB per-response cap, but `09c §9C.4b` says `MAX_FETCH_BODY_BYTES = 5 * 1024 * 1024`. The target build-plan spec is the higher authority for this MEU. Use **5 MB** unless the build plan is explicitly changed.

---

## Verdict

`changes_required` — the plan is not ready for implementation. It has security-significant scope narrowing, missing source-backed acceptance criteria, missing required tests, and a task order that violates the mandatory FIC/TDD workflow.

---

## Follow-Up Actions

1. Run `/plan-corrections` against this canonical review handoff.
2. Revise PH2 to implement the SQLCipher-aware sandbox connection path now, with a plain `sqlite3` fallback matching existing infrastructure behavior.
3. Rebuild the plan around FIC-first, tests-first MEU sequencing with red-phase evidence capture.
4. Add the omitted PH2/PH3 scope: secrets scanning, content IDs, MIME mismatch, and both FetchStep fan-out caps. Move schema-discovery route/resource/tool work and its four tests to an explicit PH9 follow-up contract.
5. Rewrite validation commands with P0 redirect receipts.

---

## Recheck (2026-04-25)

**Review Mode:** `plan` recheck  
**Targets:**
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/implementation-plan.md`
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/task.md`

**Latest Verdict:** `changes_required`

### Recheck Commands / Evidence

All shell commands used redirect-to-file receipts under `C:\Temp\zorivest\`.

| Purpose | Evidence |
|---|---|
| Session start | `pomera_diagnose(verbose=false)` succeeded; `pomera_notes(search_term="Zorivest")` succeeded; `text-editor` reads succeeded |
| Workflow/context read | Read `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/workflows/plan-critical-review.md`, target plan, target task, and this canonical review file |
| Source/spec sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-recheck.txt` |
| Deliverables sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-deliverables.txt` |

### Prior Finding Recheck

| Prior # | Status | Evidence |
|---|---|---|
| 1. FIC/TDD task order violation | fixed | `task.md:19-33` now sequences each PH as FIC -> Red tests -> Green implementation -> MEU gate. |
| 2. SQLCipher boundary narrowed | fixed | `implementation-plan.md:27`, `implementation-plan.md:94`, and `implementation-plan.md:120` require SQLCipher-aware `open_sandbox_connection()` with fallback. |
| 3. Schema-discovery ownership ambiguity | fixed/accepted | `implementation-plan.md:112`, `implementation-plan.md:129-136`, and `implementation-plan.md:183` assign route/resource/tool work and four schema-discovery tests to PH9 while PH2 owns the `DENY_TABLES` contract. This matches `05g` PH9 ownership. |
| 4. Secrets scan and content IDs omitted | fixed | `implementation-plan.md:95-98`, `implementation-plan.md:121-127`, and `task.md:25-26` include `scan_for_secrets()` and `policy_content_id()` work. |
| 5. PH3 MIME/fan-out incomplete | fixed | `implementation-plan.md:151-154`, `implementation-plan.md:162-176`, and `task.md:31-32` cover MIME mismatch, 5 MB body cap, 5 URLs/step, and 10 URLs/policy. |
| 6. Runner write path not migrated | fixed | `implementation-plan.md:56`, `implementation-plan.md:72-74`, and `task.md:22` explicitly migrate direct `context.outputs[...]` writes to `context.put_output()`. |
| 7. `sqlglot` dependency target underspecified | fixed | `implementation-plan.md:126` and `task.md:28` specify `packages/core/pyproject.toml`. |
| 8. P0 validation commands missing receipts | fixed | `task.md:20-41` uses receipt files under `C:\Temp\zorivest\`. Implementation-plan verification snippets redirect long-running tool output before reading receipt tails. |

### Remaining Finding

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|---|---|---|---|---|
| 9 | Medium | The corrected task still omits required project-state deliverables for execution completion. AGENTS requires post-MEU deliverables including registry update and `BUILD_PLAN.md` update, plus current-focus updates when the session changes project state. The task includes a `docs/BUILD_PLAN.md` grep audit, Pomera note, handoff, reflection, and metrics, but no `.agent/context/meu-registry.md` status update, no explicit `docs/BUILD_PLAN.md` status update, and no `.agent/context/current-focus.md` update. | `AGENTS.md:119`, `AGENTS.md:250`, `AGENTS.md:265`; `task.md:37-41`; `implementation-plan.md:189-194` | Add explicit final tasks for `.agent/context/meu-registry.md`, `docs/BUILD_PLAN.md` status updates for PH1-PH3, and `.agent/context/current-focus.md` session outcome update. Keep review-only sessions excluded per `AGENTS.md:119`. | open |

### Checklist Results (Latest)

| Check | Result | Evidence |
|---|---|---|
| PR-1 Plan/task alignment | pass | Plan and task both cover PH1-PH3, same test files, same dependency and runtime touchpoints. |
| PR-2 Not-started confirmation | pass | File-state sweep shows planned PH files/tests do not exist; only the plan review handoff exists. |
| PR-3 Task contract completeness | mixed | Each row has task/owner/deliverable/validation/status, but final project-state deliverable rows are missing. |
| PR-4 Validation realism | pass | Per-PH red/green commands, full regression, pyright, ruff, and MEU gates are explicit with receipts. |
| PR-5 Source-backed planning | pass | SQLCipher, schema-discovery split, approval provenance, body cap, and fan-out rules are source-tagged or human-approved. |
| PR-6 Handoff/corrections readiness | pass | Remaining fix is plan/task-only and can be handled through `/plan-corrections`. |

### Latest Verdict

`changes_required` — the security and TDD contract findings from the first review are resolved, but the execution task is still missing mandatory final project-state update tasks. This is a process-contract blocker, not a product-security blocker.

---

## Recheck (2026-04-25, Pass 2)

**Review Mode:** `plan` recheck  
**Targets:**
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/implementation-plan.md`
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/task.md`

**Latest Verdict:** `changes_required`

### Recheck Commands / Evidence

All shell commands used redirect-to-file receipts under `C:\Temp\zorivest\`.

| Purpose | Evidence |
|---|---|
| Session start | `pomera_diagnose(verbose=false)` succeeded; `pomera_notes(search_term="Zorivest")` succeeded; `text-editor` reads succeeded |
| Workflow/context read | Read `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/skills/terminal-preflight/SKILL.md`, `.agent/workflows/plan-critical-review.md`, target plan, target task, and this canonical review file |
| Scope/security/deliverable sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-recheck-2.txt` |
| BUILD_PLAN section-location sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-section-location.txt` |

### Prior Finding Recheck

| Prior # | Status | Evidence |
|---|---|---|
| 1-8 | fixed/accepted | Same status as prior recheck; no regressions found in SQLCipher, PH9 schema-discovery split, secrets/content IDs, MIME/body/fan-out caps, runner output migration, dependency ownership, or P0 receipt commands. |
| 9. Missing project-state deliverables | fixed | `task.md:42-44` now adds explicit tasks for `.agent/context/meu-registry.md`, `docs/BUILD_PLAN.md`, and `.agent/context/current-focus.md`. |

### Remaining Finding

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|---|---|---|---|---|
| 10 | Medium | The new BUILD_PLAN status task has a mismatched target and validation command. It says to update `docs/BUILD_PLAN.md` status for PH1-PH3 exit criteria and mark checkboxes in `§9C.1f`, `§9C.2f`, and `§9C.4d`, but those exit-criteria checkboxes live in `docs/build-plan/09c-pipeline-security-hardening.md`, not `docs/BUILD_PLAN.md`. Meanwhile `docs/BUILD_PLAN.md` has PH1-PH3 index rows using `⬜` status markers, not `[ ]` checkboxes. The current validation `rg "\[x\].*PH[123]" docs/BUILD_PLAN.md` would not prove the stated exit-criteria update and may fail even if the index rows are correctly marked. | `task.md:43`; `docs/build-plan/09c-pipeline-security-hardening.md:112-116`, `docs/build-plan/09c-pipeline-security-hardening.md:316-325`, `docs/build-plan/09c-pipeline-security-hardening.md:419-424`; `docs/BUILD_PLAN.md:372-374` | Split this into two precise tasks or rewrite the existing task: one for `docs/build-plan/09c-pipeline-security-hardening.md` exit criteria (`§9C.1f`, `§9C.2f`, `§9C.4d`) and one for `docs/BUILD_PLAN.md` PH1-PH3 index row status. Use validation commands that match the actual markers in each file. | open |

### Checklist Results (Latest)

| Check | Result | Evidence |
|---|---|---|
| PR-1 Plan/task alignment | pass | Plan and task still cover PH1-PH3 with coherent source-backed scope. |
| PR-2 Not-started confirmation | pass | Planned PH files/tests are absent; no correlated implementation handoff exists. |
| PR-3 Task contract completeness | mixed | Rows exist for final project-state deliverables, but task 25's deliverable/validation target is inconsistent. |
| PR-4 Validation realism | mixed | Core red/green/quality commands are realistic; task 25 validation does not prove the stated BUILD_PLAN/exit-criteria update. |
| PR-5 Source-backed planning | pass | Security and approval decisions remain source-backed or human-approved. |
| PR-6 Handoff/corrections readiness | pass | Remaining fix is plan/task-only and should go through `/plan-corrections`. |

### Latest Verdict

`changes_required` — the prior remaining blocker is fixed, but the new BUILD_PLAN status task needs one more correction so execution can produce auditable completion evidence for both the index status and the split 09c exit criteria.

---

## Recheck (2026-04-25, Pass 3)

**Review Mode:** `plan` recheck  
**Targets:**
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/implementation-plan.md`
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/task.md`

**Latest Verdict:** `changes_required`

### Recheck Commands / Evidence

All shell commands used redirect-to-file receipts under `C:\Temp\zorivest\`.

| Purpose | Evidence |
|---|---|
| Session start | `pomera_diagnose(verbose=false)` succeeded; `pomera_notes(search_term="Zorivest")` succeeded; `text-editor` reads succeeded |
| Workflow/context read | Read `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/skills/terminal-preflight/SKILL.md`, `.agent/workflows/plan-critical-review.md`, target plan, target task, and this canonical review file |
| Scope/security/deliverable sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-recheck-3.txt` |
| Targeted section read | Read `docs/build-plan/09c-pipeline-security-hardening.md:108`, `:316`, `:419`; `docs/BUILD_PLAN.md:368`; `.agent/context/meu-registry.md:306`; `task.md:37` |

### Prior Finding Recheck

| Prior # | Status | Evidence |
|---|---|---|
| 1-9 | fixed/accepted | No regression found. |
| 10. BUILD_PLAN target conflated with 09c exit criteria | mostly fixed | `task.md:42-44` now splits MEU registry, 09c exit criteria, `docs/BUILD_PLAN.md` index status, and `current-focus.md` into separate tasks. |

### Remaining Finding

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|---|---|---|---|---|
| 11 | Medium | Task 25 still has two evidence defects. First, it references `§9C.1f`, but the actual StepContext exit criteria heading is `9C.1d`. Second, its validation command `rg "\[x\]" docs/build-plan/09c-pipeline-security-hardening.md` only proves that at least one checked box exists somewhere in 09c; it does not prove the PH1/PH2/PH3 exit criteria were all updated. | `task.md:43`; `docs/build-plan/09c-pipeline-security-hardening.md:108-116`, `docs/build-plan/09c-pipeline-security-hardening.md:316-325`, `docs/build-plan/09c-pipeline-security-hardening.md:419-425` | Change `§9C.1f` to `§9C.1d`. Replace the validation with a targeted command or evidence requirement that verifies each relevant exit-criteria section, preferably by checking for no remaining unchecked boxes in those exact sections or by recording a focused diff of those sections in the handoff. | open |

### Checklist Results (Latest)

| Check | Result | Evidence |
|---|---|---|
| PR-1 Plan/task alignment | pass | Core PH1-PH3 scope remains aligned. |
| PR-2 Not-started confirmation | pass | Planned PH files/tests are absent; no correlated implementation handoff exists. |
| PR-3 Task contract completeness | mixed | Every row has required columns, but task 25 has an invalid section reference. |
| PR-4 Validation realism | mixed | Core validation commands are realistic; task 25 still does not prove the stated exit-criteria completion. |
| PR-5 Source-backed planning | pass | Security and approval decisions remain source-backed or human-approved. |
| PR-6 Handoff/corrections readiness | pass | Remaining fix is plan/task-only and should go through `/plan-corrections`. |

### Latest Verdict

`changes_required` — the previous split-target issue is corrected, but task 25 still needs a precise section reference and a validation command/evidence requirement that proves all relevant 09c exit criteria were updated.

---

## Recheck (2026-04-25, Pass 4)

**Review Mode:** `plan` recheck  
**Targets:**
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/implementation-plan.md`
- `docs/execution/plans/2026-04-25-pipeline-security-hardening/task.md`

**Latest Verdict:** `approved`

### Recheck Commands / Evidence

All shell commands used redirect-to-file receipts under `C:\Temp\zorivest\`.

| Purpose | Evidence |
|---|---|
| Session start | `pomera_diagnose(verbose=false)` succeeded; `pomera_notes(search_term="Zorivest")` succeeded; `text-editor` reads succeeded |
| Workflow/context read | Read `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/skills/terminal-preflight/SKILL.md`, `.agent/workflows/plan-critical-review.md`, target plan, target task, and this canonical review file |
| Scope/security/deliverable sweep | Receipt: `C:\Temp\zorivest\plan-critical-review-recheck-4.txt` |

### Prior Finding Recheck

| Prior # | Status | Evidence |
|---|---|---|
| 1-10 | fixed/accepted | No regression found. |
| 11. Task 25 invalid section reference and weak 09c exit validation | fixed | `task.md:43` now references `§9C.1d`, `§9C.2f`, and `§9C.4d`; the validation now checks remaining unchecked boxes in `docs/build-plan/09c-pipeline-security-hardening.md` and explicitly requires zero matches in the PH1-PH3 sections while allowing later PH4+ unchecked work. |

### Findings

No open findings in this pass.

### Checklist Results (Latest)

| Check | Result | Evidence |
|---|---|---|
| PR-1 Plan/task alignment | pass | Plan and task both cover PH1-PH3, with task rows now including the required post-execution project-state updates. |
| PR-2 Not-started confirmation | pass | Planned PH files/tests are absent; no correlated implementation handoff exists; only the plan-review handoff exists. |
| PR-3 Task contract completeness | pass | `task.md` rows include task, owner, deliverable, validation, and status. |
| PR-4 Validation realism | pass | Red/green commands, MEU gates, full checks, registry update, split 09c exit criteria, BUILD_PLAN index status, and current-focus verification are explicit. |
| PR-5 Source-backed planning | pass | SQLCipher, PH9 schema-discovery ownership, approval provenance, body cap, and fan-out rules are source-backed or human-approved. |
| PR-6 Handoff/corrections readiness | pass | Plan is ready for execution handoff; future implementation review should use `/execution-critical-review`. |

### Residual Risk

- Product tests were not run because this is an unstarted plan-review workflow.
- `docs/build-plan/09c-pipeline-security-hardening.md` still contains PH2 exit criteria that mention four PH9-owned schema-discovery tests and `GET /scheduling/db-schema`; the plan has a source-backed ownership split that leaves PH2 responsible for the `DENY_TABLES` contract and PH9 responsible for route/resource/tool filtering. Implementation handoff should restate that split when marking 09c exit criteria.

### Latest Verdict

`approved` — the execution plan and task contract are ready to proceed to implementation.
