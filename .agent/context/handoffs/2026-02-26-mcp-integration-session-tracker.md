# MCP Tool Architecture — Multi-Session Integration Tracker

## Overview

Integrate MCP tool architecture optimizations from [the proposal](2026-02-26-mcp-tool-architecture-optimization-research-composite.md) into `docs/build-plan/`. Phases A-H, session-by-session. 25 files in scope, 15 untouched.

---

## Resolved Design Decisions

| # | Decision | Resolution |
|---|---|---|
| 1 | Annotation format | `#### Annotations` block with key-value pairs per tool |
| 2 | Toolset source of truth | Centralized in `05-mcp-server.md`, replicated into each `05x` file |
| 3 | `--toolsets` priority | **P0** — Cursor is broken at 64 tools |
| 4 | Composite placement | Appendix in `05c-mcp-trade-analytics.md` |
| 5 | Response format docs | "Detailed" canonical + "Concise mode omits:" notes |
| 6 | REST endpoints | In `04-rest-api.md` with cross-refs from Phase 5 files |
| 7 | Annotation depth | Per-tool blocks in each `05x` file |

---

## Session Plan

| Session | Phase(s) | Files | Scope | Status |
|---|---|---|---|---|
| **1** | B+C | `05j` (NEW), `05-mcp-server.md`, `mcp-tool-index.md` | Architectural foundation: detection, toolsets, meta-tools, discovery file, index updates | ✅ Complete |
| **2** | A | `05a`–`05i` (9 files) | Per-tool annotation blocks + toolset membership tags | ✅ Complete |
| **3** | — | `input-index`, `output-index`, `testing-strategy`, `build-priority-matrix`, `mcp-planned-readiness` | Cross-cutting indexes: new columns, new tools, test sections, P0 items | ✅ Complete |
| **4** | D+E | `04-rest-api`, `02-infrastructure`, `dependency-manifest`, `06f-gui-settings`, `07-distribution`, `gui-actions-index`, `00-overview`, `03-service-layer` | Infrastructure cross-refs: MCP-only notes, toolset wireframe, cross-reference table | ✅ Complete |
| **5** | F+G | `05a` (CRUD), `05c` (composites), `05g` (naming) | CRUD consolidation notes, composite bifurcation appendix, naming verified | ✅ Complete |
| **6** | H | `05c` (PTC), `05j` (PTC section), research doc | PTC routing appendix, GraphQL evaluation (deferred), 05j PTC section | ✅ Complete |

### Session Sizing Rationale

Sessions are sized so each produces a coherent, self-contained set of edits that can be reviewed independently. Dependencies flow left-to-right — each session depends on the previous ones being complete.

### Post-Session Handoff (Required)

After each session is completed, copy the plan and walkthrough artifacts to the handoffs directory:

```powershell
# Copy plan
Copy-Item "<artifact-dir>/implementation_plan.md" ".agent/context/handoffs/2026-02-26-mcp-session{N}-plan.md"

# Copy walkthrough
Copy-Item "<artifact-dir>/walkthrough.md" ".agent/context/handoffs/2026-02-26-mcp-session{N}-walkthrough.md"
```

**Naming convention:** `2026-02-26-mcp-session{N}-plan.md` and `2026-02-26-mcp-session{N}-walkthrough.md`

This ensures all session artifacts are preserved in the project handoffs directory for cross-session reference and auditability.

---

## What Each Session Delivers

### Session 1 — Architectural Foundation
- **New file:** `05j-mcp-discovery.md` — meta-tools, client detection, confirmation tokens
- **Updated:** `05-mcp-server.md` — new §5.11+ sections, toolset definitions, category table update
- **Updated:** `mcp-tool-index.md` — new columns, 4 new tool rows, toolset definitions table
- **Depends on:** Nothing

### Session 2 — Annotations Sweep
- **Updated:** All 9 `05x` files — per-tool `#### Annotations` blocks, toolset membership, always-loaded flags, rich/minimal description variants
- **Depends on:** Session 1 (toolset definitions, annotation format)

### Session 3 — Cross-cutting Indexes
- **Updated:** 5 index/strategy/matrix files — new columns for annotations/toolsets, 4 new tool entries, 5 new test sections, P0 build items
- **Depends on:** Sessions 1-2 (tools and annotations must exist to index them)

### Session 4 — Infrastructure Integration
- **Updated:** 8 files — REST endpoints for toolsets/confirmation-tokens, env vars, GUI settings panel, distribution artifacts, cross-refs from Phase 5
- **Depends on:** Sessions 1-3 (endpoints need schemas from Session 1, annotations from Session 2)

### Session 5 — Consolidation & Composites
- **Updated:** 3 files — CRUD merge (`manage_settings`), composite analytics tools, scheduling naming
- **Depends on:** Sessions 1-2 (annotations must exist before consolidating)

### Session 6 — PTC & Advanced
- **Updated:** 1-2 files — PTC routing for Anthropic, GraphQL evaluation appendix
- **Depends on:** All prior (PTC layers on top of composites and annotations)
