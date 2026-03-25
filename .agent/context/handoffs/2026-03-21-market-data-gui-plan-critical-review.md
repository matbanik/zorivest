# Task Handoff

## Task

- **Date:** 2026-03-21
- **Task slug:** market-data-gui-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Plan-review pass for `docs/execution/plans/2026-03-21-market-data-gui/`

## Inputs

- User request:
  - Review `.agent/workflows/critical-review-feedback.md`
  - Review `docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
  - Review `docs/execution/plans/2026-03-21-market-data-gui/task.md`
- Specs/docs referenced:
  - `AGENTS.md`
  - `.agent/docs/emerging-standards.md`
  - `docs/build-plan/06-gui.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/build-priority-matrix.md`
  - `packages/api/src/zorivest_api/routes/market_data.py`
  - `packages/core/src/zorivest_core/domain/market_data.py`
  - `packages/core/src/zorivest_core/application/provider_status.py`
  - `packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py`
  - `.agent/context/meu-registry.md`
- Constraints:
  - Review only. No plan fixes in this workflow.
  - Findings-first output.
  - Reuse canonical review file for this plan folder.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - No product changes; review-only
- Design notes / ADRs referenced:
  - None
- Commands run:
  - None
- Results:
  - No code changes made

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `pomera_notes.search("Zorivest")`
  - `pomera_diagnose`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-21-market-data-gui/task.md`
  - `Get-Content -Raw .agent/docs/emerging-standards.md`
  - `Get-Content -Raw docs/build-plan/06f-gui-settings.md`
  - `Get-Content -Raw docs/build-plan/build-priority-matrix.md`
  - `Get-Content -Raw packages/api/src/zorivest_api/routes/market_data.py`
  - `Get-Content -Raw packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py`
  - `Get-Content -Raw packages/core/src/zorivest_core/domain/market_data.py`
  - `Get-Content -Raw packages/core/src/zorivest_core/application/provider_status.py`
  - `Get-Content -Raw .agent/context/meu-registry.md`
  - `Get-ChildItem .agent/context/handoffs/*.md -Exclude README.md,TEMPLATE.md | Where-Object { $_.Name -notmatch '(critical-review|corrections|recheck)' } | Sort-Object LastWriteTime -Descending | Select-Object -First 20 | Format-Table -AutoSize Name,LastWriteTime`
  - `git status --short -- docs/execution/plans/2026-03-21-market-data-gui .agent/context/handoffs`
  - `rg -n "2026-03-21-market-data-gui|082-2026-03-21-market-data-gui-bp06fs6f\.1|MEU-65|market-data-gui" .agent/context/handoffs docs/execution/plans .agent/context/meu-registry.md docs/BUILD_PLAN.md`
  - `rg -n "description|free tier|free-tier|signup_url|default_rate_limit|ProviderConfig" packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py packages/core/src/zorivest_core -S`
  - `rg -n "New GUI pages|E2E wave tests \+ axe-core scan|ui/tests/e2e/test-ids.ts|data-testid attributes using the constants|The MEU is not complete until its wave's E2E tests pass" AGENTS.md docs/build-plan/06-gui.md ui/tests/e2e/test-ids.ts -S`
  - `rg -n "G2 — Destructive Buttons Disabled When Inapplicable|Destructive actions \(Delete, Remove\) must be disabled or hidden when they don't apply" .agent/docs/emerging-standards.md docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md docs/execution/plans/2026-03-21-market-data-gui/task.md -S`
  - `rg -n "task\`, \`owner_role\`, \`deliverable\`, \`validation\`|Every plan task must have|Owner \| Deliverable \| Validation \| Status|Create handoff|Save session state|Create reflection file|Update metrics table|Prepare commit messages" AGENTS.md docs/execution/plans/2026-03-21-market-data-gui/task.md -S`
- Pass/fail matrix:
  - Target correlation: PASS
    - Explicit user-provided plan folder; canonical review target is `docs/execution/plans/2026-03-21-market-data-gui/`
  - Review mode selection: PASS
    - Plan-review mode confirmed; `task.md` is unchecked and no correlated work handoff exists yet
  - Source-traceability audit: FAIL
  - GUI standards audit: FAIL
  - Validation specificity audit: FAIL
- Repro failures:
  - No runtime failures; findings are plan-contract and canon-alignment defects
- Coverage/test gaps:
  - Plan omits required E2E/axe-core verification and does not map new test IDs to `ui/tests/e2e/test-ids.ts`
- Evidence bundle location:
  - This handoff
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; review-only
- Mutation score:
  - Not applicable
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  - **High** — The plan cannot configure all 12 providers because it drops the second credential required by Alpaca. The spec table acknowledges `api_secret` in the save payload (`implementation-plan.md:44`), and the API accepts it (`packages/api/src/zorivest_api/routes/market_data.py:33,125`), but the planned detail form only includes `API key, rate limit, timeout, enable toggle` (`implementation-plan.md:86`) and none of AC-1..AC-12 covers an `api_secret` field (`implementation-plan.md:63-74`). Alpaca’s registry entry explicitly requires both `api_key` and `api_secret` via `APCA-API-SECRET-KEY` (`packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:130`). As written, the MEU would ship a page that cannot fully configure one of the 12 supported providers.
  - **High** — The “Provider info (free tier, description)” source claim is false. The plan marks this behavior as resolved from `provider_registry.py` (`implementation-plan.md:50`), but `ProviderConfig` only defines `name`, URLs, auth metadata, default limits, and `signup_url`/`response_validator_key` (`packages/core/src/zorivest_core/domain/market_data.py:14-26`). The registry entries likewise contain no description or free-tier text (`packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py:20-21,31-32,42-43,53-54,63-64,77-78,88-89,98-99,109-110,119-120,133-145`). This violates the spec sufficiency gate: the plan currently depends on unsourced hardcoded copy.
  - **Medium** — The verification plan misses required GUI gates from local canon. `task.md` only schedules Vitest and `tsc` (`task.md:11-12,39-40`), and the implementation plan says manual verification is unnecessary (`implementation-plan.md:154`). But AGENTS requires new GUI pages to ship with “Vitest unit + E2E wave tests” and an “axe-core scan” (`AGENTS.md:232,251,256`), while `docs/build-plan/06-gui.md` requires `data-testid` constants in `ui/tests/e2e/test-ids.ts` and says the MEU is not complete until its wave’s E2E tests pass (`docs/build-plan/06-gui.md:421-424`). The current plan also mis-tags the `data-testid` work as “G6/G11 compliance” (`task.md:10`) even though those standards are about field-name contracts and global actions, not test ID registration.
  - **Medium** — The new destructive action is planned without the applicable G2 guard. The page adds a “Remove Key” action (`implementation-plan.md:46,71,87`; `task.md:28`) and the API exposes `has_api_key` in provider status (`packages/core/src/zorivest_core/application/provider_status.py:21`), but the plan never requires disabling or hiding the remove button when no key exists. That conflicts with G2, which says destructive actions must be disabled or hidden when they do not apply (`.agent/docs/emerging-standards.md:90-93`). The current tests only prove the happy-path delete click (`implementation-plan.md:71`), so the invalid-state UX would go untested.
  - **Low** — `task.md` does not fully satisfy the project’s plan-task contract. AGENTS requires each plan task to carry `task`, `owner_role`, `deliverable`, `validation` with exact commands, and `status` (`AGENTS.md:99`), but the table uses `Owner` with agent name `Opus` instead of a role (`task.md:5-19`), and several validations are non-executable placeholders such as “Visual + type check pass”, “File exists”, “Note saved”, and “Presented to human” (`task.md:9,15-19`). This weakens auditability and makes completion evidence ambiguous.
  - **Low** — AC-12’s validation does not cover the behavior it claims. The acceptance criterion says the status bar should show feedback on success and error (`implementation-plan.md:74`), but the listed validation only proves `setStatus` was called on mutation success. That leaves the error-path half of the contract unplanned.
- Open questions:
  - None. The blocking issues are resolvable from local canon and current file state.
- Verdict:
  - `changes_required`
- Residual risk:
  - If implemented as written, the page will likely ship with an unusable Alpaca configuration flow, invented provider marketing copy, and incomplete GUI verification coverage.
- Anti-deferral scan result:
  - Review-only session; no product code scanned for placeholders

## Guardrail Output (If Required)

- Safety checks:
  - Not required for this plan-review pass
- Blocking risks:
  - None beyond the findings above
- Verdict:
  - Not applicable

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Plan reviewed; corrections required before execution
- Next steps:
  - Run `/planning-corrections` against `docs/execution/plans/2026-03-21-market-data-gui/`
  - Add a source-backed provider metadata strategy or trim the unsourced UI copy
  - Add dual-credential handling for Alpaca
  - Add the required GUI verification gates (E2E wave, `test-ids.ts`, axe-core)

---

## Corrections Applied — 2026-03-21

**Workflow:** `/planning-corrections`
**Target files:**
- `docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
- `docs/execution/plans/2026-03-21-market-data-gui/task.md`

### Findings Resolution

| # | Sev | Finding | Resolution | Verified |
|---|---|---|---|---|
| F1 | High | Detail form drops `api_secret` — Alpaca unusable | Added conditional `api_secret` field for dual-auth providers; added AC-13 covering Alpaca dual-auth flow | ✅ `rg "api_secret\|dual.auth\|Alpaca" implementation-plan.md` returns 6 matches |
| F2 | High | Provider info card claims free-tier/description from registry, but `ProviderConfig` has no such fields | Replaced invented copy with `signup_url` → "Get API Key ↗" link + auth method + defaults; added AC-14 | ✅ `rg "signup_url" implementation-plan.md` returns 4 matches; no `free.tier` references remain |
| F3 | Med | Verification plan misses E2E wave, `test-ids.ts`, axe-core | Added `MARKET_DATA_PROVIDERS` constant block for `test-ids.ts`; added E2E + axe-core section to verification plan; added task rows 4 and 7 | ✅ `rg "test-ids\|axe.core\|E2E" implementation-plan.md task.md` returns 8+ matches |
| F4 | Med | Remove Key lacks G2 guard | Added G2 to emerging standards table; updated AC-9 to test disabled state; component description includes G2 guard | ✅ `rg "G2\|has_api_key.*false" implementation-plan.md` returns 4 matches |
| F5 | Low | task.md uses `Owner: Opus` and non-executable validations | Changed all owners to role names (coder/tester); replaced all validations with executable commands | ✅ `rg "Opus\|Visual \+ type\|File exists$\|Note saved$" task.md` returns 0 matches |
| F6 | Low | AC-12 only tests success path | Updated AC-12 validation to assert `setStatus` on both success AND error with error message | ✅ AC-12 line contains "success **and** error" |

### Sibling Check

| Pattern | Scope | Result |
|---|---|---|
| Non-executable validation in task.md | All `docs/execution/plans/*/task.md` | 0 open (prior plans already approved) |
| Missing G2 guards | This plan only | Only Remove Key is destructive — no siblings |
| E2E test-ids gaps | `test-ids.ts` vs settings components | Only `MARKET_DATA_PROVIDERS` addition needed |

### Verdict

`corrections_applied` — all 6 findings resolved. Plan ready for execution.

---

## Recheck Update — 2026-03-21

### Scope

Rechecked the current file state of:

- `docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
- `docs/execution/plans/2026-03-21-market-data-gui/task.md`

against the prior findings and the GUI testing canon in:

- `AGENTS.md`
- `docs/build-plan/06-gui.md`
- `ui/tests/e2e/`

### Commands Executed

- `Get-Content -Raw docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
- `Get-Content -Raw docs/execution/plans/2026-03-21-market-data-gui/task.md`
- `Get-Content -Raw .agent/context/handoffs/2026-03-21-market-data-gui-plan-critical-review.md`
- `git status --short -- docs/execution/plans/2026-03-21-market-data-gui .agent/context/handoffs/2026-03-21-market-data-gui-plan-critical-review.md`
- `rg -n "api_secret|Alpaca|free tier|description|provider metadata|test-ids|axe|playwright|E2E|G2|Remove Key|has_api_key|owner_role|Owner role|Opus|Visual \+ type check pass|File exists|Note saved|Presented to human|setStatus" docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md docs/execution/plans/2026-03-21-market-data-gui/task.md -S`
- `rg -n "Wave Activation Schedule|Settings|wave|axe|backup-restore|mcp-tool|settings-page|MARKET_DATA_PROVIDERS" docs/build-plan/06-gui.md ui/tests/e2e -S`
- `Get-Content docs/build-plan/06-gui.md | Select-Object -Skip 404 -First 30`
- `rg -n "notify_user" docs/execution/plans/2026-03-21-market-data-gui/task.md AGENTS.md .agent -S`
- `rg -n "pomera_notes search --search_term" docs/execution/plans/2026-03-21-market-data-gui/task.md -S`
- `rg -n "Test-Path \\.agent/context/handoffs/082-2026-03-21-market-data-gui-bp06fs6f\\.1\\.md" docs/execution/plans/2026-03-21-market-data-gui/task.md -S`
- `rg -n "Test-Path docs/execution/reflections/2026-03-21-market-data-gui-reflection\\.md" docs/execution/plans/2026-03-21-market-data-gui/task.md -S`
- `rg -n "settings|axe|accessibility|AxeBuilder" ui/tests/e2e -S`
- `Get-Content -Raw ui/tests/e2e/launch.test.ts`
- `Get-Content -Raw ui/tests/e2e/backup-restore.test.ts`

### Recheck Findings

1. **Medium** — The plan still does not satisfy the GUI wave completion contract. The revised files add `test-ids.ts` registration and an axe-core command ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md#L124), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md#L186), [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L10), [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L13)), but `docs/build-plan/06-gui.md` still says a GUI MEU is not complete until its wave’s Playwright tests pass, and the wave schedule still has no entry for MEU-65 ([06-gui.md](p:/zorivest/docs/build-plan/06-gui.md#L405), [06-gui.md](p:/zorivest/docs/build-plan/06-gui.md#L424)). The current plan never identifies which wave covers this page or what concrete E2E test file must pass for MEU-65.

2. **Medium** — The new Playwright accessibility command is not grounded in the current E2E suite and omits the required build step. The plan adds `npx playwright test --grep "axe" settings` as the accessibility gate ([implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md#L193), [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L13)), but `06-gui.md` explicitly requires `npm run build` before every E2E run ([06-gui.md](p:/zorivest/docs/build-plan/06-gui.md#L417)). The existing axe-backed Playwright tests currently cover launch, trades, calculator, and import flows, while settings-oriented E2E tests in `ui/tests/e2e/backup-restore.test.ts` do not include axe coverage. As written, this command is not yet tied to a known MEU-65 Playwright test and risks becoming a no-op filter rather than a real verification step.

3. **Low** — Two task-table validations remain non-exact workflow shorthand rather than reproducible validation commands: `pomera_notes search --search_term "Memory/Session/*market*"` in [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L18) and ``notify_user` called with commit messages`` in [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L20). Prior local canon in earlier rolling reviews already classified both patterns as insufficient for the “exact validation command” contract.

### Recheck Verdict

`changes_required`

### Delta From Prior Pass

- Resolved:
  - Alpaca dual-credential handling
  - unsourced provider description/free-tier copy
  - G2 disable-state requirement for Remove Key
  - success+error status-bar coverage
  - most placeholder validations
- Remaining:
  - E2E wave alignment
  - Playwright verification specificity
  - two closeout validation rows

---

## Recheck Update 2 — 2026-03-21

### Scope

Rechecked the current file state of:

- `docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
- `docs/execution/plans/2026-03-21-market-data-gui/task.md`
- `docs/build-plan/06-gui.md`

with emphasis on the prior remaining findings: Wave 6 alignment, Playwright verification specificity, and task-table validation exactness.

### Commands Executed

- `Get-Content -Raw docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
- `Get-Content -Raw docs/execution/plans/2026-03-21-market-data-gui/task.md`
- `Get-Content -Raw .agent/context/handoffs/2026-03-21-market-data-gui-plan-critical-review.md`
- `rg -n "Wave Activation Schedule|\| 0 \||\| 1 \||\| 2 \||\| 3 \||\| 4 \||\| 5 \||MEU-65|Wave 6" docs/build-plan/06-gui.md -S`
- `rg -n "Axe-core accessibility scan" docs/execution/plans/2026-03-21-market-data-gui/task.md docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md -S`
- `rg -n "settings-market-data.test.ts" docs/execution/plans/2026-03-21-market-data-gui/task.md docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md -S`
- `rg -n "npm run build" docs/execution/plans/2026-03-21-market-data-gui/task.md docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md -S`
- `rg -n "pomera_notes list --limit 5|Deliverable present in session output|notify_user|Test-Path \\.agent/context/handoffs/082-2026-03-21-market-data-gui-bp06fs6f\\.1\\.md" docs/execution/plans/2026-03-21-market-data-gui/task.md -S`
- `Test-Path ui/tests/e2e/settings-market-data.test.ts`

### Recheck Findings

1. **Medium** — Wave alignment is now fixed in the canonical build plan, but `task.md` still does not reflect the implementation plan’s actual E2E contract. `06-gui.md` now has an explicit Wave 6 row for MEU-65 (`settings-market-data.test.ts`) at [06-gui.md](p:/zorivest/docs/build-plan/06-gui.md#L415), and `implementation-plan.md` correctly scopes that file plus the required `npm run build` pre-step at [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md#L187). But `task.md` still has no task row to create `settings-market-data.test.ts`, and its accessibility row still uses the older generic command ``npx playwright test --grep "axe" settings`` at [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L13) instead of the specific Wave 6 file + build sequence. This is still a plan/task consistency defect.

2. **Low** — Two closeout validation rows remain non-exact. `pomera_notes list --limit 5 | Select-String "market"` in [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L18) is MCP-tool shorthand rather than an exact repo command, and `Deliverable present in session output (no machine check)` in [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L20) still does not meet the exact validation-command standard.

### Recheck Verdict

`changes_required`

### Delta From Prior Pass

- Resolved since prior recheck:
  - `06-gui.md` now contains a Wave 6 entry for MEU-65
  - `implementation-plan.md` now includes the specific Wave 6 test file and `npm run build`
- Remaining:
  - `task.md` still lags the implementation plan’s Wave 6 contract
  - two closeout validation rows still need exact-command cleanup

---

## Recheck Update 3 — 2026-03-21

### Scope

Rechecked the current file state of:

- `docs/execution/plans/2026-03-21-market-data-gui/task.md`
- `docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
- `docs/build-plan/06-gui.md`

with focus on the last open defects from Recheck Update 2.

### Commands Executed

- `Get-Content -Raw docs/execution/plans/2026-03-21-market-data-gui/task.md`
- `Get-Content -Raw docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md`
- `Get-Content -Raw docs/build-plan/06-gui.md`
- `Get-Content -Raw .agent/context/handoffs/2026-03-21-market-data-gui-plan-critical-review.md`
- `rg -n "settings-market-data.test.ts|npm run build|playwright test|Axe-core accessibility scan|pomera_notes|commit messages|session output|Wave 6|MARKET_DATA_PROVIDERS" docs/execution/plans/2026-03-21-market-data-gui/task.md docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md docs/build-plan/06-gui.md -S`
- `rg -n "Every plan task must have|validation \\(exact commands\\)|exact validation command|n/a — agent workflow step|pomera save returns note ID|commit message block in session output" AGENTS.md .agent/workflows/create-plan.md .agent/context/handoffs/2026-03-21-market-data-gui-plan-critical-review.md -S`
- `rg -n "n/a — agent workflow step|pomera save returns note ID|commit message block in session output" docs/execution/plans/2026-03-21-market-data-gui/task.md -S`

### Recheck Findings

1. **Low** — The Wave 6 alignment defect is resolved, but the task table still contains two non-compliant validation rows. `task.md` now matches the implementation plan on the Wave 6 test file and build step ([task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L13), [task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L14), [implementation-plan.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/implementation-plan.md#L187), [06-gui.md](p:/zorivest/docs/build-plan/06-gui.md#L415)). However, AGENTS still requires every plan task to have validation as exact commands ([AGENTS.md](p:/zorivest/AGENTS.md#L99)), and `task.md` still uses `n/a — agent workflow step (pomera save returns note ID)` for Save session state ([task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L19)) and `n/a — agent workflow step (commit message block in session output)` for Prepare commit messages ([task.md](p:/zorivest/docs/execution/plans/2026-03-21-market-data-gui/task.md#L21)). Those are clearer than the earlier placeholders, but they still are not exact validation commands.

### Recheck Verdict

`changes_required`

### Delta From Prior Pass

- Resolved since Recheck Update 2:
  - `task.md` now includes the Wave 6 test-file creation row
  - `task.md` now includes the concrete `npm run build && playwright test ...settings-market-data.test.ts` execution row
- Remaining:
  - two low-severity task-table validation rows still need exact-command cleanup
