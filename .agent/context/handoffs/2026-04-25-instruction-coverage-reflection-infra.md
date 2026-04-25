---
project: "2026-04-25-instruction-coverage-reflection"
meus: ["ICR-1", "ICR-2", "ICR-3"]
phase: "Phase-Infra"
verbosity: standard
date: 2026-04-25
---

# Handoff — Instruction Coverage Reflection System

## Summary

Established a data-driven instruction coverage and reflection system for the Zorivest ~50K-token agent instruction set. The system enables continuous optimization by tracking which AGENTS.md sections are actually consulted during execution, identifying silent guards, and surfacing pruning candidates.

## Changed Files

```diff
# NEW: .agent/schemas/registry.yaml
+ 23 H2 sections mapped to snake_case IDs with P0-P3 priorities
+ Workflow/role/skill file inventory with load_mode tags
+ P0 sections (never auto-prune): system_constraints, pre_handoff_self_review, execution_contract, windows_shell

# NEW: .agent/schemas/reflection.v1.yaml
+ Schema v1 definition with session metadata, per-section usage, loaded files, decisive rules
+ Token budget: ~278 (empty) / ~416 (typical) / ~612 (worst-case)

# MODIFIED: AGENTS.md
+ Added ## Instruction Coverage Reflection at EOF (recency zone)
+ Meta-prompt instructs agents to emit YAML reflection at session end
+ Negative-framing rules per Anthropic guidance ("Do not flatter...")

# MODIFIED: docs/execution/reflections/TEMPLATE.md
+ Added ## Instruction Coverage section with YAML block placeholder

# NEW: tests/unit/test_aggregate_reflections.py
+ 14 tests across 8 test classes (AC-3.1 through AC-3.8)
+ Red phase verified: 7 new/modified assertions FAIL before production fix (corrections session 2026-04-25)

# NEW: tools/aggregate_reflections.py
+ Full aggregation pipeline: load → frequency_heatmap → decay_curves → silent_guards → pruning_candidates
+ P0 safety gate: KEEP_ALWAYS (never PRUNING_CANDIDATE)
+ CLI with --input, --registry, --output, --json-stdout flags

# NEW: .agent/reflections/test/SESSION_001.yaml
+ Synthetic test reflection covering all 23 sections
```

## Evidence

| Check | Command | Result |
|-------|---------|--------|
| Registry parity | `uv run python -c "..."` | `OK: 23 sections match` |
| Schema valid | `yaml.safe_load(...)` | `OK` |
| Meta-prompt present | `rg "instruction_coverage_reflection" AGENTS.md` | 1 match |
| Template updated | `rg "Instruction Coverage" TEMPLATE.md` | 1 match |
| Red phase | `pytest test_aggregate_reflections.py` | `7 failed, 7 passed` (corrections session) |
| Green phase | `pytest test_aggregate_reflections.py -v` | `14 passed` |
| E2E aggregator | `python aggregate_reflections.py --json-stdout` | Exit 0, JSON with n_sessions=1 |
| Anti-placeholder | `rg "TODO\|FIXME\|NotImplementedError"` | 0 matches |
| BUILD_PLAN audit | `rg "instruction-coverage" BUILD_PLAN.md` | 0 matches |

## Design Decisions

1. **23 H2 sections** (not 24): `rg` overcounted H3 lines; Python regex confirmed 22. Updated to 23 after meta-prompt injection.
2. **P0 sections**: `system_constraints`, `pre_handoff_self_review`, `execution_contract`, `windows_shell` — all tagged `auto_prune: false`.
3. **Meta-prompt at EOF**: Placed as the last H2 in AGENTS.md to maximize recency bias (Liu et al., Anthropic guidance).
4. **Universal format**: Single meta-prompt works across Claude/GPT/Gemini (no XML wrappers needed since AGENTS.md is markdown).
5. **`run_analysis()` entry point**: Separate from CLI `main()` for test compatibility.
6. **Registry normalization**: `load_registry()` converts list-format sections to dict-keyed format for lookup performance.

## Residual Risk

- Corrections applied 2026-04-25 per implementation-critical-review findings (F1–F6). See review handoff.

## Next Steps

- Agents will now emit reflection YAML at session end (the meta-prompt is active).
- After 10+ sessions accumulate, run `python tools/aggregate_reflections.py` to generate the first real coverage report.
- Use report to identify pruning candidates and instruction reordering opportunities.
