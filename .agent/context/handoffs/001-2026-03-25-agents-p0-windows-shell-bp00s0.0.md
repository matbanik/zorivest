# Handoff 001 — AGENTS.md P0 Windows Shell Restructure

**Project:** agents-terminal-optimization-infra
**MEU:** A — AGENTS.md Priority-0 Restructure
**Date:** 2026-03-25
**Author:** Opus 4.6

## Changes

### [MODIFY] AGENTS.md

Prepended `## PRIORITY 0 — SYSTEM CONSTRAINTS (Non-Negotiable)` section (54 lines) before all existing content. Contains:

1. **Priority Hierarchy Table** (P0–P3) — establishes environment stability as non-negotiable
2. **Windows Shell Mandatory Redirect-to-File Pattern** — explains the root cause (PowerShell six-stream model)
3. **Pre-flight Checklist** — 4 items to satisfy before every `run_command`
4. **INCORRECT vs CORRECT Patterns** — concrete examples
5. **Per-Tool Redirect Table** — exact copy-paste commands for pytest, vitest, pyright, ruff, validate_codebase.py, git

No existing content was deleted. Total line count increased from 354 → 406.

## Acceptance Criteria Evidence

| # | Criterion | Result |
|---|-----------|--------|
| AC-1 | `rg "PRIORITY 0" AGENTS.md` in first 30 lines | ✅ L1 |
| AC-2 | `rg "\*>" AGENTS.md` ≥ 1 line | ✅ L21, L38, L44-49 |
| AC-3 | pytest/vitest/pyright/ruff all in redirect table | ✅ L44-49 |
| AC-4 | `rg "Pre-flight" AGENTS.md` | ✅ L19 |
| AC-5 | Line count ≥ 354 (original) | ✅ 406 |

## Proposed Commit Message

```
docs: add PRIORITY 0 system constraints to AGENTS.md

Prepend non-negotiable P0 block establishing PowerShell redirect-to-file
pattern as a mandatory environment stability constraint. Includes priority
hierarchy (P0-P3), 4-item pre-flight checklist, and per-tool redirect table
for pytest/vitest/pyright/ruff/validate_codebase/git.

Resolves: terminal buffer saturation causing agent session hangs
```

## Verdict

Ready for Codex review.
