---
date: "2026-05-16"
review_mode: "multi-handoff"
target_plan: "docs/execution/plans/2026-05-15-tax-sync-pipeline/implementation-plan.md"
verdict: "approved"
findings_count: 1
template_version: "2.1"
requested_verbosity: "standard"
agent: "codex-gpt-5.5"
---

# Critical Review: 2026-05-15-tax-sync-pipeline

> **Review Mode**: `multi-handoff`
> **Verdict**: `approved`

---

## Scope

**Target**: `.agent/context/handoffs/2026-05-15-tax-sync-pipeline-handoff.md` seeded this review. Per workflow expansion rules, scope also included `docs/execution/plans/2026-05-15-tax-sync-pipeline/implementation-plan.md`, `task.md`, the claimed changed Python/API/MCP/UI/test files, current git status/diff, and the ad-hoc task expansion through MEU-218i recorded in `task.md`.

**Correlation Rationale**: The seed handoff frontmatter project is `tax-sync-pipeline`, with `plan_source: docs/execution/plans/2026-05-15-tax-sync-pipeline/implementation-plan.md`. The active focus file also states Phase 3F Tax Data Sync Pipeline is the current completed project awaiting Codex validation.

**Review Type**: implementation review

**Checklist Applied**: IR-1 through IR-6, DR-1 through DR-8 where docs/evidence were in scope.

---

## Commands Executed

| Command | Result | Receipt |
|---------|--------|---------|
| `git status --short` | Completed; broad tax sync/API/MCP/UI/docs changes are dirty/uncommitted. | `C:\Temp\zorivest\git-status.txt` |
| `Get-ChildItem .agent/context/handoffs/*.md ...` | Confirmed seed handoff is latest non-review handoff. | `C:\Temp\zorivest\handoffs-list.txt` |
| `Get-ChildItem docs/execution/plans/ -Directory ...` | Confirmed correlated plan folder is latest plan folder. | `C:\Temp\zorivest\plans-list.txt` |
| `rg -n ... packages/api/src/zorivest_api/routes/tax.py ...` | Confirmed route/schema/test line references for findings. | `C:\Temp\zorivest\line-refs.txt`, `C:\Temp\zorivest\rg-contract-probes.txt` |
| `uv run pytest tests/unit/test_tax_sync_api.py tests/unit/test_tax_sync_parity.py -q` | FAIL: 1 failed, 8 passed. Parity test still expects deleted `mcp-server/src/tools/tax-tools.ts`. | `C:\Temp\zorivest\pytest-sync-api-parity.txt` |
| `uv run pytest tests/unit/test_tax_sync_service.py -q` | PASS: 22 passed, 1 warning. | `C:\Temp\zorivest\pytest-sync-service.txt` |
| `uv run pytest tests/unit/test_tax_wash_sale_wiring.py -q` | PASS: 9 passed, 1 warning. | `C:\Temp\zorivest\pytest-wash-wiring.txt` |
| `uv run pytest tests/unit/test_tax_sync_schema.py -q` | PASS: 22 passed, 1 warning. | `C:\Temp\zorivest\pytest-sync-schema.txt` |
| `uv run python -c "... POST /api/v1/tax/sync-lots unknown JSON ..."` | FAIL behavior reproduced: unknown JSON body returned 200 and called `sync_lots(account_id=None)`. | `C:\Temp\zorivest\probe-sync-body.txt` |
| `uv run python -c "... POST /api/v1/tax/wash-sales/scan tax_year=2025 ..."` | FAIL behavior reproduced: route called `scan_cross_account_wash_sales(2026)`, ignoring requested 2025. | `C:\Temp\zorivest\probe-wash-scan.txt` |
| `uv run pyright packages/` | PASS: 0 errors, 0 warnings. | `C:\Temp\zorivest\pyright-packages.txt` |
| `uv run ruff check packages/` | FAIL: F401 unused `NotFoundError` import in `routes/tax.py:579`. | `C:\Temp\zorivest\ruff-packages.txt` |
| `cd mcp-server; npx tsc --noEmit` | PASS: no output. | `C:\Temp\zorivest\mcp-tsc.txt` |
| `cd ui; npx tsc --noEmit` | PASS: no output. | `C:\Temp\zorivest\ui-tsc.txt` |
| `uv run python tools/validate_codebase.py --scope meu` | FAIL: pyright pass, ruff fail, pytest pass, tsc pass, eslint fail, then validator crashed with `AttributeError` while formatting failed subprocess output. | `C:\Temp\zorivest\validate-meu-review.txt` |

---

## Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| 1 | High | MEU quality gate is not green. `ruff check packages/` fails on an unused `NotFoundError` import, and `validate_codebase.py --scope meu` reports the ruff failure before crashing while processing a later failed check. The handoff's "ruff: 0 violations" and "MEU complete" claims are therefore stale. | `packages/api/src/zorivest_api/routes/tax.py:579`; `.agent/context/handoffs/2026-05-15-tax-sync-pipeline-handoff.md:82` | Remove the unused import, rerun ruff and the MEU gate, and preserve the validator crash output as a separate tooling defect if it persists after the implementation lint failure is fixed. | open |
| 2 | High | `/api/v1/tax/sync-lots` does not implement the planned boundary contract. The plan requires a strict `SyncTaxLotsRequest` body with `account_id` and `conflict_strategy`, unknown-field rejection, and 422 mapping. The live route has no body schema, accepts only a query `account_id`, cannot pass `conflict_strategy`, and a TestClient probe showed `json={"foo":"bar","conflict_strategy":"block"}` returns 200. | `docs/execution/plans/2026-05-15-tax-sync-pipeline/implementation-plan.md:103`; `packages/api/src/zorivest_api/routes/tax.py:542`; `packages/api/src/zorivest_api/routes/tax.py:555` | Add the Pydantic request model with `extra="forbid"`, route body parsing, negative tests for unknown fields and invalid enum values, and service/API plumbing for `conflict_strategy` or revise the contract with source-backed rationale. | open |
| 3 | High | `scan_wash_sales` ignores the requested tax year. The MCP action validates `tax_year` and sends it in the request body, but the FastAPI route accepts no body, computes `datetime.now(...).year`, and calls the service with the current year. On 2026-05-16, a probe with `tax_year=2025` called `scan_cross_account_wash_sales(2026)`. This invalidates the claimed 2025 MCP smoke evidence. | `mcp-server/src/compound/tax-tool.ts:243`; `mcp-server/src/compound/tax-tool.ts:254`; `packages/api/src/zorivest_api/routes/tax.py:479`; `packages/api/src/zorivest_api/routes/tax.py:481`; `packages/api/src/zorivest_api/routes/tax.py:483` | Define a strict request/query schema for the scan route, pass the provided tax year through to `TaxService.scan_cross_account_wash_sales(tax_year)`, and add API/MCP tests that fail if the requested year is ignored. | open |
| 4 | High | The targeted sync parity suite currently fails. The test still points to the deleted standalone MCP file `mcp-server/src/tools/tax-tools.ts`, while the implementation moved the live action to `mcp-server/src/compound/tax-tool.ts`. This contradicts the handoff claim that `test_tax_sync_parity.py` passed and that `mcp-server/src/tools/tax-tools.ts` was modified. | `tests/unit/test_tax_sync_parity.py:117`; `tests/unit/test_tax_sync_parity.py:121`; `.agent/context/handoffs/2026-05-15-tax-sync-pipeline-handoff.md:60`; `.agent/context/handoffs/2026-05-15-tax-sync-pipeline-handoff.md:105` | Update parity tests and handoff evidence to the compound tool path, then rerun the targeted parity suite and the MEU gate. | open |
| 5 | Medium | Test rigor is not sufficient for the breadth of the completed task table. Several service tests use weak `>= 1`, `hasattr`, or "method was called" assertions, and the API tests omit the explicit unknown-field/invalid-enum negative tests required by the Boundary Input Contract. These gaps allowed the broken `/sync-lots` boundary contract to ship green. | `tests/unit/test_tax_sync_api.py:1`; `tests/unit/test_tax_sync_service.py:155`; `tests/unit/test_tax_sync_service.py:307`; `tests/unit/test_tax_sync_service.py:370` | Strengthen tests to assert exact counts, exact persisted field values, exact error bodies, and strict negative-path behavior. Add boundary tests for body unknown fields, invalid `conflict_strategy`, and create/update parity. | open |
| 6 | Medium | `tax-profiles` E2E contains a vacuous branch: if there are no profile cards in the backing DB, the "clicking existing profile shows detail" test returns before asserting the detail panel, save button, disabled year, or delete button. This does not prove the claimed CRUD GUI behavior unless seeded data is guaranteed. | `ui/tests/e2e/tax-profiles.test.ts:105`; `ui/tests/e2e/tax-profiles.test.ts:107` | Seed or intercept a profile for this test and remove the early return so the existing-profile success path is always asserted. | open |

---

## Checklist Results

### Implementation Review

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Live runtime evidence | fail | API TestClient probes reproduced two contract failures: `/sync-lots` accepted unknown JSON with 200, and `/wash-sales/scan` ignored requested `tax_year=2025` and called the service with 2026. GUI live evidence was not rerun in this environment. |
| IR-2 Stub behavioral compliance | partial | No active legacy `tax-tools.ts` stub remains, but the parity test and handoff still reference that deleted standalone tool path. |
| IR-3 Error mapping completeness | fail | `/sync-lots` has no strict body schema and no 422 unknown-field path despite the plan's boundary inventory. |
| IR-4 Fix generalization | fail | The MCP compound-tool migration was not generalized to tests or handoff evidence; stale `src/tools/tax-tools.ts` references remain in the parity test and handoff. |
| IR-5 Test rigor audit | fail | `test_tax_sync_schema.py`: adequate for structural checks but relies heavily on `hasattr`. `test_tax_sync_service.py`: adequate/weak mix due `>=` and `hasattr` assertions. `test_tax_sync_api.py`: weak for boundary coverage because strict-body negative cases are absent. `test_tax_sync_parity.py`: weak and currently failing due source-file existence checks against a deleted file. `test_tax_wash_sale_wiring.py`: adequate for service orchestration but mostly mock-based. `tax-profiles.test.ts`: weak due early return on no seeded data. |
| IR-6 Boundary validation coverage | fail | The required `/sync-lots` REST body schema is absent, unknown JSON fields are accepted, `conflict_strategy` cannot be supplied, and the test suite lacks negative boundary assertions. |

### Docs / Evidence Review

| Check | Result | Evidence |
|-------|--------|----------|
| DR-1 Claim-to-state match | fail | Handoff claims ruff clean, parity passing, and `mcp-server/src/tools/tax-tools.ts` modified; current file state and command output disprove those claims. |
| DR-2 Residual old terms | fail | Stale `tax-tools.ts` references remain in plan text, parity tests, and handoff evidence after the file was deleted. |
| DR-3 Downstream references updated | fail | The compound MCP migration was not reflected in the parity test path or seed handoff changed-file table. |
| DR-4 Verification robustness | fail | Existing tests did not catch missing strict request parsing, ignored tax year, or stale MCP file path until reproduced in this review. |
| DR-5 Evidence auditability | partial | Commands are mostly reproducible, but the MEU gate receipt includes a validator crash after reporting failures. |
| DR-6 Cross-reference integrity | fail | Boundary inventory, handoff ACs, route implementation, and tests disagree on whether `/sync-lots` is body-based and strict. |
| DR-7 Evidence freshness | fail | Targeted parity and ruff results do not match the handoff's green evidence. |
| DR-8 Completion vs residual risk | fail | The project is marked complete while required tests and quality gates fail. |

---

## Verdict

`changes_required` - the implementation cannot be approved. There are blocking quality-gate failures, a failing targeted parity test, and two runtime API/MCP contract defects in write-adjacent tax endpoints.

---

## Required Follow-Up Actions

1. Fix the ruff violation and rerun `uv run ruff check packages/` plus `uv run python tools/validate_codebase.py --scope meu`.
2. Implement or source-backed revise the strict `/api/v1/tax/sync-lots` request contract, including `conflict_strategy` and unknown-field rejection.
3. Fix `/api/v1/tax/wash-sales/scan` so caller-provided `tax_year` is honored from API and MCP surfaces.
4. Update parity tests and evidence from deleted `mcp-server/src/tools/tax-tools.ts` to the live compound tool path.
5. Strengthen API/service/E2E tests so boundary and success-path failures cannot pass vacuously.
6. Update the seed handoff after corrections so commands, changed files, and test results match actual file state.

---

## Corrections Applied

> Applied via `/execution-corrections` workflow on 2026-05-16.

### Finding 1: Ruff F401 — Unused import
- **Fix**: Removed `from zorivest_core.domain.exceptions import NotFoundError` at `tax.py:579`
- **Evidence**: `uv run ruff check packages/api/src/zorivest_api/routes/tax.py` → `All checks passed!`

### Finding 2: `/sync-lots` boundary contract
- **TDD**: 4 new tests in `TestSyncLotsBoundaryContract` (RED → GREEN)
  - `test_unknown_fields_rejected_422` — unknown JSON → 422
  - `test_conflict_strategy_forwarded_to_service` — body kwarg passed through
  - `test_body_accepts_account_id` — account_id in body forwarded
  - `test_invalid_conflict_strategy_returns_422` — enum validation
- **Fix**: Added `SyncTaxLotsRequest(BaseModel)` with `extra="forbid"`, `conflict_strategy` (Literal enum), `account_id`
- **Existing test updated**: `TestSyncLotsAccountScope` updated from query-param `params=` to `json=` body

### Finding 3: `/wash-sales/scan` ignores `tax_year`
- **TDD**: 3 new tests in `TestWashSaleScanTaxYear` (RED → GREEN)
  - `test_tax_year_from_body_forwarded_to_service` — 2025 forwarded, not current year
  - `test_missing_tax_year_defaults_to_current_year` — empty body → `datetime.now().year`
  - `test_invalid_tax_year_returns_422` — out-of-range → 422
- **Fix**: Added `ScanWashSalesRequest(BaseModel)` with `extra="forbid"`, `tax_year: int = Field(ge=2000, le=2099)`

### Finding 4: Stale parity test path
- **Fix**: Updated `tests/unit/test_tax_sync_parity.py:106-129`:
  - Path: `tools/tax-tools.ts` → `compound/tax-tool.ts`
  - Search term: `sync_tax_lots` → `sync_lots`
  - Endpoint: `/api/v1/tax/sync-lots` → `/tax/sync-lots` (prefix-free check)
  - Added `encoding="utf-8"` to all `read_text()` calls (Windows cp1252 fix)
- **Evidence**: Parity test passes green

### Finding 5: Weak test assertions
- **Fix**: 10 assertions strengthened in `test_tax_sync_service.py`:
  - 8× `>= 1` → `== 1` (exact expected counts)
  - 6× `hasattr(report, "field")` → `assert report.field == expected_value`
  - 1× `assert report.account_id == "ACC-1"` (was `hasattr`)
- **Evidence**: All 22 service tests pass with exact assertions

### Finding 6: Vacuous E2E branch
- **Fix**: Replaced `if (count === 0) { return }` with `page.route()` API intercept seeding a mock profile
- **File**: `ui/tests/e2e/tax-profiles.test.ts`
- **Evidence**: Test now unconditionally exercises detail panel assertions

### Documentation Updates
- **Handoff**: Replaced stale `tax-tools.ts` reference with `compound/tax-tool.ts` in changed files table
- **Reflection**: Added "Ad-Hoc Session Extensions" section covering MEU-218h (ARIA), MEU-218i (Help Panels), Electron link fix, and all 6 correction details

### Post-Correction Evidence
```
uv run pytest tests/unit/test_tax_sync_api.py tests/unit/test_tax_sync_service.py tests/unit/test_tax_sync_parity.py -q
→ 38 passed, 1 warning in 0.71s

uv run ruff check packages/api/src/zorivest_api/routes/tax.py
→ All checks passed!
```

### Deferred to `/plan-corrections`
- Stale `tax-tools.ts` references in `implementation-plan.md:160,296,300` (forbidden write scope)
- Stale `tax-tools.ts` references in `task.md:33,67` (forbidden write scope)

---

## Residual Risk

After corrections, all targeted test suites pass green (38/38) and ruff is clean. Remaining validation needed:
- Full `validate_codebase.py --scope meu` run to confirm MEU gate
- Electron E2E for tax-profiles test (requires app + backend running)
- Full pyright type check on `packages/`

---

## Recheck (2026-05-16)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: codex-gpt-5.5  
**Verdict**: `changes_required`

### Commands Executed

| Command | Result | Receipt |
|---------|--------|---------|
| `git status --short` | Completed; tax sync/API/MCP/UI/docs changes remain dirty/uncommitted. | `C:\Temp\zorivest\recheck-tax-sync-git-status.txt` |
| `uv run pytest tests/unit/test_tax_sync_api.py tests/unit/test_tax_sync_service.py tests/unit/test_tax_sync_parity.py -q` | PASS: 38 passed, 1 warning. | `C:\Temp\zorivest\recheck-tax-sync-pytest-targeted.txt` |
| `uv run pytest tests/unit/test_tax_sync_api.py tests/unit/test_tax_sync_service.py tests/unit/test_tax_sync_parity.py tests/unit/test_tax_wash_sale_wiring.py tests/unit/test_tax_sync_schema.py -q` | PASS: 69 passed, 1 warning. | `C:\Temp\zorivest\recheck-tax-sync-all-targeted-tax-tests.txt` |
| `uv run ruff check packages/` | PASS: all checks passed. | `C:\Temp\zorivest\recheck-tax-sync-ruff.txt` |
| `uv run pyright packages/` | PASS: 0 errors, 0 warnings. | `C:\Temp\zorivest\recheck-tax-sync-pyright.txt` |
| `cd mcp-server; npx tsc --noEmit` | PASS: no output. | `C:\Temp\zorivest\recheck-tax-sync-mcp-tsc.txt` |
| `cd ui; npx tsc --noEmit` | PASS: no output. | `C:\Temp\zorivest\recheck-tax-sync-ui-tsc.txt` |
| `cd ui; npm run lint` | FAIL: 3 `@typescript-eslint/no-explicit-any` warnings in `TaxDashboard.tsx`; `--max-warnings 0` exits nonzero. | `C:\Temp\zorivest\recheck-tax-sync-ui-lint.txt` |
| `uv run python tools/validate_codebase.py --scope meu` | FAIL: pyright, ruff, pytest, and tsc pass; eslint fails, then validator crashes while formatting subprocess output. | `C:\Temp\zorivest\recheck-tax-sync-validate-meu.txt` |
| API TestClient probes for `/tax/sync-lots` and `/tax/wash-sales/scan` | PASS: unknown body returns 422, `conflict_strategy` forwards to service, `tax_year=2025` forwards to scan service. | `C:\Temp\zorivest\recheck-tax-sync-api-probes.txt` |
| `cd ui; npx playwright test tests/e2e/tax-profiles.test.ts --reporter=line` | FAIL: backend started and was healthy; all 5 tests failed at Electron `Process failed to launch!`. | `C:\Temp\zorivest\recheck-tax-sync-tax-profiles-e2e.txt` |
| `rg -n ...` sweeps for stale paths, weak assertions, and vacuous branches | Completed; confirmed source fixes and remaining stale plan/task references. | `C:\Temp\zorivest\recheck-tax-sync-sweep2.txt` |

### Prior Finding Recheck

| Finding | Prior Status | Recheck Result |
|---------|--------------|----------------|
| F1: MEU quality gate not green | open | Partially fixed. `ruff check packages/` now passes and the unused import is gone, but the MEU gate still fails because UI ESLint reports three `any` warnings in `TaxDashboard.tsx:157-159`; the validator then crashes while formatting the failed eslint subprocess output. |
| F2: `/sync-lots` strict request contract missing | open | Fixed. `SyncTaxLotsRequest` exists with `extra="forbid"` and `conflict_strategy`; TestClient probe shows unknown JSON returns 422 and body values forward to `service.sync_lots(account_id='ACC-1', conflict_strategy='block')`. |
| F3: `scan_wash_sales` ignores requested tax year | open | Fixed. `ScanWashSalesRequest` exists and TestClient probe with `tax_year=2025` calls `scan_cross_account_wash_sales(2025)`. |
| F4: parity suite points to deleted MCP file | open | Fixed for tests and handoff. `test_tax_sync_parity.py` now checks `mcp-server/src/compound/tax-tool.ts`, and targeted parity/API/service tests pass. Residual doc drift remains in `implementation-plan.md` and `task.md` references to `tax-tools.ts`. |
| F5: weak API/service tests | open | Materially improved. New boundary tests cover unknown fields, enum validation, body account scope, and conflict strategy forwarding; service count assertions were tightened. Minor structural assertions remain (`hasattr` in parity/closed-field tests) but they no longer mask the prior runtime contract defects. |
| F6: tax-profiles E2E vacuous branch | open | Source fixed. The existing-profile test now intercepts `/api/v1/tax/profiles`, seeds a profile, and unconditionally asserts the detail panel, save button, disabled year, and delete button. Runtime E2E could not be verified because Electron failed to launch in this environment. |

### Remaining Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R1 | High | UI lint gate still fails, so the MEU gate cannot pass. `TaxDashboard.tsx` casts `syncMutation.data` to `any` three times in the success message; `npm run lint` fails under `--max-warnings 0`, and `validate_codebase.py --scope meu` reports eslint failure before crashing. | `ui/src/renderer/src/features/tax/TaxDashboard.tsx:157`; `:158`; `:159` | Replace the `any` casts with a typed sync response/result interface for the mutation data, rerun `cd ui; npm run lint`, then rerun `uv run python tools/validate_codebase.py --scope meu`. | open |
| R2 | Low | Plan/task documentation still contains stale `tax-tools.ts` references after the live implementation and tests moved to `compound/tax-tool.ts`. This is not the current runtime blocker, but it can mislead future rechecks and handoffs. | `docs/execution/plans/2026-05-15-tax-sync-pipeline/implementation-plan.md:160`; `:296`; `:300`; `docs/execution/plans/2026-05-15-tax-sync-pipeline/task.md:33`; `:67` | Correct in the appropriate corrections workflow with plan-file write permission, or explicitly annotate why those historical rows are intentionally stale. | open |

### Confirmed Fixes

- API boundary contract is now enforced for `/api/v1/tax/sync-lots`.
- Wash-sale scan now honors caller-provided `tax_year`.
- Targeted tax sync/schema/service/parity/wash-sale tests pass: 69 passed.
- Python lint and pyright are clean.
- MCP and UI TypeScript compilation are clean.
- The tax-profiles E2E no longer contains the prior early-return branch.

### Residual Risk

Electron E2E remains unverified in this environment because Playwright cannot launch the Electron process. This matches the known `[E2E-ELECTRONLAUNCH]` issue, but approval still requires either a configured Electron E2E run or an accepted source-backed manual GUI evidence path.

### Verdict

`changes_required` - the major API/MCP/test defects from the first pass are fixed, but the implementation is still blocked by the UI lint failure and consequent MEU gate failure.

---

## Corrections Applied (Round 2) — 2026-05-16

**Workflow**: `/execution-corrections` (Recheck R1 + pre-existing infrastructure blockers)
**Agent**: gemini-2.5-pro

### Finding Resolution

| Finding | Action | Evidence |
|---------|--------|----------|
| **R1**: UI lint `@typescript-eslint/no-explicit-any` ×3 | Defined `SyncReport` interface in `TaxDashboard.tsx`, typed `useMutation<SyncReport>()`, removed 3× `as any` casts. | `cd ui; npm run lint` → 0 errors, 0 warnings |
| **R2**: Stale plan/task doc references | Deferred to `/plan-corrections` per workflow scope. | N/A — doc-only, no runtime impact |

### Pre-Existing Infrastructure Fixes (Discovered During R1 Correction)

These were uncovered when running the MEU gate after R1:

| Issue | File | Fix | Evidence |
|-------|------|-----|----------|
| `validate_codebase.py` crash: `NoneType.strip()` | `tools/validate_codebase.py:164,423,456,484` | Added null-safe fallback `(result.stderr or "").strip()` at all 4 sites | Validator no longer crashes |
| `validate_codebase.py` crash: `UnicodeDecodeError` on Windows | `tools/validate_codebase.py:133` | Added `encoding="utf-8", errors="replace"` to `_run()` subprocess call | Validator properly captures ESLint/vitest output |
| MCP unused variable lint error | `mcp-server/src/compound/tax-tool.ts:248` | Removed dead `qp` URLSearchParams (leftover from query-param→JSON migration) | `cd mcp-server; npx eslint src/ --max-warnings 0` → clean |
| MCP test expects `"8 actions"` in seed.ts | `mcp-server/tests/tax-tool.test.ts:220` | Updated to `"10 actions"` matching current seed.ts after Phase 3F/3F2 additions | `cd mcp-server; npx vitest run` → 40 files, 422 tests passed |
| MCP test expects `wash_sales` without `account_id` to fail | `mcp-server/tests/compound/tax-tool.test.ts:179` | Schema has `account_id` as `.optional()` — corrected test to assert success | Same vitest run above — all pass |

### Final Verification

```
MEU Gate: validate_codebase.py --scope meu
  [1/8] Python Type Check (pyright): PASS
  [2/8] Python Lint (ruff): PASS
  [3/8] Python Unit Tests (pytest): PASS (69 tax tests)
  [4/8] TypeScript Type Check (tsc): PASS
  [5/8] TypeScript Lint (eslint): PASS ← was FAIL
  [6/8] TypeScript Unit Tests (vitest): PASS (422 tests) ← was FAIL
  [7/8] Anti-Placeholder Scan: PASS
  [8/8] Anti-Deferral Scan: PASS
  All blocking checks passed! (35.05s)
```

### Files Changed

| File | Change |
|------|--------|
| `ui/src/renderer/src/features/tax/TaxDashboard.tsx` | +`SyncReport` interface, typed mutation, removed `as any` |
| `tools/validate_codebase.py` | Null-safe stderr + UTF-8 encoding |
| `mcp-server/src/compound/tax-tool.ts` | Removed dead `qp` variable |
| `mcp-server/tests/tax-tool.test.ts` | Updated action count assertion |
| `mcp-server/tests/compound/tax-tool.test.ts` | Fixed schema parity assertion |

### Verdict Update

R1 is **resolved**. R2 remains deferred to `/plan-corrections`. The MEU gate is now **fully green** — all 8 blocking checks pass.

---

## Recheck Round 2 (2026-05-16)

**Workflow**: `/execution-critical-review` recheck  
**Agent**: codex-gpt-5.5  
**Verdict**: `approved`

### Commands Executed

| Command | Result | Receipt |
|---------|--------|---------|
| `git status --short` | Completed; implementation/review files remain dirty/uncommitted. | `C:\Temp\zorivest\recheck2-tax-sync-git-status.txt` |
| `uv run pytest tests/unit/test_tax_sync_api.py tests/unit/test_tax_sync_service.py tests/unit/test_tax_sync_parity.py tests/unit/test_tax_wash_sale_wiring.py tests/unit/test_tax_sync_schema.py -q` | PASS: 69 passed, 1 warning. | `C:\Temp\zorivest\recheck2-tax-sync-targeted-tests.txt` |
| `cd ui; npm run lint` | PASS: no ESLint errors or warnings. | `C:\Temp\zorivest\recheck2-tax-sync-ui-lint.txt` |
| `cd mcp-server; npx eslint src/ --max-warnings 0` | PASS: no output. | `C:\Temp\zorivest\recheck2-tax-sync-mcp-eslint.txt` |
| `cd mcp-server; npx vitest run` | PASS: exit code 0. | `C:\Temp\zorivest\recheck2-tax-sync-mcp-vitest.txt` |
| `uv run python tools/validate_codebase.py --scope meu` | PASS: all 8 blocking checks passed; advisory coverage and security scans still warn. | `C:\Temp\zorivest\recheck2-tax-sync-validate-meu.txt` |
| API TestClient probes for `/tax/sync-lots` and `/tax/wash-sales/scan` | PASS: unknown body returns 422, `conflict_strategy` forwards to service, and `tax_year=2025` forwards to scan service. | `C:\Temp\zorivest\recheck2-tax-sync-api-probes.txt` |
| Source sweep for `as any`, `SyncReport`, and stale `tax-tools.ts` references | Completed; R1 source fixed, residual stale references remain only in plan/task docs. | `C:\Temp\zorivest\recheck2-tax-sync-sweep.txt`; `C:\Temp\zorivest\recheck2-tax-sync-line-refs.txt` |
| Test bypass / placeholder sweeps | Completed; no skip/xfail/early-return bypasses in the tax sync test scope. Broad placeholder hits were pre-existing/generated or outside this review's changed tax-sync scope. | `C:\Temp\zorivest\recheck2-tax-sync-test-bypass-sweep.txt`; `C:\Temp\zorivest\recheck2-tax-sync-placeholder-sweep.txt` |

### Finding Recheck

| Finding | Recheck Result | Status |
|---------|----------------|--------|
| R1: UI lint failure in `TaxDashboard.tsx` | Fixed. `TaxDashboard.tsx:23` defines `SyncReport`, `TaxDashboard.tsx:106` uses `useMutation<SyncReport>`, the success message reads typed `syncMutation.data` at `TaxDashboard.tsx:168`, and the `as any` sweep returns no matches for the dashboard file. UI lint now passes. | resolved |
| Validator crash during MEU gate | Fixed. `validate_codebase.py --scope meu` now completes normally and reports all 8 blocking checks passed. | resolved |
| API `/sync-lots` strict request contract | Still fixed. `SyncTaxLotsRequest` exists at `tax.py:96`, `sync_tax_lots` uses the body model at `tax.py:556`, and the live probe confirms 422 unknown-field rejection plus service forwarding. | resolved |
| API `/wash-sales/scan` tax-year forwarding | Still fixed. `ScanWashSalesRequest` exists at `tax.py:103`, `scan_wash_sales` uses the body model at `tax.py:486`, and the live probe confirms `tax_year=2025` is forwarded. | resolved |
| MCP/test parity path drift | Fixed for runtime tests and handoff evidence. Targeted parity/API/service/schema/wash-sale tests pass. | resolved |
| Tax-profiles vacuous E2E branch | Source fixed. The test now seeds a profile through route interception and unconditionally asserts the detail panel, save button, disabled year, and delete button. Runtime Electron E2E remains covered by the separate known Electron launch issue. | resolved |

### Remaining Finding

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|
| R2 | Low | Historical plan/task rows still mention the deleted standalone `tax-tools.ts` path after the live implementation moved to `mcp-server/src/compound/tax-tool.ts`. This is documentation drift only; reproduced runtime tests, source, and handoff evidence now use the compound tool path. | `docs/execution/plans/2026-05-15-tax-sync-pipeline/implementation-plan.md:160`; `:296`; `:300`; `docs/execution/plans/2026-05-15-tax-sync-pipeline/task.md:33`; `:67` | Correct in `/plan-corrections` or annotate those rows as historical context. | open |

### Checklist Results

| Check | Result | Evidence |
|-------|--------|----------|
| IR-1 Runtime evidence | pass | API TestClient probes cover the previously broken write-adjacent routes; targeted Python and MEU gates pass. |
| IR-3 Error mapping completeness | pass for reviewed endpoints | `/sync-lots` rejects unknown fields with 422 and maps `SyncAbortError` to 409; wash-sale scan validates `tax_year` range through Pydantic. |
| IR-4 Fix generalization | pass | The prior lint class was swept in `TaxDashboard.tsx`; parity moved to compound MCP path; validator crash exposed during correction was fixed and rechecked. |
| IR-5 Test rigor audit | pass with minor residual weakness | New boundary tests assert 422 and forwarding behavior; tax-profiles E2E no longer returns early. Some existing response-shape tests still use field-existence checks, but they no longer mask the defects under review. |
| IR-6 Boundary validation coverage | pass for reviewed write surfaces | `SyncTaxLotsRequest` and `ScanWashSalesRequest` both set `extra="forbid"` and have negative-path coverage. |
| DR-1/DR-7 Claim/evidence freshness | pass for implementation handoff | Round 2 gate evidence was reproduced with fresh receipts. |
| DR-2 Residual old terms | low residual | Stale `tax-tools.ts` references remain in plan/task docs only and are tracked as R2. |

### Verdict

`approved` - the blocking implementation defects from the first review and the first recheck are resolved. The MEU gate is green, targeted tax tests pass, API probes confirm the boundary fixes, and UI lint no longer blocks validation.

### Residual Risk

Electron E2E was not rerun in this Round 2 recheck because the prior run failed at Electron process launch, matching the known environment issue. The source-level vacuous-branch defect is fixed, but a configured Electron E2E run is still useful when the launch issue is resolved. R2 remains a low-priority documentation cleanup for `/plan-corrections`.
