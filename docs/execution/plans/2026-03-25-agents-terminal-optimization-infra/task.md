# Task — Agent Terminal Optimization Infrastructure
> Plan: `docs/execution/plans/2026-03-25-agents-terminal-optimization-infra/implementation-plan.md`
> Source: `_inspiration/agents_terminal_optimization/COMPOSITE-synthesis-agent-terminal-optimization.md`
> Date: 2026-03-25

## Project Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | MEU-A: AGENTS.md P0 restructure | Opus | AGENTS.md with P0 section at top | `rg "PRIORITY 0" AGENTS.md` (first 30 lines); `rg "\*>" AGENTS.md`; `rg "pytest\|vitest\|pyright\|ruff" AGENTS.md` (≥1 per tool); `rg "Pre-flight" AGENTS.md`; `(Get-Content AGENTS.md).Count` ≥ original | [x] |
| 2 | MEU-B: terminal-preflight SKILL.md | Opus | `.agent/skills/terminal-preflight/SKILL.md` | `Test-Path .agent\skills\terminal-preflight\SKILL.md`; `rg "name:" .agent/skills/terminal-preflight/SKILL.md`; `rg "Trigger\|trigger" .agent/skills/terminal-preflight/SKILL.md`; `rg "\*>" .agent/skills/terminal-preflight/SKILL.md`; `rg "redirect\|receipts\|no-pipe\|long-running" .agent/skills/terminal-preflight/SKILL.md` (all 4) | [x] |
| 3 | MEU-C: workflow amendments | Opus | `execution-session.md` + `tdd-implementation.md` updated | `rg "P0 Terminal Pre-Flight\|terminal-preflight" .agent/workflows/execution-session.md`; `rg "Pre-Completion Sweep" .agent/workflows/execution-session.md`; `rg -c "P0 REMINDER" .agent/workflows/tdd-implementation.md` = 3; `(Get-Content .agent/workflows/execution-session.md).Count` ≥ 213; `(Get-Content .agent/workflows/tdd-implementation.md).Count` ≥ 120 | [x] |
| 4 | BUILD_PLAN.md check | Opus | rg confirms no stale refs; no product rows to update | `rg "agents-terminal-optimization\|terminal-preflight\|PRIORITY 0" docs/BUILD_PLAN.md` → 0 matches | [x] |
| 5 | current-focus.md changelog | Opus | `.agent/context/current-focus.md` updated with agent-infra entry | `rg "agents-terminal-optimization-infra\|terminal-preflight" .agent/context/current-focus.md` returns ≥ 1 match | [x] |
| 6 | Handoffs created (3) | Opus | `001-*-bp00s0.0.md`, `002-*-bp00s0.0.md`, `003-*-bp00s0.0.md` | `Test-Path .agent/context/handoffs/001-2026-03-25-agents-p0-windows-shell-bp00s0.0.md`; same for 002, 003 | [x] |
| 7 | Codex review — all 3 handoffs | Codex | Review handoffs 001-003; verify no rule deletions, checklist parity, correct placement | `rg "Verdict\|verdict" .agent/context/handoffs/001-2026-03-25-agents-p0-windows-shell-bp00s0.0.md` returns ≥ 1 match; same for 002, 003 handoffs | [ ] |
| 8 | Reflection file | Opus | `docs/execution/reflections/2026-03-25-agents-terminal-optimization-infra-reflection.md` | `Test-Path docs/execution/reflections/2026-03-25-agents-terminal-optimization-infra-reflection.md` | [ ] |
| 9 | Metrics update | Opus | `docs/execution/metrics.md` updated with session row | `rg "2026-03-25.*agents-terminal" docs/execution/metrics.md` returns 1 match | [ ] |
| 10 | Commit messages prepared | Opus | Proposed commit messages presented to human | `rg "feat:\|fix:\|refactor:\|docs:\|test:" .agent/context/handoffs/003-2026-03-25-workflow-amendments-bp00s0.0.md` returns ≥ 1 match (commit msgs included in final handoff) | [x] |

---

## MEU Checklist

### MEU-A: AGENTS.md P0 Restructure
- [ ] Read current AGENTS.md: `(Get-Content AGENTS.md).Count` → record baseline line count
- [ ] Draft P0 section (priority tier table + Windows Shell checklist + per-tool redirect table)
- [ ] Insert at line 1 (before all existing content)
- [ ] Verify existing §Windows Shell section — add forward-reference comment `> See §PRIORITY 0 above`
- [ ] Run validation: `rg "PRIORITY 0" AGENTS.md`; `rg "\*>" AGENTS.md`; `rg "pytest\|vitest\|pyright\|ruff" AGENTS.md`; `rg "Pre-flight" AGENTS.md`; `(Get-Content AGENTS.md).Count` ≥ baseline
- [ ] Create handoff `001-2026-03-25-agents-p0-windows-shell-bp00s0.0.md`

### MEU-B: Terminal Pre-Flight SKILL.md
- [ ] Read existing skill files (`.agent/skills/`) for frontmatter format reference
- [ ] Create `.agent/skills/terminal-preflight/SKILL.md`
- [ ] Verify 4-item checklist exactly matches AGENTS.md P0 items
- [ ] Verify SOP 4-step sequence
- [ ] Verify per-tool table present
- [ ] Run validation: `Test-Path`; `rg "name:"` frontmatter; `rg "Trigger\|trigger"`; `rg "\*>"`; `rg "redirect\|receipts\|no-pipe\|long-running"` (all 4)
- [ ] Create handoff `002-2026-03-25-terminal-preflight-skill-bp00s0.0.md`

### MEU-C: Workflow Amendments
- [ ] Read current `execution-session.md` — target §4b L77-110 for Pre-Completion Sweep (item 7)
- [ ] Add Amendment 1 (Terminal Pre-Flight callout) before first shell step in EXECUTION phase
- [ ] Add Amendment 2 (Pre-Completion Sweep as §4b item 7) after L110
- [ ] Read current `tdd-implementation.md` — confirm 3 test-run sites: L43-47, L62-66, L84-88
- [ ] Add P0 REMINDER block before each of the 3 test-run steps (all 3, not just 1)
- [ ] Run validation: `rg "P0 Terminal Pre-Flight"`; `rg "Pre-Completion Sweep"`; `rg -c "P0 REMINDER"` = 3; line counts ≥ baselines
- [ ] Create handoff `003-2026-03-25-workflow-amendments-bp00s0.0.md`

### BUILD_PLAN.md Check
- [ ] `rg "agents-terminal-optimization\|terminal-preflight\|PRIORITY 0" docs/BUILD_PLAN.md` → expect 0 matches
- [ ] Confirm no product phase rows need updating (this is infra, not product)
- [ ] Mark task complete with evidence (paste rg output)

---

## Exit Criteria

> The agent MUST NOT call `notify_user` until all items below are checked.

- [ ] Plan files corrected in `docs/execution/plans/2026-03-25-agents-terminal-optimization-infra/`
- [ ] All 3 MEUs executed
- [ ] 3 handoff files created with sequenced naming (001, 002, 003 with `bp00s0.0` suffix)
- [ ] BUILD_PLAN.md check completed (with evidence)
- [ ] `current-focus.md` changelog entry added
- [ ] Reflection file created
- [ ] Metrics table updated
- [ ] Proposed commit messages presented
