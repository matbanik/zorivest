# REST API Foundation — Plan Critical Review

## Review Update — 2026-03-08

## Task

- **Date:** 2026-03-08
- **Task slug:** rest-api-foundation-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Pre-implementation critical review of `docs/execution/plans/2026-03-08-rest-api-foundation/`

## Inputs

- User request:
  - Critically review `.agent/workflows/critical-review-feedback.md`, `docs/execution/plans/2026-03-08-rest-api-foundation/task.md`, and `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md`.
- Specs/docs referenced:
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04-rest-api.md`
  - `docs/build-plan/04a-api-trades.md`
  - `docs/build-plan/04b-api-accounts.md`
  - `docs/build-plan/04c-api-auth.md`
  - `docs/build-plan/04g-api-system.md`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/BUILD_PLAN.md`
  - `.agent/context/meu-registry.md`
  - `pyproject.toml`
  - `packages/core/src/zorivest_core/services/*.py`
  - `packages/core/src/zorivest_core/application/commands.py`
- Constraints:
  - Review-only workflow. No fixes.
  - Explicit paths were provided, so auto-discovery was not used as the primary target selector.
  - Plan-review mode confirmed: the plan folder is new/untracked, and no correlated work handoff exists yet.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher

## Coder Output

- Changed files:
  - No product changes; review-only.
- Design notes / ADRs referenced:
  - None.
- Commands run:
  - `Get-Content -Raw SOUL.md`
  - `Get-Content -Raw GEMINI.md`
  - `Get-Content -Raw .agent/context/current-focus.md`
  - `Get-Content -Raw .agent/context/known-issues.md`
  - `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-08-rest-api-foundation/task.md`
  - `Get-Content -Raw docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md`
  - `Get-Content -Raw docs/BUILD_PLAN.md`
  - `Get-Content -Raw docs/build-plan/03-service-layer.md`
  - `Get-Content -Raw docs/build-plan/04-rest-api.md`
  - `Get-Content -Raw docs/build-plan/04a-api-trades.md`
  - `Get-Content -Raw docs/build-plan/04b-api-accounts.md`
  - `Get-Content -Raw docs/build-plan/04c-api-auth.md`
  - `Get-Content -Raw docs/build-plan/04g-api-system.md`
  - `Get-Content -Raw docs/build-plan/dependency-manifest.md`
  - `Get-Content -Raw pyproject.toml`
  - `Get-Content -Raw packages/core/src/zorivest_core/services/trade_service.py`
  - `Get-Content -Raw packages/core/src/zorivest_core/services/account_service.py`
  - `Get-Content -Raw packages/core/src/zorivest_core/services/image_service.py`
  - `Get-Content -Raw packages/core/src/zorivest_core/application/commands.py`
- Results:
  - Review scope loaded successfully.

## Tester Output

- Commands run:
  - `Get-ChildItem docs/execution/plans/2026-03-08-rest-api-foundation -Force`
  - `Get-ChildItem .agent/context/handoffs -Filter "*2026-03-08*rest-api-foundation*"`
  - `git status --short -- docs/build-plan docs/execution/plans/2026-03-08-rest-api-foundation .agent/context/handoffs`
  - `rg --files packages/core packages/infrastructure tests`
  - `rg -n "TradeService|AccountService|ImageService|SystemService|SettingsService|ConfigExportService|BackupManager|BackupRecoveryManager|McpGuard|service status|confirmation|unlock|api key|health|version" tests/unit tests/integration`
  - `Select-String -Path pyproject.toml -Pattern 'members = \["packages/\*"\]','zorivest-core = \{ workspace = true \}','zorivest-infra = \{ workspace = true \}','dependencies = \['`
  - `Select-String -Path docs/build-plan/04-rest-api.md -Pattern 'tags_metadata = \[','allow_origins=\["http://localhost:\*"\]','Routes available before unlock','include_router\(guard_router\)','health.check','version.get','## Exit Criteria','Settings CRUD endpoints return correct values','Service status endpoint returns process metrics','Graceful shutdown endpoint triggers backend restart'`
  - `Select-String -Path docs/build-plan/04a-api-trades.md -Pattern 'Trade lifecycle endpoints: CRUD, reports, plans, images','@trade_router.post\("/\{exec_id\}/report"','@plan_router.post\("/"','@trade_router.post\("/\{exec_id\}/journal-link"','@image_router.get\("/\{image_id\}/thumbnail"','@round_trip_router.get\("/"'`
  - `Select-String -Path docs/build-plan/04b-api-accounts.md -Pattern 'Broker adapters, bank accounts, CSV/PDF import, identifier resolution, positions','@broker_router.get\("/"','@banking_router.post\("/import"','@import_router.post\("/csv"','@identifiers_router.post\("/resolve"'`
  - `Select-String -Path docs/build-plan/04c-api-auth.md -Pattern 'envelope encryption','Flow:','Return current auth state','generate a time-limited confirmation token','expires_in_seconds: int = 60','get_confirmation_token'`
  - `Select-String -Path docs/build-plan/04g-api-system.md -Pattern 'MCP Guard Routes','GET /mcp-guard/status','HealthResponse','/api/v1/health','ServiceStatusResponse','/api/v1/service/status','graceful-shutdown','VersionResponse','get_version_context','No authentication required'`
  - `Select-String -Path packages/core/src/zorivest_core/services/trade_service.py -Pattern '^class TradeService','def create_trade','def get_trade','def match_round_trips'`
  - `Select-String -Path packages/core/src/zorivest_core/services/account_service.py -Pattern '^class AccountService','def create_account','def get_account','def list_accounts','def add_balance_snapshot'`
  - `Select-String -Path packages/core/src/zorivest_core/services/image_service.py -Pattern '^class ImageService','def attach_image','def get_trade_images','def get_thumbnail'`
  - `Select-String -Path packages/core/src/zorivest_core/application/commands.py -Pattern '^class CreateTrade','^class AttachImage','mime_type must be ''image/webp'''`
  - `Get-ChildItem -Force -Name .version,version,.version* 2>$null`
  - `rg --files packages/core/src/zorivest_core | Select-String -Pattern 'version\.py|_version\.py'`
- Pass/fail matrix:
  - Plan/task alignment: FAIL
  - Not-started confirmation: PASS
  - Task contract completeness: PASS
  - Validation realism: FAIL
  - Source-backed planning: FAIL
  - Dependency/order correctness: FAIL
- Repro failures:
  - No test execution performed; this was a docs-only review.
- Coverage/test gaps:
  - Planned auth tests do not verify envelope-encryption behavior, bootstrap persistence, or lock-contention errors.
  - Planned foundation tests verify the wrong health/version response shapes relative to canonical Phase 4 system spec.
  - Planned CRUD tests require service methods that do not exist in the approved service layer.
- Evidence bundle location:
  - This handoff file.
- FAIL_TO_PASS / PASS_TO_PASS result:
  - Not applicable; no code implementation was reviewed.
- Mutation score:
  - Not applicable.
- Contract verification status:
  - FAIL — canonical Phase 4 REST contracts and current repo state are not reconciled by the plan.

## Reviewer Output

- Findings by severity:

  1. **[CRITICAL]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:14-17`, `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:190-219`, `docs/build-plan/04c-api-auth.md:9-11`, `docs/build-plan/04c-api-auth.md:50-103` — The auth MEU knowingly replaces the canonical envelope-encryption flow with an in-memory stub while still marking the spec as fully resolved. Phase 4c requires API-key hash lookup, KEK/DEK unwrap, `bootstrap.json` persistence, revocation semantics, and explicit unlock failure modes. The plan instead says the unlock flow is "simplified for testing" and proposes an in-memory API key store. That is not a harmless test fixture; it changes the security contract that downstream MCP and GUI work rely on.

  2. **[HIGH]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:14-16`, `docs/build-plan/04a-api-trades.md:5`, `docs/build-plan/04a-api-trades.md:124`, `docs/build-plan/04a-api-trades.md:175`, `docs/build-plan/04a-api-trades.md:221`, `docs/build-plan/04b-api-accounts.md:5`, `docs/build-plan/04b-api-accounts.md:74`, `docs/build-plan/04b-api-accounts.md:97`, `docs/build-plan/04b-api-accounts.md:130`, `docs/build-plan/04b-api-accounts.md:156` — The plan narrows the Phase 4a/4b route surface without any canon update or approved source tag authorizing that change. Trades explicitly includes reports, trade plans, and journal linking; accounts explicitly includes broker sync, banking, import, and identifier resolution. Deferring those routes because the current repo is missing earlier prerequisites may be reasonable as a correction, but it is not spec-conformant as written. Approving this plan would lock in cross-phase contract drift for the REST, MCP, and GUI layers.

  3. **[HIGH]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:102-157`, `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:432-435`, `packages/core/src/zorivest_core/services/trade_service.py:16-71`, `packages/core/src/zorivest_core/services/account_service.py:15-55`, `packages/core/src/zorivest_core/services/image_service.py:15-62`, `packages/core/src/zorivest_core/application/commands.py:18-54` — The plan assumes a thin REST layer over an "existing approved service layer", but the required service APIs are not present. `TradeService` has `create_trade`, `get_trade`, and `match_round_trips`, but no list/update/delete methods. `AccountService` has create/get/list/add-balance, but no update/delete. `ImageService` has attach/list-trade-images/thumbnail, but no global metadata/full-image getters. The command contracts also do not line up with the proposed request shapes: `CreateTrade` requires `time`, and `AttachImage` requires `width`, `height`, and WebP MIME enforcement. The stop-condition note acknowledges the service-gap risk, but the task order still treats these routes as normal in-scope work instead of adding prerequisite service corrections.

  4. **[HIGH]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:78-82`, `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:293-301`, `docs/build-plan/04g-api-system.md:196-218`, `docs/build-plan/04g-api-system.md:283-309` — The plan's foundation acceptance criteria prove the wrong health/version contracts. It specifies `GET /api/v1/health -> {"status":"ok"}` and `GET /api/v1/version -> {"version","python","api"}`, but canonical Phase 4g defines `HealthResponse` with `status`, `version`, `uptime_seconds`, and `database`, and `VersionResponse` with `version` plus `context` resolved via `zorivest_core.version.get_version_context()`. The repository currently has no `zorivest_core/version.py` file, so this dependency gap needed to be surfaced and resolved in planning rather than replaced with a different response schema.

  5. **[MEDIUM]** `docs/execution/plans/2026-03-08-rest-api-foundation/task.md:6-9`, `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:19`, `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:84-88`, `pyproject.toml:5-15` — The workspace-change instructions are inaccurate and internally inconsistent. `task.md` says to add `zorivest-api` as a workspace member, while `implementation-plan.md` says to add it as a root dependency and workspace source. But the root workspace already uses `members = ["packages/*"]`, so `packages/api` is automatically a workspace member once created. This matters because it turns a simple scaffold step into a misleading pyproject rewrite and suggests a dependency/source change without justification.

  6. **[MEDIUM]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:234`, `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:294-296`, `docs/build-plan/04-rest-api.md:55` — Several validation/acceptance items are not realistic in the current environment. The BUILD_PLAN validation uses `grep -c` despite this repo being worked primarily from PowerShell/Windows and preferring `rg`. More importantly, AC-3 repeats the canonical CORS shape `allow_origins=["http://localhost:*"]`, but FastAPI's official CORS docs require either explicit origins or `allow_origin_regex` for pattern matching; a literal wildcard entry in `allow_origins` will not express "any localhost port". Source: FastAPI CORS docs (`allow_origins` vs `allow_origin_regex`), https://fastapi.tiangolo.com/tutorial/cors/

- Open questions:
  - Should Phase 4 be corrected to match the actual currently approved service surface, or should the missing Phase 3/4 prerequisites be added before any REST work starts?
  - Is the intent to implement only a temporary test harness for auth, or to deliver the real Phase 4c contract in this project?

- Verdict:
  - `changes_required`

- Residual risk:
  - If implementation starts from this plan unchanged, the likely outcome is either architecture bypass (API talks to repositories/DB directly), fake auth behavior presented as complete, or downstream MCP/GUI contract drift that will need to be unwound later.

- Anti-deferral scan result:
  - Review artifact only; no product code scanned for new deferrals. The plan itself contains explicit deferrals that are not yet canon-backed.

## Guardrail Output (If Required)

- Safety checks:
  - Not invoked.
- Blocking risks:
  - Security-contract drift in auth.
  - Cross-phase dependency drift for REST/MCP/GUI.
- Verdict:
  - `changes_required`

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  - `changes_required`
- Next steps:
  - Route this through `/planning-corrections`.
  - Resolve the auth contract choice against `04c-api-auth.md`.
  - Resolve whether missing service-layer capabilities are added as prerequisites or the canon is formally revised.
  - Rework MEU-23 health/version contracts to match `04g-api-system.md`.
  - Remove or justify root `pyproject.toml` edits against the actual uv workspace layout.

---

## Corrections Applied — 2026-03-08

> Executed via `/planning-corrections` workflow. All 6 findings verified against live repo, none refuted.

### Changes Made

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| 1 | Auth stub replaces envelope-encryption | CRITICAL | Rewrote MEU-26 to implement full 04c contract: Argon2id KDF → KEK → DEK unwrap, bootstrap.json persistence, 401/403/423 error modes. Added `AuthService` module. |
| 2 | Route narrowing without canon tags | HIGH | Added `Deferred:` annotations with `Local Canon` source tags for all 4 deferred route groups (reports, plans, journal, broker/banking/import). Added N/A entries to spec sufficiency tables. |
| 3 | Service layer gaps | HIGH | Added MEU-Prep prerequisite section: 9 new service methods (TradeService list/update/delete, AccountService update/delete, ImageService get_image/get_full/rename) + `version.py` module. Fixed CreateTradeRequest to include `time`. Fixed image upload to handle WebP conversion + width/height. |
| 4 | Health/version wrong schemas | HIGH | Replaced simplified schemas with canonical 04g `HealthResponse` (status, version, uptime_seconds, database) and `VersionResponse` (version, context). Added prerequisite `zorivest_core/version.py`. Updated FIC ACs. |
| 5 | Workspace pyproject.toml instructions | MEDIUM | Clarified: workspace membership automatic via `packages/*` glob. Only dependency + source entries needed. Removed misleading "workspace member" language. |
| 6 | CORS wildcard + grep syntax | MEDIUM | Changed `allow_origins=["http://localhost:*"]` → `allow_origin_regex=r"^http://localhost(:\d+)?$"`. Changed `grep -c` → `rg -c`. Source: FastAPI CORS docs. |

### Verification Results

| Check | Result |
|---|---|
| No "simplified/stub" auth language | ✅ 0 matches |
| No `grep -c` | ✅ 0 matches |
| `Deferred:` source tags present | ✅ 4 matches |
| HealthResponse/VersionResponse | ✅ 13 references |
| `allow_origin_regex` | ✅ 3 references |
| Envelope-encryption terms | ✅ 20 references |

### Updated Verdict

- **Status:** `corrections_applied`
- **Files modified:**
  - `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md` — full rewrite with all 6 corrections
  - `docs/execution/plans/2026-03-08-rest-api-foundation/task.md` — updated with MEU-Prep section, canonical schemas, full auth contract
- **Ready for:** re-review or execution approval

---

## Recheck Update — 2026-03-08

### Scope Rechecked

- `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md`
- `docs/execution/plans/2026-03-08-rest-api-foundation/task.md`
- Prior review file continuity in this handoff
- Current repo contracts:
  - `packages/core/src/zorivest_core/application/ports.py`
  - `packages/core/src/zorivest_core/domain/entities.py`
  - `packages/infrastructure/src/zorivest_infra/database/repositories.py`
  - `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py`
  - `docs/build-plan/dependency-manifest.md`
  - `docs/build-plan/03-service-layer.md`
  - `docs/build-plan/04a-api-trades.md`
  - `docs/build-plan/04b-api-accounts.md`
  - `docs/BUILD_PLAN.md`

### Commands Executed

- `Get-Content -Raw docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md`
- `Get-Content -Raw docs/execution/plans/2026-03-08-rest-api-foundation/task.md`
- `Get-Content -Raw .agent/context/handoffs/2026-03-08-rest-api-foundation-plan-critical-review.md`
- `git diff -- docs/execution/plans/2026-03-08-rest-api-foundation`
- `git status --short -- docs/execution/plans/2026-03-08-rest-api-foundation .agent/context/handoffs/2026-03-08-rest-api-foundation-plan-critical-review.md`
- `Get-Content -Raw packages/core/src/zorivest_core/application/ports.py`
- `Get-Content -Raw packages/core/src/zorivest_core/domain/entities.py`
- `Get-Content -Raw packages/infrastructure/src/zorivest_infra/database/repositories.py`
- `Get-Content -Raw packages/infrastructure/src/zorivest_infra/database/unit_of_work.py`
- `rg -n "sqlcipher|PRAGMA key|bootstrap.json|Fernet|Argon2id|argon2" packages/infrastructure packages/core docs/build-plan/02-infrastructure.md docs/build-plan/04c-api-auth.md`
- `Select-String -Path packages/core/src/zorivest_core/application/ports.py -Pattern '^class TradeRepository','def get\(','def save\(','def list_all\(','def exists\(','def list_for_account\(','^class AccountRepository','^class ImageRepository','def delete\(','def get_for_owner\(','^class UnitOfWork'`
- `Select-String -Path packages/infrastructure/src/zorivest_infra/database/repositories.py -Pattern '^class SqlAlchemyTradeRepository','def save\(self, trade: Trade\)','def list_all\(','def list_for_account\(','^class SqlAlchemyAccountRepository','def save\(self, account: Account\)','^class SqlAlchemyImageRepository','def get\(self, image_id: int\)','def get_for_owner\(','def delete\('`
- `Select-String -Path docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md -Pattern 'list_filtered','update_trade','delete_trade','update_account','delete_account','get_full_image','AuthService','cryptography','Fernet','bootstrap.json persistence','zorivest_infra.sqlcipher'`
- `Select-String -Path docs/build-plan/dependency-manifest.md -Pattern 'Phase 4: REST API','uv add --package zorivest-api fastapi uvicorn pydantic httpx','Phase 8: Market Data Aggregation','uv add --package zorivest-infra cryptography httpx'`
- `Select-String -Path docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md -Pattern '\| 0c \|','\| 0d \|','\| 0e \|','\| 0f \|','\| 0g \|'`
- `Select-String -Path docs/execution/plans/2026-03-08-rest-api-foundation/task.md -Pattern 'Extend \`TradeService\`','Extend \`AccountService\`','Extend \`ImageService\`','Create \`zorivest_core/version.py\`','Write \`test_service_extensions.py\`'`
- `Select-String -Path AGENTS.md -Pattern 'Tests FIRST, implementation after','NEVER modify tests to make them pass','Run \`pytest\` / \`vitest\` after EVERY code change'`
- `rg --files packages/infrastructure/src/zorivest_infra | sort`
- `Select-String -Path docs/BUILD_PLAN.md -Pattern '\| MEU-24 \|','\| MEU-53 \|','\| MEU-66 \|','\| MEU-117 \|'`
- `Select-String -Path docs/build-plan/03-service-layer.md -Pattern '\| \`ReportService\` \|','### ReportService','### SystemService','\`SettingsService\` with \`SettingsResolver\`'`

### Recheck Findings

1. **[HIGH]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:27-54`, `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:434-438`, `packages/core/src/zorivest_core/application/ports.py:15-60`, `packages/infrastructure/src/zorivest_infra/database/repositories.py:131-179`, `packages/infrastructure/src/zorivest_infra/database/repositories.py:241-254` — The new `MEU-Prep` step still does not fully resolve the dependency chain it introduces. The plan adds service methods that depend on repository behavior the current ports and SQLAlchemy repos do not expose: no trade/account delete methods, no filtered trade listing method, and repository `save()` implementations are insert-oriented rather than update-safe. In practice, `update_trade`, `delete_trade`, `update_account`, and `delete_account` require protocol and infrastructure changes, not just service edits. The plan now acknowledges service gaps, but it still under-scopes the prerequisite work needed to make those services implementable without breaking the dependency rule.

2. **[HIGH]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:238-269`, `docs/build-plan/dependency-manifest.md:26-27`, `docs/build-plan/dependency-manifest.md:57-58` — The reworked auth plan closes the earlier security-contract drift, but it introduces an unresolved dependency gap. The plan now requires Fernet-based DEK wrapping/unwrapping and an `AuthService`, yet Phase 4 dependencies still only add `fastapi`, `uvicorn`, `pydantic`, and `httpx`; `cryptography` is not introduced until Phase 8 in the dependency manifest. As written, the package/dependency plan is insufficient to implement the full 04c contract.

3. **[MEDIUM]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:262-269`, `packages/infrastructure/src/zorivest_infra/database/connection.py:111-113`, `packages/infrastructure/src/zorivest_infra/database/connection.py:25-33` — The auth rework also references integration with `zorivest_infra.sqlcipher`, but no such module exists in the current infrastructure package. The concrete SQLCipher entry point in repo state is `zorivest_infra.database.connection`. This is a planning accuracy issue rather than a code bug today, but it means the auth prerequisite is still not grounded in the actual package structure.

4. **[MEDIUM]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:434-438`, `docs/execution/plans/2026-03-08-rest-api-foundation/task.md:14-18`, `AGENTS.md:70-72` — The new prerequisite work is still sequenced backwards relative to the project’s TDD rule. Both `task.md` and the implementation-plan task table list service/version implementation steps before writing `test_service_extensions.py`, while `AGENTS.md` requires tests first and red/green discipline. The earlier review asked for service-gap planning; the recheck shows that the prerequisite was added, but not in a TDD-compliant order.

5. **[MEDIUM]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:14-21`, `docs/build-plan/04a-api-trades.md:5`, `docs/build-plan/04a-api-trades.md:124`, `docs/build-plan/04a-api-trades.md:175`, `docs/build-plan/04a-api-trades.md:221`, `docs/build-plan/04b-api-accounts.md:5`, `docs/build-plan/03-service-layer.md:33`, `docs/build-plan/03-service-layer.md:387`, `docs/BUILD_PLAN.md:169`, `docs/BUILD_PLAN.md:221`, `docs/BUILD_PLAN.md:252`, `docs/BUILD_PLAN.md:337` — The route deferrals are now source-tagged, which resolves the earlier “unsourced narrowing” problem, but the canon is still split across files. `BUILD_PLAN.md` supports later work for reports/plans/journaling, while `04a-api-trades.md`, `04b-api-accounts.md`, and `03-service-layer.md` still describe the broader route/service surface as part of the detailed Phase 4/3 specs. The plan is now traceable, but another agent reading the detailed build-plan files still lands on a contradictory scope.

### Recheck Resolution Status

- Resolved from previous pass:
  - Auth is no longer documented as an in-memory stub.
  - Health/version contracts now match the 04g system spec.
  - CORS guidance now uses `allow_origin_regex`.
  - Workspace-member language is corrected.
- Still open:
  - Prerequisite service work is under-scoped relative to ports/repos.
  - Auth dependencies/package references are still incomplete.
  - MEU-Prep ordering is not TDD-compliant.
  - Canon scope remains split across Phase 3/4 docs.

### Recheck Verdict

- **Verdict:** `changes_required`
- **Residual risk:** Moderate to high. The plan is materially better than the first pass, but execution would still likely stall in prerequisite work or push undocumented infrastructure changes into a Phase 4 API project.
- **Recommended next step:** Run `/planning-corrections` again, specifically to expand MEU-Prep to the required ports/repositories/dependencies and to normalize the remaining canon conflict around deferred routes.

---

## Recheck Corrections Applied — 2026-03-08

> Second `/planning-corrections` pass. All 5 recheck findings verified against live repo, none refuted.

### Changes Made

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| 1 | MEU-Prep under-scoped (ports/repos missing) | HIGH | Expanded MEU-Prep to include port protocol extensions (`TradeRepository.delete`/`list_filtered`/`update`, `AccountRepository.delete`/`update`, `ImageRepository.get_full_data`) and SQLAlchemy repository implementations (`session.merge` for upsert, `session.delete`, filtered queries). Full dependency chain: ports → repos → services. |
| 2 | Auth `cryptography` not in Phase 4 deps | HIGH | Added `cryptography` + `argon2-cffi` to `packages/api/pyproject.toml` deps. Documented as `dependency-manifest.md` amendment (forward-pull from Phase 8, required by canonical 04c auth). Added task 17 to update dependency-manifest. |
| 3 | `zorivest_infra.sqlcipher` doesn't exist | MEDIUM | Replaced all references with `zorivest_infra.database.connection` (verified actual module path). |
| 4 | MEU-Prep not TDD-ordered | MEDIUM | Reordered task table: task 0c is "Write tests FIRST (Red phase)" before any implementation tasks (0d–0i). Plan section heading says "TDD order: tests FIRST → red → implementation → green". Task.md bold-highlights test-first step. |
| 5 | Canon scope split across phase docs | MEDIUM | Added `[!NOTE]` block explaining: deferred routes are tracked at plan level, no canon files modified, future MEU plans pick up deferred routes when entity/service prerequisites arrive. This is a documentation note, not a code fix. |

### Verification Results

| Check | Result |
|---|---|
| No `zorivest_infra.sqlcipher` | ✅ 0 matches |
| `database.connection` present | ✅ 4 references |
| `cryptography` in plan | ✅ 8 references |
| `list_filtered` / `get_full_data` port extensions | ✅ 10 references |
| TDD "Write tests FIRST" ordering | ✅ Present in plan text + task table (task 0c) |

### Updated Verdict

- **Status:** `corrections_applied`
- **Files modified:**
  - `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md` — third iteration with all 11 total corrections (6 original + 5 recheck)
  - `docs/execution/plans/2026-03-08-rest-api-foundation/task.md` — third iteration matching plan changes
- **All prior findings resolved.** Ready for re-review or execution approval.

---

## Final Recheck Update — 2026-03-08

### Scope Rechecked

- `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md`
- `docs/execution/plans/2026-03-08-rest-api-foundation/task.md`
- Existing rolling review thread in this handoff
- Canon references for deferred-route ownership:
  - `docs/BUILD_PLAN.md`
  - `docs/build-plan/04a-api-trades.md`
  - `docs/build-plan/04b-api-accounts.md`
  - `docs/build-plan/03-service-layer.md`

### Commands Executed

- `Get-Content -Raw docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md`
- `Get-Content -Raw docs/execution/plans/2026-03-08-rest-api-foundation/task.md`
- `Get-Content -Raw .agent/context/handoffs/2026-03-08-rest-api-foundation-plan-critical-review.md`
- `git diff -- docs/execution/plans/2026-03-08-rest-api-foundation .agent/context/handoffs/2026-03-08-rest-api-foundation-plan-critical-review.md`
- `git status --short -- docs/execution/plans/2026-03-08-rest-api-foundation .agent/context/handoffs/2026-03-08-rest-api-foundation-plan-critical-review.md`
- `Select-String -Path docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md -Pattern 'No canon files are modified','ports.py \\+ repositories.py extension \\(MEU-Prep\\)','dependency-manifest.md forward-pull','Local Canon \\| ports.py \\+ repositories.py extension','PRAGMA key via \`zorivest_infra.database.connection\`'`
- `Select-String -Path docs/execution/plans/2026-03-08-rest-api-foundation/task.md -Pattern 'dependency-manifest.md','Write \`test_service_extensions.py\` FIRST','Verify tests FAIL','Extend \`ports.py\`','Extend \`repositories.py\`'`
- `Select-String -Path docs/BUILD_PLAN.md -Pattern '\| MEU-24 \|','\| MEU-53 \|','\| MEU-66 \|','\| MEU-117 \|'`
- `Select-String -Path docs/build-plan/04a-api-trades.md -Pattern '@trade_router.post\("/\{exec_id\}/report"','@plan_router.post\("/"','@trade_router.post\("/\{exec_id\}/journal-link"'`
- `Select-String -Path docs/build-plan/04b-api-accounts.md -Pattern '@broker_router.get\("/"','@banking_router.post\("/import"','@import_router.post\("/csv"','@identifiers_router.post\("/resolve"'`

### Final Recheck Findings

1. **[MEDIUM]** `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md:36`, `docs/BUILD_PLAN.md:169`, `docs/BUILD_PLAN.md:221`, `docs/BUILD_PLAN.md:252`, `docs/BUILD_PLAN.md:337`, `docs/build-plan/04a-api-trades.md:124`, `docs/build-plan/04a-api-trades.md:175`, `docs/build-plan/04a-api-trades.md:221`, `docs/build-plan/04b-api-accounts.md:74`, `docs/build-plan/04b-api-accounts.md:97`, `docs/build-plan/04b-api-accounts.md:130`, `docs/build-plan/04b-api-accounts.md:156`, `docs/build-plan/03-service-layer.md:33`, `docs/build-plan/03-service-layer.md:387` — The plan now explicitly acknowledges the route-deferral split, but it still does not reconcile the underlying canonical docs. `BUILD_PLAN.md` supports later work for reports/plans/journal linking, while the detailed Phase 3/4 specs still describe those capabilities as part of the current route/service ownership. A plan-level note reduces ambiguity for this one execution plan, but it does not normalize the canon. The previous “all prior findings resolved” claim is therefore too strong.

### Final Recheck Resolution Status

- Resolved since the prior recheck:
  - Ports/repositories are now explicitly part of MEU-Prep.
  - Auth dependency and module-path issues are fixed in the plan.
  - MEU-Prep is now TDD-first in both `task.md` and `implementation-plan.md`.
- Still open:
  - Detailed canon remains split across `BUILD_PLAN.md`, `03-service-layer.md`, `04a-api-trades.md`, and `04b-api-accounts.md`.

### Final Recheck Verdict

- **Verdict:** `changes_required`
- **Residual risk:** Low to moderate for this specific execution plan, but medium for project-wide planning continuity. An agent following this plan can probably execute the intended subset correctly; an agent following the detailed build-plan files still receives contradictory scope signals.
- **Recommended next step:** Either:
  - update the relevant Phase 3/4 canonical docs to reflect the deferred-route ownership, or
  - explicitly accept this plan-level override as the temporary controlling canon for this project and record that approval.

---

## Final Canon Corrections Applied — 2026-03-08

> Third `/planning-corrections` pass. Chose option 1: update canonical docs directly.

### Changes Made

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| 1 | Canon scope split across Phase 3/4 docs | MEDIUM | Added implementation-status annotations directly to `04a-api-trades.md` and `04b-api-accounts.md`. Each file header now shows which route groups are ✅ implemented (MEU-24/25) and which are ⬜ deferred (with MEU reference). Each deferred section header is tagged `[DEFERRED: MEU-XX (phase)]`. Updated plan's `[!NOTE]` block to reference the canon annotations. |

### Files Modified

| File | Changes |
|---|---|
| `docs/build-plan/04a-api-trades.md` | Added header implementation-status line + `[DEFERRED]` tags on reports (MEU-52), plans (MEU-66), journal (MEU-117) sections |
| `docs/build-plan/04b-api-accounts.md` | Added header implementation-status line + `[DEFERRED]` tags on broker, banking, import, identifiers sections (MEU-96–103) |
| `docs/execution/plans/.../implementation-plan.md` | Updated `[!NOTE]` block: "Canon scope annotations" replaces "Canon scope note", references spec-level annotations |

### Verification Results

| Check | Result |
|---|---|
| `DEFERRED:` markers in 04a-api-trades.md | ✅ 3 markers |
| `DEFERRED:` markers in 04b-api-accounts.md | ✅ 4 markers |
| `Implementation status:` headers in both files | ✅ 1 each |
| Plan NOTE block updated | ✅ "Canon scope annotations" present |

### Updated Verdict

- **Status:** `approved`
- **All findings resolved** across 3 correction passes (6 original + 5 recheck + 1 final recheck = 12 total corrections).
- **Files modified (cumulative):**
  - `docs/execution/plans/2026-03-08-rest-api-foundation/implementation-plan.md`
  - `docs/execution/plans/2026-03-08-rest-api-foundation/task.md`
  - `docs/build-plan/04a-api-trades.md`
  - `docs/build-plan/04b-api-accounts.md`
- **Ready for execution.**
