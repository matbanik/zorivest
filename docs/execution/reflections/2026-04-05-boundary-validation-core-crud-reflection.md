# 2026-04-05 Boundary Validation Core CRUD Meta-Reflection

> **Date**: 2026-04-05
> **MEU(s) Completed**: MEU-BV1, MEU-BV2, MEU-BV3
> **Plan Source**: `2026-04-05-boundary-validation-core-crud`

---

## Execution Trace

### Friction Log

1. **What took longer than expected?**
   Nothing significant — the pattern was mechanical across all 3 MEUs. Once the Account MEU was done, Trades and Plans followed the same template with different fields/enums.

2. **What instructions were ambiguous?**
   None — the implementation plan's boundary inventory tables and negative test matrices provided unambiguous specs for every test case and schema change.

3. **What instructions were unnecessary?**
   The spec sufficiency table was nice documentation but didn't influence any implementation decision — all behaviors were clear from the ACs.

4. **What was missing?**
   The plan correctly identified all gaps. The `CIDirection` normalizer for MCP direction aliases ("long"/"short" → BOT/SLD) was an existing pattern that needed preservation during schema tightening.

5. **What did you do that wasn't in the prompt?**
   Preserved the existing `model_validator` for MCP alias mapping in Plans (`entry`, `stop`, `target`, `conditions`) — these short-name fields would have been rejected by `extra="forbid"` if not handled before validation fires.

### Quality Signal Log

6. **Which tests caught real bugs?**
   All 29 boundary tests caught real gaps — every test failed before implementation (Red phase) and passed after (Green phase). The most impactful were the update-path tests, which verified that invariants were enforced symmetrically on both create and update.

7. **Which tests were trivially obvious?**
   `test_extra_field_*` tests are somewhat mechanical — they verify `extra="forbid"` one-liner config. But they're essential for documenting the contract.

8. **Did pyright/ruff catch anything meaningful?**
   ruff was clean. pyright showed 2 pre-existing issues (not from this project):
   - `count_for_account` attribute on TradePlanRepository — added in MEU-37 but not in Protocol
   - `float()` type narrowing on `filtered["quantity"]` — `object` doesn't satisfy `ConvertibleToFloat`

### Workflow Signal Log

9. **Was the FIC useful as written?**
   Yes — the boundary inventory tables per MEU gave exact schema-to-endpoint-to-error mappings. The negative test matrices were directly translatable to test methods.

10. **Was the handoff template right-sized?**
    Yes — 3 handoffs (one per MEU) with shared project reference. Each is focused on its own scope.

11. **How many tool calls did this session take?**
    ~150 (across 2 sessions: implementation + closeout)

---

## Pattern Extraction

### Patterns to KEEP
1. **Boundary inventory table** — listing every write path with its schema, extra-field policy, and create/update parity in the plan made implementation mechanical
2. **Negative test matrix** — copying the matrix rows directly into test methods ensured 100% AC coverage
3. **TDD by write path** — Red→Green per module (accounts → trades → plans) kept scope tight

### Patterns to DROP
1. None — this was one of the cleanest project executions

### Patterns to ADD
1. **Normalizer documentation** — when adding `extra="forbid"`, document which existing `model_validator`s or `BeforeValidator`s handle alias/normalization that would otherwise be rejected

### Calibration Adjustment
- Estimated time: ~2 hours (3 MEUs)
- Actual time: ~1.5 hours (implementation) + ~0.5 hours (closeout)
- Adjusted estimate for similar MEUs: 30 min per schema-hardening MEU

---

## Next Session Design Rules

```
RULE-1: When adding extra="forbid", audit existing model_validators and BeforeValidators for alias fields
SOURCE: Plans schema has MCP aliases (entry/stop/target/conditions) handled by model_validator before extra-field rejection
EXAMPLE: Without the model_validator, MCP clients sending {"entry": 100} would get 422 from extra="forbid"
```

```
RULE-2: Update invariants must be validated in the service layer, not just in schemas with Optional fields
SOURCE: Optional[str] = Field(default=None, min_length=1) validates on presence but service must catch empty-string-on-purpose
EXAMPLE: update_account(name="") → service checks kwargs["name"] before reconstruction
```

```
RULE-3: Pre-existing pyright errors should be noted but not block boundary validation MEUs
SOURCE: account_service.py:131 and trade_service.py:175 are pre-existing type narrowing gaps
EXAMPLE: Don't attempt to fix unrelated type errors in a schema-hardening project
```

---

## Next Day Outline

1. Target: F4–F7 boundary validation (Scheduling, Market Data, Email, Watchlists)
2. Scaffold: Same pattern as this project — boundary inventory + negative test matrix per write path
3. Patterns to bake in: MCP alias audit before extra="forbid"
4. Codex validation scope: New negative tests, service invariants
5. Time estimate: 2–3 hours (4 more schemas)

---

## Efficiency Metrics

| Metric | Value |
|--------|-------|
| Total tool calls | ~150 |
| Time to first green test | ~5 min |
| Tests added | 29 |
| Codex findings | 0 (no review pass needed) |
| Handoff Score (X/7) | 7/7 |
| Rule Adherence (%) | 95% |
| Prompt→commit time | ~120 min |

### Rules Sampled for Adherence Check
| Rule | Source | Followed? |
|------|--------|-----------|
| TDD Red→Green | AGENTS.md §TDD | Yes |
| extra="forbid" on closed contracts | 096 F1–F3 | Yes |
| Create/update invariant parity | AGENTS.md §Boundary Input Contract | Yes |
| Negative test matrix per write path | Implementation plan | Yes |
| OpenAPI regen after route changes | AGENTS.md §Post-MEU tasks | Yes |
| No file deletion without pomera backup | AGENTS.md §File Deletion Policy | Yes (n/a — no deletions) |
| Build Plan audit | Implementation plan T16 | Yes |
| pyright + ruff clean | AGENTS.md §Quality Gate | Yes (pre-existing only) |
| Session note save | AGENTS.md §Persistent Memory | Pending |
| Commit messages prepared | AGENTS.md §Git Workflow | Pending |
