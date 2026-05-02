---
project: "2026-05-01-market-data-expansion-doc-update"
source: "_inspiration/data-provider-api-expansion-research/market-data-expansion-doc-update-plan.md"
meus: ["MEU-182a", "MEU-182", "MEU-183", "MEU-184", "MEU-185", "MEU-186", "MEU-187", "MEU-188", "MEU-189", "MEU-190", "MEU-191", "MEU-192", "MEU-193", "MEU-194"]
status: "done"
template_version: "2.0"
type: "documentation"
---

# Implementation Plan — Market Data Expansion Documentation Update

> **Source**: [market-data-expansion-doc-update-plan.md](file:///p:/zorivest/_inspiration/data-provider-api-expansion-research/market-data-expansion-doc-update-plan.md)
> **Scope**: Documentation-only. Remove Benzinga from all layers, add 14 MEUs (MEU-182a→194, Phase 8a) to build-plan canon, create MCP rebuild skill, update mcp-audit skill/workflow.
> **Type**: Docs / Infrastructure

## Overview

This project updates Zorivest's documentation infrastructure to support the market data expansion. It does NOT implement any production code — it prepares the build plan, MEU registry, skills, and workflows for the subsequent implementation projects.

### Key Changes

1. **Benzinga removal** from 9 canonical documents `[Human-approved, 2026-05-01]`
2. **14 new MEU definitions** (MEU-182a→194) across 6 implementation layers + Layer 0 code purge
3. **New Phase 8a spec** (`08a-market-data-expansion.md`)
4. **New MCP Rebuild skill** (`.agent/skills/mcp-rebuild/SKILL.md`)
5. **MCP Audit updates** — Phases 3a/3b + consolidation score fix

### Source Basis

All requirements derive from:
- [market-data-research-synthesis.md](file:///p:/zorivest/_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md) `[Spec]`
- User decision on Benzinga exclusion `[Human-approved, 2026-05-01]`
- AGENTS.md §Boundary Input Contract `[Local Canon]`
- Plan critical review findings (5 items) `[Local Canon]`

## Verification Plan

```powershell
# Benzinga sweep
rg -i "benzinga" docs/build-plan/08-market-data.md docs/build-plan/06f-gui-settings.md docs/build-plan/06-gui.md docs/guides/policy-authoring-guide.md docs/build-plan/01a-logging.md

# Provider count consistency
rg "14 market" docs/BUILD_PLAN.md

# New Phase 8a exists
Test-Path docs/build-plan/08a-market-data-expansion.md

# MEU registry updated
rg "MEU-194" .agent/context/meu-registry.md

# Audit score fixed
rg "/ 12" .agent/skills/mcp-audit/SKILL.md .agent/workflows/mcp-audit.md

# Priority matrix count
rg "221 items" docs/build-plan/build-priority-matrix.md

# New skill exists
Test-Path .agent/skills/mcp-rebuild/SKILL.md
```

All commands should return 0 matches (for removal checks) or True (for existence checks).
