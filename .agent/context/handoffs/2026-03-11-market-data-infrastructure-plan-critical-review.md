# Task Handoff

## Task

- **Date:** 2026-03-11
- **Task slug:** market-data-infrastructure-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Critical review of the unstarted execution plan in `docs/execution/plans/2026-03-11-market-data-infrastructure/` using `.agent/workflows/critical-review-feedback.md`, current Phase 8 specs, and current repo state

## Inputs

- User request:
  Review `.agent/workflows/critical-review-feedback.md`, `docs/execution/plans/2026-03-11-market-data-infrastructure/implementation-plan.md`, and `docs/execution/plans/2026-03-11-market-data-infrastructure/task.md`.
- Specs/docs referenced:
  `SOUL.md`; `GEMINI.md`; `AGENTS.md`; `.agent/context/current-focus.md`; `.agent/context/known-issues.md`; `docs/build-plan/08-market-data.md`; `docs/build-plan/06f-gui-settings.md`; `docs/BUILD_PLAN.md`; `.agent/context/meu-registry.md`; `packages/core/src/zorivest_core/application/ports.py`; `packages/infrastructure/src/zorivest_infra/security/api_key_encryption.py`; `packages/infrastructure/src/zorivest_infra/database/models.py`; `.agent/context/handoffs/2026-03-11-market-data-foundation-plan-critical-review.md`; `.agent/context/handoffs/2026-03-11-market-data-foundation-implementation-critical-review.md`
- Constraints:
  Review-only workflow. No product fixes in this pass.

## Role Plan

1. orchestrator — confirm plan-review scope, read required session context, and identify the canonical spec set for MEU-59/60/62
2. tester — inspect plan/task/spec/code artifacts and repo status for contract drift
3. reviewer — produce findings-first verdict and concrete planning corrections
- Optional roles: none

## Coder Output

- Changed files:
  Review-only. No product changes.
- Design notes / ADRs referenced:
  None beyond cited build-plan sections.
- Commands run:
  None.
- Results:
  None.

## Tester Output

- Commands run:
  - MCP/session preflight:
    - `pomera_diagnose`
    - `pomera_notes search "Zorivest"`
    - `get_text_file_contents` for `SOUL.md`, `GEMINI.md`, `.agent/context/current-focus.md`, `.agent/context/known-issues.md`, `.agent/workflows/critical-review-feedback.md`, the target plan/task files, and referenced spec/code files
  - Repo/state inspection:
    - `rg --files ... | rg "market-data|08-market-data|TEMPLATE|critical-review|implementation-critical-review|plan-critical-review"`
    - `rg -n "ProviderConnectionService|ProviderStatus|list_providers|configure_provider|test_connection|remove_api_key|rate_limiters|MarketProviderSettingModel|UnitOfWork" packages tests docs/build-plan/08-market-data.md`
    - numbered line inspections for the target plan, `08-market-data.md`, `06f-gui-settings.md`, `ports.py`, `BUILD_PLAN.md`, and `.agent/context/meu-registry.md`
- Pass/fail matrix:
  - Review mode: `plan review` confirmed. The target folder has no correlated implementation handoffs yet and all task checklist items remain unchecked.
  - Session preflight / MCP availability: PASS (`pomera`, `text-editor`, `sequential-thinking` available; `pomera_diagnose` healthy)
  - Plan/task/spec alignment: FAIL
  - Repo-state / hub-update math: FAIL
  - Workflow contract compliance for task validations: FAIL
- Repro failures:
  - None executed; this was a pre-implementation review pass.
- Coverage/test gaps:
  - No tests were run because the target is an unstarted plan. Findings are based on spec, repo-contract, and cross-file consistency review.
- Evidence bundle location:
  - This handoff.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - N/A — no implementation under review.
- Mutation score:
  - Not run.
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  1. **High** — The plan is not executable against the current persistence contract because `ProviderConnectionService` is supposed to persist `MarketProviderSettingModel` through `uow`, but the existing `UnitOfWork` protocol has no repository or attribute for market-provider settings. The plan marks persistence as already resolved in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:90) and [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:131), and proposes a service that depends on `uow` in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:209), but the current `UnitOfWork` only exposes `trades`, `images`, `accounts`, `balance_snapshots`, `round_trips`, `settings`, and `app_defaults` in [ports.py](P:\zorivest\packages\core\src\zorivest_core\application\ports.py:142). There is no planned task to add a market-provider repository, extend the `UnitOfWork` contract, or wire the concrete infra implementation. As written, the coder would have to either violate the repo’s existing service/UoW pattern or do unplanned architecture work.
  2. **High** — The `configure_provider` contract in the plan is narrower than the Phase 8 API contract it is supposed to underpin. The plan resolves and tests `configure_provider(name, api_key, api_secret?, rate_limit?, timeout?)` in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:82), [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:131), and [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:217), but the canonical REST contract says omitted fields are allowed, `api_key` is optional, and `is_enabled` must also flow through the service in [08-market-data.md](P:\zorivest\docs\build-plan\08-market-data.md:529) and [08-market-data.md](P:\zorivest\docs\build-plan\08-market-data.md:554). If implemented as planned, later MEU-63/65 work will immediately need to reopen MEU-60 just to support the published PATCH semantics and enable/disable toggles.
  3. **High** — The connection-test acceptance criteria flatten the provider-specific validation rules into a generic `response_validator_key` check, which does not match the actual spec and will miss valid success cases. The plan’s AC-4 says success is HTTP 200 with JSON matching a provider’s single `response_validator_key` in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:133), and the planned tests only include one generic success case plus the FMP legacy exception in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:220). The real Phase 8 table has multiple provider-specific branches: Alpha Vantage accepts `"Global Quote"` or `"Time Series"`, Polygon accepts `"results"` or `"status"`, Nasdaq requires nested `datatable.data`, SEC API expects a list-of-dicts shape, API Ninjas requires both `price` and `name`, and Benzinga accepts either a list or `data` array in [08-market-data.md](P:\zorivest\docs\build-plan\08-market-data.md:671). The current plan would green-light an implementation that can still reject valid credentials for several providers.
  4. **Medium** — `list_providers()` is under-specified as `list[dict]`, but downstream specs already depend on a stable `ProviderStatus` shape. The plan resolves `list_providers() -> list[dict]` in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:81), and its tests only promise the “correct shape” in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:216). But the concurrency section explicitly says `list_providers()` returns `ProviderStatus` in [08-market-data.md](P:\zorivest\docs\build-plan\08-market-data.md:705), and the GUI contract already fixes the required fields as `provider_name`, `is_enabled`, `has_api_key`, `rate_limit`, `timeout`, and `last_test_status` in [06f-gui-settings.md](P:\zorivest\docs\build-plan\06f-gui-settings.md:65). The plan needs either a concrete Python status model/typed dict contract or much tighter AC/test coverage so this interface does not drift before the outer layers consume it.
  5. **Medium** — The planned `BUILD_PLAN.md` total-count update is mathematically inconsistent with the repo state it claims to fix. The plan says the hub update will set Phase 8 completed to `6 total` and overall completed to `48` in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:240). But the same note says the stale Phase 5 summary (`1`) will be corrected to `12` in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:243), while `BUILD_PLAN.md` currently shows Phase 8 with 3 completed rows already present in [BUILD_PLAN.md](P:\zorivest\docs\BUILD_PLAN.md:233) and summary counts of Phase 5=`1`, Phase 8=`0`, Total=`22` in [BUILD_PLAN.md](P:\zorivest\docs\BUILD_PLAN.md:459). If this project also flips MEU-59/60/62 to `✅`, the corrected total becomes `51`, not `48` (`45` approved P0 MEUs per `.agent/context/meu-registry.md:101` plus `6` Phase 8 MEUs). The hub-update instructions are therefore internally wrong before coding even starts.
  6. **Medium** — The task table still violates the repo’s planning contract for exact validations. The project rules require every task to include a concrete validation command, but several rows use non-executable placeholders such as `Follows TEMPLATE.md`, `Verify row statuses match summary table counts`, `Rows present with ✅ status`, `File exists with lessons learned`, `Note saved`, and `Presented to human` in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:260). That makes the plan weaker as an execution artifact because completion for those rows cannot be objectively reproduced from the plan alone.
  7. **Low** — The plan drifts from the spec’s module location for the market-data redaction utility. Phase 8 places the utility in `packages/infrastructure/src/zorivest_infra/security/log_redaction.py` in [08-market-data.md](P:\zorivest\docs\build-plan\08-market-data.md:356), while the plan moves it to `packages/infrastructure/src/zorivest_infra/market_data/log_redaction.py` in [implementation-plan.md](P:\zorivest\docs\execution\plans\2026-03-11-market-data-infrastructure\implementation-plan.md:183). Because the same plan already notes this logic is part of the broader security/logging policy, this relocation should be deliberate and source-backed if it is kept; otherwise it creates avoidable path drift before the code exists.
- Open questions:
  - Should the planning correction fold `MarketProviderSettingsRepository` plus `UnitOfWork` / concrete infra wiring into this project, or is there an existing sanctioned pattern for Phase 8 services to bypass the repository contract?
  - Does the team want a dedicated Python `ProviderStatus` model in this project, or a narrower typed-dict/DTO contract that still matches the `06f` GUI fields exactly?
- Verdict:
  - `changes_required`
- Residual risk:
  - The plan has the right project slice, but the current service contract and validation design are not stable enough to start TDD cleanly. If implementation begins as written, the most likely outcome is immediate mid-project scope expansion into ports/UoW work plus rework when MEU-63/65 consume the service.
- Anti-deferral scan result:
  - Mixed. There are no placeholder product stubs yet because this is a plan review, but several task validations are still placeholder-style rather than exact executable checks.

## Guardrail Output (If Required)

- Safety checks:
  Not required for this plan-review pass.
- Blocking risks:
  N/A
- Verdict:
  N/A

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  Critical review completed. The plan is not implementation-ready in its current form.
- Next steps:
  1. Amend the plan so MEU-60 includes the persistence contract work it actually depends on: repository/UoW extensions and concrete infra wiring, or an explicitly approved alternative pattern.
  2. Expand `configure_provider` to the full PATCH-style contract from Phase 8, including optional `api_key` and `is_enabled`.
  3. Replace the generic connection-success rule with provider-specific ACs/tests sourced from the full §8.6 validation table.
  4. Tighten the `list_providers()` contract to the `ProviderStatus` shape already required by §8.6 and `06f-gui-settings.md`.
  5. Correct the `BUILD_PLAN.md` target totals and replace non-executable validation placeholders with exact commands.

---

## Corrections Applied — 2026-03-11

**Applied by:** Opus (implementation agent)
**Workflow:** `/planning-corrections`
**Files updated:** `implementation-plan.md`, `task.md`

### Verified Findings (7/7 confirmed)

| # | Severity | Verified? | Fix Applied |
|---|----------|-----------|-------------|
| 1 | High | ✅ Confirmed: `UnitOfWork` at ports.py:142-159 has no market-provider repo | Added `MarketProviderSettingsRepository` protocol, `UoW` extension, concrete `SqlMarketProviderSettingsRepository`, and wiring to MEU-60 scope |
| 2 | High | ✅ Confirmed: §8.4 ProviderConfigRequest L554-560 has all-optional fields + `is_enabled` | Expanded `configure_provider` to PATCH semantics: all params optional including `is_enabled` |
| 3 | High | ✅ Confirmed: §8.6 L673-683 has multi-branch per-provider rules | Replaced generic AC-4 with 9 provider-specific ACs (AC-7 through AC-15) + AC-16 for unexpected JSON + AC-27 for providers without table entries |
| 4 | Medium | ✅ Confirmed: §8.6 L706 uses `ProviderStatus`, 06f L65-72 defines TypeScript shape | Added `ProviderStatus` Pydantic model (AC-1) and changed `list_providers()` return type from `list[dict]` to `list[ProviderStatus]` |
| 5 | Medium | ✅ Confirmed: P5=`1` (should be `12`), total=`22` (should be `45` approved), Phase 8 existing=`3` | Corrected math: `45` (P0 approved) + `6` (Phase 8) = `51` total |
| 6 | Medium | ✅ Confirmed: rows 10-14, 17-20 had placeholder validations | Replaced all with executable commands (`test -f`, `rg`, `pomera_notes search`) |
| 7 | Low | ✅ Confirmed: spec §8.2d puts utility in `security/`, plan had `market_data/` | Moved `log_redaction.py` to `security/log_redaction.py` per spec |

### Changes Summary

- Total ACs expanded from 28 → 43 (FIC-59: 6, FIC-62: 7, FIC-60: 30)
- MEU-60 scope expanded to include persistence layer: `MarketProviderSettingsRepository` + UoW extension + concrete repo
- New files added to plan: `provider_status.py`, `test_market_provider_settings_repo.py`
- Task table expanded from 20 → 24 rows
- All task validations now executable

### Verdict

`corrections_applied` — Ready for re-review or execution approval.
