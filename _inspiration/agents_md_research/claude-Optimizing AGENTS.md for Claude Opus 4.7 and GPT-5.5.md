# Optimizing AGENTS.md for Claude Opus 4.7 and GPT-5.5

**Bottom line up front:** Nearly every model claim in the upgrade brief is **VERIFIED against official Anthropic and OpenAI documentation** — Claude Opus 4.7 (released April 16, 2026) genuinely introduces an `xhigh` effort level, a new tokenizer that uses ~1.0–1.35× more tokens, public-beta task budgets, more literal instruction-following, and 2,576-pixel vision. GPT-5.5 (API-available April 24, 2026) is the current latest OpenAI model and supersedes GPT-5.4. The upgrade is **GO**, but with non-trivial editing required because (a) Opus 4.7's "more literal" behavior breaks any prompt that relied on Claude generalizing, (b) the new tokenizer inflates the cache footprint by up to 35% — every cache breakpoint needs re-budgeting, (c) `temperature` and `top_p` are now rejected with HTTP 400 on Opus 4.7, and (d) the dual-agent reviewer should move to `gpt-5.5` (or `gpt-5.5-pro` for hard cases), but the locked-baseline language in the existing AGENTS.md is now actively wrong because GPT-5.4 has been retired from ChatGPT and superseded in API. The single biggest risk is **silent prompt regression**: phrasing that worked on Opus 4.6 ("update the schema and any related code") will under-perform on 4.7 unless it explicitly enumerates the related code. The single biggest opportunity is **task budgets + adaptive thinking**, which together let one prompt run economically at low effort and escalate to `xhigh` only when the model judges the work warrants it.

The rest of this report delivers section-by-section edit recommendations with quoted current text, replacement text, source URLs, and priority ratings. A risk register, a go/no-go scorecard, and three new sections (Tokenizer Migration, Adaptive Thinking Policy, Prompt Caching Layout) are proposed at the end.

---

## 1. Verification table

The following table records the verdict on every claim in the task brief. Sources are official unless otherwise noted; dates reflect the documentation/announcement date observed during research.

| # | Claim | Verdict | Primary source |
|---|---|---|---|
| 1 | Claude Opus 4.7 exists; model ID `claude-opus-4-7` | **VERIFIED** | anthropic.com/news/claude-opus-4-7 (Apr 16 2026); platform.claude.com/docs/en/about-claude/models/overview |
| 2 | `xhigh` effort level between `high` and `max` | **VERIFIED** | platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7; Claude Code default raised to `xhigh` |
| 3 | Claude has effort levels (low/medium/high/xhigh/max) | **VERIFIED**; coexists with legacy `budget_tokens` (now rejected on 4.7) | platform.claude.com/docs/en/build-with-claude/effort and /adaptive-thinking |
| 4 | New tokenizer maps text to ~1.0–1.35× more tokens vs 4.6 | **VERIFIED** | platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7 (direct quote) |
| 5 | `task budgets` is a public beta feature | **VERIFIED**; opt-in via `task-budgets-2026-03-13` beta header | platform.claude.com/docs/en/build-with-claude/task-budgets |
| 6 | Opus 4.7 is "more literal and precise" | **VERIFIED**; Anthropic explicitly tells users to re-tune prompts | platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7 |
| 7 | Enhanced vision vs prior models | **VERIFIED**; up to 2,576 px on long edge (~3.75 MP), 1:1 pixel coords | platform.claude.com/docs/en/build-with-claude/vision |
| 8 | GPT-5.5 exists | **VERIFIED**; API rollout Apr 24 2026 | openai.com/index/introducing-gpt-5-5/ |
| 9 | GPT-5.5 has adjustable reasoning effort | **VERIFIED**; `reasoning.effort` ∈ {none, low, medium, high}; `xhigh` only on Pro/Thinking-class variants | platform.openai.com/docs/models/gpt-5; developers.openai.com/api/docs/guides/latest-model |
| 10 | GPT-5.5 "designed for outcome-based instructions" | **PARTIALLY VERIFIED / MISLEADING** — the phrase "outcome-based" appears in OpenAI prompting guidance for *reasoning models in general*, not as a unique GPT-5.5 design feature; closest real framing: "give it a goal, trust it to work out the details" | platform.openai.com/docs/guides/prompt-engineering; cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide |
| 11 | GPT-5.4 exists | **VERIFIED** — released Mar 5 2026; superseded by 5.5 on Apr 23–24 2026; baseline-locking on 5.4 is now stale | openai.com/index/introducing-gpt-5-4/; developers.openai.com/api/docs/changelog |

**Net result:** every model-feature claim is real except #10, which conflates a general reasoning-model prompting principle with GPT-5.5-specific design intent. The brief's instinct to be skeptical was correct in spirit but, in this case, the brief itself is mostly accurate. The remaining work is implementation: applying these features to AGENTS.md correctly.

---

## 2. Opus 4.7 changes by section

### 2.1 PRIORITY 0 — System constraints

**Verdict: no changes required.** Windows PowerShell redirect rules are environment-level and model-agnostic. Opus 4.7's "more literal" behavior actually *helps* compliance here — it is less likely to silently optimize away the file-redirect step. **Priority: none.**

One small enhancement is worth considering. Anthropic's own context-engineering guidance recommends section delimiters that the model can attend to reliably ("organizing prompts into distinct sections … using XML tagging or Markdown headers"; *Effective context engineering for AI agents*, anthropic.com/engineering, Sep 29 2025). The current `## PRIORITY 0` heading already does this; consider wrapping the non-negotiable rules in `<non_negotiable>...</non_negotiable>` tags inside that section to give Opus 4.7 an unambiguous attentional anchor. **Priority: Low.**

### 2.2 Communication policy and session discipline

**Current text (representative):** the file currently leaves communication style implicit, with verbosity governed by the "Verbosity Tiers" rule under Context Compression.

**Recommended addition** (place at top of Communication Policy):

> *Opus 4.7 follows instructions literally. State exactly what you want — do not rely on the model inferring related work. When you want generalization, say "apply this change everywhere it applies in the repo, then list each file you touched." When you want strict scope, say "modify only the files I named; do not edit other files even if you notice issues."*

**Source:** anthropic.com/news/claude-opus-4-7 — "where previous models interpreted instructions loosely or skipped parts entirely, Opus 4.7 takes the instructions literally. Users should re-tune their prompts and harnesses accordingly." **Priority: Critical.** This is the single most important behavioral change in 4.7 and the existing AGENTS.md is silent on it.

### 2.3 Operating Model (PLANNING / EXECUTION / VERIFICATION)

**Current text:** "Three modes map to six project roles … Mode transitions: Start in PLANNING, switch to EXECUTION after user approves plan, switch to VERIFICATION after implementation complete."

**Issue:** the modes are correctly named but the AGENTS.md does not attach a thinking-effort policy to each mode. With effort levels now the primary thinking control on Opus 4.7, the file should bind effort to mode rather than leaving it implicit at the harness level.

**Recommended replacement:**

> *Modes also bind a default reasoning effort and task budget. PLANNING runs at `effort: high` with no task budget — exploratory thinking is the goal. EXECUTION runs at `effort: medium` with a task budget proportional to MEU size (≈25k tokens per small MEU, ≈100k for large). VERIFICATION runs at `effort: xhigh` with no task budget — thorough adversarial review is the goal. Use `effort: max` only when explicitly invoked via the `/ultrareview` slash command or when the human explicitly asks for it; max is roughly 2× the latency of xhigh and is reserved for genuinely hard problems.*

**Sources:** platform.claude.com/docs/en/build-with-claude/effort (effort levels); platform.claude.com/docs/en/build-with-claude/task-budgets (task budgets, public beta via `task-budgets-2026-03-13`); anthropic.com/news/claude-opus-4-7 (Claude Code's default raised to `xhigh`, `/ultrareview` command). **Priority: High.** This is the largest single improvement available from the upgrade.

### 2.4 Roles & Workflows

**Current text:** "Six deterministic roles in .agent/roles/: orchestrator, coder, tester, reviewer, researcher, guardrail. Every plan task must have: task, owner_role, deliverable, validation, status."

**Issue:** the file treats roles as deterministic but doesn't say which role runs at which effort level, and it doesn't tell Claude when to spawn subagents versus stay in the main thread. Anthropic's *multi-agent research system* post and the Claude Code best-practices doc both make subagent spawning a first-class architectural decision.

**Recommended replacement** (append to Roles & Workflows):

> *Each role declares its execution mode and effort budget. Orchestrator and researcher run in the main thread. Coder runs in the main thread for changes ≤3 files; ≥4 files spawn a `coder` subagent per logical chunk so each chunk gets a clean context window. Reviewer always runs as a separate subagent or as the cross-vendor reviewer (see §6) — a fresh context improves code review because Claude is not biased toward code it just wrote. Tester and guardrail run in the main thread but isolate their tool calls behind tool-result clearing.*

**Sources:** code.claude.com/docs/en/best-practices ("A fresh context improves code review since Claude won't be biased toward code it just wrote. Use a Writer/Reviewer pattern."); anthropic.com/engineering/multi-agent-research-system (subagent isolation; ~1,000–2,000-token summary returns); anthropic.com/engineering/effective-context-engineering-for-ai-agents (sub-agent architectures). **Priority: High.**

### 2.5 Planning Contract

**Current text:** "Spec Sufficiency Gate — classify each required behavior as Spec/Local Canon/Research-backed/Human-approved … Boundary Input Contract — Every MEU touching external input must include …"

**Verdict: keep as-is, but add a literal-instruction guard.** The Planning Contract is well-designed and benefits from Opus 4.7's literal-following behavior — classifications will now be applied as written, not generalized. The one addition needed is an explicit instruction to the model that **uncategorized behaviors are forbidden, not "to be inferred"**.

**Recommended insertion** (under Spec Sufficiency Gate):

> *If a required behavior cannot be classified into one of the four buckets, it is a planning defect — escalate to the human and stop. Do not proceed by inferring intent. Opus 4.7 follows this rule literally; do not soften it in a working session.*

**Source:** platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7 — "The model will not silently generalize an instruction from one item to another, and will not infer requests you didn't make." **Priority: Medium.**

### 2.6 Testing & TDD Protocol

**Current text:** "Tests FIRST … FIC-Based TDD … Test Immutability: Once tests are written in Red phase, do NOT modify test assertions in Green phase."

**Verdict: keep, with one addition.** Test Immutability benefits enormously from 4.7's literal following. The one missing element is a directive about **what counts as the test**: with the new tokenizer, the same test-file dump is up to 35% larger in tokens, which can push a single MEU past a cache breakpoint mid-iteration and kick the agent out of the cache.

**Recommended addition:**

> *During Green phase, present failing tests as `pytest -x --tb=short` output (not full repository dumps). Opus 4.7's tokenizer encodes text into roughly 1.0–1.35× as many tokens as Opus 4.6, so verbose test output that previously fit one cache breakpoint may now overflow it. Use the Compression Rules (§Execution Contract) — only failing test names, plus the assertion lines.*

**Sources:** platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7 (tokenizer change); platform.claude.com/docs/en/build-with-claude/prompt-caching (cache breakpoint mechanics). **Priority: High.**

### 2.7 Execution Contract — anti-premature-stop and context window checkpoint

**Current text:** "Anti-premature-stop rule: Do NOT stop or report to user during execution unless blocked … Context window checkpoint: If context exceeds ~80% capacity, save state, complete current MEU's handoff, notify human."

**Issues:**

1. The 80% threshold dates from a 200k-context era. Opus 4.7 has a **1M-token context window** (verified at platform.claude.com/docs/en/about-claude/context-windows), but Anthropic's own guidance and third-party "context rot" research both state model accuracy degrades materially past ~50% fill. An 80% threshold on a 1M window is far too generous in practice — it puts the agent at ~800k tokens, where degradation is severe.

2. Anti-premature-stop is exactly the behavior `task budgets` was designed to manage. The current rule is correct in intent but blunt; task budgets give Opus 4.7 a running countdown so it prioritizes work and finishes gracefully rather than either stopping early or running unbounded.

**Recommended replacement:**

> *Context window checkpoint: trigger at **50% of the effective working window** (500k tokens on 1M-context models, 100k on legacy 200k models). At checkpoint: complete the current atomic step, write a structured handoff note to `.agent/notes/checkpoint-{timestamp}.md`, then either (a) compact via Claude Code's `/compact` if available, or (b) hand off to a fresh subagent with the structured note as its only handoff context. Do not continue past 50% on the same context — accuracy degrades materially past this threshold.*
>
> *Anti-premature-stop is enforced via task budgets (public beta header `task-budgets-2026-03-13`). EXECUTION mode sets `output_config.task_budget` proportional to MEU size, and Claude sees a running countdown. The model is instructed to plan toward the budget and finish gracefully; it does not stop early just to be safe, and it does not run unbounded. Pair task_budget with `max_tokens` for a hard cap — task_budget is advisory, not a hard ceiling.*

**Sources:** platform.claude.com/docs/en/about-claude/context-windows (1M context); anthropic.com/engineering/effective-context-engineering-for-ai-agents ("attention budget … context rot"); platform.claude.com/docs/en/build-with-claude/task-budgets (advisory, soft cap, pair with max_tokens). **Priority: Critical.** The 80% threshold is the largest correctness risk in the current file.

### 2.8 Context Compression Rules

**Current text:**
1. "Test Output Compression — Only output failing test names. Summarize passing as {N} passed."
2. "Delta-Only Code Sections — Use unified diff blocks instead of full file contents."
3. "Cache Boundary — Do not place dynamic content above the CACHE BOUNDARY marker."
4. "Verbosity Tiers — Default is standard (~2,000 tokens)."

**Verdict: keep all four; add three.** The existing rules align with Anthropic's `context engineering` guidance (smallest set of high-signal tokens). What is missing:

5. **Tool-result clearing**: the cookbook example *tool-use-context-engineering-context-engineering-tools* (platform.claude.com/cookbook, March 20 2026) explicitly recommends clearing stale tool results from history. Add: *Tool results older than 5 turns are summarized to a 1–2 line outcome line and the raw payload is dropped.*

6. **JIT retrieval over inline**: per the same Anthropic guidance, *prefer file paths and grep queries over inline file dumps*; load full files only on the turn they are actually edited.

7. **Tokenizer-aware budgeting**: with Opus 4.7's tokenizer change, all token counts in this file are now soft estimates. Add: *All token estimates in AGENTS.md are calibrated for Opus 4.7's tokenizer; for Opus 4.6 or earlier, scale by 0.74–1.0× downward. Re-validate via `messages.count_tokens(model='claude-opus-4-7', ...)` after material edits to AGENTS.md itself.*

**Sources:** anthropic.com/engineering/effective-context-engineering-for-ai-agents; platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools; platform.claude.com/docs/en/build-with-claude/token-counting. **Priority: High.**

### 2.9 Pre-Handoff Self-Review

**Current text:** five-item checklist distilled from "7 critical review handoffs (37+ passes) where 10 recurring patterns caused 4-11 passes per project."

**Verdict: this section is excellent and benefits directly from 4.7's "verify own outputs before reporting back" behavior.** Anthropic's release post for 4.7 notes the model "pays precise attention to instructions, and devises ways to verify its own outputs before reporting back" (anthropic.com/news/claude-opus-4-7). The existing five rules align perfectly. **Add one rule** to exploit this:

> *6. State the verification command you actually ran and paste its tail (last 20 lines). "I ran the tests" without output is no longer acceptable — Opus 4.7 is capable of producing actual evidence and the harness rewards it.*

**Priority: Medium.**

### 2.10 Vision capability addition

**Current text:** the file does not mention vision at all.

**Issue:** Opus 4.7 ships with materially upgraded vision — up to 2,576 px on the long edge (~3.75 MP), 1:1 pixel coordinate mapping with no scale-factor math, and JPEG/PNG/GIF (first frame)/WebP support, with up to 100 images per API request. For a code-review use case this enables three workflows the current AGENTS.md ignores: screenshot-driven bug reports, design-mockup parity reviews, and CI/test-output-image diff review.

**Recommended new sub-section under Roles & Workflows or VERIFICATION mode:**

> ### Visual review inputs
>
> *Reviewer accepts image inputs for: (a) screenshots of failing UI states with bug reports, (b) design mockups for parity comparison, (c) CI artifact images (charts, dashboards, snapshot diffs). Pass images at native resolution up to 2,576 px on the long edge — Opus 4.7 maps coordinates 1:1 to pixels, so the model can name UI regions by pixel range without scale conversion. Up to 100 images per request; over 20 images causes automatic downscaling to 2000×2000 px. Total payload ≤32 MB; for larger sets use the Files API and reference by file ID.*

**Source:** platform.claude.com/docs/en/build-with-claude/vision and the Opus 4.7 launch posts. **Priority: Medium** (depends on whether the team actually has visual artifacts; if pure backend repo, downgrade to Low).

### 2.11 Sampling parameters

**Current text:** does not mention temperature/top_p, but if the harness or any subagent role currently sets these, **it will fail with HTTP 400 on Opus 4.7**.

**Recommended addition** (under Skills or a new Sampling sub-section):

> *Opus 4.7 rejects `temperature`, `top_p`, and `top_k` parameters with HTTP 400. Omit them entirely from all API calls. The harness, all roles, and any third-party tooling must be audited for stray sampling-parameter usage during the upgrade.*

**Source:** platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7. **Priority: Critical** (will hard-fail otherwise).

---

## 3. GPT-5.5 changes by section

### 3.1 Dual-Agent Workflow — reviewer model

**Current text:** "Reviewer model: GPT-5.4 (locked as baseline — do not downgrade)"

**Issue:** GPT-5.4 has been superseded by GPT-5.5 (API GA April 24, 2026; openai.com/index/introducing-gpt-5-5/). The "locked as baseline" language was sound when written but is now actively misleading because GPT-5.4 is available in API but no longer in ChatGPT and is no longer the recommended OpenAI choice for new agentic work.

**Recommended replacement:**

> *Reviewer model: `gpt-5.5` via Responses API (default). Escalate to `gpt-5.5-pro` for adversarial review of security-sensitive changes or when reviewer disagrees with implementor and human arbitration is needed. The baseline floor is `gpt-5.4` — do not downgrade below it; the baseline ceiling rotates as OpenAI releases successor models. Use `reasoning.effort: medium` for routine review and `xhigh` (5.5-pro only) for adversarial. Verbosity: `low` for pass/fail and short rationale, `medium` for full reviews. Pass `previous_response_id` to chain review turns and preserve reasoning state across the review session.*

**Sources:** openai.com/index/introducing-gpt-5-5/; platform.openai.com/docs/guides/migrate-to-responses; platform.openai.com/docs/guides/latest-model. **Priority: Critical.** This is the central change driving the upgrade and the wording in the current file is now incorrect.

### 3.2 Reviewer capability

**Current text:** "Reviewer capability: Run commands, execute tests, check builds, create handoff docs with test improvements."

**Verdict: keep, but add Responses API specifics.**

**Recommended addition:**

> *Reviewer runs in OpenAI's Responses API (Chat Completions for cost-sensitive lanes). Use `previous_response_id` to chain turns within a single review — this preserves the reasoning trace across tool calls and improves agentic accuracy materially (OpenAI's published Tau-Bench Retail figures show 73.9% → 78.2% with reasoning persistence). For ZDR/stateless lanes, set `include: ["reasoning.encrypted_content"]` to round-trip encrypted reasoning items without server-side storage. Built-in tools available without custom code: `web_search`, `file_search`, `code_interpreter`, `mcp`. Reviewer should prefer built-in `code_interpreter` for short script execution over our custom run_command tool when sandboxing is sufficient.*

**Sources:** openai.com/index/new-tools-and-features-in-the-responses-api/ (March 2025); platform.openai.com/docs/guides/migrate-to-responses. **Priority: High.**

### 3.3 Validation priority

**Current text:** "Validation priority: 1. Contract tests pass/fail → 2. Security posture → 3. Adversarial edge cases → 4. Code style consistency → 5. Documentation accuracy"

**Verdict: keep order; add structured-output enforcement.** GPT-5.5 supports strict JSON schema decoding (`text.format` with `strict: true`), which can encode the validation priority as a machine-checkable schema rather than free text — making the cross-vendor handoff to Claude (or to a CI gate) deterministic.

**Recommended addition:**

> *Reviewer must return a structured output conforming to schema `.agent/schemas/review_verdict.json` (verdict ∈ {pass, fix_required, block}; per-priority findings array; evidence file:line references; recommended next action). Use Responses API `text: {format: {type: "json_schema", strict: true, schema: ...}}` for 100% schema compliance via constrained decoding. The schema is the contract — do not return prose only.*

**Source:** developers.openai.com/api/docs/guides/structured-outputs; openai.com/index/introducing-structured-outputs-in-the-api/. **Priority: High.**

### 3.4 Goal-oriented framing for the reviewer prompt

**Current text:** the reviewer instructions are procedural — they list five priorities to check.

**Issue:** OpenAI's own prompting guidance recommends *goal-oriented* prompting for reasoning models: "A reasoning model is like a senior co-worker. You can give them a goal to achieve and trust them to work out the details" (platform.openai.com/docs/guides/prompt-engineering). The current procedural framing under-utilizes GPT-5.5's reasoning. Note: the brief's claim that GPT-5.5 is *specifically* "designed for outcome-based instructions" is **partially verified / misleading** — that framing applies to reasoning models in general, not as a 5.5-unique design feature. Either way, the recommendation stands.

**Recommended replacement (paired with the procedural priorities, not in lieu of them):**

> *Reviewer goal: identify any change in this diff that could regress production behavior, weaken security posture, or violate the project's local canon. Use the five-priority list as a coverage checklist, not a script — reason about what the diff is actually trying to do, then verify it is what the spec asks for. If the implementor (Claude) appears to have generalized beyond the spec, flag it; if it appears to have followed the spec literally to a wrong conclusion, flag the spec, not the code.*

**Source:** platform.openai.com/docs/guides/prompt-engineering. **Priority: Medium.**

### 3.5 Reasoning effort and verbosity tuning

**Current text:** silent on these.

**Issue:** GPT-5.5 has both `reasoning.effort` (none/low/medium/high; `xhigh` only on Pro/Thinking variants) and `verbosity` (low/medium/high). Without explicit policy, the harness defaults are paid for on every review.

**Recommended addition:**

> *Reasoning effort policy:*
> *- Routine diff review: `reasoning.effort: medium`, `verbosity: low`*
> *- Adversarial review (security, concurrency, async edge cases): `reasoning.effort: high`, `verbosity: medium`, model: `gpt-5.5-pro` for `xhigh`*
> *- Triage / quick-pass acceptance check: `reasoning.effort: low` (or `none` for trivial style checks)*
>
> *Note: parallel tool calls are not supported when `reasoning.effort` is `minimal`/`none`. Either set effort ≥ low when the reviewer needs to run multiple tools in parallel, or set `parallel_tool_calls: false` and live with serial calls.*

**Sources:** platform.openai.com/docs/models/gpt-5; cookbook.openai.com/examples/gpt-5/gpt-5_new_params_and_tools. **Priority: High.**

### 3.6 Prompt caching for the reviewer

**Current text:** silent.

**Issue:** OpenAI prompt caching is automatic above 1,024 tokens with discounts up to ~90% on cached input on newer models, but only for **prefixes that match exactly**. The reviewer prompt should be structured as: stable system prompt → stable schema → stable repo digest → diff (variable). The current AGENTS.md does not specify this ordering.

**Recommended addition:**

> *Reviewer prompt layout (cache-optimized, in order):*
> *1. System role + project rules (static; same across every review)*
> *2. Validation schema definition (static)*
> *3. Repository digest (architecture summary, key invariants — refresh at most weekly)*
> *4. Per-MEU context: the diff, failing test output, the implementor's handoff note*
>
> *Optional: pass `prompt_cache_key` to keep similar prompts on the same routing path (15 RPM threshold per prefix-key combo). With this layout, blocks 1–3 hit the cache on every review after the first.*

**Sources:** platform.openai.com/docs/guides/prompt-caching; openai.com/index/api-prompt-caching/; cookbook.openai.com/examples/prompt_caching_201. **Priority: High.**

### 3.7 Adversarial review — dedicated lane

**Current text:** "Adversarial edge cases" appears only as priority #3 in the validation list.

**Issue:** OpenAI ships an explicit `codex-plugin-cc` (Codex plugin for Claude Code, March 30 2026; community.openai.com/t/introducing-codex-plugin-for-claude-code/1378186) with a `/codex:adversarial-review` command — i.e., an OpenAI-built Codex/GPT-5 reviewer designed to plug into Claude Code workflows. This is the exact dual-agent topology the user is building, and it is now a first-party tool.

**Recommended addition (new sub-section under Dual-Agent Workflow):**

> ### Adversarial review lane
>
> *For changes touching auth, payment flow, data deletion, RBAC, or other security-sensitive surfaces, route through the adversarial lane: invoke the Codex plugin's `/codex:adversarial-review` (or, if not installed, run a `gpt-5.5-pro` review with `reasoning.effort: xhigh` and the prompt template `.agent/prompts/adversarial-review.md`). The adversarial reviewer's role is not "find any issue" but "construct a plausible attack or failure scenario the implementor missed, and demonstrate it." Output: at minimum one concrete failing scenario or an explicit "no plausible regression found."*

**Sources:** community.openai.com/t/introducing-codex-plugin-for-claude-code/1378186 (Codex plugin announcement); github.com/openai/codex (Codex CLI). **Priority: Medium** (High if the codebase includes auth/payments).

---

## 4. Structural refactoring

The current AGENTS.md is well-organized at the section level but has three structural issues that the upgrade is a natural occasion to fix.

**Cache-friendly ordering.** Anthropic's prompt-caching guidance is explicit: *"Place static, reusable content (tool definitions, system instructions, examples) at the beginning of your prompt. Mark the end of the cacheable content using the cache_control parameter"* (platform.claude.com/docs/en/build-with-claude/prompt-caching). The CACHE BOUNDARY marker referenced in §Context Compression Rules is the right idea but is not reflected in the file's actual structure. Today, dynamic-feeling content (Validation Pipeline commands, Skills list) sits in the middle while highly stable content (PRIORITY 0, Operating Model, Roles, Planning Contract, Testing) is on either side. Recommended order:

1. PRIORITY 0 system constraints (most stable; never changes)
2. Sampling parameters & API constraints (new section; very stable)
3. Operating Model (modes + effort/budget bindings)
4. Roles & Workflows
5. Planning Contract
6. Testing & TDD Protocol
7. Execution Contract
8. Pre-Handoff Self-Review
9. **`<!-- CACHE BOUNDARY -->`**
10. Code Quality
11. Validation Pipeline (commands change occasionally)
12. Dual-Agent Workflow (model names change with releases)
13. Skills, MCP Servers, Context & Docs (most volatile)

The refactor improves cache hit rate — every routine session keeps the top 8 sections in cache; only sections 10–13 invalidate when, e.g., a new MCP server is added or the GPT-5 reviewer is upgraded again. **Priority: High.**

**Hierarchy explicitness.** The PRIORITY 0/1/2/3 hierarchy is named once at the top and then never referenced again. Anthropic's HumanLayer-style guidance and the Claude Code memory hierarchy (Managed Policy → Project Memory → Local → Auto) both treat hierarchy as a first-class concept that gets *cited* whenever rules conflict. Recommendation: each subsequent section that contains a rule should annotate the rule with `[P0]`/`[P1]`/`[P2]`/`[P3]` so the model never has to infer precedence. Example: "Anti-premature-stop rule [P2]: Do NOT stop or report …" with [P2] making clear it yields to a P0 environment-stability incident. **Priority: Medium.**

**Mode/role separation via inclusion, not conditionals.** The agents.md spec recommends nested files for monorepo-specific rules, and OpenAI's Codex CLI documents `AGENTS.override.md` for nested overrides (developers.openai.com/codex/guides/agents-md). Today's AGENTS.md tries to encode mode-conditional behavior in a single file ("During PLANNING, do X; during EXECUTION, do Y"). For the six sub-roles, consider extracting them to `.agent/roles/{orchestrator,coder,tester,reviewer,researcher,guardrail}.md` as the actual subagent system prompts, and let AGENTS.md be the cross-cutting policy file. This matches Claude Code's native `.claude/agents/` convention and OpenAI's nested-AGENTS pattern. **Priority: Medium.**

---

## 5. Internal consistency fixes

**Reviewer model lock vs reality.** The Dual-Agent Workflow says "GPT-5.4 (locked as baseline — do not downgrade)." This conflicts with Validation Pipeline (which says nothing about which model runs validation) and with the new world where GPT-5.5 is the documented latest. Resolution: change "locked as baseline" to "minimum baseline = 5.4; default = 5.5; ceiling = current latest GPT-5 family release." **Priority: Critical.**

**Verbosity Tier vs token budgets.** "Default is standard (~2,000 tokens)" under Context Compression Rules predates `task_budget` and predates the OpenAI `verbosity` parameter. Today both vendors expose a verbosity primitive natively. Resolution: re-state the tier in vendor-aligned terms — `verbosity: medium` for OpenAI calls, `effort + task_budget` for Claude calls — and make the 2,000-token figure a floor for the *human-facing* status update, not the LLM call config. **Priority: Medium.**

**Context window checkpoint at 80%.** As described in §2.7, this conflicts with both Anthropic's own context-rot guidance (~50%) and the new 1M context window (where 80% = 800k tokens, far past degradation onset). Resolution: drop to 50% of effective window. **Priority: Critical.**

**FIC-Based TDD references absent definition.** The acronym FIC is used but not expanded. If FIC stands for "Functional Intent Contract" (or whatever the local definition is), it must be expanded on first use — Opus 4.7's literal-following will not infer it from context. **Priority: Medium** (compliance fix).

**Cache Boundary marker referenced but not located.** §Context Compression Rules tells Claude not to place dynamic content "above the CACHE BOUNDARY marker," but no marker exists in the file as written. Resolution: insert the literal `<!-- CACHE BOUNDARY -->` HTML comment at the position recommended in §4 above. **Priority: High.**

**Skills section incomplete vs Roles.** Skills lists five items; Roles & Workflows references six roles. The mapping is not explicit — which Skill belongs to which role? Recommendation: add a one-line "owner role" annotation to each Skill (`Backend Startup [coder]`, `Pre-Handoff Review [reviewer]`, etc.). **Priority: Low.**

**MCP servers vs Tool guidance.** Anthropic's context-engineering post warns against bloated tool sets ("If a human engineer can't definitively say which tool should be used in a given situation, an AI agent can't be expected to do better"). The three MCP servers listed are fine, but there is no guidance on *when* to use sequential-thinking vs the model's own native thinking. Resolution: add one line to MCP Servers — *"sequential-thinking is for explicit multi-hypothesis decomposition tasks. For routine reasoning, use the model's native effort/thinking — do not invoke sequential-thinking redundantly."* **Priority: Low.**

---

## 6. New sections needed

### 6.1 Tokenizer migration

A new short section is warranted because the tokenizer change is silent — code that worked yesterday will silently overflow today.

> ### Tokenizer migration (Opus 4.7)
>
> *Opus 4.7 ships with a new tokenizer. Plain-English text encodes to roughly 1.0–1.35× as many tokens as on Opus 4.6 (up to ~35% more). All token estimates in this file, in `.agent/budgets/`, and in any cache-size assumption are calibrated for 4.7. When migrating from a 4.6-era estimate, multiply by ~1.2× as a planning heuristic. Validate via `client.messages.count_tokens(model='claude-opus-4-7', ...)` — the endpoint is free to call and supports all active models. The old `claude.ai` web tokenizer is no longer authoritative for 4.7 inputs.*
>
> *Practical implications: (1) cache breakpoints budgeted for 4.6 may now exceed the 1,024-token Sonnet/4,096-token Opus minimums in the wrong direction (still cacheable, just larger); (2) rate-limit budgeting per session should be re-baselined; (3) human-readable summaries that previously hit the 2,000-token verbosity tier may now run 2,400–2,700 tokens — re-tune the tier threshold or accept the slight inflation.*

**Sources:** platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7; platform.claude.com/docs/en/build-with-claude/token-counting. **Priority: Critical.**

### 6.2 Adaptive thinking and effort policy

A consolidated section on thinking control replaces the scattered references currently in the file.

> ### Adaptive thinking & effort policy
>
> *Opus 4.7 uses adaptive thinking by default — the model decides how much to think based on task difficulty and the configured effort level. Set `output_config: {effort: <level>}`; do not pass `thinking.budget_tokens` (rejected with HTTP 400 on 4.7).*
>
> *Effort levels and their semantic meaning:*
> *- `low` — quick mechanical edits, simple lookups, formatting*
> *- `medium` — routine implementation, single-file changes, straight-line refactors*
> *- `high` — multi-file changes, planning, architectural reasoning*
> *- `xhigh` — Claude Code's default; adversarial review, hard debugging, novel design*
> *- `max` — only via `/ultrareview` or explicit human request; ~2× xhigh latency*
>
> *Mode-to-effort binding is defined in §Operating Model. Override only when the human asks. Interleaved thinking (Claude reasoning between tool calls) is automatic on 4.7 — the legacy `interleaved-thinking-2025-05-14` beta header is silently ignored.*
>
> *Task budgets (public beta, header `task-budgets-2026-03-13`): set `output_config.task_budget: {type: "tokens", total: N}` to give Claude a running countdown across the full agentic loop (thinking + tool calls + tool results + final output). Advisory, not a hard cap. Pair with `max_tokens` for a hard ceiling. Recommended budgets: 25k for small MEU, 100k for large MEU, 250k for whole-phase verification.*

**Sources:** platform.claude.com/docs/en/build-with-claude/effort, /adaptive-thinking, /task-budgets, /extended-thinking; anthropic.com/news/claude-opus-4-7. **Priority: Critical.**

### 6.3 Prompt-cache layout contract

> ### Prompt-cache layout contract
>
> *Both Claude and the GPT-5.5 reviewer benefit materially from cache-friendly ordering. The structural rule:*
>
> *Static prefix (in order): tool definitions → system prompt (this file) → schemas → repo digest. Mark the end of the static prefix with `cache_control: {type: "ephemeral"}` on the last static block — for long-running sessions, use `{type: "ephemeral", ttl: "1h"}` (2× write premium, 0.10× read price). Maximum 4 explicit cache breakpoints per Claude request. Minimum cacheable size: 1,024 tokens for Sonnet/Opus, 4,096 for Haiku 4.5.*
>
> *What invalidates the Claude cache: changes to `tool_choice`, presence/absence of images, changes to thinking parameters/budget (invalidates message-level cache only; system and tool caches survive), any byte-level diff to the cached prefix. Order matters — caching follows tools → system → messages, and a change at any level invalidates that level and all subsequent levels.*
>
> *OpenAI prompt caching is automatic, no breakpoints required, ≥1,024 tokens minimum, with cache-eviction at ~5–10 minutes idle (up to 1 hour off-peak; 24h via Extended Prompt Cache Retention if enabled). Cached input is discounted up to ~90% on newer models. Use the same static-first layout — exact-prefix match is required.*

**Sources:** platform.claude.com/docs/en/build-with-claude/prompt-caching; platform.openai.com/docs/guides/prompt-caching; openai.com/index/api-prompt-caching/. **Priority: High.**

### 6.4 Cross-vendor handoff protocol

The current Dual-Agent Workflow tells Claude to hand to GPT-5 but does not define the wire format.

> ### Cross-vendor handoff protocol
>
> *Implementor → Reviewer handoff payload (JSON, validated against `.agent/schemas/handoff.json`): {meu_id, spec_refs[], files_changed[], diff (unified, ≤500 lines or summarized + linked), tests_run[], tests_passing, tests_failing[], residual_risks[], implementor_confidence ∈ [0,1], implementor_reasoning_summary (≤500 tokens; not the raw thinking trace)}.*
>
> *The reviewer sees the handoff payload, the diff, and the failing-test output — it does NOT see Claude's raw thinking blocks. This is intentional: cross-vendor critic effectiveness depends on the reviewer reasoning independently rather than rubber-stamping the implementor's logic. (Self-Contrast, arxiv 2401.02009, finds intrinsic self-reflection often fails due to overconfidence; diverse perspectives are the robust pattern.)*
>
> *Reviewer → Implementor handoff: structured-output JSON conforming to `.agent/schemas/review_verdict.json` (verdict, findings with file:line evidence, recommended next action). On `fix_required`, Claude receives only the findings — it does not retain the reviewer's prose chain-of-thought, again to preserve independent reasoning on the next implementor iteration.*

**Sources:** code.claude.com/docs/en/best-practices (Writer/Reviewer fresh-context principle); developers.openai.com/api/docs/guides/structured-outputs; arxiv 2401.02009 (Self-Contrast). **Priority: High.**

---

## 7. Risk assessment and go/no-go

### 7.1 Go/no-go scorecard for the upgrade

| Dimension | Opus 4.6 → 4.7 | GPT-5.4 → 5.5 |
|---|---|---|
| Capability uplift | Strong: literal instruction following, vision +2.3×, 1M context standard | Strong: 1M API context, improved agentic coding, 5.5-Pro adds xhigh |
| API compatibility | Breaking: `temperature`/`top_p`/`top_k` rejected with HTTP 400; `thinking.budget_tokens` rejected; tokenizer counts shift up to 1.35× | Mostly additive; reasoning/verbosity values stable; minimal `none` default differs from 5.4 |
| Prompt rewriting required | Yes — literal-following demands explicit enumeration where 4.6 generalized | Light — prompt structure unchanged, switch is mostly model-name |
| Cost direction | Mixed: more tokens per text (worse) but adaptive thinking + task budgets (better); `xhigh` adds latency vs `high` | Mostly down: cache discounts increased on newer models; 5.5-Pro priced for hard cases only |
| New capabilities worth adopting | xhigh, task budgets, hi-res vision, /ultrareview | Responses API reasoning persistence, encrypted reasoning items, structured outputs strict mode |
| Risk if NOT upgraded | Falling behind Anthropic's deprecation curve; Opus 4 and 4.1 already deprecated from Claude Code | GPT-5.4 supersedure imminent; 5.4 already retired from ChatGPT |
| Decision | **GO** with the prompt rewrites in §2 | **GO**, with default = `gpt-5.5`, escalate to `gpt-5.5-pro` for adversarial |

### 7.2 Risk register

**R1 — Silent literal-following regressions [Critical, likely].** Prompts that worked on 4.6 by relying on Claude generalizing ("update the schema and any related code") will under-perform on 4.7. Mitigation: §2.2 communication policy edit; spot-check first 5 sessions post-upgrade against the prior reviewer's verdict.

**R2 — Stray sampling parameters [Critical, possible].** Any code path that sets `temperature`, `top_p`, or `top_k` will hard-fail with HTTP 400 on Opus 4.7. Mitigation: §2.11 sampling section + grep audit during upgrade.

**R3 — Cache invalidation after tokenizer change [High, certain].** All previously-warmed caches are useless on 4.7 — token boundaries shift. Mitigation: schedule the upgrade during a lull; expect first-day costs ~10% above steady-state until caches re-warm.

**R4 — Context-window checkpoint at 80% [High, certain].** Hitting the existing 80% checkpoint on a 1M context puts the agent at 800k tokens, deep in context-rot territory. Mitigation: §2.7 drop to 50%.

**R5 — `task_budget` is advisory, not a hard cap [Medium, likely].** Task budgets do not stop the model from exceeding them. Mitigation: pair with `max_tokens` as the explicit hard cap; alert if `task_budget` is exceeded by >25%.

**R6 — Cross-vendor reviewer schema drift [Medium, possible].** OpenAI's structured-output strict mode is reliable, but the reviewer schema must be in sync between implementor (Claude reads the verdict) and reviewer (GPT-5.5 produces it). Mitigation: keep `.agent/schemas/review_verdict.json` as the single source of truth; both sides reference by path, not inline copy.

**R7 — `xhigh` latency surprise [Medium, likely].** Claude Code's new default is `xhigh`, which is slower than the previous `high`. Total wall-clock time per session may rise even though token cost falls (because adaptive thinking trims budget where unneeded). Mitigation: bind effort to mode (§2.3) so EXECUTION stays at `medium`; reserve `xhigh` for VERIFICATION.

**R8 — GPT-5.5 `parallel_tool_calls` × low effort interaction [Low, certain].** Parallel tool calls are not supported when reasoning effort is `none`/`minimal`. Mitigation: §3.5 — set effort ≥ `low` when parallel tools are needed, or set `parallel_tool_calls: false`.

**R9 — Codex plugin adoption decision [Low, optional].** The OpenAI Codex plugin for Claude Code provides a turn-key adversarial reviewer but adds another moving part. Mitigation: defer until a security-sensitive MEU actually needs it; the bare `gpt-5.5-pro` review path covers 95% of cases.

**R10 — Vision feature scope-creep [Low, possible].** Hi-res vision is genuinely better, but if the team has no visual artifacts the §2.10 section invites rule bloat. Mitigation: gate the vision section behind an "if visual artifacts present" preface, or omit entirely on backend-only repos.

### 7.3 Breaking changes summary (the must-fix list)

These items will fail if not addressed before the model swap:

1. **Remove `temperature`/`top_p`/`top_k` from all Claude API calls** (HTTP 400 on Opus 4.7). Audit harness, all six role configs, and any direct SDK usage.
2. **Replace `thinking.budget_tokens` with `output_config.effort`** on Opus 4.7 paths. The legacy parameter is rejected.
3. **Update reviewer model name** from `gpt-5.4` to `gpt-5.5`/`gpt-5.5-pro` in all configs and prompts. Confirm Responses API is the call surface (Chat Completions still works but loses reasoning persistence and built-in tools).
4. **Drop the context-window checkpoint to 50%** of effective window. The 80% threshold is materially unsafe on a 1M-token context.
5. **Re-budget all token estimates** for the new tokenizer (~1.0–1.35× shift). Affects task budgets, verbosity tiers, cache break placement, and any rate-limit budgeting.

The first three are hard failures; the last two are correctness regressions that only manifest under load or on long sessions.

---

## 8. Conclusion — what changes and why it matters

The upgrade is a **GO**, but the brief's instinct to verify everything against primary sources was the right discipline — it surfaced one important distinction (the GPT-5.5 "outcome-based" framing is reasoning-models-general, not 5.5-specific) and it confirmed every other claim against official Anthropic and OpenAI documentation released between September 2025 and April 2026. The four most consequential edits, in order of impact:

The **literal-following clause in Communication Policy** (§2.2) is the single highest-leverage change in this entire report. Anthropic's own release post explicitly tells users to re-tune prompts because Opus 4.7 will not infer requests not made. Every other edit is downstream of this behavioral shift. The **context-window checkpoint at 50%** (§2.7) prevents the silent accuracy collapse that 1M-token windows otherwise enable; the existing 80% rule is a relic of the 200k era. The **mode-to-effort binding** (§2.3) and the **task-budget public beta** (§6.2) together give the agent a principled cost/latency dial that the current AGENTS.md handles via blunt `max_tokens` only. And the **reviewer model swap to GPT-5.5** with structured-output verdicts and Responses-API reasoning persistence (§3.1, §3.3, §6.4) modernizes the dual-agent topology to the patterns OpenAI itself now ships in the Codex plugin.

Two risks remain in the "watch carefully" bucket rather than the "block on" bucket. The new tokenizer means the first week post-upgrade will run materially hotter on cache-write costs while caches re-warm, and the prompt-cache layout in §6.3 will only realize its full value once the static prefix has stabilized. And the cross-vendor reviewer pattern is well-attested as qualitatively useful but no peer-reviewed benchmark exists for "Claude implementor + GPT-5 reviewer" specifically — the strongest defensible claim is that divergent training distributions yield divergent failure modes, which is exactly what an adversarial reviewer needs.

Net assessment: this upgrade pays for itself within the first 50 sessions through `xhigh` defaults catching review issues earlier, task budgets right-sizing executions that previously over-spent at uniform `high`, and the GPT-5.5 reviewer's structured-output verdicts eliminating the prose-parsing layer between reviewer and implementor. The work to capture that value is the prompt rewriting cataloged above — small in scope, high in leverage, and mostly a one-time edit.
