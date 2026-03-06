# Gap Remediation Plan — Agentic Infrastructure Improvements

> **Date**: 2026-03-06
> **Source**: gap-analysis.md (Antigravity brain artifact) + [synthesis.md](synthesis.md)
> **Purpose**: Plug the gaps between current Zorivest agentic infrastructure and research-backed best practices.
> **Validation**: This plan is intended for GPT-5.4 Codex review before execution.

---

## Scope

Six remediation tasks, ordered by priority. All changes are to `.agent/` configuration and `docs/execution/` — **no application code changes**. Total estimated effort: 2–3 hours.

> [!IMPORTANT]
> These are agentic infrastructure improvements, not product MEUs. They should be executed **before or alongside** the MEU-1 Calculator pilot so the pilot session can benefit from the improved handoff structure and metrics.

---

## Task 1: Create `docs/decisions/` Directory with ADR Template

**Gap**: Design decisions are currently embedded inline within handoff artifacts (the "Design Decisions & Known Risks" section in `meu-handoff.md`). With 114+ handoff files, decisions are scattered and unsearchable. The synthesis research cites Archgate (ADR validation for AI agents) and Claude's finding that "silent assumption propagation" is the highest-risk multi-agent failure mode. The build-plan scaffold (`01-domain-layer.md:19`) already defines `docs/decisions/ADR-0001-architecture.md`, so all ADRs are unified there.

**Outcome**: A dedicated, searchable registry for architectural decisions at `docs/decisions/`, referenceable by both agents, aligned with the build-plan scaffold.

### Files to Create

#### [NEW] `docs/decisions/TEMPLATE.md`

```markdown
# ADR-{NNNN}: {Title}

> Status: proposed | accepted | superseded | deprecated
> Date: {YYYY-MM-DD}
> Deciders: {agent name + human}

## Context

{What is the situation that motivates this decision? Include constraints, requirements, and relevant forces.}

## Decision

{What is the change that we're proposing and/or doing?}

## Consequences

### Positive
- {benefit}

### Negative
- {trade-off}

### Risks
- {what could go wrong}

## References

- Build plan section: {link}
- Related ADRs: {ADR-NNNN}
- Handoff: {link to handoff file if decision was made during implementation}
```

#### [NEW] `docs/decisions/README.md`

```markdown
# Architecture Decision Records

Decisions are numbered sequentially (ADR-0001, ADR-0002, etc.).
File naming: `ADR-{NNNN}-{kebab-case-title}.md`

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| — | — | — | — |

## When to Create an ADR

Create an ADR when a decision:
- Affects cross-package boundaries (core ↔ infra ↔ api ↔ mcp ↔ ui)
- Rejects a plausible alternative (document why)
- Is likely to be questioned by the other agent or by a future session
- Involves a trade-off with non-obvious consequences

## Integration with Handoffs

When a decision is made during MEU implementation, the handoff's "Design Decisions & Known Risks" section should **reference** the ADR by number (e.g., "See ADR-003") rather than inlining the full rationale.
```

#### [MODIFY] `.agent/context/handoffs/TEMPLATE.md`

Add ADR reference to the Coder Output section so review handoffs also capture decisions:

```diff
 ## Coder Output
 
 - Changed files:
-- Design notes:
+- Design notes / ADRs referenced:
 - Commands run:
 - Results:
```

### Files to Modify

#### [MODIFY] `.agent/workflows/meu-handoff.md`

Add an ADR reference instruction to the "Design Decisions & Known Risks" section of the template:

```diff
 ## Design Decisions & Known Risks
 
-- **Decision**: {what you chose} — **Reasoning**: {why, in 1-2 sentences}
+- **Decision**: {what you chose} — **Reasoning**: {why, in 1-2 sentences} — **ADR**: {ADR-NNNN if created, or "inline" if minor}
 - **Assumption**: {any assumption made during implementation}
 - **Risk**: {any edge cases not fully covered}
+
+> For decisions affecting cross-package boundaries or rejecting plausible alternatives, create a formal ADR at `docs/decisions/`. Reference it here by number.
```

#### [MODIFY] `.agent/roles/coder.md`

Add `decisions/` to the coder's input reading order:

```diff
 ## Inputs (Read In Order)
 
 1. `.agent/context/handoffs/{task}.md` (latest task handoff)
 2. `AGENTS.md`
-3. `.agent/docs/architecture.md`
+3. `docs/decisions/` (scan README index for relevant ADRs)
+4. `.agent/docs/architecture.md`
```

---

## Task 2: Deduplicate Instructions Between AGENTS.md and GEMINI.md

**Gap**: Combined instruction count is ~105, just above the research-recommended ≤100 ceiling. Approximately 10 instructions are duplicated between the two files. The ICLR 2025 "Curse of Instructions" study confirms that compliance decays multiplicatively with instruction count.

**Outcome**: Combined count reduced to ≤95 instructions with no loss of coverage.

### Duplications Identified

| Instruction | In AGENTS.md | In GEMINI.md | Resolution |
|-------------|-------------|-------------|------------|
| "One task = one session" | Line 45 | Line 52 | Keep in AGENTS.md, remove from GEMINI.md (replace with "See AGENTS.md §Session Discipline") |
| "Time is not a constraint" | Line 46 | Line 53 | Keep in AGENTS.md, remove from GEMINI.md |
| "Token usage is not a constraint" | Line 47 | Line 54 | Keep in AGENTS.md, remove from GEMINI.md |
| "Human approval required" | Line 52 | Line 63 | Keep in AGENTS.md, remove from GEMINI.md |
| "Save to pomera_notes" | Line 50 | Lines 61, 87 | Keep in AGENTS.md with naming convention, reference from GEMINI.md |
| "Update current-focus.md" | Line 50 | Line 62 | Keep in AGENTS.md, remove from GEMINI.md |

### Files to Modify

#### [MODIFY] `GEMINI.md` — §Execution Contract

Replace duplicated instructions with cross-references:

```diff
 ## Execution Contract
 
-- One task per session; do not combine unrelated work streams.
-- **Time is not a constraint.** Do not optimize for speed over quality.
-- **Token usage is not a constraint** (subscription-based). Do not truncate or skip work.
+- Follow `AGENTS.md` §Session Discipline for session rules, time/token policy, and session end protocol.
 - Run targeted tests after each change.
 - **MEU gate** (per-session): targeted `pytest`, `pyright`, `ruff`, and anti-placeholder scan scoped to touched packages/files.
```

```diff
-- Save session summary and next steps to `pomera_notes` with title `Memory/Session/Zorivest-{task}-{date}`.
-- Update `.agent/context/current-focus.md` with new state.
-- Human approval is required before merge/release/deploy.
+- Follow `AGENTS.md` §Session Discipline for session-end saves and human approval.
```

**Expected reduction**: ~10 instructions removed → combined total drops from ~105 to ~95.

---

## Task 3: Reorder Handoff Template for U-Shaped Attention

**Gap**: The meu-handoff template places "Design Decisions & Known Risks" in the middle of the document (after "Commands Executed"), which is exactly where the Liu et al. "Lost in the Middle" research shows LLMs lose 20%+ performance. The synthesis recommends front-loading decisions and back-loading next actions.

**Outcome**: Decisions moved to a high-attention position in the handoff template.

### Files to Modify

#### [MODIFY] `.agent/workflows/meu-handoff.md` — Template section order

Reorder the template sections from:

```
Current order:                     Proposed order (U-shaped optimized):
1. Scope                          1. Scope                    ← FRONT (high attention)
2. Feature Intent Contract        2. Feature Intent Contract  ← FRONT (high attention)
3. Changed Files                  3. Design Decisions & Risks ← MOVED UP (was #6)
4. Commands Executed              4. Changed Files
5. (blank space)                  5. Commands Executed        ← MIDDLE (low attention — OK for evidence)
6. Design Decisions & Known Risks 6. FAIL_TO_PASS Evidence    ← MIDDLE
7. FAIL_TO_PASS Evidence          7. Codex Validation Report  ← BACK (high attention)
8. Codex Validation Report
```

The key change: **Design Decisions & Known Risks** moves from position 6 to position 3, immediately after the Feature Intent Contract. This exploits the U-shaped attention curve — decisions are in the first third of the document where both agents and humans pay the most attention.

---

## Task 4: Extend Session Quality Metrics

**Gap**: `docs/execution/metrics.md` tracks 7 metrics but is missing two that the synthesis identifies as critical for data-driven improvement: **handoff completeness score** and **rule adherence rate**.

**Outcome**: Two additional columns added to the metrics table, with clear measurement definitions.

### Files to Modify

#### [MODIFY] `docs/execution/metrics.md`

Add two columns and a measurement guide:

```diff
 ## Session Metrics
 
-| Date | MEU(s) | Tool Calls | Time to First Green | Tests Added | Codex Findings | Prompt→Commit (min) | Notes |
-|------|--------|------------|---------------------|-------------|---------------|---------------------|-------|
-| 2026-03-06 | MEU-1 | — | — | — | — | — | Pilot |
+| Date | MEU(s) | Tool Calls | Time to First Green | Tests Added | Codex Findings | Handoff Score | Rule Adherence | Prompt→Commit (min) | Notes |
+|------|--------|------------|---------------------|-------------|---------------|---------------|----------------|---------------------|-------|
+| 2026-03-06 | MEU-1 | — | — | — | — | —/7 | —% | — | Pilot |
```

Add measurement definitions:

```markdown
## Measurement Definitions

### Handoff Score (X/7)
Count how many of these 7 required sections are substantively filled (not blank/placeholder):
1. Scope
2. Feature Intent Contract (with ACs)
3. Design Decisions (with at least one decision + reasoning)
4. Changed Files (with descriptions)
5. Commands Executed (with results)
6. FAIL_TO_PASS Evidence
7. Test Mapping (AC → test function)

### Rule Adherence (%)
At session end, score: (rules followed / rules applicable) × 100.
Sample the top 10 most-relevant rules from AGENTS.md + GEMINI.md for the session's task type. Document which rules were checked in the reflection file.

### Trend Alerts
- Handoff Score below 5/7 for 2+ consecutive sessions → review template compliance
- Rule Adherence below 70% for any rule across 3+ sessions → candidate for removal or rewording
```

#### [MODIFY] `.agent/workflows/execution-session.md` — §5e Update Metrics

Update the metrics template row to include new columns:

```diff
-| {YYYY-MM-DD} | MEU-{N} | {count} | {duration} | {count} | {count} | {duration} | {notes} |
+| {YYYY-MM-DD} | MEU-{N} | {count} | {duration} | {count} | {count} | {X}/7 | {N}% | {duration} | {notes} |
```

Update the column description:

```diff
-The columns are: Date, MEU(s), Tool Calls, Time to First Green, Tests Added, Codex Findings, Prompt→Commit (min), Notes.
+The columns are: Date, MEU(s), Tool Calls, Time to First Green, Tests Added, Codex Findings, Handoff Score (X/7), Rule Adherence (%), Prompt→Commit (min), Notes.
```

#### [MODIFY] `docs/execution/reflections/TEMPLATE.md` — §Efficiency Metrics

Extend the reflection template to include the new metrics and a rules-sampled table:

```diff
 | Codex findings | ___ |
 | Prompt→commit time | ___ |
+| Handoff Score (X/7) | ___ |
+| Rule Adherence (%) | ___ |
+
+### Rules Sampled for Adherence Check
+| Rule | Source | Followed? |
+|------|--------|----------|
+| _{rule description}_ | AGENTS.md §X | Yes/No |
```

This ensures the three-file schema (`metrics.md`, `execution-session.md`, `reflections/TEMPLATE.md`) stays aligned.

---

## Task 5: Create `skills/` Directory with Operational Loading

**Gap**: No `.agent/skills/` directory exists. All agent context is loaded upfront via AGENTS.md + GEMINI.md. The synthesis cites Gemini's research on "progressive skill disclosure" — loading only relevant SKILL.md files on demand prevents context window bloat as the codebase grows.

**Outcome**: Directory structure created with a README, and loading references added to `AGENTS.md` and `orchestrator.md` so agents actually discover and use skills.

### Files to Create

#### [NEW] `.agent/skills/README.md`

```markdown
# Agent Skills — Progressive Disclosure

Skills are domain-specific instruction sets loaded on demand, not at session start.
This prevents context window bloat as the project scales.

## When to Create a Skill

Create a SKILL.md when:
- A workflow involves domain-specific patterns not in AGENTS.md (e.g., SQLCipher encryption, Electron IPC)
- Instructions exceed 20 lines and apply to only one layer (core, infra, api, ui, mcp)
- A task requires specialized tool usage (e.g., database migration, audio generation)

## Skill Format

```yaml
---
name: {skill-name}
description: {one-line description}
applies_to: [packages/core, packages/infrastructure, etc.]
---

{Markdown instructions, examples, and patterns}
```

## Loading Strategy

- Agents read AGENTS.md + GEMINI.md at session start (always)
- Skills are loaded only when the task touches the skill's `applies_to` packages
- The orchestrator role determines which skills to load during PLANNING mode

## Planned Skills (populate as codebase grows)

| Skill | Applies To | Content |
|-------|-----------|---------|
| `sqlcipher-patterns.md` | packages/infrastructure | Encryption key management, migration patterns |
| `electron-ipc.md` | ui/ | Main↔renderer IPC protocol, preload scripts |
| `fastapi-patterns.md` | packages/api | Dependency injection, middleware, error responses |
| `mcp-tool-patterns.md` | mcp-server/ | Tool registration, schema validation, response format |
```

### Files to Modify

#### [MODIFY] `AGENTS.md` — §Context & Docs

Add a skills reference so agents know the directory exists:

```diff
 ## Context & Docs
 
 - Architecture → `.agent/docs/architecture.md`
+- Skills → `.agent/skills/` (load on-demand per task scope; see README inside)
 - Domain model → `.agent/docs/domain-model.md`
```

#### [MODIFY] `.agent/roles/orchestrator.md` — §Must Do

Add skill loading to the orchestrator's responsibilities:

```diff
 ## Must Do
 
 7. Require blocking validation checks to pass before declaring done.
+8. During PLANNING, check `.agent/skills/` for relevant skill files that match the task's target packages. Load applicable skills into context.
```

---

## Task 6: Update `docs/execution/README.md` Post-Implementation

**Gap**: The execution README currently documents a simplified 5-step lifecycle that predates the dual-agent workflow. It has been updated with the full 7-step lifecycle, governing files, artifact chain, and key safeguards — but after Tasks 1–5 are implemented, it needs a final pass to reflect the actual changes.

**Outcome**: README accurately documents the implemented infrastructure, including ADR references, reordered handoff sections, and extended metrics.

### Files to Modify

#### [MODIFY] `docs/execution/README.md`

After all other tasks are complete, update the README to reflect:

1. **Step 4 row** — add reference to `docs/decisions/` for ADR creation during implementation
2. **Key Safeguards** — add bullet: "ADR-based decision tracking for cross-boundary decisions (`docs/decisions/`)"
3. **Structure tree** — verify `metrics.md` description mentions the new Handoff Score and Rule Adherence columns
4. **Skills reference** — add note that `.agent/skills/` exists for progressive context loading when codebase grows
5. **Cross-verify** — ensure all governing file references in the 7-step table still point to correct file paths after Tasks 1–3 modified those files

> This task is intentionally last because it documents the final state after all other changes are applied.

---

## Verification Plan

Since all changes are documentation/configuration (no application code), verification is manual but structured:

### V1: Structural Verification

```powershell
# Verify all new directories and files exist
Test-Path docs/decisions/TEMPLATE.md
Test-Path docs/decisions/README.md
Test-Path .agent/skills/README.md
```

### V2: Instruction Count Verification

```powershell
# Count actionable instruction lines in both files (PowerShell-native)
# Actionable = lines starting with -, numbers, or containing "must", "never", "always", "do not"
# Target: combined ≤100
@("AGENTS.md","GEMINI.md") | ForEach-Object {
  $file = $_
  $count = (Select-String -Path $file -Pattern '^\s*[-\d]|must |never |always |do not ' -CaseSensitive:$false).Count
  "$file : $count actionable lines"
}

# Scan for duplicate bold-phrase instructions between files (safe escaping)
$agentsLines = (Select-String -Path AGENTS.md -Pattern '^\s*-\s+\*\*.+\*\*').Line | ForEach-Object { $_.Trim() }
$geminiLines  = (Select-String -Path GEMINI.md  -Pattern '^\s*-\s+\*\*.+\*\*').Line | ForEach-Object { $_.Trim() }
$duplicates = $agentsLines | Where-Object { $geminiLines -contains $_ }
if ($duplicates) { $duplicates | ForEach-Object { "DUPLICATE: $_" } } else { "No duplicates found" }
```

Manual check: Read through both files and confirm no duplicate instructions remain.

### V3: Handoff Template Section Order

Open `.agent/workflows/meu-handoff.md` and verify that "Design Decisions & Known Risks" appears immediately after "Feature Intent Contract" (position 3), before "Changed Files" (position 4).

### V4: Metrics Table Columns

Open `docs/execution/metrics.md` and verify:
- Table has 10 columns (was 8)
- New columns: "Handoff Score" and "Rule Adherence"
- Measurement Definitions section exists with clear formulas

### V5: Cross-Reference Integrity

Verify that:
- `meu-handoff.md` template references ADR format from `docs/decisions/TEMPLATE.md`
- `coder.md` input order includes `docs/decisions/` directory
- Handoff `TEMPLATE.md` Coder Output section includes "Design notes / ADRs referenced"
- `reflections/TEMPLATE.md` includes Handoff Score, Rule Adherence, and Rules Sampled table
- `AGENTS.md` §Context & Docs references `.agent/skills/`
- `orchestrator.md` §Must Do includes skill loading step
- `execution-session.md` metrics row matches `metrics.md` column count
- GEMINI.md Execution Contract references AGENTS.md Session Discipline (no inlined duplicates)

### V6: Codex Review Criteria

The reviewing agent (GPT-5.4 Codex) should validate:
1. **Consistency**: Do cross-references between files resolve correctly?
2. **Completeness**: Does the ADR template capture sufficient context for future agents?
3. **No regressions**: Does deduplication in GEMINI.md actually reduce instruction count without losing coverage?
4. **U-shaped optimization**: Is the handoff reorder justified by the Liu et al. research cited in the synthesis?
5. **Measurement feasibility**: Are the new metrics (Handoff Score, Rule Adherence) practically measurable during a session?

---

## Execution Order

| Order | Task | Depends On | Estimated Time |
|-------|------|-----------|----------------|
| 1 | Task 2: Deduplicate AGENTS.md / GEMINI.md | None | 15 min |
| 2 | Task 1: Create `decisions/` directory + ADR template | None | 20 min |
| 3 | Task 3: Reorder handoff template sections | Task 1 (ADR reference added) | 15 min |
| 4 | Task 4: Extend metrics table | None | 20 min |
| 5 | Task 5: Create `skills/` directory | None | 10 min |
| 6 | Task 6: Update `docs/execution/README.md` | Tasks 1–5 complete | 10 min |

**Total**: ~90 minutes

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Deduplication removes a nuance that GEMINI.md needs | Low | Medium | Cross-reference "See AGENTS.md §X" keeps full text accessible |
| ADR ceremony slows down implementation | Medium | Low | "inline" option for minor decisions; ADRs only for cross-boundary choices |
| New metrics columns forgotten during reflection | Medium | Low | execution-session.md template updated to prompt for them |
| Skills directory sits empty indefinitely | Low | None | README explains trigger conditions; no cost to having it ready |

---

## Success Criteria

- [ ] Combined AGENTS.md + GEMINI.md instruction count ≤ 100
- [ ] `docs/decisions/` exists with TEMPLATE.md and README.md (aligned with build-plan scaffold)
- [ ] `.agent/skills/` exists with README.md
- [ ] `AGENTS.md` §Context & Docs references `.agent/skills/`
- [ ] `orchestrator.md` §Must Do includes skill loading step
- [ ] Handoff `TEMPLATE.md` Coder Output includes "Design notes / ADRs referenced"
- [ ] meu-handoff.md template has "Design Decisions" in position 3 (after FIC, before Changed Files)
- [ ] `docs/execution/metrics.md` has 10 columns including Handoff Score and Rule Adherence
- [ ] `execution-session.md` metrics row format matches `metrics.md` column count
- [ ] `reflections/TEMPLATE.md` includes Handoff Score, Rule Adherence, and Rules Sampled table
- [ ] `coder.md` input order includes `docs/decisions/` scan
- [ ] No duplicate instructions remain between AGENTS.md and GEMINI.md
- [ ] Verification commands are PowerShell-native and runnable without errors
- [ ] `docs/execution/README.md` reflects all implemented changes (ADRs, reordered handoff, extended metrics, skills)
