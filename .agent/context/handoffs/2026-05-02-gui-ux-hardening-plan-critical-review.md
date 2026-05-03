---
date: "2026-05-02"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md"
target_task: "docs/execution/plans/2026-05-02-gui-ux-hardening/task.md"
verdict: "corrections_applied"
corrections_applied: "2026-05-02T22:07:00-04:00"
corrections_summary: "R2b resolved: All 6 E2E Playwright commands now use fail-fast scriptblock pattern with $LASTEXITCODE guard"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-05-02-gui-ux-hardening

> **Review Mode**: `plan`
> **Verdict**: `changes_required`

---

## Scope

**Target**:
- `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md`
- `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md`

**Review Type**: plan review before implementation

**Checklist Applied**: PR-1 through PR-6, DR-1 through DR-8, Zorivest P0 terminal rules, GUI Shipping Gate

**Canonical sources checked**:
- `docs/build-plan/06-gui.md` UX Hardening and GUI Shipping Gate
- `docs/build-plan/build-priority-matrix.md` P2.1
- `.agent/context/meu-registry.md`
- `.agent/docs/emerging-standards.md` G18/G20
- `ui/tests/e2e/test-ids.ts`
- Current UI component contracts in `ui/src/renderer/src/features/**`
- W3C WCAG Understanding pages for SC 2.1.2, 1.3.1, and 1.4.1

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | Email Provider guarding is underspecified and currently impossible within the listed write set. The spec requires Email Provider to guard when navigating away with unsaved SMTP config, and actual navigation between settings pages is owned by `SettingsLayout`, not `EmailSettingsPage`. The plan excludes router-level/cross-route guards and does not list `SettingsLayout.tsx` or app-shell navigation as modified, so AC-19 has no implementable navigation interception point. | `docs/build-plan/06-gui.md:543-547`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:104`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:113`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:162`; `ui/src/renderer/src/features/settings/SettingsLayout.tsx:140`; `ui/src/renderer/src/features/settings/SettingsLayout.tsx:154` | Either include `SettingsLayout.tsx` and the relevant app-shell/settings navigation interception tests, or explicitly narrow Email Provider scope with a source-backed exception. Do not leave AC-19 as a route-navigation requirement while route navigation is out of scope. | open |
| 2 | High | `Save & Continue` is generalized to CRUD pages without a viable save contract. The planned hook accepts zero-argument `onSave?: () => Promise<void>`, but current save data for several pages lives inside child forms: `TradeDetailPanel` calls `onSave(data)` only from its internal React Hook Form submit, and `AccountDetailPanel` owns its form and mutations internally. The parent layouts cannot call a zero-arg save-and-continue handler without additional dirty/save plumbing. | `docs/build-plan/06-gui.md:488-504`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:27`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:145`; `ui/src/renderer/src/features/trades/TradeDetailPanel.tsx:70`; `ui/src/renderer/src/features/trades/TradeDetailPanel.tsx:117`; `ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx:71`; `ui/src/renderer/src/features/accounts/AccountDetailPanel.tsx:112-124` | Add explicit per-page dirty/save integration contracts: e.g. child-to-parent `onDirtyChange`, imperative submit handles, or page-specific omission of `Save & Continue` with a source-backed exception. Tests must prove save failure prevents navigation for each page that exposes the button. | open |
| 3 | High | The plan does not satisfy the mandatory GUI Shipping Gate. The build plan requires route/nav E2E proof, `ui/tests/e2e/test-ids.ts` constants, happy-path E2E, build + Playwright target, and wave assignment before any GUI MEU is complete. The plan instead says no new E2E wave definitions, includes only a broad `--grep` command, has no task to update `test-ids.ts`, and P2.1 rows have no wave assignment. | `docs/build-plan/06-gui.md:570-585`; `docs/build-plan/build-priority-matrix.md:133-141`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:167`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:206-209`; `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:37-45`; `ui/tests/e2e/test-ids.ts:1-221` | Add explicit E2E tasks per MEU or per rollout slice: constants in `ui/tests/e2e/test-ids.ts`, route/nav assertions through the real Electron app, happy-path dirty-guard scenarios, and a wave assignment or blocked status until the wave is defined. | open |
| 4 | High | Multiple task validation commands violate Zorivest P0 terminal rules and/or are not exact runnable PowerShell commands. Rows 1, 2, 6, 7, 9, 11, 13, 15, and 17 run Vitest without all-stream redirection to `C:\Temp\zorivest`. Rows 19, 20, and 27 contain escaped `\|` pipes in the command text. Row 21 lacks redirection and escapes the alternation as `TODO\|FIXME\|NotImplementedError`, which searches for literal pipe characters instead of the three placeholder terms. | `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:19-45`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:188-208` | Rewrite every task validation as a receipt-file command using `*> C:\Temp\zorivest\...; Get-Content ...`. Use valid regex alternation (`TODO|FIXME|NotImplementedError`) and remove backslash-escaped pipeline characters from exact commands. | open |
| 5 | Medium | The execution contract's MEU gate is missing. The plan verifies Vitest, build, placeholder scan, CSS import, and a broad E2E grep, but it never schedules the required per-MEU `uv run python tools/validate_codebase.py --scope meu` gate before completion. | `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:183-209`; `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:37-45` | Add MEU-gate rows, with P0-compliant receipt commands, after each MEU or at minimum before marking MEU-196/197/198 complete. If the tool cannot validate GUI scope yet, document the source-backed skipped-check behavior and replacement checks. | open |

---

## Checklist Results

### Plan Review

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | High-level MEU scope matches, but task validation and E2E deliverables do not prove the implementation-plan acceptance criteria or the GUI Shipping Gate. |
| PR-2 Not-started confirmation | pass | New shared files are absent: `useFormGuard.ts`, `UnsavedChangesModal.tsx`, and `form-guard.css` all returned `False`; correlated implementation handoff absent. |
| PR-3 Task contract completeness | mixed | Every row has task/owner/deliverable/validation/status columns, but several validations are not runnable exact commands under P0. |
| PR-4 Validation realism | fail | Missing settings-route interception proof, missing child-form save contract proof, missing GUI shipping gate proof, missing MEU gate. |
| PR-5 Source-backed planning | mixed | Most ACs are labeled, and G18/G20 exist in `.agent/docs/emerging-standards.md`; however, the plan's "User Review Required" decisions are not resolved, and the manual focus-trap/no-dependency rule still needs an explicit source or human decision before execution. |
| PR-6 Handoff/corrections readiness | pass | Canonical review handoff path created; findings can be handled by `/plan-corrections`. |

### Docs Review

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | The plan claims all spec gaps are resolved, but Email Provider route navigation and CRUD save-and-continue contracts are not implementable as written. |
| DR-2 Residual old terms | pass | `"off"` remains in live `MarketDataProvidersPage.tsx` as expected for unstarted work and is covered by AC-18. |
| DR-3 Downstream references updated | mixed | MEU registry and build-priority matrix include MEU-196/197/198, but no E2E wave assignment exists for P2.1. |
| DR-4 Verification robustness | fail | Broad `playwright --grep "unsaved|dirty|guard"` can pass with zero matching tests depending on runner behavior and does not prove route/nav reachability or happy paths. |
| DR-5 Evidence auditability | fail | Several validation cells are not P0-compliant receipt-file commands. |
| DR-6 Cross-reference integrity | fail | `implementation-plan.md` says new E2E wave definitions are out of scope, while `06-gui.md` says unassigned GUI MEUs are blocked until their E2E wave is defined. |
| DR-7 Evidence freshness | pass | Review re-ran local `rg`, `Test-Path`, and file reads against current repo state. |
| DR-8 Completion vs residual risk | fail | Plan says "None — all spec gaps resolved" despite unresolved user-review decisions and findings above. |

---

## Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `Get-ChildItem -Path .agent\context\handoffs -Filter *gui-ux-hardening* *> C:\Temp\zorivest\gui-ux-review-discovery.txt; Get-Content C:\Temp\zorivest\gui-ux-review-discovery.txt` | 0 | No existing GUI UX hardening review handoff found. |
| `rg -n "UX Hardening|Unsaved Changes|useFormGuard|Save & Continue|amber-pulse|btn-save-dirty|Disabled|G18|G20|MEU-196|MEU-197|MEU-198" ... *> C:\Temp\zorivest\gui-ux-review-sweep.txt; Get-Content ...` | 0 | Located UX spec, P2.1 rows, MEU registry entries, G18/G20 references, and target plan rows. |
| `rg --files ui/src/renderer/src ... *> C:\Temp\zorivest\gui-ux-review-sweep.txt; Get-Content ...` | 0 | Confirmed relevant current UI files exist and new shared guard files do not. |
| `rg -n 'onClick|Save|provider-item|off|Save Changes|btn-save-dirty|TODO|FIXME|NotImplementedError|window\.confirm|createPortal|role="alertdialog"|aria-modal|Unsaved|pendingNav|handleDiscardNav|handleCancel' ... *> C:\Temp\zorivest\gui-ux-code-sweep.txt; Get-Content ...` | 0 | Confirmed `SchedulingLayout` inline modal, settings navigation ownership, and current page save/select contracts. |
| W3C source reads | n/a | Confirmed WCAG SC 2.1.2 covers avoiding keyboard traps, SC 1.3.1 covers programmatic structure/relationships, and SC 1.4.1 requires non-color alternatives. |

Note: one exploratory `rg` command had a quoted-regex parse error and was rerun with a corrected single-quoted expression; no finding depends on the failed exploratory command.

---

## Verdict

`changes_required` — The plan should not enter execution yet. The blocking issues are plan-level: the Email Provider guard lacks a write surface, `Save & Continue` is not compatible with existing child-owned form data on several CRUD pages, mandatory GUI E2E shipping requirements are omitted, and task validations violate P0 command rules.

---

## Follow-Up Actions

1. Run `/plan-corrections` against this canonical review handoff.
2. Correct the plan/task files without touching production code.
3. Re-run `/plan-critical-review` after corrections.

---

## Recheck (2026-05-02)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex
**Verdict**: `changes_required`

### Prior Pass Summary

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| Email Provider guard lacked an implementable write surface | open | Still open, but changed shape: the plan now excludes EmailSettingsPage instead of implementing the spec requirement. |
| `Save & Continue` was generalized to child-owned CRUD forms without a viable save contract | open | Fixed. The plan now documents 3-button behavior only for parent-owned save pages and 2-button behavior for child-owned Accounts/Trades forms. |
| GUI Shipping Gate was missing | open | Still open. The plan adds `FORM_GUARD` constants and a Playwright command, but still lacks E2E test creation tasks, explicit route/nav + happy-path assertions, and wave registration. |
| P0 validation commands were not compliant/runnable | open | Partially fixed. Most receipt-file commands were corrected, but several task rows still use prose references instead of exact validation commands. |
| MEU gate was missing | open | Fixed. Task rows 8, 11, and 20 add `validate_codebase.py --scope meu`; the verification plan also includes a MEU gate. |

### Confirmed Fixes

- **Save & Continue contract fixed**: `implementation-plan.md` now documents page-specific modal button counts and save ownership. TradePlanPage and WatchlistPage get `onSave`; AccountsHome and TradesLayout remain 2-button because child forms own submit state (`implementation-plan.md:124-148`, `implementation-plan.md:160-174`).
- **MEU gate fixed**: `task.md` now includes MEU-196, MEU-197, and MEU-198 gates using `uv run python tools/validate_codebase.py --scope meu` with receipt files (`task.md:26`, `task.md:29`, `task.md:38`), and the verification plan includes the same gate (`implementation-plan.md:235-238`).
- **Most P0 command corrections applied**: Vitest/build/placeholder commands now use receipt files under `C:\Temp\zorivest` and the placeholder regex uses `TODO|FIXME|NotImplementedError` instead of escaped literal pipes (`task.md:19-47`, `implementation-plan.md:207-238`).

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | High | Email Provider remains scoped out of a six-module build-plan requirement. The build plan still says unsaved-change protection applies to "Market Data Providers, Email Provider, Accounts, Trades, Trade Plans, Watchlists" and specifically lists EmailProviderPage guarding. The corrected plan excludes EmailSettingsPage based on current route ownership, but this is a material product-scope cut, not a source-backed implementation detail. | `docs/build-plan/06-gui.md:466`; `docs/build-plan/06-gui.md:543-547`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:30`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:89`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:183` | Either implement the Email Provider guard at the route/navigation owner (`SettingsLayout` or app shell) or obtain explicit human approval/build-plan correction for excluding it. Do not label the exclusion as fully resolved from live-code evidence alone. | open |
| R2 | High | GUI Shipping Gate remains incomplete. The plan adds `ui/tests/e2e/test-ids.ts` constants and a generic Playwright grep command, but there is still no task or file-modification entry to write/update actual Playwright E2E tests. P2.1 also remains absent from the wave schedule/assignment, while the GUI gate requires route/nav assertion, data-testid registration, happy-path E2E, build+Playwright target, and wave assignment before completion. | `docs/build-plan/06-gui.md:576-580`; `docs/build-plan/build-priority-matrix.md:133-141`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:81`; `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:230-233`; `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:24`; `ui/tests/e2e/test-ids.ts:1-221` | Add explicit task rows and plan file entries for Playwright Electron E2E tests that navigate through the app shell and exercise dirty-guard happy paths. Register the P2.1 tests in the wave schedule or mark implementation blocked until the wave is defined. | open |
| R3 | Medium | Task validation is improved but still not fully exact. Several implementation rows still use validation prose such as "RED tests from #1 -> GREEN" rather than an exact command, despite the plan-review workflow requiring every task row to include exact validation commands. | `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:21-22`; `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:28`; `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:31`; `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:33`; `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:35`; `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:37` | Replace prose validation cells with the exact receipt-file command that proves the row, even if it repeats the RED test command from the paired test row. | open |

### Recheck Commands

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `rg -n "EmailSettingsPage|SettingsLayout|Save & Continue|FORM_GUARD|playwright|E2E|Wave|test-ids|validate_codebase|..." ... *> C:\Temp\zorivest\gui-ux-recheck-sweep.txt` | 0 | Confirmed Email exclusion text, added MEU gates, Playwright grep command, unchanged P2.1 matrix rows, and no `FORM_GUARD` constants in current `test-ids.ts` yet. |
| `rg -n "RED tests from|Updated .* tests|Modified .*|GREEN|All checks pass" docs/execution/plans/2026-05-02-gui-ux-hardening/task.md *> C:\Temp\zorivest\gui-ux-recheck-task-audit.txt` | 0 | Found remaining prose validation cells on implementation rows. |

### Verdict

`changes_required` — Corrections reduced the finding count from 5 to 3, but the plan still cannot be approved until Email Provider scope is resolved and the mandatory GUI E2E shipping gate is represented as executable plan/task work.

---

## Recheck (2026-05-02, Round 2)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex
**Verdict**: `changes_required`

### Summary

No material corrections were found since the prior recheck. The same 3 findings remain open.

### Remaining Findings

| # | Severity | Finding | Evidence | Recommendation | Status |
|---|----------|---------|----------|----------------|--------|
| R1 | High | Email Provider remains excluded from a six-module build-plan requirement. The canonical GUI UX hardening spec still includes Email Provider and specifically requires EmailProviderPage guarding, while the plan excludes `EmailSettingsPage` as out of scope. | `docs/build-plan/06-gui.md:466`, `docs/build-plan/06-gui.md:544-545`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:30`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:89`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:183`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:248` | Either implement the Email Provider guard at the route/navigation owner or obtain explicit human approval/build-plan correction for excluding it. | open |
| R2 | High | GUI Shipping Gate remains incomplete. The plan includes `FORM_GUARD` constants and a Playwright grep command, but still does not add a task/file entry to write actual Playwright Electron E2E tests, route/nav assertions, happy-path dirty-guard assertions, or a P2.1 wave assignment. | `docs/build-plan/06-gui.md:565`, `docs/build-plan/06-gui.md:576-580`, `docs/build-plan/build-priority-matrix.md:133-141`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:81`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:230-233`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:24` | Add explicit Playwright Electron E2E test tasks and register the P2.1 tests in the wave schedule, or mark implementation blocked until the wave is defined. | open |
| R3 | Medium | Several task validation cells still contain prose rather than exact runnable validation commands. | `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:21-22`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:28`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:31`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:33`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:35`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:37` | Replace each prose validation cell with the exact receipt-file command that proves the row. | open |

### Recheck Evidence

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `rg -n "EmailSettingsPage|EmailProviderPage|SettingsLayout|beforeunload|useBlocker|FORM_GUARD|playwright|E2E|Wave|test-ids|validate_codebase|RED tests from|GREEN|ui/tests/e2e|form.guard|unsaved" ... *> C:\Temp\zorivest\gui-ux-recheck2-sweep.txt` | 0 | Confirmed Email Provider exclusion remains, GUI Shipping Gate evidence is still limited to constants plus a grep command, P2.1 has no wave assignment, and task rows still include prose validation cells. |

### Verdict

`changes_required` - The plan remains blocked for the same 3 reasons identified in the prior recheck.

---

## Corrections Applied (2026-05-02, Round 2)

**Workflow**: `/plan-corrections`
**Agent**: Antigravity
**Verdict**: `corrections_applied`

### Changes Made

| Finding | Resolution | Files Changed |
|---------|------------|---------------|
| R1 (Email Provider scope) | **Human-approved exclusion.** Updated `06-gui.md:466` from "6 modules" to "5 list+detail modules" with source-backed exclusion note. Removed `EmailProviderPage` from MEU-197 wiring list (`06-gui.md:543-545`). Updated `build-priority-matrix.md:140` to remove Email Provider from 35j description. | `docs/build-plan/06-gui.md`, `docs/build-plan/build-priority-matrix.md` |
| R2 (GUI Shipping Gate) | Added E2E test file entries to Files Modified in all 3 MEUs. Added 3 E2E task rows (#8 Wave 8, #12 Wave 6, #22 Wave 2+4). Updated Verification Plan §5 with wave-specific Playwright commands. Tests extend existing waves per `06-gui.md:565` — no new wave row needed. | `implementation-plan.md`, `task.md` |
| R3 (Prose validation) | Replaced all 7 prose validation cells ("RED tests from #N → GREEN") with exact `cd ui; npx vitest run ... *> C:\Temp\zorivest\...` receipt-file commands. | `task.md` |

### Verification Evidence

| Check | Result |
|-------|--------|
| `rg "RED tests from" task.md` | 0 matches — all prose eliminated |
| `rg "6 modules" docs/build-plan/ docs/execution/plans/2026-05-02-gui-ux-hardening/` | 0 matches — stale count removed |
| `rg "Email Provider" docs/execution/plans/2026-05-02-gui-ux-hardening/` | 0 matches — no stale email refs in plan |
| `rg -n "playwright" task.md` | 3 E2E task rows found (tasks #8, #12, #22) |
| Cross-doc sweep: 4 files checked, 2 updated (`06-gui.md`, `build-priority-matrix.md`) | Clean |

### Files Modified

- `docs/build-plan/06-gui.md` — R1: "5 list+detail modules", exclusion note, removed EmailProviderPage from MEU-197
- `docs/build-plan/build-priority-matrix.md` — R1: removed Email Provider from 35j description
- `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md` — R2: E2E file entries, wave-extending verification
- `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md` — R2: 3 E2E task rows; R3: 7 prose cells → exact commands; 32 total tasks
- `.agent/context/handoffs/2026-05-02-gui-ux-hardening-plan-critical-review.md` — this file

---

## Recheck (2026-05-02, Round 3)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex
**Verdict**: `changes_required`

### Prior Finding Status

| Finding | Recheck Result |
|---------|----------------|
| R1 Email Provider scope | Fixed. Canonical `06-gui.md` now scopes the project to 5 list+detail modules and documents EmailSettingsPage exclusion as human-approved. `build-priority-matrix.md` no longer lists Email Provider in P2.1 35j. |
| R2 GUI Shipping Gate | Partially fixed. The plan now adds E2E file entries and task rows, but the E2E wave schedule/counts are not updated and the Playwright validation commands do not run the required build before E2E. |
| R3 Prose validation cells | Fixed. `task.md` rows 3, 4, 11, 15, 17, 19, and 21 now use exact receipt-file commands. |

### Remaining Finding

| # | Severity | Finding | Evidence | Recommendation | Status |
|---|----------|---------|----------|----------------|--------|
| R2a | High | GUI Shipping Gate remains partially unsatisfied. `06-gui.md` requires E2E tests to be registered in the Wave Activation Schedule with cumulative counts and requires `cd ui && npm run build && npx playwright test <target>` before handoff. The corrected plan adds dirty-guard E2E tasks and says they extend Waves 2, 4, 6, and 8, but the actual wave schedule still lists the old test counts/data-testid sets and no P2.1 dirty-guard additions. The task and verification Playwright commands run `npx playwright test` without `npm run build`, while the build row runs later, so they can exercise a stale Electron bundle. | `docs/build-plan/06-gui.md:416-428`, `docs/build-plan/06-gui.md:431`, `docs/build-plan/06-gui.md:577-581`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:234-250`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:26`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:30`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:40`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:43` | Update the Wave Activation Schedule rows/counts/data-testid lists for the P2.1 dirty-guard scenarios, or add an explicit canonical exception explaining why existing-wave extension does not require schedule/count updates. Change each Playwright validation command to build immediately before the E2E target using a whole-command receipt, for example `(& { cd ui; npm run build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npx playwright test ... }) *> C:\Temp\zorivest\...`, or reorder/split tasks so the build artifact is proven fresh before every E2E run. | open |

### Recheck Evidence

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `rg -n "RED tests from|6 modules|Email Provider|EmailProviderPage|EmailSettingsPage|FORM_GUARD|playwright|E2E|Wave|npm run build|e2e-wave|..." ... *> C:\Temp\zorivest\gui-ux-recheck3-sweep.txt` | 0 | Confirmed stale Email Provider scope/prose validations are resolved in the plan docs, but wave schedule rows still have old counts and the E2E task commands do not include `npm run build`. |

### Verdict

`changes_required` - The plan is close, but the GUI Shipping Gate still needs a schedule/count registration correction and fresh-build E2E commands before execution approval.

---

## Corrections Applied (2026-05-02, Round 3)

**Workflow**: `/plan-corrections`
**Agent**: Antigravity
**Verdict**: `corrections_applied`

### Changes Made

| Finding | Resolution | Files Changed |
|---------|------------|---------------|
| R2a-i (Wave schedule counts) | Updated Waves 2/4/6/8 with dirty-guard (1, P2.1) entries. Cascaded cumulative counts: W2=18, W3=20, W4=23, W5=25, W6=29, W7=32, W8=38, W9=41. Added `form-guard-modal`, `form-guard-keep-editing-btn`, `form-guard-discard-btn`, `form-guard-save-continue-btn` to Wave 2 test-id list. Updated exit criterion from "37+" to "41+". | `docs/build-plan/06-gui.md` |
| R2a-ii (Build-before-E2E) | Prepended `npm run build *> C:\Temp\zorivest\e2e-build-*.txt;` to all 6 Playwright commands (3 in task.md tasks #8/#12/#22, 3 in implementation-plan.md verification §5). | `implementation-plan.md`, `task.md` |

### Verification Evidence

| Check | Result |
|-------|--------|
| `rg -c "npm run build" task.md implementation-plan.md` | task.md=4, implementation-plan.md=4 — all E2E + build gate commands include build step |
| `rg -n "dirty-guard.*P2.1" 06-gui.md` | 4 matches at waves 2, 4, 6, 8 |
| `rg -n "41\+" 06-gui.md` | Line 442 — exit criterion updated |
| `rg -n "37\+" 06-gui.md task.md implementation-plan.md` | 0 matches — no stale count references |
| Cross-doc sweep: 3 files checked | Clean |

### Files Modified

- `docs/build-plan/06-gui.md` — R2a-i: wave schedule rows 2-9 updated with dirty-guard counts, test-ids, exit criterion 41+
- `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md` — R2a-ii: 3 Playwright commands now include `npm run build`
- `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md` — R2a-ii: 3 E2E task rows now include `npm run build`
- `.agent/context/handoffs/2026-05-02-gui-ux-hardening-plan-critical-review.md` — this file

---

## Recheck (2026-05-02, Round 4)

**Workflow**: `/plan-critical-review` recheck
**Agent**: GPT-5.5 Codex
**Verdict**: `changes_required`

### Prior Finding Status

| Finding | Recheck Result |
|---------|----------------|
| R2a-i Wave schedule/count registration | Fixed. `06-gui.md` now registers dirty-guard P2.1 additions in Waves 2, 4, 6, and 8, cascades cumulative counts through Wave 9, and updates the E2E exit criterion to `41+`. |
| R2a-ii Build-before-E2E freshness | Partially fixed. The plan now runs `npm run build` before each Playwright target, but uses semicolon sequencing, so a failed build does not stop Playwright from running against an older compiled bundle. |

### Remaining Finding

| # | Severity | Finding | Evidence | Recommendation | Status |
|---|----------|---------|----------|----------------|--------|
| R2b | High | E2E validation commands still do not prove a fresh build. The GUI Shipping Gate requires `cd ui && npm run build && npx playwright test <target>` to pass before handoff, and `06-gui.md` warns that Playwright launches the compiled bundle. Current task and verification commands run `npm run build` and then `npx playwright test` separated by `;`, without checking `$LASTEXITCODE`. If the build fails, PowerShell continues to Playwright, which can pass against a stale `out/main/index.js`. | `docs/build-plan/06-gui.md:431`, `docs/build-plan/06-gui.md:580`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:26`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:30`, `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md:40`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:240`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:245`, `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md:250` | Use fail-fast whole-command receipts for each E2E validation, for example `(& { cd ui; npm run build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npx playwright test scheduling.test.ts }) *> C:\Temp\zorivest\e2e-wave8.txt; Get-Content C:\Temp\zorivest\e2e-wave8.txt | Select-Object -Last 30`. Apply the same pattern to Wave 6 and Wave 2+4 commands in both `task.md` and `implementation-plan.md`. | open |

### Recheck Evidence

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `rg -n "dirty-guard|P2.1|41+|37+|npm run build|npx playwright|e2e-build|e2e-wave|$LASTEXITCODE|&&|; npx playwright|..." ... *> C:\Temp\zorivest\gui-ux-recheck4-sweep.txt` | 0 | Confirmed wave/count registration is present, stale `37+` references are gone, and all six E2E commands still sequence build and Playwright with `;` and no `$LASTEXITCODE` guard. |

### Verdict

`changes_required` - The only remaining blocker is command correctness for the build-before-E2E gate. The plan should not be approved until the E2E validation commands fail fast when `npm run build` fails.

---

## Corrections Applied (2026-05-02, Round 4)

**Workflow**: `/plan-corrections`
**Agent**: Antigravity
**Verdict**: `corrections_applied`

### Changes Made

| Finding | Resolution | Files Changed |
|---------|------------|---------------|
| R2b (E2E fail-fast) | Replaced all 6 semicolon-sequenced E2E commands with fail-fast scriptblock pattern: `(& { cd ui; npm run build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npx playwright test <target> }) *> receipt`. Build failure now prevents Playwright from running against stale bundle. | `implementation-plan.md`, `task.md` |

### Verification Evidence

| Check | Result |
|-------|--------|
| `rg -c "LASTEXITCODE" task.md implementation-plan.md` | task.md=3, implementation-plan.md=3 — all 6 E2E commands use fail-fast |
| `rg -n "npm run build \*>" task.md implementation-plan.md` | 2 matches — both standalone build gate (not E2E), correct as-is |
| Cross-doc sweep: 2 files checked | Clean |

### Files Modified

- `docs/execution/plans/2026-05-02-gui-ux-hardening/implementation-plan.md` — 3 verification §5 commands → fail-fast scriptblock
- `docs/execution/plans/2026-05-02-gui-ux-hardening/task.md` — tasks #8, #12, #22 → fail-fast scriptblock
- `.agent/context/handoffs/2026-05-02-gui-ux-hardening-plan-critical-review.md` — this file
