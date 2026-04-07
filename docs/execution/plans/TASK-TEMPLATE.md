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
| N | Audit `docs/BUILD_PLAN.md` for stale refs | orchestrator | No changes expected; evidence of clean grep | `rg "{project-slug}" docs/BUILD_PLAN.md` (expect 0 matches) | `[ ]` |
| N+1 | Run verification plan | tester | All checks pass | `{exact command(s) from implementation-plan.md}` | `[ ]` |
| N+2 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-{slug}-{date}` | MCP: `pomera_notes(action="search", search_term="Zorivest-{slug}*")` returns ≥1 result | `[ ]` |
| N+3 | Create handoff | reviewer | `.agent/context/handoffs/{SEQ}-{date}-{slug}-bp{NN}s{X.Y}.md` | `Test-Path .agent/context/handoffs/{filename}` | `[ ]` |
| N+4 | Create reflection | orchestrator | `docs/execution/reflections/{date}-{slug}-reflection.md` | `Test-Path docs/execution/reflections/{filename}` | `[ ]` |
| N+5 | Append metrics row | orchestrator | Row appended to `docs/execution/metrics.md` | `Get-Content docs/execution/metrics.md \| Select-Object -Last 3` | `[ ]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |
