# MCP Tool Architecture — Build Plan Implementation Brainstorm

## Task

- **Date:** 2026-02-26
- **Task slug:** mcp-build-plan-implementation
- **Owner role:** orchestrator
- **Scope:** Map the MCP tool architecture proposal onto all 40 build-plan files
- **Status:** Brainstorm only — no planning action taken

## Source

Derived from [MCP Tool Architecture Optimization Proposal](2026-02-26-mcp-tool-architecture-optimization-research-composite.md) via sequential thinking analysis.

---

## Impact Summary

| Impact Level | File Count | Description |
|---|---|---|
| **New file** | 1 | `05j-mcp-discovery.md` |
| **Heavy modification** | 5 | Hub, analytics, index, testing, build matrix |
| **Moderate modification** | 12 | All 9 category files + 3 indexes |
| **Light modification** | 7 | Infrastructure, GUI settings, REST API, distribution |
| **Untouched** | 15 | Domain layer, logging, backup, most GUI tabs, market data engine, scheduling engine |
| **Total** | **40** | **25 files in scope** |

---

## Complete File Impact Map

### 🔴 Heavy Modifications (New sections / structural changes)

| File | What Changes |
|---|---|
| `05-mcp-server.md` | New §5.X: Client Detection & Adaptive Mode Selection. New: toolset grouping config, server instructions section, response format negotiation. Updated: MCP registration flow to include annotations. |
| `05j-mcp-discovery.md` (**NEW**) | 3 meta-tools (`list_available_toolsets`, `describe_toolset`, `enable_toolset`). `get_confirmation_token` tool for safety gate. Detection logic specification. `defer_loading` integration. |
| `05c-mcp-trade-analytics.md` | New: Composite bifurcation appendix (3-4 composite tools for constrained mode). All 19 tools get annotation blocks. PTC routing section (`allowed_callers`). Rich vs minimal description variants. |
| `mcp-tool-index.md` | New columns: `annotations`, `toolset`, `always-loaded`, `composite-mapping`. 4 new tool rows (3 meta + confirmation_token). Updated category summary with active/deferred counts. Toolset definitions table. |
| `testing-strategy.md` | 5 new test sections: client detection mocks, toolset grouping validation, response compression parity, safety confirmation flow, composite↔discrete tool parity. |
| `build-priority-matrix.md` | New build items: annotations sweep, toolset grouping, adaptive detection, meta-tools, safety confirmation. Dependency updates. Priority placement (`--toolsets` flag arguably P0 given Cursor breakage). |

### 🟡 Moderate Modifications (Annotations + toolset membership)

| File | What Changes |
|---|---|
| `05a` through `05i` (9 files) | Every tool gets: annotation block (`readOnlyHint`, `destructiveHint`, `idempotentHint`), toolset membership tag, `alwaysLoaded` flag, rich/minimal description variants. `05a` also gets CRUD consolidation (`manage_settings`). |
| `input-index.md` | New entries for 4 new tools. Updated entries for consolidated `manage_settings`. Composite tool input schemas. |
| `output-index.md` | New entries for 4 new tools. "Concise mode omits:" notes on existing entries (avoids duplicating every output). |
| `04-rest-api.md` | New: `/api/v1/toolsets` endpoint (list, describe). New: `/api/v1/confirmation-tokens` endpoint (generate, validate). Optional: `?response_format=concise` query param on existing endpoints. |
| `mcp-planned-readiness.md` | Meta-tools and confirmation_token added to readiness table. Composites tracked. |

### 🟢 Light Modifications (cross-references, minor additions)

| File | What Changes |
|---|---|
| `00-overview.md` | Phase 5 summary updated to mention adaptive tool surfacing |
| `02-infrastructure.md` | `ZORIVEST_CLIENT_MODE` env var documented. Toolset config file reference. |
| `03-service-layer.md` | Mention `ToolsetService` / `ClientCapabilityService` |
| `06f-gui-settings.md` | New: MCP Toolset Configuration panel (select active toolsets, client mode override) |
| `07-distribution.md` | Build artifacts include toolset-config.json |
| `dependency-manifest.md` | Any new runtime dependencies |
| `gui-actions-index.md` | New meta-tool GUI actions |

### ⚪ Untouched (15 files)

`01-domain-layer.md`, `01a-logging.md`, `02a-backup-restore.md`, `06-gui.md`, `06a`–`06e`, `06g`–`06h`, `08-market-data.md`, `09-scheduling.md`, `10-service-daemon.md`, `image-architecture.md`, `domain-model-reference.md`

---

## Recommended Session Sequence

| Session | Nickname | Files | Effort | Dependency |
|---|---|---|---|---|
| **1** | Architectural Foundation | `05j` (NEW), `05-mcp-server.md`, `mcp-tool-index.md` | Medium | None |
| **2** | Annotations Sweep | `05a`–`05i` (9 files) | Low per file, bulk | Session 1 |
| **3** | Cross-cutting Indexes | `input-index`, `output-index`, `testing-strategy`, `build-priority-matrix`, `mcp-planned-readiness` | Medium | Sessions 1-2 |
| **4** | Infrastructure Integration | `04-rest-api`, `02-infrastructure`, `dependency-manifest`, `06f-gui-settings`, `07-distribution`, `gui-actions-index`, `00-overview`, `03-service-layer` | Low per file | Sessions 1-3 |
| **5** | Consolidation & Composites | `05a` (CRUD), `05c` (composites), `05g` (naming) | Medium | Sessions 1-2 |
| **6** | PTC & Advanced | `05c` (PTC), GraphQL prototype | High | All prior |

---

## Design Decisions to Resolve Before Starting

| # | Decision | Recommendation | Why |
|---|---|---|---|
| 1 | Annotation format in markdown | Standardized `#### Annotations` block with key-value pairs | Greppable, translates directly to MCP SDK `annotations` object |
| 2 | Toolset source of truth | Centralized definition in `05-mcp-server.md`, replicated into each `05x` file | Single authoritative source; category files get local context |
| 3 | `--toolsets` flag build priority | **P0** (not P1) | Cursor is broken today at 64 tools. Minimum fix. |
| 4 | Composite tool placement | Appendix section in `05c-mcp-trade-analytics.md` | Views into the same category, not a new category |
| 5 | Response format in output-index | Document "detailed" as canonical; add "Concise mode omits:" notes | Avoids doubling every output entry |
