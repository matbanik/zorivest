---
project: "{YYYY-MM-DD}-{project-slug}"
source: "docs/execution/plans/{YYYY-MM-DD}-{project-slug}/implementation-plan.md"
meus: ["{MEU-ID-1}", "{MEU-ID-2}"]
status: "in_progress"
template_version: "2.0"
---

# Task — {Project Title}

> **Project:** `{YYYY-MM-DD}-{project-slug}`
> **Type:** {Infrastructure/Docs | Domain | API | GUI | MCP}
> **Estimate:** {N files changed}

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | {first implementation task} | coder | {deliverable} | `{exact command}` | `[ ]` |
| 2 | {second implementation task} | coder | {deliverable} | `{exact command}` | `[ ]` |
| ... | ... | ... | ... | ... | ... |
| | **🔄 Re-Anchor Gate** | | | | |
| N | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation rows above are still `[ ]`, go back and complete them before proceeding. | coder | Console output confirming 0 unchecked implementation rows | `Select-String '\[ \]' docs/execution/plans/{YYYY-MM-DD}-{project-slug}/task.md` | `[ ]` |
| | **📋 Closeout Phase** | | | | |
| | ⚠️ *Closeout artifacts are institutional memory. Apply the same rigor as production code. Context fatigue at session end is the primary risk — these steps are the countermeasure.* | | | | |
| | **🔄 Re-Anchor Gate** | | | | |
| N+1 | 🔄 `view_file` this `task.md`. Count all `[ ]` rows remaining and list them. If any implementation/verification rows above are still `[ ]`, go back and complete them before proceeding to closeout. | coder | Console output confirming 0 unchecked implementation rows | `Select-String '\\[ \\]' docs/execution/plans/{YYYY-MM-DD}-{project-slug}/task.md` | `[ ]` |
| N+2 | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected; evidence of clean grep | `rg "{project-slug}" docs/BUILD_PLAN.md` (expect 0 matches) | `[ ]` |
| N+3 | Run verification plan | tester | All checks pass | `{exact command(s) from implementation-plan.md}` | `[ ]` |
| N+4 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-{slug}-{date}` | MCP: `pomera_notes(action="search", search_term="Zorivest-{slug}*")` returns ≥1 result | `[ ]` |
| | **Template + Exemplar Loading** (mandatory before writing closeout artifacts) | | | | |
| N+5 | Load templates and exemplars: `view_file` BOTH the template AND the most recent peer exemplar for each artifact. Do NOT write from memory. | orchestrator | Console evidence of template + exemplar reads | `view_file: docs/execution/reflections/TEMPLATE.md` + `view_file` most recent `*-reflection.md`. `view_file: .agent/context/handoffs/TEMPLATE.md` + `view_file` most recent `*-handoff.md`. | `[ ]` |
| N+6 | Create handoff following template structure and exemplar quality | reviewer | `.agent/context/handoffs/{date}-{slug}-handoff.md` with all 7 scored sections populated | `rg "Acceptance Criteria\|CACHE BOUNDARY\|Evidence\|Changed Files" .agent/context/handoffs/{date}-{slug}-handoff.md *> C:\Temp\zorivest\handoff-check.txt; Get-Content C:\Temp\zorivest\handoff-check.txt` | `[ ]` |
| N+7 | Create reflection following template structure and exemplar quality | orchestrator | `docs/execution/reflections/{date}-{slug}-reflection.md` with all 11 sections + metrics + YAML | `rg "Friction Log\|Pattern Extraction\|Efficiency Metrics\|Rule Adherence\|Instruction Coverage\|schema: v1" docs/execution/reflections/{filename} *> C:\Temp\zorivest\reflection-check.txt; Get-Content C:\Temp\zorivest\reflection-check.txt` | `[ ]` |
| N+8 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md *> C:\Temp\zorivest\metrics-check.txt; Get-Content C:\Temp\zorivest\metrics-check.txt \| Select-Object -Last 3` | `[ ]` |
| | **Closeout Quality Gate** | | | | |
| N+9 | Run closeout structural checks: verify reflection has all 9 structural markers, handoff has all 4 markers, metrics row exists | tester | All structural markers present (0 missing) | Run `completion-preflight` §Structural Marker Checklist + §Closeout Artifact Quality Check | `[ ]` |


### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
