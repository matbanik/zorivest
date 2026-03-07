# 2026-03-06 Meta-Reflection

> **Date**: 2026-03-06
> **MEU(s) Completed**: MEU-1 (calculator)
> **Prompt Used**: `docs/execution/prompts/2026-03-06-meu-1-calculator-pilot.md`

---

## Execution Trace

### Friction Log

1. **What took longer than expected?**
   Workspace wiring — the `hatchling.backends` typo (correct: `hatchling.build`) and the missing `[tool.uv.sources]` workspace dependency took 2 extra iterations. The package needed to be importable before tests could run.

2. **What instructions were ambiguous?**
   The prompt listed `packages/core/pyproject.toml` without specifying the exact build backend value. The build plan §1.3 showed the code but not the packaging config. `hatchling.build` vs `hatchling.backends` was a common pitfall.

3. **What instructions were unnecessary?**
   None — the prompt was well-scoped for a day-1 pilot.

4. **What was missing?**
   The prompt should explicitly mention adding `zorivest-core` as a workspace dependency with `[tool.uv.sources]` in the root `pyproject.toml`. Without this, `import zorivest_core` fails in the venv.

5. **What did you do that wasn't in the prompt?**
   Added `zorivest-core` as a workspace dependency in root `pyproject.toml`. Fixed `hatchling.backends` → `hatchling.build`. Removed unused `importlib` import caught by ruff.

### Quality Signal Log

6. **Which tests caught real bugs?**
   None — the implementation matched the spec on first attempt. This is expected for pure math with no dependencies.

7. **Which tests were trivially obvious?**
   `test_frozen_dataclass` — the `frozen=True` flag makes this pass automatically. Still valuable as a regression guard.

8. **Did pyright/ruff catch anything meaningful?**
   Ruff caught an unused `importlib` import in the test file (F401). pyright found 0 issues.

### Workflow Signal Log

9. **Was the FIC useful as written?**
   Yes — the 7 ACs mapped cleanly to 9 test functions. The FIC was the right level of detail.

10. **Was the handoff template right-sized?**
    Yes — the template fit naturally without padding.

11. **How many tool calls did this session take?**
    ~50 tool calls (including file reads, workspace setup, and verification).

---

## Pattern Extraction

### Patterns to KEEP
1. Writing all tests before any implementation — the Red phase was clean and fast
2. Using `pytest.approx()` for floating-point assertions — avoided brittleness

### Patterns to DROP
1. None identified in this pilot session

### Patterns to ADD
1. Include exact `pyproject.toml` workspace dependency config in the prompt template
2. Run `uv sync --reinstall-package <pkg>` after creating new source files in workspace packages

### Calibration Adjustment
- Estimated time: 30 minutes
- Actual time: ~15 minutes
- Adjusted estimate for similar MEUs: 15–20 minutes for pure math modules

---

## Next Prompt Design Rules

```
RULE-1: Include explicit workspace dependency wiring in bootstrap section
SOURCE: Friction log #4 — missing [tool.uv.sources] caused import failures
EXAMPLE: Add "zorivest-core = { workspace = true }" to root pyproject.toml
```

```
RULE-2: Specify exact build-backend value for new packages
SOURCE: Friction log #1 — hatchling.backends typo cost 2 iterations
EXAMPLE: build-backend = "hatchling.build" (not "hatchling.backends")
```

```
RULE-3: After creating new source files in workspace packages, rebuild with --reinstall-package
SOURCE: Friction log #1 — new files not visible until package rebuilt
EXAMPLE: uv sync --reinstall-package zorivest-core
```

---

## Next Day Outline

1. **Target MEU(s)**: MEU-2 (enums) — 15 StrEnum definitions
2. **Scaffold changes**: No new packages needed — add `enums.py` to existing `domain/` package
3. **Patterns to bake in**: Explicit workspace wiring already done; --reinstall-package after new files
4. **Codex validation scope**: `packages/core/src/` and `tests/unit/` only
5. **Time estimate**: 15–20 minutes (similar pure-definition module)

---

## Efficiency Metrics

| Metric | Value |
|--------|-------|
| Total tool calls | ~50 |
| Time to first green test | ~8 minutes |
| Tests added | 9 |
| Codex findings | 0 (approved) |
| Handoff Score (X/7) | 7/7 |
| Rule Adherence (%) | 100% |
| Prompt→commit time | ~15 min |

### Rules Sampled for Adherence Check
| Rule | Source | Followed? |
|------|--------|-----------|
| Tests written before implementation | GEMINI.md §TDD-First Protocol | Yes |
| Test immutability in Green phase | GEMINI.md §TDD-First Protocol | Yes |
| Anti-placeholder enforcement | GEMINI.md §Execution Contract | Yes |
| No auto-commits | Prompt §Stop Conditions | Yes |
| ONE MEU per session | execution-session.md §4 | Yes |
| Evidence-first completion | GEMINI.md §Execution Contract | Yes |
| Handoff is self-contained | meu-handoff.md | Yes |
| Pomera notes saved | tdd-implementation.md §8 | Yes |
| MEU registry updated | Prompt §Handoff and State | Yes |
| Stop conditions respected | Prompt §Stop Conditions | Yes |
