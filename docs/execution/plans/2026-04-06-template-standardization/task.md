---
project: 2026-04-06-template-standardization
source: docs/execution/plans/2026-04-06-template-standardization/implementation-plan.md
meus: [INFRA-TEMPLATES]
status: complete
---

# Task — Template Standardization

> **Project:** `2026-04-06-template-standardization`
> **Type:** Infrastructure/Docs (no product code, no TDD)
> **Estimate:** 12 files changed

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Write research synthesis document | orchestrator | `_inspiration/inter_agent_protocols_research/research-synthesis.md` | `Test-Path _inspiration/inter_agent_protocols_research/research-synthesis.md` | `[x]` |
| 2 | Create Handoff TEMPLATE.md v2 | coder | `.agent/context/handoffs/TEMPLATE.md` (overwrite) | `rg "^---" .agent/context/handoffs/TEMPLATE.md; rg "template_version:" .agent/context/handoffs/TEMPLATE.md` | `[x]` |
| 3 | Create REVIEW-TEMPLATE.md | coder | `.agent/context/handoffs/REVIEW-TEMPLATE.md` (new) | `Test-Path .agent/context/handoffs/REVIEW-TEMPLATE.md; rg "^---" .agent/context/handoffs/REVIEW-TEMPLATE.md` | `[x]` |
| 4 | Create PLAN-TEMPLATE.md | coder | `docs/execution/plans/PLAN-TEMPLATE.md` (new) | `Test-Path docs/execution/plans/PLAN-TEMPLATE.md; rg "^---" docs/execution/plans/PLAN-TEMPLATE.md` | `[x]` |
| 5 | Create TASK-TEMPLATE.md | coder | `docs/execution/plans/TASK-TEMPLATE.md` (new) | `Test-Path docs/execution/plans/TASK-TEMPLATE.md; rg "^---" docs/execution/plans/TASK-TEMPLATE.md` | `[x]` |
| 6 | Update Reflection TEMPLATE.md to v2 | coder | `docs/execution/reflections/TEMPLATE.md` (overwrite) | `rg "^---" docs/execution/reflections/TEMPLATE.md; rg "template_version:" docs/execution/reflections/TEMPLATE.md` | `[x]` |
| 7 | Update `meu-handoff.md` workflow | coder | Extract inline template → file reference | `rg "TEMPLATE\.md" .agent/workflows/meu-handoff.md` | `[x]` |
| 8 | Update `create-plan.md` workflow | coder | Add PLAN-TEMPLATE + TASK-TEMPLATE references | `rg "PLAN-TEMPLATE" .agent/workflows/create-plan.md` | `[x]` |
| 9 | Update `critical-review-feedback.md` workflow | coder | Add REVIEW-TEMPLATE reference | `rg "REVIEW-TEMPLATE" .agent/workflows/critical-review-feedback.md` | `[x]` |
| 10 | Update `execution-session.md` workflow | coder | Add reflection template reference | `rg "reflections/TEMPLATE" .agent/workflows/execution-session.md` | `[x]` |
| 11 | Update handoffs `README.md` | coder | Add review naming + YAML field docs | `rg "REVIEW-TEMPLATE" .agent/context/handoffs/README.md` | `[x]` |
| 12 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | 0 matches confirmed | `rg "template-standardization" docs/BUILD_PLAN.md` (expect 0 matches) | `[x]` |
| 13a | Run full Verification Plan §1–§7 | tester | All checks pass — evidence at `C:\Temp\zorivest\verify-full.txt` | `$f=@('.agent/context/handoffs/TEMPLATE.md','.agent/context/handoffs/REVIEW-TEMPLATE.md','docs/execution/plans/PLAN-TEMPLATE.md','docs/execution/plans/TASK-TEMPLATE.md','docs/execution/reflections/TEMPLATE.md'); $f | ForEach-Object {"$(if(Test-Path $_){'ok'}else{'FAIL'}) $_"}; rg "TEMPLATE\.md" .agent/workflows/meu-handoff.md; rg "PLAN-TEMPLATE\.md" .agent/workflows/create-plan.md; rg "TASK-TEMPLATE\.md" .agent/workflows/create-plan.md; rg "REVIEW-TEMPLATE\.md" .agent/workflows/critical-review-feedback.md; rg "reflections/TEMPLATE\.md" .agent/workflows/execution-session.md; rg "TEMPLATE" .agent/context/handoffs/README.md; rg "^(seq|date|project|meu|status|action_required|template_version):" .agent/context/handoffs/TEMPLATE.md; rg "^(date|review_mode|target_plan|verdict|findings_count|template_version):" .agent/context/handoffs/REVIEW-TEMPLATE.md; rg "^(project|date|source|meus|status|template_version):" docs/execution/plans/PLAN-TEMPLATE.md; rg "^(project|source|meus|status|template_version):" docs/execution/plans/TASK-TEMPLATE.md; rg "^(date|project|meus|plan_source|template_version):" docs/execution/reflections/TEMPLATE.md; rg "^## (Scope|Acceptance Criteria|Evidence|Codex Validation Report)" .agent/context/handoffs/TEMPLATE.md; rg "^## (Scope|Findings|Checklist Results)" .agent/context/handoffs/REVIEW-TEMPLATE.md; rg "^## (Goal|Proposed Changes|BUILD_PLAN.md Audit|Verification Plan)" docs/execution/plans/PLAN-TEMPLATE.md; rg "^## Task Table" docs/execution/plans/TASK-TEMPLATE.md; rg "BUILD_PLAN|handoff|reflection|metrics" docs/execution/plans/TASK-TEMPLATE.md; rg "^## (Execution Trace|Pattern Extraction|Next Session Design Rules|Efficiency Metrics)" docs/execution/reflections/TEMPLATE.md; rg "draft|in_progress|complete|blocked" .agent/context/handoffs/TEMPLATE.md; rg "approved|changes_required" .agent/context/handoffs/REVIEW-TEMPLATE.md; rg "VALIDATE_AND_APPROVE|REVIEW_CORRECTIONS|EXECUTE" .agent/context/handoffs/TEMPLATE.md; rg "template_version:" .agent/context/handoffs/TEMPLATE.md .agent/context/handoffs/REVIEW-TEMPLATE.md docs/execution/plans/PLAN-TEMPLATE.md docs/execution/plans/TASK-TEMPLATE.md docs/execution/reflections/TEMPLATE.md; python -c "import yaml,pathlib;[yaml.safe_load(pathlib.Path(f).read_text(encoding='utf-8').split('---')[1]) for f in ['.agent/context/handoffs/TEMPLATE.md','.agent/context/handoffs/REVIEW-TEMPLATE.md','docs/execution/plans/PLAN-TEMPLATE.md','docs/execution/plans/TASK-TEMPLATE.md','docs/execution/reflections/TEMPLATE.md']];print('YAML OK')"` | `[x]` |
| 13b | Smoke-check key invariants | tester | template_version 5/5, sections 4/4, YAML OK 5/5 | `rg "template_version:" .agent/context/handoffs/TEMPLATE.md .agent/context/handoffs/REVIEW-TEMPLATE.md docs/execution/plans/PLAN-TEMPLATE.md docs/execution/plans/TASK-TEMPLATE.md docs/execution/reflections/TEMPLATE.md` | `[x]` |
| 14 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-template-standardization-2026-04-06` | MCP: `pomera_notes(action="search", search_term="Zorivest-template-standardization*")` returns ≥1 result | `[x]` |
| 15 | Create handoff | reviewer | `.agent/context/handoffs/103-2026-04-06-template-standardization-infra.md` (naming exception: see implementation-plan.md §Handoff Naming Exception) | `Test-Path .agent/context/handoffs/103-2026-04-06-template-standardization-infra.md` | `[x]` |
| 16 | Create reflection | orchestrator | `docs/execution/reflections/2026-04-06-template-standardization-reflection.md` | `Test-Path docs/execution/reflections/2026-04-06-template-standardization-reflection.md` | `[ ]` |
| 17 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md | Select-Object -Last 3` | `[ ]` |
