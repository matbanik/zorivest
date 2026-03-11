# Deep Research Prompts — Agentic Workflow Optimization

Generated: 2026-03-11

These prompts are designed for each platform's documented strengths. They include the actual changes made for validation and adversarial questions about potential downsides.

---

## Prompt 1: Gemini 3.1 Pro (Systematic Checklist Generation)

**Why Gemini**: Gemini 3.1 Pro excels at long-context code analysis (1M+ token context window), systematic software engineering workflows, and structured data synthesis (77.1% ARC-AGI-2, optimized for agentic workflows).

**Context to provide**: Attach all files listed in "Files to Include" below.

### Prompt

```
You are analyzing a dual-agent software engineering workflow where:
- Agent A (Claude Opus 4.6, "Opus") implements code changes following a TDD protocol
- Agent B (GPT-5.4 Codex, "Codex") reviews the implementation, producing adversarial findings
- The goal is to reduce the average number of review passes from 4-11 to 2-3

I've analyzed 7 critical review handoffs (37+ review passes total) and identified 10 recurring patterns. I then made specific changes to 6 workflow files, 1 agent config file, 1 role file, and created 1 new skill file to address these patterns.

## The 10 Patterns (frequency-ranked)

1. **Claim-to-State Drift** (7/7 reviews) — Opus says AC is met but code doesn't satisfy it
2. **Project Artifact Incompleteness** (6/7 reviews) — Post-project items lag behind code
3. **Evidence Staleness** (6/7 reviews) — Test counts and regression totals are wrong
4. **Mock-Based Test Masking** (5/7 reviews) — Green tests hide broken runtime
5. **Scope Overstatement** (5/7 reviews) — "Complete" while known gaps exist
6. **Fix-Specific-Not-General** (meta-pattern) — Fixing cited instance, not all same-category instances
7. **Canonical Doc Contradiction** (3/7 reviews) — Design change not propagated to all docs
8. **Stub Inadequacy** (3/7 reviews) — Stubs compile but violate behavioral contracts
9. **Error Mapping Gaps** (3/7 reviews) — Domain exceptions not mapped to HTTP codes
10. **Lifecycle Ordering** (3/7 reviews) — Post-project artifacts created before validation

## Changes Made

### execution-session.md — Added "Step 4b: Pre-Handoff Self-Review Protocol"
6-point mandatory checklist: claim-to-state verification, evidence freshness, fix-general-not-specific, error mapping sweep, cross-reference sweep, project artifact completeness.

### meu-handoff.md — Added "Live Runtime Probe Requirements"
Mandatory integration test with real stack (no dependency overrides), minimum probe sequence (Create→Get→List→Duplicate→Error→Filter), stub quality gate table, prohibited patterns list.

### critical-review-feedback.md — Added DR-6/7/8 + IR-1..IR-4
DR-6 (cross-reference integrity), DR-7 (evidence freshness), DR-8 (completion vs residual risk), plus Implementation Review Checklist with 4 checks.

### planning-corrections.md — Added Step 2b + Step 5b + Step 5c + Hard Rule #8
Step 2b: categorize-and-generalize findings. Step 5b: evidence refresh after all corrections. Step 5c: cross-doc sweep. Rule #8: fix-general principle.

### coder.md — Added rules 8/9/10
Rule 8: fix-general-not-specific. Rule 9: map ALL domain exceptions. Rule 10: stubs must honor behavioral contracts.

### GEMINI.md — Added Pre-Handoff Self-Review subsection + skill registration
7-point self-review protocol summary under Execution Contract, plus skill table entry.

### NEW: .agent/skills/pre-handoff-review/SKILL.md
7-step protocol with specific `rg` commands, pass/fail criteria for each check, and a 10-item checklist summary.

## Your Tasks

1. **Validate the changes**: Review each change against the 10 patterns it claims to address. For each change, answer:
   - Does this change actually prevent the pattern it targets?
   - Is the instruction specific enough that an AI agent will follow it consistently?
   - Are there edge cases where following this instruction would produce worse results?

2. **Generate a comprehensive pre-handoff quality checklist** that covers ALL 10 patterns with:
   - Specific `rg` / `grep` / `Get-ChildItem` commands to run
   - Expected output patterns (what "pass" looks like)
   - Failure indicators (what "fail" looks like)
   - Priority ordering (which checks to run first)

3. **Adversarial analysis** — answer these specific questions:
   - Could the "Fix-General-Not-Specific" rule cause over-correction, where an agent changes code it shouldn't because it's superficially similar but semantically different?
   - Could the "Live Runtime Probe" requirement make the implementation agent spend excessive time on integration tests for simple entity/DTO MEUs that don't touch routes?
   - Could the "Evidence Freshness" rule create a never-ending loop where counts keep changing because the agent keeps making tiny fixes?
   - Does the "Stub Quality Gate" prohibit `__getattr__` too broadly? Are there legitimate uses (e.g., proxy patterns, lazy loading)?
   - Could the "Cross-Reference Sweep" rule cause scope creep, where fixing one doc leads to chain-reaction updates across many files?
   - Is there a risk that the self-review protocol adds so much overhead that it slows down the implementation agent without proportional quality gains?
   - Are any of these rules contradictory with each other or with existing rules in AGENTS.md / GEMINI.md?

4. **Identify any missing patterns** — based on the handoff evidence, are there recurring issues I didn't capture in my 10 patterns?
```

### Files to Include
- All 7 critical review handoff files
- Updated `execution-session.md`, `meu-handoff.md`, `critical-review-feedback.md`, `planning-corrections.md`
- Updated `coder.md`, `GEMINI.md`
- New `pre-handoff-review/SKILL.md`
- `meta-reflection-patterns.md`

---

## Prompt 2: GPT-5.4 (Adversarial Gap Analysis)

**Why GPT-5.4**: GPT-5.4 excels at adversarial review, instruction following, reduced hallucination (65% fewer false claims vs o3), and deep agentic coding with up to 1M token context. It's the same model used as the reviewer agent (Codex), so it can evaluate rules from the reviewer's perspective.

**Context to provide**: Attach all files listed in "Files to Include" below.

### Prompt

```
You are GPT-5.4 Codex — the reviewer agent in a dual-agent workflow. Your counterpart (Claude Opus 4.6, "Opus") implements code; you review it adversarially. After analyzing 7 of your review handoffs (37+ passes total), the human orchestrator identified 10 recurring patterns and made changes to workflow files, role files, and created a new pre-handoff review skill.

Your job is to **adversarially review the proposed changes themselves** — applying the same rigor you'd apply to code review.

## Context

The changes target reducing review passes from 4-11 to 2-3. The 10 patterns are:
[Same 10 patterns as Prompt 1]

## Changes Made
[Same changes summary as Prompt 1]

## Your Tasks

### Task 1: Rule Stress Testing
For each new rule, construct a plausible scenario where:
a) The rule would be correctly triggered but the agent would misinterpret/misapply it
b) The rule would NOT be triggered but the underlying pattern would still occur
c) The rule would be triggered but the correct action is to NOT follow it

### Task 2: Rule Interaction Analysis
- Map the dependency graph between all new rules. Which rules depend on others?
- Identify any circular dependencies or contradictions
- Find rules that could conflict with existing AGENTS.md / GEMINI.md contracts
- Determine if the ordering of checks in the pre-handoff review skill matters (could early checks mask issues that later checks would catch?)

### Task 3: Coverage Gap Analysis
Based on your experience as the reviewer agent, list:
- Patterns you've seen in reviews that are NOT covered by any of the 10 identified patterns
- Situations where Opus would pass ALL 10 checks but you would still find HIGH findings
- Test categories that the "Live Runtime Probe" doesn't cover but should
- Types of evidence staleness that the "Evidence Freshness" rule wouldn't catch

### Task 4: Detrimental Effect Analysis
For each changed file, answer:
- **Could this change make Opus SLOWER without proportional quality gains?** Quantify where possible.
- **Could this change make Opus produce WORSE code by over-optimizing for reviewer compliance?** (e.g., writing tests that satisfy checklists rather than tests that catch real bugs)
- **Could the "Fix-General" rule cause regression by changing working code that superficially matches a pattern?**
- **Could the stub prohibition cause Opus to over-engineer early implementations?**
- **Could the mandatory integration test requirement block progress on MEUs that are genuinely unit-testable?**

### Task 5: Improved Rule Proposals
For any gap or detrimental effect you identified, propose a concrete rule improvement that closes the gap without introducing new problems. Use the same format as the existing rules.
```

### Files to Include
Same as Prompt 1.

---

## Prompt 3: Claude Opus 4.6 (Deep Reasoning Synthesis)

**Why Claude Opus 4.6**: Claude Opus 4.6 excels at structured multi-step reasoning, adaptive thinking, nuanced analysis with strong self-correction, and production-ready output. It's the same model used as the implementation agent (Opus), so it can evaluate rules from the implementer's perspective.

**Context to provide**: Attach all files listed in "Files to Include" below. Use extended thinking / deep reasoning mode if available.

### Prompt

```
You are Claude Opus 4.6 — the implementation agent in a dual-agent workflow. Your counterpart (GPT-5.4 Codex, "Codex") reviews your work adversarially. After 7 review cycles (37+ passes), the human orchestrator analyzed the patterns and made changes to the workflow rules you follow.

This is a deep reasoning task. Use extended thinking to analyze whether these changes will actually achieve the stated goal of reducing review passes from 4-11 to 2-3.

## Context

Your review history:
- rest-api-foundation: 11 passes, ~25 findings
- settings-backup-foundation: 10 passes, multiple KDF/wiring issues
- toolset-registry: 9 rechecks, mostly doc consistency
- market-data-foundation: 5 rounds, port contracts + evidence
- domain-entities-ports: 1 pass, lifecycle issues
- commands-events-analytics: 1 pass, test coverage issues

The 10 patterns are:
[Same 10 patterns as Prompt 1]

## Changes Made
[Same changes summary as Prompt 1]

## Your Tasks

### Task 1: Implementer Impact Assessment
As the agent who would follow these rules during implementation, analyze:

1. **Time overhead**: Estimate how much additional time (in tool calls or minutes) each new rule adds to a typical 4-MEU project session. Is it proportional to the quality gain?
2. **Cognitive load**: Do these rules create decision paralysis? Are there situations where multiple rules apply and their guidance conflicts?
3. **False positive risk**: For each `rg` command in the pre-handoff review skill, estimate the false positive rate. Would benign matches waste time investigating?

### Task 2: Structural vs Behavioral Classification
Classify each pattern as:
- **Structural** — can be caught by automated tooling (rg commands, linters, test frameworks)
- **Behavioral** — requires the agent to change its reasoning approach
- **Process** — requires workflow ordering changes

For structural patterns, propose specific automated checks that could replace manual agent vigilance. For behavioral patterns, analyze whether instruction changes alone are sufficient or whether the model needs different prompting techniques.

### Task 3: Root Cause Depth Analysis
The 10 patterns have surface-level root causes listed. Using your deep reasoning capability, analyze whether there are deeper systemic causes:

- Is claim-to-state drift actually caused by the TDD protocol itself? (Tests pass → agent assumes contract is met)
- Is fix-specific-not-general caused by the MEU scoping model? (Agent focuses on one MEU's scope, missing cross-MEU implications)
- Is evidence staleness caused by the handoff format? (Writing prose about numbers rather than embedding live command output)
- Are there upstream planning phase changes that would prevent these patterns from occurring in the implementation phase?

### Task 4: Detrimental Effect Analysis
Evaluate these specific risks as the agent who would follow these rules:

- **Over-verification paralysis**: Could the 7-step self-review protocol cause me to spend more time reviewing my own work than implementing? What's the right balance?
- **Checklist-driven behavior**: Could I start optimizing for passing the checklist rather than writing good code? (Goodhart's Law applied to agent instructions)
- **Stub prohibition scope**: The `__getattr__` prohibition is absolute. As the implementer, are there situations where I'd legitimately need this pattern and the prohibition would force a worse design?
- **Integration test mandate**: For pure entity/DTO MEUs (like market-data entities), would the integration test requirement add overhead without value?
- **Fix-general scope creep**: If I search for "all instances of the same category," how do I know when to stop? What if the category is broad (e.g., "any function that could throw an exception")?

### Task 5: Synthesis
Based on all the above analysis:
1. Rank the 10 patterns by which ones these changes will MOST effectively reduce
2. Rank them by which ones these changes will LEAST effectively reduce
3. Propose 3 specific improvements to the rules that would close the remaining gaps
4. Estimate the realistic pass reduction: will it actually reach 2-3, or is 3-5 more realistic?
5. Identify any rules that should be REMOVED because they would cause more harm than good
```

### Files to Include
Same as Prompt 1.

---

## Usage Instructions

1. **Run all 3 prompts independently** — don't let output from one influence input to another
2. **Use deep research / extended thinking modes** where available:
   - Gemini: Use Gemini Deep Research or standard generation with high token budget
   - GPT-5.4: Use reasoning_effort=xhigh via Pomera research action
   - Claude Opus 4.6: Use deepreasoning action via Pomera with thinking_budget=128000
3. **Synthesize results** — after all 3 return, look for:
   - **Agreement across all 3**: high confidence findings
   - **Disagreement**: areas needing further investigation
   - **Unique insights**: each platform will catch different things based on its strengths
4. **Act on synthesis** — update the workflow files based on the validated findings
