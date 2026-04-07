---
project: 2026-04-06-template-standardization
date: 2026-04-06
source: Strategic review of 333 handoffs + inter-agent protocol research synthesis
build_plan_sections: [infrastructure/docs — no build-plan section]
meus: [INFRA-TEMPLATES]
status: draft
---

# Template Standardization — Execution Artifact Consistency

## Goal

Establish a unified, research-backed template system for all Zorivest execution artifacts (handoffs, plans, tasks, reflections, reviews). Resolves 6 systemic consistency problems identified across 333 handoffs, 49 plans, and 44 reflections. Incorporates findings from a 3-platform deep research synthesis covering 80+ sources on agentic AI artifact design (2025–2026).

> **This is an infrastructure/docs project.** No product code changes. No TDD cycle. No build-plan section. Validation is file-existence + cross-reference integrity.

## User Review Required

> [!IMPORTANT]
> **Forward-only enforcement.** YAML frontmatter and new template structures apply to new artifacts only. Existing 333 handoffs retain their current format. No retroactive migration.

> [!IMPORTANT]
> **Template extraction.** The inline template in `meu-handoff.md` (lines 31–115) will be replaced with a file reference to `TEMPLATE.md`. The workflow retains all protocol sections — only the embedded template content is extracted.

> [!IMPORTANT]
> **Unlimited append for reviews.** Review files remain append-only (no versioned chains) per user decision. However, each recheck section now starts with a "Prior Pass Summary" table for orientation — a pattern validated by Claude's research on the U-shaped attention curve.

## Research Foundation

Synthesis of findings from three independent deep research reports:

| Source | Coverage | Key Insight Applied |
|--------|----------|---------------------|
| **ChatGPT Deep Research** | Codex artifact patterns, YAML schema validation, GitHub Docs frontmatter | Schema-validated frontmatter with `additionalProperties: false`; three-plane model (instruction/plan/trace) |
| **Claude Deep Research** | Anthropic multi-agent patterns, MetaGPT SOPs, CAID protocol, U-shaped attention | `action_required` verb field; section ordering for agent attention; 10KB per-file budget for reviews; emoji status indicators for dual-audience design |
| **Gemini Deep Research** | A2A/MCP protocols, LangGraph/CrewAI/AutoGen, gitagent standard, Kumiho memory | Naming conventions as machine-readable index; progressive disclosure; 150-200 line agent attention limit; append-only event sourcing |

### Key Convergence Points

> **Scope note:** These are research findings from the synthesized sources. This project delivers structural enforcement (YAML parse + required sections + enum documentation + template_version). Full runtime schema validation (`validate_artifacts.py` with `additionalProperties: false`) is tracked as a future MEU in the Out of Scope section.

1. **YAML frontmatter is non-negotiable** — all three sources agree on typed, schema-validated metadata headers
2. **Enum fields for machine routing** — `status`, `verdict`, `severity` must be closed enums, never free text
3. **Evidence must be structured tables** — not prose; file paths + commands + results
4. **Anti-drift requires validation tooling** — prompting harder doesn't work; schema checks do
5. **U-shaped attention curve** — critical info in first 50-100 tokens; history/detail at bottom
6. **`action_required` field** — receiving agent needs an explicit verb, not just a data dump

Full synthesis: [`_inspiration/inter_agent_protocols_research/research-synthesis.md`](file:///p:/zorivest/_inspiration/inter_agent_protocols_research/research-synthesis.md)

---

## Proposed Changes

### INFRA-TEMPLATES: Template Files + Workflow Updates

#### Phase 1 — Template Creation (5 files)

##### [OVERWRITE] [TEMPLATE.md](file:///p:/zorivest/.agent/context/handoffs/TEMPLATE.md)

MEU Handoff Template v2. Research-grounded redesign:
- **YAML frontmatter** with 13 typed fields including `action_required` verb (from Claude research on XTrace failures)
- **Section ordering** follows U-shaped attention curve: Identity → Status → Scope → AC table → Evidence → History
- **Drops role-based sections** (Coder/Tester/Reviewer Output) — agents produce content by topic, not by role (validated by reviewing 333 actual handoffs where none followed role-based structure)
- **Mandatory Evidence section** with subsections: FAIL_TO_PASS table, Commands Executed table, Quality Gate results
- **AC table** merges FIC acceptance criteria and source labels into one compact table: `| AC | Description | Source | Test(s) | Status |`
- **Codex Validation Report** section left blank with structured recheck protocol
- **Corrections Applied** as repeatable dated section
- **Deferred Items** table (optional, skip if none)

##### [NEW] [REVIEW-TEMPLATE.md](file:///p:/zorivest/.agent/context/handoffs/REVIEW-TEMPLATE.md)

Critical Review Template. Currently no template exists — reviews grow to 70KB unbounded:
- **YAML frontmatter** with review-specific fields: `review_mode`, `target_plan`, `verdict`, `findings_count`
- **Rolling Summary Header** — each recheck starts with a compact prior-pass table (from Claude's versioned chain research, adapted for unlimited append)
- **Structured Findings table**: `| # | Severity | Finding | File:Line | Recommendation | Status |`
- **Checklist Results** section (IR/DR/PR checklist pass/fail)
- **Recheck section** as repeatable dated block with its own verdict

##### [NEW] [PLAN-TEMPLATE.md](file:///p:/zorivest/docs/execution/plans/PLAN-TEMPLATE.md)

Implementation Plan Template. Based on best-performing plans + Codex's `plans.md` pattern:
- **YAML frontmatter** with project metadata: `project`, `date`, `source`, `meus`, `status`
- **Per-MEU blocks** with: Boundary Inventory, Acceptance Criteria (source-tagged), Negative Test Matrix, Files Modified
- **Spec Sufficiency Table** — source-backed resolution for under-specified behavior
- **BUILD_PLAN.md Audit** — mandatory section per create-plan.md requirements
- **Verification Plan** with exact commands

##### [NEW] [TASK-TEMPLATE.md](file:///p:/zorivest/docs/execution/plans/TASK-TEMPLATE.md)

Task Tracker Template. Standardizes the task table format:
- **YAML frontmatter** linking to plan
- **Consistent columns**: `| # | Task | Owner | Deliverable | Validation | Status |`
- **Standardized status values**: `[ ]`, `[/]`, `[x]`, `[B]` (blocked)
- **Mandatory post-MEU rows** appended to every task file (registry, BUILD_PLAN, reflection, metrics, pomera, commits)

##### [OVERWRITE] [reflections/TEMPLATE.md](file:///p:/zorivest/docs/execution/reflections/TEMPLATE.md)

Reflection Template v2:
- **Adds YAML frontmatter** (date, project, meus, plan_source)
- **Enforces naming convention**: `{YYYY-MM-DD}-{project-slug}-reflection.md`
- **Preserves** all 11 proven questions + Pattern Extraction + Design Rules + Metrics
- **Tightens** Efficiency Metrics table headers for consistency

---

#### Phase 2 — Workflow Updates (4 files, surgical edits)

##### [MODIFY] [meu-handoff.md](file:///p:/zorivest/.agent/workflows/meu-handoff.md)

- Replace inline template (lines 31–115) with file reference: `> Start from .agent/context/handoffs/TEMPLATE.md`
- Retain all protocol sections: Live Runtime Probe, Stub Quality Gate, Fix Generalization, Status Transitions
- Add note about `action_required` field semantics

##### [MODIFY] [create-plan.md](file:///p:/zorivest/.agent/workflows/create-plan.md)

- In Step 4, add template references for both `PLAN-TEMPLATE.md` and `TASK-TEMPLATE.md`
- No other structural changes

##### [MODIFY] [critical-review-feedback.md](file:///p:/zorivest/.agent/workflows/critical-review-feedback.md)

- In Step 5, add: `> Start from .agent/context/handoffs/REVIEW-TEMPLATE.md`
- Add note about Rolling Summary Header for rechecks

##### [MODIFY] [execution-session.md](file:///p:/zorivest/.agent/workflows/execution-session.md)

- In §5 (Meta-Reflection), add reference to `docs/execution/reflections/TEMPLATE.md`

---

#### Phase 3 — Documentation + Synthesis (2 files)

##### [MODIFY] [handoffs/README.md](file:///p:/zorivest/.agent/context/handoffs/README.md)

- Add critical review file naming convention
- Reference both `TEMPLATE.md` and `REVIEW-TEMPLATE.md`
- Add YAML frontmatter field documentation with enum definitions

##### [NEW] [research-synthesis.md](file:///p:/zorivest/_inspiration/inter_agent_protocols_research/research-synthesis.md)

Combined research synthesis document citing all three platform reports with convergence/divergence analysis.

---

## Out of Scope

- **Retroactive frontmatter migration** — 333 existing handoffs keep their current format
- **Artifact linter tool** (`validate_artifacts.py`) — tracked as future MEU; templates include `template_version` field to enable future validation
- **Schema hash validation** — the `template_version` field is sufficient at current scale; schema hashing (sha256 per artifact) deferred until artifact count exceeds validation tooling threshold
- **JSON sidecar files** — research suggests JSON resists agent modification better, but markdown primary is simpler for Zorivest's dual-agent scale
- **Versioned review chains** — user decided unlimited append; mitigated by Rolling Summary Header

## BUILD_PLAN.md Audit

This project does not modify any build-plan sections or product code. No `docs/BUILD_PLAN.md` updates are required. Validation:

```powershell
rg "template-standardization" docs/BUILD_PLAN.md  # Expected: 0 matches (not a build-plan MEU)
```

## Handoff Naming Exception

The standard handoff naming convention is `{SEQ}-{YYYY-MM-DD}-{slug}-bp{NN}s{X.Y}.md` per `create-plan.md:142`. This project is infrastructure/docs-only and has no numbered build-plan section, so the `-bp{NN}s{X.Y}` suffix cannot be applied.

**Exception:** The handoff will use `103-2026-04-06-template-standardization-infra.md` with the `-infra` suffix instead.

**Precedent:** `073-2026-03-16-test-rigor-audit-session.md` (existing infra handoff without `-bp` suffix).

## Verification Plan

### 1. File Existence
```powershell
$files = @(
  ".agent/context/handoffs/TEMPLATE.md",
  ".agent/context/handoffs/REVIEW-TEMPLATE.md",
  "docs/execution/plans/PLAN-TEMPLATE.md",
  "docs/execution/plans/TASK-TEMPLATE.md",
  "docs/execution/reflections/TEMPLATE.md"
)
$files | ForEach-Object { "$(if (Test-Path $_) {'✅'} else {'❌'}) $_" }
```

### 2. Cross-Reference Integrity
```powershell
# Verify workflows reference templates
rg "TEMPLATE\.md" .agent/workflows/meu-handoff.md
rg "PLAN-TEMPLATE\.md" .agent/workflows/create-plan.md
rg "TASK-TEMPLATE\.md" .agent/workflows/create-plan.md
rg "REVIEW-TEMPLATE\.md" .agent/workflows/critical-review-feedback.md
rg "reflections/TEMPLATE\.md" .agent/workflows/execution-session.md

# Verify README references both templates
rg "TEMPLATE" .agent/context/handoffs/README.md
```

### 3. YAML Frontmatter Completeness (per template)
```powershell
# Handoff TEMPLATE — required frontmatter fields
rg "^(seq|date|project|meu|status|action_required|template_version):" .agent/context/handoffs/TEMPLATE.md

# REVIEW-TEMPLATE — required frontmatter fields
rg "^(date|review_mode|target_plan|verdict|findings_count|template_version):" .agent/context/handoffs/REVIEW-TEMPLATE.md

# PLAN-TEMPLATE — required frontmatter fields
rg "^(project|date|source|meus|status|template_version):" docs/execution/plans/PLAN-TEMPLATE.md

# TASK-TEMPLATE — required frontmatter fields
rg "^(project|source|meus|status|template_version):" docs/execution/plans/TASK-TEMPLATE.md

# Reflection TEMPLATE — required frontmatter fields
rg "^(date|project|meus|plan_source|template_version):" docs/execution/reflections/TEMPLATE.md
```

### 4. Required Sections Present (structural validation)
```powershell
# Handoff TEMPLATE — mandatory sections
rg "^## (Scope|Acceptance Criteria|Evidence|Codex Validation Report)" .agent/context/handoffs/TEMPLATE.md

# REVIEW-TEMPLATE — mandatory sections
rg "^## (Scope|Findings|Checklist Results)" .agent/context/handoffs/REVIEW-TEMPLATE.md

# PLAN-TEMPLATE — mandatory sections
rg "^## (Goal|Proposed Changes|BUILD_PLAN.md Audit|Verification Plan)" docs/execution/plans/PLAN-TEMPLATE.md

# TASK-TEMPLATE — mandatory section + post-MEU rows
rg "^## Task Table" docs/execution/plans/TASK-TEMPLATE.md
rg "BUILD_PLAN|handoff|reflection|metrics" docs/execution/plans/TASK-TEMPLATE.md

# Reflection TEMPLATE — mandatory sections
rg "^## (Execution Trace|Pattern Extraction|Next Session Design Rules|Efficiency Metrics)" docs/execution/reflections/TEMPLATE.md
```

### 5. Enum Documentation
```powershell
# Verify closed enum values are documented (not just field names)
rg "draft|in_progress|complete|blocked" .agent/context/handoffs/TEMPLATE.md
rg "approved|changes_required" .agent/context/handoffs/REVIEW-TEMPLATE.md
rg "VALIDATE_AND_APPROVE|REVIEW_CORRECTIONS|EXECUTE" .agent/context/handoffs/TEMPLATE.md
```

### 6. Template Version Presence
```powershell
# Every template must have template_version field
rg "template_version:" .agent/context/handoffs/TEMPLATE.md .agent/context/handoffs/REVIEW-TEMPLATE.md docs/execution/plans/PLAN-TEMPLATE.md docs/execution/plans/TASK-TEMPLATE.md docs/execution/reflections/TEMPLATE.md
```

### 7. YAML Frontmatter Parses (well-formedness proof)
```powershell
python -c "import yaml, pathlib; files=['.agent/context/handoffs/TEMPLATE.md','.agent/context/handoffs/REVIEW-TEMPLATE.md','docs/execution/plans/PLAN-TEMPLATE.md','docs/execution/plans/TASK-TEMPLATE.md','docs/execution/reflections/TEMPLATE.md']; [yaml.safe_load(pathlib.Path(f).read_text(encoding='utf-8').split('---')[1]) for f in files]; print('All 5 templates parse valid YAML frontmatter')"
```

## Research References

- [`chatgpt-Standardizing File-Based Execution Artifacts.md`](file:///p:/zorivest/_inspiration/inter_agent_protocols_research/chatgpt-Standardizing%20File-Based%20Execution%20Artifacts%20for%20Multi-Agent%20Coding%20Systems%20in%202025%E2%80%932026.md)
- [`claude-Agentic AI artifact design.md`](file:///p:/zorivest/_inspiration/inter_agent_protocols_research/claude-Agentic%20AI%20artifact%20design%20for%20multi-agent%20software%20engineering.md)
- [`gemini-Agent Artifacts Research Report.md`](file:///p:/zorivest/_inspiration/inter_agent_protocols_research/gemini-Agent%20Artifacts%20Research%20Report.md)
