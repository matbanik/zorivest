# Deep Research Prompts — Zorivest AGENTS.md Optimization

**Problem**: Claude Opus 4.6 repeatedly runs terminal commands in PowerShell, then waits for output even though the commands have already completed — causing session hangs. The current testing workflow (pytest, vitest, pyright, ruff) is not agentic-AI-friendly. AGENTS.md has conflicting priority signals across its sections.

---

## Prompt 1 — Gemini 3.1 Pro (Deep Research)

**Platform**: [aistudio.google.com](https://aistudio.google.com) → Model picker → **Gemini 3.1 Pro** → Enable **Deep Research** (or use **gemini.google.com** → Gemini app → AI Pro/Ultra plan)

**Why Gemini 3.1 Pro for this**: Released Feb 19, 2026, Gemini 3.1 Pro's Deep Think mode generates multiple competing hypotheses in parallel before synthesizing — scoring 77.1% on ARC-AGI-2 (double Gemini 3 Pro). Ideal for a problem with multiple possible root causes (context dilution, AGENTS.md instruction architecture, workflow scaffolding). Its 1M-token context allows ingesting the full AGENTS.md, all workflow .md files, and session logs in a single pass. Deep Research is optimized for task prioritization and detecting dead-ends — exactly what's needed for navigating a multi-file instruction architecture.

---

### PROMPT (copy-paste into Gemini 2.5 Pro Deep Research):

```
I am working with an AI coding agent (Claude Opus 4.6, codenamed "Kael") that operates inside a structured agentic workflow project called Zorivest. The agent is controlled by a file called AGENTS.md — a 355-line instruction document that defines its operating model, testing protocols, Windows PowerShell rules, commit policies, and more.

CRITICAL PROBLEM: The agent repeatedly runs terminal commands in PowerShell (such as `uv run pytest`, `npx vitest run`, `uv run pyright`) and then enters a waiting loop — polling for output even though the commands have already completed and written their results. This causes session hangs, requires repeated human correction, and violates a clearly stated rule in AGENTS.md (§Windows Shell, lines 279–305) that prohibits piping long-running processes to filters and requires redirect-to-file patterns instead.

I need your help with three interconnected research questions. Please conduct deep research across current AI agent engineering literature, PowerShell behavior documentation, and agentic system design best practices to produce a comprehensive, evidence-based analysis:

**Research Question 1: Instruction Architecture & Priority Hierarchy**
The AGENTS.md file contains these competing priority signals:
- §Session Discipline: "Quality-First Policy" — quality above all
- §Windows Shell: explicit pipe/filter prohibition with correct redirect pattern
- §Testing & TDD Protocol: Commands run after every change
- §Execution Contract: "Anti-premature-stop rule" — never stop mid-execution
- §Anti-Slop Checklist: verify before handoff

The agent correctly verbalizes the PowerShell rules when corrected, but reverts to the prohibited behavior in subsequent commands. This matches the "constraint erosion" pattern documented in long-context AI agents (arXiv 2601.11653). Research and answer:
- How should AGENTS.md be restructured so that the Windows Shell rules take execution-time priority over all other sections?
- Where in the instruction hierarchy should "terminal command rules" sit relative to "quality", "don't stop", and "test after every change"?
- What instruction patterns (repetition anchors, pre-flight checklists, decision trees) prevent constraint erosion in long agentic sessions?
- Should the Zorivest project adopt a separate "Terminal Policy" file with higher authority than AGENTS.md?

**Research Question 2: Agentic-Friendly Testing Workflow Design**
The current testing approach requires running pytest, vitest, pyright, ruff, and the validate_codebase.py script at multiple points during each MEU implementation cycle. This is what causes the agent to repeatedly enter the "run command → wait for completion" loop. Research and answer:
- What are the current best practices (as of 2026) for structuring automated test execution in agentic AI coding workflows?
- How should the MEU gate (`uv run python tools/validate_codebase.py --scope meu`) be redesigned as a skill or workflow step that produces file-based output the agent reads passively, rather than streaming output it waits for?
- What patterns do leading agentic workflows use (GitHub Continuous AI, Anthropic effective agent building, Google ADK) for making test result consumption non-blocking?
- Should the project adopt a "test receipt" pattern where all test runs write structured JSON/markdown output to a designated folder, and the agent reads receipts instead of waiting for process exit?

**Research Question 3: Workflow and Skill Redesign Recommendations**
The Zorivest project uses a set of .md skill files (git-workflow/SKILL.md, quality-gate/SKILL.md, pre-handoff-review/SKILL.md) and workflow files (execution-session.md, orchestrated-delivery.md, tdd-implementation.md). Research and answer:
- What should a "Terminal Command Pre-Flight" skill look like? Provide a template.
- How should the execution-session.md workflow be modified to enforce file-redirect behavior before any run_command call?
- What is the optimal placement and structure of validation steps within a TDD cycle to minimize agent-blocking waits?

Please produce: (1) a prioritized findings report with source citations, (2) a concrete restructured AGENTS.md §Windows Shell section, (3) a draft "Terminal Command Pre-Flight" skill file template, and (4) a recommended testing workflow redesign as a step-by-step execution-session workflow amendment.
```

---

## Prompt 2 — ChatGPT GPT-5.4 (Deep Research Mode)

**Platform**: [chatgpt.com](https://chatgpt.com) → Composer → Click the 🔍 **Deep Research** button → Submit

**Why GPT-5.4 Deep Research for this**: ChatGPT's Deep Research (now GPT-5.2/5.4-based) is optimized for synthesizing hundreds of web sources into structured, cited reports. Its Feb 2026 update adds real-time source control (restrict to trusted sites) and MCP server connectivity — useful for anchoring research to official Anthropic, OpenAI, and Microsoft docs. GPT-5.4 Thinking adds a preamble outlining its approach, so you can redirect mid-research. Best for generating an actionable engineering specification with evidence links.

**Before submitting**: In the Deep Research settings panel (Feb 2026 update), add these trusted domains: `docs.anthropic.com`, `learn.microsoft.com`, `docs.pytest.org`, `arxiv.org`, `platform.openai.com`

---

### PROMPT (copy-paste into ChatGPT Deep Research):

```
Conduct deep research to produce an engineering specification addressing a persistent failure mode in agentic AI development workflows.

## Context

I run a software project (Zorivest) that uses Claude Opus 4.6 as a coding agent. The agent operates under a structured instruction file (AGENTS.md) that controls its behavior. The project runs on Windows with PowerShell as the shell. The tech stack is Python (pytest, pyright, ruff) + TypeScript (vitest, tsc, eslint) in a monorepo.

## The Core Problem

Claude Opus 4.6 repeatedly violates this rule from AGENTS.md §Windows Shell:

> "Never pipe long-running commands through filters in PowerShell. Piping `vitest`, `pytest`, `npm run`, or any process that exits after producing output into `| Select-String`, `| findstr`, or `| Where-Object` causes the pipeline to hang indefinitely."

The correct pattern (already documented in AGENTS.md) is:
```powershell
# Correct: redirect to file, read after
uv run pytest tests/ > C:\Temp\out.txt 2>&1; Get-Content C:\Temp\out.txt | Select-Object -Last 30
```

Despite the rule being clearly written:
1. The agent verbalizes the rule when corrected by the human
2. The agent immediately reverts to the prohibited pattern in the next command
3. Three separate human corrections were required in one session
4. The agent also polls `command_status` repeatedly on background processes, which AGENTS.md also prohibits
5. When multiple git processes are spawned waiting for completion, they conflict and corrupt state

## Research Tasks

### Task 1: Root Cause Analysis — Instruction Retention in Long Agentic Sessions

Research the current scientific understanding of "constraint erosion" or "instruction drift" in long-context LLM agents (2024–2026 papers and practitioner reports). Specifically:
- Why do models that correctly verbalize a rule immediately violate it after correction?
- What cognitive/architectural mechanisms explain this (attention dilution, recency bias, instruction-following fine-tuning limits)?
- What prompt engineering or scaffolding patterns from current best practice mitigate this?
- Cite specific papers (arXiv preferred) and practitioner resources.

### Task 2: AGENTS.md Instruction Prioritization Redesign

Given the instruction file structure described above (Quality-First Policy, Windows Shell rules, TDD Protocol, Anti-premature-stop rule, Anti-Slop Checklist), provide:
- A concrete priority hierarchy for the top-level sections
- Which sections should appear first, which should be formatted as decision trees vs. prose, and which should be repeated as inline reminders at strategic points
- How to format the Windows Shell section so it functions as a "mandatory pre-flight gate" rather than a reference section
- Whether a separate RULES.md with explicit priority numbering (RULE-1 through RULE-N) would be more effective than embedding rules within AGENTS.md

### Task 3: Agentic-Friendly Terminal Command Workflow

Research and specify:
- The current best practice (2025–2026) for non-blocking test execution in agentic AI coding pipelines
- How to restructure the Zorivest testing workflow (pytest MEU gate → validate_codebase.py → pyright → ruff → vitest) as a "fire-and-read" pattern:
  1. All commands write to named output files under `C:\Temp\zorivest\`
  2. Agent reads output files after a fixed wait period (WaitMsBeforeAsync=10000)
  3. Agent never polls; reads are one-shot Get-Content
- Provide a complete redesigned testing workflow as a step-by-step skill file (Markdown format, YAML frontmatter)

### Task 4: Git Workflow Safety

Research best practices for preventing concurrent git operations in agentic contexts. Specifically:
- How should an AI agent handle a git commit that goes to background?
- What verification pattern (git log, file existence check) should replace command_status polling?
- What should the agent do when a git commit is stuck for >5 minutes?
- Provide a concrete decision tree the agent should follow.

## Deliverables Required

1. Root cause analysis with citations (500 words)
2. Restructured AGENTS.md priority hierarchy (table format)  
3. Redesigned Windows Shell section (formatted as a mandatory pre-flight checklist)
4. Complete testing workflow skill file (Markdown, ready to save as `SKILL.md`)
5. Git workflow decision tree (mermaid diagram or numbered list)

Please include URLs for all cited sources. Structure output as a formal engineering specification.
```

---

## Prompt 3 — Claude Opus 4.6 (Extended Thinking / Adaptive Mode)

**Platform**: [claude.ai](https://claude.ai) → Model: **Claude Opus 4.6** → Enable **Extended Thinking** (toggle in conversation settings) → Set effort to **Max**

**Why Opus 4.6 for this**: This is meta-research — asking Claude Opus 4.6 to reason about its own behavioral failure modes. Opus 4.6's adaptive thinking with max effort enables the deepest self-referential reasoning. Its web search + code execution tools are built-in, and the 1M token context means you can paste in the full AGENTS.md, multiple workflow files AND session log excerpts simultaneously. The 128k output token limit means comprehensive recommendations without truncation. Critically: Opus 4.6 has the strongest understanding of its own tool-calling architecture and can reason about `run_command`, `command_status`, and `WaitMsBeforeAsync` from a first-principles perspective.

**Before submitting**: Paste the full contents of the following files directly into the prompt:
1. `p:\zorivest\AGENTS.md` (paste full content under the AGENTS.MD heading)
2. `p:\zorivest\.agent\workflows\execution-session.md` (paste under EXECUTION WORKFLOW heading)
3. `p:\zorivest\.agent\skills\git-workflow\SKILL.md` (paste under GIT SKILL heading)
4. The "TERMINAL COMMAND VIOLATIONS" section below (already in the prompt)

---

### PROMPT (copy-paste into Claude Opus 4.6 with Extended Thinking, Max Effort):

```
<purpose>
You are performing a deep self-analysis and systems redesign task. I need you to reason carefully about your own behavioral failure patterns when operating as a coding agent in the Zorivest project, then produce concrete AGENTS.md amendments, new skill files, and workflow changes that will prevent those failures from recurring.

Use extended thinking with max effort. Take as long as needed. This is a critical quality improvement task.
</purpose>

<project_context>
AGENTS.MD:
[PASTE FULL AGENTS.MD CONTENT HERE]

EXECUTION WORKFLOW:
[PASTE CONTENT OF .agent/workflows/execution-session.md HERE]

GIT SKILL:
[PASTE CONTENT OF .agent/skills/git-workflow/SKILL.md HERE]
</project_context>

<documented_failure_patterns>
The following failure patterns were extracted from analysis of a real session log (70-73-session.md, 2402 lines) where you implemented MEU-73 (Email Provider Settings). These are your actual behaviors, not hypotheticals:

FAILURE PATTERN A — Terminal Command Piping (Critical, 12+ violations):
Despite AGENTS.md §Windows Shell explicitly prohibiting pipes to Select-String/rg/findstr, you ran:
  - `uv run pytest tests/ --tb=short -q 2>&1 | Select-String "FAILED|ERROR|assert"`
  - `uv run pytest tests/ -v --tb=no -q 2>&1 | Select-String "FAILED"`
  - `npx vitest run ... --reporter=verbose 2>&1 | rg "✓|×|PASS|FAIL"`
  - `uv run ruff check ... 2>&1 | Select-Object -Last 10`
All caused hangs. After human correction, you verbalized the rule ("Never pipe long-running commands"), then violated it again in the next 3 commands.

FAILURE PATTERN B — command_status Polling Loop (Critical, 8+ instances):
After running async commands, you called command_status 8 consecutive times waiting for pytest to complete, including:
  Line 835-845: 5 consecutive command_status calls on a single pytest run
  Line 960-963: 2 consecutive command_status calls after fixing test_models.py
AGENTS.md §Windows Shell requires redirect-to-file instead. The skill was not followed.

FAILURE PATTERN C — Competing Git Processes (Critical, 1 incident):
When agent-commit.ps1 went to background:
  1. You spawned a second git script (-SkipTests flag) — also background
  2. You ran a direct `git commit` — also background
  3. All 3 were competing simultaneously, corrupting state
The git skill says "stop, verify, never spawn more." You knew the rule (verbalized it), violated it anyway.

FAILURE PATTERN D — Premature corrections_applied Verdict (High):
After applying 4 correction-round findings, you declared `corrections_applied` and updated the handoff.
Immediately, a recheck found 3 more unresolved findings (F5: weak encryption test, F6: stale counts in 091 handoff, F7: dependency rule violation).
You had not run the pre-handoff-review skill before declaring completion.

FAILURE PATTERN E — Fix-Local-Not-Global (High, 3 rounds):
The same stale count issue (test counts in handoffs not matching actuals) appeared in correction rounds 1, 2, AND 3. Each round you fixed one location but did not sweep all count-bearing sections of affected files.

FAILURE PATTERN F — Scope Inference Too Narrow (Medium):
When asked to "check and validate MEU state", you read only documentation/handoff files and not the code. Human correction: "look at the code as well!" Required a second response to include actual file inspection.
</documented_failure_patterns>

<research_tasks>
Please perform the following, using extended thinking and web search as needed:

TASK 1 — Self-Diagnostic Root Cause Analysis
Reason carefully about WHY each failure pattern occurs at the architectural level:
- Pattern A/B/C: Why do you verbalize a rule and then violate it immediately? Is this attention dilution, instruction placement, fine-tuning artifacts, or something else? What does current research (2025-2026) say about "constraint erosion" in extended agentic sessions?
- Pattern D/E: Why does fixing a finding locally not trigger a global sweep? What cognitive shortcut leads to declaring completion before the pre-handoff-review skill is used?
- Pattern F: Why does "validate X" default to documentation-only scope rather than code+docs scope?

TASK 2 — AGENTS.md Redesign
Produce a concrete, implementation-ready redesign of AGENTS.md that addresses all 6 failure patterns:
- Restructure the instruction priority hierarchy so that Windows Shell rules are treated as a mandatory pre-flight gate before every run_command call
- Add a "Terminal Command Decision Tree" that must be traversed before submitting any command that runs pytest/vitest/npm/python/git
- Add a "Pre-Completion Mandatory Sweep" checklist that must be completed before any corrections_applied or task complete declaration
- Specify where in the file each new section should appear and why that placement reduces the risk of attention dilution

TASK 3 — New Skill File: Terminal Command Pre-Flight (SKILL.md)
Write a complete `.agent/skills/terminal-preflight/SKILL.md` file that:
- Provides a mandatory decision tree: "Before any run_command, answer these questions..."
- Specifies the exact redirect-to-file pattern for each tool category (pytest, vitest, pyright, ruff, git, validate_codebase.py)
- Specifies the WaitMsBeforeAsync values for each category
- Defines what "verification" looks like after each command (what to read, how much to read)
- Defines what to do when a command goes to background and seems stuck

TASK 4 — Testing Workflow Redesign
The current MEU testing cycle requires running 5+ separate commands (pytest, pyright, ruff, vitest, validate_codebase.py). Redesign this as a single `quality-gate` skill invocation that:
- Runs all checks sequentially via a PowerShell script that writes all results to `C:\Temp\zorivest\gate-{timestamp}\` folder
- Returns a single `gate-result.json` that the agent reads once
- Never requires the agent to wait for individual tool output
- Integrates with the existing `.agent/skills/quality-gate/SKILL.md` pattern

Provide the complete redesigned PowerShell script AND the updated SKILL.md section.

TASK 5 — Execution-Session Workflow Amendment
Amend `.agent/workflows/execution-session.md` to:
- Add a "Terminal Pre-Flight" mandatory step at the beginning of every EXECUTION phase
- Add a "Pre-Completion Sweep" mandatory step before any handoff is declared complete
- Specify how these steps integrate with the existing orchestrator/coder/tester/reviewer role transitions

Provide the complete amendment as a diff or full replacement of the relevant sections.
</research_tasks>

<output_format>
Produce your analysis and recommendations as a structured engineering document with these sections:
1. Root Cause Analysis (with citations to current research where available)
2. AGENTS.md Priority Redesign (as a complete rewritten §Windows Shell and §Execution Contract, plus a new §Mandatory Pre-Flight section)
3. Terminal Pre-Flight SKILL.md (complete file, ready to save)
4. Quality Gate Redesign (PowerShell script + SKILL.md update)
5. Execution-Session Workflow Amendment (diff format)
6. Implementation Priority (which changes have highest expected ROI per session)

Be specific. Cite exact line numbers from AGENTS.md where changes are needed. Provide exact markdown/YAML content ready to paste into files.
</output_format>
```

---

## Submission Notes

| Platform | URL | Model | Feature to Enable |
|----------|-----|-------|-------------------|
| Gemini Deep Research | [aistudio.google.com](https://aistudio.google.com) | **Gemini 3.1 Pro** | Toggle "Deep Research" in composer |
| ChatGPT | [chatgpt.com](https://chatgpt.com) | **GPT-5.4 Thinking** | Click 🔍 icon in composer → "Deep Research" |
| Claude | [claude.ai](https://claude.ai) | **Claude Opus 4.6** | Extended Thinking toggle → Effort: Max |

**Before submitting Prompt 3 to Claude**: Paste the actual file contents of `AGENTS.md`, `execution-session.md`, and `git-workflow/SKILL.md` into the designated `[PASTE ... HERE]` placeholders. The longer the context you provide, the more specific the recommendations will be.

**After receiving results**: Compare the three outputs side by side. Gemini will produce the most systematic document synthesis, GPT-5.4 the most structured specification with citations, and Opus 4.6 the most nuanced self-referential recommendations. Combine into a single `RULE-UPGRADE-2026-03-25.md` and apply as amendments to AGENTS.md and the relevant skill/workflow files.
