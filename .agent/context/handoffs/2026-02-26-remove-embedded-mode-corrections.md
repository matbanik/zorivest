# Corrections: Embedded Mode Removal Review Findings

## Task

- **Date:** 2026-02-26
- **Task slug:** remove-embedded-mode-corrections
- **Owner role:** coder
- **Source:** [Critical review](2026-02-26-remove-embedded-mode-critical-review.md)
- **Status:** ✅ Complete

---

## Findings Addressed

| # | Severity | Finding | Fix |
|---|----------|---------|-----|
| 1 | **High** | Broken anchor `#step-57-mcp-auth-bootstrap-standalone-mode` in `07-distribution.md:199` | Updated to `#step-57-mcp-auth-bootstrap` |
| 2 | **Medium** | Build-plan doc linked to `.agent/context/handoffs/` (portability risk) | Made design decision note self-contained with all 5 risks enumerated inline |
| 3 | **Medium** | Handoff verification used phrase-only grep, missed slug variants | Replaced with slug/anchor-aware `rg` command + handoff link check |
| 4 | **Low** | `render_diffs()` placeholders not reproducible | Replaced with inline diff summaries |

## Files Modified

| File | Change |
|---|---|
| `docs/build-plan/07-distribution.md` | Line 199: anchor fix |
| `docs/build-plan/05-mcp-server.md` | Lines 284-290: self-contained design decision |
| `.agent/context/handoffs/2026-02-26-remove-embedded-mode.md` | Verification + diffs sections |

## Verification

- `rg -n "standalone.mode|standalone-mode|mcp-auth-bootstrap-standalone" docs/build-plan/` → **0 results** ✅
- `rg -n "\.agent/context/handoffs" docs/build-plan/` → **0 results** ✅
- `rg -n "render_diffs" .agent/context/handoffs/2026-02-26-remove-embedded-mode.md` → **0 results** ✅

## Workflow Created

New reusable workflow: [/planning-corrections](.agent/workflows/planning-corrections.md)
