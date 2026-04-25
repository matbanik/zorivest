# Instruction Coverage System — Cross-Model Research Synthesis

_Synthesized from Gemini Deep Research Max, ChatGPT GPT-5, and Claude Opus 4.6 reports on 2026-04-25_

---

## Executive Summary

Three frontier models independently researched how to track, prune, and reorder a ~50K-token AI agent instruction set. Their findings converge on five core truths:

1. **The instruction set is 3-10x too long** — practitioner consensus is <300 lines for root files; the current ~900-line AGENTS.md sits in the "instruction decay zone" where adherence drops 15-25 points (IFScale, arXiv:2507.11538)
2. **Positional bias is empirically validated** — U-shaped attention curve means rules at tokens ~15K-35K are 1.5-3x more likely to be violated
3. **Section-level reflection with top-5 decisive rules** is the optimal granularity
4. **Safety rules must never be auto-pruned** — counterfactual ablation testing required
5. **Golden test set + statistical significance** is the only safe way to validate changes

---

## 1. Where All Three Models Agree

| Finding | Gemini | ChatGPT | Claude |
|---------|--------|---------|--------|
| AGENTS.md is too long | SDE research | Vendor guidance | IFScale + practitioner numbers |
| Lost-in-the-middle bias | Primacy/recency | Serial position | U-curve + sandwich strategy |
| Lazy loading beats load-everything | Dual-agent pattern | Cline 30% reduction | Claude Code ~80 pieces/session |
| Golden test set essential | MVES framework | Regression suite | Inspect AI + Promptfoo |
| Safety/P0 rules never auto-pruned | Structural partition | Non-prunable tags | ABLATION_TEST_REQUIRED gate |
| Section-level granularity | Yes | Yes | Yes + decisive_rules hybrid |
| All vendors endorse XML tags | Yes | Yes | Yes (model-specific notes) |
| Shorter is better | SDE +8.4% | "Start small" | <300 lines consensus |

## 2. Contradictions Resolved

### Format: YAML vs JSON

- **Gemini**: Markdown+YAML frontmatter (GPT-4 scores 81.2% Markdown vs 73.9% JSON — 7.3pt penalty)
- **ChatGPT**: JSON (no evidence)
- **Claude**: YAML in fenced code block (token-budget verified: 416 tokens)
- **Winner: Claude's YAML-in-fenced-codeblock** — inherits Markdown advantage, machine-parseable, cross-model compatible

### Optimization Framework: MIPROv2 vs GEPA

- **Gemini**: DSPy MIPROv2 (+13%, needs 200+ examples)
- **Claude**: GEPA (+10% over MIPROv2, **35x fewer rollouts**, works with 30-50 examples)
- **Winner: GEPA preferred**, MIPROv2 as fallback when 200+ examples available

### Statistical Validation

- **Gemini**: Golden test pass/fail (no specific test)
- **ChatGPT**: Outcome distribution monitoring
- **Claude**: McNemar's test + paired bootstrap; 50+ discordant pairs, 250-500 total runs
- **Winner: Claude's McNemar approach** — most rigorous, paired tests yield large variance reduction

## 3. Unique Contributions Worth Stealing

### From Gemini
- **Semantic Density Effect (SDE)** — ultra-dense prompts (SDE > 0.80) outperform diluted by +8.4%, +11.7% with placement
- **ACE (Agentic Context Engine)** — open-source, operates on raw traces, generates optimization suggestions with evidence
- **Meta-prompting audit** — secondary LLM scans AGENTS.md for redundancies and contradictions
- **Negative rules are fragile** — "Do NOT X" fails more than "Always Y"

### From ChatGPT
- **Cline's 30% reduction** — moved system prompt bulk into on-demand tool. Directly applicable to Zorivest skills.
- **Arize AI prompt learning** — iterative rule-file improvement boosted accuracy 10-15%
- **Symbolic references** — `Rule[N]` prefixes for minimal-token citation

### From Claude
- **Token-budget verification** — 278 empty, 416 typical, 612 worst-case. Only model that counted.
- **Silent-guard detection** — influence>=1 but cited=false. Aggregator labels KEEP_AS_SILENT_GUARD
- **PAR/TSR trade-off** — must track Principle Adherence Rate and Task Success Rate together
- **Cache-stability** — lock top 1-2KB as prefix; GEPA only mutates inside `<mutable>` region
- **Cross-family judge** — Claude judges GPT-5 and vice versa (self-preference bias: 10-25%)
- **All runnable artifacts** — aggregator, meta-prompts, golden test set

## 4. Best-of-Breed Reflection Schema

```yaml
schema: v1
session:
  id: <uuid>
  task_class: tdd|review|debug|refactor|security|other
  outcome: success|partial|failed
  tokens_in: 0
  tokens_out: 0
  turns: 0
sections:
  - id: tdd_protocol
    cited: true
    influence: 3          # 0=ignored, 1=read-only, 2=shaped-output, 3=decisive
  - id: fic_workflow
    cited: false
    influence: 2          # silent guard: influence>0 without citation
loaded:
  workflows: [tdd]
  roles: [coder, tester]
  skills: [pytest]
  refs: []
decisive_rules: [P0:never-skip-tests, P1:windows-bash-quoting]  # max 5
conflicts: []
note: "one sentence max"
```

**Budget**: 278 (empty) / 416 (typical) / 612 (worst) tokens

## 5. Merged Implementation Roadmap

| Phase | Timeline | Actions |
|-------|----------|---------|
| **1: Instrument** | Week 1 | Drop meta-prompt into AGENTS.md. Create registry.yaml with P0-P3 tags. Run 30-50 sessions. Inspect 10 reflections for honesty. |
| **2: Aggregate** | Weeks 2-3 | Wire aggregator script to nightly cron. Build Promptfoo golden set (20 cases). Add CI gate: McNemar p<0.05 blocks merge. |
| **3: Compress** | Week 4 | LLMLingua-2 for 30-50% reduction baseline. Reframe negatives as positives. Target SDE > 0.80. |
| **4: Optimize** | Weeks 5-8 | GEPA with cross-family judge. Lock cache prefix. McNemar + no TSR collapse before merge. |
| **5: Lazy-load** | Week 8+ | Move RAREBUT_DECISIVE sections to on-demand files. Compressed skill index in system prompt. |

## 6. Risk Catalog (Merged)

| Risk | Mitigation |
|------|------------|
| Silent-guard removal | Counterfactual ablation; ABLATION_TEST_REQUIRED gate |
| Reflection gaming (inflation) | Cap decisive_rules at 5; spot-check vs traces |
| Reflection gaming (deflation) | Cross-reference vs Inspect AI traces |
| Goodhart's Law | Counts as heuristic; LLM-as-judge sampling |
| Cache invalidation | Lock first 1-2KB; mutate only in `<mutable>` region |
| PAR/TSR trade-off | Composite metric; reject if TSR drops >5% |
| Self-preference judge bias | Cross-family judge; swap-augmentation |
| "Yes-Man" reviewer | Golden set includes intentionally flawed code |
| Over-pruning rare-but-critical | RAREBUT_DECISIVE migrates to on-demand, never deletes |
| Prompt injection after pruning | Golden set includes adversarial prompts; P0 pinned |

## 7. Runnable Artifacts (in Claude Report)

| Artifact | Claude Report Section |
|----------|-----------------------|
| Aggregator script | §3 `aggregate_reflections.py` |
| Meta-prompt (Claude) | §4.1 XML session_reflection |
| Meta-prompt (GPT-5) | §4.2 Developer-message spec |
| Meta-prompt (Gemini) | §4.3 Markdown heading + constraints last |
| Golden test set | §5 Promptfoo YAML, 7 test classes |
| Registry schema | §3 load_registry function |

## 8. Immediate Next Actions

1. **Create `.agent/registry.yaml`** — enumerate every AGENTS.md H2 section with priority + safety tags
2. **Paste Claude's meta-prompt** (§4.1) at end of AGENTS.md
3. **Create `.agent/schemas/reflection.v1.yaml`**
4. **Run 30 sessions** collecting reflection data
5. **Deploy aggregator** and generate first coverage report
6. **Move `gui-integration-testing` and `security-audit`** to on-demand (both flagged as candidates by multiple models)

## Appendix: Source Quality

| Report | Strengths | Weaknesses |
|--------|-----------|------------|
| **Gemini** | 60 citations; strong academic grounding; SDE formalization; observability platform comparison | MIPROv2 over GEPA; no token budget; some tangential citations |
| **ChatGPT** | Practical tool comparisons; concise; real-world patterns | Shortest; JSON without evidence; no stats methodology; no runnable code |
| **Claude** | Most implementation-complete; runnable artifacts; token-verified; strongest stats; GEPA evidence | Dense; vendor details may date quickly |
