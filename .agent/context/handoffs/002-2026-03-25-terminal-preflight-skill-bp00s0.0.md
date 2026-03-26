# Handoff 002 — Terminal Pre-Flight Skill

**Project:** agents-terminal-optimization-infra
**MEU:** B — Terminal Pre-Flight SKILL.md
**Date:** 2026-03-25
**Author:** Opus 4.6

## Changes

### [NEW] .agent/skills/terminal-preflight/SKILL.md

Created new skill file with:

1. **YAML frontmatter** — `name: Terminal Pre-Flight`, `description`
2. **Trigger clause** — MUST invoke before any `run_command` in execution phase
3. **4-item checklist** — matches AGENTS.md §P0 exactly (redirect, receipts dir, no-pipe, background)
4. **SOP: 4-step sequence** — Declare → Formulate → Execute+Detach → Consume Artifact
5. **Per-tool redirect table** — cross-references AGENTS.md §P0 (authoritative copy)
6. **Example thought process** — concrete step-by-step demonstration
7. **Anti-patterns section** — explicit "Never Do These" with examples
8. **Skip list** — lightweight commands exempt from redirect (rg, Get-Content, Test-Path)

## Acceptance Criteria Evidence

| # | Criterion | Result |
|---|-----------|--------|
| AC-1 | `Test-Path` | ✅ True |
| AC-2 | `rg "name:"` frontmatter | ✅ L2 `name: Terminal Pre-Flight` |
| AC-3 | `rg "Trigger\|trigger"` | ✅ L8 `Trigger: MUST be invoked...` |
| AC-4 | `rg "\*>"` | ✅ L16, L54+ (multiple matches) |
| AC-5 | `rg "redirect\|receipts\|no-pipe\|long-running"` all 4 | ✅ 7 total matches |

## Proposed Commit Message

```
docs: add terminal-preflight skill for P0 redirect enforcement

Create .agent/skills/terminal-preflight/SKILL.md with 4-item checklist,
SOP (Declare/Formulate/Execute/Consume), per-tool redirect table, and
anti-pattern examples. Enforces the redirect-to-file pattern at workflow
invocation points.

Part-of: agents-terminal-optimization-infra
```

## Verdict

Ready for Codex review.
