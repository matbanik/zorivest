---
date: "2026-04-24"
review_mode: "handoff"
target_plan: ".agent/context/handoffs/125-2026-04-24-build-plan-incomplete-meus-critical-review.md"
verdict: "changes_required"
findings_count: 11
template_version: "2.1"
requested_verbosity: "standard"
agent: "Codex"
---

# Critical Review: 125 Build Plan Incomplete MEUs Corrections

> **Review Mode**: `handoff`
> **Verdict**: `changes_required`

## Scope

**Target**: `.agent/context/handoffs/125-2026-04-24-build-plan-incomplete-meus-critical-review.md`
**Review Type**: plan-corrections recheck of a resolved critical review handoff
**Checklist Applied**: PR + DR from `.agent/workflows/plan-critical-review.md`

The target handoff now claims all 16 original findings were corrected and sets `status: resolved`, `action_required: NONE`. This recheck verifies that claim against the corrected build-plan docs and current code symbols.

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | Critical | The target handoff falsely marks all findings resolved. The root build phase table still says Phase 7 depends on `All` and Phase 10 depends on `Phases 4, 7, 9`, preserving the original Phase 7/10 cycle at the top-level source of truth. The detailed daemon/distribution docs were partly corrected, but `docs/BUILD_PLAN.md` remains contradictory. | `.agent/context/handoffs/125-2026-04-24-build-plan-incomplete-meus-critical-review.md:1`, `docs/BUILD_PLAN.md:47`, `docs/BUILD_PLAN.md:56` | Reopen C1. Update `docs/BUILD_PLAN.md` phase table to match the corrected split dependency contract, then only mark the handoff resolved after this top-level table is consistent. | open |
| 2 | Critical | SQL sandbox corrections are internally inconsistent and still name the wrong sensitive tables. The main `SqlSandbox` snippet still denies only `encrypted_keys`, `auth_users`, and SQLite metadata, still opens plain `sqlite3.connect(...mode=ro)` with no SQLCipher key path, and the later deny expansion uses table names that do not match current ORM tables (`market_data_providers` vs `market_provider_settings`, `email_provider_settings` vs `email_provider`). | `docs/build-plan/09c-pipeline-security-hardening.md:146`, `docs/build-plan/09c-pipeline-security-hardening.md:221`, `docs/build-plan/09c-pipeline-security-hardening.md:227`, `packages/infrastructure/src/zorivest_infra/database/models.py:221`, `packages/infrastructure/src/zorivest_infra/database/models.py:244` | Reopen C3. Make the canonical code snippet SQLCipher-aware and update `DENY_TABLES`/tests to actual table names from `models.py`. Remove contradictory old deny-list text. | open |
| 3 | Critical | Policy Emulator was changed to accept `EmailTemplatePort`, but the code body still calls `self._template_repo.get_by_name(...)`. This would not compile and leaves the template-port correction incomplete. | `docs/build-plan/09f-policy-emulator.md:29`, `docs/build-plan/09f-policy-emulator.md:68` | Reopen C4. Replace all emulator references to `_template_repo` with `_template_port`, and add a contract test or exit criterion that prevents infra repository names in core emulator code. | open |
| 4 | Critical | Tax API boundary and dependency corrections were appended after the original spec instead of applied to the authoritative route/model snippets. The primary request models still lack `ConfigDict(extra="forbid")`, `reassign_lot_basis` still accepts `body: dict`, and MEU-148 still depends only on MEU-123-126 while requiring later capabilities. | `docs/build-plan/04f-api-tax.md:20`, `docs/build-plan/04f-api-tax.md:147`, `docs/build-plan/04f-api-tax.md:215`, `docs/build-plan/04f-api-tax.md:266` | Reopen C6. Rewrite the original route/model section itself; do not leave a conflicting addendum. Re-slice MEU-148 prerequisites or remove routes until their service MEUs exist. | open |
| 5 | High | DashboardService correction did not land. The primary service snippet still imports `zorivest_core.ports.unit_of_work`, still uses `a.id`, `a.current_balance`, `list_by_status`, `list_recent`, `list_active`, and `list_next_runs`, and still leaves `/watchlists` as `...`. These remain out of sync with current ports/entities. | `docs/build-plan/06j-gui-home.md:45`, `docs/build-plan/06j-gui-home.md:83`, `docs/build-plan/06j-gui-home.md:89`, `docs/build-plan/06j-gui-home.md:98`, `docs/build-plan/06j-gui-home.md:103`, `docs/build-plan/06j-gui-home.md:108`, `docs/build-plan/06j-gui-home.md:117`, `docs/build-plan/06j-gui-home.md:164` | Reopen H1. Replace the service contract with APIs that exist today or explicitly add new read ports first. Remove placeholder endpoints. | open |
| 6 | High | WebSocket corrections conflict with the original WebSocket spec. A new canonical block uses `17787` and `/api/v1/ws`, but the earlier architecture/code still shows `ws://8765`, connects to `/ws`, and calls `this.emit(...)` on a class that still does not extend/import EventEmitter. | `docs/build-plan/04-rest-api.md:342`, `docs/build-plan/04-rest-api.md:404`, `docs/build-plan/04-rest-api.md:413`, `docs/build-plan/04-rest-api.md:430` | Reopen C5/H3. Rewrite the original WebSocket section so all code snippets use the same endpoint, port, class inheritance, and auth/producer contract. | open |
| 7 | High | Service daemon URL corrections are incomplete. The unlock protocol was added, but the daemon doc still hardcodes `8765` in the architecture diagram, MCP default `API`, status UI mockup, and React status text despite the canonical dev backend being `17787`/`ZORIVEST_API_URL`. | `docs/build-plan/10-service-daemon.md:43`, `docs/build-plan/10-service-daemon.md:49`, `docs/build-plan/10-service-daemon.md:794`, `docs/build-plan/10-service-daemon.md:960`, `docs/build-plan/10-service-daemon.md:1101`, `.agent/skills/backend-startup/SKILL.md:20` | Reopen H3. Replace hardcoded ports with `ZORIVEST_API_URL`/runtime discovery, except where an explicitly labeled example must use the canonical dev value. | open |
| 8 | High | MCP template boundary ownership remains contradictory. `09e` still says MCP create/update schema owners are Pydantic request models, while `05g` adds Zod schemas. That leaves two conflicting boundary owners for MCP inputs. | `docs/build-plan/09e-template-database.md:14`, `docs/build-plan/09e-template-database.md:24`, `docs/build-plan/05g-mcp-scheduling.md:386` | Reopen H2. Change the 09e boundary inventory so MCP surfaces are owned by strict Zod schemas, with Pydantic as REST owner and parity tests between the two. | open |
| 9 | High | Tax MCP write annotations are unchanged. `record_quarterly_tax_payment` still declares `destructiveHint: false` and `idempotentHint: true` while documenting `Side Effects: Writes payment record`. | `docs/build-plan/05h-mcp-tax.md:290`, `docs/build-plan/05h-mcp-tax.md:294`, `docs/build-plan/05h-mcp-tax.md:304` | Reopen H5. Mark the tool destructive/non-idempotent unless an idempotency key is specified, and wire the M3 confirmation gate rather than only `confirm: true`. | open |
| 10 | High | Monetization corrections are partial. A feature enforcement matrix was added, but the core Google service snippets still build Google payloads and call `_create_event`/`_create_task` inside core, token storage still says settings table via `SettingsResolver`, and `UsageMeteringService.increment()` still references nonexistent `meter.tier`. | `docs/build-plan/11-monetization.md:76`, `docs/build-plan/11-monetization.md:145`, `docs/build-plan/11-monetization.md:165`, `docs/build-plan/11-monetization.md:182`, `docs/build-plan/11-monetization.md:193`, `docs/build-plan/11-monetization.md:318` | Reopen H4. Move Google integration behind core ports/infrastructure adapters, resolve token storage against an encrypted model, and fix `UsageMeter`/quota error contracts. | open |
| 11 | Medium | Several corrections were appended as addenda while contradictory original snippets remain above them. This creates two sources of truth and makes implementation order-dependent on which section a future agent reads first. Examples include Tax API boundary enforcement, WebSocket canonical endpoint, and SQL sandbox deny-list expansion. | `docs/build-plan/04f-api-tax.md:20`, `docs/build-plan/04f-api-tax.md:266`, `docs/build-plan/04-rest-api.md:342`, `docs/build-plan/04-rest-api.md:430`, `docs/build-plan/09c-pipeline-security-hardening.md:146`, `docs/build-plan/09c-pipeline-security-hardening.md:227` | Convert addenda into edits of the canonical snippets. Avoid "later correction overrides earlier code" patterns in build-plan docs. | open |

## Checklist Results

### Plan Review

| Check | Result | Evidence |
|-------|--------|----------|
| PR-1 Plan/task alignment | fail | The target handoff says all corrections resolved, but corrected docs still contradict the original findings. |
| PR-2 Not-started confirmation | pass | This is docs-only plan correction review; no production code implementation is under review. |
| PR-3 Task contract completeness | n/a | Target is a correction handoff, not an execution `task.md`. |
| PR-4 Validation realism | fail | The resolved handoff lists correction batches but no reproducible verification for the 16 closure claims. |
| PR-5 Source-backed planning | fail | Several corrected docs still conflict with local canon, especially architecture and boundary ownership. |
| PR-6 Handoff/corrections readiness | fail | The handoff status/action state says no action is required despite multiple residual critical/high findings. |

### Docs Review

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | `status: resolved` does not match residual file state. |
| DR-2 Residual old terms | fail | `8765`, `_template_repo`, `body: dict`, and wrong sensitive table names remain. |
| DR-3 Downstream references updated | fail | `docs/BUILD_PLAN.md` top-level phase dependency table was not updated. |
| DR-4 Verification robustness | fail | No evidence sweep in the handoff would catch contradictory old snippets. |
| DR-5 Evidence auditability | fail | Correction batch table names files but gives no line refs or command receipts. |
| DR-6 Cross-reference integrity | fail | 09e/05g boundary ownership, daemon/backend ports, and dashboard/current ports are inconsistent. |
| DR-7 Evidence freshness | fail | Reproduced sweeps contradict the handoff's resolved verdict. |
| DR-8 Completion vs residual risk | fail | The handoff declares `Action Required: NONE` with unresolved critical/high items. |

## Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Initial correction sweeps | `C:\Temp\zorivest\plan-review-125-sweeps.txt` |
| GUI/API/MCP/monetization residual sweeps | `C:\Temp\zorivest\plan-review-125-sweeps-b.txt` |

## Verdict

`changes_required` - The correction pass is not actually complete. The resolved handoff should be reopened, or a new `/plan-corrections` pass should address the 11 residual findings above before implementation resumes from these incomplete MEUs.

---

## Recheck (2026-04-24, Pass 2)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: Codex  
**Verdict**: `changes_required`

The second correction pass materially improved the plan set. The prior all-open status is no longer accurate: 7 of the 11 previous recheck findings are now fixed or reduced to non-blocking cleanup. Four findings remain blocking, with one additional medium consistency issue.

### Prior Pass Summary

| Prior Finding | Recheck Result | Evidence |
|---|---|---|
| 1. Phase 7/10 cycle | Fixed | `docs/BUILD_PLAN.md:47` now scopes Phase 7 to Phase 10 static artifacts only; `docs/BUILD_PLAN.md:56` removes Phase 7 from Phase 10 dependencies. |
| 2. SQL sandbox table/cipher mismatch | Mostly fixed | `09c-pipeline-security-hardening.md:146-172` now uses SQLCipher-aware `open_sandbox_connection(db_path, key, read_only=True)` and actual table names including `market_provider_settings`/`email_provider`. Minor residual: file-change table at `09c:220-222` still has stale signature/context wording. |
| 3. Emulator template port | Fixed | `09f-policy-emulator.md:30-68` now uses `EmailTemplatePort` and `_template_port.get_by_name`. |
| 4. Tax API boundary/deps | Partially fixed | Strict request models and `ReassignBasisRequest` are present at `04f:17-57` and `04f:155`; MEU-148 dependency/order and response envelope contradictions remain. |
| 5. Dashboard service | Still open | Service snippet still uses nonexistent `Account.id` and downstream docs still reference removed endpoints. |
| 6. WebSocket endpoint/EventEmitter | Mostly fixed | `04-rest-api.md:404` now connects to `/api/v1/ws` and `this.emit` is removed. Residual endpoint diagram/producer detail is non-blocking but should be cleaned. |
| 7. Service daemon URL | Fixed | `10-service-daemon.md:43`, `10-service-daemon.md:794`, and `10-service-daemon.md:1101` now use `17787`/`ZORIVEST_API_URL`. |
| 8. MCP template boundary ownership | Fixed | `09e-template-database.md:18-21` now assigns MCP schemas to Zod and REST schemas to Pydantic. |
| 9. Tax MCP payment annotations | Fixed | `05h-mcp-tax.md:295-310` marks the payment tool destructive/non-idempotent and documents write side effects. |
| 10. Monetization enforcement/ports | Partially fixed | Feature gate and Google adapter split are present; OAuth token storage still claims encrypted `SettingsResolver` storage, which current resolver does not provide. |
| 11. Addenda overriding canonical snippets | Partially fixed | Several snippets were rewritten, but Tax route responses and Dashboard docs still have contradictory canonical/addendum behavior. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | High | DashboardService still does not compile against current entities/ports. The corrected snippet imports current repository protocols, but still filters and reads accounts via `a.id`; the actual `Account` entity exposes `account_id`. Tests also still instantiate `DashboardService(uow)` even though the constructor now requires five repositories. | `docs/build-plan/06j-gui-home.md:45`, `docs/build-plan/06j-gui-home.md:96`, `docs/build-plan/06j-gui-home.md:99`, `docs/build-plan/06j-gui-home.md:102`, `docs/build-plan/06j-gui-home.md:404-420`, `packages/core/src/zorivest_core/domain/entities.py:98-101` | Replace all `a.id` usages with `a.account_id`, update tests to pass repositories or specify a UoW-backed constructor, and verify every method in the snippet exists on current ports. | open |
| R2 | High | Dashboard REST/UI contract is internally inconsistent. The endpoint list now defines only four endpoints, but UI/query/startup/output sections still reference six sections/endpoints including `/dashboard/active-trades` and `/dashboard/upcoming-jobs`. | `docs/build-plan/06j-gui-home.md:135-168`, `docs/build-plan/06j-gui-home.md:179-183`, `docs/build-plan/06j-gui-home.md:231-256`, `docs/build-plan/06j-gui-home.md:371-374`, `docs/build-plan/06j-gui-home.md:491` | Either restore service methods/routes for active trades and upcoming jobs or reduce every UI/output/test reference to the four real endpoints. | open |
| R3 | High | Tax API MEU-148 is still dependency-broken. It still says MEU-123-126 produce a `TaxService` implementing quarterly estimates, payments, harvesting, YTD summary, and audit, but those capabilities correspond to later tax MEUs in `BUILD_PLAN.md`. This still forces stubs or premature scope expansion. | `docs/build-plan/04f-api-tax.md:225-240`, `docs/BUILD_PLAN.md:479-532` | Re-slice MEU-148 by capability, move full tax API after required service MEUs, or explicitly split route groups into staged MEUs with only implemented methods exposed. | open |
| R4 | High | Tax disclaimer envelope is specified but not integrated into the route snippets. The routes still return raw service results, while the later envelope block says all tax endpoints must return `TaxResponseEnvelope`. Future implementers can reasonably follow the route code and omit the disclaimer. | `docs/build-plan/04f-api-tax.md:60-179`, `docs/build-plan/04f-api-tax.md:275-295` | Make the route snippets themselves return `TaxResponseEnvelope` or define a response helper/dependency used by every route. Do not leave envelope behavior as a later addendum. | open |
| R5 | Medium | Monetization OAuth token storage still overclaims encryption through `SettingsResolver`. Current `SettingsResolver` is pure parsing/resolution and export filtering; it does not encrypt/decrypt values. The plan still says tokens are stored in the settings table via `SettingsResolver` and retrieved by Google adapters from settings. | `docs/build-plan/11-monetization.md:144-149`, `docs/build-plan/11-monetization.md:163`, `docs/build-plan/11-monetization.md:198-213`, `packages/core/src/zorivest_core/domain/settings_resolver.py:28-98` | Specify a real encrypted OAuth token model/repository or a concrete encrypted settings storage adapter. Do not attribute encryption to `SettingsResolver` unless a new encryption contract is added. | open |
| R6 | Medium | SQL sandbox doc has a stale file-change table after the corrected canonical snippet. It says `open_sandbox_connection(db_path) -> SqlSandbox` and that `pipeline_runner.py` injects `sql_sandbox` alongside `db_connection`, while the mandatory callsite section says step context must expose only `sql_sandbox`. | `docs/build-plan/09c-pipeline-security-hardening.md:216-238` | Align the file-change table with the canonical snippet: include `(db_path, key, read_only=True)` and remove "alongside `db_connection`" wording. | open |

### Confirmed Fixes

- Phase 7/10 top-level dependency cycle is corrected in `docs/BUILD_PLAN.md`.
- SQL sandbox sensitive table names now match current ORM tables for the originally cited market/email credential tables.
- Policy Emulator no longer references the infra repository in the constructor/body.
- MCP template boundary ownership now correctly separates Zod for MCP and Pydantic for REST.
- Tax MCP payment tool annotations now match write side effects.
- Service daemon port defaults are aligned to `17787`/`ZORIVEST_API_URL`.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 2 residual sweeps | `C:\Temp\zorivest\recheck-125-2-sweeps.txt` |
| Dashboard and monetization focused sweeps | `C:\Temp\zorivest\recheck-125-2-sweeps-b.txt` |
| ORM table-name confirmation | `C:\Temp\zorivest\recheck-125-2-tables.txt` |
| SettingsResolver/WebSocket producer checks | `C:\Temp\zorivest\recheck-125-2-extra.txt` |

### Verdict

`changes_required` - The plan corrections are substantially closer, but Dashboard, Tax API staging/response contract, monetization token storage, and a stale SQL sandbox wording conflict still need correction before this handoff can honestly return to `resolved`.

---

## Recheck (2026-04-24, Pass 3)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: Codex  
**Verdict**: `changes_required`

Pass 3 closes most of the remaining blocking items from Pass 2. Dashboard entity/constructor wiring, Dashboard endpoint count, Tax response envelopes, and monetization token storage were corrected. The remaining issues are now narrow, but still need correction before the parent handoff should be treated as resolved.

### Prior Pass Summary

| Pass 2 Finding | Recheck Result | Evidence |
|---|---|---|
| R1. DashboardService uses `Account.id` / wrong constructor tests | Fixed | `06j-gui-home.md:96-102` now uses `a.account_id`; `06j-gui-home.md:377` constructs `DashboardService(account_repo, balance_repo, trade_repo, plan_repo, watchlist_repo)`; tests use a matching `dashboard_svc` fixture at `06j:377-420`. |
| R2. Dashboard endpoint count mismatch | Fixed | Dashboard is now consistently scoped to 4 endpoints/sections at `06j:135-138`, `06j:170-260`, and `06j:467`. |
| R3. Tax API MEU-148 dependency break | Mostly fixed | `04f-api-tax.md:255-268` now provides a route availability matrix and says not to register routes before backing MEUs complete. Residual contradictory wording remains in the MEU-148 wiring text. |
| R4. Tax disclaimer envelope not integrated | Fixed | `TaxResponseEnvelope` is defined in the main route snippet at `04f:61-69`, and route snippets return it at `04f:80-203`. |
| R5. Monetization token storage via `SettingsResolver` | Fixed | `11-monetization.md:145-217` now uses `OAuthTokenPort` backed by encrypted `MarketProviderSettingModel` rows; Google adapters take `token_store: OAuthTokenPort`. |
| R6. SQL sandbox stale file-change table | Mostly fixed | `09c-pipeline-security-hardening.md:220-222` now has the correct `open_sandbox_connection(db_path, key, read_only=True)` signature and says steps no longer access the raw connection. One stale callsite row remains. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P3-1 | High | Tax API staging is still contradicted by MEU-148 wiring text. The new staging matrix says routes are registered only when their upstream service MEUs complete, but the same section still says MEU-148 wires "all Phase 3 tax functionality" and creates `TaxService` implementing all stubbed methods, including later capabilities like quarterly estimates, harvesting, and YTD summary. | `docs/build-plan/04f-api-tax.md:249-274`, `docs/BUILD_PLAN.md:524` | Change the MEU-148 wiring text to match staged registration. Suggested wording: "MEU-148 defines route contracts and wires only route groups whose prerequisite TaxService methods are implemented; later route groups activate in their owning MEUs." |
| P3-2 | Medium | Dashboard settings are specified as 8 new settings keys, but the plan does not say to add corresponding `SettingSpec` entries to the canonical `SETTINGS_REGISTRY`; current registry has no `dashboard.sections.*` keys. Settings API validation rejects unknown keys, so the dashboard settings page can fail unless this wiring is explicit. | `docs/build-plan/06j-gui-home.md:248-263`, `docs/build-plan/06j-gui-home.md:467`, `packages/core/src/zorivest_core/domain/settings.py:60` | Add a `SETTINGS_REGISTRY` task/exit criterion for the 8 dashboard keys, including value types, min/max order values, category, defaults, and export/sensitivity policy. |
| P3-3 | Medium | SQL sandbox callsite migration still has a stale "Current Path" row saying `pipeline_runner.py` injects both `db_connection` and `sql_sandbox`, while the corrected file-change table says `db_connection` is replaced by `sql_sandbox` in `context.outputs`. This is smaller than the previous issue but still leaves conflicting implementation instructions. | `docs/build-plan/09c-pipeline-security-hardening.md:220-236` | Rewrite the row to say the current path exposes raw `db_connection`; required change replaces it with `sql_sandbox` only. Avoid saying both are injected after the fix. |

### Confirmed Fixes

- Dashboard service now uses current repository protocols and `Account.account_id`.
- Dashboard docs are now consistently four sections/endpoints instead of a 4/6 split.
- Tax routes now return `TaxResponseEnvelope` in the main route snippets.
- Monetization no longer attributes OAuth token encryption to `SettingsResolver`; token access is behind `OAuthTokenPort`.
- SQL sandbox file-change table now uses the corrected SQLCipher-aware factory signature.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 3 residual sweeps | `C:\Temp\zorivest\recheck-125-3-sweeps.txt` |
| Dashboard settings registry and tax staging checks | `C:\Temp\zorivest\recheck-125-3-sweeps-b.txt` |

### Verdict

`changes_required` - The correction pass is close, but the Tax API staging contradiction and Dashboard settings registry gap are still implementation-affecting plan issues. The SQL sandbox row is a smaller cleanup item but should be fixed in the same pass to keep the security section single-sourced.

---

## Recheck (2026-04-24, Pass 4)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: Codex  
**Verdict**: `changes_required`

Pass 4 verifies that all three Pass 3 residual findings were corrected. A broader regression sweep found one remaining security-contract split from the original C3 area, so the parent handoff should still not be treated as fully resolved.

### Prior Pass Summary

| Pass 3 Finding | Recheck Result | Evidence |
|---|---|---|
| P3-1. Tax API staged route registration contradicted by MEU-148 text | Fixed | `04f-api-tax.md:249-251` now says MEU-148 wires only route groups whose prerequisite `TaxService` methods exist, and `04f:255-268` keeps the route prerequisite matrix plus the "do not register" rule. |
| P3-2. Dashboard settings not tied to `SETTINGS_REGISTRY` | Fixed | `06j-gui-home.md:268-280` now requires all 8 dashboard keys to be registered and gives type/default/min/max/export metadata; `06j:473` adds this as an exit criterion. |
| P3-3. SQL sandbox callsite row said both `db_connection` and `sql_sandbox` were injected | Fixed | `09c-pipeline-security-hardening.md:220-236` now says `context.outputs` replaces raw `db_connection` with `sql_sandbox`, and runner persistence keeps `db_connection` internal only. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P4-1 | High | SQL sensitive-table filtering is still not single-sourced. The canonical `DENY_TABLES` snippet now blocks actual current credential/control tables (`settings`, `market_provider_settings`, `email_provider`, `broker_configs`, `mcp_guard`), but the security-control table still says L1 denies only non-existent `encrypted_keys`/`auth_users`. More importantly, the MCP `list_db_tables` tool still says schema discovery excludes only `encrypted_keys`/`auth_users`; if implemented from that text, AI agents can discover schemas for the real sensitive tables even though later sample-row execution uses `SqlSandbox`. | `docs/build-plan/09c-pipeline-security-hardening.md:138`, `docs/build-plan/09c-pipeline-security-hardening.md:155-161`, `docs/build-plan/05g-mcp-scheduling.md:328`, `docs/build-plan/05g-mcp-scheduling.md:432-444`, `packages/infrastructure/src/zorivest_infra/database/models.py:200`, `packages/infrastructure/src/zorivest_infra/database/models.py:224`, `packages/infrastructure/src/zorivest_infra/database/models.py:244`, `packages/infrastructure/src/zorivest_infra/database/models.py:263`, `packages/infrastructure/src/zorivest_infra/database/models.py:381` | Replace the stale table names with a reference to `SqlSandbox.DENY_TABLES` everywhere schema discovery or SQL filtering is specified. Add explicit tests that `pipeline://db-schema`, `list_db_tables`, and `sample_table_rows` all hide/reject every denied table. | open |
| P4-2 | Medium | Phase 11 adds a future encrypted credential table, `ai_provider_keys`, but the monetization plan does not require adding that table to the SQL sandbox/schema-discovery deny contract. That can silently regress the Phase 9 security boundary when BYOK AI keys are introduced. | `docs/build-plan/11-monetization.md:328-341`, `docs/build-plan/11-monetization.md:548`, `docs/build-plan/11-monetization.md:558`, `docs/build-plan/09c-pipeline-security-hardening.md:155-161` | Add a Phase 11 acceptance criterion/exit criterion that `ai_provider_keys` is added to the SQL sandbox deny source and hidden from MCP DB schema discovery before BYOK key storage ships. | open |

### Confirmed Fixes

- Tax API MEU-148 now describes staged route registration instead of all-at-once wiring.
- Dashboard settings now explicitly require all 8 `SettingSpec` entries in `SETTINGS_REGISTRY`.
- SQL sandbox callsite migration now consistently exposes only `sql_sandbox` to step-accessible context.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 4 focused residual sweeps | `C:\Temp\zorivest\recheck-125-4-sweeps.txt` |
| Pass 4 old-finding regression sweep | `C:\Temp\zorivest\recheck-125-4-regression.txt` |
| SQL sensitive-table reference sweep | `C:\Temp\zorivest\recheck-125-4-sql-sensitive.txt` |
| Table-definition confirmation | `C:\Temp\zorivest\recheck-125-4-tabledefs.txt` |
| Monetization credential-table sweep | `C:\Temp\zorivest\recheck-125-4-monetization-keys.txt` |

### Verdict

`changes_required` - The Pass 3 residuals are fixed, but the SQL/table-discovery security contract is still split across `09c`, `05g`, and future Phase 11 credential storage. Correct that before treating handoff 125 as resolved.

---

## Recheck (2026-04-24, Pass 5)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: Codex  
**Verdict**: `changes_required`

Pass 5 verifies the stale sensitive-table names were removed from the reviewed SQL/MCP docs and that Phase 11 now calls out `ai_provider_keys`. One cross-layer wiring gap remains for schema discovery implementation and validation.

### Prior Pass Summary

| Pass 4 Finding | Recheck Result | Evidence |
|---|---|---|
| P4-1. SQL sensitive-table filtering not single-sourced | Partially fixed | `09c-pipeline-security-hardening.md:138` now points L1 at `SqlSandbox.DENY_TABLES`; `05g-mcp-scheduling.md:328` and `05g:432-444` now say schema/table/sample discovery excludes or enforces `DENY_TABLES`. Residual: the MCP resource fetches an unspecified backend route and the deny-list behavior is not pinned by explicit resource/tool tests. |
| P4-2. Phase 11 `ai_provider_keys` not tied to sandbox/schema discovery | Fixed | `11-monetization.md:363-366` requires `ai_provider_keys` in `SqlSandbox.DENY_TABLES` and hidden from MCP schema discovery before BYOK ships; `11:555` adds the same exit criterion. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P5-1 | High | DB schema discovery still has a missed backend/test wiring contract. The MCP `pipeline://db-schema` resource fetches `GET ${API_BASE}/scheduling/db-schema`, but no reviewed build-plan section defines that REST route/service owner or states that the backend endpoint filters via `SqlSandbox.DENY_TABLES`. The `list_db_tables` and `get_db_row_samples` text now references `DENY_TABLES`, but the MEU validation remains only generic "Vitest mocks"; the required security tests for `pipeline://db-schema`, `list_db_tables`, and `get_db_row_samples` hiding/rejecting denied tables are still not specified. An implementer can satisfy the current visible plan by mocking the MCP fetch while the real backend schema endpoint leaks sensitive table metadata or is never implemented. | `docs/build-plan/05g-mcp-scheduling.md:328`, `docs/build-plan/05g-mcp-scheduling.md:346-351`, `docs/build-plan/05g-mcp-scheduling.md:430-444`, `docs/build-plan/build-priority-matrix.md:149`, `docs/BUILD_PLAN.md:380` | Define the backend schema endpoint or service method that owns `/scheduling/db-schema`, require it to filter `SqlSandbox.DENY_TABLES`, and add explicit tests for the MCP resource plus `list_db_tables` and `get_db_row_samples` against every denied table. | open |

### Confirmed Fixes

- Old `encrypted_keys`/`auth_users` sensitive-table names no longer appear in `09c`, `05g`, or `11`.
- `09c` and `05g` now reference `SqlSandbox.DENY_TABLES` for SQL filtering and MCP schema/table discovery.
- Phase 11 BYOK key storage now carries an explicit SQL sandbox and MCP schema-discovery exit criterion.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 5 focused residual sweeps | `C:\Temp\zorivest\recheck-125-5-focused.txt` |
| Pass 5 broader regression sweep | `C:\Temp\zorivest\recheck-125-5-regression.txt` |
| Pass 5 test/exit-criterion sweep | `C:\Temp\zorivest\recheck-125-5-tests.txt` |

### Verdict

`changes_required` - The old sensitive-table-name contradictions are fixed, but DB schema discovery still lacks backend ownership and security-specific validation. This is exactly the kind of cross-layer wiring gap that can derail MEU-PH9.

---

## Recheck (2026-04-24, Pass 6)

**Workflow**: `/plan-critical-review` recheck  
**Agent**: Codex  
**Verdict**: `changes_required`

Pass 6 verifies that the missing backend ownership and security-test contract from Pass 5 was added. The remaining issue is now narrower: the new backend route snippet conflicts with the existing FastAPI router path/prefix convention.

### Prior Pass Summary

| Pass 5 Finding | Recheck Result | Evidence |
|---|---|---|
| P5-1. DB schema discovery lacked backend ownership and deny-table tests | Mostly fixed | `09c-pipeline-security-hardening.md:269-277` now adds four explicit schema-discovery security tests; `09c:281-310` defines backend route ownership and server-side `SqlSandbox.DENY_TABLES` filtering; `09c:314-322` updates exit criteria; `05g-mcp-scheduling.md:354-355` and `05g:441-454` now point MCP resource/tool behavior at the backend route and `09c` contract. Residual: the route snippet uses the wrong module path/decorator for current router canon. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P6-1 | High | The new schema-discovery backend route is documented against the wrong FastAPI router shape. Current code and Phase 9 canon use `packages/api/src/zorivest_api/routes/scheduling.py` with `scheduling_router = APIRouter(prefix="/api/v1/scheduling", tags=["scheduling"])`; the inserted snippet says `packages/api/src/zorivest_api/routers/scheduling.py` and `@router.get("/scheduling/db-schema")`. Implemented literally in the existing router, this either targets a non-existent module/variable or double-prefixes the route as `/api/v1/scheduling/scheduling/db-schema`, while MCP fetches `${API_BASE}/scheduling/db-schema` (`/api/v1/scheduling/db-schema`). | `docs/build-plan/09c-pipeline-security-hardening.md:282-290`, `docs/build-plan/05g-mcp-scheduling.md:19`, `docs/build-plan/05g-mcp-scheduling.md:349`, `docs/build-plan/09-scheduling.md:2409-2418`, `packages/api/src/zorivest_api/routes/scheduling.py:1`, `packages/api/src/zorivest_api/routes/scheduling.py:24`, `packages/api/src/zorivest_api/main.py:421` | Align the snippet with current canon: `packages/api/src/zorivest_api/routes/scheduling.py`, `@scheduling_router.get("/db-schema")`, externally reachable as `GET /api/v1/scheduling/db-schema` via `API_BASE + "/scheduling/db-schema"`. Update test names/descriptions to use the externally reachable path or explicitly state that `/scheduling/db-schema` is relative to `API_BASE`. | open |

### Confirmed Fixes

- Schema-discovery security tests are now explicitly listed.
- `pipeline://db-schema`, `list_db_tables`, and `get_db_row_samples` now have backend/deny-table security contracts.
- Phase 11 BYOK `ai_provider_keys` remains tied to `SqlSandbox.DENY_TABLES` and MCP schema-discovery hiding.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 6 focused schema-discovery sweep | `C:\Temp\zorivest\recheck-125-6-focused.txt` |
| Pass 6 route canon/prefix sweep | `C:\Temp\zorivest\recheck-125-6-routecanon.txt` |

### Verdict

`changes_required` - The security ownership and tests are now present, but the route snippet can still miswire the backend endpoint because it conflicts with current API router conventions.

---

## Recheck (2026-04-24, Pass 7)

**Workflow**: `/plan-critical-review` recheck + expanded GUI/TDD pass  
**Agent**: Codex  
**Verdict**: `changes_required`

Pass 7 confirms the Pass 6 schema route-prefix issue is fixed. The expanded review then checked `docs/BUILD_PLAN.md` and the referenced GUI build-plan sections for TDD/E2E readiness. The main residual risk is now the GUI shipping gate: the docs still allow several GUI MEUs to complete with manual/visual checks or stale E2E wave coverage, despite the project rule that Electron GUI verification must use Playwright E2E.

### Prior Pass Summary

| Pass 6 Finding | Recheck Result | Evidence |
|---|---|---|
| P6-1. Schema-discovery route snippet used wrong router module/decorator | Fixed | `09c-pipeline-security-hardening.md:286-292` now points to `packages/api/src/zorivest_api/routes/scheduling.py`, documents external `GET /api/v1/scheduling/db-schema`, and uses `@scheduling_router.get("/db-schema")`. `05g-mcp-scheduling.md:349` still fetches `${API_BASE}/scheduling/db-schema`, which resolves to the documented external route because `API_BASE` includes `/api/v1`. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P7-1 | Critical | The root build plan and priority matrix still permit GUI MEUs to ship without a Playwright E2E proof that the feature is reachable and visible in the real Electron UI. This conflicts with the project rule that GUI verification must use Playwright E2E and that GUI MEUs must check `ui/tests/e2e/test-ids.ts` and pass their wave tests. Multiple not-started GUI rows have no E2E gate (`gui-config-export`, `gui-reset-defaults`, `service-gui`, `gui-trade-detail-tabs`, `gui-account-enhance`, `gui-analytics-dashboard`, `gui-tax`, `gui-calculator`, `monetization-api-gui`), while the matrix still labels many GUI items as `Manual` / `Visual`. This is the same failure mode the user called out: a feature can be coded but never appear in the app shell/nav. | `AGENTS.md:218`, `AGENTS.md:344`, `docs/BUILD_PLAN.md:291-292`, `docs/BUILD_PLAN.md:417`, `docs/BUILD_PLAN.md:465-467`, `docs/BUILD_PLAN.md:530-531`, `docs/BUILD_PLAN.md:557`, `docs/build-plan/build-priority-matrix.md:43`, `docs/build-plan/build-priority-matrix.md:46-50`, `docs/build-plan/build-priority-matrix.md:84`, `docs/build-plan/build-priority-matrix.md:96-104`, `docs/build-plan/build-priority-matrix.md:164`, `docs/build-plan/build-priority-matrix.md:213-215`, `docs/build-plan/build-priority-matrix.md:279-280` | Add a root GUI shipping gate: every GUI MEU must define or extend a Playwright Electron E2E test before implementation, add/verify `data-testid` constants, run `cd ui && npm run build && npx playwright test <target>`, and show the feature reachable through the real nav/route/command entry. Replace `Manual`/`Visual` matrix validation for GUI rows with explicit Playwright targets or mark the row blocked until an E2E wave is defined. | open |
| P7-2 | High | The canonical E2E wave inventory is stale and contradictory. `06-gui.md` has Wave 6 at 23 tests, `06j` adds Wave 7 with `+3` and `TBD`, but `testing-strategy.md` still says 20 tests in 8 files over 6 waves and root `BUILD_PLAN.md` still defines MEU-170 as "All 20" after Waves 0-5. Current `ui/tests/e2e/` also contains additional tests (`account-crud`, `scheduling`, `scheduling-tz`, `screenshot-panel`, `settings-market-data`) not represented in the canonical schedule. The final E2E gate is therefore not a reliable completion condition. | `docs/build-plan/06-gui.md:416-424`, `docs/build-plan/06-gui.md:438`, `docs/build-plan/06j-gui-home.md:368-377`, `docs/build-plan/testing-strategy.md:524-550`, `docs/BUILD_PLAN.md:604`, `ui/tests/e2e/account-crud.test.ts:4`, `ui/tests/e2e/scheduling.test.ts:25`, `ui/tests/e2e/scheduling-tz.test.ts:32`, `ui/tests/e2e/screenshot-panel.test.ts:81`, `ui/tests/e2e/settings-market-data.test.ts:2` | Rebuild the E2E wave table from actual `ui/tests/e2e/*.test.ts`, add future waves for all remaining GUI MEUs, and update MEU-170 to the real cumulative count/scope. Do not leave Wave 7 as `TBD`. | open |
| P7-3 | High | The Home Dashboard route/nav correction is incomplete across GUI shell docs. `06-gui` and `06j` now make Home `/` with `Ctrl+1` and move Accounts to `/accounts` with `Ctrl+2`, but `06a-gui-shell.md` still claims the command registry matches the canonical route map while registering `nav:accounts` at `/` with `Ctrl+1`, `nav:trades` at `Ctrl+2`, and no `nav:home`. If implemented from `06a`, Home may not be reachable through the command palette/nav wiring and Accounts can keep stealing the default route. | `docs/build-plan/06-gui.md:244-255`, `docs/build-plan/06j-gui-home.md:316-344`, `docs/build-plan/06a-gui-shell.md:212-217` | Update the command registry/navigation contract to include `nav:home -> "/" -> Ctrl+1`, move Accounts to `/accounts` / `Ctrl+2`, shift the other shortcuts, and add an E2E assertion that Home loads on startup and via nav/command palette. | open |
| P7-4 | High | Detailed GUI section exit criteria still omit Playwright evidence for many pages/components. Several GUI specs only say components render or workflows work, but do not require the real Electron route to be opened after `npm run build`, nor a nav-visible assertion. This leaves future agents free to satisfy unit/component tests while never wiring the feature into the main UI. | `docs/build-plan/06b-gui-trades.md:458-485`, `docs/build-plan/06c-gui-planning.md:167-179`, `docs/build-plan/06d-gui-accounts.md:276-300`, `docs/build-plan/06e-gui-scheduling.md:211-227`, `docs/build-plan/06f-gui-settings.md:761-786`, `docs/build-plan/06g-gui-tax.md:468-493`, `docs/build-plan/06h-gui-calculator.md:355-388`, `docs/build-plan/06i-gui-watchlist-visual.md:145-178` | Add per-section exit criteria requiring a route/nav assertion in Playwright: open the real Electron app, navigate to the page through the app shell, verify the feature's root `data-testid` is visible, exercise the primary happy path, and run axe where applicable. | open |

### Confirmed Fixes

- The schema-discovery backend route snippet now matches the current `routes/scheduling.py` router and avoids the double-prefix issue.
- The SQL schema-discovery security contract from Pass 6 remains present: backend filtering, MCP resource/tool tests, and `SqlSandbox.DENY_TABLES` references are now specified.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 7 route-prefix and initial GUI sweep | `C:\Temp\zorivest\recheck-125-7-sweeps.txt` |
| GUI build-plan/E2E sweep | `C:\Temp\zorivest\recheck-125-7-gui-sweep.txt` |
| Actual UI E2E file inventory | `C:\Temp\zorivest\recheck-125-7-ui-e2e-files.txt` |
| GUI/E2E cross-reference sweep | `C:\Temp\zorivest\recheck-125-7-crossrefs.txt` |

### Verdict

`changes_required` - The prior backend route issue is fixed, but the GUI/TDD plan still has a systemic E2E enforcement gap. Before more GUI MEUs ship, the build plan should require Playwright Electron proof that each GUI feature is wired into the app shell and visible through real navigation.

---

## Recheck (2026-04-24, Pass 8)

**Workflow**: `/plan-critical-review` recheck focused on GUI TDD/E2E corrections  
**Agent**: Codex  
**Verdict**: `changes_required`

Pass 8 confirms substantial corrections landed since Pass 7: `06-gui.md` now has a mandatory GUI Shipping Gate, most detailed GUI section exit criteria now mention Playwright route/page assertions, and `06a-gui-shell.md` corrected the command registry to make Home `/` / `Ctrl+1` and Accounts `/accounts` / `Ctrl+2`. The remaining blockers are now cross-document drift that can still derail GUI implementation by pointing future agents at stale startup routes, stale E2E totals, or manual-only validation rows.

### Prior Pass Summary

| Pass 7 Finding | Recheck Result | Evidence |
|---|---|---|
| P7-1. GUI MEUs could ship without Playwright proof | Partially fixed | `06-gui.md:461-474` now requires route/nav E2E, `data-testid` constants, happy-path E2E, build gate, and wave assignment. However the priority matrix still labels many GUI rows `Manual`/`Visual`, and root `BUILD_PLAN.md` still has stale E2E count text. |
| P7-2. E2E wave inventory stale/contradictory | Partially fixed | `06-gui.md:416-428` and `testing-strategy.md:541-554` now list Waves 0-9 to 37 tests, but `testing-strategy.md:572-581` still inventories only 8 files / 20 tests and `BUILD_PLAN.md:604` still says MEU-170 is "All 20" after Waves 0-5. |
| P7-3. Home Dashboard nav/command registry mismatch | Mostly fixed | `06a-gui-shell.md:213-218` now matches Home default and Accounts second. Residual stale text remains in the command palette visual mockup, but the stronger registry contract is corrected. |
| P7-4. Detailed GUI section exit criteria omitted Playwright evidence | Mostly fixed | `06b`-`06i` sections now generally include Playwright E2E route/page checks. The remaining risk is not per-section absence; it is stale global/root contracts and matrix labels overriding the new gate. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P8-1 | High | The E2E final gate remains internally inconsistent. `06-gui.md` now says MEU-170 requires all 37+ Playwright tests after Waves 0-9, and `testing-strategy.md` repeats 37+ / 13 files. But the same testing strategy still lists only 8 files and **Total 20**, while root `BUILD_PLAN.md` still defines MEU-170 as "All 20 Playwright E2E tests green (final gate after Waves 0-5 complete)." A future implementer using the root plan can still stop at the stale 20-test gate and miss Home, scheduling, screenshot, and later GUI waves. | `docs/build-plan/06-gui.md:416-442`, `docs/build-plan/testing-strategy.md:526`, `docs/build-plan/testing-strategy.md:541-581`, `docs/BUILD_PLAN.md:604` | Make MEU-170 single-source consistent across root and referenced docs: real file inventory, real cumulative count, Waves 0-9 included, Wave 10 either enumerated per remaining GUI MEU or explicitly blocked until specified. | open |
| P8-2 | High | `06-gui.md` still describes Accounts Home as the startup/default route in multiple canonical shell sections even though `06j` and the nav table now make Home Dashboard `/` the default. The startup sequence still renders "Accounts Home skeleton"; progressive loading still tracks MRU account cards as startup data; the layout mockup still says "Accounts Home is default"; exit criteria and outputs still require `AccountsHome page` as the shell output. This can lead the next GUI-shell implementation to keep Accounts as the real first screen while Home exists only in docs/tests. | `docs/build-plan/06-gui.md:49`, `docs/build-plan/06-gui.md:103-122`, `docs/build-plan/06-gui.md:230`, `docs/build-plan/06-gui.md:480-509`, `docs/build-plan/06j-gui-home.md:316-344` | Replace all startup/default shell language with Home Dashboard as the initial route and main-bundle page. Move Accounts Home wording to `/accounts` lazy route behavior, and require an E2E startup assertion that verifies `home-page` is visible before Accounts-specific content. | open |
| P8-3 | Medium | The priority matrix still presents many GUI rows as `Manual` or `Visual`, even though the new `06-gui` gate says Manual means blocked until an E2E wave exists. This is easy to miss because agents often start from the matrix row and root MEU entry. Current E2E scaffolding also lacks `NAV_HOME` and `AppPage.navigateTo('home')` while `06-gui.md` Wave 0 now requires `nav-home`, so the test contract and the planned route/nav contract are not aligned yet. | `docs/build-plan/build-priority-matrix.md:39`, `docs/build-plan/build-priority-matrix.md:46-50`, `docs/build-plan/build-priority-matrix.md:96-104`, `docs/build-plan/build-priority-matrix.md:164`, `docs/build-plan/build-priority-matrix.md:213-215`, `docs/build-plan/build-priority-matrix.md:279-280`, `ui/tests/e2e/test-ids.ts:12-19`, `ui/tests/e2e/pages/AppPage.ts:114-126` | Replace GUI matrix validation cells with explicit Playwright targets or `Blocked - define E2E wave first`. Add/track `NAV_HOME` and Home navigation support in the E2E POM as part of the Home Dashboard correction. | open |

### Confirmed Fixes

- `06-gui.md` now contains a mandatory GUI Shipping Gate requiring real Electron Playwright proof before GUI MEU completion.
- Most detailed GUI section exit criteria now require Playwright E2E route/page verification.
- `06a-gui-shell.md` command registry now maps Home to `/` / `Ctrl+1` and Accounts to `/accounts` / `Ctrl+2`.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 8 GUI/E2E correction sweep | `C:\Temp\zorivest\recheck-125-8-sweeps.txt` |
| Pass 8 current E2E nav/test-id scaffold sweep | `C:\Temp\zorivest\recheck-125-8-e2e-nav.txt` |

### Verdict

`changes_required` - The systemic GUI E2E gate is now much stronger, but the plan is not yet internally safe to execute. The root E2E gate, shell startup/default-route contract, matrix validation labels, and current E2E nav constants still conflict with the intended Home-first, Playwright-verified GUI delivery model.

---

## Recheck (2026-04-24, Pass 9)

**Workflow**: `/plan-critical-review` recheck focused on Pass 8 corrections  
**Agent**: Codex  
**Verdict**: `changes_required`

Pass 9 confirms the main Pass 8 items were mostly corrected: root MEU-170 now says 37+ tests after Waves 0-9, `testing-strategy.md` now inventories 13 E2E files / 37+ tests, `06-gui.md` now uses Home Dashboard as the startup skeleton/main-bundle page in the main startup text, the priority matrix no longer uses bare `Manual` / `Visual` for the checked GUI rows, and E2E scaffolding now has `NAV_HOME` plus `AppPage.navigateTo('home')`. The remaining risk shifted from "missing E2E gate" to "wrong E2E wave/route mapping."

### Prior Pass Summary

| Pass 8 Finding | Recheck Result | Evidence |
|---|---|---|
| P8-1. E2E final gate still said 20 tests in root/testing docs | Fixed for Waves 0-9 | `BUILD_PLAN.md:604` now says 37+ after Waves 0-9. `testing-strategy.md:526-585` now lists 13 files and `Total` 37+. |
| P8-2. `06-gui.md` still treated Accounts Home as startup/default | Mostly fixed | Startup/progressive loading now references Home Dashboard in `06-gui.md:49`, `06-gui.md:110-122`, and outputs include `HomePage` at `06-gui.md:508`. Accounts is explicitly `/accounts` at `06-gui.md:284-286`. |
| P8-3. Matrix/manual labels and E2E scaffolding lacked Home nav | Partially fixed | Matrix rows now generally say Playwright E2E instead of bare manual validation, and `ui/tests/e2e/test-ids.ts:12-20` plus `ui/tests/e2e/pages/AppPage.ts:114-126` now include Home navigation. However many matrix wave assignments contradict `06-gui.md`'s canonical wave table. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P9-1 | High | The priority matrix now names Playwright E2E, but many wave numbers are wrong relative to the canonical wave table. Examples: matrix says Planning GUI is Wave 5 while `06-gui` says `gui-plans`/position-size is Wave 4; Account Management is Wave 4 while `06-gui` says accounts is Wave 2; Scheduling is Wave 6 while `06-gui` says scheduling is Wave 8; Market Data GUI is Wave 3 while `06-gui` says market-data is Wave 6; Tax GUI is Wave 9 while `06-gui` says Wave 9 is screenshot-panel; Calculator is Wave 2 while `06-gui` says position-size/calculator is Wave 4. This can cause future MEU handoffs to run the wrong Playwright target or claim the wrong cumulative gate. | `docs/build-plan/06-gui.md:418-427`, `docs/build-plan/build-priority-matrix.md:84`, `docs/build-plan/build-priority-matrix.md:96-104`, `docs/build-plan/build-priority-matrix.md:279-280` | Reconcile the matrix against the `06-gui.md` wave table or make `06-gui.md` the single source and replace matrix wave numbers with links to the wave table. Do not leave contradictory wave numbers in two canonical docs. | open |
| P9-2 | High | The `06-gui.md` router code sample still uses route strings with a trailing `/$` for concrete pages (`'/accounts/$'`, `'/trades/$'`, `'/planning/$'`, `'/scheduling/$'`, `'/settings/$'`), while the nav rail, command registry, and Home spec all use concrete routes without that suffix (`/accounts`, `/trades`, etc.). Even if this was intended as exact-match notation, it is not explained and directly conflicts with the implementation-facing snippets. This is a route-wiring hazard: the app shell could navigate to `/accounts` while the router snippet registers a different path. | `docs/build-plan/06-gui.md:166-186`, `docs/build-plan/06-gui.md:244-255`, `docs/build-plan/06a-gui-shell.md:213-218`, `docs/build-plan/06j-gui-home.md:331-343` | Make all router snippets use the same concrete paths as the nav/command contracts, or document and test the exact TanStack Router meaning if `/$` is intentionally required. Add a Playwright route/nav assertion that each nav item lands on the expected page root test id. | open |
| P9-3 | Medium | Several not-started GUI MEUs in root `BUILD_PLAN.md` still do not carry their Playwright wave/target in the row description, even though their matrix rows now do. `MEU-75` config export/import, `MEU-76` reset defaults, `MEU-154` tax GUI, and `MEU-155` calculator GUI still read as plain GUI work from the root plan. The global GUI Shipping Gate mitigates this, but the root MEU list remains the first stop for agents and should not omit the E2E requirement on incomplete GUI rows. | `docs/BUILD_PLAN.md:291-292`, `docs/BUILD_PLAN.md:530-531`, `docs/build-plan/06-gui.md:461-474` | Add the specific Playwright wave/target or `Blocked - define E2E wave first` wording to every incomplete GUI MEU row in root `BUILD_PLAN.md`, not only the matrix. | open |

### Confirmed Fixes

- The stale "All 20" E2E final gate is corrected to 37+ after Waves 0-9.
- The testing strategy inventory now lists the additional current E2E files (`account-crud`, `scheduling`, `scheduling-tz`, `settings-market-data`, `screenshot-panel`) and totals 37+.
- Home Dashboard is now represented in E2E test IDs and the AppPage page object.
- `06a-gui-shell.md` command registry remains aligned with Home `/` and Accounts `/accounts`.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 9 Pass-8-residual sweep | `C:\Temp\zorivest\recheck-125-9-sweep.txt` |
| Pass 9 E2E wave/route consistency sweep | `C:\Temp\zorivest\recheck-125-9-wave-routes.txt` |

### Verdict

`changes_required` - The GUI E2E policy is much healthier, but the build plan still contains contradictory wave numbers and route snippets. Those are implementation-wiring risks: future agents can run the wrong Playwright target, claim the wrong wave, or wire nav to routes that do not match the router sample.

---

## Recheck (2026-04-24, Pass 10)

**Workflow**: `/plan-critical-review` recheck focused on Pass 9 corrections  
**Agent**: Codex  
**Verdict**: `changes_required`

Pass 10 confirms the main Pass 9 blockers were mostly corrected. `06-gui.md` router snippets now use concrete paths without `/$`, the priority matrix wave numbers for the checked Waves 0-9 rows now mostly match the canonical `06-gui.md` table, and root incomplete GUI rows now generally carry `E2E wave TBD` / "define wave before implementation" wording. The remaining blocker is a narrower but still important GUI E2E contract hole around the not-started calculator expansion.

### Prior Pass Summary

| Pass 9 Finding | Recheck Result | Evidence |
|---|---|---|
| P9-1. Priority matrix wave numbers contradicted `06-gui.md` | Mostly fixed | Matrix rows now match the canonical table for market data Wave 6, planning/calculator base Wave 4, accounts Wave 2, scheduling Wave 8, backup Wave 3, and Home Wave 7 (`build-priority-matrix.md:84`, `build-priority-matrix.md:96-104`, `build-priority-matrix.md:279-280`; canonical table at `06-gui.md:416-428`). |
| P9-2. Router snippets used `/$` concrete paths | Fixed | `06-gui.md:166-186` now uses `/accounts`, `/trades`, `/planning`, `/scheduling`, and `/settings`, matching the nav/command contracts in `06a-gui-shell.md:213-218` and `06j-gui-home.md:331-343`. |
| P9-3. Root incomplete GUI rows omitted E2E wave/target or blocked wording | Mostly fixed | `BUILD_PLAN.md:291-292`, `BUILD_PLAN.md:417`, `BUILD_PLAN.md:465-467`, `BUILD_PLAN.md:530`, and `BUILD_PLAN.md:557` now use `E2E wave TBD` / define-wave-before-implementation wording. Residual issue remains for `MEU-155`. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P10-1 | High | `MEU-155` (`gui-calculator`) is not started, but root `BUILD_PLAN.md` and the priority matrix map it to the already-existing Wave 4 `position-size.test.ts` coverage owned by base MEU-48. `06h-gui-calculator.md` explicitly says Equity mode is the base MEU-48 implementation, while additional modes, scenario comparison, calculation history, and Copy-to-Plan are a follow-up MEU. The expansion acceptance criteria do not include a Playwright E2E assertion, and the Wave 4 test only covers the base equity calculation. This lets the calculator expansion ship by reusing old E2E proof that does not cover the expansion behavior. | `docs/BUILD_PLAN.md:231`, `docs/BUILD_PLAN.md:531`, `docs/build-plan/build-priority-matrix.md:280`, `docs/build-plan/06-gui.md:422`, `docs/build-plan/06h-gui-calculator.md:9-11`, `docs/build-plan/06h-gui-calculator.md:363-379`, `docs/build-plan/06h-gui-calculator.md:386-395` | Treat `MEU-155` as expansion work, not the already-covered base calculator. Either mark it `E2E wave TBD - define expansion tests before implementation`, or add a Wave 10+ calculator-expansion test set covering mode switching, scenario comparison/history, and Copy-to-Plan. Add the matching Playwright requirement to `06h` expansion exit criteria. | open |
| P10-2 | Medium | Some root E2E cumulative counts are still stale even after the wave mapping fixes. `MEU-48` says Wave 4 `position-size` tests are `+2 = 18`, but the canonical `06-gui.md` table says Wave 4 cumulative is 21. `MEU-74` says backup restore is `+2 = 16`, but canonical Wave 3 cumulative is 19. These are not as dangerous as missing E2E targets, but they make completion evidence unreliable and can cause handoffs to claim the wrong total. | `docs/BUILD_PLAN.md:231`, `docs/BUILD_PLAN.md:290`, `docs/build-plan/06-gui.md:420-422` | Update root cumulative counts to match `06-gui.md`, or remove cumulative totals from individual MEU rows and link to the canonical wave table. | open |

### Confirmed Fixes

- Concrete router paths now align across `06-gui`, `06a`, and `06j`.
- Most checked priority-matrix GUI rows now point to the correct Playwright wave or explicitly say wave TBD.
- Root incomplete GUI rows now generally block implementation until an E2E wave is defined.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 10 Pass-9-residual sweep | `C:\Temp\zorivest\recheck-125-10-sweep.txt` |
| Pass 10 calculator expansion E2E sweep | `C:\Temp\zorivest\recheck-125-10-calculator.txt` |

### Verdict

`changes_required` - The broad GUI E2E gate is now close, but `MEU-155` still has a real contract violation: it reuses base calculator E2E coverage for a not-started expansion MEU whose behaviors are not tested by that wave. Fix that and the stale root cumulative counts before approving the plan.

---

## Recheck (2026-04-24, Pass 11)

**Workflow**: `/plan-critical-review` recheck focused on Pass 10 corrections  
**Agent**: Codex  
**Verdict**: `no_blocking_findings`

Pass 11 confirms both Pass 10 blockers are fixed. `MEU-155` is now explicitly scoped as calculator expansion work, blocked on Wave 10+ expansion-specific Playwright tests before implementation, and `06h-gui-calculator.md` now adds expansion E2E coverage for mode switching, scenario comparison, calculation history, and Copy-to-Plan. Root cumulative counts for Wave 3 and Wave 4 now match the canonical `06-gui.md` wave table.

### Prior Pass Summary

| Pass 10 Finding | Recheck Result | Evidence |
|---|---|---|
| P10-1. `MEU-155` reused base Wave 4 calculator E2E coverage for expansion work | Fixed | `BUILD_PLAN.md:531` now says `MEU-155` is expansion modes/scenarios/history/Copy-to-Plan and requires `E2E wave TBD (Wave 10+)` with expansion-specific tests before implementation. `build-priority-matrix.md:280` now says expansion wave TBD and explicitly separates base Wave 4. `06h-gui-calculator.md:365-380` now adds a Wave 10+ expansion Playwright criterion. |
| P10-2. Root cumulative E2E counts were stale | Fixed | `BUILD_PLAN.md:231` now says Wave 4 `+2 = 21`; `BUILD_PLAN.md:290` now says Wave 3 `+2 = 19`, matching `06-gui.md:421-422` and `testing-strategy.md:548-549`. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| P11-1 | Low | `06-gui.md` shipping-gate note still describes Phase 12+ matrix rows as "marked `Manual`" and explains the "`Manual` validation label", but the matrix rows checked in this pass now use `Playwright E2E — wave TBD` wording instead. This is stale documentation, not an implementation blocker, because the operational rule remains clear: unassigned GUI waves are blocked before implementation. | `docs/build-plan/06-gui.md:474`, `docs/build-plan/build-priority-matrix.md:99-102`, `docs/build-plan/build-priority-matrix.md:164`, `docs/build-plan/build-priority-matrix.md:213-215`, `docs/build-plan/build-priority-matrix.md:279-280` | Update the note to say rows marked `Playwright E2E — wave TBD` are blocked until assigned to a wave. Remove the obsolete `Manual` label language. | open |

### Confirmed Fixes

- `MEU-155` no longer reuses base Wave 4 E2E as proof for expansion behavior.
- `06h` expansion exit criteria now include explicit Playwright coverage.
- Root E2E cumulative counts for Wave 3 and Wave 4 now match the canonical wave table.
- No remaining high-severity GUI E2E wiring blockers were found in this pass.

### Commands Executed

All terminal commands redirected output to `C:\Temp\zorivest\`.

| Purpose | Receipt |
|---------|---------|
| Pass 11 Pass-10-residual sweep | `C:\Temp\zorivest\recheck-125-11-sweep.txt` |
| Pass 11 stale wording cleanup sweep | `C:\Temp\zorivest\recheck-125-11-cleanup.txt` |

### Verdict

`no_blocking_findings` - The GUI E2E contract is now coherent enough to proceed. Only a stale explanatory note remains: replace the obsolete `Manual` wording in `06-gui.md` with the current `Playwright E2E — wave TBD` terminology.
