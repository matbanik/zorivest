# 2026-03-27 Meta-Reflection — Account Management GUI

> **Date**: 2026-03-27
> **MEU(s) Completed**: MEU-71a (`account-gui`)
> **Plan Source**: `/create-plan` workflow → `/planning-corrections` → `/tdd-implementation`

---

## Execution Trace

### Friction Log

1. **What took longer than expected?**
   Three runtime bugs discovered during live GUI testing consumed ~40% of the session. The `AccountPayload` type didn't include `account_id` (required by API), the "Add New" button had no create form to show, and TanStack Query retry configuration interfered with test determinism. All three were **mock-based test masking** (Pattern 4) — unit tests passed with mocks but the live runtime was broken.

2. **What instructions were ambiguous?**
   The `CreateAccountRequest` schema requiring `account_id` as a mandatory client-supplied field was implicit in the Python code but never documented in the implementation plan's FIC. AC-6 said "Save persists via `POST /accounts`" but didn't specify the required payload shape against the actual API contract.

3. **What instructions were unnecessary?**
   The implementation plan's Stop Condition #1 (Lightweight Charts incompatibility) was overly cautious — the decision to use `<canvas>` was made immediately and never needed a halt. The stop condition ceremony was unnecessary.

4. **What was missing?**
   - **Mock-Contract Validation**: No step in the FIC or test plan required verifying mock payloads against the actual API schema (`CreateAccountRequest`). The `AccountPayload` TS interface was written from the build plan description, not from the actual Pydantic model.
   - **Live smoke test**: No task required launching the GUI and testing basic CRUD against the running backend before declaring unit tests complete.
   - **E2E test spec alignment**: The pre-written E2E tests (`persistence.test.ts`) had 3 spec mismatches that were never caught because they were assumed to be correct.

5. **What did you do that wasn't in the prompt?**
   - Added `showCreateForm` state and `CreateAccountForm` component — the plan said "Add New card opens blank detail form" but `AccountDetailPanel` requires a non-null `Account` prop, so a separate create form was needed.
   - Fixed E2E test infrastructure: API response shape, navigation, Electron BrowserWindow bounds API.
   - Removed per-hook `retry` overrides and relied on app-level QueryClient configuration.

### Quality Signal Log

6. **Which tests caught real bugs?**
   None caught the 422 or the freeze — those were pure **mock masking**. The `useAccounts.test.ts` AC-6 error test DID catch the retry timing issue (it timed out), which led to removing per-hook overrides.

7. **Which tests were trivially obvious?**
   `BalanceHistory.test.tsx` empty state tests ("No balance history available" renders) — low signal but required for completeness.

8. **Did pyright/ruff catch anything meaningful?**
   `tsc --noEmit` caught zero errors — implementation was type-safe from the start. No meaningful catches, but the clean run was a good quality gate.

### Workflow Signal Log

9. **Was the FIC useful as written?**
   Partially. The 16 ACs covered the GUI behavior well, but AC-6 ("Save persists via POST") was too vague about the payload contract. A FIC that maps to actual API schemas (not just HTTP verbs) would have caught BF-2.

10. **Was the handoff template right-sized?**
    Yes — the handoff format captured all evidence. The bug fix section was added post-hoc, which was appropriate.

11. **How many tool calls did this session take?**
    ~100+ tool calls across planning corrections, TDD implementation, bug fixes, and E2E fixes.

---

## Pattern Extraction

### Patterns to KEEP
1. **TDD cycle** — writing tests first caught the retry timing issue and ensured consistent coverage
2. **G11 custom event pattern** — clean separation between command palette and wizard lifecycle
3. **Canvas sparkline over heavyweight charting lib** — stop condition was right, early decision avoided dependency issues

### Patterns to DROP
1. **Assuming pre-written E2E tests are correct** — persistence.test.ts had 3 spec mismatches that were only discovered when actually running the tests. E2E tests must be validated against the actual API contract and component testids before declaring them "ready to activate."

### Patterns to ADD
1. **Mock-Contract Validation gate** — after writing unit tests with mocks, verify at least one mock payload against the actual API schema. Compare `AccountPayload` TS interface against `CreateAccountRequest` Pydantic model. This catches field mismatches before they become 422 errors at runtime.
2. **Live smoke test step** — after unit tests pass, launch the dev server and test basic CRUD (create one entity, verify in API response). This catches the gap between mocked unit tests and real runtime behavior.
3. **E2E spec audit** — before running pre-written E2E tests, read the test file and verify all `apiGet` response types and `data-testid` references match the actual implementation.

### Calibration Adjustment
- Estimated time: ~2 hours (FIC + Green implementation)
- Actual time: ~4 hours (implementation + 3 bug fixes + E2E repair)
- Adjusted estimate for similar MEUs: **3.5 hours** (budget 40% for mock-contract gaps and E2E alignment)

---

## Next Session Design Rules

```
RULE-1: Verify mock payload shapes against actual API Pydantic models before declaring unit tests complete
SOURCE: BF-2 (422 on POST /accounts — `AccountPayload` missing `account_id` required by `CreateAccountRequest`)
EXAMPLE: Before: test mock is `{ name, account_type }` → After: compare with `rg "class CreateAccountRequest" packages/api` and add `account_id`
```

```
RULE-2: Run live smoke test (create + verify via API) after unit tests pass for any CRUD-heavy GUI MEU
SOURCE: BF-1 + BF-2 (both undetectable by mocked unit tests)
EXAMPLE: Before: "47 tests GREEN → done" → After: "47 tests GREEN → `npm run dev` → create account → verify 201"
```

```
RULE-3: Audit pre-written E2E test specs against actual implementation before running them
SOURCE: E2E-2/3/4 (3 spec mismatches in persistence.test.ts — response shape, missing navigation, wrong viewport API)
EXAMPLE: Before: "run E2E, fix if broken" → After: "read E2E test → verify `apiGet` types match API → verify `data-testid` refs exist → then run"
```

---

## Next Day Outline

1. **Target MEU(s):** Run MEU gate (`validate_codebase.py --scope meu`), trigger Codex validation
2. **Scaffold changes needed:** None — all GUI components are in place
3. **Patterns to bake in from today:** RULE-1 (mock-contract validation), RULE-2 (live smoke test)
4. **Codex validation scope:** Full MEU-71a — FIC compliance, test coverage, bug fix verification
5. **Time estimate:** 30 min (gate + Codex handoff)

---

## Efficiency Metrics

| Metric | Value |
|--------|-------|
| Total tool calls | ~100+ |
| Time to first green test | ~45 min (FIC + AccountContext) |
| Tests added | 47 unit + 2 E2E fixed |
| Codex findings | Pending |
| Handoff Score (X/7) | 6/7 (deferred: MEU gate not run) |
| Rule Adherence (%) | 85% |
| Prompt→commit time | ~4 hours |

### Rules Sampled for Adherence Check
| Rule | Source | Followed? |
|------|--------|-----------|
| Tests FIRST, implementation after | AGENTS.md §TDD Protocol | Yes |
| NEVER modify tests to make them pass | AGENTS.md §TDD Protocol | Yes |
| Mock-Contract Validation (check API schema) | `.agent/skills/e2e-testing/SKILL.md` §Mock-Contract | **No** — caught in-session |
| Re-run ALL commands after ALL fixes | meta-reflection Pattern 3 | Yes (after BF-1/2/3) |
| Evidence-first completion | AGENTS.md §Execution Contract | Yes (live 201, E2E 2/2) |

### Meta-Reflection Pattern Match

| Pattern | Triggered? | Impact |
|---------|-----------|--------|
| P4: Mock-Based Test Masking | **YES** | 3 bugs hidden by mocks (BF-1, BF-2, BF-3) |
| P1: Claim-to-State Drift | Partial | Initial task.md was over-simplified, losing original granularity |
| P2: Artifact Incompleteness | Partial | Original task.md/handoff created before E2E and bug fixes |
| P3: Evidence Staleness | No | Evidence refreshed after every fix |
| P5: Scope Overstatement | No | Handoff listed remaining items honestly |
