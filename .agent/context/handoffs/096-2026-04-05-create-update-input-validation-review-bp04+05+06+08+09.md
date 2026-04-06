# Task Handoff Template

## Task

- **Date:** 2026-04-05
- **Task slug:** create-update-input-validation-review
- **Owner role:** reviewer
- **Scope:** Review create/update operations across REST, service, MCP, and UI boundaries; verify whether external inputs are validated before processing; compare current implementation against official Python/FastAPI/Pydantic/Zod guidance.

## Inputs

- User request:
  Review the source code in this project, pay closer attention to CREATE and UPDATE operations, verify that external inputs are asserted/validated before acceptance and processing, perform web research for best practices in the languages/frameworks used here, and produce a review handoff.
- Specs/docs referenced:
  `AGENTS.md`
  `SOUL.md`
  `.agent/context/current-focus.md`
  `.agent/context/known-issues.md`
  `.agent/roles/reviewer.md`
  `.agent/skills/terminal-preflight/SKILL.md`
  `.agent/skills/pre-handoff-review/SKILL.md`
  Official baseline:
  `https://docs.python.org/3/reference/simple_stmts.html`
  `https://fastapi.tiangolo.com/tutorial/body/`
  `https://docs.pydantic.dev/2.0/usage/strict_mode/`
  `https://zod.dev/api`
- Constraints:
  Windows PowerShell P0 redirect-to-file pattern enforced.
  Dirty worktree present before review; do not touch unrelated files.
  Review-only session; no production code changes requested.

## Role Plan

1. researcher
2. tester
3. reviewer
- Optional roles: guardrail not required, coder not used beyond handoff creation

## Coder Output

- Changed files:
  `.agent/context/handoffs/096-2026-04-05-create-update-input-validation-review-bp04+05+06+08+09.md`
- Design notes / ADRs referenced:
  None.
- Commands run:
  `git status --short`
  `Get-ChildItem -Recurse -File`
  `rg -n "create_|update_|patch_" packages api mcp-server ui`
  `rg -n "\\bassert\\b" packages ui mcp-server`
  `rg -n "test_.*(invalid|blank|empty|negative|cron|timezone|status|direction|provider|email)" tests`
- Results:
  Source review completed across API, core services, MCP tools, and UI mutation paths.
  Runtime `assert` is not used as boundary validation in the reviewed create/update paths; the dominant issue is missing or incomplete runtime schema/invariant validation.

## Tester Output

- Commands run:
  `uv run pytest tests/unit/test_api_accounts.py tests/unit/test_api_trades.py tests/unit/test_api_reports.py tests/unit/test_api_plans.py tests/unit/test_api_settings.py tests/unit/test_api_email_settings.py tests/unit/test_api_scheduling.py tests/unit/test_market_data_api.py -q *> C:\Temp\zorivest\review-pytest.txt`
- Pass/fail matrix:
  `pytest`: pass
- Repro failures:
  None in the targeted suite.
- Coverage/test gaps:
  Existing tests cover happy paths and a few enum/status errors, but do not cover most malformed create/update payloads found in this review.
  Missing or weak coverage is visible in:
  `tests/unit/test_api_accounts.py:58-121`
  `tests/unit/test_api_trades.py:175-193`
  `tests/unit/test_api_plans.py:240-310`
  `tests/unit/test_market_data_api.py:207-230`
- Evidence bundle location:
  `C:\Temp\zorivest\review-pytest.txt`
  `C:\Temp\zorivest\validation-tests-search-2.txt`
- FAIL_TO_PASS / PASS_TO_PASS result:
  PASS_TO_PASS only. Result: `127 passed, 1 warning in 14.91s`.
- Mutation score:
  Not run.
- Contract verification status:
  Partial only. The green suite does not verify invalid-input rejection for several create/update boundaries.

## Reviewer Output

- Findings by severity:
  High:
  Account create/update does not fully validate boundary input and can either surface invalid enum input as an unhandled failure or persist weakly validated state. `packages/api/src/zorivest_api/routes/accounts.py:29-45` defines unconstrained request fields; `packages/api/src/zorivest_api/routes/accounts.py:133-143` converts `body.account_type` directly with `AccountType(...)`; `packages/core/src/zorivest_core/application/commands.py:60-76` only validates `account_id` and `name`; `packages/core/src/zorivest_core/services/account_service.py:96-113` rebuilds `Account(**{**account.__dict__, **kwargs})` without rechecking invariants beyond enum coercion.
  High:
  Trade create/update accepts insufficiently constrained external input. `packages/api/src/zorivest_api/routes/trades.py:30-52` exposes plain `str` and unconstrained numeric fields; `packages/core/src/zorivest_core/application/commands.py:18-38` only rejects empty `exec_id` and non-positive `quantity`; `packages/core/src/zorivest_core/services/trade_service.py:23-59` persists `price`, `instrument`, and `account_id` without additional checks; `packages/core/src/zorivest_core/services/trade_service.py:160-179` performs partial-update reconstruction without invariant validation.
  High:
  Trade plan create/update/status patch accepts raw strings for enum-like domain fields and stores them without runtime enforcement. `packages/api/src/zorivest_api/routes/plans.py:23-72` uses plain strings for `direction`, `conviction`, `timeframe`, and `status`; `packages/api/src/zorivest_api/routes/plans.py:180-207` accepts status patch input as plain `str`; `packages/core/src/zorivest_core/services/report_service.py:113-147` builds `TradePlan` from raw dict data; `packages/core/src/zorivest_core/services/report_service.py:181-196` applies `replace(existing, **updates, ...)`; `packages/core/src/zorivest_core/domain/entities.py:115-150` defines `TradePlan` as a dataclass with typed annotations but no runtime validation.
  High:
  Schedule PATCH bypasses the validation path that create/update policy flows already use. `packages/api/src/zorivest_api/routes/scheduling.py:280-289` takes `cron_expression`, `enabled`, and `timezone` directly as optional parameters instead of a validated body model; `packages/core/src/zorivest_core/services/scheduling_service.py:138-148` validates full policy documents with `PolicyDocument(**policy_json)` and `validate_policy(doc)`; `packages/core/src/zorivest_core/services/scheduling_service.py:389-430` mutates nested trigger JSON and saves it without rebuilding the policy document or rerunning validation.
  High:
  Provider configuration and email settings writes accept weakly validated configuration. `packages/api/src/zorivest_api/routes/market_data.py:27-34` and `packages/api/src/zorivest_api/routes/email_settings.py:42-49` define unconstrained request models; `packages/core/src/zorivest_core/services/provider_connection_service.py:251-302` accepts any provided `rate_limit`, `timeout`, and secrets after only checking provider existence; `packages/core/src/zorivest_core/services/email_provider_service.py:68-86` persists SMTP config without validating host, port, security mode, or email shape.
  Medium:
  Watchlist create/update/item add paths allow blank or malformed strings through REST and MCP boundaries. `packages/api/src/zorivest_api/routes/watchlists.py:22-34` uses bare strings; `packages/core/src/zorivest_core/services/watchlist_service.py:31-56`, `packages/core/src/zorivest_core/services/watchlist_service.py:68-91`, and `packages/core/src/zorivest_core/services/watchlist_service.py:109-149` only enforce existence/duplication, not non-empty normalized names or tickers; `mcp-server/src/tools/planning-tools.ts:126-137` and `mcp-server/src/tools/planning-tools.ts:274-289` use unconstrained `z.string()` inputs.
  Medium:
  TypeScript boundary validation is inconsistent, so some clients still forward raw payloads directly to server write paths. `ui/src/renderer/src/hooks/useAccounts.ts:105-136`, `ui/src/renderer/src/features/settings/EmailSettingsPage.tsx:73-78`, and `ui/src/renderer/src/features/settings/MarketDataProvidersPage.tsx:106-122` serialize user input without local schema parsing or normalization. This is less severe than the server defects, but it weakens defense in depth and reduces early error quality.
- Open questions:
  None blocking for the review.
  Assumption: create/update endpoints are intended to reject malformed domain input with 4xx responses instead of accepting it and failing later in service logic or downstream integrations.
- Verdict:
  Changes required.
- Residual risk:
  The project currently relies on a mix of partial command validation, ad hoc service coercion, and happy-path tests. That combination leaves malformed input paths under-specified and weakly enforced.
  The highest-risk pattern is partial update code that reconstructs dataclasses from `kwargs` after boundary parsing, because it bypasses the same invariants that create flows are expected to enforce.
  Passing tests do not materially reduce this risk because they mostly exercise valid payloads plus a small number of enum/status error cases.
- Anti-deferral scan result:
  Review-only session. No new placeholders introduced.

## Guardrail Output (If Required)

- Safety checks:
  Not required for this read-only review.
- Blocking risks:
  None beyond the findings above.
- Verdict:
  Not applicable.

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- Status:
  Review completed. Multiple create/update boundaries do not currently validate external input to the level expected by the stack or by the user request.
- Next steps:
  Introduce explicit boundary schemas for all write paths, with enums and field constraints at the API/MCP/UI edges.
  For Python, do not use `assert` as runtime validation; use Pydantic/FastAPI field constraints, enums, `extra="forbid"` where contracts are closed, and service/domain invariant checks that run in both create and update flows.
  For TypeScript, use Zod parsing at UI/MCP boundaries and prefer strict object schemas for mutation payloads.
  Add regression tests for invalid account type, blank identifiers/names/tickers, non-positive numeric fields, invalid plan status/direction/timeframe, invalid provider timeout/rate limit, invalid email config, and invalid schedule patch cron/timezone.

## Recommended `.agent` Adjustments

- **`AGENTS.md`**
  Add a mandatory **Boundary Input Contract** requirement under Planning Contract and FIC-Based TDD:
  every MEU that touches external input must enumerate all write boundaries (`REST body/query/path`, `MCP tool input`, `UI form payload`, `file import`, `env/config input`) and define, for each boundary, the schema owner, field constraints, enum/format rules, normalization rules, extra-field policy, error mapping, and create/update parity requirements.
  Add an explicit rule that Python `assert` and type annotations alone are not acceptable runtime boundary validation.
  Add a verification rule that partial update paths must enforce the same invariants as create paths unless a source-backed exception is documented.

- **`.agent/workflows/create-plan.md`**
  Extend the Spec Sufficiency Gate to require a **Boundary Inventory Table** in the plan for all external-input MEUs.
  The plan should not be approvable until it identifies every external input surface and documents expected rejection behavior for malformed, missing, out-of-range, and unexpected fields.

- **`.agent/workflows/tdd-implementation.md`**
  Strengthen Step 2 and Step 3 so the FIC and Red phase must include negative tests for:
  blank required strings, invalid enums, malformed format fields, non-positive or out-of-range numerics, unexpected/extra fields, and partial-update parity with create invariants.
  Add an explicit rule that handlers/services may not accept raw `dict` or `kwargs` updates from external input unless those values have already passed boundary validation.

- **`.agent/workflows/meu-handoff.md`**
  Extend the template with a **Boundary Contract Matrix** and **Negative Input Coverage** section.
  Each write-adjacent handoff should show:
  boundary name, schema used, extra-field policy, normalization rules, error codes, and exact tests proving rejection behavior.

- **`.agent/workflows/validation-review.md`**
  Add adversarial checks for:
  whether every external write boundary has an explicit schema,
  whether unknown fields are rejected or intentionally allowed with source-backed rationale,
  whether create and update flows share invariant enforcement,
  and whether invalid inputs produce controlled `4xx` responses instead of downstream exceptions or deferred failures.

- **`.agent/workflows/critical-review-feedback.md`**
  Add a standard review sweep for external-input boundaries in implementation-review mode:
  enumerate all create/update/patch/import surfaces in scope, then verify boundary schema, negative tests, unknown-field handling, and create/update parity before declaring the review complete.

- **`.agent/workflows/planning-corrections.md`**
  Add a dedicated correction category for **boundary validation gaps** so fixes are generalized across sibling write paths rather than patched one endpoint at a time.

- **`.agent/skills/quality-gate/SKILL.md`**
  Add a blocking or near-blocking **boundary validation audit** for touched write surfaces.
  At minimum, the gate should check that:
  write-adjacent API/MCP/UI inputs have explicit schemas,
  negative tests exist for malformed input,
  and partial update paths are covered by tests.
  If automation is added later, this is the right skill to bind it to.

- **`.agent/skills/pre-handoff-review/SKILL.md`**
  Add a required self-review step for external-input work:
  list every boundary touched,
  cite the schema or validator used at that boundary,
  prove at least one rejection test per invalid-input class,
  and confirm no partial update path bypasses create-time invariants.

- **`.agent/docs/code-quality.md`**
  Expand `Every function must have input validation` into boundary-specific standards:
  validate at the first trust boundary,
  reject or explicitly document unknown fields,
  do not rely on dataclass/type-hint annotations as runtime validation,
  do not use `replace(...)` or `Model(**{**old, **updates})` on external input without prior validation,
  and keep create/update invariant logic centralized.

- **`.agent/docs/testing-strategy.md`**
  Add a **write-boundary test matrix** for API/MCP/UI/config work.
  Required cases should include:
  valid create, valid update, invalid enum, blank required field, malformed format field, non-positive/out-of-range numeric, extra field handling, missing-entity mapping, and create/update parity.

- **`.agent/roles/reviewer.md`**
  Make boundary validation an explicit reviewer responsibility, not just a generic “boundary violation” phrase.
  Reviewer output should call out:
  missing schemas,
  unconstrained write DTOs,
  silent coercion,
  unknown-field acceptance,
  and update paths that reconstruct domain objects without revalidation.

## Research-Backed Baseline

- Python:
  Official Python docs specify that `assert` is a debugging aid and generated bytecode is omitted when optimization is requested. Inference: production boundary validation must not depend on `assert`.
- FastAPI / Pydantic:
  FastAPI’s request-body model flow is designed to validate and parse inbound data before handler logic runs. Pydantic provides strict mode and constrained field types for runtime validation rather than post-hoc coercion.
- TypeScript / Zod:
  Zod’s schema parsing model is the appropriate boundary validation mechanism for UI and MCP mutation inputs; strict object schemas should be preferred where unexpected keys should be rejected.

## Research Notes

- Source links:
  `https://docs.python.org/3/reference/simple_stmts.html`
  `https://fastapi.tiangolo.com/tutorial/body/`
  `https://docs.pydantic.dev/2.0/usage/strict_mode/`
  `https://zod.dev/api`

---

## Corrections Applied — 2026-04-05

### Category B: `.agent` Process Hardening (12 changes — applied)

All 12 recommended `.agent` adjustments from the review have been applied:

| # | File | Change |
|---|------|--------|
| B1 | `AGENTS.md` | Added mandatory Boundary Input Contract section under Planning Contract |
| B2 | `create-plan.md` | Added Boundary Inventory Table requirement to Spec Sufficiency Gate |
| B3 | `tdd-implementation.md` | Added boundary contract and negative input test requirements to FIC (Step 2) and Red Phase (Step 3) |
| B4 | `meu-handoff.md` | Added Boundary Contract section to handoff template |
| B5 | `validation-review.md` | Added AV-7 (boundary schema), AV-8 (create/update parity), AV-9 (invalid→4xx) checks |
| B6 | `critical-review-feedback.md` | Added IR-6 (boundary validation coverage) to Implementation Review Checklist |
| B7 | `planning-corrections.md` | Added "boundary validation gap" correction category to Step 2b |
| B8 | `quality-gate/SKILL.md` | Added blocking check #11 (boundary validation audit) |
| B9 | `pre-handoff-review/SKILL.md` | Added Step 6b (Boundary Validation Audit, Pattern 11) |
| B10 | `code-quality.md` | Expanded input validation into Boundary Validation Standards with forbidden patterns |
| B11 | `testing-strategy.md` | Added Write-Boundary Test Matrix with 9 required test categories |
| B12 | `reviewer.md` | Added item 8 with specific boundary validation responsibilities |

### Category A: Code-Level Fixes (7 findings — deferred)

Findings F1–F7 (code-level validation gaps) are tracked in `known-issues.md` under `[BOUNDARY-GAP]`. These require a dedicated input-validation-hardening project via `/create-plan` with full TDD discipline.

### Verification

```
rg -n "Boundary" AGENTS.md .agent/workflows/ .agent/skills/ .agent/docs/ .agent/roles/
→ 15 matches across 10 files (all 12 corrections confirmed present)

rg -n "AV-7|AV-8|AV-9|IR-6" .agent/workflows/
→ 4 matches (all new checks confirmed)
```

### Verdict

Category B corrections: **complete**.
Category A code fixes: **deferred** to dedicated project (tracked in `known-issues.md`).
Overall review status: **partially resolved** — process hardening applied, code changes pending.
