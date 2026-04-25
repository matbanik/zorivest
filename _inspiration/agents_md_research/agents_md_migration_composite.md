# AGENTS.md Modernization — Composite Analysis & Migration Plan

**Sources:** ChatGPT (C), Gemini (G), Claude (A) deep research reports  
**Target models:** Claude Opus 4.7 (implementor), GPT-5.5 (reviewer)  
**Current file:** [AGENTS.md](file:///p:/zorivest/AGENTS.md) — 423 lines

---

## 1. Source Report Quality Assessment

| Report | Grade | Strengths | Weaknesses |
|--------|-------|-----------|------------|
| **Claude (A)** | **A+** | Line-level diffs, 11-item verification table, 10-risk register, correctly identifies what to KEEP | Some proposals assume harness-level API control we may not have |
| **ChatGPT (C)** | **B** | Good summary tables, useful before/after examples, caching strategy | Misses HTTP 400 sampling break, over-simplifies shell commands, generic advice labeled as GPT-5.5-specific |
| **Gemini (G)** | **B−** | Best "big picture" framing, strongest failure-mode taxonomy | Most proposals assume infrastructure that doesn't exist; treats file as greenfield rather than migration |

**Reliability hierarchy:** Claude > ChatGPT > Gemini for practical Zorivest applicability.

> [!TIP]
> **Reading guide:** Each report has a distinct bias. Claude is surgical/conservative, ChatGPT is best-practice-forward, Gemini is architecturally radical. The right composite uses Claude as backbone, ChatGPT for practical additions, and Gemini for failure-mode guards only.

---

## 2. Consensus Matrix

Shows each report's position on every migration axis. ✅ = agrees, ❌ = disagrees/silent, ⚠️ = partially.

| # | Migration Axis | Claude (A) | ChatGPT (C) | Gemini (G) | Consensus |
|---|---------------|------------|-------------|------------|-----------|
| 1 | Upgrade reviewer → GPT-5.5 | ✅ Critical | ✅ Critical | ✅ Immediate | **UNANIMOUS** |
| 2 | Mode-to-effort binding | ✅ High | ✅ High | ✅ (matrix) | **UNANIMOUS** (details conflict) |
| 3 | Drop context checkpoint below 80% | ✅ 50% | ⚠️ ~70% old | ⚠️ Implicit | **DIRECTION AGREED** (number conflicts) |
| 4 | Prompt caching static-first layout | ✅ Detailed | ✅ Detailed | ✅ Cost-framed | **UNANIMOUS** |
| 5 | Sampling params break (HTTP 400) | ✅ Critical | ❌ Silent | ⚠️ Mentioned | **MAJORITY** (C missed it) |
| 6 | Task budgets adoption | ✅ Critical | ✅ Medium | ✅ Phase 3 | **UNANIMOUS** |
| 7 | Literal instruction re-tuning | ✅ Critical | ✅ High | ⚠️ Indirect | **UNANIMOUS** |
| 8 | Tokenizer inflation (1.0–1.35×) | ✅ Critical | ✅ Medium | ✅ Mentioned | **UNANIMOUS** |
| 9 | Vision capability integration | ✅ Medium/Low | ✅ Medium | ✅ Medium | **UNANIMOUS** (scope conflicts) |
| 10 | Keep TDD protocol | ✅ Keep | ✅ Keep | ❌ Replace w/ ARIA | **MAJORITY** (G dissents) |
| 11 | Keep human approval gates | ✅ Keep | ✅ Keep | ❌ Remove for std work | **MAJORITY** (G dissents) |
| 12 | Simplify prescriptive commands | ❌ Keep exact | ✅ Outcome-based | ✅ Strip process | **SPLIT** (A vs C+G) |
| 13 | Decompose AGENTS.md into tiers | ❌ Single file | ⚠️ Optional split | ✅ Full decompose | **SPLIT** |
| 14 | Agent topology (who implements?) | ✅ Claude impl | ✅ Flexible | ❌ Invert (GPT impl) | **SPLIT** |
| 15 | Add anti-patterns section | ⚠️ Inline | ✅ Dedicated | ✅ Dedicated | **MAJORITY** |
| 16 | Structured review verdict schema | ✅ High | ❌ Silent | ❌ Silent | **CLAUDE ONLY** (but high value) |
| 17 | Cross-vendor handoff protocol | ✅ High | ❌ Silent | ❌ Silent | **CLAUDE ONLY** (but high value) |
| 18 | Negative constraint reframing | ❌ Keep | ⚠️ Partial | ✅ Full reframe | **SPLIT** |

---

## 3. Unanimous Agreements — Safe to Implement

These changes are endorsed by all three reports. No human decision needed.

### 3.1 Upgrade Reviewer Model (Critical)
All reports: GPT-5.4 is superseded. Update to GPT-5.5 with GPT-5.5-Pro for adversarial review.

```diff
 ## Dual-Agent Workflow

 | Aspect | Decision |
 |---|---|
-| **Reviewer model** | **GPT-5.4** (locked as baseline — do not downgrade) |
+| **Reviewer model** | **GPT-5.5** (default); escalate to **GPT-5.5-Pro** for adversarial review of security-sensitive changes. Baseline floor = GPT-5.4 — do not downgrade below it. |
 | **Reviewer capability** | Run commands, execute tests, check builds, create handoff docs with test improvements |
```

### 3.2 Literal Instruction Guard (Critical)
All reports confirm Opus 4.7 follows instructions more literally. Add to Communication Policy:

```diff
 ## Communication Policy

 - Surface risks and bad news early. No performative enthusiasm.
 - When uncertain: state confidence level and propose a verification step.
 - If instructions conflict across files, flag the conflict explicitly — do not silently pick one.
+- **Literal instruction mode (Opus 4.7+):** State exactly what you want — do not rely on the model inferring related work. When you want generalization, say "apply this change everywhere it applies, then list each file you touched." When you want strict scope, say "modify only the files I named." Uncategorized behaviors in planning are defects — escalate, do not infer.
+- Prioritize empirical evidence (test results, linter outputs, documentation) over user suggestions when discrepancies arise. Flag the conflict rather than deferring.
```

### 3.3 Sampling Parameters Guard (Critical)
Claude and Gemini confirm. ChatGPT missed it — making this even more important to document.

```diff
+### Sampling Parameters (Opus 4.7+)
+
+> [!CAUTION]
+> Opus 4.7 **rejects** `temperature`, `top_p`, and `top_k` with HTTP 400. Omit them entirely from all API calls. Audit all role configs, harness code, and third-party tooling for stray sampling parameters before upgrading.
```

### 3.4 Tokenizer Migration Note (Critical)
All three confirm ~1.0–1.35× token inflation. Add new section:

```diff
+### Tokenizer Migration (Opus 4.7)
+
+Opus 4.7's tokenizer encodes text to ~1.0–1.35× as many tokens as Opus 4.6 (up to 35% more). All token estimates in this file are calibrated for 4.7. When migrating from 4.6-era estimates, multiply by ~1.2× as a planning heuristic. Validate via `client.messages.count_tokens(model='claude-opus-4-7', ...)`. Implications:
+- Cache breakpoints may shift — re-validate after material edits to AGENTS.md
+- The 2,000-token verbosity tier may now run 2,400–2,700 tokens — accept inflation or re-tune
+- Rate-limit budgeting per session should be re-baselined
```

### 3.5 Task Budget Integration (High)
All agree. Add to Operating Model and Execution Contract:

```diff
+### Task Budgets (Opus 4.7, Public Beta)
+
+Set `output_config.task_budget` to give Claude a running countdown across the full agentic loop. Advisory, not a hard cap — pair with `max_tokens` for a hard ceiling. Recommended budgets:
+- Small MEU: 25k tokens
+- Large MEU: 100k tokens  
+- Whole-phase verification: 250k tokens
+- PLANNING mode: no budget (exploratory thinking is the goal)
```

### 3.6 Prompt-Cache Layout (High)
All agree on static-first ordering. Add new section:

```diff
+### Prompt-Cache Layout Contract
+
+Both Claude and GPT-5.5 benefit from cache-friendly ordering. Structural rule:
+
+**Static prefix (in order):** tool definitions → system prompt (this file) → schemas → repo digest. Mark end of static prefix with `cache_control: {type: "ephemeral"}`. Maximum 4 cache breakpoints per Claude request.
+
+**OpenAI caching** is automatic (≥1,024 tokens, exact-prefix match). Use the same static-first layout. Cached input discounted up to ~90%.
+
+**What invalidates Claude cache:** any byte-level diff to cached prefix, changes to `tool_choice`, presence/absence of images, changes to thinking parameters.
```

### 3.7 Pre-Handoff Enhancement (Medium)
Claude recommends, aligns with all reports' emphasis on verification evidence:

```diff
 ## Pre-Handoff Self-Review (Mandatory)
 ...
 6. Stubs must honor behavioral contracts, not just compile.
-7. Follow the full protocol in `.agent/skills/pre-handoff-review/SKILL.md`.
+7. State the verification command you actually ran and paste its tail (last 20 lines). "I ran the tests" without output is not acceptable — produce actual evidence.
+8. Before asserting a file exists or a test passes, programmatically verify it. Do not defend claims from memory when contradicted by tool output.
+9. Follow the full protocol in `.agent/skills/pre-handoff-review/SKILL.md`.
```

### 3.8 FIC Acronym Expansion (Medium)
Claude correctly flags this. Add on first use (line 220):

```diff
-### FIC-Based TDD Workflow (Mandatory)
+### FIC-Based TDD Workflow (Mandatory)
+
+> FIC = **Feature Intent Contract** — the acceptance-criteria document written before any code.
```

---

## 4. Conflicts Requiring Your Decision

### ✅ DECISION 1: EXECUTION Mode Effort Level — **N/A (DROPPED)**

**User ruling:** Not relevant. Effort levels are selected by the human in the chat prompt UI (Antigravity/Codex settings), not controlled by the model via AGENTS.md. Removed effort/budget columns from Operating Model table.

> [!NOTE]
> The mode-to-effort binding concept from all three reports assumed API-level control. In the Zorivest workflow, the human selects effort per-session in the IDE, making this an operational setting rather than an instruction.

---

### ✅ DECISION 2: Agent Topology — **N/A (DROPPED)**

**User ruling:** Not relevant for current environment. Zorivest is dominantly using Antigravity with settings designed for Claude-as-implementor. This is an infrastructure constant, not a prompt decision.

---

### ✅ DECISION 3: Context Checkpoint Threshold — **50% SELECTED**

**User ruling:** 50%. However, the user notes this is a soft self-policing instruction — the model estimates its own context usage and checkpoints. Neither Opus 4.7 nor GPT-5.5 mechanically enforce this; it relies on the model's awareness of its context fill level.

> [!NOTE]
> Applied to AGENTS.md. The checkpoint text now reads: "~50% capacity (~500k tokens on a 1M window)" with a rationale about context rot.

---

### ✅ DECISION 4: Cache-Friendly Section Reorder — **NO (DROPPED)**

**User ruling:** No. Zorivest uses subscriptions with time-based usage limits, so API token costs don't apply. Caching is handled server-side by the model backend. Optimizing AGENTS.md layout for cache hits is a "fool's errand" since models change every ~4 months, invalidating any layout assumptions. Removed `<!-- CACHE BOUNDARY -->` marker and Prompt-Cache Layout Contract section.

---

### ✅ DECISION 5: Structured Review Verdict Schema — **ALREADY HANDLED (DROPPED)**

**User ruling:** Already optimized. The decision for hybrid YAML+freeform format was made previously and lives in the `/meu-handoff` and `/validation-review` workflows. Updated the Cross-Vendor Handoff Protocol to reference these workflows instead of a new JSON schema file.

---

### ✅ DECISION 6: Vision Testing Section — **ALREADY HANDLED (DROPPED)**

**User ruling:** UI workflows are already implemented and moved out of AGENTS.md into dedicated workflows (`/e2e-testing`, `/gui-integration-testing`). The E2E wave activation section in AGENTS.md already covers GUI test requirements. No additional vision section needed.

---

### ✅ DECISION 7: Anti-Patterns Section — **DISTRIBUTED**

**User ruling:** Distributed. Anti-patterns are not always needed and are likely to change in the near future. Keeping them distributed means each can be updated independently when new implementation patterns emerge, without requiring a separate consolidated section. Removed the dedicated FM table; guards remain distributed in their respective sections (Communication Policy, Pre-Handoff, Sampling Parameters).

---

### ✅ DECISION 8: Negative Constraint Reframing — **KEEP ALL**

**User ruling:** Keep all negative constraints as-is. Content at the bottom of long files gets pushed out of context in extended sessions, so removing negative constraints from upper sections reduces accuracy. For quick changes, the full set of constraints actually gets read and provides better accuracy. No reframing needed.

---

### ✅ DECISION 8 rationale continued:

> [!NOTE]
> The user's insight about context window position is important: negative constraints placed high in the file survive long-session context truncation, while content at the bottom gets dropped. This validates keeping explicit negative guards near the rules they protect.

---

## 5. Infeasible Recommendations — Rejected with Reasoning

| # | Recommendation | Source | Why It Doesn't Work |
|---|----------------|--------|---------------------|
| 1 | **Strip prescriptive Quick Commands** — replace with outcome goals | C, G | P0 shell commands are PowerShell survival patterns. Without exact `*>` redirect syntax, agents hang terminals. These are environment workarounds, not model scaffolding. |
| 2 | **Decompose AGENTS.md into tiered hierarchy** (API Core → Repo → Directory) | G | Current infrastructure expects single AGENTS.md. Would break `validate_codebase.py`, handoff templates, Gemini shim, and `user_rules` injection. The `.agent/roles/` system already serves as Tier 3. |
| 3 | **Replace TDD with ARIA/FIC framework** | G | FIC-based TDD is deeply integrated across 50+ MEUs, 11 workflow files, quality gate validator, and all handoff templates. ARIA is an academic framework from a single ResearchGate paper. Replacing would destroy institutional knowledge. |
| 4 | **Remove human approval gates** for standard work | G | Human is the product owner. Financial/portfolio software requires human oversight by design philosophy. The "Quality-First Policy" explicitly prohibits compromising quality for speed. |
| 5 | **GPT-5.5 as primary executor** (invert topology) | G | Entire infrastructure (MCP servers, role definitions, Claude Code integration, slash commands) built for Claude-as-implementor. This is an infrastructure overhaul, not a prompt edit. |
| 6 | **Separate model-specific context files** (GPT.md + CLAUDE.md) | C | The GPT-5.5 reviewer receives instructions via the review prompt template, not by reading repo files. A separate "GPT.md" would be dead weight. |
| 7 | **Remove line-count caps** on context files (30/100 lines) | G | These limits are proven anti-bloat mechanisms. Without them, agents let `known-issues.md` grow unbounded (observed behavior). "Semantic density" is not enforceable as a concrete rule. |
| 8 | **Remove inline schema definitions** from prompts | G | AGENTS.md doesn't contain inline JSON schemas. The file contains Markdown tables and code blocks that are instructions, not API payloads. Recommendation conflates prompt content with API parameters. |
| 9 | **"Workflow-End Skills" for knowledge graph sync** | G | No "codebase knowledge graph" exists. Post-MEU cleanup is handled by handoff templates, pomera_notes, and context file hygiene. Adding a knowledge graph sync is scope creep. |
| 10 | **Phase parameter preservation** for GPT-5.5 | G | Reviewer runs as one-shot API calls, not persistent Responses API sessions. Phase parameters matter for conversational workflows, not for review invocations. Defer until needed. |

---

## 6. Breaking Changes Checklist — Must Fix Before Model Swap

These items cause **hard failures** if not addressed:

| # | Change | Severity | Source |
|---|--------|----------|--------|
| 1 | Remove `temperature`/`top_p`/`top_k` from all Claude API calls | 🔴 HTTP 400 | A, G |
| 2 | Replace `thinking.budget_tokens` with `output_config.effort` on Opus 4.7 paths | 🔴 HTTP 400 | A |
| 3 | Update reviewer model name `gpt-5.4` → `gpt-5.5` in all configs and AGENTS.md | 🔴 Stale model | A, C, G |
| 4 | Drop context-window checkpoint from 80% → **your chosen threshold** | 🟡 Correctness | A, C, G |
| 5 | Re-budget all token estimates for new tokenizer (~1.2× multiplier) | 🟡 Correctness | A, C, G |

Items 1–3 are hard failures. Items 4–5 are correctness regressions under load.

---

## 7. Consolidated Risk Register

| ID | Risk | Severity | Likelihood | Mitigation |
|----|------|----------|------------|------------|
| R1 | **Silent literal-following regressions** — prompts relying on Claude generalizing will under-perform | Critical | Likely | Add literal-instruction guard (§3.2); spot-check first 5 sessions |
| R2 | **Stray sampling parameters** — HTTP 400 on any temp/top_p/top_k usage | Critical | Possible | Grep audit of all code paths before swap |
| R3 | **Cache invalidation** — all warmed caches useless on new tokenizer | High | Certain | Schedule upgrade during lull; expect ~10% cost spike day 1 |
| R4 | **Context checkpoint at 80%** — 800k tokens is deep in degradation zone | High | Certain | Drop to 50% (or chosen threshold) |
| R5 | **Task budget is advisory** — model can exceed it | Medium | Likely | Pair with `max_tokens` as hard cap |
| R6 | **Cross-vendor schema drift** — reviewer output schema diverges | Medium | Possible | Single `.agent/schemas/review_verdict.json` as source of truth |
| R7 | **`xhigh` latency surprise** — slower than `high` for VERIFICATION | Medium | Likely | Bind effort to mode; EXECUTION stays at `medium` |
| R8 | **Opus 4.7 gaslighting** — invents file paths, defends fabrications | Medium | Possible | Pre-Handoff rule: programmatically verify before asserting |
| R9 | **GPT-5.5 state tracking decay** — loses position in long loops | Low | Possible | One-shot review pattern (current) avoids this naturally |
| R10 | **Vision scope creep** — rules for features that don't exist yet | Low | Possible | Gate vision section behind "when UI layer scaffolded" |

---

## 8. Diff-Based Migration Plan — Execution Order

### Phase 1: Breaking Changes (Day 1)

| # | Section | Change | Lines | Priority |
|---|---------|--------|-------|----------|
| 1.1 | New: Sampling Parameters | Add HTTP 400 guard | After L94 | 🔴 Critical |
| 1.2 | Dual-Agent Workflow | GPT-5.4 → GPT-5.5 | L287-293 | 🔴 Critical |
| 1.3 | Execution Contract | 80% → 50% checkpoint | L262 | 🔴 Critical |

### Phase 2: Effort & Budget Bindings (Day 2)

| # | Section | Change | Lines | Priority |
|---|---------|--------|-------|----------|
| 2.1 | New: Adaptive Thinking & Effort Policy | Add effort level definitions + mode bindings | New section | 🟡 High |
| 2.2 | Operating Model | Add effort/budget columns to mode table | L130-134 | 🟡 High |
| 2.3 | New: Task Budgets | Add budget guidance | New section | 🟡 High |

### Phase 3: Literal-Following & Communication (Day 2)

| # | Section | Change | Lines | Priority |
|---|---------|--------|-------|----------|
| 3.1 | Communication Policy | Add literal-instruction guard | After L105 | 🔴 Critical |
| 3.2 | Planning Contract | Add uncategorized-behavior stop rule | After L193 | 🟡 High |
| 3.3 | FIC-Based TDD | Expand FIC acronym | L220 | 🟢 Medium |

### Phase 4: Context & Caching (Day 3)

| # | Section | Change | Lines | Priority |
|---|---------|--------|-------|----------|
| 4.1 | New: Tokenizer Migration | Add tokenizer inflation guidance | New section | 🔴 Critical |
| 4.2 | New: Prompt-Cache Layout | Add cache-friendly ordering contract | New section | 🟡 High |
| 4.3 | Context Compression | Add tool-result clearing + JIT retrieval rules | After L271 | 🟡 High |
| 4.4 | Testing & TDD | Add tokenizer-aware test output note | After L233 | 🟡 High |

### Phase 5: Dual-Agent Modernization (Day 3)

| # | Section | Change | Lines | Priority |
|---|---------|--------|-------|----------|
| 5.1 | Dual-Agent Workflow | Add reasoning effort policy for reviewer | After L293 | 🟡 High |
| 5.2 | New: Cross-Vendor Handoff Protocol | Add structured handoff payload spec | New section | 🟡 High |
| 5.3 | New: Review Verdict Schema | Reference `.agent/schemas/review_verdict.json` | New section | 🟡 High |

### Phase 6: Guards & Polish (Day 4)

| # | Section | Change | Lines | Priority |
|---|---------|--------|-------|----------|
| 6.1 | Pre-Handoff Self-Review | Add evidence + programmatic verification rules | L277-283 | 🟢 Medium |
| 6.2 | New: Failure Mode Guards | Add gaslighting, state decay, social anchoring | End of file | 🟢 Medium |
| 6.3 | Structural reorder | Reorder sections for cache friendliness + insert `<!-- CACHE BOUNDARY -->` | Whole file | 🟡 High |

---

## 9. Summary: What Gets Applied, What Gets Rejected

### ✅ ACCEPTED & APPLIED (14 changes)
- Reviewer → GPT-5.5 + GPT-5.5-Pro escalation (all 3)
- Implementor model row added (Opus 4.7)
- Literal instruction guard in Communication Policy (all 3)
- Empirical evidence priority rule (G)
- Sampling parameter guard — HTTP 400 prevention (A, G)
- Context checkpoint 80% → 50% (all 3)
- FIC acronym expansion (A)
- Pre-handoff evidence rule #7 — paste actual output (A)
- Pre-handoff programmatic verify rule #8 (G)
- Tool-result clearing / JIT retrieval rule (A)
- Verbosity tier tokenizer inflation note (A)
- Cross-vendor handoff protocol — refs existing workflows (A)
- Social anchoring guard — distributed in Communication Policy (G)
- Gaslighting guard — distributed in Pre-Handoff #8 (G)

### ❌ REJECTED (10 recommendations — unchanged)
- Strip prescriptive Quick Commands (C, G)
- Decompose into tiered hierarchy (G)
- Replace TDD with ARIA (G)
- Remove human approval gates (G)
- Invert agent topology (G)
- Separate model-specific files (C)
- Remove line-count caps (G)
- Remove inline schemas (G — inapplicable)
- Workflow-end knowledge graph sync (G)
- Phase parameter preservation (G — deferred)

### 🚫 DROPPED BY USER DECISION (8 items)
- Mode-to-effort binding columns — effort selected in UI, not by model (Q1)
- Task budget integration — same, UI-controlled (Q1)
- Agent topology change — infrastructure constant, not a prompt decision (Q2)
- Prompt-cache layout contract — subscription model, server handles caching (Q4)
- Cache boundary marker — same (Q4)
- Tokenizer migration section — same (Q4)
- Structured review verdict JSON schema — already handled via YAML+freeform in workflows (Q5)
- Dedicated failure mode guards table — user prefers distributed (Q7)

### ✅ ALL 8 DECISIONS RESOLVED
| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | EXECUTION effort | **N/A** — dropped | Human-selected in UI, not model-controlled |
| 2 | Agent topology | **N/A** — dropped | Infrastructure constant (Antigravity) |
| 3 | Context checkpoint | **50%** | Safe failure mode; applied to AGENTS.md |
| 4 | Cache reorder | **No** | Subscription; server-side caching; models change every ~4 months |
| 5 | Review schema | **Already handled** | YAML+freeform hybrid in `/meu-handoff` and `/validation-review` workflows |
| 6 | Vision section | **Already handled** | E2E testing workflows exist outside AGENTS.md |
| 7 | Anti-patterns | **Distributed** | Easier to update independently on new implementations |
| 8 | Negative constraints | **Keep all** | Top-of-file negatives survive context truncation; improve accuracy on quick changes |
