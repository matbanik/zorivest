---
project: "2026-05-01-market-data-expansion-doc-update"
source: "docs/execution/plans/2026-05-01-market-data-expansion-doc-update/implementation-plan.md"
meus: ["MEU-182a", "MEU-182", "MEU-183", "MEU-184", "MEU-185", "MEU-186", "MEU-187", "MEU-188", "MEU-189", "MEU-190", "MEU-191", "MEU-192", "MEU-193", "MEU-194"]
status: "done"
template_version: "2.0"
---

# Task — Market Data Expansion Documentation Update

> **Project:** `2026-05-01-market-data-expansion-doc-update`
> **Type:** Docs / Infrastructure
> **Estimate:** 11 files changed, 2 files created

## Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|------|-------|-------------|------------|--------|
| 1 | Remove Benzinga from `market-data-research-synthesis.md` | coder | Updated tables with Benzinga column removed | `rg -i benzinga _inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md` → 0 matches | `[x]` |
| 2 | Remove Benzinga from `08-market-data.md` + update counts 14→13 | coder | Updated spec with 13 providers | `rg -i benzinga docs/build-plan/08-market-data.md` → 0 matches | `[x]` |
| 3 | Remove Benzinga from `06f-gui-settings.md`, `06-gui.md`, `policy-authoring-guide.md`, `01a-logging.md` | coder | Updated downstream refs | `rg -i benzinga docs/build-plan/06f-gui-settings.md docs/build-plan/06-gui.md docs/guides/policy-authoring-guide.md docs/build-plan/01a-logging.md` → 0 matches | `[x]` |
| 4 | Update `BUILD_PLAN.md` provider counts + `meu-registry.md` MEU-59 | coder | Consistent 13-provider count | `rg "14 market" docs/BUILD_PLAN.md` → 0 matches | `[x]` |
| 5 | Create `08a-market-data-expansion.md` | coder | New Phase 8a spec | `Test-Path docs/build-plan/08a-market-data-expansion.md` → True | `[x]` |
| 6 | Update `build-priority-matrix.md` — add P1.5a + fix header count | coder | 14 new items + "235 items" header | `rg "221 items" docs/build-plan/build-priority-matrix.md` → 0 matches | `[x]` |
| 7 | Update `BUILD_PLAN.md` — add Phase 8a row + 13 MEU entries | coder | Phase 8a visible in index | `rg "Phase 8a" docs/BUILD_PLAN.md` → ≥1 match | `[x]` |
| 8 | Update `meu-registry.md` — add MEU-182a→194 | coder | 14 new entries | `rg "MEU-194" .agent/context/meu-registry.md` → ≥1 match | `[x]` |
| 9 | Create `.agent/skills/mcp-rebuild/SKILL.md` | coder | New skill file | `Test-Path .agent/skills/mcp-rebuild/SKILL.md` → True | `[x]` |
| 10 | Update `.agent/skills/mcp-audit/SKILL.md` — add Phases 3a/3b + fix `/ 12` → `/ 13` | coder | Updated audit skill | `rg "/ 12" .agent/skills/mcp-audit/SKILL.md` → 0 matches AND `rg "Phase 3a" .agent/skills/mcp-audit/SKILL.md` → ≥1 match | `[x]`^1^ |
| 11 | Update `.agent/workflows/mcp-audit.md` — add Steps 4a/4b + fix `/ 12` → `/ 13` | coder | Updated audit workflow | `rg "/ 12" .agent/workflows/mcp-audit.md` → 0 matches AND `rg "Step 4a" .agent/workflows/mcp-audit.md` → ≥1 match | `[x]`^1^ |
| 12 | Cross-doc sweep: verify no stale Benzinga/count refs remain | tester | Clean `rg` output | `rg -i "benzinga" docs .agent` → only historical refs in `docs/execution/plans/` | `[x]` |
| 13 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-market-data-expansion-doc-2026-05-01` | MCP: `pomera_notes(action="search", search_term="market-data-expansion*")` → ≥1 | `[x]` |
| 14 | Create handoff | reviewer | `.agent/context/handoffs/` updated | `Test-Path` → True | `[x]` |

| 15 | Register MEU-182a `benzinga-code-purge` (Layer 0) in 08a spec, matrix, BUILD_PLAN, registry | coder | Item 30.0 added, counts updated (235/249/14) | `rg "MEU-182a" docs/build-plan/08a-market-data-expansion.md .agent/context/meu-registry.md docs/BUILD_PLAN.md docs/build-plan/build-priority-matrix.md` → ≥4 matches | `[x]` |

### Status Legend

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | Complete |
| `[B]` | Blocked (must link follow-up) |

> ^1^ **Plan-correction artifact**: The `/ 12 → / 13` denominator change in `.agent/skills/mcp-audit/SKILL.md` and `.agent/workflows/mcp-audit.md` was applied during the `/plan-corrections` workflow as a prerequisite fix. The Phase 3a/3b and Steps 4a/4b content deliverables were completed during execution and are now `[x]`.
