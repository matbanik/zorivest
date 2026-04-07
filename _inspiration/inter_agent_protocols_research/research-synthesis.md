# Research Synthesis: Standardizing Agent Execution Artifacts

> **Date**: 2026-04-06
> **Sources**: ChatGPT (GPT-5), Claude (Opus 4.5), Gemini (2.5 Pro)
> **Scope**: Multi-agent coding system artifact design, 2025–2026

---

## Executive Summary

Three independent research reports were commissioned to evaluate best practices for standardizing file-based execution artifacts in multi-agent software engineering systems. This synthesis captures the convergent findings, divergent recommendations, and the design decisions made for Zorivest's template infrastructure.

---

## Convergent Findings (All Three Agree)

### 1. YAML Frontmatter is Essential
All three reports independently recommend structured YAML frontmatter for machine-parseable metadata. This enables automated validation, indexing, and cross-referencing without parsing document body text.

- **ChatGPT**: "Typed YAML frontmatter is the single highest-ROI change" — enables schema validation, grep-based audits, and pipeline triggers.
- **Claude**: XTrace pattern failures traced to missing structured metadata; recommends 10–15 typed fields per artifact.
- **Gemini**: Google's internal GitAgent system uses YAML frontmatter for all execution artifacts; recommends `template_version` field for forward compatibility.

### 2. Closed Enum Status Fields
All reports converge on finite, documented status values instead of free-text fields:

| Report | Recommended Statuses |
|--------|---------------------|
| ChatGPT | `draft`, `in_progress`, `complete`, `blocked` |
| Claude | `draft`, `in_progress`, `complete`, `blocked`, `deferred` |
| Gemini | `pending`, `in_progress`, `done`, `blocked` |

**Decision**: Zorivest uses `draft`, `in_progress`, `complete`, `blocked` (ChatGPT/Claude consensus).

### 3. Evidence-First Handoffs
All three reports reject prose-only completion claims:

- **ChatGPT**: "Every completion claim must cite file:line and command output."
- **Claude**: FAIL_TO_PASS evidence table is "non-negotiable for TDD workflows."
- **Gemini**: Commands Executed table with exact output prevents "phantom green" claims.

### 4. Template Versioning
All reports recommend a `template_version` field to enable forward-compatible schema evolution without breaking existing artifacts.

### 5. Repeatable Correction Sections
All reports recommend dated, append-only correction blocks rather than in-place edits to maintain audit trails.

---

## Divergent Recommendations

### Role-Based vs. Topic-Based Sections
- **ChatGPT**: Topic-based (Scope → Evidence → History) — validated by reviewing 333 actual handoffs.
- **Claude**: Role-based (Coder → Tester → Reviewer) — traditional but rarely followed in practice.
- **Gemini**: Hybrid — recommends topic-based primary with role attribution in metadata.

**Decision**: Topic-based (ChatGPT recommendation), validated against Zorivest's actual handoff corpus.

### Review Chain Strategy
- **ChatGPT**: Rolling Summary Header per recheck round — compact, bounded growth.
- **Claude**: Versioned review chains with separate files per round — clean but proliferates files.
- **Gemini**: Append-only within single file — simple but unbounded.

**Decision**: Unlimited append with Rolling Summary Header (ChatGPT + Gemini hybrid, per user preference).

### Acceptance Criteria Format
- **ChatGPT**: Compact table: `| AC | Description | Source | Test(s) | Status |`
- **Claude**: Nested YAML blocks with formal source labels.
- **Gemini**: Markdown checklist with inline references.

**Decision**: Compact table format (ChatGPT recommendation) — fits naturally in markdown, supports source tagging.

---

## Design Decisions for Zorivest

| Decision | Choice | Source |
|----------|--------|--------|
| Frontmatter format | YAML with `---` delimiters | All three (convergent) |
| Template versioning | `template_version: "2.0"` field | All three (convergent) |
| Status enum | `draft\|in_progress\|complete\|blocked` | ChatGPT + Claude |
| Section ordering | U-shaped attention: Identity → Status → Evidence | ChatGPT (research-backed) |
| Review chains | Append-only + Rolling Summary Header | ChatGPT + Gemini hybrid |
| AC table format | `\| AC \| Description \| Source \| Test(s) \| Status \|` | ChatGPT |
| Role-based sections | Dropped (topic-based instead) | ChatGPT (validated against corpus) |
| Forward enforcement | New templates only; existing artifacts untouched | Gemini recommendation |
| Schema validation | Deferred to future `validate_artifacts.py` MEU | Gemini recommendation |

---

## References

- [`chatgpt-Standardizing File-Based Execution Artifacts.md`](chatgpt-Standardizing%20File-Based%20Execution%20Artifacts%20for%20Multi-Agent%20Coding%20Systems%20in%202025%E2%80%932026.md)
- [`claude-Agentic AI artifact design.md`](claude-Agentic%20AI%20artifact%20design%20for%20multi-agent%20software%20engineering.md)
- [`gemini-Agent Artifacts Research Report.md`](gemini-Agent%20Artifacts%20Research%20Report.md)
