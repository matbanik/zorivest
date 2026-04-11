# 2026-04-11 Watchlist Redesign Plan Size - Plan Critical Review

> Date: 2026-04-11
> Review mode: plan
> Target plan: `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/`
> Canonical review file: `.agent/context/handoffs/2026-04-11-watchlist-redesign-plan-size-plan-critical-review.md`

## Scope and Correlation

- Plan review mode was selected because the user provided the plan folder explicitly, `task.md` is still `pending_approval`, and no correlated work handoff exists yet.
- Reviewed artifacts:
  - `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md`
  - `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md`
  - `docs/build-plan/06i-gui-watchlist-visual.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/known-issues.md`
  - `.agent/docs/emerging-standards.md`
  - `packages/core/src/zorivest_core/domain/settings.py`
  - `packages/api/src/zorivest_api/routes/settings.py`
  - `packages/api/src/zorivest_api/routes/plans.py`
  - `mcp-server/src/tools/planning-tools.ts`
  - `ui/src/renderer/src/features/planning/TradePlanPage.tsx`
  - `ui/src/renderer/src/features/planning/PositionCalculatorModal.tsx`
  - `packages/api/src/zorivest_api/routes/watchlists.py`
  - `tests/unit/test_api_watchlists.py`
  - `tests/unit/test_api_plans.py`

## Findings

### High - The draft plan would regress the already-shipped editable `shares_planned` workflow without resolving the spec conflict

- The draft turns the plan form into a readonly display for `shares_planned` and `position_size` (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:132`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:31`).
- The currently tracked repo contract already says MEU-70b delivered an editable `shares_planned` field, not a readonly one (`docs/BUILD_PLAN.md:263`).
- Current GUI state matches that completed contract: `TradePlanPage` renders an editable numeric input for `shares_planned` and a "Copy from Calc" action (`ui/src/renderer/src/features/planning/TradePlanPage.tsx:615`, `ui/src/renderer/src/features/planning/TradePlanPage.tsx:629`).
- If 06i is intended to replace the editable field with readonly calculator-driven data, that is a product decision conflict between MEU-70b and 06i that must be resolved explicitly before execution. As written, the plan silently chooses one side and would remove approved behavior.

### High - AC-18 is not implementable as written because `watchlist_colorblind_mode` does not exist in the settings registry

- The plan says the colorblind toggle will persist through the existing Settings API under key `watchlist_colorblind_mode` (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:27`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:108`).
- The Settings API rejects unknown keys by checking `key not in SETTINGS_REGISTRY` (`packages/api/src/zorivest_api/routes/settings.py:172`, `packages/api/src/zorivest_api/routes/settings.py:174`).
- The settings registry is documented as the canonical list of all 26 known settings (`packages/core/src/zorivest_core/domain/settings.py:9`, `packages/core/src/zorivest_core/domain/settings.py:60`), and a repo search found `watchlist_colorblind_mode` only in this plan draft.
- The task list contains no work to add a registry entry, validator, or settings tests. Execution would therefore hit a 404/validation failure on the first persistence attempt.

### High - The plan silently rewrites the `[PLAN-NOSIZE]` contract from `shares` to `shares_planned` without a source-backed resolution or compatibility rule

- The governing sources still define this MEU as full-stack propagation of `position_size` and `shares` (`docs/build-plan/06i-gui-watchlist-visual.md:37`, `docs/build-plan/06i-gui-watchlist-visual.md:41`, `docs/build-plan/06i-gui-watchlist-visual.md:48`, `.agent/context/known-issues.md:16`, `.agent/context/known-issues.md:21`, `docs/BUILD_PLAN.md:262`).
- The draft instead standardizes on `shares_planned` everywhere and explicitly says no alias is needed (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:44`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:56`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:64`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:67`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:23`).
- Current repo canon does use `shares_planned` internally (`packages/core/src/zorivest_core/domain/entities.py:141`, `packages/infrastructure/src/zorivest_infra/database/models.py:144`, `packages/api/src/zorivest_api/routes/plans.py:64`, `packages/api/src/zorivest_api/routes/plans.py:289`), but that does not resolve the outward contract drift on its own.
- Before execution, the plan needs an explicit, source-backed rule for one of these paths:
  - keep external/user-facing contract as `shares` and add alias mapping,
  - formally rename the build-plan/known-issue contract to `shares_planned`,
  - or document a human-approved compatibility policy.

### Medium - The `BUILD_PLAN.md` audit task is stale and would duplicate an entry that already exists

- The implementation plan says `docs/BUILD_PLAN.md` currently has no watchlist-visual or MEU-70 references and requires a new status entry (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:182`).
- The task file repeats that stale premise by making "MEU-70a status entry added" a deliverable (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:34`).
- But `docs/BUILD_PLAN.md` already contains the MEU-70a row with the 06i reference and description (`docs/BUILD_PLAN.md:262`).
- This should be rewritten as "update existing MEU-70a status/details if needed", not "add a new entry".

### Medium - `task.md` is not execution-ready under the repo's mandatory TDD and shell contracts

- The repo requires tests before implementation and a fail-first Red phase for every MEU (`AGENTS.md:208`, `AGENTS.md:223`, `AGENTS.md:224`).
- The task sequence starts with backend and MCP implementation work before any Red-phase test task exists (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:19` through `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:26`), and even the watchlist utility test task comes after the utility file creation task (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:26`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:27`).
- The task also points API validation at a nonexistent file, `tests/unit/test_plans_api.py` (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:22`), while the actual test file is `tests/unit/test_api_plans.py:1`.
- P0 also requires every terminal command to use the redirect-to-file pattern (`AGENTS.md:17`, `AGENTS.md:21`), but multiple task validation commands are written as bare `uv run ...` or `cd ...; npx ...` commands with no receipt file (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:19` through `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:35`).

## Review Checks

| Check | Result | Notes |
|---|---|---|
| Plan/task consistency | Fail | Shared scope exists, but task deliverables are stale and execution order breaks the repo TDD contract. |
| Status readiness | Pass | Plan is still pre-implementation; no correlated work handoff found. |
| Source-traceability | Fail | `shares` was silently normalized to `shares_planned` without resolving the spec/build-plan wording conflict. |
| Validation specificity | Fail | One validation target file does not exist, and shell commands ignore the mandatory redirect pattern. |
| Dependency/order correctness | Fail | Existing MEU-70b behavior would be regressed without an explicit decision gate. |
| Boundary prerequisite check | Pass | The MEU-70a `[BOUNDARY-GAP]` watchlist-route prerequisite is already satisfied in current source (`packages/api/src/zorivest_api/routes/watchlists.py:32`, `packages/api/src/zorivest_api/routes/watchlists.py:39`, `packages/api/src/zorivest_api/routes/watchlists.py:46`, `tests/unit/test_api_watchlists.py:200`). |

## Commands Executed

```powershell
git status --short *> C:\Temp\zorivest\git-status-short.txt
rg -n "shares_planned|position_size|watchlist_colorblind_mode|zorivest:calculator-apply|zorivest:open-calculator|trade-planning-tools|planning-tools\.ts|test_api_plans\.py|test_plans_api\.py" packages ui mcp-server tests docs .agent *> C:\Temp\zorivest\rg-plan-review.txt
rg -n -e watchlist_colorblind_mode -e colorblind -e shares_planned -e position_size -e zorivest:calculator-apply -e zorivest:open-calculator packages ui mcp-server *> C:\Temp\zorivest\rg-specific2.txt
rg -n -e watchlists_router -e CreateWatchlist -e UpdateWatchlist -e AddWatchlistItem -e 'extra="forbid"' -e StrippedStr packages/api/src/zorivest_api/routes/watchlists.py tests/unit *> C:\Temp\zorivest\rg-watchlists2.txt
git diff -- docs/BUILD_PLAN.md docs/build-plan/06i-gui-watchlist-visual.md docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md *> C:\Temp\zorivest\git-diff-plan.txt
rg -n -F "watchlist_colorblind_mode" docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md packages/core/src/zorivest_core/domain/settings.py packages/api/src/zorivest_api/routes/settings.py *> C:\Temp\zorivest\line-colorblind-all.txt
```

## Open Questions

- Does 06i intentionally supersede MEU-70b's editable `shares_planned` field, or should execution preserve editability and add only the new `position_size` display/write-back?
- Is the intended external contract for this MEU `shares`, `shares_planned`, or dual-name compatibility? The plan cannot treat that as settled until the build-plan and task artifacts agree.

## Verdict

`changes_required`

## Residual Risk

- If executed as written, this plan is likely to fail on the first settings persistence attempt, drift further from the documented `shares` contract, and potentially remove already-approved GUI behavior from MEU-70b.
- The current task list also cannot serve as reliable execution evidence because its test order and several validation commands are invalid under the repo's own workflow rules.

---

## Recheck - 2026-04-11 14:15 ET

### What Changed Since The Prior Review

- The plan no longer regresses MEU-70b's editable `shares_planned` behavior. It now preserves editability and limits readonly treatment to `position_size` (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:138`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:149`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:44`).
- The colorblind toggle persistence issue is now planned explicitly: the key was renamed to `ui.watchlist.colorblind_mode`, AC-29 was added, and the task includes registry/test work (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:27`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:114`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:33`).
- The `shares` versus `shares_planned` wording conflict was normalized across the cited canon docs:
  - `docs/build-plan/06i-gui-watchlist-visual.md:37`
  - `docs/BUILD_PLAN.md:262`
  - `.agent/context/known-issues.md:17`
- The stale `BUILD_PLAN.md` add-row task was corrected to updating the existing MEU-70a row/status (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:182`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:48`).
- The task file also fixed the bad API test path and most validation commands now follow the repo's redirect-to-file shell pattern (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:19`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:22`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:34`).

### Remaining Findings

#### Medium - The new `Human-approved` source labels still lack an independent approval artifact

- The revised plan and build-plan now label the `shares` -> `shares_planned` decision as `Human-Approved` / `Human-approved` (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:33`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:70`, `docs/build-plan/06i-gui-watchlist-visual.md:39`).
- But the planning workflow defines `Human-approved` as a rule resolved by explicit user decision (`.agent/workflows/create-plan.md:79` through `.agent/workflows/create-plan.md:82`).
- I rechecked the local artifacts and found the `Human-Approved` wording only inside the edited plan/build-plan set itself; I did not find an independent decision artifact, ADR, or handoff note recording an explicit user ruling for this naming change.
- The docs are now internally consistent, which removes the original contract-drift blocker, but the provenance label is still overstated unless the user decision is recorded somewhere outside the same edited plan text.

#### Medium - The task still does not fully satisfy the mandatory Red-first TDD contract for all sub-MEUs

- The task is much better than before: Sub-MEU A and part of Sub-MEU B now start with explicit Red-phase test work (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:19`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:34`).
- However, the repo contract is still "Write ALL tests FIRST" before implementation (`AGENTS.md:223`) and Sub-MEU C has no tester-owned Red phase at all. It begins directly with coder tasks for UI changes and only uses post-change `vitest`/`tsc` validation (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:42` through `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:46`).
- Task 8 also mixes registry code and test update into one coder task with no explicit fail-first proof (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:33`).
- Existing test canon for the planning surface already exists in `planning.test.tsx` (`ui/src/renderer/src/features/planning/__tests__/planning.test.tsx:942`), so the absence of Red-phase tasks here is a planning omission, not a tooling limitation.

### Commands Executed For Recheck

```powershell
git diff -- docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md .agent/context/handoffs/2026-04-11-watchlist-redesign-plan-size-plan-critical-review.md *> C:\Temp\zorivest\recheck-plan-diff.txt
rg -n -F "shares_planned" .agent/context/known-issues.md docs/build-plan/06i-gui-watchlist-visual.md docs/BUILD_PLAN.md *> C:\Temp\zorivest\recheck-shares-propagation.txt
rg -n -F "calculator-apply" docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md ui/src/renderer/src/features/planning/__tests__/planning.test.tsx *> C:\Temp\zorivest\recheck-calculator-apply.txt
rg -n -F "Human-Approved" -F "Human-approved" docs/execution/plans/2026-04-11-watchlist-redesign-plan-size docs/build-plan/06i-gui-watchlist-visual.md docs/BUILD_PLAN.md .agent/context/known-issues.md .agent/context/handoffs *> C:\Temp\zorivest\recheck-human-approved.txt
```

### Updated Verdict

`changes_required`

### Updated Residual Risk

- The plan is now close to execution-ready, but the source provenance for the renamed `shares_planned` contract is still self-asserted rather than independently evidenced.
- If execution starts with the current task table, the calculator write-back and settings-registry slices will not produce clean FAIL_TO_PASS evidence under the repo's TDD rules.

---

## Recheck - 2026-04-11 14:50 ET

### What Changed Since The Prior Recheck

- The task now satisfies the Red-first TDD structure that was still missing in the previous pass:
  - Settings registry now has an explicit Red test task before implementation (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:33`).
  - Calculator write-back now has an explicit tester-owned Red task before the UI implementation steps (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md:45`).
- The implementation plan now cites a concrete decision record for the `shares_planned` naming choice: `pomera note #795` (`docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:33`, `docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md:70`).

### Remaining Finding

#### Medium - The `Human-approved` label for `shares_planned` is better documented, but the cited note still records an inferred approval rather than an explicit naming decision

- The planning contract still requires `Human-approved` behaviors to be resolved by explicit user decision (`.agent/workflows/create-plan.md:79` through `.agent/workflows/create-plan.md:82`).
- The new decision artifact exists: `pomera` note `#795` (`Memory/Decisions/shares-planned-naming-2026-04-11`).
- But the note’s own text does not show a direct user decision on the `shares` versus `shares_planned` naming conflict. It records the user statement as: `chatgpt recommended ui.watchlist.colorblind_mode and I agree with it in retrospect` and then treats the absence of objection to `shares_planned` as confirmation of that naming choice.
- That is materially better than the prior self-asserted label, but it is still an inferred approval for the naming decision rather than an explicit user ruling on that specific conflict.

### Resolved Since Prior Recheck

- The prior TDD finding is resolved. The current task now provides fail-first coverage for:
  - backend `position_size` work (`task.md:21`)
  - settings registry key addition (`task.md:33`)
  - watchlist utilities (`task.md:35`)
  - calculator write-back / readonly `position_size` flow (`task.md:45`)

### Commands Executed For This Recheck

```powershell
git diff -- docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/task.md docs/build-plan/06i-gui-watchlist-visual.md .agent/context/known-issues.md docs/BUILD_PLAN.md .agent/context/handoffs/2026-04-11-watchlist-redesign-plan-size-plan-critical-review.md *> C:\Temp\zorivest\recheck2-plan-diff.txt
Get pomera note #795
Read full numbered task.md to verify Red/Green ordering
rg -n -F "pomera note #795" docs/execution/plans/2026-04-11-watchlist-redesign-plan-size/implementation-plan.md docs/build-plan/06i-gui-watchlist-visual.md .agent/context/handoffs/2026-04-11-watchlist-redesign-plan-size-plan-critical-review.md *> C:\Temp\zorivest\recheck3-note795.txt
```

### Updated Verdict

`changes_required`

### Updated Residual Risk

- The plan structure is now execution-ready apart from one provenance issue.
- If the team accepts inferred approval recorded in `pomera` notes as sufficient for `Human-approved`, this plan is effectively ready. Under the stricter wording of the planning contract, though, the `shares_planned` naming decision still needs either:
  - a direct user approval artifact,
  - or relabeling to a different allowed source type.
