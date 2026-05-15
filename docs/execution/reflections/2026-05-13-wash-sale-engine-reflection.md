---
date: "2026-05-13"
project: "wash-sale-engine"
meus: ["MEU-130", "MEU-131", "MEU-132"]
plan_source: "docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md"
template_version: "2.0"
---

# 2026-05-13 Meta-Reflection

> **Date**: 2026-05-13
> **MEU(s) Completed**: MEU-130, MEU-131, MEU-132
> **Plan Source**: docs/execution/plans/2026-05-13-wash-sale-engine/implementation-plan.md

---

## Execution Trace

### Friction Log

1. **What took longer than expected?**
   The table count regression tests (`test_models.py`, `test_market_data_models.py`) required investigation to find both locations that assert exact table counts. The 42→44 update was straightforward once located, but finding both assertion sites required careful searching.

2. **What instructions were ambiguous?**
   Task 29 (spousal toggle) specified "honor `TaxProfile.include_spousal_accounts`" but didn't clarify the interface contract. The AC said the field "already exists" but the scan method didn't have a parameter for it. Added `include_spousal` parameter with default `True`.

3. **What instructions were unnecessary?**
   Separate FIC creation (Tasks 1/13/22) was already done in the prior session — the FICs existed but task status wasn't updated. The re-anchor gate (Task 32) is redundant when task status is maintained correctly.

4. **What was missing?**
   The plan didn't specify that adding 2 new tables requires updating `test_ports.py` protocol counts (22→23 protocols, 23→24 classes). This is a recurring regression pattern when new repositories are added.

5. **What did you do that wasn't in the prompt?**
   - Added `WashSaleChainManager` to `domain/tax/__init__.py` exports
   - Fixed pyright `Decimal | Literal[0]` typing issue with `sum()` initial value
   - Removed unused `Text` import from `wash_sale_models.py` and `WashSaleStatus` import from `scan_cross_account_wash_sales()`
   - Added `_get_spousal_account_ids()` private helper method

### Quality Signal Log

6. **Which tests caught real bugs?**
   The `test_scan_method_accepts_spousal_param` test drove the addition of the `include_spousal` parameter which was missing from the initial implementation.

7. **Which tests were trivially obvious?**
   The method-existence tests (`test_method_exists`, `test_class_exists`) are low-value — pyright already catches missing methods. However, they serve as contract documentation.

8. **Did pyright/ruff catch anything meaningful?**
   - **pyright**: Caught `Decimal | Literal[0]` type mismatch on `sum()` without initial value — real bug that would cause runtime issues in strict type-checking environments.
   - **ruff**: Caught 2 unused imports — clean code maintenance value.

### Workflow Signal Log

9. **Was the FIC useful as written?**
   Yes — the AC-by-AC structure mapped cleanly to test functions. The IRS Pub 550 citations were essential for the 30-day window and holding period tacking requirements.

10. **Was the handoff template right-sized?**
    For a 3-MEU project, the standard template works well. The AC table per MEU provides clear traceability.

11. **How many tool calls did this session take?**
    ~65 tool calls across planning, implementation, and post-implementation phases.

---

## Pattern Extraction

### Patterns to KEEP
1. **Test-per-AC mapping**: Each acceptance criterion maps to exactly one test function — provides clear FAIL_TO_PASS traceability
2. **State machine as separate class**: `WashSaleChainManager` encapsulates all state transitions cleanly, making the chain lifecycle testable in isolation
3. **Regression test updates as explicit tasks**: Table count and protocol count tests should be checked when adding new infrastructure

### Patterns to DROP
1. **Separate method-exists tests**: These add ceremony without catching real bugs beyond what pyright already validates

### Patterns to ADD
1. **Auto-detect table/protocol count regressions**: Future plans should include a task to check `test_models.py`, `test_market_data_models.py`, and `test_ports.py` whenever new models/protocols are added

### Calibration Adjustment
- Estimated time: ~4 hours (3 MEUs × ~90 min each)
- Actual time: ~3 hours (batched across 2 sessions)
- Adjusted estimate for similar MEUs: 75 min per domain+infra MEU when entity/repository patterns are established

---

## Next Session Design Rules

```
RULE-1: Always check table count and protocol count tests when adding new models
SOURCE: Friction Log #4 — regression discovered during post-implementation
EXAMPLE: Adding WashSaleChainModel → must update test_models.py (42→44) AND test_ports.py (22→23)
```

```
RULE-2: Use Decimal(0) as sum() initial value when summing Decimal fields
SOURCE: Quality Signal #8 — pyright caught Decimal | Literal[0] mismatch
EXAMPLE: sum(m.amount for m in matches) → sum((m.amount for m in matches), Decimal(0))
```

```
RULE-3: Add spousal/toggle parameters with safe defaults in initial implementation
SOURCE: Friction Log #2 — ambiguous AC required a second pass to add parameter
EXAMPLE: def scan(..., include_spousal: bool = True) — default True = IRS-compliant
```

---

## Next Day Outline

1. **Target MEU(s)**: MEU-133 (Options-to-Stock Wash Sale), MEU-134 (DRIP Wash Sale)
2. **Scaffold changes needed**: None — entities, chain manager, and service already support the extension points
3. **Patterns to bake in from today**: Table/protocol count regression checks as explicit plan tasks
4. **Codex validation scope**: Full wash sale test suite + regression
5. **Time estimate**: ~2.5 hours for 2 MEUs

---

## Efficiency Metrics

| Metric | Value |
|--------|-------|
| Total tool calls | ~65 |
| Time to first green test | ~30 min |
| Tests added | 50 |
| Codex findings | pending |
| Handoff Score (X/7) | 7/7 |
| Rule Adherence (%) | 95% |
| Prompt→commit time | ~3 hours |

### Rules Sampled for Adherence Check

| Rule | Source | Followed? |
|------|--------|-----------|
| Tests FIRST, implementation after | AGENTS.md §Testing | Yes |
| Never modify tests to make them pass | AGENTS.md §Testing | Yes |
| Run targeted tests after EVERY code change | AGENTS.md §Execution | Yes |
| Anti-premature-stop rule | AGENTS.md §Execution | Yes |
| No `command_status` for reading output | AGENTS.md §P0 | Yes |

---

## Instruction Coverage

```yaml
schema: v1
session:
  id: "12e2ff1e-8bad-4f1b-9f13-1fc17c1ea9a5"
  task_class: tdd
  outcome: success
  tokens_in: 0
  tokens_out: 0
  turns: 6
sections:
  - id: testing_tdd_protocol
    cited: true
    influence: 3
  - id: execution_contract
    cited: true
    influence: 3
  - id: session_discipline
    cited: true
    influence: 2
  - id: operating_model
    cited: true
    influence: 2
  - id: p0_system_constraints
    cited: true
    influence: 3
  - id: planning_contract
    cited: true
    influence: 1
loaded:
  workflows: [execution_session, tdd_implementation]
  roles: [coder, tester, reviewer, orchestrator]
  skills: [completion_preflight, quality_gate]
  refs: [reflection.v1.yaml]
decisive_rules:
  - "P1:tests-first-implementation-after"
  - "P0:redirect-to-file-pattern"
  - "P1:fic-before-code"
  - "P1:anti-premature-stop"
  - "P2:evidence-first-completion"
conflicts: []
note: "3-MEU batch execution pattern worked well — shared entity foundation enabled efficient chain of MEU-130→131→132."
```
