---
project: "2026-04-25-instruction-coverage-reflection"
date: "2026-04-25"
source: "non-standard — _inspiration/reflaction_enhancment-research/synthesis-instruction-coverage-system.md"
meus: ["ICR-1", "ICR-2", "ICR-3"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Instruction Coverage Reflection System

> **Project**: `2026-04-25-instruction-coverage-reflection`
> **Build Plan Section(s)**: Non-standard — agent infrastructure enhancement
> **Status**: `draft`

---

## Goal

Instrument the Zorivest agent instruction set with a **session-end reflection log** so that instruction usage data can be collected, aggregated, and used to optimize the ~50K-token instruction surface area. This is Phase 1 (Instrument) of the 5-phase roadmap from the cross-model research synthesis.

**Problem**: The current ~900-line AGENTS.md is 3–10× longer than practitioner consensus (<300 lines). Research shows instructions in the "lost-in-the-middle" zone (tokens ~15K–35K) are 1.5–3× more likely to be violated. There is no data on which instructions are actually used, which are ignored, and which are "silent guards."

**What this project delivers**:
1. A YAML reflection schema (v1) for session-end instruction usage logging
2. An instruction registry (`registry.yaml`) tagging every AGENTS.md H2 section with priority
3. A meta-prompt injected into AGENTS.md that mandates reflection at session end
4. A Python aggregation script that processes reflection logs into coverage reports
5. Updates to the reflection template to include the instruction coverage section

---

## User Review Required

> [!IMPORTANT]
> **Non-standard project**: This does not map to the build-plan matrix. It modifies agent infrastructure files (AGENTS.md, templates, schemas) rather than production code. The standard MEU gate (`validate_codebase.py`) will be replaced with targeted verification commands.

> [!IMPORTANT]
> **Meta-prompt injection into AGENTS.md**: The meta-prompt adds ~15 lines to the end of AGENTS.md (after `## Context & Docs`, in the recency zone per Liu et al.). This is the highest-impact change — it tells all agents to produce reflection logs. If this wording is wrong, every future session will produce bad data.

> [!WARNING]
> **Token budget**: The reflection schema is token-budget verified at 278 (empty) → 416 (typical) → 612 (worst case). This fits within the <500 target for typical sessions.

---

## Proposed Changes

### ICR-1: Instruction Registry

Create `.agent/schemas/registry.yaml` — a machine-readable inventory of every AGENTS.md H2 section with priority tags. H3 sub-sections inherit priority from their parent H2.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1.1 | Registry enumerates every H2 section in AGENTS.md with a unique `section_id`. Completeness validated by an automated script that: (a) extracts all H2 headings from AGENTS.md, (b) derives expected snake_case IDs, (c) loads registry IDs, and (d) fails on missing, extra, duplicate, or misnamed entries. | Research-backed (synthesis §4) | Missing section → validation script fails with specific diff; extra/duplicate/misnamed ID → validation script fails |
| AC-1.2 | Each section has `priority: P0|P1|P2|P3` and `safety: true|false` | Research-backed (synthesis §6 risk catalog) | P0 section without safety=true → schema validation error |
| AC-1.3 | P0 sections have `auto_prune: false` hard-coded | Research-backed (synthesis §6 "silent-guard removal") | — |
| AC-1.4 | Registry includes workflow, role, and skill files with `load_mode: on_demand|always` | Research-backed (synthesis §3 Gemini lazy-loading) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Section ID naming convention | Research-backed | snake_case derived from H2 heading text (synthesis §4 schema) |
| Priority assignment | Research-backed | P0 = safety/guardrail rules, P1 = quality gates, P2 = workflow/process, P3 = convenience/speed. Derived from synthesis §6 risk catalog heuristic. User reviews full registry before ICR-3 aggregation begins. |
| Workflow load_mode default | Research-backed | `on_demand` for workflows cited <5% in synthesis §5 candidates |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `.agent/schemas/registry.yaml` | new | Instruction registry with priority tags |

---

### ICR-2: Reflection Schema & Meta-Prompt

Create the YAML reflection schema and inject the meta-prompt into AGENTS.md and the reflection template.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-2.1 | `.agent/schemas/reflection.v1.yaml` defines the session reflection schema | Research-backed (synthesis §4) | — |
| AC-2.2 | Meta-prompt appended to the end of AGENTS.md (after `## Context & Docs`), in the recency zone per Liu et al. and Anthropic's "queries at end" guidance | Research-backed (synthesis §4 Claude §4.1; Claude report line 366) | — |
| AC-2.3 | Meta-prompt fits within 20 lines and is parseable by all three model families | Research-backed (synthesis §2 format resolution) | — |
| AC-2.4 | Reflection template (`docs/execution/reflections/TEMPLATE.md`) updated with instruction coverage section | Local Canon (existing template structure) | — |
| AC-2.5 | Handoff template (`TEMPLATE.md`) unchanged — reflection goes in reflection file, not handoff | Local Canon (meu-handoff.md §Target size) | — |
| AC-2.6 | `decisive_rules` capped at 5 entries per schema | Research-backed (synthesis §6 gaming mitigation) | — |
| AC-2.7 | `influence` field uses 0-3 scale: 0=ignored, 1=read-only, 2=shaped-output, 3=decisive | Research-backed (synthesis §4 schema) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Schema format | Research-backed | YAML in fenced code block (synthesis §2 — 7.3pt reasoning advantage over JSON) |
| Token budget | Research-backed | 278 empty / 416 typical / 612 worst-case (Claude report §4) |
| Schema version field | Research-backed | `schema: v1` for future migration |
| Meta-prompt placement | Research-backed | End of AGENTS.md, after `## Context & Docs` (EOF recency zone per Liu et al. and Anthropic). Safety rules stay at the top via primacy bias; the reflection prompt benefits from recency at the bottom. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `.agent/schemas/reflection.v1.yaml` | new | Schema definition with field documentation |
| `AGENTS.md` | modify | Append ~15-line meta-prompt after `## Context & Docs` section (EOF recency zone) |
| `docs/execution/reflections/TEMPLATE.md` | modify | Add `## Instruction Coverage` section after `## Efficiency Metrics` |

---

### ICR-3: Aggregation Script

Create a Python script that processes multiple reflection YAML files and generates a coverage report identifying pruning candidates.

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-3.1 | Script reads all `.yaml` files from a configurable reflections directory | Research-backed (Claude report §3) | Empty directory → graceful exit with message |
| AC-3.2 | Outputs a frequency heatmap (section_id × citation_count) | Research-backed (synthesis §5 Phase 2) | — |
| AC-3.3 | Identifies silent guards: sections with influence≥1 but cited=false | Research-backed (synthesis §3 Claude silent-guard detection) | — |
| AC-3.4 | Routes P0 sections to `KEEP_ALWAYS` regardless of frequency | Research-backed (synthesis §6 risk catalog) | P0 section with 0 citations → still KEEP_ALWAYS |
| AC-3.5 | Routes low-frequency non-P0 sections to `PRUNING_CANDIDATE` | Research-backed (synthesis §5 Phase 2) | — |
| AC-3.6 | Routes sections with influence≥2 but cited<5% to `RAREBUT_DECISIVE` | Research-backed (synthesis §3 Claude) | — |
| AC-3.7 | Loads registry.yaml for priority/safety tags | Research-backed (synthesis §4 schema) | Missing registry → error with instructions |
| AC-3.8 | Outputs JSON report to stdout or configurable output file | Research-backed (Claude report §3 aggregator) | — |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Decay curve | Research-backed | Not implemented in Phase 1 — requires 30+ sessions of data |
| Statistical validation | Research-backed | McNemar's test deferred to Phase 4 — insufficient data in Phase 1 |
| Script location | Research-backed | `tools/` directory is the canonical location for developer scripts in this monorepo (existing: `validate_codebase.py`, git-hooks). Claude report §3 places aggregator in `tools/`. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `tools/aggregate_reflections.py` | new | Aggregation script with frequency analysis and silent-guard detection |

---

## Out of Scope

- **Phase 2–5 of the roadmap** (golden test set, LLMLingua-2 compression, GEPA optimization, lazy-loading migration) — those require 30+ sessions of reflection data first
- **Production code changes** — this project modifies only agent infrastructure
- **Automated CI integration** — the aggregator runs manually in Phase 1
- **Cross-model meta-prompt variants** — Phase 1 uses a single universal meta-prompt; model-specific variants (Claude XML, GPT developer-message, Gemini markdown) deferred until data shows divergence

---

## BUILD_PLAN.md Audit

This project does not modify build-plan sections. It operates entirely in agent infrastructure (`.agent/`, `tools/`, `docs/execution/`).

```powershell
rg "instruction-coverage" docs/BUILD_PLAN.md  # Expected: 0 matches
```

---

## Verification Plan

### 1. Schema Validation
```powershell
# Verify registry.yaml is valid YAML with structural completeness check
# Extracts H2 headings from AGENTS.md, derives expected snake_case IDs,
# loads registry IDs, and fails on missing/extra/duplicate/misnamed entries
uv run python -c "
import yaml, re, sys
with open('AGENTS.md') as f:
    headings = [m.group(1) for m in re.finditer(r'^## (.+)$', f.read(), re.MULTILINE)]
expected = {re.sub(r'[^a-z0-9]+', '_', h.lower()).strip('_') for h in headings}
reg = yaml.safe_load(open('.agent/schemas/registry.yaml'))
actual = {s['section_id'] for s in reg['sections']}
if len(actual) != len(reg['sections']):
    print(f'FAIL: duplicate IDs in registry'); sys.exit(1)
missing = expected - actual
extra = actual - expected
if missing or extra:
    print(f'FAIL: missing={missing}, extra={extra}'); sys.exit(1)
print(f'OK: {len(actual)} sections, all match AGENTS.md H2 headings')
" *> C:\Temp\zorivest\registry-check.txt; Get-Content C:\Temp\zorivest\registry-check.txt
```

### 2. Reflection Schema Validation
```powershell
# Verify reflection schema is valid YAML
uv run python -c "import yaml; yaml.safe_load(open('.agent/schemas/reflection.v1.yaml')); print('schema OK')" *> C:\Temp\zorivest\schema-check.txt; Get-Content C:\Temp\zorivest\schema-check.txt
```

### 3. Meta-Prompt Presence
```powershell
# Verify meta-prompt is in AGENTS.md
rg "instruction_coverage_reflection" AGENTS.md *> C:\Temp\zorivest\metaprompt-check.txt; Get-Content C:\Temp\zorivest\metaprompt-check.txt
```

### 4. Reflection Template Updated
```powershell
# Verify new section exists in reflection template
rg "Instruction Coverage" docs/execution/reflections/TEMPLATE.md *> C:\Temp\zorivest\template-check.txt; Get-Content C:\Temp\zorivest\template-check.txt
```

### 5. Aggregator Tests (TDD)
```powershell
# Red phase: tests written, all fail (no -x so every test runs and proves red)
uv run pytest tests/unit/test_aggregate_reflections.py --tb=short *> C:\Temp\zorivest\aggregator-red.txt; Get-Content C:\Temp\zorivest\aggregator-red.txt | Select-Object -Last 20

# Green phase: implementation makes tests pass
uv run pytest tests/unit/test_aggregate_reflections.py -x --tb=short *> C:\Temp\zorivest\aggregator-green.txt; Get-Content C:\Temp\zorivest\aggregator-green.txt | Select-Object -Last 20

# Smoke: help flag
uv run python tools/aggregate_reflections.py --help *> C:\Temp\zorivest\aggregator-help.txt; Get-Content C:\Temp\zorivest\aggregator-help.txt
```

### 6. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" .agent/schemas/ tools/aggregate_reflections.py *> C:\Temp\zorivest\placeholder-check.txt; Get-Content C:\Temp\zorivest\placeholder-check.txt
```

---

## Resolved Decisions

- **Priority assignments**: Research-backed heuristic (P0 = safety/guardrail, P1 = quality gates, P2 = workflow, P3 = convenience) per synthesis §6. User reviews the full registry deliverable (ICR-1) before ICR-3 aggregation begins.
- **Reflection placement**: Instruction coverage YAML block goes in the reflection file (`docs/execution/reflections/`), not the handoff. This keeps handoffs lean per the 2,000-token target (Local Canon: meu-handoff.md §Target size).
- **Meta-prompt location**: End of AGENTS.md (EOF recency zone) per Liu et al. and Anthropic guidance (Claude report §4.1, synthesis §4).
- **Script location**: `tools/aggregate_reflections.py` per monorepo convention and Claude report §3.

---

## Research References

- [Synthesis Document](file:///p:/zorivest/_inspiration/reflaction_enhancment-research/synthesis-instruction-coverage-system.md) — cross-model research synthesis
- [Claude Deep Research](file:///p:/zorivest/_inspiration/reflaction_enhancment-research/claude-Instruction%20Coverage%20Analysis%20for%20a%2050K-Token%20Coding%20Agent.md) — runnable artifacts source
- [Gemini Deep Research](file:///p:/zorivest/_inspiration/reflaction_enhancment-research/gemin-LLM%20Instruction%20Set%20Optimization%20Research.md) — SDE formalization
- [ChatGPT Deep Research](file:///p:/zorivest/_inspiration/reflaction_enhancment-research/chatgpt-State%20of%20the%20Art.md) — practical patterns
