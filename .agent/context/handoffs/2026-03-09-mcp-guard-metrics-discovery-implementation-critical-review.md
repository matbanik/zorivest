# Task Handoff

## Task

- **Date:** 2026-03-10
- **Task slug:** mcp-guard-metrics-discovery-implementation-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of the correlated MEU-39 / MEU-38 / MEU-41 implementation handoff set against actual repo state

## Inputs

- User request:
  Critically review [critical-review-feedback.md](p:/zorivest/.agent/workflows/critical-review-feedback.md), [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md), [038-2026-03-09-mcp-guard-bp05s5.6.md](p:/zorivest/.agent/context/handoffs/038-2026-03-09-mcp-guard-bp05s5.6.md), and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md).
- Specs/docs referenced:
  [critical-review-feedback.md](p:/zorivest/.agent/workflows/critical-review-feedback.md), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/implementation-plan.md), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md), [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md), [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md), [testing-strategy.md](p:/zorivest/docs/build-plan/testing-strategy.md), [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md), [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md)
- Constraints:
  Findings only. No product fixes during this workflow. Expand from the provided seed handoffs to the full correlated project scope.

## Role Plan

1. orchestrator — correlate the three handoffs to the shared execution plan folder and shared deliverables
2. tester — read actual code/docs, run verification commands, compare claims to repo state
3. reviewer — produce findings-first verdict and write canonical implementation review handoff
- Optional roles: none

## Coder Output

- Changed files:
  No product changes; review-only.
- Design notes / ADRs referenced:
  [ADR-0002-mcp-guard-fail-closed-default.md](p:/zorivest/docs/decisions/ADR-0002-mcp-guard-fail-closed-default.md) reviewed as part of claimed MEU-38 scope.
- Commands run:
  None in coder role.
- Results:
  Review-only pass; no code edits applied.

## Tester Output

- Correlation rationale:
  The user explicitly provided the three sibling work handoffs. They correlate to the shared project folder [2026-03-09-mcp-guard-metrics-discovery](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/) via the task checklist entries at [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L44), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L45), and [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L46).
- Commands run:
  - `git status --short`
  - `git status --short -- docs/build-plan docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md docs/execution/reflections mcp-server`
  - `git diff -- docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md mcp-server/src/index.ts mcp-server/src/tools/diagnostics-tools.ts`
  - `rg --files mcp-server docs .agent/context | rg "(metrics|guard|discovery|registry|diagnostics-tools|index|meu-registry|reflection|BUILD_PLAN|execution/metrics|039-|038-|037-)"`
  - `rg -n "withMetrics|withGuard|registerToolsForClient|guardedTools|Tool call|always applied|apply withGuard" docs/build-plan/05-mcp-server.md`
  - `rg -n "enable_toolset|static client|listChanged|tools/list_changed|ToolsetRegistry|get_confirmation_token|confirmation-tokens|adaptive|dynamic client" docs/build-plan/05j-mcp-discovery.md docs/build-plan/testing-strategy.md`
  - `rg -n "toolsetRegistry\.register\(" mcp-server/src mcp-server/tests`
  - `rg -n "withMetrics\(|withGuard\(" mcp-server/src`
  - `npx vitest run tests/metrics.test.ts`
  - `npx vitest run tests/guard.test.ts`
  - `npx vitest run tests/discovery-tools.test.ts`
  - `npx vitest run`
  - `npx tsc --noEmit`
  - `npm run lint`
  - `npm run build`
  - `uv run pytest tests/ -v`
  - `rg -n "mcp-guard-metrics-discovery|mcp-guard|mcp-perf-metrics|mcp-discovery" docs/execution/metrics.md docs/execution/reflections`
- Pass/fail matrix:
  | Check | Result |
  |------|--------|
  | `tests/metrics.test.ts` | 16 passed |
  | `tests/guard.test.ts` | 7 passed |
  | `tests/discovery-tools.test.ts` | 10 passed |
  | Full Vitest | 72 passed |
  | `tsc --noEmit` | clean |
  | `npm run lint` | clean |
  | `npm run build` | clean |
  | `pytest tests/ -v` | 648 passed, 1 skipped |
  | Reflection/metrics grep | no matches |
- Repro failures:
  None in command execution. The review findings are contract/state mismatches, not current test/build failures.
- Coverage/test gaps:
  `enable_toolset` static-client behavior remains unverified in the automated tests, and the runtime registry path is not exercised because tests seed the singleton registry manually at [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L24) and [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L73).
- Evidence bundle location:
  This review handoff plus the correlated handoffs [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md), [038-2026-03-09-mcp-guard-bp05s5.6.md](p:/zorivest/.agent/context/handoffs/038-2026-03-09-mcp-guard-bp05s5.6.md), and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md).
- FAIL_TO_PASS / PASS_TO_PASS result:
  Claimed validations pass in the current repo state, but several handoff claims overstate runtime completeness.
- Mutation score:
  Not run.
- Contract verification status:
  Partial. Unit/build validation passes, but the correlated project still misses required runtime behavior and required shared-project deliverables.

## Reviewer Output

- Findings by severity:
  1. **High:** The discovery tools are wired to a registry that is only populated in tests, so the runtime implementation cannot actually discover or enable real toolsets. The production code reads from `toolsetRegistry.getAll()` and `toolsetRegistry.get()` in [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L48), [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L100), and [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L184), but the singleton registry only exposes storage methods in [registry.ts](p:/zorivest/mcp-server/src/toolsets/registry.ts#L35) through [registry.ts](p:/zorivest/mcp-server/src/toolsets/registry.ts#L80) and there is no production registration step in [index.ts](p:/zorivest/mcp-server/src/index.ts#L27). In contrast, the tests manually seed the singleton at [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L24) and [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L73). That violates the canonical startup contract that the `ToolsetRegistry` is initialized at server startup in [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L330) and makes [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L106) materially overstate completion.
  2. **High:** The project marked live middleware composition complete, but no registered production tool is actually wrapped with `withMetrics(withGuard(...))`. The correlated task explicitly marks this done at [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L19), and the hub spec requires guarded tools to be registered through the wrapper chain in [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L518) and [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L959). In the actual runtime code, [index.ts](p:/zorivest/mcp-server/src/index.ts#L27) through [index.ts](p:/zorivest/mcp-server/src/index.ts#L33) still register tool groups directly, `rg -n "withMetrics\\(|withGuard\\(" mcp-server/src` finds no wrapper call sites outside the middleware definitions, and [diagnostics-tools.ts](p:/zorivest/mcp-server/src/tools/diagnostics-tools.ts#L126) only reads from `metricsCollector` without any tool ever recording into it. The handoffs treat composition as complete, but the runtime still does not measure or guard any registered tool.
  3. **High:** `enable_toolset` does not implement the static-client rejection and explicit tool-list notification required by the discovery spec, yet the discovery handoff still reports AC-1 through AC-11 as verified. The canonical behavior in [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L121) through [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L167) requires rejecting static clients via `clientSupportsNotification('notifications/tools/list_changed')` and then sending `notifications/tools/list_changed`. The current implementation at [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L145) through [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L223) does neither; it only calls `ts.register(server)` and leaves a comment assuming the server will auto-send notifications. The handoff explicitly admits AC-6 was not tested and substitutes a design assertion at [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L69) and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L75), which is not equivalent to implementing the specified branch.
  4. **Medium:** The handoff set overstates project readiness by treating review as the last step before commit while required shared-project deliverables remain undone and the status docs are still stale. All three handoffs end with “Implementation complete … Awaiting Codex reviewer validation” and “Next steps: Codex validation pass, then git commit” at [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L96), [038-2026-03-09-mcp-guard-bp05s5.6.md](p:/zorivest/.agent/context/handoffs/038-2026-03-09-mcp-guard-bp05s5.6.md#L94), and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L106). But the correlated task still leaves [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L47) through [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L51) unchecked, [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L190), [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L191), and [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L193) still show MEU-38/39/41 as pending, [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L79), [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L80), and [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L82) still show pending, and the reflection/metrics grep returned no matches. The project is not ready for commit even if the code were otherwise accepted.
  5. **Medium:** Parts of the handoff evidence are no longer auditable against current repo state. [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L33) says `metrics.test.ts` contains 14 tests, but `npx vitest run tests/metrics.test.ts` currently executes 16. [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L34) says `discovery-tools.test.ts` contains 12 tests, but the file currently runs 10. [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L51) also reports `648 passed` for pytest without noting the current skipped test (`648 passed, 1 skipped`). These are auditability issues rather than broken behavior, but they reduce trust in the evidence bundle.
- Open questions:
  None. The blocking issues are visible in current file state.
- Verdict:
  `changes_required`
- Residual risk:
  Even after the shared-doc status updates are completed, the runtime discovery/guard/metrics behavior still needs correction. Right now the tests mostly prove isolated helpers and a synthetic registry setup, not the actual production registration path.
- Anti-deferral scan result:
  No placeholder `TODO`/`FIXME` markers were needed to identify the blockers. The main problem is missing runtime wiring and missing shared-project completion work, not explicit deferral markers.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  Review completed for the full correlated MEU-39 / 38 / 41 project set. Build and test commands pass, but the implementation still fails critical runtime and project-completeness checks.
- Next steps:
  Route the fixes through `/planning-corrections`, then re-run this implementation review against the corrected runtime wiring and shared project artifacts.

---

## Recheck — 2026-03-10T23:00-04:00

### Scope

- Re-reviewed the same correlated MEU-39 / MEU-38 / MEU-41 implementation set.
- Checked whether the prior findings were corrected in current repo state.

### Commands Re-run

- `rg -n "withMetrics|withGuard|toolsetRegistry\.register|clientSupportsNotification|notification\(|tools/list_changed|registerTradeTools|registerDiscoveryTools" mcp-server/src mcp-server/tests docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md`
- `npx vitest run tests/trade-tools.test.ts tests/discovery-tools.test.ts`
- `npx vitest run`
- `uv run pytest tests/ -q`

### Resolved On This Pass

- The previous live-composition gap is resolved. `create_trade` is now wrapped with `withMetrics(withGuard(...))` in [trade-tools.ts](p:/zorivest/mcp-server/src/tools/trade-tools.ts#L73), which satisfies the project’s “one registered tool” proof requirement.
- Shared status docs were partially advanced from pending to in-review at [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L190), [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L191), [BUILD_PLAN.md](p:/zorivest/docs/BUILD_PLAN.md#L193), [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L79), [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L80), and [.agent/context/meu-registry.md](p:/zorivest/.agent/context/meu-registry.md#L82).

### Remaining Findings

- **High:** The discovery runtime still depends on a registry that is only seeded in tests. I rechecked production code and `rg -n "toolsetRegistry\.register\(" mcp-server/src mcp-server/tests` still returns `NO_MATCHES` for `mcp-server/src`, while the tests still seed the singleton manually at [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L24) and [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L73). The production discovery handlers still read from the singleton at [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L48), [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L100), and [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L184), so runtime discovery remains effectively uninitialized.
- **High:** `enable_toolset` still does not implement the spec-required static-client rejection or explicit `notifications/tools/list_changed` behavior. The spec branch remains required at [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L121), but the implementation still stops at `ts.register(server)` plus a comment in [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L218). The discovery handoff still treats AC-6 as “covered by design” instead of implemented at [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L69) and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L75).
- **Medium:** The project-level completion artifacts are still inconsistent. The task checklist still leaves [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L47) through [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L51) unchecked, there is still no matching reflection or metrics row, and the handoffs still say the next step after review is `git commit` at [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L98), [038-2026-03-09-mcp-guard-bp05s5.6.md](p:/zorivest/.agent/context/handoffs/038-2026-03-09-mcp-guard-bp05s5.6.md#L94), and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L106). The readiness claim is still ahead of the project state.
- **Medium:** Evidence drift remains in the handoffs. [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L33) now says `metrics.test.ts` has 16 tests, but its final summary still says `14/14` at [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L98). [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L34) now says `10 unit tests`, but its final summary still says `12/12` at [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L106).

### Recheck Verdict

`changes_required`

### Recheck Summary

The live wrapper proof is now in place, so the review is no longer blocked on middleware composition. The remaining blockers are the same discovery-runtime contract gap, the still-unimplemented static-client branch, and incomplete project-closeout artifacts.

---

## Recheck — 2026-03-10T23:10-04:00

### Scope

- Re-reviewed the same correlated implementation set after the latest handoff/task/status updates.
- Focused on the previously open discovery-runtime, static-client, and closeout findings.

### Commands Re-run

- `rg -n "toolsetRegistry\.register\(|clientSupportsNotification|notification\(|tools/list_changed|withMetrics\(|withGuard\(|mcp-guard-metrics-discovery|MEU-38|MEU-39|MEU-41" mcp-server/src mcp-server/tests docs/BUILD_PLAN.md .agent/context/meu-registry.md docs/execution/metrics.md docs/execution/reflections docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md .agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md .agent/context/handoffs/038-2026-03-09-mcp-guard-bp05s5.6.md .agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md`
- `npx vitest run tests/discovery-tools.test.ts tests/trade-tools.test.ts`
- `npx tsc --noEmit`
- `npm run lint`
- `npm run build`
- `uv run pytest tests/ -q`

### Resolved On This Pass

- The runtime registry is no longer empty. [index.ts](p:/zorivest/mcp-server/src/index.ts#L20) now seeds the singleton at startup via [seed.ts](p:/zorivest/mcp-server/src/toolsets/seed.ts#L133), so the previous “tests-only registry” finding is resolved.
- The prior handoff test-count drift is resolved. [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L98) now reports `16/16`, and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L106) now reports `10/10` plus `648 Python tests pass, 1 skipped`.

### Remaining Findings

- **High:** The production registry seed is still incomplete relative to the canonical toolset inventory. The seed bridge only registers `core`, `trade-analytics`, `tax`, and `behavioral` in [seed.ts](p:/zorivest/mcp-server/src/toolsets/seed.ts#L24), [seed.ts](p:/zorivest/mcp-server/src/toolsets/seed.ts#L55), [seed.ts](p:/zorivest/mcp-server/src/toolsets/seed.ts#L89), and [seed.ts](p:/zorivest/mcp-server/src/toolsets/seed.ts#L108). The hub spec defines eight toolsets plus discovery in [05-mcp-server.md](p:/zorivest/docs/build-plan/05-mcp-server.md#L735), and the testing canon still says `list_available_toolsets` returns all 8 toolsets in [testing-strategy.md](p:/zorivest/docs/build-plan/testing-strategy.md#L372). The current discovery tests still only seed a reduced set and assert `total_tools === 6` at [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L24), [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L73), and [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L117), so they do not protect the canonical inventory contract.
- **High:** AC-6 is still not implemented as specified. The spec requires rejecting static clients via `clientSupportsNotification('notifications/tools/list_changed')` before enabling a toolset in [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L152). The current code only registers the tools and calls `server.sendToolListChanged()` in [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L218), with no static-client branch. The test file still has no static-client or notification assertion at all (`rg -n "static client|clientSupportsNotification|sendToolListChanged|tools/list_changed" mcp-server/tests/discovery-tools.test.ts` returned `NO_MATCHES`), while the handoff now incorrectly treats SDK auto-notification as satisfying AC-6 at [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L69) and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L75).
- **Medium:** The verification record still overstates lint cleanliness. `npm run lint` now emits two warnings in [trade-tools.ts](p:/zorivest/mcp-server/src/tools/trade-tools.ts#L75) and [trade-tools.ts](p:/zorivest/mcp-server/src/tools/trade-tools.ts#L115), so the task’s `clean eslint` checkbox at [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L35) and the handoff claims at [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L48) and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L49) are no longer accurate.
- **Medium:** The project-closeout mismatch remains. The task now explicitly defers reflection, metrics, pomera session state, and commit-message work to closeout at [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L49), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L50), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L51), and [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L52), and there are still no matching reflection or execution-metrics entries. But the handoffs still say the next step after validation is `git commit` at [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L100), [038-2026-03-09-mcp-guard-bp05s5.6.md](p:/zorivest/.agent/context/handoffs/038-2026-03-09-mcp-guard-bp05s5.6.md#L96), and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L108). That is still premature.

### Recheck Verdict

`changes_required`

### Recheck Summary

The implementation is closer: live middleware composition is present, the runtime registry now exists, and the handoff count drift is fixed. The remaining blockers are now narrower and mostly centered on discovery-spec completeness plus inaccurate closeout/verification claims.

---

## Recheck — 2026-03-10T23:24-04:00

### Scope

- Re-reviewed the same correlated implementation set after the latest discovery, task, and handoff updates.
- Focused on whether the prior runtime-inventory, evidence-drift, lint, and closeout findings still hold.

### Commands Re-run

- `npx vitest run tests/discovery-tools.test.ts`
- `npx vitest run`
- `npm run lint`
- `uv run pytest tests/ -q`
- `rg -n "clientSupportsNotification|sendToolListChanged|static client|tools/list_changed|clean eslint|72/72|73/73|648/648|648 Python tests pass|reflection|metrics" mcp-server/src/tools/discovery-tools.ts mcp-server/tests/discovery-tools.test.ts docs/build-plan/05j-mcp-discovery.md docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md .agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md .agent/context/handoffs/038-2026-03-09-mcp-guard-bp05s5.6.md .agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md docs/execution/metrics.md docs/execution/reflections`

### Resolved On This Pass

- The seeded inventory gap is resolved. [seed.ts](p:/zorivest/mcp-server/src/toolsets/seed.ts#L9) now documents the canonical “8 toolsets + discovery” split, and the seed bridge registers all eight non-discovery toolsets before startup use.
- The discovery test-count drift is resolved. `npx vitest run tests/discovery-tools.test.ts` now reports 11 tests, and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L106) now matches `11/11 tests green`.
- The handoff verification rows were corrected to reflect current lint reality. [037-2026-03-09-mcp-perf-metrics-bp05s5.9.md](p:/zorivest/.agent/context/handoffs/037-2026-03-09-mcp-perf-metrics-bp05s5.9.md#L48) and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L49) now record `2 warnings` instead of claiming clean lint.
- The handoff closeout wording is no longer premature. The correlated handoffs now point to project closeout after review rather than directly to `git commit`.

### Remaining Findings

- **High:** AC-6 is still not implemented as specified. The spec requires rejecting static clients before dynamic tool loading via `clientSupportsNotification('notifications/tools/list_changed')` in [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L152). The current implementation in [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L218) still only registers the toolset and performs a best-effort `server.sendToolListChanged()` call, with no static-client rejection branch. The test file adds a `sendToolListChanged` spy at [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L267) but still has no static-client rejection case, and the discovery handoff still treats AC-6 as a “spec gap” rather than an implementation miss at [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L69) and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L75).
- **Medium:** The task verification block is now stale. [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L35) still says `npm run lint` is “clean eslint,” but the current command emits two warnings in [trade-tools.ts](p:/zorivest/mcp-server/src/tools/trade-tools.ts#L75) and [trade-tools.ts](p:/zorivest/mcp-server/src/tools/trade-tools.ts#L115). The same task block also still records `72/72` MCP tests and `648/648` Python tests at [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L37) and [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L38), while the current reruns are `73/73` and `648 passed, 1 skipped`.
- **Medium:** Project closeout remains incomplete. The task explicitly still defers the reflection, metrics row, pomera session save, and commit-message proposal at [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L49), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L50), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L51), and [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L52). I also still found no matching project entry in `docs/execution/metrics.md` and no matching reflection under `docs/execution/reflections/`.

### Recheck Verdict

`changes_required`

### Recheck Summary

The runtime seeding and evidence-alignment work is materially improved, and the remaining issues are now narrow. The review is still blocked by the missing AC-6 static-client branch, plus stale task verification text and unfinished project-closeout artifacts.

---

## Recheck — 2026-03-10T23:34-04:00

### Scope

- Re-reviewed the same correlated implementation set after the latest discovery, task, metrics, and reflection updates.
- Focused on whether AC-6 is now satisfied in production, not just in tests or docs.

### Commands Re-run

- `npx vitest run tests/discovery-tools.test.ts`
- `npx vitest run`
- `npm run lint`
- `uv run pytest tests/ -q`
- `rg -n "dynamicLoadingEnabled\\s*=|dynamicLoadingEnabled\\b" mcp-server/src mcp-server/tests`
- `rg -n "clientSupportsNotification|sendToolListChanged|static client|tools/list_changed|648 passed, 1 skipped|74/74|2 warnings" mcp-server/src mcp-server/tests docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md .agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md docs/execution/metrics.md docs/execution/reflections/2026-03-09-mcp-guard-metrics-discovery-reflection.md`

### Resolved On This Pass

- The task verification block is now current. [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L35) now records `2 warnings`, [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L37) records `74/74`, and [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L38) records `648 passed, 1 skipped`.
- Project closeout artifacts now exist. [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L49), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L50), [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L51), and [task.md](p:/zorivest/docs/execution/plans/2026-03-09-mcp-guard-metrics-discovery/task.md#L52) are now complete, with matching entries in [metrics.md](p:/zorivest/docs/execution/metrics.md#L18) and [2026-03-09-mcp-guard-metrics-discovery-reflection.md](p:/zorivest/docs/execution/reflections/2026-03-09-mcp-guard-metrics-discovery-reflection.md#L1).
- Discovery verification counts are updated. `npx vitest run tests/discovery-tools.test.ts` now reports `12/12`, and the discovery handoff reflects that at [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L106).

### Remaining Findings

- **High:** AC-6 is still only simulated, not wired in live runtime behavior. The implementation now checks [registry.ts](p:/zorivest/mcp-server/src/toolsets/registry.ts#L47) via [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L223), and the test toggles that flag at [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L314). But `rg -n "dynamicLoadingEnabled\\s*=|dynamicLoadingEnabled\\b" mcp-server/src mcp-server/tests` shows no production setter beyond the default `true` declaration and the read in `enable_toolset`; the only mutation is in the test. That means static-client rejection still depends on future MEU-42 wiring, not current runtime state, which falls short of the spec’s live client-capability gate in [05j-mcp-discovery.md](p:/zorivest/docs/build-plan/05j-mcp-discovery.md#L152).
- **Medium:** The discovery handoff still contains contradictory evidence about AC-6. It says AC-6 is implemented and functionally verified at [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L69) and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L75), but the same handoff still says `AC-6 (static client) not testable` at [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L92). The evidence bundle is still internally inconsistent.

### Recheck Verdict

`changes_required`

### Recheck Summary

Most of the earlier process and evidence issues are now corrected. The remaining blocker is narrower: discovery now has a testable AC-6 flag, but it is not yet connected to any production path that can classify a client as static, so the current server still assumes dynamic loading by default.

---

## Recheck — 2026-03-10T23:39-04:00

### Scope

- Re-reviewed the same correlated implementation set after the latest AC-6 runtime-wiring update.
- Focused on whether the prior production-setter gap and handoff inconsistency are now resolved.

### Commands Re-run

- `npx vitest run tests/discovery-tools.test.ts`
- `npx vitest run`
- `npm run lint`
- `uv run pytest tests/ -q`
- `rg -n "dynamicLoadingEnabled\\s*=|dynamicLoadingEnabled\\b|clientSupportsNotification|static client|sendToolListChanged|tools/list_changed|AC-6|not testable" mcp-server/src mcp-server/tests .agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md docs/build-plan/05j-mcp-discovery.md`

### Resolved On This Pass

- The prior production-wiring gap is resolved. [index.ts](p:/zorivest/mcp-server/src/index.ts#L33) now sets [registry.ts](p:/zorivest/mcp-server/src/toolsets/registry.ts#L47) to static-client mode when `ZORIVEST_STATIC_CLIENT` is present, and [discovery-tools.ts](p:/zorivest/mcp-server/src/tools/discovery-tools.ts#L223) rejects `enable_toolset` accordingly.
- The discovery handoff is now internally consistent on AC-6. [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L69), [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L75), and [039-2026-03-09-mcp-discovery-bp05js5j.md](p:/zorivest/.agent/context/handoffs/039-2026-03-09-mcp-discovery-bp05js5j.md#L92) now all describe the same implementation model.

### Remaining Findings

- No remaining implementation-critical findings in the current draft.

### Residual Risk

- The startup env-var path in [index.ts](p:/zorivest/mcp-server/src/index.ts#L33) is not directly exercised by automated tests; the discovery test still toggles the registry flag directly at [discovery-tools.test.ts](p:/zorivest/mcp-server/tests/discovery-tools.test.ts#L314).
- `npm run lint` still reports the two known composition-boundary warnings in [trade-tools.ts](p:/zorivest/mcp-server/src/tools/trade-tools.ts#L75) and [trade-tools.ts](p:/zorivest/mcp-server/src/tools/trade-tools.ts#L115), but those warnings are now accurately disclosed in the task and handoffs.

### Recheck Verdict

`approved`

### Recheck Summary

The implementation now matches the reviewed contract closely enough to approve. The remaining risks are limited to coverage depth around the startup AC-6 env-var path and the already-disclosed lint warnings, not to product behavior defects.
