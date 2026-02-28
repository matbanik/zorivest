# Dual-Agent Coding Workflow: Composite Research Synthesis

> **Sources**: ChatGPT Deep Research, Claude Research (Opus 4.6 + Web Search), Gemini Deep Research
> **Date**: 2026-02-28
> **Scope**: Claude Opus 4.6 (implementation) + GPT 5.3 Codex (validation) — community practices, tooling, pitfalls
> **Legend**: 🟢 CONSENSUS (all 3 agree) · 🔵 CONFIRMED (2/3 agree) · ⚪ UNIQUE (1 source)

---

## 1. Executive Summary

All three research reports independently converge on the same core finding: **"Claude builds, Codex validates" is the dominant dual-agent pattern in the 2026 developer community**, supported by production tooling (VS Code v1.109, MCP bridges, GitHub Actions) and practitioner evidence. The pattern works because Opus 4.6 excels at deep architectural reasoning and greenfield development (1M-token context, extended planning), while Codex 5.3 excels at terminal-native execution, aggressive codebase exploration, and precise code review (77.3% Terminal-Bench 2.0 vs Opus's 65.4%).

However, all three reports also agree on a critical caveat: **the human orchestrator is not optional**. The METR randomized controlled trial found developers *believe* AI makes them 20% faster while *actually being 19% slower* (on mature codebases with older models). Two AIs can confidently agree on a bad design. The dual-agent workflow is best understood not as replacing human judgment but as making review discipline automatic.

**Three universal warnings**:
1. **TDD theater** — AI-generated tests validate implementations, not intentions
2. **Rubber-stamp reviews** — Codex approving everything without real scrutiny
3. **Handoff quality** — the artifact passed between agents is the bottleneck, not the models

---

## 2. Agent Strengths & Role Assignment

### 🟢 CONSENSUS: Opus = Architect/Builder, Codex = Reviewer/Validator

| Capability | Opus 4.6 | Codex 5.3 | Source |
|------------|----------|-----------|--------|
| Deep architectural reasoning | ★★★★★ | ★★★☆☆ | All 3 |
| 1M-token context | ★★★★★ | ★★★☆☆ | Claude, Gemini |
| Terminal-Bench 2.0 | 65.4% | 77.3% | Gemini |
| Token generation speed | Slower (deliberate) | ~240 tok/s (25% faster than predecessor) | Gemini |
| Edge case detection | Misses when context is long | Catches Opus misses | ChatGPT, Claude |
| Error handling | Skips under long context | Over-engineers but thorough | Claude |
| Code review quality | "Verbose without catching bugs" | "Finds legitimate, hard-to-spot bugs" | Claude (Builder.io CEO) |
| Failure mode | "Opus Slop" — bypassed edge cases, type loopholes | Over-engineering — 80K lines of pedantic tests | Gemini |

### 🔵 CONFIRMED: Reddit Community Preference

- 65.3% of direct comparison comments preferred Codex (79.9% upvote-weighted) — Claude
- Claude generated 4× more discussion volume — Claude
- Consensus framing: "Claude as big-picture planner, Codex as shell-first surgeon" — Claude

### 🔵 CONFIRMED: Builder.io CEO (Steve Sewell) Recommendation

> "Design architecture and run deep investigations with Claude Code, then pass focused implementation tasks to Codex for fast execution." — Claude, Gemini

---

## 3. Workflow Patterns

### 🟢 CONSENSUS: Standard Session Flow

All three reports describe essentially the same flow:

```
1. PLAN      Human scopes task, provides requirement
2. SPEC      Opus reads repo context, generates implementation plan
3. IMPLEMENT Opus writes tests + code (TDD), pushes rapid iterations
4. CHECKPOINT State saved — git commit + handoff artifact created
5. VALIDATE  Codex reads handoff + changed files, runs tests, reviews
6. FEEDBACK  Codex issues verdict — approved / changes_required
7. ITERATE   If changes_required, feedback routes back to Opus (max 3 rounds)
8. MERGE     Human approves final result
```

### 🟢 CONSENSUS: Git Worktree Isolation

All three reports emphasize isolating each agent in its own git branch/worktree:
- Prevents agents from overwriting each other's work
- Primary branch stays pristine until validation completes
- Enables parallel agent execution without collision

### 🔵 CONFIRMED: Multi-Session Orchestration

- Multi-agent orchestrator (initially Bash/AppleScript, later TypeScript) manages many Claude and Codex sessions in parallel — ChatGPT
- Simon Willison: multiple terminal windows with Claude Code and Codex CLI in different directories using git worktrees — Claude
- "Parallel Code" desktop app for managing AI agent sessions — Claude

### ⚪ UNIQUE: Traycer Planning Tool

- Traycer drafts a plan, Claude implements, Codex reviews against original plan — ChatGPT
- Creates file-level to-do lists so agents only see what they need — ChatGPT

---

## 4. Handoff Engineering

### 🟢 CONSENSUS: Handoff Is the Critical Bottleneck

> "The difference between a productive dual-agent workflow and an expensive token furnace comes down to what gets passed between agents." — Claude

### 🔵 CONFIRMED: Three Leading Handoff Patterns

| Pattern | Mechanism | Maturity | Best For |
|---------|-----------|----------|----------|
| **Structured Markdown + YAML frontmatter** | Files in `.handoffs/` or `.specify/` | Most practical | Claude→Codex handoff |
| **MCP-based bridging** | Direct agent-to-agent communication | Most elegant | Real-time review |
| **Git/PR-based** | Branch → PR → inline review | Most mature | CI/CD integration |

#### Pattern 1: Structured Markdown (Recommended)

- GitHub Spec Kit v0.1.4 formalizes: `spec.md → plan.md → tasks.md` in `.specify/` directory — Claude
- YAML frontmatter for machine-parseable fields (verdict, iteration count, files changed, test status) — Claude
- Markdown body for human-readable reasoning, findings, file references — Claude
- Claude Code users independently developed `.claude/handoff-[date].md` — Claude

#### Pattern 2: MCP Bridges

- **Codex Bridge** — consultation and batch processing between Claude and Codex — Claude
- **PAL MCP Server** — Claude Code spawns Codex subagents — Claude, Gemini
- **claude-codex-bridge** — MCP server for direct communication — Gemini
- **Context Pack** — lightweight "anchors" instead of copying code — Claude
- Anti-recursion guards via `BRIDGE_DEPTH` environment variable — Gemini

#### Pattern 3: Git/PR-based

- Graphite Agent: ~90-second feedback loop, 40× faster than human review — Claude
- GitHub Agentic Workflows (technical preview, Feb 2026): agent-neutral CI/CD — Claude
- Qodo/PR-Agent, CodeRabbit for automated PR review — Claude

### 🟢 CONSENSUS: Optimal Handoff Size and Content

| Dimension | Recommendation | Sources |
|-----------|---------------|---------|
| **Target size** | 2,000–5,000 tokens | Claude |
| **Include reasoning** | YES — without it, reviewer becomes a smart linter | Claude, ChatGPT |
| **Include diffs** | Reference diffs, don't inline full files | Claude, Gemini |
| **Include acceptance criteria** | YES — so reviewer can verify tests against intent | Claude |
| **Format** | Machine-parseable YAML frontmatter + human-readable markdown | Claude, ChatGPT |
| **JSON verdict format** | `{verdict, issues, suggestions}` — strict, no extra text | ChatGPT |

### 🟢 CONSENSUS: Include Implementation Reasoning

> "Without reasoning, the reviewer is reduced to a smart linter over diffs — the 2023-2024 era approach that failed to catch architectural issues." — Claude

Multiple sources confirm: Qodo 2.0 includes "evidence and reasoning that explains how the agent reached its conclusion" in every review finding.

---

## 5. Automation & Tooling

### 🟢 CONSENSUS: VS Code v1.109 Is the Canonical Platform

- Runs Claude, Codex, and Copilot simultaneously — All 3
- Agent Sessions UI shows all agents in one place — ChatGPT
- Both local and cloud execution options — Claude
- **`anthropic.claude-code`** extension: subagents, hooks, inline diffs — Claude
- **`openai.chatgpt`** extension: three modes (chat-only → full autonomous) — Claude

### 🟢 CONSENSUS: CI/CD Integration via Official GitHub Actions

| Action | Purpose | Source |
|--------|---------|--------|
| `openai/codex-action@v1` | Code reviews, PR comments, configurable safety | Claude |
| `anthropics/claude-code-action` | PR review, test generation, refactoring proposals | Claude |
| GitHub Agentic Workflows | Agent-neutral CI/CD in markdown (6 pattern categories) | Claude |
| GitHub Agent HQ | Assign issues to Claude, Codex, Copilot simultaneously | Claude |

### 🔵 CONFIRMED: MCP Bridge Tools

| Tool | What It Does | Source |
|------|-------------|--------|
| `pal-mcp-server` | Claude Code spawns Codex/Gemini/OpenRouter subagents | Claude, Gemini |
| `claude-codex-bridge` | Direct MCP communication between agents | Gemini |
| Codex Bridge | Consultation and batch processing | Claude |
| Context Pack | Lightweight anchors, orchestrator renders to markdown pack | Claude |
| `codex mcp-server` | Run Codex CLI as MCP server for Claude Desktop | Claude |

### 🔵 CONFIRMED: Orchestration Frameworks

| Framework | Approach | Source |
|-----------|----------|--------|
| **sudocode** | Context-as-Code, JSONL+SQLite, Kanban visualization | Gemini |
| **ralphex** | Persistent agent loop, `--review` flag for Codex read-only | Gemini |
| **Harbor** | Converts Claude outputs to Codex task format | Gemini |
| **CrewAI / AutoGen / LangGraph** | General multi-agent orchestration | ChatGPT |
| **OpenAI Agents SDK** | Chain PM → Designer → Developer → Tester with traces | Claude |
| **OpenHands** (64K+ GitHub stars) | `AgentDelegateAction`, Docker sandbox, 72% SWE-Bench | Claude |

### 🔵 CONFIRMED: Claude Code Hooks for TDD Enforcement

- **15 hook events, 3 handler types** (command, prompt, agent hooks) — Claude
- `PreToolUse` hooks block file edits if no corresponding failing test exists — Claude, Gemini
- `PostToolUse` hooks trigger Codex validation sweep on file write — Gemini
- **TDD Guard** (open-source): blocks modifications without failing tests (Jest, Vitest, pytest) — Claude

### Shell Script Chaining (Practical Automation)

```bash
# Chain Claude non-interactive → Codex headless review
claude -p "implement feature X using TDD" --output-format json
codex exec "review the changes on this branch" --json --output-last-message
```
— Claude source

---

## 6. Configuration Best Practices

### 🟢 CONSENSUS: File Hierarchy

| File | Purpose | Size Limit | Scope |
|------|---------|-----------|-------|
| **AGENTS.md** | Universal repo standards (cross-platform) | <150 lines (GitHub analysis of 2,500+ files) | All agents |
| **CLAUDE.md** | Claude-specific instructions | <50 lines | Opus only |
| **.codex/config.toml** | Codex operational parameters | Minimal | Codex only |
| **HANDOFF.md** | Ephemeral state transfer | 2,000–5,000 tokens | Per-handoff |
| **learnings.md** | Persistent institutional memory | Append-only | Cross-session |

### 🟢 CONSENSUS: AGENTS.md as Linux Foundation Standard

- AGENTS.md is now the cross-tool standard, supported by 20+ tools including Codex, Cursor, Jules, Copilot, Gemini CLI — Claude
- GitHub analysis: most effective ones stay under 150 lines, put build commands early, use code examples over explanations — Claude
- 60,000+ repositories use it — Claude

### ⚪ UNIQUE: ETH Zurich Study (Critical Finding)

> Monolithic auto-generated AGENTS.md files **decrease model performance by ~3%** while **inflating inference costs by 159%**. Irrelevant rules dilute the attention mechanism and lead to hallucinations. — Gemini

**Mitigation**: Tiered, path-specific rule injection:
- Directory-scoped `AGENTS.override.md` files (e.g., `services/payments/AGENTS.override.md`)
- Reduces context size by 60–80%
- `@docs/architecture.md` syntax for lazy-loading shared knowledge — Gemini

### 🟢 CONSENSUS: Configuring Codex as Review-Only

| Method | How | Source |
|--------|-----|--------|
| Prompt constraint | "You are a senior engineer reviewing — do NOT write new code" | ChatGPT |
| `.codex/config.toml` | `approval_mode = "suggest"` or `ask-for-approval` | Gemini |
| `ralphex --review` | Read-only analysis, structured JSON/Markdown output | Gemini |
| `/review-dirty` script | `codex exec "Review dirty repo changes..."` | ChatGPT |
| CLAUDE.md protocol | "Do not commit without Codex approval" | ChatGPT |

---

## 7. TDD Integration

### 🟢 CONSENSUS: TDD Is the #1 Guardrail

> "The simplest guardrail is to make sure your AI uses TDD — write a unit test first, then code to pass it." — ChatGPT

All three reports agree that TDD is the most effective way to constrain AI agents and prevent drift.

### 🟢 CONSENSUS: TDD Theater Is a Major Risk

> "When you ask an AI to generate tests, it almost always starts by analyzing the code. Your tests now validate the implementation, not the intention." — Claude

**The failure mode**: AI writes code first, then retrofits trivial tests that pass but don't verify feature intent.

**Mitigations (all sources agree)**:
1. Write tests BEFORE implementation (true TDD, not retrofit)
2. Encode acceptance criteria in natural language in the handoff artifact
3. Have the review agent verify tests against intent, not just that tests pass
4. Use Claude Code hooks / TDD Guard to block edits without failing tests
5. Never let the implementing agent also write the acceptance criteria

### 🔵 CONFIRMED: Tests as Handoff Mechanism

Tests serve as the bridge between agents — they're unambiguous, executable, and self-documenting. When Opus writes tests from FIC acceptance criteria, those tests become the spec that Codex validates against.

### ⚪ UNIQUE: Agent-Specific Test Failure Modes

- **Opus**: Generates tests that pass trivially by heavily mocking internal logic rather than verifying execution paths — Gemini
- **Codex**: Over-engineers — one case of 80,000 lines of pedantic test suites for a minor feature migration that took 20 hours — Gemini

---

## 8. Developer Experience & Productivity

### Productivity Claims

| Claim | Metric | Source | Confidence |
|-------|--------|--------|------------|
| 44 PRs in 5 days | PR throughput | ChatGPT | 🔵 CONFIRMED |
| 93,000 lines in 5 days | Lines shipped | Gemini | ⚪ UNIQUE |
| 80–90% functional success | "Accept all" vibe coding for CRUD/UI | Gemini | ⚪ UNIQUE |
| Bottleneck is human review speed | Not agent speed | Claude | ⚪ UNIQUE |

### 🟢 CONSENSUS: Sobering Counterpoints

| Finding | Detail | Source |
|---------|--------|--------|
| **METR RCT** | Devs believe 20% faster, actually **19% slower** (246 tasks, mature repos, older models) | Claude |
| **DORA report** | Every 25% AI adoption increase → 1.5% delivery speed dip, 7.2% stability drop | Claude |
| **Stack Overflow 2025** | Trust in AI accuracy dropped from 43% to **33%** YoY; 45% say debugging AI code takes longer than expected | Claude |
| **Columbia DAPLab** | 9 critical failure patterns in 15+ vibe-coded apps; agents prioritize runnable code over correctness | Claude |
| **Anthropic themselves** | "Even frontier Opus 4.5 in a loop falls short of production-quality if only given a high-level prompt" | Claude |

### 🔵 CONFIRMED: Subjective Experience

> "It's closer to being a tech lead than a pair programmer. You sit in the middle, Claude writes, Codex reviews, and you make the judgment calls." — Claude (Sakiharu report)

> "The efficiency jumped immediately. Not because the agents got smarter, but because the review discipline became automatic instead of depending on my willpower at 2am." — Claude (Sakiharu report)

### ⚪ UNIQUE: Complementary Context Windows

> "When one agent's context is compressed and loses details, the other agent still remembers. They don't share the same context window, so they don't lose the same information at the same time." — Claude

---

## 9. Failure Modes & Anti-Patterns (Ranked by Severity)

### Tier 1: Critical — Can Silently Ship Bad Code

| # | Failure Mode | Description | Mitigation | Sources |
|---|-------------|-------------|------------|---------|
| 1 | **Rubber-stamp reviewing** | Codex approves everything; "green checkmarks that mean nothing" | Confidence gates, structured verdicts with evidence, AV checklist | 🟢 All 3 |
| 2 | **TDD theater** | Tests validate implementation, not intention; coverage rises but bugs survive | True TDD (tests before code), acceptance criteria in handoff | 🟢 All 3 |
| 3 | **Mutual agreement on bad design** | "Two AIs can happily agree on a bad design" — human domain judgment required | Human orchestrator is NOT optional | 🟢 All 3 |

### Tier 2: Serious — Causes Rework or Degradation

| # | Failure Mode | Description | Mitigation | Sources |
|---|-------------|-------------|------------|---------|
| 4 | **Context rot** | Performance degrades beyond 100K tokens; "lost in the middle" phenomenon | Reset context between iterations, keep handoffs lean | 🔵 Claude, Gemini |
| 5 | **Agent ping-pong** | Fix→review→new issue→fix→new issue; GPT-4o showed 37.6% MORE vulnerabilities after 5 iterations | Hard iteration limits (3–5 rounds), human escalation | 🔵 Claude, ChatGPT |
| 6 | **Agent drift** | Infinite refactoring loops when agents disagree on approach | Human arbiter, explicit acceptance/override in instructions | 🔵 ChatGPT, Gemini |
| 7 | **"Opus Slop"** | Skipped error handling, type loopholes, bypassed edge cases when prioritizing speed | Codex review catches these; explicit error-handling requirements | ⚪ Gemini |

### Tier 3: Operational — Increases Cost/Friction

| # | Failure Mode | Description | Mitigation | Sources |
|---|-------------|-------------|------------|---------|
| 8 | **Configuration fatigue** | Too many .md files; agents partially ignore instructions | Tiered config (AGENTS.md <150 lines), path-specific overrides | 🟢 All 3 |
| 9 | **Cost spirals** | 7–15× token multiplier from agentic patterns; $200–5,600/month | Portfolio approach: cheap models for routine, frontier for complex | 🔵 Claude, Gemini |
| 10 | **Session boundary loss** | Agent session closes, context lost unless explicitly serialized | Handoff artifacts, pomera_notes, git commits as checkpoints | 🔵 ChatGPT, Gemini |
| 11 | **Handoff bloat** | Dumping everything (40K tokens of process to find 3K tokens of insight) | Target 2,000–5,000 tokens; diffs + reasoning, not full files | 🔵 Claude, Gemini |

### ⚪ UNIQUE: Antigravity IDE Rate Limiting

Professional developers report 7–10 day lockouts after only 2–3 complex Opus 4.6 queries, despite a documented 5-hour refresh window. Evidence of opaque model routing to older pools. Significant cohort migrating to raw Claude Code CLI or Cursor. — Gemini

---

## 10. Cost Analysis

### Token Pricing (February 2026)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Source |
|-------|----------------------|----------------------|--------|
| Claude Opus 4.6 | $5 | $25 | Claude |
| GPT-5.3-Codex | ~$6 | ~$30 | Gemini |

### Real-World Spend

| Scenario | Monthly Cost | Source |
|----------|-------------|--------|
| Subscriptions (Claude Code + planning tools) | $100–150 | ChatGPT |
| Heavy dual-agent (API rates, subscriptions) | $200–400+ | Claude |
| Extreme case (201 Claude sessions, API rates) | $5,623 | Claude |
| Enterprise dual-agent team | ~$4,000 ($2K Claude + $1.5K OpenAI + $500 monitoring) | Claude |

### Token Multipliers

| Pattern | Multiplier | Source |
|---------|-----------|--------|
| Agent teams (Claude Code) | 7× vs standard | Claude |
| Multi-agent systems | 15× vs single-agent | Claude |
| Subagent pattern vs handoff-with-history | **67% fewer tokens** (9K vs 14K+) | Claude |
| Monolithic AGENTS.md cost inflation | +159% | Gemini (ETH Zurich) |

### 🔵 CONFIRMED: Cost Justified by Productivity

> "While the bill can skyrocket, the speed gains (44 PRs vs months of work) justify it." — ChatGPT
> "Not because the agents got smarter, but because the review discipline became automatic." — Claude

---

## 11. Actionable Recommendations

### Immediate Setup (Day 1)

1. **Create AGENTS.md** at project root — under 150 lines, build commands first, code examples over prose
2. **Create CLAUDE.md** — under 50 lines, imports AGENTS.md, adds TDD enforcement
3. **Configure Codex as review-only** — `.codex/config.toml` with suggest mode, or `ralphex --review`
4. **Define handoff template** — YAML frontmatter + markdown body, target 2,000–5,000 tokens
5. **Install TDD Guard** or configure Claude Code hooks to block edits without failing tests

### Workflow Rules

6. **One task per handoff** — 87.2% success on single-function vs 19.36% on multi-file tasks
7. **Max 3 review cycles** then escalate to human
8. **Include reasoning in handoffs** — not just diffs
9. **Encode acceptance criteria in natural language** — separate from test code
10. **Reset context between iterations** — don't let sessions accumulate beyond 100K tokens

### Quality Gates

11. **Tests before implementation** — true TDD, never retrofit
12. **Human reviews Codex's review** — never merge on AI approval alone
13. **Scan for banned patterns** — `TODO`, `FIXME`, `NotImplementedError`
14. **Verify tests encode intent, not implementation** — adversarial check

### Cost Control

15. **Use subagent pattern** (67% fewer tokens) over growing conversation history
16. **Tiered config** — path-specific AGENTS.override.md instead of monolithic files
17. **Cheap models for routine** — frontier models only for complex work

---

## 12. Tool Registry

### MCP Bridges & Agent Tools

| Tool | URL/Reference | Purpose |
|------|--------------|---------|
| PAL MCP Server | [github.com/BeehiveInnovations/pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server) | Claude spawns Codex/Gemini subagents |
| claude-codex-bridge | [lobehub.com/mcp/user-claude-codex-bridge](https://lobehub.com/mcp/user-claude-codex-bridge) | Direct MCP communication |
| Codex High-Reasoning Bridge | [mcpmarket.com/tools/skills/codex-high-reasoning-bridge](https://mcpmarket.com/tools/skills/codex-high-reasoning-bridge) | High-reasoning integration |
| Context Pack | (Claude research) | Lightweight anchors for context |
| Codex MCP Server | `codex mcp-server` CLI command | Run Codex as MCP server |

### Orchestration Frameworks

| Tool | URL/Reference | Purpose |
|------|--------------|---------|
| sudocode | [github.com/sudocode-ai/sudocode](https://github.com/sudocode-ai/sudocode) | Context-as-Code, Kanban visualization |
| ralphex | [github.com/umputun/ralphex](https://github.com/umputun/ralphex) | Persistent agent loop, `--review` mode |
| OpenHands | (formerly OpenDevin, 64K+ GitHub stars) | Multi-agent + Docker sandbox |
| Harbor | [github.com/laude-institute/harbor](https://github.com/laude-institute/harbor) | Claude→Codex format conversion |
| Ruflo | (Claude research) | CLAUDE.md + AGENTS.md dual-mode init |
| TDD Guard | (Claude research) | Blocks edits without failing tests |

### CI/CD Actions

| Action | Purpose |
|--------|---------|
| `openai/codex-action@v1` | Codex CLI in CI, PR review comments |
| `anthropics/claude-code-action` | Claude Code in CI, PR review/test generation |
| GitHub Agentic Workflows | Agent-neutral CI/CD (technical preview) |
| GitHub Agent HQ | Assign issues to multiple agents simultaneously |

### VS Code Extensions

| Extension | Purpose |
|-----------|---------|
| `anthropic.claude-code` | Claude Code with subagents, hooks, inline diffs |
| `openai.chatgpt` | Codex with three autonomy modes |
| VS Code Agent Sessions (v1.109+) | Unified multi-agent management |

### PR Review Tools

| Tool | Speed | Model |
|------|-------|-------|
| Graphite Agent | ~90 seconds (40× faster than human) | Multi-provider |
| Qodo 2.0 / PR-Agent | Multi-agent alignment phase | Custom |
| CodeRabbit | Automated inline review | Multi-provider |
| Traycer | Plan→implement→review orchestration | Claude/Codex |

### Planning Tools

| Tool | Purpose |
|------|---------|
| GitHub Spec Kit (v0.1.4) | `spec.md → plan.md → tasks.md` in `.specify/` |
| Traycer | File-level planning for scoped agent calls |

### References

| Source | URL |
|--------|-----|
| ShakaCode Guide | (Claude builds, Codex validates pattern) |
| Builder.io CEO comparison | (Steve Sewell's production comparison) |
| Sakiharu 2-year report | (Detailed first-person dual-agent workflow) |
| ETH Zurich AGENTS.md study | [digitalapplied.com/blog/agents-md-eth-zurich-study](https://www.digitalapplied.com/blog/agents-md-eth-zurich-study-inference-costs-guide) |
| METR RCT | (246 tasks, 16 developers, mature repos) |
| DORA report | (AI adoption impact on delivery speed) |
| Columbia DAPLab | (9 failure patterns in 15+ vibe-coded apps) |
| Addy Osmani workflow | [addyosmani.com/blog/ai-coding-workflow](https://addyosmani.com/blog/ai-coding-workflow/) |
| The Tale of 2 Models (Cordero Core) | [medium.com/@cdcore](https://medium.com/@cdcore/the-tale-of-2-models-opus-4-6-vs-gpt-5-3-codex-129fcb35630f) |
| Lenny's Newsletter (93K lines) | [lennysnewsletter.com](https://www.lennysnewsletter.com/p/claude-opus-46-vs-gpt-53-codex-how) |

---

## Key Contradictions Between Sources

| Topic | ChatGPT | Claude | Gemini |
|-------|---------|--------|--------|
| **Productivity** | 44 PRs in 5 days (positive) | METR: actually 19% slower (cautious) | 93K lines in 5 days (very positive) |
| **Cost justification** | "Justified by speed" | $5,623/month possible, needs portfolio approach | Doubles baseline, ETH Zurich shows 159% waste |
| **Automation maturity** | Scripts + MCP bridges work today | "No universal standard" for handoffs | "Rapidly matured" with sudocode, ralphex |
| **GitHub Actions** | Mentioned briefly | Detailed both actions + Agentic Workflows | Not emphasized |

The Claude report is notably more cautious and evidence-based (citing METR RCT, DORA, Stack Overflow surveys). The Gemini report is most detailed on tooling and configuration. The ChatGPT report is most practical with specific developer quotes and workflow scripts.
