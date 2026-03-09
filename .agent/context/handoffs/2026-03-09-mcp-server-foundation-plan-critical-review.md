# Task Handoff Template

## Task

- **Date:** 2026-03-09
- **Task slug:** mcp-server-foundation-plan-critical-review
- **Owner role:** reviewer
- **Scope:** Pre-implementation critical review of `docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md` and `task.md`, plus cited MCP/API canon and current repo state needed to validate feasibility.

## Inputs

- User request:
  Review `.agent/workflows/critical-review-feedback.md` against `docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md` and `task.md`.
- Specs/docs referenced:
  `SOUL.md`
  `GEMINI.md`
  `AGENTS.md`
  `.agent/context/current-focus.md`
  `.agent/context/known-issues.md`
  `docs/BUILD_PLAN.md`
  `.agent/context/meu-registry.md`
  `docs/build-plan/05-mcp-server.md`
  `docs/build-plan/05a-mcp-zorivest-settings.md`
  `docs/build-plan/05c-mcp-trade-analytics.md`
  `docs/build-plan/05d-mcp-trade-planning.md`
  `docs/build-plan/04a-api-trades.md`
  `docs/build-plan/04c-api-auth.md`
  `docs/build-plan/04d-api-settings.md`
  `docs/build-plan/05j-mcp-discovery.md`
  `docs/build-plan/testing-strategy.md`
  `docs/build-plan/dependency-manifest.md`
  `packages/api/src/zorivest_api/main.py`
  `packages/api/src/zorivest_api/dependencies.py`
  `packages/api/src/zorivest_api/auth/auth_service.py`
  `packages/api/src/zorivest_api/routes/auth.py`
  `packages/api/src/zorivest_api/routes/trades.py`
  `tests/unit/test_api_trades.py`
  `tools/validate_codebase.py`
  `.agent/skills/quality-gate/SKILL.md`
- Constraints:
  Review-only workflow. No product changes. Findings first. Canonical rolling review file required for this plan folder.

## Role Plan

1. orchestrator
2. tester
3. reviewer
- Optional roles: researcher, guardrail

## Coder Output

- Changed files:
  No product changes; review-only.
- Design notes / ADRs referenced:
  None.
- Commands run:
  None.
- Results:
  No code or docs under review target were modified.

## Tester Output

- Commands run:
  `Get-Content -Raw SOUL.md`
  `Get-Content -Raw GEMINI.md`
  `Get-Content -Raw AGENTS.md`
  `Get-Content -Raw .agent/context/current-focus.md`
  `Get-Content -Raw .agent/context/known-issues.md`
  `pomera_notes search: Zorivest`
  `pomera_diagnose`
  `Get-Content -Raw .agent/workflows/critical-review-feedback.md`
  `Get-Content -Raw docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md`
  `Get-Content -Raw docs/execution/plans/2026-03-09-mcp-server-foundation/task.md`
  `Get-ChildItem .agent/context/handoffs/*.md ...`
  `rg -n "2026-03-09-mcp-server-foundation|mcp-server-foundation|032-2026-03-09-mcp-core-tools|033-2026-03-09-mcp-settings|034-2026-03-09-mcp-integration-test" .agent/context/handoffs docs/execution/plans/2026-03-09-mcp-server-foundation`
  `git status --short -- docs/execution/plans/2026-03-09-mcp-server-foundation .agent/context/handoffs docs/BUILD_PLAN.md .agent/context/meu-registry.md`
  `Get-Content -Raw docs/BUILD_PLAN.md`
  `Get-Content -Raw .agent/context/meu-registry.md`
  `Get-Content -Raw docs/build-plan/05-mcp-server.md`
  `Get-Content -Raw docs/build-plan/05a-mcp-zorivest-settings.md`
  `Get-Content -Raw docs/build-plan/05c-mcp-trade-analytics.md`
  `Get-Content -Raw docs/build-plan/05d-mcp-trade-planning.md`
  `Get-Content -Raw docs/build-plan/04a-api-trades.md`
  `Get-Content -Raw docs/build-plan/04c-api-auth.md`
  `Get-Content -Raw docs/build-plan/04d-api-settings.md`
  `Get-Content -Raw docs/build-plan/05j-mcp-discovery.md`
  `Get-Content -Raw docs/build-plan/testing-strategy.md`
  `Get-Content -Raw docs/build-plan/dependency-manifest.md`
  `Get-ChildItem packages -Directory`
  `Get-ChildItem packages/api -Recurse -File`
  `Get-ChildItem mcp-server -Recurse -File`
  `rg -n "Depends\(|get_auth_context|require_auth|Authorization|session_token|auth" packages/api/src/zorivest_api -g "*.py"`
  `Get-Content -Raw packages/api/src/zorivest_api/dependencies.py`
  `Get-Content -Raw packages/api/src/zorivest_api/auth/auth_service.py`
  `Get-Content -Raw packages/api/src/zorivest_api/routes/auth.py`
  `Get-Content -Raw packages/api/src/zorivest_api/routes/mcp_guard.py`
  `Get-Content -Raw packages/api/src/zorivest_api/routes/settings.py`
  `Get-Content -Raw packages/api/src/zorivest_api/routes/trades.py`
  `Get-Content -Raw packages/api/src/zorivest_api/main.py`
  `rg -n "scope meu|tsc --noEmit|vitest|npm run build|eslint" tools/validate_codebase.py .agent/skills/quality-gate/SKILL.md`
  `Get-Content -Raw tools/validate_codebase.py`
  `Get-Content -Raw .agent/skills/quality-gate/SKILL.md`
  `Get-ChildItem -Recurse -File -Include package.json,eslint.config.*,*.eslintrc*`
  Numbered file sweeps with `Get-Content ... | ForEach-Object { '{0,4}: {1}' -f $i, $_ } | Select-String ...` across the plan, task, build-plan, MEU registry, API auth/dependency/trade files, tests, and quality gate.
- Pass/fail matrix:
  Target correlation: PASS
  Plan-review mode confirmation (no correlated work handoffs yet): PASS
  Plan/task scope alignment: PASS
  Status readiness (unstarted): PASS
  Auth/bootstrap feasibility against current API state: FAIL
  `create_trade` contract alignment with current API/test suite: FAIL
  TypeScript gate readiness (`eslint` + `vitest` + `tsc`) for new `mcp-server/`: FAIL
  BUILD_PLAN maintenance completeness for phase transition: FAIL
- Repro failures:
  Auth/bootstrap: current API starts with `db_unlocked = False` and route dependencies reject locked DB calls until `/api/v1/auth/unlock` succeeds.
  Trade contract: current API `CreateTradeRequest` requires `time`, but the plan’s MCP `create_trade` contract omits it.
  Validation: MEU gate runs `npx eslint src/ --max-warnings 0` once `mcp-server/` exists, but the plan does not scaffold eslint dependencies/config.
  Build-plan maintenance: planned edits advance Phase 5 while leaving Phase 4 status stale in `docs/BUILD_PLAN.md`.
- Coverage/test gaps:
  No external research needed. Review was bounded to repo canon plus current implementation state.
- Evidence bundle location:
  This handoff file.
- FAIL_TO_PASS / PASS_TO_PASS result:
  Not applicable; review-only.
- Mutation score:
  Not applicable.
- Contract verification status:
  `changes_required`

## Reviewer Output

- Findings by severity:
  1. **High** — The plan defers MCP auth bootstrap even though the current API cannot service the day-1 tools until the DB is explicitly unlocked. The draft claims a dev-mode no-op `getAuthHeaders()` is enough and says day-1 tools will work against the “current no-auth state” (`implementation-plan.md:21`, `implementation-plan.md:101`), but the actual API starts locked (`packages/api/src/zorivest_api/main.py:61`, `packages/api/src/zorivest_api/main.py:67`), rejects trades/settings/images while locked (`packages/api/src/zorivest_api/dependencies.py:11`, `packages/api/src/zorivest_api/dependencies.py:20`), and the Phase 5 hub explicitly says the MCP server must unlock the encrypted DB before any tools can function (`docs/build-plan/05-mcp-server.md:196`, `docs/build-plan/05-mcp-server.md:198`, `docs/build-plan/05-mcp-server.md:240`, `docs/build-plan/05-mcp-server.md:258`). As written, the live integration test and most runtime tool calls are blocked before they start. The same issue is compounded by the current auth service starting with an empty key store (`packages/api/src/zorivest_api/auth/auth_service.py:60`, `packages/api/src/zorivest_api/auth/auth_service.py:63`, `packages/api/src/zorivest_api/auth/auth_service.py:80`), so the plan also needs an explicit key-creation/unlock bootstrap path for tests (`packages/api/src/zorivest_api/routes/auth.py:35`, `packages/api/src/zorivest_api/routes/auth.py:67`).
  2. **High** — The planned `create_trade` MCP contract does not match the live API it is supposed to proxy. The plan treats the Phase 5 trade spec as sufficient (`implementation-plan.md:33`, `implementation-plan.md:60`) and AC-1 only requires `{exec_id, instrument, action, quantity, price, account_id}` (`implementation-plan.md:212`). That matches the current Phase 5 trade doc (`docs/build-plan/05c-mcp-trade-analytics.md:29`, `docs/build-plan/05c-mcp-trade-analytics.md:40`, `docs/build-plan/05c-mcp-trade-analytics.md:56`) but not the checked-in REST API, which requires `time` in `CreateTradeRequest` and forwards it into `CreateTrade` (`packages/api/src/zorivest_api/routes/trades.py:25`, `packages/api/src/zorivest_api/routes/trades.py:27`, `packages/api/src/zorivest_api/routes/trades.py:60`, `packages/api/src/zorivest_api/routes/trades.py:67`, `packages/api/src/zorivest_api/routes/trades.py:69`). The existing API unit test also asserts `time` is present (`tests/unit/test_api_trades.py:85`, `tests/unit/test_api_trades.py:92`). If the MCP tool is implemented exactly per this plan, the round-trip path will 422 against the current repo.
  3. **High** — The scaffold/validation plan cannot clear the repo’s TypeScript quality gate because it omits eslint setup entirely. The draft says the new `package.json` only adds `@modelcontextprotocol/sdk`, `zod`, `typescript`, `vitest`, `@types/node`, and `tsx` (`implementation-plan.md:70`, `implementation-plan.md:73`, `implementation-plan.md:75`), and task 1 validates only `npm install` plus `npx tsc --noEmit` (`implementation-plan.md:191`). But once `mcp-server/` exists, the MEU gate automatically enables TypeScript checks for `mcp-server/` and `ui/` (`tools/validate_codebase.py:30`, `tools/validate_codebase.py:291`) including `npx eslint src/ --max-warnings 0` and `npx vitest run` (`tools/validate_codebase.py:378`, `tools/validate_codebase.py:381`, `tools/validate_codebase.py:398`). The quality-gate skill documents the same blocking requirements (`.agent/skills/quality-gate/SKILL.md:46`, `.agent/skills/quality-gate/SKILL.md:47`, `.agent/skills/quality-gate/SKILL.md:48`). No checked-in eslint config was found in the repo, so this plan needs explicit eslint dependency/config work before task 10 can honestly be marked complete.
  4. **Medium** — The planned `BUILD_PLAN.md` maintenance step advances Phase 5 without resolving the already-stale Phase 4 status tracker. The draft only plans to fix the Phase 3/4 summary count and set Phase 5 to In Progress (`implementation-plan.md:176`, `implementation-plan.md:177`, `implementation-plan.md:198`), while the current build plan still says “4 — REST API | In Progress” even though all Phase 4 MEUs 23–30 are already marked approved and Phase 4 is the prerequisite for Phase 5 (`docs/BUILD_PLAN.md:63`, `docs/BUILD_PLAN.md:183`, `docs/BUILD_PLAN.md:184`, `docs/BUILD_PLAN.md:185`, `.agent/context/meu-registry.md:62`, `.agent/context/meu-registry.md:71`). If executed as written, the maintenance pass will leave the build plan internally contradictory at the moment Phase 5 work starts.
- Open questions:
  Should the correction path extend this project to include a real Phase 5.7 bootstrap flow for tests/runtime, or should the API side be given an explicit dev-only pre-unlocked mode? The current repo does not implement the latter.
  Should the MCP `create_trade` surface adopt the repo’s current `time` requirement now, or should the REST/API canon be changed back to the narrower Phase 5 spec before Phase 5 implementation begins?
- Verdict:
  `changes_required`
- Residual risk:
  Even after fixing the four findings above, the plan should still be rechecked for any deliberate Stage-1 omissions versus the shared Phase 5 infrastructure (toolset loading, discovery, confirmation routing) before implementation starts.
- Anti-deferral scan result:
  Review-only; no new code scanned for deferrals beyond the standard quality-gate evidence checks.

## Guardrail Output (If Required)

- Safety checks:
  Not required for this docs-only review.
- Blocking risks:
  None beyond the findings listed above.
- Verdict:
  Not applicable.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  `changes_required`
- Next steps:
  Run `/planning-corrections` against `docs/execution/plans/2026-03-09-mcp-server-foundation/`.
  Correct the auth/bootstrap plan to match the current locked-DB API behavior.
  Reconcile the `create_trade` MCP payload with the checked-in REST/API contract.
  Add explicit TypeScript lint/build setup so the MEU gate is passable after scaffolding.
  Expand the maintenance step so `docs/BUILD_PLAN.md` reflects Phase 4 completion before Phase 5 is marked in progress.

---

## Corrections Applied — 2026-03-09

### Scope

Applied `/planning-corrections` against canonical review file above. All 4 findings verified against live codebase, zero refuted.

### Verified Findings

| # | Severity | Verified? | Current Evidence | Fix Applied |
|---|----------|-----------|------------------|-------------|
| 1 | High | ✅ Confirmed | `main.py:61` → `db_unlocked = False`; `dependencies.py:11-21` → `require_unlocked_db` gating; `auth_service.py:60` → empty `_keys` dict | Added `bootstrapAuth()` to `api-client.ts` (create-key → unlock → cache-token); updated integration test `beforeAll`; updated AC-8 |
| 2 | High | ✅ Confirmed | `trades.py:27` → `time: datetime` required in `CreateTradeRequest` | Added `time` field (ISO 8601, defaults to `new Date().toISOString()`) to `create_trade` MCP tool schema; updated AC-1, integration test AC-3 |
| 3 | High | ✅ Confirmed | `validate_codebase.py:380-383` → `npx eslint src/ --max-warnings 0` runs when `mcp-server/` exists | Added `eslint`, `@typescript-eslint/parser`, `@typescript-eslint/eslint-plugin` to dev deps; added `eslint.config.mjs` to scaffold; added `lint` script; added AC-11; updated task table row 1 |
| 4 | Medium | ✅ Confirmed | `BUILD_PLAN.md:63` → Phase 4 still `🟡 In Progress` despite all MEU-22..30 ✅ | Expanded maintenance task: fix Phase Status table (Phase 4 → `✅ Completed`), fix MEU Summary count (1 → 9), then advance Phase 5 |

### Changes Made

- **File:** `docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md`
  - 12 edit chunks applied via `multi_replace_file_content`
  - User Review Required section rewritten (auth bootstrap, Phase 4 status)
  - Scaffold section expanded (eslint deps + config file)
  - api-client.ts specification updated (bootstrapAuth + getAuthHeaders)
  - create_trade tool spec updated (time field)
  - Integration test spec updated (create-key + unlock in beforeAll)
  - BUILD_PLAN.md maintenance expanded (5 tasks, not 4)
  - Task table row 1 updated (eslint validation)
  - FIC AC-1 updated (time field source: Local Canon)
  - FIC AC-8 updated (bootstrapAuth source: Local Canon)
  - FIC AC-11 added (ESLint)
  - FIC MEU-32 ACs updated (AC-2 auth bootstrap, AC-3 time field, AC-5 added)
  - Verification plan expanded (eslint step + integration test description)

### Verification Results

```
rg "no-op|no.auth|stub.*empty" plan → 0 matches ✅
rg "In Progress" plan → 2 matches (drift description + Phase 5 target) ✅
rg -c "eslint|ESLint" plan → 8 mentions ✅
rg "time.*ISO|trades.py" plan → 3 matches (tool spec, AC-1, AC-3) ✅
rg "bootstrapAuth|create-key|unlock" plan → present in api-client + integration test ✅
```

### Open Question Resolutions

| Question | Resolution |
|----------|-----------|
| Should the project include a real Phase 5.7 bootstrap flow or a dev-only pre-unlocked mode? | **Real bootstrap.** `bootstrapAuth()` implements create-key → unlock → cache-token. Full §5.7 IDE integration deferred to MEU-38/42. |
| Should `create_trade` adopt the repo's `time` requirement or should the API be changed? | **Adopt from repo.** MCP tool adds `time` field with ISO 8601 default. Simpler and safer than changing the checked-in API contract. |

### Verdict

`approved` — all 4 findings resolved, verification clean, ready for execution.

---

## Recheck Update — 2026-03-09

### Scope

Rechecked the corrected `implementation-plan.md` and `task.md` against the prior four findings, plus the shared auth canon in `04c-api-auth.md` and `05-mcp-server.md`.

### Commands Executed

`Get-Content -Raw docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md`
`Get-Content -Raw docs/execution/plans/2026-03-09-mcp-server-foundation/task.md`
`Get-Content -Raw .agent/context/handoffs/2026-03-09-mcp-server-foundation-plan-critical-review.md`
`git status --short -- docs/execution/plans/2026-03-09-mcp-server-foundation docs/BUILD_PLAN.md .agent/context/meu-registry.md .agent/context/handoffs/2026-03-09-mcp-server-foundation-plan-critical-review.md`
`git diff -- docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md docs/execution/plans/2026-03-09-mcp-server-foundation/task.md`
Numbered line sweeps over:
`docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md`
`docs/execution/plans/2026-03-09-mcp-server-foundation/task.md`
`docs/build-plan/04c-api-auth.md`
`docs/build-plan/05-mcp-server.md`
`docs/BUILD_PLAN.md`

### Recheck Result

The previous four findings were corrected in `implementation-plan.md`:
- auth/unlock need is now acknowledged
- `create_trade` now includes `time`
- eslint scaffold is now planned
- `BUILD_PLAN.md` maintenance now includes Phase 4 completion

Two issues still remain.

### Findings by Severity

1. **High** — The revised auth correction now contradicts the documented auth model by auto-creating a new API key at MCP server startup. The updated plan explicitly says `bootstrapAuth()` will call `POST /auth/keys` and then `POST /auth/unlock` on server startup (`implementation-plan.md:21`, `implementation-plan.md:105`, `implementation-plan.md:168`). But the auth spec defines API key management as **admin only** (`docs/build-plan/04c-api-auth.md:79`, `docs/build-plan/04c-api-auth.md:83`), and the shared MCP auth flow expects the IDE to already provide `Authorization: Bearer zrv_sk_...`, with the MCP server only exchanging that provided key for a session token (`docs/build-plan/05-mcp-server.md:198`, `docs/build-plan/05-mcp-server.md:200`, `docs/build-plan/05-mcp-server.md:204`, `docs/build-plan/05-mcp-server.md:283`). As written, the plan solves the locked-DB issue by inventing implicit key minting during runtime startup, which bypasses the intended credential model instead of implementing it.

2. **Medium** — `task.md` was not brought into sync with the corrected implementation plan. The plan now requires `eslint.config.mjs` in the scaffold and a Phase 4 status-table fix in `BUILD_PLAN.md` (`implementation-plan.md:81`, `implementation-plan.md:181`, `implementation-plan.md:197`), but the task checklist still only mentions `package.json, tsconfig, vitest.config` and only says `fix Phase 3/4 count: 1→9, Phase 5 status` (`task.md:7`, `task.md:27`). That leaves the execution checklist out of alignment with the reviewed plan and makes it easier to mark the project complete while missing part of the agreed corrections.

### Open Questions

- Should Day-1 runtime auth use a spec-backed pre-provisioned API key path, with key creation limited to test harness setup only?
- If the API key cannot be pre-provisioned yet, should this project stop at integration-test bootstrap and defer runtime MCP startup auth entirely until the credential model is implemented correctly?

### Verdict

`changes_required`

### Residual Risk

If the auth bootstrap path is not corrected, the project may ship a startup flow that normalizes unaudited admin-key creation as a runtime behavior rather than a provisioning step.

---

## Recheck Corrections Applied — 2026-03-09

### Scope

Applied `/planning-corrections` against the 2 recheck findings (1 High, 1 Medium). Both verified against live codebase and spec docs.

### Verified Findings

| # | Severity | Verified? | Evidence | Fix Applied |
|---|----------|-----------|----------|-------------|
| 1 | High | ✅ Confirmed | `04c-api-auth.md:79` → key creation is "admin only"; `05-mcp-server.md:200-264` → canonical flow is IDE provides `zrv_sk_...` → MCP exchanges for session token | Rewrote `bootstrapAuth(apiKey)` to accept a pre-provisioned key from env (`ZORIVEST_API_KEY`), no runtime key creation. Test harness creates key in `beforeAll` only (explicitly labeled "test-only setup, not runtime behavior"). Updated 5 locations: User Review §auth, api-client.ts spec, integration test, AC-8, MEU-32 AC-2. |
| 2 | Medium | ✅ Confirmed | `task.md:7` missing `eslint.config.mjs`; `task.md:22` missing Phase 4 status fix | Synced both `task.md` (canonical and artifact) — scaffold now lists `eslint.config.mjs`, BUILD_PLAN task now includes `Phase 4 status: In Progress→Completed`. |

### Verification Results

```
rg "creates.*key|POST /auth/keys" plan → only in test harness context + User Review explainer ✅
"does NOT create keys" present in User Review auth section ✅
rg "eslint" task.md → line 7 mentions eslint.config.mjs ✅
rg "Phase 4.*Completed|In Progress.*Completed" task.md → line 27 ✅
```

### Open Question Resolutions

| Question | Resolution |
|----------|-----------|
| Should Day-1 runtime auth use a pre-provisioned key path? | **Yes.** `bootstrapAuth(apiKey)` reads key from `ZORIVEST_API_KEY` env var. Key provisioning is admin-only per `04c-api-auth.md:79`. MCP server never mints keys. |
| Should key creation be limited to test harness only? | **Yes.** Integration test `beforeAll` creates a key via `POST /auth/keys` — explicitly labeled as test-only setup. Runtime MCP server assumes key already exists. |

### Verdict

`approved` — both findings resolved, verification clean, plan and task.md are aligned.

---

## Final Recheck — 2026-03-09

### Scope

Rechecked the latest corrected `implementation-plan.md` and `task.md` against the two remaining findings from the prior recheck:

1. runtime auth bootstrap must not mint API keys
2. `task.md` must stay aligned with the corrected implementation plan

### Commands Executed

`Get-Content -Raw docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md`
`Get-Content -Raw docs/execution/plans/2026-03-09-mcp-server-foundation/task.md`
`Get-Content -Raw .agent/context/handoffs/2026-03-09-mcp-server-foundation-plan-critical-review.md`
`git status --short -- docs/execution/plans/2026-03-09-mcp-server-foundation .agent/context/handoffs/2026-03-09-mcp-server-foundation-plan-critical-review.md`
`git diff -- docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md docs/execution/plans/2026-03-09-mcp-server-foundation/task.md`
Numbered line sweeps over:
`docs/execution/plans/2026-03-09-mcp-server-foundation/implementation-plan.md`
`docs/execution/plans/2026-03-09-mcp-server-foundation/task.md`
`docs/build-plan/04c-api-auth.md`
`docs/build-plan/05-mcp-server.md`

### Verification Result

Both remaining findings are resolved.

- **Auth model fixed:** runtime bootstrap now takes a pre-provisioned key and explicitly states that the MCP server does not create keys (`implementation-plan.md:21`, `implementation-plan.md:105`, `implementation-plan.md:106`). That now aligns with the admin-only key-management rule in `04c-api-auth.md` (`04c-api-auth.md:79`, `04c-api-auth.md:83`) and with the shared auth bootstrap requirement that the server unlock before tools function and call `bootstrapAuth` before proxied use (`05-mcp-server.md:198`, `05-mcp-server.md:204`, `05-mcp-server.md:260`, `05-mcp-server.md:283`).
- **Task sync fixed:** `task.md` now includes `eslint.config.mjs` in the scaffold checklist and includes the Phase 4 status-table correction in the `BUILD_PLAN.md` maintenance item (`task.md:7`, `task.md:27`), matching the implementation plan (`implementation-plan.md:81`, `implementation-plan.md:181`, `implementation-plan.md:197`).

### Findings by Severity

None.

### Verdict

`approved`

### Residual Risk

The full HTTP-header extraction model from Phase 5 §5.7 is still explicitly deferred to later MEUs. That is acceptable at plan level because the current draft now distinguishes runtime pre-provisioned-key bootstrap from test-only key creation and no longer conflates the two.
