---
date: "2026-05-14"
review_mode: "plan"
target_plan: "docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md"
verdict: "approved"
findings_count: 0
template_version: "2.1"
requested_verbosity: "standard"
agent: "GPT-5.5 Codex"
---

# Critical Review: 2026-05-14-tax-gui

> **Review Mode**: `plan`
> **Verdict**: `approved` after recheck

---

## Scope

**Target**:
- `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md`
- `docs/execution/plans/2026-05-14-tax-gui/task.md`

**Review Type**: plan review
**Checklist Applied**: PR + DR

Additional evidence checked:
- `docs/build-plan/06-gui.md`
- `docs/build-plan/06g-gui-tax.md`
- `docs/build-plan/06h-gui-calculator.md`
- `docs/build-plan/build-priority-matrix.md`
- `docs/build-plan/04f-api-tax.md`
- `packages/api/src/zorivest_api/routes/tax.py`
- `packages/core/src/zorivest_core/domain/settings.py`
- `packages/core/src/zorivest_core/domain/settings_validator.py`
- `ui/tests/e2e/test-ids.ts`

---

## Commands Executed

| Command | Receipt |
|---|---|
| `rg -n "Tax Profile\|section_475\|Section 475\|/api/v1/settings\|FormGuard\|useFormGuard\|TaxLayout\|PositionCalculatorModal\|navRoutes\|Receipt\|tax-gui\|MEU-154\|MEU-155\|MEU-156\|data-testid\|API =\|__ZORIVEST_API_URL__\|settings" docs/build-plan docs/BUILD_PLAN.md .agent/context/meu-registry.md ui/src/renderer/src -g "*.md" -g "*.tsx" -g "*.ts"` | `C:\Temp\zorivest\plan-review-rg.txt` |
| `rg --files \| rg "emerging-standards\|test-ids\.ts\|SettingsLayout\.tsx\|PositionCalculatorModal\.tsx\|api.*tax\|routes.*tax\|tax.*routes\|Tax"` | `C:\Temp\zorivest\plan-review-files.txt` |
| `rg -n "section_475\|section_1256\|forex\|tax\.\|filing_status\|cost_basis" packages docs -g "*.py" -g "*.md"` | `C:\Temp\zorivest\tax-settings-rg.txt` |
| `rg -n "SETTINGS_REGISTRY\|SettingSpec\|tax\|section_475\|section_1256\|forex_worksheet" packages/core packages/api packages/infrastructure -g "*.py"` | `C:\Temp\zorivest\settings-registry-rg.txt` |
| `rg -n 'Every GUI MEU\|Build gate\|MEU is not complete\|Wave 11\|E2E Playwright tests\|POST.*quarterly\|GET.*quarterly\|emerging-standards\|section_475\|section_1256\|forex_reporting\|Matrix Item\|tax-gui' ...` | `C:\Temp\zorivest\finding-lines.txt` |
| `rg -n 'quarterly/payment\|tax_year: int\|Settings body\|Unknown setting\|SETTINGS_REGISTRY\|section_475\|section_1256\|Tax Estimator\|Position calculator GUI\|Section 475\|Tax should\|Close This Lot\|Reassign Method' ...` | `C:\Temp\zorivest\finding-lines-2.txt` |

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | The plan explicitly defers Playwright E2E tests, but the canonical GUI gate says every GUI MEU must include Electron E2E proof before completion. The task only adds Vitest component tests for MEU-154, so the plan cannot satisfy the GUI shipping gate or Wave 11 activation. | `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:232`; `docs/execution/plans/2026-05-14-tax-gui/task.md:32`; `docs/build-plan/06-gui.md:577`; `docs/build-plan/06-gui.md:584` | Add Wave 11 Playwright test implementation/build tasks and validation commands, including `cd ui && npm run build` and targeted `npx playwright test ...` receipts. | **resolved** — E2E removed from Out of Scope. AC-154.18 added. Wave 11 section added to task.md (rows 25a–25e). Verification Plan §5 added. |
| 2 | High | MEU-156 persistence is planned through `PUT /api/v1/settings`, but the canonical settings registry has no tax-profile keys and the validator rejects unknown settings. The plan also uses names that do not match the domain model (`section_475`/`section_1256`/`forex_reporting` vs. existing domain names such as `section_475_elected`, `section_1256_eligible`, and spec `forex_worksheet`). This will fail with 422 or silently wire the GUI to non-canonical keys. | `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:93`; `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:210`; `packages/core/src/zorivest_core/domain/settings.py:60`; `packages/core/src/zorivest_core/domain/settings_validator.py:72`; `docs/build-plan/06f-gui-settings.md:355` | Either add source-backed backend registry/API tasks for exact tax-profile keys, or route the GUI to the existing tax profile repository/API if that is the intended owner. Update the Boundary Input Contract with exact keys, schema owner, string/boolean encoding, and 422 mapping. | **resolved** — Option A selected: persistence `[B]` blocked. Toggles render read-only. Field names corrected to `section_475_elected`, `section_1256_eligible`. `forex_worksheet` marked blocked pending domain expansion. AC-156.5/AC-156.6 marked `[B]`. Task row 23a added as blocked. |
| 3 | High | Quarterly Tracker endpoints in the plan do not match the implemented API. The plan says payment entry posts to `POST /api/v1/tax/quarterly`, but the implemented route is `POST /api/v1/tax/quarterly/payment`. The implemented write body uses `payment_amount` and `confirm`, while the plan's boundary contract uses `amount` and `date_paid`. The implemented GET route also requires `quarter` and `tax_year`, so a single "list all quarters" fetch is not currently supported by the route. | `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:117`; `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:118`; `packages/api/src/zorivest_api/routes/tax.py:219`; `packages/api/src/zorivest_api/routes/tax.py:245`; `packages/api/src/zorivest_api/routes/tax.py:85` | Correct the plan to the implemented API, or add explicit backend/API correction tasks before GUI work. Tests must assert request shape, error behavior, and the four-quarter display strategy. | **resolved** — AC-154.13 corrected to 4 separate GET requests with `quarter`+`tax_year` params. AC-154.14 corrected to `POST /quarterly/payment` with `{ quarter, tax_year, payment_amount, confirm: true }`. Boundary contract updated. Task row 11 updated. |
| 4 | High | The plan cuts Lot Viewer close/reassign actions out of scope even though `06g` lists lot closing as an exit criterion and Wave 11 test IDs already include `tax-lot-close-btn` and `tax-lot-reassign-btn`. The open question asks whether to hide/disable these actions, but no Human-approved exception exists, so this is an unsourced scope narrowing. | `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:228`; `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:287`; `docs/build-plan/06g-gui-tax.md:467`; `ui/tests/e2e/test-ids.ts:268` | Include close/reassign UI tasks and tests, or mark the affected AC as blocked with explicit human approval and a follow-up task before plan approval. | **resolved** — Buttons rendered as **disabled** with tooltip "Coming soon — Module C4/C5". AC-154.7 updated. Out of Scope clarified (dialog/logic deferred, buttons present). Task row 7 updated. |
| 5 | Medium | The plan contains unresolved "User Review Required" and "Open Questions" sections while also presenting executable tasks. Several questions are already answered by local canon: Tax is specified as the top 6th nav item, not nested, and the shortcut is specified as `Ctrl+6`. Unresolved questions make the plan not execution-ready. | `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:39`; `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:285`; `docs/build-plan/06-gui.md:255` | Resolve each question in the plan with `Spec`, `Local Canon`, or `Human-approved` labels before execution. Remove questions that are answered by canonical docs. | **resolved** — "User Review Required" replaced with "Resolved Design Decisions" table (5 rows, all with `Spec`/`Research-backed`/`Local Canon` labels). "Open Questions" replaced with "Resolved Design Decisions (Post-Review)" back-reference. |
| 6 | Medium | The "Emerging Standards" source link is broken. The referenced path resolves to `docs/emerging-standards.md`, but `rg --files` found no such file. Since the plan cites it for G23/G14, those AC source labels are not auditable. | `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:28`; `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:296` | Replace the broken link with the actual canonical source, or cite `docs/build-plan/06-gui.md` for G23 with exact lines. | **resolved** — Both links (line 28 and Research References) corrected to `../../../../.agent/docs/emerging-standards.md`. Cross-doc sweep confirms 0 stale paths remain. |
| 7 | Medium | The plan uses incorrect build-priority matrix item numbers for MEU-155 and MEU-156. The plan labels MEU-155 as matrix item 82 and MEU-156 as 83, while the canonical matrix lists MEU-155 as 81a and MEU-156 as 82. | `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:155`; `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:200`; `docs/build-plan/build-priority-matrix.md:383`; `docs/build-plan/build-priority-matrix.md:384` | Correct the item numbers and update any downstream task references that rely on them. | **resolved** — MEU-155 corrected to 81a. MEU-156 corrected to 82. Spec Sources table updated to "81, 81a, 82". Cross-doc sweep confirms 0 references to matrix item 83. |
| 8 | Medium | The validation plan and task rows use non-P0 short commands such as raw `npx vitest run` and `npx tsc --noEmit`, and the BUILD_PLAN audit grep expects zero `tax-gui` matches even though the canonical slug is `gui-tax`. These validation cells are not exact enough to be run safely or to prove the intended matrix rows. | `docs/execution/plans/2026-05-14-tax-gui/task.md:32`; `docs/execution/plans/2026-05-14-tax-gui/task.md:53`; `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md:241`; `docs/BUILD_PLAN.md:670` | Rewrite validation cells with receipt-file commands and audit canonical MEU ids/slugs (`MEU-154`, `gui-tax`, `MEU-155`, `gui-calculator`, `MEU-156`, `tax-section-toggles`) instead of expecting zero matches. | **resolved** — Validation cells for tasks 5, 6, 7, 11, 23, 24, 25, 25a–25e, 28, 29 updated to P0-safe `*> C:\Temp\zorivest\...` redirect pattern. BUILD_PLAN audit grep corrected to canonical slugs. Verification Plan §5+§6 added. |

---

## Checklist Results

### Plan Review (PR)

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | `implementation-plan.md` defers E2E at line 232; `task.md` has no E2E implementation/build rows. |
| PR-2 Not-started confirmation | pass | `task.md` rows are unchecked; no correlated implementation handoff exists for this plan. |
| PR-3 Task contract completeness | partial | Rows have task/owner/deliverable/validation/status, but validation cells are not P0-safe exact commands. |
| PR-4 Validation realism | fail | No Playwright/build gate despite GUI shipping gate; stale BUILD_PLAN grep checks the wrong slug. |
| PR-5 Source-backed planning | fail | Broken source link for emerging standards; unsourced deferral of Lot Viewer actions and E2E. |
| PR-6 Handoff/corrections readiness | pass | Canonical review handoff path is established; fixes should route through `/plan-corrections`. |

### Docs Review (DR)

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | Plan claims settings persistence via existing API, but registry has no tax-profile keys and unknown keys are rejected. |
| DR-2 Residual old terms | fail | `tax-gui` audit expects zero matches while canonical build plan uses `gui-tax`. |
| DR-3 Downstream references updated | fail | Matrix item numbers drift from canonical build-priority matrix. |
| DR-4 Verification robustness | fail | Planned checks would miss route reachability, E2E Wave 11, and settings-key rejection. |
| DR-5 Evidence auditability | partial | Plan includes commands, but several are not exact receipt-file commands. |
| DR-6 Cross-reference integrity | fail | Quarterly endpoint contracts conflict between plan and implemented API. |
| DR-7 Evidence freshness | pass | Review used current file state and local `rg` receipts. |
| DR-8 Completion vs residual risk | fail | The plan contains unresolved open questions but is structured as execution-ready. |

---

## Verdict

`corrections_applied` — All 8 findings resolved. Plan and task files corrected. Ready for re-review.

**Correction summary:**
- 4 High findings: E2E scope restored (Wave 11), MEU-156 persistence blocked properly, quarterly endpoint/body fixed, lot actions rendered disabled
- 4 Medium findings: open questions resolved with source labels, link fixed, matrix items corrected, validation commands P0-safe
- 1 blocked item: `[B]` TaxProfile CRUD REST API (separate MEU)

---

## Follow-Up Actions

1. ~~Run `/plan-corrections` against `docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md` and `task.md`.~~ **Done.**
2. ~~Add E2E Wave 11 tasks and validation commands, or obtain explicit human-approved scope changes if E2E is intentionally deferred.~~ **Done — AC-154.18 + tasks 25a–25e.**
3. ~~Resolve MEU-156 persistence ownership: settings registry keys vs. tax profile API/repository.~~ **Done — Option A: blocked pending TaxProfile CRUD API.**
4. ~~Align Quarterly Tracker contracts with `packages/api/src/zorivest_api/routes/tax.py` or add backend correction tasks.~~ **Done — AC-154.13/14 + task 11 corrected.**
5. ~~Remove unresolved questions from the execution plan after each is resolved by `Spec`, `Local Canon`, or `Human-approved`.~~ **Done — all 3 resolved.**
6. **Next:** Submit for Codex re-review (`/plan-critical-review`) to confirm `approved` verdict.

---

## Recheck (2026-05-14)

**Review Mode**: `/plan-critical-review` recheck  
**Agent**: GPT-5.5 Codex  
**Verdict**: `changes_required`

### Commands Executed

| Command | Receipt |
|---|---|
| `rg -n "npx vitest run$|npx vitest run src|npx tsc --noEmit$|npm run build|playwright test|Select-Object|\*> C:\\Temp\\zorivest" docs/execution/plans/2026-05-14-tax-gui/task.md docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md` | `C:\Temp\zorivest\tax-gui-recheck-validation.txt` |
| `Test-Path .agent/context/handoffs/2026-05-14-tax-gui-handoff.md` plus targeted `rg` checks for corrected plan claims | `C:\Temp\zorivest\tax-gui-recheck-state.txt` |

### Prior Findings Recheck

| Prior Finding | Recheck Result | Evidence |
|---|---|---|
| 1. Missing Wave 11 E2E | resolved | `implementation-plan.md:286-287` includes `npm run build` and `npx playwright test tests/e2e/tax-*.test.ts`; `task.md:49-53` adds five Wave 11 E2E tasks. |
| 2. MEU-156 invalid settings persistence | resolved | `implementation-plan.md:212-224` marks TaxProfile persistence blocked and read-only; `task.md:44-45` includes read-only UI plus `[B]` backend follow-up. |
| 3. Quarterly endpoint/body mismatch | resolved | `implementation-plan.md:121` and `task.md:30` now use `POST /quarterly/payment` with `{ quarter, tax_year, payment_amount, confirm: true }`. |
| 4. Lot close/reassign unsourced deferral | resolved | `task.md:26` requires disabled Close/Reassign buttons with tooltip. |
| 5. Unresolved open questions | resolved | `implementation-plan.md:39` adds resolved decisions and `implementation-plan.md:309` closes the old open-question section. |
| 6. Broken emerging standards link | resolved | `implementation-plan.md:28` and `implementation-plan.md:320` point to `../../../../.agent/docs/emerging-standards.md`. |
| 7. Matrix item drift | resolved | `implementation-plan.md:164` uses MEU-155 item `81a`; `implementation-plan.md:209` uses MEU-156 item `82`. |
| 8. Unsafe validation commands / stale audit grep | partially resolved | BUILD_PLAN audit and the main Verification Plan are corrected, but multiple `task.md` validation cells still contain raw unredirected commands. |

### Findings

| # | Severity | Finding | File:Line | Recommendation |
|---|----------|---------|-----------|----------------|
| R1 | High | Several `task.md` validation cells still contain raw commands such as `npx vitest run`, `npx tsc --noEmit`, and `Select-String ...` without the mandatory receipt-file redirect pattern. The previous finding required validation cells to be P0-safe, and Zorivest's P0 rules make this non-negotiable for commands that implementers may copy during execution. | `docs/execution/plans/2026-05-14-tax-gui/task.md:20-23`; `docs/execution/plans/2026-05-14-tax-gui/task.md:28-42`; `docs/execution/plans/2026-05-14-tax-gui/task.md:54`; `docs/execution/plans/2026-05-14-tax-gui/task.md:57` | Rewrite every remaining shell validation cell to use the `*> C:\Temp\zorivest\...; Get-Content ...` receipt pattern, or replace per-row commands with exact references to the P0-safe Verification Plan only where that still proves the row's deliverable. |

### Checklist Results

| Check | Result | Evidence |
|---|---|---|
| PR-1 Plan/task alignment | pass | MEU order and corrected scope match between plan and task table. |
| PR-2 Not-started confirmation | pass | `.agent/context/handoffs/2026-05-14-tax-gui-handoff.md` does not exist; task rows remain unchecked/blocked only. |
| PR-3 Task contract completeness | partial | Rows have task/owner/deliverable/validation/status, but some validation cells remain unsafe. |
| PR-4 Validation realism | fail | The full Verification Plan is P0-safe, but task-level validation commands are still copyable unsafe commands. |
| PR-5 Source-backed planning | pass | Corrected decisions are labeled to `Spec`, `Local Canon`, or `Research-backed` sources. |
| PR-6 Handoff/corrections readiness | pass | Canonical rolling review file updated; remaining fix belongs in `/plan-corrections`. |

### Verdict

`changes_required` — the substantive product-contract findings are resolved, including E2E Wave 11, TaxProfile persistence blocking, quarterly API alignment, lot action treatment, source links, and matrix references. One P0 validation-contract issue remains in `task.md`, so the plan should not be approved until every task validation command is receipt-file safe.

---

## Corrections Applied — Recheck R1 (2026-05-14)

**Finding R1 — resolved.** All 20 remaining bare validation cells in `task.md` converted to P0-safe receipt-file redirect pattern.

### Changes Made

| File | Lines Changed | Description |
|------|---------------|-------------|
| `task.md` | 20–23 | Rows 1–4 (MEU-154): `npx vitest run` / `npx tsc --noEmit` → P0-safe `vitest-tax.txt` / `tsc-tax.txt` |
| `task.md` | 27–29 | Rows 8–10 (MEU-154): `npx vitest run` → P0-safe `vitest-tax.txt` |
| `task.md` | 31–32 | Rows 12–13 (MEU-154): bare vitest → P0-safe `vitest-tax.txt` / `vitest-tax-tests.txt` |
| `task.md` | 34–42 | Rows 14–22 (MEU-155): `npx vitest run` → P0-safe `vitest-calc.txt` / `vitest-calc-tests.txt` |
| `task.md` | 55 | Row 26 (re-anchor): `Select-String` → P0-safe `reanchor.txt` |
| `task.md` | 59 | Row 27 (re-anchor): `Select-String` → P0-safe `reanchor.txt` |

### Verification

```
rg -n "``npx vitest run``|``npx tsc --noEmit``" task.md → 0 matches ✅
All 35 task rows now use receipt-file redirect or non-shell validation (MCP, view_file, §reference)
```

### Status

`corrections_applied` — All original 8 findings + recheck R1 resolved. Ready for re-review.

---

## Recheck Approval (2026-05-14)

**Review Mode**: `/plan-critical-review` recheck  
**Agent**: GPT-5.5 Codex  
**Verdict**: `approved`

### Commands Executed

| Command | Receipt |
|---|---|
| `Test-Path .agent/context/handoffs/2026-05-14-tax-gui-handoff.md` plus validation-command sweep for `npx`, `npm`, `playwright`, `Select-String`, and receipt redirects | `C:\Temp\zorivest\tax-gui-recheck2-validation-sweep.txt` |
| `rg -n -P "(npx vitest run|npx tsc --noEmit|npx playwright test|npm run build|Select-String)(?!.*\*> C:\\Temp\\zorivest)" docs/execution/plans/2026-05-14-tax-gui/task.md docs/execution/plans/2026-05-14-tax-gui/implementation-plan.md` | `C:\Temp\zorivest\tax-gui-recheck2-negative-sweep.txt` |
| `rg -n "AC-154.18|Wave 11|TaxProfile CRUD|quarterly/payment|section_475_elected|section_1256_eligible|forex_worksheet|Resolved Design Decisions|gui-calculator|tax-section-toggles" ...` | `C:\Temp\zorivest\tax-gui-recheck2-contract-sweep.txt` |

### Findings

None.

### Prior Findings Recheck

| Finding | Result | Evidence |
|---|---|---|
| Original findings 1-7 | resolved | Contract sweep confirms Wave 11 E2E/build coverage, TaxProfile persistence blocked/read-only, quarterly payment endpoint/body alignment, resolved design decisions, source-backed Section fields, and corrected matrix slugs/items. |
| Original finding 8 / recheck R1 | resolved | `tax-gui-recheck2-negative-sweep.txt` returned `NO_UNSAFE_VALIDATION_COMMANDS_FOUND`. All `task.md` shell validation cells with `npx`, `npm`, `playwright`, or `Select-String` now include `*> C:\Temp\zorivest\...` receipt redirects. |

### Checklist Results

| Check | Result | Evidence |
|---|---|---|
| PR-1 Plan/task alignment | pass | `implementation-plan.md` and `task.md` now describe the same MEU order, deliverables, blocked TaxProfile persistence, and Wave 11 E2E scope. |
| PR-2 Not-started confirmation | pass | `Test-Path .agent/context/handoffs/2026-05-14-tax-gui-handoff.md` returned `False`; task rows remain unchecked except the intentional `[B]` follow-up. |
| PR-3 Task contract completeness | pass | Every task row has task, owner, deliverable, validation, and status. |
| PR-4 Validation realism | pass | Task-level commands and the full Verification Plan are receipt-file safe; E2E includes build before Wave 11. |
| PR-5 Source-backed planning | pass | Resolved decisions and acceptance criteria cite `Spec`, `Local Canon`, or `Research-backed` sources. |
| PR-6 Handoff/corrections readiness | pass | One rolling review file maintained; no product or plan files modified during this recheck. |

### Verdict

`approved` — all original findings and recheck R1 are resolved. The plan is ready for the next human-approved workflow step.
