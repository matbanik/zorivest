# Agentic AI artifact design for multi-agent software engineering

**Structured markdown artifacts with versioned schemas, explicit action contracts, and self-correcting templates solve the format drift problem in dual-agent systems.** Research across Anthropic's internal pipelines, 10 major frameworks, and 15+ academic papers converges on a clear finding: agents communicating through structured documents with defined schemas dramatically outperform those using free-form dialogue. MetaGPT's SOP-mandated document approach scored **3.9 vs ChatDev's 2.1** on software benchmarks — the most rigorous evidence that structure matters. For a system producing 333+ handoffs in 30 days with 70KB append-only review files, the path forward involves versioned file chains capped at 10KB, YAML frontmatter contracts, typed status enums, and a meta-reflection loop that detects and corrects template drift automatically.

This report synthesizes findings from Anthropic's engineering blog posts, Google's Agent Development Kit, the A2A protocol specification, 8 academic papers (ICLR 2024–2026, ACL 2024–2025, NeurIPS 2024), and production implementations from AutoGen, CrewAI, LangGraph, MetaGPT, ChatDev, OpenHands, SWE-Agent, Aider, and Claude Code.

---

## 1. Contract-based agent communication demands typed metadata and explicit action verbs

When markdown files are the sole communication channel between two agents with no shared context, every artifact must function as a self-contained contract. Research from Anthropic, XTrace, and Skywork converges on **seven required metadata fields** that constitute the minimum viable handoff:

```markdown
---
handoff_id: HO-2026-0334
schema_version: 2.1.0
created: 2026-04-06T14:30:00Z
source_agent: implementation
target_agent: validation
status: AWAITING_REVIEW          # closed enum, never free text
action_required: VALIDATE_FEATURE # explicit verb + object
scope: feature/user-auth-flow
parent_handoff: HO-2026-0330
---
```

The **`action_required` field is the single most critical element**. XTrace's research on agent context handoff demonstrates that agents fail when they receive a "context dump" without knowing what to *do* with it — a receiving agent needs an explicit verb, not just data. Anthropic's long-running agent harness reinforces this: without explicit scope, agents "try to do too much at once" or "declare victory on the entire project too early."

**Anthropic's internal patterns reveal four specific artifact designs.** First, the `claude-progress.txt` pattern: each coding agent reads a structured progress file at session start and updates it at session end, containing what was done, what failed, and what's next. Second, the `feature_list.json` pattern: features tracked as JSON objects with `passes: true/false` status. Critically, **Anthropic chose JSON over markdown for this data because "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files"** — directly relevant to format drift. Third, the sprint contract pattern: in their 3-agent architecture (planner/generator/evaluator), "before each sprint, the generator and evaluator negotiated a sprint contract: agreeing on what 'done' looked like for that chunk of work before any code was written." Fourth, in their multi-agent research system, subagents store work in external systems and pass lightweight references back to the coordinator, preventing information loss and reducing token overhead.

The documented failure modes when artifacts lack structure extend well beyond the three known issues. The table below catalogs ten distinct failure patterns observed across production systems:

| Failure mode | Description | Source |
|---|---|---|
| **Claim-to-state drift** | Agent claims something is done but filesystem state doesn't match | Anthropic harness blog |
| **Evidence staleness** | Cited evidence outdated as code changes; no timestamp/commit linking | Anthropic sprint contracts |
| **Fix-specific-not-general** | Agent fixes specific case without addressing root cause | Validation loop pattern |
| **Context dump fallacy** | Large unstructured context transfers increase noise, degrade reasoning | XTrace |
| **Telephone game degradation** | Each summarization step loses fidelity; fifth agent has degraded access to original data | XTrace, Anthropic |
| **Schema drift** | Model adds unexpected fields, renames keys, nests differently than specified | Tetrate |
| **Premature victory** | Agent sees progress and declares done without testing all criteria | Anthropic harness |
| **Context anxiety** | Models wrap up work prematurely near perceived context limits | Anthropic |
| **Self-evaluation leniency** | Agents confidently praise their own mediocre work | Anthropic |
| **Competing templates** | Different sessions produce slightly different formats; cascading parse failures | Skywork |

**Feature Intent Contracts should be structured for binary verifiability.** Anthropic's evaluator used "hard thresholds — if any one fell below it, the sprint failed." Every acceptance criterion must resolve to PASS/FAIL with a specified verification method:

```markdown
## Acceptance Criteria (Verifiable)
| ID | Criterion | Verification Method | Pass Condition |
|----|-----------|-------------------|----------------|
| AC-01 | Login form renders | Navigate to /login | Form visible with email + password fields |
| AC-02 | Valid credentials grant access | Submit valid creds | Redirect to /dashboard, JWT in cookie |
| AC-03 | Invalid credentials show error | Submit invalid creds | Error message displayed, no redirect |

## Evidence Requirements
For each AC, the implementation agent MUST provide:
1. Commit hash where the feature was implemented
2. Test file path and test type (unit/integration/e2e)
3. Test output (stdout/stderr or screenshot)

## Verdict Schema (JSON in fenced block for deterministic parsing)
```json
{
  "contract_id": "FIC-2026-0042",
  "verdict": "PASS",
  "criteria_results": [
    {"id": "AC-01", "result": "PASS", "evidence": "screenshot-path"},
    {"id": "AC-02", "result": "FAIL", "evidence": "error-log-path", "failure_reason": "..."}
  ]
}
```

The verdict uses constrained JSON rather than prose to prevent the self-evaluation leniency problem. The contract must be negotiated *before* implementation begins — this prevents the moving-goalposts anti-pattern where criteria are written post-hoc to match what was built.

---

## 2. Versioned file chains beat append-only documents by a wide margin

The current 70KB append-only review files represent approximately **18,000–23,000 tokens** — deep in the zone where LLM accuracy degrades severely. Three independent studies quantify this degradation. Liu et al.'s "Lost in the Middle" (Stanford/TACL 2024) demonstrated **30%+ accuracy drops** when relevant information sits in the middle of context versus the beginning or end, following a U-shaped attention curve affecting all models. Chroma's 2025 "Context Rot" study tested 18 frontier models and found accuracy drops of **20–50% from 10K to 100K tokens**. Du et al. (2025) showed even whitespace padding alone causes 17–20% degradation under 30K tokens.

The optimal architecture is a **versioned chain with a rolling summary header**. Each review pass becomes a separate file (`review-042-v1.md`, `review-042-v2.md`, `review-042-v3.md`), with the latest version containing a compact summary of prior passes plus the full current review:

```markdown
# Review Chain: TASK-042

## Current Status (v3) — 2026-04-06
- **Verdict**: PASS_WITH_NOTES
- **Open items**: 1 minor (logging format)
- **Previous**: review-042-v2.md → FAIL (2 blockers)

## Prior Pass Summary
| Pass | Date | Verdict | Key Finding |
|------|------|---------|-------------|
| v1 | Apr 4 | FAIL | Missing error handling in auth module |
| v2 | Apr 5 | FAIL | Test coverage below 80% threshold |
| v3 | Apr 6 | PASS_WITH_NOTES | All blockers resolved |

## Current Pass Details
[... focused review content for this pass only ...]
```

**Concrete size budgets keep each file under 10KB (~3,000–4,000 tokens):**

| Section | Target |
|---------|--------|
| Summary header + prior pass table | ~700 tokens |
| AC traceability table | ~400 tokens |
| TDD evidence chain | ~700 tokens |
| Pre-existing failures baseline | ~270 tokens |
| Current pass review details | ~2,000 tokens |
| **Total** | **~4,000 tokens (~10KB)** |

Google's Agent Development Kit validates this approach explicitly — it treats large data as **named, versioned artifacts** with a "handle pattern" where large data lives in an artifact store and the prompt contains only lightweight references. DevOps best practice from JFrog Artifactory and Sonatype Nexus enforces immutable, permanently-versioned artifacts with semantic versioning. Git-based code review systems (Gerrit's patchset model, GitHub PR reviews) all use the versioned approach: each review iteration is a separate reviewable snapshot, not appended text.

---

## 3. Self-improving templates detect drift through schema hashing and meta-reflection

Three drift types threaten the dual-agent system: **prompt drift** (template instructions diverging across sessions), **concept drift** (changing input/output relationships over time), and **agent drift** (misalignment between expected and actual agent behavior). Research shows ~91% of ML models degrade over time without proactive intervention.

The most practical detection mechanism is **schema hash validation on every handoff**. Each artifact includes a hash of the canonical template it was generated from; mismatches trigger immediate flagging:

```markdown
---
template_version: "2.3.1"
schema_hash: "sha256:a3f2b1c..."
canonical_source: /templates/handoff.md
drift_score: 0.02  # 0.0 = identical, 1.0 = fully diverged
---
```

GitHub's Spec-Kit project (Issue #682) demonstrates a real-world pattern for drift detection: provenance headers in generated files, flow gating where downstream commands verify provenance before processing, and a drift checker script that compares project templates with upstream canonical versions reporting ADDED/REMOVED/CHANGED sections.

**Meta-reflection extracts reusable rules from execution friction.** The Meta-Reflection paper (Wang et al., ACL 2025) introduces a codebook of reflective insights indexed by vector similarity — on new problems, the system retrieves similar past reflections to guide reasoning in a single inference pass. CLIN (Allen AI, Majumder et al. 2023) uses **causal abstractions** with linguistic uncertainty markers ("may," "should," "must") stored in persistent textual memory, generating meta-memory summaries across episodes. CLIN outperformed Reflexion by **23 absolute points** on ScienceWorld.

A practical session retrospective format for the dual-agent system:

```markdown
# Session Retrospective: S-043 — 2026-04-06

## Friction Log
| Handoff # | Friction Type | Description | Severity |
|-----------|--------------|-------------|----------|
| #247 | Format Mismatch | Missing `## Status` section | High |
| #251 | Schema Violation | Used `status:` instead of `## Status` | Medium |

## Causal Analysis
- Root Cause: Agent omitted Status section when context exceeded 4000 tokens
- Pattern: Long context → section truncation → downstream parse failure

## Extracted Rules
### RULE-087: Status section preservation
- Trigger: Any handoff generation
- Rule: `## Status` MUST appear within first 500 tokens
- Confidence: must (validated across 15 occurrences)

### RULE-088: Long context truncation guard
- Trigger: Context window > 3500 tokens
- Rule: Prioritize structural headers over content detail
- Confidence: should (validated across 3 occurrences)

## Template Delta
```diff
+ ## Status  ← now enforced as required first-level section
  ## Changes
  ## Validation Results
- ## Notes (optional)  ← deprecated, merged into Changes
```
```

**Rule propagation follows a four-layer pipeline.** Layer 1: session-level extraction of candidate rules with confidence levels. Layer 2: validation against the last 50 handoffs as a regression check. Layer 3: promoted rules merged into the canonical template via diff, version incremented using semver. Layer 4: every 50 handoffs, a meta-reflection prunes outdated rules and resolves conflicts. GEPA (Agrawal et al., 2025) — now integrated into MLflow, DSPy, Google ADK, and OpenAI's Cookbook — provides the most advanced framework for this, maintaining a **Pareto frontier** of diverse prompt variants and outperforming GRPO by 6 percentage points using 35× fewer rollouts.

The AGENTS.md standard (now under the Linux Foundation's Agentic AI Foundation) demonstrates living documentation that evolves with the system. GitHub's analysis of 2,500+ repositories found that the best AGENTS.md files use executable commands for self-verification, three-tier boundaries ("always do / ask first / never do"), and concrete code examples over abstract descriptions.

---

## 4. Evidence chains require structured tables linking criteria to tests to timestamps

Simon Willison's agentic engineering patterns confirm that Red/Green TDD is a "pleasingly succinct" instruction for coding agents — every good model understands the shorthand. The evidence chain must capture three phases with timestamps, file paths, and output hashes:

```markdown
## TDD Evidence Chain: TASK-042

### Phase: RED (Tests Written, Expected to Fail)
- **Timestamp**: 2026-04-05T14:32:00Z
- **Test file**: `tests/test_auth_handler.py`
- **Run command**: `pytest tests/test_auth_handler.py -v`
- **Result**: ❌ FAIL (3 failed, 0 passed)
- **Output hash**: `sha256:a1b2c3...`

### Phase: GREEN (Implementation Complete)
- **Timestamp**: 2026-04-05T15:10:00Z
- **Files modified**: `src/auth_handler.py` (new), `src/__init__.py`
- **Run command**: `pytest tests/test_auth_handler.py -v`
- **Result**: ✅ PASS (3 passed, 0 failed)
- **Full suite**: `pytest --tb=short` → 47 passed, 0 failed
```

The **acceptance criteria traceability matrix** maps each criterion to its test function, status, and evidence in a single scannable table:

```markdown
| AC ID | Criterion | Test Function | Status | Evidence |
|-------|-----------|---------------|--------|----------|
| AC-1 | Valid JWT returns user | `test_valid_token_returns_user` | ✅ PASS | Green at 15:10 |
| AC-2 | Expired JWT raises error | `test_expired_token_raises` | ✅ PASS | Green at 15:10 |
| AC-3 | Malformed JWT raises error | `test_malformed_token_raises` | ✅ PASS | Green at 15:10 |
| AC-4 | Rate limiting enforcement | `test_rate_limit_enforcement` | ⚠️ PARTIAL | Edge case at 99 |
| AC-5 | Audit log on failure | NOT_IMPL | ❌ | Deferred to TASK-043 |
```

**Pre-existing failures must be explicitly classified** to prevent them from blocking unrelated work. Industry patterns from Azure DevOps, Harness, and Atlassian's Flakinator (which recovered 22,000+ builds and identified 7,000 unique flaky tests) converge on a four-category classification:

```markdown
## Known Failures Baseline
Classification:
- KNOWN_FAIL: Bug exists, tracked, not related to current work
- QUARANTINED: Flaky, temporarily excluded from gate decisions
- EXPECTED_FAIL: Intentionally failing (e.g., TDD red phase)
- REGRESSION: New failure introduced by current work (BLOCKS)

| Test | Classification | Ticket | Since |
|------|---------------|--------|-------|
| `test_legacy_csv` | KNOWN_FAIL | BUG-789 | Mar 15 |
| `test_network_retry` | QUARANTINED | BUG-801 | Mar 28 |

> Gate rule: Only REGRESSION failures block handoff.
```

Evidence bundles should include a manifest with commit SHA, test command, pass rate, coverage percentage, and content hash — mirroring CI/CD compliance patterns from PCI-DSS 4.0 and EU AI Act evidence pack requirements that mandate cryptographic checksums and append-only storage proofs.

---

## 5. Agent-native documents maximize density at the top and use hybrid formatting

**Markdown is the optimal base format**, delivering ~85% token reduction over HTML (Cloudflare) and better extraction accuracy than HTML for tables (**60.7% vs 53.6%**, ReleasePad). However, for structured tracking data that must resist agent modification, JSON embedded in fenced code blocks is more robust — Anthropic found models are less likely to corrupt JSON entries than markdown. CSV outperforms JSON by **40–50%** for tabular data. The TOON format (Token-Oriented Object Notation) achieves **30–60% fewer tokens** than JSON for structured data while maintaining extraction accuracy across GPT-5 Nano, Gemini Flash, and Claude Haiku.

**Section ordering must exploit the U-shaped attention curve.** Information at the beginning and end of context is retrieved most reliably; middle content suffers 30%+ accuracy drops. The optimal ordering for agent-consumed documents:

```markdown
# [Document Type]: [Feature/Scope]     ← IDENTITY (first 10 tokens)
## Status: AWAITING_REVIEW              ← IMMEDIATE SIGNAL (first 50 tokens)
## Action Required: VALIDATE AC-01–05   ← WHAT TO DO (first 100 tokens)
## Summary                              ← COMPRESSED CONTEXT (3-5 lines)
## Acceptance Criteria                  ← VERIFIABLE CONTRACT
## Changes / Evidence                   ← SUPPORTING DETAIL
## Decisions Made                       ← REASONING CHAIN
## Open Issues                          ← RISK SIGNALS
## History                              ← LEAST URGENT (at bottom)
---
metadata_footer:                        ← MACHINE-PARSEABLE TAIL
  handoff_id: HO-2026-0334
  commit: abc123f
```

**Deterministic parsing requires five formatting disciplines.** YAML frontmatter with `---` delimiters is the most reliably parseable section. Markdown tables with `|` separators provide explicit column structure. Status fields must use closed enums (`PASS | FAIL | BLOCKED`), never free text — "a field named 'priority' might be interpreted as a number, a string, or a boolean depending on context." Heading hierarchy must be semantic and never skip levels — LLM comprehension improved **15–20%** in RAG setups with clean heading structure. JSON for machine-critical data should be embedded in fenced code blocks with language tags.

For dual-audience design (agent parsing + human review), the document uses three layers: YAML frontmatter for machine-parseable metadata, narrative sections with emoji indicators (🟢🟡🔴) for human scanning, and structured JSON blocks for deterministic agent extraction. Emoji status indicators serve both audiences — humans scan them instantly while agents parse them as tokens mapping to status enums. Using both simultaneously (`🟡 AWAITING_REVIEW`) provides maximum compatibility.

---

## 6. Real-world frameworks validate structured artifacts over free-form dialogue

Across 10 major frameworks, a clear spectrum of communication structure emerges, with more structured approaches consistently producing better outcomes:

| Structure level | Framework | Communication pattern | Quality indicator |
|---|---|---|---|
| Highest | MetaGPT | SOP-mandated documents (PRDs, API specs, file lists) | 3.9/5 SoftwareDev, 100% completion |
| High | LangGraph | TypedDict state schemas with reducer functions | 400+ production companies |
| Medium-high | CrewAI | Pydantic model outputs with guardrails | Easy start, limited ceiling |
| Medium | Claude Code | Filesystem mailboxes + Task objects | Production at Anthropic |
| Medium | ChatDev | ChatChain JSON messages + format markers | 2.1/5 SoftwareDev |
| Low | SWE-Agent | Thought/action/observation JSON trajectories | 77.6% SWE-bench (OpenHands) |
| Lowest | Aider | Plain text SEARCH/REPLACE blocks | 61% refactoring benchmark |

**MetaGPT's SOP approach is the strongest validation** of structured artifact communication. Its central thesis — agents communicating via structured artifacts (PRDs, UML diagrams, API specs) dramatically outperform agents using unstructured dialogue — produced 100% task completion rates and SOTA scores on HumanEval (85.9%) and MBPP (87.7%). The publish-subscribe message pool where agents subscribe to relevant artifact types from other roles directly parallels implementation/validation agents reading and writing shared markdown files.

**CAID (Centralized Asynchronous Isolated Delegation, arXiv 2025)** provides the closest academic analog to the dual-agent markdown system. Its three primitives — centralized task delegation, asynchronous execution, and isolated workspaces via git worktree — achieved **+26.7% accuracy** over single-agent baselines. The paper states explicitly: "All communication between the manager and engineers uses structured JSON instructions and git commits rather than free-form dialog, avoiding the inter-agent misalignment that has been identified as the primary failure mode in multi-agent systems."

The ICLR 2026 Workshop paper on "Shared Cognitive Substrates" argues that **"natural language should serve as an interface to multi-agent coordination, not its substrate"** — identifying three structural failure modes: information loss (typed structures become untyped strings), consistency failure (no dependency tracking between parallel agents), and coordination overhead (cost scales with token count, not semantic content). This provides the theoretical foundation for structured markdown over conversational exchange.

**Claude Code's production multi-agent system validates filesystem-based communication.** Agent teams use tmux-spawned subagents communicating through filesystem mailboxes, with a task list tracking status (pending/in_progress/completed) and blocking dependencies. Claude Code Review (launched March 2026) spawns specialized agents in parallel (logic, security, regression, pattern compliance, performance), then an aggregator deduplicates findings — an architecture directly applicable to the dual-agent system.

**Aider's counter-intuitive finding matters for code artifacts specifically**: extensive benchmarking showed that JSON/function calls are *worse* than simple text formats for code editing. "Stuffing source code into JSON is complicated and error prone" due to escaping issues. This means the dual-agent system should use structured markdown/JSON for *metadata and contracts* but plain text or diff formats for *code content*.

Two emerging protocols define the future landscape. Google's **A2A (Agent-to-Agent Protocol)**, now under the Linux Foundation, standardizes agent-to-agent communication with Agent Cards for capability discovery, Tasks with lifecycle states, and typed Artifacts as outputs. Anthropic's **MCP (Model Context Protocol)** standardizes agent-to-tool communication. For a simpler dual-agent system, these protocols are heavyweight, but their design principles — typed artifacts, task lifecycle management, capability discovery — directly inform good architecture.

---

## Conclusion: a unified architecture for the dual-agent system

The research converges on a specific architecture. Every handoff artifact should use **YAML frontmatter for typed metadata** (status enums, action verbs, schema version, handoff chain links) and **markdown body for narrative content** (summaries, evidence, decisions). Structured tracking data like acceptance criteria verdicts should use **JSON in fenced code blocks** — the format most resistant to agent modification. Each review pass should be a **separate versioned file capped at 10KB**, with the latest file containing a compact summary table of prior passes. A **schema hash validation** on every handoff catches drift immediately, while periodic **meta-reflection sessions** extract reusable rules using CLIN-style causal abstractions with may/should/must confidence levels. The canonical template lives in a single `_templates/` directory, versioned with semver, and only the human orchestrator can promote template changes.

Three insights emerged that were not obvious before this research. First, Anthropic's explicit finding that JSON resists agent modification better than markdown suggests a hybrid format — not pure markdown — is optimal for the contract layer. Second, the 10KB ceiling is not arbitrary: it follows directly from the U-shaped attention curve and measured 20–50% accuracy degradation in the 10K–100K token range. Third, the self-correction loop should not run continuously but on a cadence (every 20–50 handoffs), because the Reflection-in-Reflection framework found that "overlong refinement causes conceptual drift" — too much self-improvement is as harmful as too little.
