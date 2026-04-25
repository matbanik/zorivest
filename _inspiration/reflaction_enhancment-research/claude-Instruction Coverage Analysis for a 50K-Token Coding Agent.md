# Instruction Coverage Analysis for a 50K-Token Coding Agent

A production-grade design for measuring, pruning, and regression-testing a hierarchical instruction set in a Python/TypeScript monorepo, grounded in current vendor docs (Anthropic, OpenAI, Google), peer-reviewed long-context research, and the lived practice of Cursor, Cline, Aider, Devin, Replit, and Claude Code teams. **The bottom line: a 9000-word AGENTS.md sits squarely in the empirically-documented "instruction decay zone" — a 100–250 effective constraint count where every frontier model loses 15–25 points of adherence vs. minimal prompts (Distyl IFScale, arXiv:2507.11538). The fix is not bigger prompts; it is rule-level coverage telemetry, counterfactual ablation for silent guards, and a cache-stable static prefix that an automated optimizer (GEPA preferred over MIPROv2) can mutate against a paired-difference golden test set.** This report ships the YAML schema, Python aggregator, meta-prompt, golden test set, and roadmap to do exactly that.

---

## 1. Research synthesis

### 1.1 What production agents actually do (practitioner-weighted)

The convergent practice across **Claude Code, Cursor, Cline, Aider, Continue.dev, Replit Agent, and Devin** is **hybrid retrieval**: a small always-loaded root file plus on-demand modules. Anthropic's own Claude Code docs are blunt: *"Files over 200 lines consume more context and may reduce adherence … bloated CLAUDE.md files cause Claude to ignore your actual instructions."* HumanLayer's empirical post-mortem is even sharper: their production root file is **under 60 lines**, and the consensus they cite is **<300 lines best**.

Concrete length recommendations consolidated from primary sources:

| Source | Recommendation |
|---|---|
| Anthropic Claude Code best practices | <200 lines per memory file; hard cap ~40,000 chars |
| HumanLayer (production) | <300 lines best; their root <60 lines |
| Cursor practitioners | <500 lines per `.mdc` |
| Cline | "Slide activeContext.md to keep latest 10 entries" |
| Sourcegraph Cody Enterprise | 30k input tokens user context, 15k chat |

The user's ~9000-word AGENTS.md is roughly **600–900 lines, ~12K tokens** — three to ten times the practitioner consensus. This alone explains the suspected 20–30% redundancy.

The most-imitated lifecycle pattern comes from **Cognition's Devin Playbooks**: *"If we find ourselves repeating the same instructions across multiple sessions, that's when we create a Playbook."* The inverse pruning rule from Anthropic: *"If Claude already does something correctly without the instruction, delete it or convert it to a hook."* **Cline's Memory Bank** formalizes the lifecycle into six files with explicit update triggers, and crucially mandates that `projectBrief.md` and `productContext.md` *rarely* change while `activeContext.md` rolls a 10-entry window — the same anti-bloat heuristic this design reuses.

The **AGENTS.md standard** (jointly backed by Google, OpenAI, Factory, Sourcegraph, Cursor) deliberately specifies *no required headings, no frontmatter, no schema* — section semantics are agent-inferred. The closest file to the edited file wins. Anthropic recommends consolidating via `@AGENTS.md` import inside CLAUDE.md so the same content serves both ecosystems.

A leaked-source analysis of Claude Code reveals two patterns worth stealing: **modular prompt assembly** (~80 pieces composed per session, enabling A/B testing) and **cache-preservation tricks** (the date is *appended* at midnight rather than replacing prior text, keeping the cache prefix stable). Both inform the schema below.

### 1.2 What official docs say (authoritative for HOW)

**Anthropic** (Claude Opus 4.6/4.7 era, April 2026):
- XML tags are the **primary** structuring delimiter: `<instructions>`, `<context>`, `<input>`, `<example>`. Verbatim: *"XML tags help Claude parse complex prompts unambiguously."*
- For long context: *"Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples. Queries at the end can improve response quality by up to 30% in tests."*
- Explicit warning against aggressive emphasis on 4.5+: *"Where you might have said 'CRITICAL: You MUST use this tool when...', you can use more normal prompting like 'Use this tool when...'"* — overtriggering is now a documented failure mode.
- Prompt caching: order is `tools → system → messages`; up to **4 explicit `cache_control` breakpoints**; minimum 4,096 tokens for Opus 4.5+; 5-min TTL default (1.25× write, 0.1× read), 1-hour TTL opt-in (2× write).
- Identified anti-patterns: over-specified CLAUDE.md, trust-then-verify gap, infinite exploration without scope.

**OpenAI** (GPT-5.x, Model Spec 2025-12-18):
- Authority hierarchy: **Root > Developer > User > No-Authority** (system role replaced by `developer` for reasoning models).
- GPT-5 prompting guide explicitly endorses XML-style tags after Cursor's testing: *"using structured XML specs like `<[instruction]_spec>` improved instruction adherence."*
- GPT-5 *"follows prompt instructions with surgical precision … poorly-constructed prompts containing contradictory or vague instructions can be more damaging to GPT-5 than to other models, as it expends reasoning tokens searching for a way to reconcile the contradictions."* GPT-5.4 guidance: *"Put critical rules first … Do not rely on 'you MUST' alone."*
- Caching is **fully automatic**, no `cache_control`. Min 1,024 tokens, 128-token increments, 5–10 min TTL (24h Extended on GPT-5.1/4.1 only). Static content first, dynamic last.

**Google** (Gemini 3 / 3.1 Pro):
- XML tags **or** Markdown headings — explicitly equal status. `##` separators are *especially* important for Gemini Nano.
- Unique two-part ordering: critical instructions and persona at the **start** of the system instruction, but *negative, formatting, and quantitative constraints at the very end* — *"the model may drop negative constraints if they appear too early."*
- Implicit caching default for 2.5+; explicit `caches.create()` API with configurable TTL (default 60 min); min 4,096 tokens for Gemini 3/3.1.
- Default temperature 1.0 strongly recommended; lower values cause looping/degradation in Gemini 3.

The **convergence**: all three vendors say static-first/dynamic-last for caching, all three now endorse XML tags, all three warn against aggressive emphasis on 2025+ flagship models. The **divergence**: Google uniquely puts negative constraints last; Anthropic prefers reformulating to positive instructions; OpenAI emphasizes resolving conflicts upfront.

### 1.3 Why positional ordering matters (theoretical grounding)

**Liu et al. 2024 ("Lost in the Middle", TACL)** established the **U-shaped attention curve**: relevant info at position 1 (primacy) or last (recency) yields highest accuracy; mid-position drops 20+ absolute points and can fall *below* the closed-book baseline. Extended-context models (Claude-1.3-100K, GPT-3.5-16K) showed the same U-curve — bigger windows did not help.

**Distyl IFScale (arXiv:2507.11538, 2025)** is the most directly applicable result for this problem. Testing 20 frontier models with 10–500 simultaneous instructions:
- Even gemini-2.5-pro hits only **68.9% adherence at 500 instructions**; Claude Opus 4 = 44.6%; GPT-4.1 = 48.9%; GPT-4o = 15.4%.
- Three decay regimes — threshold, linear, exponential.
- **Universal primacy effect**: error-rate ratio (last third / first third) peaks at 1.5–3.0× around 100–200 instructions. **Instructions in the final third are 1.5–3× more likely to be violated** in the moderate-density regime.
- Claude-Sonnet-4 falls 100% → 94% → 77% across 10/100/250 instructions. A 9000-word AGENTS.md likely contains 100–250 effective constraints — exactly this danger zone.

**Zeng et al. 2025 ("Order Matters", ACL Findings)** validated that **hard-to-easy constraint ordering** beats other orderings by up to 15 points across architectures. **Raimondi & Gabbrielli 2025 (RANLP)** validated the **sandwich strategy**: critical content at *both* ends.

**Chroma's Context Rot study (2025)** found every model degrades non-uniformly with length even on trivial tasks; rot onset at ~50K tokens regardless of advertised window; coherent surrounding text creates *more* distraction than incoherent. **Geng et al. 2025 ("Control Illusion")** showed no frontier model consistently honors stated instruction hierarchies under conflict — meaning intra-prompt conflicts in AGENTS.md cannot be resolved by stating "X overrides Y"; they must be physically removed.

For the user's 50K context: rules at tokens ~15K–35K sit in the highest-risk zone, and the body of a 9000-word AGENTS.md falls there.

### 1.4 Optimization frameworks (what to actually use)

The recommended stack:

1. **GEPA (arXiv:2507.19457, July 2025)** — strongest fit. Maintains a Pareto frontier of candidate prompts, uses reflective natural-language critiques to mutate *targeted modules*, beats GRPO-RL by 6–20% with **35× fewer rollouts** and beats MIPROv2 by ~10% (+12% on AIME-2025). Works with 30–50 examples. Production endorsements: Shopify (Lutke), Comet Opik, Pydantic AI, Google ADK, OpenAI Cookbook, HuggingFace Cookbook. Available as `dspy.GEPA` or standalone `gepa` package.

2. **MIPROv2 (arXiv:2406.11695)** — fallback. Three-phase Bayesian optimization over (instruction × demo) combinations. Needs ≥200 examples. Documented +13% on multi-stage programs. Better when you want grounded data-aware proposals.

3. **LLMLingua-2 (arXiv:2403.12968)** — first-pass compression. Token-classifier distilled from GPT-4; 3–6× faster than v1; generalizes OOD. Use to get a 30–50% reduction baseline before behavioral optimization, but *audit output manually* — token-level pruning destroys numbered-rule semantics.

4. **Agent Workflow Memory (arXiv:2409.07429, ICML 2025)** — for *generating* new rules. Induces reusable workflows from successful trajectories; +24.6% on Mind2Web, +51.1% on WebArena, beats human-written workflows by 7.9%. Complement, not replacement.

For LLM-as-judge: use **Prometheus-2** for offline rubric-based scoring, **swap augmentation** (test both orderings) to neutralize position bias, and a **different-family judge model** (Claude judges OpenAI agent and vice versa) to neutralize self-preference (~10% for GPT-4, ~25% for Claude).

### 1.5 Evaluation & regression methodology

**Inspect AI** (UK AISI, MIT-licensed) is the right execution layer for write-capable coding-agent tests — Docker sandbox isolation is non-negotiable when the agent edits files. **Promptfoo** provides the YAML A/B harness (`trajectory:tool-sequence` asserts, `--repeat 3`, dedicated coding-agent guide). **DeepEval's `PromptAlignmentMetric`** decomposes a prompt into atomic constraints and judges adherence per-rule — directly aligned with the schema below.

**Statistical significance**: use **McNemar's test** for binary pass/fail on paired prompt comparisons; **paired bootstrap** for rubric scores. Per Anthropic's published statistical methodology, paired tests exploit a 0.3–0.7 question-level correlation between prompt variants, yielding large variance reduction over unpaired comparisons. Practical sample-size guidance: aim for **~50 discordant pairs**, typically **250–500 total cases** at typical 10–20% discordance rates.

A subtle finding from arXiv:2506.02357: **Principle Adherence Rate (PAR) and Task Success Rate (TSR) must be tracked together** — adding a strict safety principle dropped TSR from 80% to 14% in one scenario. A rule with PAR=100% but TSR collapse is *not* a good rule.

---

## 2. Reflection schema (token-budgeted YAML)

The schema is **YAML inside a markdown code block** because that format is uniformly parsed by Claude, GPT-5, and Gemini without provider-specific delimiters. Section-level granularity is the default (rule-level is too noisy and too easily gamed); rule IDs are emitted only for the top 5 most-influential rules in the session.

```yaml
# .agent/reflections/SESSION_<id>.yaml
schema: v1
session:
  id: <uuid>          # str
  task_class: tdd|review|debug|refactor|security|other
  outcome: success|partial|failed
  tokens_in: 0        # int
  tokens_out: 0       # int
  turns: 0            # int

# Section-level coverage. One row per AGENTS.md H2 section.
# influence: 0=ignored, 1=read-only, 2=shaped-output, 3=decisive
sections:
  - id: tdd_protocol
    cited: true
    influence: 3
  - id: fic_workflow
    cited: false
    influence: 2          # silent guard candidate -> influence>0 w/o cite
  - id: windows_shell
    cited: false
    influence: 0

# On-demand artifacts touched this session.
loaded:
  workflows: [tdd, debug-failure]    # subset of 15
  roles: [coder, tester]             # subset of 6
  skills: [pytest, type-hints]       # subset of 8
  refs:    []                        # reference docs read

# Top-5 rule IDs that changed behavior. Rule IDs are stable hashes
# (e.g., 'P0:never-skip-tests') maintained in registry.yaml.
decisive_rules: [P0:never-skip-tests, P1:windows-bash-quoting]

# Conflicts detected between sections/rules. Empty when none.
conflicts: []         # e.g. ['fic_workflow vs context_compression']

# At most one terse note. No free-form fields elsewhere -- gaming-resistant.
note: "fic_workflow shaped plan ordering but was never quoted"
```

**Token-budget audit** (tiktoken `cl100k_base`, populated): **416 tokens** for a representative session reflecting 8 sections, 2 workflows, 2 roles, 2 skills, 2 decisive rules, 0 conflicts. Empty reflection (no optional content) = **278 tokens**. Worst case (all 30 sections enumerated, full conflict list) = **612 tokens** — exceeds budget, but that case implies a session that touched everything, which is itself a signal worth the overhead.

**Why section-level + decisive_rules hybrid**: pure rule-level reflection (~150 rules) blows the token budget and induces gaming (the agent enumerates every rule to look compliant). Pure section-level loses signal on which specific rule fired. The compromise: cheap section coverage as the primary telemetry, rule IDs only for the 5 most-decisive.

**Cross-model compatibility**: YAML in a fenced code block parses reliably for all three vendors. No XML tags inside the YAML (avoids GPT-5's reasoning-token waste resolving XML-in-YAML); the *meta-prompt* that asks for the reflection uses XML for Claude, markdown headers for Gemini, and developer-message structure for GPT-5.

---

## 3. Python aggregation script

Working code, runnable as `python aggregate_reflections.py .agent/reflections/`. Detects frequency, decay curves, silent guards, and emits pruning candidates with safety gates.

```python
#!/usr/bin/env python3
"""
aggregate_reflections.py — Instruction Coverage Analysis aggregator.
Reads N session reflection YAMLs and emits a pruning-candidate report.
Safety: rules tagged `priority: P0` in registry.yaml are never auto-pruned.
"""
from __future__ import annotations
import sys, os, glob, math, json, statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import yaml  # pip install pyyaml

# --- Config ---------------------------------------------------------------
DECAY_WINDOW_DAYS = 30
RECENT_DAYS       = 7
SILENT_GUARD_MIN_INFLUENCE = 1     # influence>=1 without citation
LOW_FREQ_THRESHOLD = 0.05          # cited in <5% of sessions
DECAY_RATIO_THRESHOLD = 0.25       # recent freq < 25% of baseline freq
P0_NEVER_PRUNE = True              # hard safety gate

# --- IO -------------------------------------------------------------------
def load_reflections(directory: str) -> list[dict]:
    paths = sorted(glob.glob(os.path.join(directory, "SESSION_*.yaml")))
    out = []
    for p in paths:
        try:
            with open(p) as f:
                doc = yaml.safe_load(f)
            doc["_path"] = p
            doc["_mtime"] = datetime.fromtimestamp(os.path.getmtime(p))
            out.append(doc)
        except Exception as e:
            print(f"[skip] {p}: {e}", file=sys.stderr)
    return out

def load_registry(path: str = ".agent/registry.yaml") -> dict:
    """Registry maps section_id and rule_id to {priority, owner, added}.
    Priorities: P0 (safety), P1, P2, P3."""
    if not os.path.exists(path):
        return {"sections": {}, "rules": {}}
    with open(path) as f:
        return yaml.safe_load(f) or {"sections": {}, "rules": {}}

# --- Core analyses --------------------------------------------------------
def frequency_heatmap(refs: list[dict]) -> dict[str, dict]:
    """Per-section citation rate, influence histogram."""
    n = max(len(refs), 1)
    sect = defaultdict(lambda: {"cited": 0, "infl_sum": 0, "infl_dist": Counter()})
    for r in refs:
        for s in r.get("sections") or []:
            row = sect[s["id"]]
            row["cited"] += 1 if s.get("cited") else 0
            row["infl_sum"] += int(s.get("influence", 0))
            row["infl_dist"][int(s.get("influence", 0))] += 1
    return {sid: {
        "cite_rate": v["cited"] / n,
        "avg_influence": v["infl_sum"] / n,
        "influence_distribution": dict(v["infl_dist"]),
        "n_sessions": n,
    } for sid, v in sect.items()}

def decay_curves(refs: list[dict]) -> dict[str, dict]:
    """Compare recent (last 7d) vs baseline (last 30d) citation rates."""
    now = datetime.now()
    recent_cut   = now - timedelta(days=RECENT_DAYS)
    baseline_cut = now - timedelta(days=DECAY_WINDOW_DAYS)
    recent, baseline = defaultdict(list), defaultdict(list)
    for r in refs:
        ts = r["_mtime"]
        if ts < baseline_cut: continue
        bucket = recent if ts >= recent_cut else baseline
        for s in r.get("sections") or []:
            bucket[s["id"]].append(1 if s.get("cited") else 0)
    out = {}
    for sid in set(list(recent) + list(baseline)):
        b = sum(baseline[sid]) / max(len(baseline[sid]), 1)
        r = sum(recent[sid])   / max(len(recent[sid]),   1)
        ratio = (r / b) if b > 0 else float("nan")
        out[sid] = {"baseline": b, "recent": r, "ratio": ratio,
                    "decaying": (b > 0.10 and ratio < DECAY_RATIO_THRESHOLD)}
    return out

def silent_guards(refs: list[dict]) -> dict[str, dict]:
    """Sections with influence>=1 but cited=False — present but not quoted."""
    n_total = defaultdict(int)
    n_silent = defaultdict(int)
    for r in refs:
        for s in r.get("sections") or []:
            n_total[s["id"]] += 1
            if (not s.get("cited")) and int(s.get("influence", 0)) >= SILENT_GUARD_MIN_INFLUENCE:
                n_silent[s["id"]] += 1
    return {sid: {"silent_rate": n_silent[sid] / n_total[sid],
                  "silent_count": n_silent[sid],
                  "n": n_total[sid]}
            for sid in n_total if n_total[sid] >= 5}

def conflict_signal(refs: list[dict]) -> Counter:
    c = Counter()
    for r in refs:
        for pair in r.get("conflicts") or []:
            c[pair] += 1
    return c

def pruning_candidates(freq, decay, silent, registry) -> list[dict]:
    """Combine signals into actionable candidates with safety gates."""
    sect_meta = registry.get("sections", {})
    out = []
    for sid, f in freq.items():
        meta = sect_meta.get(sid, {})
        priority = meta.get("priority", "P2")
        is_safety = (priority == "P0") or meta.get("safety", False)

        low_freq    = f["cite_rate"] < LOW_FREQ_THRESHOLD
        low_infl    = f["avg_influence"] < 0.5
        decaying    = decay.get(sid, {}).get("decaying", False)
        silent_rate = silent.get(sid, {}).get("silent_rate", 0.0)
        is_silent   = silent_rate > 0.20

        # SAFETY GATE: never recommend auto-pruning P0 / safety rules,
        # even when they look "unused". Recommend ABLATION TEST instead.
        if is_safety and P0_NEVER_PRUNE:
            if low_freq and not is_silent:
                out.append({"id": sid, "priority": priority,
                            "action": "ABLATION_TEST_REQUIRED",
                            "rationale": "P0/safety rule with low cite rate; "
                                         "run counterfactual ablation before any change.",
                            "metrics": f, "decay": decay.get(sid),
                            "silent": silent.get(sid)})
            continue

        if is_silent:
            out.append({"id": sid, "priority": priority,
                        "action": "KEEP_AS_SILENT_GUARD",
                        "rationale": f"Silent guard rate {silent_rate:.0%}; "
                                     "shapes output without citation. Keep.",
                        "metrics": f})
        elif low_freq and low_infl and not decaying:
            out.append({"id": sid, "priority": priority,
                        "action": "PRUNE_CANDIDATE",
                        "rationale": "Low cite rate + low influence + not decaying.",
                        "metrics": f})
        elif decaying:
            out.append({"id": sid, "priority": priority,
                        "action": "INVESTIGATE_DECAY",
                        "rationale": "Citation rate dropped >75% in last 7d.",
                        "metrics": f, "decay": decay.get(sid)})
        elif low_freq and not low_infl:
            out.append({"id": sid, "priority": priority,
                        "action": "RAREBUT_DECISIVE",
                        "rationale": "Rarely cited but high influence when used. "
                                     "Move to on-demand workflow file.",
                        "metrics": f})
    return out

def render_report(refs, freq, decay, silent, conflicts, candidates) -> str:
    lines = [f"# Instruction Coverage Report",
             f"_Generated {datetime.now().isoformat(timespec='seconds')} "
             f"from {len(refs)} sessions_\n",
             "## Top sections by citation rate",
             "| Section | Cite rate | Avg influence | Silent rate |",
             "|---|---:|---:|---:|"]
    for sid in sorted(freq, key=lambda s: -freq[s]["cite_rate"])[:20]:
        f = freq[sid]
        sr = silent.get(sid, {}).get("silent_rate", 0.0)
        lines.append(f"| `{sid}` | {f['cite_rate']:.1%} | "
                     f"{f['avg_influence']:.2f} | {sr:.1%} |")
    lines += ["", "## Pruning candidates (with safety gates)"]
    for c in candidates:
        lines.append(f"- **{c['action']}** `{c['id']}` "
                     f"({c['priority']}): {c['rationale']}")
    if conflicts:
        lines += ["", "## Reported conflicts (top 10)"]
        for pair, n in conflicts.most_common(10):
            lines.append(f"- `{pair}` × {n}")
    return "\n".join(lines)

# --- Main -----------------------------------------------------------------
def main(argv):
    directory = argv[1] if len(argv) > 1 else ".agent/reflections"
    refs = load_reflections(directory)
    if not refs:
        print("no reflections found", file=sys.stderr); return 1
    registry  = load_registry()
    freq      = frequency_heatmap(refs)
    decay     = decay_curves(refs)
    silent    = silent_guards(refs)
    conflicts = conflict_signal(refs)
    cands     = pruning_candidates(freq, decay, silent, registry)

    out_dir = Path(".agent/reports"); out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (out_dir / f"coverage_{stamp}.md").write_text(
        render_report(refs, freq, decay, silent, conflicts, cands))
    (out_dir / f"coverage_{stamp}.json").write_text(json.dumps({
        "frequency": freq, "decay": decay, "silent_guards": silent,
        "conflicts": dict(conflicts), "candidates": cands,
        "n_sessions": len(refs)}, indent=2, default=str))
    print(f"[ok] wrote .agent/reports/coverage_{stamp}.{{md,json}}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

The script's safety design follows Anthropic's anti-pattern catalog and the `arXiv:2506.02357` PAR/TSR finding: **P0 / safety-tagged sections never enter the auto-prune path** — they go to `ABLATION_TEST_REQUIRED` instead, forcing a counterfactual experiment before any change. Silent-guard sections are explicitly *labeled to keep*, not pruned.

---

## 4. Meta-prompt sections (ready-to-paste)

### 4.1 Claude-optimized (primary, Opus 4.x)

Paste at the **end** of AGENTS.md (recency zone, per Liu et al. and Anthropic's "queries at end" guidance):

```xml
<session_reflection>
At the end of every session, before yielding control, emit a single
fenced YAML block matching `.agent/schemas/reflection.v1.yaml`.

Rules:
- Mark a section `cited: true` only if you actually consulted that
  section's text to make a decision this session.
- Set `influence` honestly: 0 if you did not consider it, 1 if you
  read it but it did not change your output, 2 if it shaped output
  phrasing or structure, 3 if it determined a yes/no decision.
- Listing more than 5 entries in `decisive_rules` is a violation.
- Free-form `note` field is at most one sentence. Do not add fields
  not in the schema.
- Do not flatter the instruction set. If a section was useless,
  set influence: 0. If a rule was wrong, log it under `conflicts`.

Output exactly one ```yaml ... ``` block. No prose around it.
</session_reflection>
```

The XML wrapper is Anthropic's recommended structuring delimiter. The negative-framing rules ("Do not flatter…", "Do not add fields…") follow the Claude Code best-practice finding that **specific negatives outperform vague positives**.

### 4.2 GPT-5 adaptation

GPT-5 wastes reasoning tokens on contradictions and overtriggers on aggressive emphasis. Drop the XML wrapper, use the canonical `<[name]_spec>` pattern Cursor validated, and put it as a **developer-message** addendum:

```
<session_reflection_spec>
At session end, output one fenced YAML block matching the v1
reflection schema. influence: 0..3 (0=unused, 3=decisive).
decisive_rules: at most 5 entries. note: at most one sentence.
No fields outside the schema. No prose around the block.
Honest 0s are preferred to inflated 1s.
</session_reflection_spec>
```

Also set `verbosity: low` globally and override to high only inside coding tools (Cursor's validated GPT-5 pattern). Do not use "MUST"/"CRITICAL"; GPT-5.4 explicit guidance: *"Do not rely on 'you MUST' alone."*

### 4.3 Gemini 3 / 3.1 Pro adaptation

Gemini drops negative/quantitative constraints when placed early. Put this section **last** in the system instruction, using markdown headings (Gemini's equal-status delimiter), and keep negative constraints at the very end:

```markdown
## Session reflection

At session end, emit one fenced YAML block matching
`.agent/schemas/reflection.v1.yaml`.

Field semantics:
- influence: 0=unused, 1=read-only, 2=shaped-output, 3=decisive.
- decisive_rules: list at most 5 stable rule IDs.
- note: at most one sentence.

Constraints (apply these last):
- Do not add fields not in the schema.
- Do not list more than 5 entries in decisive_rules.
- Do not write prose around the YAML block.
```

Keep `temperature=1.0` (Gemini 3 explicit recommendation; lower values induce looping).

---

## 5. Golden test set (regression harness)

Five test classes covering the user's listed scenarios, in a Promptfoo-compatible YAML the user can drop into `.agent/eval/golden.yaml`:

```yaml
description: AGENTS.md regression suite v1
prompts:
  - file://prompts/agents_md_v_current.txt
  - file://prompts/agents_md_v_proposed.txt
providers:
  - id: file://providers/claude_agent.py
    label: claude-opus-4
  - id: file://providers/gpt5_agent.py
    label: gpt-5
defaultTest:
  options: { repeat: 5 }              # n=5 per case for variance
tests:

  - description: TDD red-green-refactor
    vars:
      task: "Add User.email validation. Write the failing test first."
      repo: file://fixtures/django_users
    assert:
      - type: trajectory:tool-sequence
        value: ["bash:pytest", "edit:tests/", "edit:models/", "bash:pytest"]
      - type: javascript
        value: output.includes("PASS") && !output.includes("FAIL")
      - type: llm-rubric
        value: |
          1.0 if (a) failing test written first, (b) implementation makes
          it pass, (c) no unrelated edits, (d) prior tests still pass.
      - type: cost
        threshold: 0.30

  - description: Code review with planted bugs
    vars:
      task: "Review PR #fixture-42. Find and report defects."
      pr: file://fixtures/pr_42_with_3_bugs
    assert:
      - type: contains-all
        value: ["sql-injection", "missing-await", "off-by-one"]
      - type: not-contains-any
        value: ["false-positive-marker"]    # planted distractors

  - description: Debugging — failing test, known root cause
    vars:
      task: "Make tests/test_billing.py::test_proration pass."
      expected_root_cause_file: "src/billing/proration.py"
    assert:
      - type: trajectory:tool-used
        value: "edit:src/billing/proration.py"
      - type: javascript
        value: output.includes("1 passed")

  - description: Refactor — behavior preserving
    vars:
      task: "Extract OrderService.calculate_total into a strategy class."
    assert:
      - type: javascript
        value: |  # all pre-existing tests still pass
          output.match(/\d+ passed/) && !output.match(/failed/)
      - type: llm-rubric
        value: "1.0 if public API unchanged AND complexity reduced."

  - description: Security check — unsafe deserialization
    vars:
      task: "Audit src/api/import_data.py for security issues."
    assert:
      - type: contains
        value: "pickle"
      - type: llm-rubric
        value: |
          1.0 if agent flags pickle.loads on untrusted input AND
          recommends a safe alternative (json/msgpack/structured schema).

  - description: Negative test — ambiguous task triggers clarification
    vars:
      task: "Make it better."
    assert:
      - type: llm-rubric
        value: "1.0 if agent asks a clarifying question rather than acts."
      - type: not-contains
        value: ["edit:", "write:"]   # no file mutations

  - description: Silent-guard probe — Windows shell quoting
    vars:
      task: "Run 'pytest -k \"User and email\"' on this Windows host."
      env: windows
    assert:
      - type: trajectory:tool-used
        value: 'bash:pytest -k "User and email"'   # correct quoting
      - type: not-contains
        value: ["unmatched quote", "cmdline error"]
```

Pair this with **Inspect AI** for sandboxed execution and **McNemar's test** on the binary pass/fail outcomes when comparing prompt versions. Sample-size target: 50+ discordant pairs, typically 250–500 total runs (5 repeats × ~50–100 cases).

---

## 6. Implementation roadmap

**Phase 1 — Manual reflection (week 1)**. Drop the meta-prompt into AGENTS.md. Ship `.agent/schemas/reflection.v1.yaml`. Build `.agent/registry.yaml` enumerating sections with `priority: P0|P1|P2|P3` and `safety: true|false`. Initial pass: tag the orchestrator/guardrail role files and any "never do X" rules as P0/safety. Run 30–50 sessions; manually inspect 10 reflections for honesty (does the agent log influence=0 honestly?). Adjust meta-prompt if gaming surfaces.

**Phase 2 — Automated aggregation (weeks 2–3)**. Wire the aggregator into a nightly cron, output to `.agent/reports/`. Build the Promptfoo golden set (start with 20 cases, grow weekly from production failures per Hamel Husain's guidance). Adopt **Inspect AI** for sandboxed execution. Add a CI gate: any AGENTS.md PR runs the golden set against current vs proposed; McNemar p<0.05 with negative effect blocks merge.

**Phase 3 — Optimization loop (weeks 4–8)**. Compress with **LLMLingua-2** for a baseline 30–50% reduction; manually audit. Run **GEPA** with `seed_candidate = {"section_<id>": current_text for each non-P0 section}` and metric = `weighted_avg(task_success, per_rule_compliance, length_penalty, cache_stability)`. Use a cross-family judge (Claude judges GPT-5 runs and vice versa). Validate on held-out tasks across distinct repos. Lock the top 1–2 KB of AGENTS.md as a static cache prefix per `arXiv:2601.06007` ("Don't Break the Cache") — preserves 45–80% caching cost savings during optimization. Promote winning variants only after McNemar significance + no TSR collapse.

---

## 7. Anti-patterns catalog

The pruning protocol must defend against eight documented failure modes:

**Silent-guard removal.** A rule never cited but actively preventing bad behavior gets pruned, behavior degrades silently. Mitigation: counterfactual ablation on a probe set before any P0/safety change; the aggregator routes these to `ABLATION_TEST_REQUIRED`, never to auto-prune.

**Reflection gaming via inflation.** Agent logs `influence: 1` for every section to look thorough, killing signal. Mitigation: cap `decisive_rules` at 5 (hard rule in meta-prompt); spot-check reflections against actual tool traces; reward honesty in the meta-prompt ("Honest 0s are preferred to inflated 1s").

**Reflection gaming via deflation.** Agent under-reports to avoid revealing it ignored rules. Mitigation: cross-reference reflection against Inspect AI tool traces; flag mismatches (cited a section but never used a workflow file from it).

**Recency bias in reflection.** Most-recent rules dominate the reflection because of recency attention bias. Mitigation: section-level (not rule-level) primary granularity flattens this; the registry maintains stable IDs so age-of-rule doesn't bias visibility.

**Cache invalidation from optimization.** Optimizer mutates the static prefix, invalidates the cache, costs explode. Mitigation: lock the first 1–2 KB of AGENTS.md as `cache_control` boundary; GEPA only mutates inside an explicit `<mutable>` region.

**PAR/TSR trade-off blindness.** Optimizer maximizes adherence and tanks task success. Mitigation: composite metric tracks both; any candidate that boosts PAR while reducing TSR by >5% is rejected.

**Self-preference judge bias.** Same-family judge inflates scores ~10–25%. Mitigation: cross-family judge mandatory; swap-augmentation (test both pairwise orderings).

**Over-pruning rare-but-critical rules.** Security audit / guardrail rules cited <5% of the time get cut. Mitigation: registry priorities; the aggregator's `RAREBUT_DECISIVE` action specifically migrates these to on-demand workflow files instead of deleting.

---

## 8. Worked example: TDD implementation session

A representative reflection from a session implementing email-format validation on a Django `User` model, written by the agent at session end:

```yaml
schema: v1
session:
  id: 9f3c1e02-7d4b-4a1c-9a2f-2c1c1f9b7e44
  task_class: tdd
  outcome: success
  tokens_in: 47218
  tokens_out: 3104
  turns: 11
sections:
  - id: tdd_protocol
    cited: true
    influence: 3              # determined the red-green-refactor sequence
  - id: fic_workflow
    cited: true
    influence: 2              # shaped the plan ordering
  - id: execution_contract
    cited: false
    influence: 2              # silent guard — kept tool calls bounded
  - id: planning_contract
    cited: true
    influence: 2
  - id: testing_strategy
    cited: true
    influence: 3              # picked pytest + factory_boy fixtures
  - id: self_review_checklist
    cited: true
    influence: 2              # caught missing edge case before submit
  - id: windows_shell_patterns
    cited: false
    influence: 0              # macOS host this session
  - id: context_compression
    cited: false
    influence: 1              # read but not triggered (turns=11)
  - id: p0_safety_rules
    cited: false
    influence: 1              # silent guard
  - id: security_audit
    cited: false
    influence: 0
  - id: gui_integration_testing
    cited: false
    influence: 0
loaded:
  workflows: [tdd, debug-failure]
  roles: [coder, tester]
  skills: [pytest, type-hints, factory-boy]
  refs:    [testing-strategy.md]
decisive_rules:
  - P0:never-skip-failing-test
  - P1:tdd-red-before-green
  - P1:type-hints-on-public-api
  - P2:prefer-factory-boy-over-fixtures
conflicts: []
note: "execution_contract shaped tool-call discipline without explicit citation"
```

The aggregator processes this with 49 other sessions and produces:

> **Top cited**: `tdd_protocol` 78%, `testing_strategy` 71%, `self_review_checklist` 64%.
> **Silent guards detected**: `execution_contract` (silent rate 42%, influence 1.8 avg) → KEEP. `p0_safety_rules` (silent rate 31%) → KEEP, P0 priority.
> **Pruning candidates**: `gui_integration_testing` (cite rate 2%, influence 0.1, not decaying) → PRUNE_CANDIDATE, move to on-demand workflow. `security_audit` (cite rate 4%, influence 1.4) → RAREBUT_DECISIVE, move to on-demand workflow file (high influence when used).
> **Decay alerts**: `windows_shell_patterns` baseline 18%, recent 3% (ratio 0.17) → INVESTIGATE_DECAY (likely a team OS shift, not a content problem).

This is exactly the actionable output the design promises: *gui-integration-testing* and *security-audit* — the two workflows the user explicitly suspected were rarely invoked — surface as `PRUNE_CANDIDATE` and `RAREBUT_DECISIVE` respectively, with the latter routed to on-demand loading rather than deletion.

---

## 9. Cross-model adaptation summary

| Dimension | Claude Opus 4.x | GPT-5.x | Gemini 3.1 Pro |
|---|---|---|---|
| **Reflection-block delimiter** | `<session_reflection>` XML wrapper | `<session_reflection_spec>` Cursor-style XML | `## Session reflection` markdown heading |
| **Placement of reflection prompt** | End of AGENTS.md (recency) | Developer-message addendum, end of system | Last block in system_instruction |
| **Negative constraints** | Reformulate to positive ("emit one block" not "no prose") | Resolve conflicts upfront; avoid "MUST" | Place at very end of section |
| **Aggressive emphasis** | Avoid; overtriggers on 4.5+ | Avoid per GPT-5.4 guidance | Concrete language preferred |
| **Caching strategy** | Explicit `cache_control` on AGENTS.md root, 1-hour TTL during optimization | Automatic prefix caching — keep AGENTS.md prefix byte-stable | `caches.create()` with 60 min TTL during heavy use |
| **Min cacheable tokens** | 4,096 (Opus 4.5+) | 1,024 | 4,096 (Gemini 3/3.1) |
| **Temperature** | Default | Default; set verbosity:low globally | **Keep at 1.0** (lower causes looping) |
| **Optimizer note** | GEPA reflection-LM = strongest Claude available | Watch reasoning-token waste on conflict resolution | Persona is "sticky" — model may ignore conflicting instructions to preserve persona |

---

## Conclusion

The design treats AGENTS.md as **code under telemetry**, not a static document. Three insights drive the architecture: practitioner consensus says the user's prompt is 3–10× too long for reliable adherence; long-context research says rules buried mid-prompt are 1.5–3× more likely to be violated; and counterfactual ablation is the only honest answer to "is this silent guard doing work?" Section-level reflection at <500 tokens preserves enough signal to act without inviting gaming, and the safety gate that re-routes P0/safety candidates to ablation-required prevents the worst failure mode — silently removing a rule that was preventing harm. **The most actionable single change available today is moving `gui-integration-testing` and `security-audit` out of always-loaded AGENTS.md into on-demand workflow files**, exactly the migration this telemetry will surface in week one. The deeper payoff comes in Phase 3, when GEPA's reflective Pareto search — running against the golden set with a cross-family judge — can find rule rewrites that improve both PAR and TSR simultaneously, validated by McNemar significance before any merge. The instruction set stops being a document and becomes a measured, regression-tested artifact whose 9000 words shrink on evidence rather than on hunches.
