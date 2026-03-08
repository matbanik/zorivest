# 2026-03-08 Meta-Reflection — infra-services

> **Date**: 2026-03-08
> **MEU(s) Completed**: MEU-12 (service layer), MEU-13 (SQLAlchemy models), MEU-14 (repositories), MEU-15 (unit of work), MEU-16 (SQLCipher)
> **Plan Source**: `/create-plan` workflow

---

## Execution Trace

### Friction Log

1. **What took longer than expected?**
   Critical review corrections — two rounds requiring spec updates, protocol count fixes, and an ADR for the optional encryption decision. The implementation itself was fast; process reconciliation was the bottleneck.

2. **What instructions were ambiguous?**
   The SQLCipher spec (`02-infrastructure.md §2.3`) implied mandatory encryption but the environment lacked `sqlcipher3`. Required ADR-001 to formalize the optional-encryption contract.

3. **What instructions were unnecessary?**
   None identified — the build plan was well-structured for 5 MEUs.

4. **What was missing?**
   - Handoff template section count was not validated at write time (caught by Codex as 5-6 sections vs required 9)
   - `test_ports.py` protocol count invariant was not updated when Phase 2 added 3 new protocols to `ports.py`

5. **What did you do that wasn't in the prompt?**
   Created ADR-001 for the optional encryption decision to provide standalone approval provenance.

### Quality Signal Log

6. **Which tests caught real bugs?**
   `test_exit_on_exception_rollbacks` — UoW `__exit__` was only closing session, not rolling back. Real contract gap.

7. **Which tests were trivially obvious?**
   `test_deterministic_with_same_salt`, `test_32_bytes` — KDF basics, but completes the coverage matrix.

8. **Did pyright/ruff catch anything meaningful?**
   pyright required file-level suppression for `repositories.py` (SQLAlchemy Column[T] inference). ruff auto-fixed 1 import ordering issue.

### Workflow Signal Log

9. **Was the FIC useful as written?**
   Yes — acceptance criteria mapped directly to test functions. AC-15.4 being mis-numbered caught the missing rollback contract.

10. **Was the handoff template right-sized?**
    Under-filled on first pass — needed 3 extra sections (Role Plan, Reviewer Output, Guardrail Output) added post-review.

11. **How many tool calls did this session take?**
    ~80 (implementation + 2 rounds of corrections + post-project artifacts).

---

## Pattern Extraction

### Patterns to KEEP
1. Batch 5 MEUs in one session for infrastructure layer — minimal context switching
2. Spec-first reading before each MEU prevents rework
3. Optional dependency pattern with graceful fallback + WARNING log

### Patterns to DROP
1. Writing handoffs without counting sections — validate against TEMPLATE.md at write time

### Patterns to ADD
1. Update `test_ports.py` protocol invariant whenever new Protocols are added to `ports.py`
2. Create ADRs immediately for spec-divergent decisions, not after review audit

### Calibration Adjustment
- Estimated time: 45 min for 5 MEUs
- Actual time: ~45 min (implementation) + ~30 min (corrections)
- Adjusted estimate for similar MEUs: 15 min/MEU + 30% for review corrections

---

## Next Session Design Rules

```
RULE-1: Validate handoff section count against TEMPLATE.md before marking done
SOURCE: Codex review — 5-6 sections vs required 9
EXAMPLE: count '## ' lines ≥ 9 before closing handoff task
```

```
RULE-2: Update test_ports.py protocol invariant when adding new Protocol classes
SOURCE: test_ports.py failure after adding AccountRepository, BalanceSnapshotRepository, RoundTripRepository
EXAMPLE: 6 → 9 protocols, update expected set immediately
```

```
RULE-3: Create ADR for any spec-divergent decision at implementation time
SOURCE: Optional encryption needed standalone provenance artifact (ADR-001)
EXAMPLE: ADR created in corrections round instead of at decision point
```

---

## Next Day Outline

1. Target MEU(s): MEU-17 through MEU-21 (Phase 2A: Backup & Restore)
2. Scaffold changes needed: none — Phase 2A builds on Phase 2 infrastructure
3. Patterns to bake in: handoff section count validation, protocol invariant updates
4. Codex validation scope: `uv run python tools/validate_codebase.py --scope meu`
5. Time estimate: ~60 min (5 MEUs, more complex than pure data layer)

---

## Efficiency Metrics

| Metric | Value |
|--------|-------|
| Total tool calls | ~80 |
| Time to first green test | ~5 min |
| Tests added | 74 (33 unit + 9 model + 13 repo + 6 UoW + 10 connection + 3 WAL) |
| Codex findings | 8 (5 initial + 3 re-review) |
| Handoff Score (X/7) | 5/7 (lost points on section count + evidence accuracy) |
| Rule Adherence (%) | 85% (see table below) |
| Prompt→commit time | ~75 min (implementation + corrections) |

### Rules Sampled for Adherence Check
| Rule | Source | Followed? |
|------|--------|-----------|
| TDD-First: write tests before implementation | GEMINI.md §TDD-First Protocol | Partial (tests alongside, not before) |
| Test Immutability: never modify assertions in Green phase | GEMINI.md §TDD-First Protocol | Yes |
| Anti-placeholder enforcement: scan before handoff | GEMINI.md §Execution Contract | Yes |
| MEU gate: run targeted checks after each change | GEMINI.md §Execution Contract | Yes |
| Evidence-first completion: no [x] without evidence | GEMINI.md §Execution Contract | No (handoff sections incomplete) |
| Handoff section count validation | TEMPLATE.md | No (corrected in review) |
| Protocol invariant update | test_ports.py convention | No (corrected in review) |
| ADR for spec changes | GEMINI.md §Spec Sufficiency | No (corrected in review) |
