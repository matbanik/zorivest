# Task Handoff Template

## Task

- **Date:** 2026-03-24
- **Task slug:** gui-planning-email-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Plan review for `docs/execution/plans/2026-03-24-gui-planning-email/`

## Inputs

- User request:
  - Review the explicit plan artifacts for `2026-03-24-gui-planning-email`
- Specs/docs referenced:
  - `SOUL.md`
  - `AGENTS.md`
  - `.agent/context/current-focus.md`
  - `.agent/context/known-issues.md`
  - `.agent/workflows/critical-review-feedback.md`
  - `docs/build-plan/06c-gui-planning.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `docs/build-plan/06-gui.md`
  - `.agent/docs/emerging-standards.md`
  - prior correlated plan/handoff context from `2026-03-20-gui-plans-reports-multiaccnt`
- Constraints:
  - Review-only workflow: no product fixes
  - Canonical review file for this plan folder only
  - Findings must be file-state based, not plan-claim based

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  - No product changes; review-only
  - Created `.agent/context/handoffs/2026-03-24-gui-planning-email-plan-critical-review.md`
- Design notes / ADRs referenced:
  - None
- Commands run:
  - None in coder role
- Results:
  - Review handoff created

## Tester Output

- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw AGENTS.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/task.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md`
  - `Get-Content -Raw .agent/docs/emerging-standards.md`
  - `Get-Content -Raw docs/build-plan/06c-gui-planning.md`
  - `Get-Content -Raw docs/build-plan/06f-gui-settings.md`
  - `git status --short -- docs/execution/plans/2026-03-24-gui-planning-email .agent/context/handoffs`
  - `rg -n --hidden --glob '!node_modules' --glob '!dist' "2026-03-24-gui-planning-email|gui-planning-email|090-2026-03-24-gui-planning-bp06cs6|091-2026-03-24-gui-email-settings-bp06fs2|EmailSettingsPage|email_settings_router|/api/v1/settings/email|WatchlistPage|planning.test.tsx" .`
  - `rg -n --hidden --glob '!node_modules' --glob '!dist' "settings/market|settings/email|createFileRoute\\('/settings|routeTree|SettingsLayout|McpServerStatusPanel|Email Provider|Market Data Providers'" ui/src/renderer/src`
  - `rg -n --hidden --glob '!node_modules' --glob '!dist' "aiosmtplib|SendStep|send test email|smtp" packages tests`
  - `rg -n --hidden --glob '!node_modules' --glob '!dist' "playwright test|position-size|planning|watchlist|Wave 4|Wave" ui/tests docs/build-plan docs/execution/plans`
  - `rg -n "bulk_upsert\\(|email\\.password|market_data|encrypt|Fernet|api_key" packages/infrastructure packages/core packages/api`
  - `rg -n "email\\." packages/core/src/zorivest_core/domain/settings.py tests/unit/test_settings_registry.py packages/api/src/zorivest_api/routes/settings.py packages/core/src/zorivest_core/services/settings_service.py`
  - Local route-shadowing proof:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get('/api/v1/settings/{key}')
def dyn(key: str):
    return {'route': 'dyn', 'key': key}

@app.get('/api/v1/settings/email')
def static():
    return {'route': 'static'}

print(TestClient(app).get('/api/v1/settings/email').json())
```

- Pass/fail matrix:
  - MCP/session prerequisites: PASS
  - Explicit target correlation: PASS
  - Plan-not-started confirmation: PASS (`git status` shows only untracked plan folder)
  - MEU-70 baseline accuracy: FAIL
  - MEU-73 storage/security assumption: FAIL
  - MEU-73 UI/API route integration completeness: FAIL
  - Validation specificity / plan-task contract: FAIL
- Repro failures:
  - Local FastAPI proof returned `{'route': 'dyn', 'key': 'email'}` showing `/api/v1/settings/{key}` shadows a later `/api/v1/settings/email` route
  - `rg -n "email\\." ...` returned no matches in the generic settings registry/service/router files
- Coverage/test gaps:
  - The plan does not specify exact E2E coverage for the new email page
  - The plan does not identify the real missing MEU-70 assertions versus already-existing watchlist coverage
- Evidence bundle location:
  - This handoff plus cited repo files
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; review-only
- Mutation score:
  - Not run
- Contract verification status:
  - `changes_required`

## Reviewer Output

- Findings by severity:
  - **Critical** — MEU-73’s core persistence/security design is invalid as written. The plan says email settings should be saved via `SettingsService.bulk_upsert` and that `email.password` will be Fernet-encrypted at rest ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L14), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L53), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L88), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L24)). The actual settings pipeline does not support that: `SettingsService.bulk_upsert()` first validates every key against the registry and only then writes through ([settings_service.py](/p:/zorivest/packages/core/src/zorivest_core/services/settings_service.py#L56), [settings_validator.py](/p:/zorivest/packages/core/src/zorivest_core/domain/settings_validator.py#L65)), unknown keys are rejected as `Unknown setting` ([settings_validator.py](/p:/zorivest/packages/core/src/zorivest_core/domain/settings_validator.py#L65)), the registry/test suite hard-locks the generic settings catalog to exactly 24 entries across six existing categories ([test_settings_registry.py](/p:/zorivest/tests/unit/test_settings_registry.py#L4), [test_settings_registry.py](/p:/zorivest/tests/unit/test_settings_registry.py#L39), [test_settings_registry.py](/p:/zorivest/tests/unit/test_settings_registry.py#L102)), and the repository stores raw `str(v)` values with no encryption step ([repositories.py](/p:/zorivest/packages/infrastructure/src/zorivest_infra/database/repositories.py#L429)). Before implementation, the plan must either add source-backed registry/domain/test changes plus secret-at-rest handling, or switch MEU-73 to a different persistence pattern that actually supports encrypted secrets.
  - **High** — MEU-73 omits required route integration work and understates a real API shadowing hazard. The UI already exposes `navigate('/settings/email')` in the command registry ([commandRegistry.ts](/p:/zorivest/ui/src/renderer/src/registry/commandRegistry.ts#L108)), but the router only defines `/settings` and `/settings/market` ([router.tsx](/p:/zorivest/ui/src/renderer/src/router.tsx#L44)); the plan only calls out a `SettingsLayout.tsx` nav item, not a new router entry ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L120), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L40)). On the API side, the existing generic settings router already claims `GET /api/v1/settings/{key}` and `PUT /api/v1/settings/{key}` ([settings.py](/p:/zorivest/packages/api/src/zorivest_api/routes/settings.py#L44), [settings.py](/p:/zorivest/packages/api/src/zorivest_api/routes/settings.py#L95)), and `main.py` registers `settings_router` before any future email router ([main.py](/p:/zorivest/packages/api/src/zorivest_api/main.py#L309)). A local FastAPI proof in this review returned `{'route': 'dyn', 'key': 'email'}` for `/api/v1/settings/email`, confirming that naive registration would route to the generic key handler. The plan must explicitly resolve both the UI route addition and the API path/registration-order conflict.
  - **High** — MEU-70 is silently narrowed to “tests only” even though the current repo and prior project artifacts already place additional frontend work on MEU-70. The current plan says “No new component code required” ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L20)), but the prior correlated planning project explicitly deferred TradePlanPage enhancements into MEU-70 ([2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L199)). At the same time, the current task treats watchlist CRUD tests as largely missing ([task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L7)), but `planning.test.tsx` already contains watchlist render/select/add/remove/create coverage ([planning.test.tsx](/p:/zorivest/ui/src/renderer/src/features/planning/__tests__/planning.test.tsx#L280)) and the earlier MEU-48 plan already marked watchlist CRUD tests as delivered ([2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L166), [2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md#L279)). The plan needs to decide, with source-backed justification, whether MEU-70 is a corrections/assertion-strength pass, a carry-forward frontend enhancement pass, or both.
  - **Medium** — The plan artifacts do not meet the required task-contract and validation-specificity bar. `task.md` is a checkbox list rather than the required `task` / `owner_role` / `deliverable` / `validation` / `status` structure ([AGENTS.md](/p:/zorivest/AGENTS.md#L97), [critical-review-feedback.md](/p:/zorivest/.agent/workflows/critical-review-feedback.md#L186), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L5)). The verification section is also too loose for execution: it says `Wave TBD` and uses `npx playwright test --grep "planning|watchlist"` ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L161)), but the canonical wave schedule names the active planning gate as `position-size.test.ts` under Wave 4 and requires `npm run build` before every E2E run ([06-gui.md](/p:/zorivest/docs/build-plan/06-gui.md#L407), [position-size.test.ts](/p:/zorivest/ui/tests/e2e/position-size.test.ts#L1)). As written, the plan does not give the coder exact, auditable commands for the real gate.
- Open questions:
  - Should email-provider credentials live in the generic settings subsystem at all, or should MEU-73 use a dedicated encrypted model/service analogous to market-data provider credentials?
  - Is MEU-70 intended to execute the previously deferred TradePlanPage enhancement work, or should those carry-forward items be explicitly de-scoped with source-backed approval?
- Verdict:
  - `changes_required`
- Residual risk:
  - Approving this plan would send implementation into an invalid secret-storage design, ambiguous `/settings/email` routing, and a stale MEU-70 scope baseline.
- Anti-deferral scan result:
  - No placeholder stubs found in the plan artifacts themselves; the issue is incorrect/incomplete planning, not deferred wording.

## Guardrail Output (If Required)

- Safety checks:
  - Not invoked
- Blocking risks:
  - Not invoked
- Verdict:
  - Not invoked

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - Plan reviewed; canonical review file created; corrections required before execution
- Next steps:
  - Use `/planning-corrections` to rewrite MEU-73 around a valid persistence/encryption approach
  - Add explicit UI/API routing tasks for `/settings/email`
  - Reconcile MEU-70 with prior deferred scope and already-existing planning tests
  - Rewrite `task.md` into the required role/deliverable/validation/status contract with exact commands

---

## Recheck Update — 2026-03-24 (Revised Plan v2)

### Scope reviewed

- Rechecked the same underlying plan target `docs/execution/plans/2026-03-24-gui-planning-email/`
- Used the existing canonical review handoff as context only; file state remained source of truth
- Observed that `task.md` and `implementation-plan.md` were materially revised after the first review

### Commands rerun

- `Get-Content -Raw .agent/context/handoffs/2026-03-24-gui-planning-email-plan-critical-review.md`
- `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/task.md`
- `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md`
- `git status --short -- docs/execution/plans/2026-03-24-gui-planning-email .agent/context/handoffs/2026-03-24-gui-planning-email-plan-critical-review.md`
- `rg -n "email\\.password|/settings/email|settings_router|bulk_upsert\\(|Unknown setting|Wave TBD|watchlist CRUD|No new component code required|tests only|MEU-70" docs/execution/plans/2026-03-24-gui-planning-email .agent/context/handoffs/2026-03-24-gui-planning-email-plan-critical-review.md packages/api/src/zorivest_api/routes/settings.py packages/api/src/zorivest_api/main.py packages/core/src/zorivest_core/services/settings_service.py packages/core/src/zorivest_core/domain/settings_validator.py ui/src/renderer/src/router.tsx ui/src/renderer/src/registry/commandRegistry.ts ui/src/renderer/src/features/planning/__tests__/planning.test.tsx docs/build-plan/06-gui.md docs/execution/plans/2026-03-20-gui-plans-reports-multiaccnt/implementation-plan.md`
- Line-numbered reads of:
  - `docs/execution/plans/2026-03-24-gui-planning-email/task.md`
  - `docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md`
  - `docs/build-plan/06f-gui-settings.md`
  - `AGENTS.md`

### Findings

- **High** — The revised plan resolves the route-shadowing problem by changing the public REST contract instead of preserving the documented spec. The build plan explicitly defines `GET/PUT /api/v1/settings/email` and `POST /api/v1/settings/email/test` for this feature ([06f-gui-settings.md](/p:/zorivest/docs/build-plan/06f-gui-settings.md#L252)). The revised plan replaces those with `/api/v1/email-config` and labels that choice as `Revised spec` ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L31), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L75), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L46)). That is a product/API behavior change, not a neutral implementation detail. Under the planning contract, non-spec rules must be tagged `Spec`, `Local Canon`, `Research-backed`, or `Human-approved`, and under-specified or inconvenient specs are not permission to invent narrower behavior ([AGENTS.md](/p:/zorivest/AGENTS.md#L125), [AGENTS.md](/p:/zorivest/AGENTS.md#L160)). This plan must either preserve the specified `/settings/email` contract while solving the routing conflict internally, or carry an explicit source-backed approval for changing the API surface.

- **Medium** — The revised MEU-70 execution language now conflicts with the test-immutability rule. The plan says to “fix the failures (component or test)” and the task says “Fix any other component gaps revealed by the test run (test code is authoritative)” ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L19), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L16)). But AGENTS is explicit: once tests exist, do not modify test assertions/expected values to make them pass; only implementation changes are allowed except for setup/fixture fixes ([AGENTS.md](/p:/zorivest/AGENTS.md#L153)). The plan should remove “or test” language and state the permitted exception boundary precisely, or it invites invalid green-phase behavior.

- **Medium** — Several revised validation commands are still not execution-safe or contract-complete. The task uses `npx vitest ... | Tee-Object` for a long-running command ([task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L14)), which still violates the PowerShell guidance against piping long-running test runners ([AGENTS.md](/p:/zorivest/AGENTS.md#L281)). The E2E commands also use `cd ui && ... npx playwright test ui/tests/e2e/position-size.test.ts`, which points to `ui/tests/...` after already changing into `ui` ([task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L20), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L29)). Finally, the revised task omits the mandatory MEU gate command `uv run python tools/validate_codebase.py --scope meu` from its finalization checklist ([task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L89), [AGENTS.md](/p:/zorivest/AGENTS.md#L171)). The revised plan is much closer, but its validation section is still not ready to execute verbatim.

### Resolved Since Previous Pass

- The earlier critical finding about trying to use the generic settings pipeline for encrypted `email.*` values is now resolved in the revised plan: it recognizes that `SettingsService.bulk_upsert` cannot support this feature and proposes dedicated persistence instead ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L27)).
- The earlier high finding about omitted UI route work is partially resolved: the revised plan now explicitly adds `/settings/email` route work in `router.tsx` ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L153), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L73)).
- The earlier high finding about stale MEU-70 baseline is partially resolved: the revised plan now acknowledges that watchlist CRUD coverage already exists and reframes MEU-70 as a failure-fix/signoff pass ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L12)).

### Updated Verdict

- **Current verdict:** `changes_required`
- **Why:** the revised plan corrected the most serious storage/routing-baseline problems, but it now introduces unsourced API contract drift and still contains execution commands/instructions that do not satisfy the repo’s planning and shell rules.

### Follow-up Actions

- Keep the build-plan REST contract (`/api/v1/settings/email`) unless a source-backed exception is added; solve the route conflict without changing the public endpoint path.
- Remove or narrow any language that permits modifying tests in green phase.
- Rewrite the command blocks to use execution-safe PowerShell patterns and include the mandatory MEU gate.

---

## Recheck Update — 2026-03-24 (Revised Plan v3)

### Scope reviewed

- Rechecked the same underlying plan target `docs/execution/plans/2026-03-24-gui-planning-email/`
- Focused on whether the revised MEU-73 design is now fully wired to the repo's existing API/service/persistence architecture

### Commands rerun

- `Get-Content -Raw .agent/context/handoffs/2026-03-24-gui-planning-email-plan-critical-review.md`
- `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/task.md`
- `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md`
- `rg -n "app\\.state\\.email|get_email_provider_service|EmailProviderService\\(|email_settings_router|Base\\.metadata\\.create_all|market_provider_settings" docs/execution/plans/2026-03-24-gui-planning-email/task.md docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md packages/api/src/zorivest_api/main.py packages/api/src/zorivest_api/dependencies.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py packages/core/src/zorivest_core/application/ports.py packages/infrastructure/src/zorivest_infra/database/models.py`
- Line-numbered reads of:
  - `docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md`
  - `docs/execution/plans/2026-03-24-gui-planning-email/task.md`
  - `packages/api/src/zorivest_api/main.py`
  - `packages/api/src/zorivest_api/dependencies.py`
  - `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py`
  - `packages/core/src/zorivest_core/application/ports.py`
  - `packages/infrastructure/src/zorivest_infra/database/models.py`
- Local FastAPI registration-order proof (rerun): static `/api/v1/settings/email` registered before dynamic `/api/v1/settings/{key}` returned the correct email handlers for both `GET /api/v1/settings/email` and `POST /api/v1/settings/email/test`

### Findings

- **High** — The latest revision fixes the public API contract and the route-order issue, but MEU-73 still omits required internal wiring for this codebase's service/persistence architecture. The plan now adds a new domain model, repository, service, route, and dependency ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L84), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L122), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L55)), but the current API resolves services from `app.state` and returns `500` when they are not preconfigured ([dependencies.py](/p:/zorivest/packages/api/src/zorivest_api/dependencies.py#L24), [dependencies.py](/p:/zorivest/packages/api/src/zorivest_api/dependencies.py#L109)). `main.py` constructs every route-backed service during lifespan and calls `Base.metadata.create_all(engine)` before any new email-specific module is mentioned ([main.py](/p:/zorivest/packages/api/src/zorivest_api/main.py#L147), [main.py](/p:/zorivest/packages/api/src/zorivest_api/main.py#L170)). The current persistence pattern also exposes repositories through `UnitOfWork`/`SqlAlchemyUnitOfWork` attributes, but neither protocol nor implementation has an email-provider slot today ([ports.py](/p:/zorivest/packages/core/src/zorivest_core/application/ports.py#L240), [unit_of_work.py](/p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py#L55), [unit_of_work.py](/p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py#L81)). Finally, existing ORM models are centralized in `models.py` and are known to `Base.metadata.create_all(engine)` from there ([models.py](/p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L182), [models.py](/p:/zorivest/packages/infrastructure/src/zorivest_infra/database/models.py#L206)), while the plan puts the new SQLAlchemy model inside a separate `email_provider_repository.py` file without specifying how that model is imported before schema creation ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L88)). Before execution, the plan needs explicit tasks for repository/UoW wiring, lifespan service construction on `app.state`, and deterministic model registration before `create_all`.

### Resolved Since Previous Pass

- The plan now preserves the spec API contract `GET/PUT /api/v1/settings/email` and `POST /api/v1/settings/email/test` instead of drifting to `/api/v1/email-config` ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L27)).
- The route-shadowing fix is now technically valid: registering the static email router before the generic settings router is sufficient, and the local FastAPI proof returned the correct handlers.
- The test-immutability conflict is resolved: the task now says to fix implementation code only, with setup/fixture fixes as the narrow exception ([task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L16)).
- The PowerShell and validation command issues are resolved: the latest task removes the hanging pipe pattern, fixes the Playwright path after `cd ui`, and includes `uv run python tools/validate_codebase.py --scope meu` ([task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L31), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L94)).

### Updated Verdict

- **Current verdict:** `changes_required`
- **Why:** the external contract and validation plan are now in good shape, but the latest draft still does not tell the coder how to integrate the new email service/repository/model into the repo's existing `app.state`, `UnitOfWork`, and SQLAlchemy model-registration flow. That is a runtime-affecting omission, not a cosmetic detail.

### Follow-up Actions

- Add explicit MEU-73 tasks for `app.state.email_provider_service` construction in `main.py` lifespan.
- Add explicit protocol/UoW/repository exposure steps if `EmailProviderService` is meant to use the existing UoW pattern.
- Either register the new ORM model in `models.py` or specify a guaranteed import path before `Base.metadata.create_all(engine)` runs.

---

## Recheck Update — 2026-03-24 (Revised Plan v4)

### Scope reviewed

- Rechecked the same underlying plan target `docs/execution/plans/2026-03-24-gui-planning-email/`
- Focused on whether the latest correction pass propagated the previously requested MEU-73 wiring fixes consistently across both `implementation-plan.md` and `task.md`

### Commands rerun

- `Get-Content -Raw .agent/context/handoffs/2026-03-24-gui-planning-email-plan-critical-review.md`
- `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md`
- `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/task.md`
- `rg -n "email_provider|EmailProviderService|app\\.state\\.email|UnitOfWork|email_settings_router|create_all|models\\.py|Base\\.metadata\\.create_all" docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md docs/execution/plans/2026-03-24-gui-planning-email/task.md packages/api/src/zorivest_api/main.py packages/api/src/zorivest_api/dependencies.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py packages/core/src/zorivest_core/application/ports.py packages/infrastructure/src/zorivest_infra/database/models.py`
- Line-numbered reads of:
  - `docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md`
  - `docs/execution/plans/2026-03-24-gui-planning-email/task.md`

### Findings

- **Medium** — The architecture-wiring gap is fixed in `implementation-plan.md`, but `task.md` still does not tell the coder to perform several of those required runtime steps. The revised plan now explicitly adds `models.py`, `ports.py`, `unit_of_work.py`, and lifespan wiring in `main.py` ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L33), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L93), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L174)), which resolves the prior design omission. But the executable backend checklist in `task.md` still only tells the coder to create the domain/repository/service/route, register the router, and add the dependency provider ([task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L55)). It never calls out modifying `models.py`, `ports.py`, `unit_of_work.py`, or constructing `app.state.email_provider_service` in `main.py` lifespan. Because `task.md` is the actionable execution contract, this mismatch can still lead to an incomplete implementation even though the higher-level plan is now correct.

### Resolved Since Previous Pass

- The prior high finding about missing internal MEU-73 wiring in the design plan is resolved. `implementation-plan.md` now explicitly covers ORM model placement in `models.py`, protocol/UoW exposure, lifespan service construction on `app.state`, and dependency resolution ([implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L29), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L112), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L178)).

### Updated Verdict

- **Current verdict:** `changes_required`
- **Why:** the design is now materially correct, but the execution checklist is still out of sync with that design. Before approval, `task.md` should enumerate the same required wiring steps that `implementation-plan.md` now correctly specifies.

### Follow-up Actions

- Expand the MEU-73 backend checklist in `task.md` to include `models.py`, `ports.py`, `unit_of_work.py`, and `main.py` lifespan service wiring, not just route registration and dependency creation.

---

## Recheck Update — 2026-03-24 (Revised Plan v5)

### Scope reviewed

- Rechecked the same underlying plan target `docs/execution/plans/2026-03-24-gui-planning-email/`
- Focused on whether `task.md` now fully matches the corrected MEU-73 design and execution contract

### Commands rerun

- `Get-Content -Raw .agent/context/handoffs/2026-03-24-gui-planning-email-plan-critical-review.md`
- `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md`
- `Get-Content -Raw docs/execution/plans/2026-03-24-gui-planning-email/task.md`
- `rg -n "models\\.py|ports\\.py|unit_of_work\\.py|email_provider_service|email_settings_router|app\\.state\\.email_provider_service|get_email_provider_service" docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md docs/execution/plans/2026-03-24-gui-planning-email/task.md`

### Findings

- No findings. The remaining v4 mismatch is resolved: `task.md` now explicitly includes the previously missing `models.py`, `ports.py`, `unit_of_work.py`, and `main.py` lifespan wiring steps, bringing the executable checklist into alignment with the corrected design in `implementation-plan.md` ([task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L55), [task.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/task.md#L70), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L33), [implementation-plan.md](/p:/zorivest/docs/execution/plans/2026-03-24-gui-planning-email/implementation-plan.md#L174)).

### Resolved Since Previous Pass

- The only remaining v4 issue is now closed. The MEU-73 execution checklist in `task.md` matches the internal wiring plan for `models.py`, `ports.py`, `unit_of_work.py`, `main.py`, dependency resolution, and tests.

### Updated Verdict

- **Current verdict:** `approved`
- **Why:** the current plan preserves the documented API contract, resolves the routing hazard correctly, uses a valid encrypted-persistence pattern, aligns the execution checklist with the design, and provides execution-safe validation commands.

### Residual Risk

- Normal implementation risk remains, but no plan-level blockers were found in this pass.
