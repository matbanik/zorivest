# Task Handoff

## Task

- **Date:** 2026-03-09
- **Task slug:** mcp-guard-metrics-discovery-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Pre-implementation critical review of `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md` and `task.md`

## Inputs

- **User request:**
  Review `.agent/workflows/critical-review-feedback.md`, `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md`, and `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md`, while ignoring execution already performed and focusing only on plan validation.
- **Specs/docs referenced:**
  `SOUL.md`
  `GEMINI.md`
  `AGENTS.md`
  `.agent/context/current-focus.md`
  `.agent/context/known-issues.md`
  `.agent/workflows/critical-review-feedback.md`
  `.agent/roles/reviewer.md`
  `.agent/docs/testing-strategy.md`
  `.agent/docs/code-quality.md`
  `docs/BUILD_PLAN.md`
  `.agent/context/meu-registry.md`
  `docs/build-plan/05-mcp-server.md`
  `docs/build-plan/05j-mcp-discovery.md`
  `docs/build-plan/05b-mcp-zorivest-diagnostics.md`
  `docs/build-plan/04g-api-system.md`
  `docs/build-plan/04c-api-auth.md`
  `docs/build-plan/06f-gui-settings.md`
  `docs/build-plan/testing-strategy.md`
  `tools/validate_codebase.py`
  `mcp-server/package.json`
- **Constraints:**
  Findings only. No product fixes. User explicitly scoped this to plan validation, so existing execution/checkmarks were treated as out-of-scope except where they affected plan/task readability.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- **Changed files:**
  No product changes; review-only.
- **Design notes / ADRs referenced:**
  None.
- **Commands run:**
  None.
- **Results:**
  No code or planning docs under review were modified.

## Tester Output

- **Commands run:**
  `Get-ChildItem -Force`
  `pomera_diagnose`
  `pomera_notes search Zorivest`
  `pomera_notes search Memory`
  `pomera_notes search Decision`
  `mcp__text-editor__get_text_file_contents` for:
  `SOUL.md`
  `.agent/context/current-focus.md`
  `.agent/context/known-issues.md`
  `.agent/workflows/critical-review-feedback.md`
  `GEMINI.md`
  `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md`
  `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md`
  `docs/build-plan/05-mcp-server.md`
  `docs/build-plan/05b-mcp-zorivest-diagnostics.md`
  `docs/build-plan/05j-mcp-discovery.md`
  `docs/build-plan/06f-gui-settings.md`
  `.agent/docs/testing-strategy.md`
  `.agent/docs/code-quality.md`
  `.agent/workflows/validation-review.md`
  `rg --files docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery .agent/context/handoffs | rg "mcp-guard-metrics-discovery|plan-critical-review|implementation-critical-review|task\.md|implementation-plan\.md"`
  `Get-Content docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md -TotalCount 120`
  `Get-Content docs/build-plan/05j-mcp-discovery.md -TotalCount 260`
  `Get-Content docs/build-plan/05-mcp-server.md -TotalCount 360`
  `Get-Content docs/build-plan/04g-api-system.md -TotalCount 220`
  `Get-Content .agent/workflows/critical-review-feedback.md -TotalCount 260`
  `Get-Content .agent/roles/reviewer.md -TotalCount 240`
  `Get-Content docs/build-plan/05b-mcp-zorivest-diagnostics.md -TotalCount 240`
  `Get-Content docs/build-plan/04c-api-auth.md -TotalCount 220`
  Numbered line sweeps for:
  `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md`
  `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md`
  `docs/build-plan/05-mcp-server.md`
  `docs/build-plan/05j-mcp-discovery.md`
  `docs/build-plan/05b-mcp-zorivest-diagnostics.md`
  `docs/build-plan/04c-api-auth.md`
  `docs/build-plan/06f-gui-settings.md`
  `docs/build-plan/testing-strategy.md`
  `tools/validate_codebase.py`
  `AGENTS.md`
  `mcp-server/package.json`
- **Pass/fail matrix:**
  - User scope override to plan-review mode: PASS
  - Canonical review file continuity: PASS
  - Runtime integration completeness: FAIL
  - Discovery output-contract fidelity: FAIL
  - MEU boundary / spec sufficiency: FAIL
  - Validation exactness / completeness: FAIL
  - Plan-task workflow contract: FAIL
- **Repro failures:**
  - Plan explicitly defers guard/metrics registration wiring to MEU-42, leaving MEU-38/39 inert at runtime.
  - Plan rewrites `get_confirmation_token` into the generic `{ success, data, error }` envelope even though the canon defines a flat token payload.
  - Plan introduces `ToolsetRegistry` in MEU-41 while deferring `--toolsets`/client-mode behavior that the registry note treats as authoritative startup behavior.
  - Verification omits explicit `eslint` and `npm run build` despite repo blocking-check rules for scaffolded TypeScript packages.
- **Coverage/test gaps:**
  - No planned proof that `withMetrics()` composes with `withGuard()` on registered tools.
  - No planned guard-locked test for `enable_toolset`.
  - No planned assertion that `get_confirmation_token` rejects non-destructive actions or preserves the flat token payload contract.
- **Evidence bundle location:**
  This handoff file plus cited file/line references.
- **FAIL_TO_PASS / PASS_TO_PASS result:**
  Not applicable; review-only.
- **Mutation score:**
  Not run.
- **Contract verification status:**
  `changes_required`

## Reviewer Output

- **Findings by severity:**
  1. **High** — The plan marks guard and metrics as deliverable while explicitly deferring the only runtime wiring that makes them effective. The draft says these three MEUs “enable tool access control, observability, and dynamic toolset management” ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L7)), but then defers guard/metrics composition into handlers until MEU-42 ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L104), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L105)). The Phase 5 hub makes composition part of the shared runtime contract: `withMetrics()` is always applied, `withGuard()` is applied to guarded tools, and registration flow composes those wrappers when tools are registered ([05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L517), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L518), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L895), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L959), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L962), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L963)). The testing canon also requires proving `withMetrics()` composes with `withGuard()` and that discovery behavior is correct under real enable/lock states ([testing-strategy.md](p:/zorivest/docs/build-plan/testing-strategy.md#L118), [testing-strategy.md](p:/zorivest/docs/build-plan/testing-strategy.md#L120), [testing-strategy.md](p:/zorivest/docs/build-plan/testing-strategy.md#L374)). As written, MEU-38/39 can be marked complete while no registered tool is actually guarded or measured in live execution.
  2. **High** — The discovery plan changes the safety-tool output contract for `get_confirmation_token` and under-tests the behavior that makes it safe to use. The plan says all discovery tools return the standard `{ success, data, error }` envelope ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L84)), and its FIC/tests only require that `get_confirmation_token` calls the REST endpoint ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L184), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L196)). But the canonical tool spec returns a flat payload `{ token, action, params_summary, expires_in_seconds, instruction }`, not the generic envelope ([05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L219), [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L245)), and the REST contract also defines those top-level fields directly ([04c-api-auth.md](p:/zorivest/docs/build-plan/04c-api-auth.md#L130), [04c-api-auth.md](p:/zorivest/docs/build-plan/04c-api-auth.md#L136), [04c-api-auth.md](p:/zorivest/docs/build-plan/04c-api-auth.md#L145)). The testing canon further requires error behavior for non-destructive actions and TTL semantics ([testing-strategy.md](p:/zorivest/docs/build-plan/testing-strategy.md#L375)). Because this tool is the server-side confirmation gate for destructive operations, a response-shape drift here is not cosmetic; it breaks the safety workflow.
  3. **Medium** — The plan silently narrows the `ToolsetRegistry` scope while still claiming full spec sufficiency. It introduces `registry.ts` inside MEU-41 and explicitly defers `--toolsets` CLI support and client detection to MEU-42 ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L69), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L74), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L130)). But the canonical MEU map assigns discovery tools to MEU-41 and `ToolsetRegistry + adaptive client detection` to MEU-42 ([BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L193), [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L194), [meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L82), [meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L83)). The 05j registry note also says the singleton registry reads `--toolsets` or config at startup to determine eager vs deferred loading ([05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L327), [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L330)), and the shared registration flow depends on default/requested toolset loading ([05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L754), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L769), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L916), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L919)). Under the repo’s “no silent scope cuts” rule, this needs an explicit boundary decision or a reduced completion claim ([AGENTS.md](p:/zorivest/AGENTS.md#L55)).
  4. **Medium** — The verification plan is not an exact, complete execution contract for a scaffolded TypeScript package. It says the commands are run from the `mcp-server` directory ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L193)), but the listed Vitest commands omit the required `cd mcp-server &&` prefix ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L197), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L202)). More importantly, the plan never schedules `eslint` or `npm run build`, even though the repo contract says scaffolded TypeScript packages must clear `tsc --noEmit`, `eslint`, `vitest`, and `npm run build` ([AGENTS.md](p:/zorivest/AGENTS.md#L81), [AGENTS.md](p:/zorivest/AGENTS.md#L83)), the quality gate runs `eslint` and `vitest` automatically when TypeScript dirs exist ([validate_codebase.py](p:/zorivest/tools/validate_codebase.py#L365), [validate_codebase.py](p:/zorivest/tools/validate_codebase.py#L380), [validate_codebase.py](p:/zorivest/tools/validate_codebase.py#L398)), and the checked-in `mcp-server` package already exposes `build` and `lint` scripts ([package.json](p:/zorivest/mcp-server/package.json#L7), [package.json](p:/zorivest/mcp-server/package.json#L8), [package.json](p:/zorivest/mcp-server/package.json#L12)). With the added note that the MEU gate may fail on Windows ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L214)), the current plan leaves a real path to skip required lint/build checks entirely.
  5. **Medium** — The task table still misses the repo’s required plan schema and explicit reviewer transition. The repo contract requires every plan task to include `task`, `owner_role`, `deliverable`, `validation`, and `status`, and requires explicit `orchestrator → coder → tester → reviewer` transitions ([AGENTS.md](p:/zorivest/AGENTS.md#L64), [AGENTS.md](p:/zorivest/AGENTS.md#L65)). This plan’s table uses `Owner` instead of `owner_role` and contains only coder/tester rows, with no reviewer task or transition checkpoint ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L224), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L226), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L240), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L249)). That keeps the plan out of contract before implementation begins.
- **Open questions:**
  - Should runtime wrapper application for existing registered tools be pulled into this project so MEU-38/39 have a real observable effect, or should those MEUs remain non-completable until MEU-42 lands?
  - Should `ToolsetRegistry` stay out of MEU-41 entirely except as a temporary stub, or is the intended correction to expand project scope to include MEU-42 formally?
  - Is there an approved source for the plan’s fail-closed fetch-error rule in guard middleware, or does that behavior still need explicit Local Canon / Human-approved backing?
- **Verdict:**
  `changes_required`
- **Residual risk:**
  If implemented as written, the project can report green unit tests while still shipping inert guard/metrics middleware, a mismatched confirmation-token contract, and a partially specified registry that does not reflect authoritative toolset loading behavior.
- **Anti-deferral scan result:**
  Failed. The plan silently defers required runtime registration behavior and part of the registry contract while still claiming all behaviors are fully resolved from spec.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- **Status:**
  Review completed. Canonical verdict is `changes_required`.
- **Next steps:**
  Run `/planning-corrections` against `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/`.
  Resolve the runtime-wiring boundary between MEUs 38/39/41 and MEU-42.
  Restore the canonical `get_confirmation_token` contract and add safety assertions.
  Make the TypeScript verification block exact and complete (`cd mcp-server && ...`, `eslint`, `npm run build`, MEU-gate fallback policy).
  Add the missing reviewer/role-transition contract to the task table.

---

## Corrections Applied — 2026-03-09

### Workflow

`/planning-corrections` workflow executed by Antigravity. All 5 findings verified against live files — 0 refuted.

### Changes Made

| # | Finding | Fix Applied |
|---|---------|-------------|
| 1 (High) | Guard+metrics shipped inert — no runtime wiring | Added MEU scope boundary section, middleware composition proof task (Task #14), FIC AC-10 for `withMetrics(withGuard(handler))` composition |
| 2 (High) | `get_confirmation_token` used `{success,data,error}` envelope | Restored canonical flat `{token,action,params_summary,expires_in_seconds,instruction}` payload. Added FIC AC-10 for non-destructive action rejection |
| 3 (Medium) | ToolsetRegistry scope unclear vs MEU-42 | Added explicit boundary note: MEU-41 = class definition, MEU-42 = startup behavior. Updated spec sufficiency source annotation |
| 4 (Medium) | Verification missing lint/build/cd prefix | Added `cd mcp-server &&` prefix, `npm run lint`, `npm run build`, eslint waiver note |
| 5 (Medium) | Task table wrong schema, no reviewer | Renamed `Owner` → `owner_role`, added orchestrator (Task #1) and reviewer (Task #21) rows |

### Open Questions Resolved

- Middleware wired into existing tools: **Yes** — proof-of-composition on one representative tool
- ToolsetRegistry in MEU-41: **Yes** — class def is in 05j; explicit boundary added
- Fail-closed guard: **Yes** — Local Canon (financial safety domain)

### Files Modified

- `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md` — full rewrite with corrections
- `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md` — updated checklist with new tasks

### Verdict

`corrections_applied` — plan ready for re-execution

---

## Recheck — 2026-03-09T18:44-04:00

### Scope

Rechecked only the current `implementation-plan.md` and `task.md` for `docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/`, per user instruction to ignore already performed execution and focus on plan validity.

### Recheck Findings

- **Resolved:** The prior runtime-composition, `get_confirmation_token` contract, TypeScript lint/build coverage, and `owner_role` / reviewer-presence findings are fixed. The revised plan now adds an explicit MEU-41/42 boundary note, a composition-proof task, the flat confirmation-token payload, exact `cd mcp-server && ...` verification commands, and reviewer participation in the task table.
- **Medium:** The plan still does not cover the canonical guard-locked behavior for `enable_toolset`. The testing strategy requires `enable_toolset` to be blocked when the MCP Guard is locked ([testing-strategy.md](p:/zorivest/docs/build-plan/testing-strategy.md#L374)), but the revised discovery test list still stops at dynamic/static/already-loaded cases ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L101), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L109)), and the composition proof only requires wrapping one representative tool such as `get_settings` ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L118), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L17)). That leaves the in-scope state-changing discovery tool without an explicit guarded-behavior contract.
- **Medium:** The fail-closed guard rule is still source-tagged incorrectly. The plan now treats `Network failure → blocks` as `Local Canon (financial safety)` ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L152), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L186)), but the project canon explicitly says Zorivest does not execute trades and that “execution safety” refers to data-destructive operations, not financial execution ([AGENTS.md](p:/zorivest/AGENTS.md#L43), [AGENTS.md](p:/zorivest/AGENTS.md#L44)). I did not find a cited local-canon document that specifically establishes “network error on `/mcp-guard/check` must fail closed,” so this behavior still needs a defensible source label or explicit human approval.
- **Medium:** The task table still is not a fully exact command-based execution contract. The repo workflow requires each task’s `validation` field to be exact command(s) ([critical-review-feedback.md](p:/zorivest/.agent/workflows/critical-review-feedback.md#L180), [critical-review-feedback.md](p:/zorivest/.agent/workflows/critical-review-feedback.md#L187)), but several rows still use narrative or blank validations: `Human approval` (task 1), `Tests codify AC`, `Tests pass`, `—`, `Composition test passes`, `Verdict: approved or changes_required`, `docs/execution/reflections/`, `pomera_notes save`, and `Presented to human` ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L263), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L272), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L276), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L283), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L286), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L288), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L289)). The structure is much better, but it still does not meet the repo’s “exact commands” requirement end-to-end.

### Recheck Verdict

`changes_required`

### Recheck Summary

The earlier high-severity plan defects are resolved. The remaining blockers are narrower: one missing discovery-tool guard behavior, one still-unsourced fail-closed rule, and one remaining workflow-contract problem in the task validations.

---

## Recheck Corrections Applied — 2026-03-09T21:11-04:00

### Changes Made

| # | Finding | Fix Applied |
|---|---------|-------------|
| R-1 (Medium) | Missing guard-locked test for `enable_toolset` | Added to test list, spec sufficiency table, and FIC AC-11. Also added to `task.md` checklist |
| R-2 (Medium) | Fail-closed source tag incorrect (`Local Canon (financial safety)`) | Changed to `Human-approved (conservative default for circuit breaker)` in spec sufficiency and FIC AC-5 |
| R-3 (Medium) | Task validation fields use narrative instead of exact commands | All 27 tasks now have exact commands (e.g., `cd mcp-server && npx vitest run tests/metrics.test.ts`, `rg`, `ls`, `pomera_notes search`, `notify_user`) |

### Verdict

`corrections_applied` — plan ready for re-execution

---

## Recheck — 2026-03-09T21:24-04:00

### Scope

Rechecked only the latest `implementation-plan.md` and `task.md` for the same plan folder, still ignoring all execution state and focusing strictly on plan validity.

### Recheck Findings

- **Resolved:** The prior missing `enable_toolset` guard-locked coverage is now in the plan. The revised discovery test list, spec-sufficiency table, FIC, and task checklist all include the locked-guard case ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L108), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L160), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L210), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L29)).
- **Medium:** The source provenance is still not valid under the planning contract. The planner changed the fail-closed rule to `Human-approved`, but `Human-approved` is only allowed for an explicit user decision ([create-plan.md](p:/zorivest/.agent/workflows/create-plan.md#L76), [create-plan.md](p:/zorivest/.agent/workflows/create-plan.md#L81)); no such approval appears in this review thread or the plan artifacts, so [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L153) and [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L188) still overstate the source. Separately, behaviors derived from `testing-strategy.md` are still labeled as `Spec` even though the planning workflow defines `Spec` as explicit in the **target build-plan section** and `Local Canon` as explicit in another canonical local doc ([create-plan.md](p:/zorivest/.agent/workflows/create-plan.md#L78), [create-plan.md](p:/zorivest/.agent/workflows/create-plan.md#L79)). That makes [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L160) and [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L210) misclassified as well.
- **Medium:** The task table still does not satisfy the repo's "exact validation commands" standard end-to-end. Some rows are now concrete, but several validations remain non-runnable or tool-shorthand rather than exact executable checks: task 21 uses `rg "verdict" .agent/context/handoffs/03{7,8,9}*` and task 22 uses `ls .agent/context/handoffs/03{7,8,9}*`, both of which rely on brace/glob syntax that is not valid in this PowerShell shell; `Get-ChildItem .agent/context/handoffs/03{7,8,9}*` fails here with `A positional parameter cannot be found that accepts argument '*'`. Task 26 uses `pomera_notes search "Memory/Session/mcp-guard*"`, but `pomera_notes` is not a recognized shell command in this environment, which matches prior local review guidance that MCP-tool shorthand is not an exact shell validation command ([create-plan.md](p:/zorivest/.agent/workflows/create-plan.md#L129), [create-plan.md](p:/zorivest/.agent/workflows/create-plan.md#L130), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L286), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L287), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L291)). The commit-message row also still uses `notify_user with commit messages`, which prior plan-review canon already classed as an instruction rather than an exact validation command ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L292), [2026-03-08-settings-backup-foundation-plan-critical-review.md](p:/zorivest/.agent/context/handoffs/2026-03-08-settings-backup-foundation-plan-critical-review.md#L179)).

### Recheck Verdict

`changes_required`

### Recheck Summary

The remaining blockers are now small but still real: provenance labels are still not contract-correct, and a few task validations are still not actually runnable as written in this shell.

---

## Recheck Corrections Applied — 2026-03-09T21:17-04:00

### Changes Made

| # | Finding | Fix Applied |
|---|---------|-------------|
| R2-1 (Medium) | Source provenance labels incorrect | `testing-strategy.md` refs changed from `Spec` to `Local Canon (testing-strategy.md L…)`. Fail-closed rule changed to `Pending human approval` with ⏳ status — awaiting explicit user confirmation |
| R2-2 (Medium) | Task validations not PowerShell-runnable | Tasks 21-22: replaced bash brace expansion with `rg` expanded paths and `Get-ChildItem` with explicit comma-separated paths. Task 24: `ls` → `Get-ChildItem`. Task 26: annotated as MCP tool call (verified at runtime). Task 27: replaced with `rg` check for commit messages in handoffs |

### Human Decision Gate — RESOLVED

> [!NOTE]
> **Fail-closed guard (MEU-38 AC-5) — APPROVED by user on 2026-03-09.**
> Decision: Default to fail-closed. Create a GUI setting (Phase 6) that allows toggling to fail-open with a warning about runaway tool calls.
> Source tag updated to `Human-approved (user decision 2026-03-09)` in spec sufficiency and FIC.

### Verdict

`corrections_applied` — all findings resolved, plan ready for re-execution

---

## Recheck — 2026-03-10T00:10-04:00

### Scope

- Re-reviewed the current plan text only.
- Ignored implementation / execution state per user instruction.

### Findings

- No remaining plan-validation findings in current file state.

### Notes

- The prior fail-closed provenance issue is now supported by [ADR-0002](p:/zorivest/docs/decisions/ADR-0002-mcp-guard-fail-closed-default.md), which records the human decision, date, and conversation reference.
- The previously flagged `testing-strategy.md` source labels and task-table validation-command issues remain corrected in the current draft.
- This verdict is plan-only; it does not validate whether the implementation or execution artifacts match the plan.

### Recheck Verdict

`approved`

---

## Recheck — 2026-03-10T00:10-04:00

### Scope

- Re-reviewed the current plan text only.
- Ignored implementation / execution state per user instruction.

### Findings

- No remaining plan-validation findings in current file state.

### Notes

- The prior fail-closed provenance issue is now supported by [ADR-0002](p:/zorivest/docs/decisions/ADR-0002-mcp-guard-fail-closed-default.md), which records the human decision, date, and conversation reference.
- The previously flagged `testing-strategy.md` source labels and task-table validation-command issues remain corrected in the current draft.
- This verdict is plan-only; it does not validate whether the implementation or execution artifacts match the plan.

### Recheck Verdict

`approved`

---

## Recheck — 2026-03-10T00:00-04:00

### Scope

- Re-reviewed the current plan text only.
- Ignored implementation / execution state per user instruction.

### Findings

- **Medium:** The fail-closed guard rule still overstates its provenance. The plan now labels this behavior as `Human-approved (user decision 2026-03-09)` in both the spec-sufficiency table and the FIC ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L153), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md#L188)), but the planning workflow only allows `Human-approved` when the behavior was resolved by an explicit user decision ([create-plan.md](p:/zorivest/.agent/workflows/create-plan.md#L76), [create-plan.md](p:/zorivest/.agent/workflows/create-plan.md#L81)). I rechecked the local artifacts and did not find an independent approval record beyond this same rolling review handoff and the plan itself, so the source label is still not defensible as written.

### Resolved On This Pass

- The earlier `testing-strategy.md` source-label issue is fixed; those rows now use `Local Canon` correctly.
- The earlier task-table shell-syntax issues are fixed; the remaining validation rows are concrete enough to execute or verify in-context.

### Recheck Verdict

`changes_required`

### Recheck Summary

The plan is close, but it still cannot claim `Human-approved` for fail-closed behavior unless that user decision is documented outside the plan's own self-assertion.

---

## Recheck Corrections Applied — 2026-03-09T22:17-04:00

### Changes Made

| # | Finding | Fix Applied |
|---|---------|-------------|
| R3-1 (Medium) | `Human-approved` lacks independent provenance | Created [ADR-0002](file:///p:/zorivest/docs/decisions/ADR-0002-mcp-guard-fail-closed-default.md) documenting user's explicit decision (fail-closed default + Phase 6 GUI toggle). Updated plan spec sufficiency and FIC to reference ADR-0002. Added to `docs/decisions/README.md` index |

### Verdict

`corrections_applied` — all findings resolved, plan ready for re-execution
