# Agent Terminal Optimization Infrastructure

**Project slug:** `agents-terminal-optimization-infra`  
**Date:** 2026-03-25  
**Source:** [`_inspiration/agents_terminal_optimization/COMPOSITE-synthesis-agent-terminal-optimization.md`](../../../../_inspiration/agents_terminal_optimization/COMPOSITE-synthesis-agent-terminal-optimization.md)  
**Type:** Agent infrastructure (not BUILD_PLAN product feature)  
**Codex review:**  `.agent/workflows/validation-review.md`

## Background

Three parallel deep research reports (ChatGPT GPT-5.4, Claude Opus 4.6, Gemini 3.1 Pro Deep Research) independently converge on the same diagnosis and fix class for two chronic Zorivest agentic failure modes:

1. **Terminal blocking** — Opus 4.6 executes `pytest`/`vitest`/`pyright` directly in the active terminal, causing PowerShell buffer saturation and indefinite polling loops (requiring human intervention, costing 10–30 min per incident).
2. **Constraint erosion** — AGENTS.md Windows Shell rules lose attention weight by mid-session (~80K tokens = ~1% weight), causing rule re-verbalization without behavioral adherence.

Root cause: both failures are architectural. PowerShell's six-stream output model causes buffer-saturation hangs on unredirected commands. The Transformer attention mechanism dilutes early instructions proportionally with context growth. Neither can be fixed by adding more clarifying text in an existing prose section.

**Solution class (all three reports):** Move enforcement outside the model — pre-flight checklists, structured skill files invoked by name, and workflow-embedded reminders — rather than relying on the model remembering rules from a single prose mention in a long file.

> [!IMPORTANT]
> This project modifies `AGENTS.md`, `.agent/` skill files, and workflow `.md` files. These are the agent's primary operating instructions. Changes here directly affect every future agentic session on this repository. Codex must validate that no existing rules are inadvertently removed or weakened, and that all new rules are internally consistent with existing sections.

---

## Spec Sufficiency

All behaviors are sourced from the COMPOSITE synthesis document; no product BUILD_PLAN spec is required. All behaviors have `Research-backed` or `Local Canon` provenance.

| MEU | Behavior / Contract | Source Type | Source | Resolved? |
|-----|---------------------|------------|--------|-----------|
| A | P0 block placed at lines 1–N (before all other content) in AGENTS.md | Research-backed | COMPOSITE §Part 2, ChatGPT §Priority Hierarchy | ✅ |
| A | 4-item PowerShell pre-flight checklist (redirect, receipts dir, no-pipe, bg-flag) | Research-backed | COMPOSITE §5.1, Gemini Deliverable 1 | ✅ |
| A | `*>` operator (all-stream) specified, not `>` (stdout only) | Research-backed | COMPOSITE §3.1, Gemini §The Mechanical Reality | ✅ |
| A | Per-tool redirect table (pytest, vitest, pyright, ruff, validate_codebase.py, git) | Research-backed | ChatGPT §Testing Workflow Skill, Gemini Deliverable 1 | ✅ |
| A | 4-tier priority hierarchy (P0–P3) table retained in AGENTS.md body | Research-backed | COMPOSITE §Part 2, Gemini §Formalizing the Instruction Hierarchy | ✅ |
| B | SKILL.md trigger: "MUST activate before any `run_command`" | Research-backed | COMPOSITE §5.2, Gemini SKILL-TERM-001 | ✅ |
| B | 4-item pre-flight checklist matches AGENTS.md P0 (single source of truth) | Research-backed | COMPOSITE §4.1 convergence point | ✅ |
| B | SOP: Declare → Formulate → Execute+Detach → Consume Artifact | Research-backed | COMPOSITE §4.1, Gemini §SOP | ✅ |
| B | Example thought process block included | Research-backed | Gemini Deliverable 2 §Example Execution Pattern | ✅ |
| C | `execution-session.md`: terminal pre-flight callout before first shell step | Research-backed | COMPOSITE §5.4, Gemini §Redesigning the Execution Session | ✅ |
| C | `execution-session.md`: Pre-Completion Sweep gate (rg sweep + pre-handoff-review) | Local Canon | COMPOSITE §5.4; meta-review Rule RULE-2 | ✅ |
| C | `tdd-implementation.md`: P0 inline reminder before each test-run numbered step | Research-backed | COMPOSITE §5.5, Claude §Periodic re-injection | ✅ |
| ALL | No existing AGENTS.md rules deleted or weakened | Local Canon | AGENTS.md (live file) | ✅ |
| ALL | docs/BUILD_PLAN.md: no product rows to update; check for stale refs | Local Canon | create-plan workflow §4 mandatory check | ✅ |

---

## Proposed Changes

### MEU-A — AGENTS.md Priority-0 Restructure

**Handoff:** `001-2026-03-25-agents-p0-windows-shell-bp00s0.0.md`

#### [MODIFY] [AGENTS.md](file:///p:/zorivest/AGENTS.md)

Insert at line 1 (before all existing content), a new `## PRIORITY 0 — SYSTEM CONSTRAINTS` section containing:

1. **Priority tier table** (P0–P3) explaining why environment stability ranks above task completion speed
2. **Windows Shell mandatory redirect block** with:
   - The `INCORRECT` vs `CORRECT` pattern (direct run vs `*>` redirect)
   - 4-item pre-flight checklist (must be satisfied before every `run_command`)
   - Per-tool redirect table: exact command strings for `pytest`, `vitest`, `pyright`, `ruff`, `validate_codebase.py`, `git`
   - One-liner fire-and-read pattern: `<command> *> C:\Temp\zorivest\<name>.txt; Get-Content C:\Temp\zorivest\<name>.txt | Select-Object -Last 40`

**Preservation rule (unambiguous):** No existing AGENTS.md content is deleted. The new P0 section is prepended before all existing content. If the existing `§Windows Shell` section contains rules that overlap with the new P0 block, those rules are retained in place with a forward-reference comment added (e.g., `> See §PRIORITY 0 above for the authoritative version`). This ensures total line count only increases.

**FIC Acceptance Criteria:**

| # | Criterion | Source |
|---|-----------|--------|
| AC-1 | `rg "PRIORITY 0" AGENTS.md` returns a match in the first 30 lines | Research-backed |
| AC-2 | `rg "\*>" AGENTS.md` returns ≥ 1 line showing the all-stream redirect operator | Research-backed |
| AC-3 | `rg "pytest\|vitest\|pyright\|ruff" AGENTS.md` shows at least one redirect example per tool | Research-backed |
| AC-4 | `rg "Pre-flight checklist\|pre-flight" AGENTS.md` returns a match | Research-backed |
| AC-5 | Total line count of AGENTS.md after edit ≥ original line count (no deletions) | Local Canon |

---

### MEU-B — Terminal Pre-Flight SKILL.md

**Handoff:** `002-2026-03-25-terminal-preflight-skill-bp00s0.0.md`

#### [NEW] [SKILL.md](file:///p:/zorivest/.agent/skills/terminal-preflight/SKILL.md)

New skill file at `.agent/skills/terminal-preflight/SKILL.md` conforming to the existing skill frontmatter format (`name:`, `description:`).

Contents:

1. **Trigger** — must be invoked before any `run_command` / terminal execution tool
2. **Objective** — prevent PowerShell buffer saturation and session hang
3. **4-item Pre-Flight Checklist:**
   - `[ ]` Redirect check: command ends with `*> [filepath]`
   - `[ ]` Receipts dir: output routed to `C:\Temp\zorivest\` (or `.zorivest\receipts\`)
   - `[ ]` No-pipe check: no `|` to long-running right-hand process
   - `[ ]` Long-running flag: if validation script, configured to write structured output
4. **SOP** (numbered steps): Declare → Formulate → Execute+Detach → Consume
5. **Per-tool command table** matching AGENTS.md P0 (single source of truth — do not duplicate prose, cross-reference P0)
6. **Example thought process block** showing agent self-narration invoking the skill

**FIC Acceptance Criteria:**

| # | Criterion | Source |
|---|-----------|--------|
| AC-1 | File exists at `.agent/skills/terminal-preflight/SKILL.md` | Research-backed |
| AC-2 | `rg "name:" .agent/skills/terminal-preflight/SKILL.md` shows valid frontmatter | Local Canon (skill format) |
| AC-3 | `rg "Trigger\|trigger" .agent/skills/terminal-preflight/SKILL.md` confirms trigger clause | Research-backed |
| AC-4 | `rg "\*>" .agent/skills/terminal-preflight/SKILL.md` confirms redirect operator documented | Research-backed |
| AC-5 | File contains all 4 checklist items (redirect, receipts, no-pipe, long-running) | Research-backed |

---

### MEU-C — Workflow Amendments (execution-session + tdd-implementation)

**Handoff:** `003-2026-03-25-workflow-amendments-bp00s0.0.md`

#### [MODIFY] [execution-session.md](file:///p:/zorivest/.agent/workflows/execution-session.md)

**Amendment 1 — Terminal Pre-Flight Gate:**  
In the EXECUTION phase section, immediately before the first numbered step that invokes a shell command, add a callout block:

```markdown
> ⚠️ **P0 Terminal Pre-Flight** — Before the first `run_command` in this phase, invoke
> `.agent/skills/terminal-preflight/SKILL.md` and confirm all 4 checklist items.
> See `AGENTS.md §PRIORITY 0` for the redirect pattern.
```

**Amendment 2 — Pre-Completion Sweep Gate:**  
In `execution-session.md` §4b "Pre-Handoff Self-Review Protocol" (currently L77-110), append as item **7** after item 6 "Project Artifact Completeness" (L107-110):

```markdown
7. **Pre-Completion Sweep** (Pattern: count-bearing string drift, meta-review RULE-2)
   - `rg` all count-bearing strings (test counts, "passing", "FAIL_TO_PASS") across ALL touched handoffs/docs.
   - Cross-check every file listed in the handoff evidence table exists on disk: `Test-Path <path>` for each.
   - Run `pre-handoff-review` SKILL (`.agent/skills/pre-handoff-review/SKILL.md`) — 10-pattern self-check.
   - Only after all three sub-steps pass: mark complete and set `corrections_applied`.
```

#### [MODIFY] [tdd-implementation.md](file:///p:/zorivest/.agent/workflows/tdd-implementation.md)

Before each numbered step that executes tests (e.g., "Run tests", "Run pytest", "Execute test suite"), prepend:

```markdown
> ⚠️ **P0 REMINDER:** Use redirect-to-file pattern for all shell commands.
> `uv run pytest tests/ *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40`
> Never pipe directly. See `AGENTS.md §PRIORITY 0` and `terminal-preflight/SKILL.md`.
```

**FIC Acceptance Criteria:**

| # | Criterion | Source |
|---|-----------|--------|
| AC-1 | `rg "P0 Terminal Pre-Flight\|terminal-preflight" .agent/workflows/execution-session.md` returns ≥ 1 match | Research-backed |
| AC-2 | `rg "Pre-Completion Sweep" .agent/workflows/execution-session.md` returns ≥ 1 match | Local Canon (RULE-2 from meta-review) |
| AC-3 | `rg -c "P0 REMINDER" .agent/workflows/tdd-implementation.md` returns exactly `3` (one per test-run site: L43-47, L62-66, L84-88) | Research-backed |
| AC-4 | Line count of execution-session.md ≥ original (213 lines): `(Get-Content .agent/workflows/execution-session.md).Count` | Local Canon |
| AC-5 | Line count of tdd-implementation.md ≥ original (120 lines): `(Get-Content .agent/workflows/tdd-implementation.md).Count` | Local Canon |

---

### BUILD_PLAN.md Check (All MEUs)

This project adds agent infrastructure only — no product features are implemented and no BUILD_PLAN.md product phase changes. The mandatory check task:

**Validation:** `rg "agents-terminal-optimization\|terminal-preflight\|P0" docs/BUILD_PLAN.md` → expected: 0 matches (correct — this is infrastructure, not tracked in BUILD_PLAN product table). Confirm no stale references to the COMPOSITE synthesis file exist in BUILD_PLAN.md that would need updating.

---

## Verification Plan

### Automated Checks

```powershell
# MEU-A acceptance criteria
rg "PRIORITY 0" AGENTS.md
rg "\*>" AGENTS.md
rg "pytest" AGENTS.md
rg "Pre-flight" AGENTS.md

# MEU-B acceptance criteria
Test-Path ".agent\skills\terminal-preflight\SKILL.md"
rg "name:" .agent\skills\terminal-preflight\SKILL.md
rg "Trigger" .agent\skills\terminal-preflight\SKILL.md

# MEU-C acceptance criteria
rg "P0 Terminal Pre-Flight" .agent\workflows\execution-session.md
rg "Pre-Completion Sweep" .agent\workflows\execution-session.md
rg -c "P0 REMINDER" .agent\workflows\tdd-implementation.md  # must be exactly 3
(Get-Content .agent\workflows\execution-session.md).Count   # must be ≥ 213
(Get-Content .agent\workflows\tdd-implementation.md).Count   # must be ≥ 120

# No regression to existing AGENTS.md rules
# (Codex to verify: line count before vs after, no deleted rules)
```

### Codex Adversarial Review Focus

1. **Rule integrity**: Verify no existing AGENTS.md rules were deleted, paraphrased-to-weaken, or moved in a way that reduces their prominence (primacy effect matters)
2. **Checklist consistency**: AGENTS.md P0 checklist items 1–4 must exactly match SKILL.md checklist items 1–4 (single source of truth, no drift between files)
3. **Workflow completeness**: Confirm both workflow amendments are present in the correct phase of each workflow (not buried in a phase that doesn't involve shell commands)
4. **Scope discipline**: Confirm tools/run-gate.ps1 (Test Receipt script) is NOT in scope for this project — it is deferred to a future MEU requiring Python implementation + TDD

### Manual Verification

Not required for this project (doc/config only — no executable code changes).

---

## Handoff Naming

> **Infrastructure sentinel (`Human-approved`):** This project has no `docs/build-plan/` section. The canonical convention `{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md` (`create-plan.md` §Handoff Naming L135, L192) requires a `bp{NN}s{X.Y}` suffix for parseable naming. `bp00s0.0` is adopted as the sentinel value for infrastructure/meta projects with no build-plan section. Source: `Human-approved` — decision artifact: `pomera_notes` ID 699 (`Memory/Decisions/bp00s0.0-infra-handoff-sentinel-2026-03-25`), recording user's explicit LGTM approval of this convention on 2026-03-25.

```
001-2026-03-25-agents-p0-windows-shell-bp00s0.0.md
002-2026-03-25-terminal-preflight-skill-bp00s0.0.md
003-2026-03-25-workflow-amendments-bp00s0.0.md
```

Sequence starts at `001` (no prior sequenced handoffs exist; all existing handoffs use legacy `YYYY-MM-DD-` prefix per create-plan workflow §Handoff Naming bootstrap note).
