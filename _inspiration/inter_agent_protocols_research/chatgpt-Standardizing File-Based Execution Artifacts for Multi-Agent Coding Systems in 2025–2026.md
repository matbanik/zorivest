# Standardizing File-Based Execution Artifacts for Multi-Agent Coding Systems in 2025–2026

## What “execution artifacts” have converged to mean in modern coding agents

Across 2025–2026 coding-agent products and open-source agent frameworks, “execution artifacts” have converged toward a layered set of **explicit, portable, file-backed representations** of: (a) the *rules and context* an agent must obey, (b) the *plan and checkpoints* an agent is executing against, and (c) an *inspectable audit trail* of what it actually did (commands, diffs, tool calls, test results). This is most visible in production-facing systems that support long-running or multi-step work, where reliability depends less on hidden reasoning and more on **checkpointing, validations, and inspectability**. citeturn2view2turn17view2turn11view6turn11view5

A practical way to frame the convergence is “three planes” of artifacts:

**Instruction plane (portable context):**
- Repo- or directory-scoped instruction files that are loaded automatically at the start of work, so behavior doesn’t depend on prior chat context. Codex’s **AGENTS.md** discovery and precedence rules exemplify this (global + repo + nested overrides, size cap, and auditability). citeturn7view0turn8view10turn18search26  
- Claude Code’s **CLAUDE.md** serves a similar purpose (project-root instructions loaded at session start). citeturn11view8

**Plan plane (agent-executable checkpoints):**
- A durable plan file with explicit milestones, acceptance criteria, and validation commands, designed so the agent can self-drive, verify, and recover without a human “remembering the thread.” The Codex long-horizon example is explicit about this pattern, including a “plan file as source of truth,” “stop-and-fix,” and continuous verification. citeturn2view2turn3view0turn4view0

**Trace plane (machine-readable event log / trajectory):**
- JSONL or JSON “event streams” capturing what the agent did step-by-step (commands executed, file changes, tool calls), often with typed events. Codex supports JSONL streaming for non-interactive runs and defines a typed “item/turn/thread” event model in its App Server protocol. citeturn17view2turn17view0turn11view3  
- OpenHands explicitly treats its event system as an immutable, append-only log that serves as the agent’s memory and integration surface, and its headless mode can emit JSONL events. citeturn11view7turn11view6  
- SWE-agent writes a structured trajectory file (`.traj`) containing thought/action/observation turns. citeturn11view5

Your constraint (two agents, file system only, no shared memory) pushes you to *make these three planes explicit and first-class*, and to ensure every handoff document carries: **(1) the operative context**, **(2) the checkpointed plan state**, and **(3) sufficient evidence pointers** to trace logs and verification outputs.

## Codex-oriented artifact formats for handoffs, completion evidence, and review loops

### What Codex surfaces as “internal work artifacts” in practice

Codex’s public materials make it unusually clear that the “artifact” boundary is not just code changes—it’s increasingly **structured plans, runbooks, and logs**.

In the long-horizon Codex case study (a 25-hour run), the author uses three explicit Markdown artifacts as *operational scaffolding*:

- `plans.md`: milestone-by-milestone checkpoints, each with acceptance criteria and validation commands. citeturn2view1turn3view0  
- `implement.md`: an execution runbook stating that `plans.md` is source of truth, requiring verification after each milestone, and enforcing a “write failing test → fix → verify” rule. citeturn2view2turn4view0  
- `documentation.md`: a continuously-updated “shared memory and audit log” with current milestone status, decisions, how to run/demo, and known issues. citeturn2view2turn4view1  

Those files (especially `documentation.md`) are effectively **codified handoff artifacts**: their purpose is explicitly to let someone step away for hours and still understand what happened. citeturn2view2

Codex also ships a **native plan mode** (CLI/app/IDE) invoked via `/plan`, reinforcing “plan as artifact before edits.” citeturn13search16turn17view4

### How Codex represents completion evidence and “what happened”

Codex offers *two* complementary evidence representations:

**Human-readable “final message” output files**
- In non-interactive mode, you can write the final response to a file (`--output-last-message` / `-o`). citeturn11view1turn17view2  
- In the Codex GitHub Action, you can save the final message to an `output-file` (e.g., `codex-output.md`) and post it back to the PR. citeturn6view0

**Machine-readable event logs (JSONL)**
- `codex exec --json` turns stdout into a JSONL stream of events; the docs enumerate event types `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.*`, `error`, and item types including command executions, file changes, web searches, and plan updates, with an explicit sample stream. citeturn17view2  
- At the protocol level, Codex’s App Server defines **Items** (typed atomic units with lifecycle `item/started → item/*/delta → item/completed`), grouped into **Turns**, grouped into durable **Threads** with persisted history. citeturn17view0turn17view1

For your filesystem-only multi-agent workflow, this implies a strong “best-of-both-worlds” pattern:

- Each agent emits a *readable* Markdown handoff, but every claim in it should point to **either a patch/diff** or to *trace-plane evidence* (test output, command logs, JSONL events).
- If you can’t persist full tool output safely in Markdown, persist it alongside as files and reference paths.

### Where “acceptance criteria” live in Codex-style setups

Codex’s long-horizon pattern puts acceptance criteria in the **plan artifact** itself (milestones + acceptance criteria + verification commands). citeturn2view1turn3view0

That’s not accidental; Codex’s own CLI/API surfaces “plan first” (via `/plan`) and emphasizes verification at checkpoints. citeturn13search16turn17view4turn2view2

A representative snippet (from the published `plans.md`) shows the exact structure that has emerged as a practical standard: “Scope → key files → acceptance criteria → verification commands,” repeated per milestone. citeturn3view0

### How the “review feedback loop” is structured in Codex ecosystems

Codex’s GitHub integration makes the loop structurally explicit:

- A user triggers a PR review by commenting `@codex review`. Codex replies as a “standard GitHub code review.” citeturn8view1  
- Review behavior can be customized via a `## Review guidelines` section in AGENTS.md; Codex applies the *closest* AGENTS.md to each changed file (directory-scoped policy). citeturn8view1turn7view0  
- Codex’s GitHub integration states that, by default, it flags only **P0 and P1** issues—this is an explicit severity gating choice that you can mirror for automation reliability. citeturn8view1

For automation and downstream processing, Codex also supports **schema-enforced review outputs**:

- The Codex GitHub Action documents passing an output schema (`--output-schema` via `codex-args`) and saving outputs to files. citeturn6view0turn17view2  
- A Codex cookbook example for code review shows using a JSON schema (`codex-output-schema.json`) so results can be mapped to precise code ranges in a PR workflow, and saving the resulting JSON (`codex-output.json`). citeturn11view4

This suggests a very robust structure for your Agent A → Agent B loop:

- Agent A emits a Markdown handoff plus (optionally) a structured JSON “handoff manifest.”
- Agent B emits a Markdown critical review plus a structured JSON “review findings” file that downstream automation can consume.

## YAML frontmatter and structured metadata standards that are actually emerging

### Two real, production-facing frontmatter convergences

**Agent Skills standard (SKILL.md)**
An unusually concrete 2025–2026 convergence is the **Agent Skills** authoring format, which *requires* YAML frontmatter in `SKILL.md`:

- Required fields: `name` and `description` with detailed constraints (length limits, allowed characters, and semantics that explicitly include “what it does and when to use it”). citeturn5view1turn5view4  
- Optional fields include `license`, `compatibility`, `metadata`, and experimental `allowed-tools`. citeturn5view1  
- Skills are designed for **progressive disclosure**: metadata loads first, full instructions later, references/scripts only on demand. citeturn5view4turn5view7  
- There is an explicit validation tool (`skills-ref validate`) and a `read-properties` mode that outputs JSON for programmatic use—this is directly relevant to “artifact linters.” citeturn14view0turn5view4

Codex explicitly “builds on the open agent skills standard” and describes the same progressive-disclosure behavior. citeturn5view7turn5view5

**Documentation frontmatter with schema validation (GitHub Docs)**
Another mature convergence is “Markdown + YAML frontmatter validated by a schema,” exemplified by GitHub Docs:

- GitHub Docs uses YAML frontmatter for page metadata and notes that its test suite validates frontmatter against a schema. citeturn1view7  
- In the GitHub Docs codebase, the frontmatter schema is a JSON Schema-like object with `required` keys and `additionalProperties: false`, plus enums and constraints—exactly the shape you want to prevent drift. citeturn12view4turn12view0  

This provides an existence proof that “human-readable Markdown documents with machine-enforceable frontmatter contracts” scales to very large doc sets with CI enforcement.

### Making frontmatter queryable without destroying readability

The most successful pattern across these ecosystems is:

1. Keep the frontmatter **short, shallow, and mostly scalar** (strings/booleans/enums).  
2. Put large content (long lists, logs, detailed evidence) **in the body or sidecar files**.  
3. Validate frontmatter with a JSON Schema and fail CI on schema violations (GitHub Docs does this for docs; Agent Skills does this for skills). citeturn12view4turn5view4turn14view0

If you want frontmatter validation tooling that operates on Markdown documents, there are established “remark/unified” lint rules that validate YAML frontmatter against JSON Schema (useful both locally and in CI). citeturn18search2turn18search21  
For general JSON Schema validation performance and ecosystem maturity, Ajv is a widely used reference implementation in JavaScript tooling. citeturn18search1turn18search25

### Which fields should be enums vs free text for grep/filter reliability

Based on what survives at scale in (a) schema-validated frontmatter (GitHub Docs) and (b) “routing metadata” (Agent Skills), the stable rule is:

**Use enums for fields that drive automation.**  
Examples: `artifact_type`, `status`, `verdict`, `severity`, `owner_role`, `scope_kind`, `risk_level`. (This makes grep + reliable downstream parsing possible, and makes drift detectable.) citeturn5view1turn12view4turn11view4

**Use free text only for fields that are inherently narrative.**  
Examples: `summary`, `rationale`, `notes`, `decision_log`.

**Use constrained strings (pattern/length) for identifiers.**  
Agent Skills’ `name` constraints are a good exemplar: short, lowercase, hyphenated names that map cleanly to folder names and are easy to reference. citeturn5view1

### Concrete frontmatter schemas for your “handoff” and “critical review” documents

Below are practical, production-oriented schemas inspired by (1) the plan/runbook/status pattern in long-horizon Codex work, (2) the “routing metadata” discipline of Agent Skills, and (3) schema-validation practices from doc platforms.

Handoff document (Agent A → Agent B):

```markdown
---
artifact_type: handoff
schema_version: "handoff.v1"
run_id: "run_2026-04-06T14-22-10Z_a1"
produced_by:
  agent: "agent_a"
  model: "claude-opus-4-6"
repo:
  root: "."
  branch: "feature/widget-x"
  base_branch: "main"
  head_commit: "abc1234"
scope:
  kind: feature
  area: ["payments", "api"]
status: ready_for_review   # enum
validation:
  policy: "tdd"
  commands:
    - "pytest -q"
    - "ruff check ."
    - "mypy ."
evidence:
  diff: "evidence/patch.diff"
  test_log: "evidence/tests.txt"
  trace_jsonl: "evidence/agent-a.exec.jsonl"
handoff_to: "agent_b"
---
# Summary
...
```

This directly mirrors how Codex long-horizon work externalizes “plan + verification + audit log” for inspectability. citeturn2view2turn3view0turn17view2

Critical review document (Agent B → Agent A):

```markdown
---
artifact_type: critical_review
schema_version: "review.v1"
review_id: "review_2026-04-06T16-05-31Z_b1"
review_of_run_id: "run_2026-04-06T14-22-10Z_a1"
produced_by:
  agent: "agent_b"
  model: "gpt-5-4-codex"
verdict: changes_required     # enum
severity_gate: ["P0", "P1", "P2"]
passes:
  - pass_id: 1
    mode: adversarial
    started_at: "2026-04-06T16-05-31Z"
    completed_at: "2026-04-06T16-18-02Z"
findings_json: "evidence/findings.json"
trace_jsonl: "evidence/agent-b.review.jsonl"
---
# Verdict
...
```

This aligns with Codex’s GitHub review practice of explicit severity gating (Codex-in-GitHub: P0/P1 default), which is useful for automations to avoid noisy failure modes. citeturn8view1turn6view0turn11view4

## Structuring implementation plans so they are executable by agents

### What distinguishes “agent-executable” plans from human-readable plans

Codex’s published long-horizon example is a clean definition of what “agent-executable” means in practice:

- Milestones “small enough to complete in one loop.” citeturn2view1turn3view0  
- Explicit “acceptance criteria + validation commands per milestone.” citeturn2view1turn3view0  
- A “stop-and-fix rule” if validation fails. citeturn2view1turn4view0  
- Decision notes to prevent oscillation and scope creep. citeturn2view1turn3view0  
- A separate runbook telling the agent to treat the plan as source of truth, keep diffs scoped, and continuously update documentation. citeturn4view0turn2view2  

The difference from a human-centric plan is that an agent plan must encode **all the “hidden glue” humans often keep in their heads**: commands, where tests live, what “done” means, and what to do when stuck.

### A plan format that maps cleanly to your MEUs

If you already use a task table, the key additions that consistently show up in agentic systems are:

- A stable **unit identifier** that can be referenced by other artifacts and logs.  
- Explicit **validation** per unit.  
- Machine-queryable **status** and **dependencies**.

A “MEU table” that stays human-readable but becomes tool-friendly when paired with frontmatter might look like:

```markdown
| # | MEU | Owner Role | Deliverable | Validation | Depends On | Status |
|---|-----|------------|-------------|------------|------------|--------|
| 1 | Add failing tests for Widget X | implementer | tests/test_widget_x.py | pytest -q tests/test_widget_x.py | - | done |
| 2 | Implement Widget X core logic | implementer | src/widget_x.py | pytest -q && ruff check . | 1 | done |
| 3 | Add API integration | implementer | src/api/routes.py | pytest -q && mypy . | 2 | in_progress |
| 4 | Update docs + runbook | implementer | docs/widget_x.md | doc build command | 3 | todo |
```

This mirrors the milestone structure in the widely-cited `plans.md` example: “key files/modules + acceptance criteria + verification commands,” repeated mechanically per checkpoint. citeturn3view0

### Dependency tracking that survives filesystem-only collaboration

When agents share only disk, you need dependency links that are resolvable without context. Two production-proven approaches are:

- **Backlinks via IDs** (e.g., `run_id`, `review_id`, `MEU-003`), stored in frontmatter + echoed in headings. This mirrors how Codex treats “threads” and “turns” as durable IDs that can be resumed and audited later. citeturn17view0turn17view3turn17view2  
- **Sidecar state snapshots** (`state.json`, `index.json`, or checkpoint DB), akin to LangGraph’s “threads” and step-wise checkpoints that enable replay, time travel, and resumption. citeturn11view9turn11view11  

Even if you don’t adopt LangGraph directly, the design principle carries: *every unit of work should be restartable from disk using stable identifiers*, not by re-reading a chat transcript. citeturn11view9turn17view2

## Review and audit trail artifacts that work for downstream automation

### Review document structure patterns that scale

Codex-in-GitHub gives two high-signal patterns worth copying:

- Reviews are posted as “standard GitHub code review,” which implies a stable external contract (review comments mapped to diffs, with an overall state like approve/request changes). citeturn8view1turn13search11  
- Reviews are filtered by severity (Codex flags P0/P1 by default), which makes automation decisions less brittle. citeturn8view1  

For machine-friendly review artifacts—especially when you want to map findings to code ranges—the Codex cookbook explicitly recommends schema-constrained outputs so you can reliably produce structured “comments on code ranges” in PR tooling. citeturn11view4turn17view2

### Severity classification schemes used in practice

You effectively have two families of severity schemes available, both widely used:

**Priority-based (“P0/P1/…”)**
- Explicitly used by Codex-in-GitHub, with default gating to P0 and P1. citeturn8view1  
- Works well when your downstream automation is “block merge if >= P1,” and when reviewers need “what’s urgent vs what’s polish.”

**Standardized analyzer levels (SARIF / code scanning)**
- SARIF supports `level` values such as `error`, `warning`, `note`, `none` in results, and GitHub code scanning explicitly surfaces alert levels Error/Warning/Note (plus separate security severity Critical/High/Medium/Low for CodeQL-style security findings). citeturn13search1turn13search26turn18search11  
- This family is compelling if you want to unify human review findings with static analyzers and security scanners in a single ingestion pipeline (since SARIF is designed as an interchange format). citeturn13search9turn13search10  

A pragmatic hybrid is to keep **P-levels** for agent review verdict gating, but emit a SARIF-compatible “level” field in structured findings so integration is easier later.

### Verdict formats that are automation-friendly and ecosystem-aligned

GitHub’s review APIs provide a crisp, widely-integrated set of review actions: `APPROVE`, `REQUEST_CHANGES`, `COMMENT` (with `PENDING` as a draft state). citeturn13search11turn13search5  

Even if you don’t write directly into GitHub, aligning your verdict enum to this family reduces translation layers. A minimal enum set that maps cleanly is:

- `approved`  → `APPROVE`
- `changes_required` → `REQUEST_CHANGES`
- `comment_only` → `COMMENT`
- `blocked` → (a stronger internal state; often maps to “changes_required” plus a blocking reason)

Codex’s own automation tooling reinforces “structured output” as the durable contract when you need stable fields. citeturn17view2turn11view4

### Multi-pass reviews: single document vs multiple documents

Modern agent systems support both patterns; the right choice depends on whether “review history” should be immutable:

- **Single document with appended passes** mirrors an “append-only log” philosophy (similar to OpenHands’ event stream as a log of events). citeturn11view7turn11view6  
  - Pro: one canonical review artifact.  
  - Con: harder to enforce immutability per pass.

- **One document per pass, linked by IDs** mirrors “threads and turns” (durable container + units) and is friendlier to schema validation and audit immutability. Codex’s own protocol primitives (Thread/Turn/Item) are conceptually aligned with this. citeturn17view0turn17view1  

For filesystem-only collaboration where you may later want forensic clarity, “one file per pass” usually wins: `critical_review.pass1.md`, `critical_review.pass2.md`, each referencing `review_of_run_id` and a `previous_review_id`.

## Preventing structural drift when you produce hundreds of artifacts

### What actually works in real implementations

The strongest anti-drift mechanisms documented in 2025–2026 agent tooling are **schema validation and explicit format contracts**—not “prompting harder.”

Three concrete, implementation-backed mechanisms:

**Schema-validated frontmatter**
- GitHub Docs validates YAML frontmatter against a schema and disallows unknown keys (`additionalProperties: false`). citeturn1view7turn12view4  
- This is exactly the kind of guardrail that prevents “template drift” across large artifact corpora.

**Dedicated validators for standardized artifact formats**
- Agent Skills includes `skills-ref validate`, plus “read properties” JSON output and prompt-generation utilities. citeturn14view0turn5view4  
- This is a direct analogue to “artifact linter / template validator” for skills, and the design generalizes well to your handoff/review docs.

**Schema-enforced outputs from agents themselves**
- Codex supports `--output-schema` (JSON Schema) to force stable structured outputs for automation and downstream steps, including review workflows. citeturn17view2turn11view4turn6view0  
- Codex App Server can generate JSON Schema bundles *per Codex version*, which is a powerful way to pin schemas and detect drift when clients upgrade. citeturn11view3turn17view0

### A practical “artifact linter” design for your system

A production-ready linter for your Markdown artifacts is typically two checks:

**Frontmatter contract check**
- Parse YAML frontmatter, validate against JSON Schema (fail on unknown keys, missing required keys, invalid enums/patterns).
- Tooling options include remark-based lint rules that validate frontmatter against JSON Schema, enabling both CI linting and editor feedback. citeturn18search2turn18search21  
- Ajv is a common implementation choice for JSON Schema validation in Node ecosystems. citeturn18search1

**Body structure check**
- Enforce required section headings (e.g., `# Summary`, `# Evidence`, `# How to Validate`, `# Risks`, `# Follow-ups`) and ensure they’re non-empty.
- Validate that evidence paths exist on disk (diff, test logs, JSONL traces) and that referenced MEU IDs are defined.

This mirrors how the Agent Skills ecosystem treats “frontmatter + body content + optional directories” as a single coherent contract with validation. citeturn5view4turn14view0

### Detecting deviation and course-correcting in-agent

Because you have a two-agent loop, you can combine mechanical linting with adversarial review:

- **Mechanical drift detection:** CI/pre-commit runs `artifact-lint` and fails if schemas/sections don’t match. (This catches “format drift” deterministically.)  
- **Adversarial format policing:** Agent B includes “schema violations” and “missing evidence” as first-class finding categories, and refuses `approved` verdict if the handoff lacks required evidence pointers.

This is consistent with Codex’s own operational philosophy in long-horizon work: “continuous verification” plus “runbook rules” to keep work inspectable and bounded. citeturn2view2turn4view0turn17view2

### Putting it together: an artifact set that matches your constraints

A filesystem-only, two-agent production system typically stabilizes around a directory structure like:

```text
artifacts/
  runs/
    run_..._a/
      handoff.md
      evidence/
        patch.diff
        tests.txt
        agent-a.exec.jsonl
    run_..._b/
      critical_review.pass1.md
      evidence/
        findings.json
        agent-b.review.jsonl
  schemas/
    handoff.v1.schema.json
    review.v1.schema.json
  index.json
```

This structure intentionally mirrors the durable-ID worldview present in Codex (threads/turns persisted; JSONL event streams) and in other agent systems (OpenHands JSONL events; SWE-agent trajectories). citeturn17view2turn11view6turn11view5
