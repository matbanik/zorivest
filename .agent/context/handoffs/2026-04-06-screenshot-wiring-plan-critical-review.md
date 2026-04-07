# Task Handoff Template

## Task

- **Date:** 2026-04-06
- **Task slug:** 2026-04-06-screenshot-wiring-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Plan review mode for `docs/execution/plans/2026-04-06-screenshot-wiring/` (`implementation-plan.md` + `task.md`)

## Inputs

- User request: Critical review of `.agent/workflows/critical-review-feedback.md`, `docs/execution/plans/2026-04-06-screenshot-wiring/implementation-plan.md`, and `docs/execution/plans/2026-04-06-screenshot-wiring/task.md`
- Specs/docs referenced: `AGENTS.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `pomera_notes` search for `Zorivest`, `.agent/docs/emerging-standards.md`, `.agent/workflows/critical-review-feedback.md`, `.agent/workflows/create-plan.md`, `.agent/workflows/meu-handoff.md`, `docs/BUILD_PLAN.md`, `docs/build-plan/06b-gui-trades.md`, `docs/build-plan/06-gui.md`, `docs/build-plan/04a-api-trades.md`, `docs/build-plan/gui-actions-index.md`
- Constraints: Review-only workflow. No product or plan fixes in this pass. Canonical rolling handoff path required.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files: `.agent/context/handoffs/2026-04-06-screenshot-wiring-plan-critical-review.md`
- Design notes / ADRs referenced: None
- Commands run: None
- Results: No repo fixes applied; review-only

## Tester Output

- Commands run:
  - `pomera_diagnose`
  - `pomera_notes search "Zorivest"`
  - `get_text_file_contents` on the target plan/task, workflow/context files, and cited canonical docs/code
  - `git status`
  - `rg -n "MEU-47a|ScreenshotPanel|DELETE /api/v1/images|delete_image\(|/images/\{image_id\}|trade-images|lightbox|Paste \(Ctrl\+V\)" p:\zorivest`
  - `rg -n "screenshot-wiring|Screenshot Panel|Create handoff|Handoff Naming|Memory/Session/Zorivest-screenshot-wiring" ...`
  - `rg -n "class ImageRepository|def delete\(|self\.uow\.images\.delete|@.*images|/api/v1/images|def get_for_owner|def get_full_data" ...`
  - `rg -n "TestTradeImages|TestGlobalImages|test_get_image_metadata|test_get_full_image|test_upload_trade_image_201|delete.*image|DELETE /api/v1/images|/api/v1/images/\{image_id\}" ...`
  - `rg -n "drag|drop|clipboard|paste|Screenshot panel supports upload, paste, and lightbox viewing|Screenshot Panel" ...`
  - `Test-Path .agent/context/handoffs/2026-04-06-screenshot-wiring-plan-critical-review.md`
- Pass/fail matrix:
  - Explicit-path scope override to plan review mode: PASS
  - No correlated MEU handoff exists yet: PASS
  - Repo baseline still matches "unstarted" task state: FAIL
  - Backend regression coverage scope in task rows: FAIL
  - Frontend regression coverage scope in task rows: FAIL
  - Spec-scope completeness for clipboard/drag-drop behavior: FAIL
  - Exact handoff artifact declaration in task rows: FAIL
- Repro failures:
  - `packages/core/src/zorivest_core/services/image_service.py:96-107` already contains `delete_image`, and `tests/unit/test_image_service.py:96-123` already contains the two delete tests, while `implementation-plan.md:20-29` and `task.md:19-22` still describe those slices as future RED/GREEN work.
  - `task.md:20,23` targets a new `tests/unit/test_image_routes.py`, but current image-route canon and adjacent coverage live in `tests/unit/test_api_trades.py:211-314`.
  - `task.md:21,24` targets only a new `ScreenshotPanel.test.tsx`, while existing integration coverage already lives in `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx:211-230` and `ui/src/renderer/src/features/trades/TradeDetailPanel.tsx:299-303`.
  - `implementation-plan.md:112-115` explicitly defers Electron clipboard API wiring and drag-and-drop upload even though the cited spec requires both behaviors in `docs/build-plan/06b-gui-trades.md:207,236-254` and the action index records drag-drop delete/open contracts in `docs/build-plan/gui-actions-index.md:48-52`.
- Coverage/test gaps: Review-only pass; no product tests executed
- Evidence bundle location: This handoff file
- FAIL_TO_PASS / PASS_TO_PASS result: N/A
- Mutation score: N/A
- Contract verification status: changes_required

## Reviewer Output

- Findings by severity:
  - **High** — The plan is stale against the live repo baseline, so its TDD sequence cannot produce honest fail-to-pass evidence for the backend slice. `implementation-plan.md:20-29` and `task.md:19-22` still say `ImageService.delete_image()` and its two unit tests are future work, but the dirty working tree already contains both the implementation at `packages/core/src/zorivest_core/services/image_service.py:96-107` and the tests at `tests/unit/test_image_service.py:96-123`. That breaks the workflow's requirement to confirm a real Red phase before Green, and it means this target is no longer genuinely "not started" in repository state even though the task file says it is.
  - **High** — The plan makes unsourced scope cuts against the cited screenshot-panel spec. `implementation-plan.md:112-115` declares Electron clipboard API wiring and drag-and-drop upload out of scope, but the plan cites `docs/build-plan/06b-gui-trades.md §Screenshot Panel` as authority, and that spec explicitly calls for Electron clipboard usage plus file input or drag-and-drop at `docs/build-plan/06b-gui-trades.md:207,236-254`. `docs/build-plan/gui-actions-index.md:48-52` also treats drag-and-drop upload as part of the contract. Under `AGENTS.md` and `create-plan.md:143-146`, this cannot be deferred without a source-backed carry-forward rule or explicit follow-up MEU.
  - **Medium** — Backend verification scope is too narrow and would miss regressions in the already-existing image API surface. `task.md:20,23` only runs a new `tests/unit/test_image_routes.py`, but current coverage for image listing/upload/global-image routes lives in `tests/unit/test_api_trades.py:211-314`, and the active route surface spans both `packages/api/src/zorivest_api/routes/trades.py:178-225` and `packages/api/src/zorivest_api/routes/images.py:1-67`. A plan that only proves the new DELETE path can still regress GET list/upload/metadata/full-image behavior.
  - **Medium** — Frontend verification scope is also too narrow for the component integration this MEU changes. `task.md:21,24` only references a new `ui/src/renderer/src/features/trades/__tests__/ScreenshotPanel.test.tsx`, but existing integration coverage already exercises the component in `ui/src/renderer/src/features/trades/__tests__/trades.test.tsx:211-230`, and the live consumer wiring is `ui/src/renderer/src/features/trades/TradeDetailPanel.tsx:299-303`. Replacing the prop-driven shell with self-contained React Query logic can break the trade-detail tab contract while the new isolated test file still passes.
  - **Medium** — The handoff row does not meet the exact-artifact planning contract. `task.md:29` uses a placeholder path `.agent/context/handoffs/{SEQ}-2026-04-06-screenshot-wiring-bp06bs16.1.md` and validates it with a wildcard `Test-Path .agent/context/handoffs/*screenshot*`. `create-plan.md:133-146` requires exact handoff file paths in the plan/task, and `.agent/workflows/meu-handoff.md:90-99` treats the handoff file as the primary execution artifact. This row is not deterministic enough for later review continuity.
- Open questions:
  - Was the partially implemented `ImageService.delete_image()` slice an abandoned execution pass for this same project, or is it unrelated local work that needs to be excluded before planning can proceed?
  - If the intent is to keep drag-and-drop and Electron clipboard work out of MEU-47a, what approved source or follow-up MEU owns that remaining screenshot-panel contract?
- Verdict: changes_required
- Residual risk:
  - If execution starts from this plan unchanged, the team can claim RED/GREEN completion for backend delete behavior that is already present, leaving no trustworthy fail-to-pass evidence for that slice.
  - Even if the new DELETE route and React Query wiring land cleanly, the plan can still leave the screenshot panel short of the cited GUI contract and can miss regressions in existing upload/list/integration behavior.
- Anti-deferral scan result: No placeholder-code finding in scope, but the plan itself contains unsourced deferrals and stale baseline assumptions that must be corrected before execution.

## Guardrail Output (If Required)

- Safety checks: Not required for plan review
- Blocking risks: N/A
- Verdict: N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:** 2026-04-06

## Final Summary

- Status: changes_required
- Next steps:
  - Route the plan through `/planning-corrections`
  - Re-baseline the backend delete work to match current repo state, or explicitly convert this target into implementation-review mode
  - Remove or source-justify the clipboard/drag-drop deferrals
  - Add pass-to-pass regression coverage rows for the existing backend and frontend suites
  - Replace the placeholder/wildcard handoff row with an exact artifact path and exact validation command

---

## Recheck (Round 1) - 2026-04-06

**Workflow:** `/planning-corrections` recheck
**Agent:** Codex (GPT-5)

### Prior Pass Summary

| Finding | Prior Sev | Prior Status | Recheck Result |
|---|---|---|---|
| Stale backend baseline | High | Open | Fixed |
| Unsourced clipboard/drag-drop scope cut | High | Open | Fixed |
| Backend regression scope too narrow | Medium | Open | Fixed |
| Frontend regression scope too narrow | Medium | Open | Fixed |
| Placeholder/wildcard handoff row | Medium | Open | Fixed |

### Confirmed Fixes

- The backend baseline is now explicit. [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/implementation-plan.md):20-25 records `ImageService.delete_image()` and its two unit tests as pre-existing, and [task.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/task.md):17-19 converts that slice into a completed regression row instead of a fake Red/Green cycle.
- The screenshot scope now includes drag-and-drop and a source-backed clipboard resolution. [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/implementation-plan.md):83-99 adds AC-13 for drag-and-drop, and [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/implementation-plan.md):103-116 replaces the prior silent deferral with an explicit research-backed rationale for using renderer `ClipboardEvent` paste handling while keeping drag-and-drop in scope.
- Backend regression coverage is now correctly anchored to the existing canon. [task.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/task.md):19-23 moves the DELETE route tests into `tests/unit/test_api_trades.py`, and [task.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/task.md):23-24 adds a pass-to-pass backend suite row covering both `test_image_service.py` and `test_api_trades.py`.
- Frontend regression coverage is now two-layered. [task.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/task.md):20-25 keeps the new focused `ScreenshotPanel.test.tsx` red/green path, and [task.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/task.md):24-25 adds the existing `trades.test.tsx` integration regression row.
- The handoff artifact is now deterministic. [task.md](p:/zorivest/docs/execution/plans/2026-04-06-screenshot-wiring/task.md):29 declares the exact handoff path `104-2026-04-06-screenshot-wiring-bp06bs16.1.md` and validates it with an exact `Test-Path` command.

### Findings

- No remaining material findings in the corrected plan.

### Residual Risk

- The plan's clipboard approach is now explicitly justified, but execution still needs to prove the intended `Ctrl+V` behavior in renderer tests because the implementation will not use the exact Electron `clipboard.readImage()` sketch shown in the build-plan example.

### Verdict

`approved` - the previously reported plan-level issues are resolved well enough for execution to start.
