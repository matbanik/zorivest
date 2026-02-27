# Session 1: MCP Architectural Foundation

## Goal

Establish the core MCP optimization architecture in 3 files: one new, two updated. This session defines client detection, toolset grouping, meta-tools, confirmation tokens, and adaptive patterns — the foundation all subsequent sessions build on.

> [!IMPORTANT]
> **Tracker:** [Session tracker](file:///p:/zorivest/.agent/context/handoffs/2026-02-26-mcp-integration-session-tracker.md) — this is Session 1 of 6.

---

## Proposed Changes

### Discovery & Meta-Tools

#### [NEW] [05j-mcp-discovery.md](file:///p:/zorivest/docs/build-plan/05j-mcp-discovery.md)

New category file following the same structure as `05a`–`05i`. Contains:

1. **4 tool specifications** (same format as existing tool specs — Zod schema, REST proxy, Vitest):
   - `list_available_toolsets` — returns all toolset names + descriptions + tool counts + loaded status
   - `describe_toolset` — returns tool names/descriptions for a specific toolset
   - `enable_toolset` — activates a toolset for the current session (dynamic clients only)
   - `get_confirmation_token` — generates a time-limited token for destructive operations

2. **Per-tool annotation blocks** (format established here, replicated to `05x` files in Session 2):
   ```markdown
   #### Annotations
   - `readOnlyHint`: true
   - `destructiveHint`: false
   - `idempotentHint`: true
   - `toolset`: discovery
   - `alwaysLoaded`: true
   ```

3. **Vitest test specifications** for all 4 tools

> Cross-reference: REST endpoints for these tools go in `04-rest-api.md` (Session 4).

---

### Hub Infrastructure

#### [MODIFY] [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md)

Add 4 new sections after existing §5.10 (GUI Launch):

**§5.11: Toolset Configuration**
- Toolset definitions table: name, category file(s), tools included, default loaded status
- `--toolsets` CLI flag spec (GitHub-style: `--toolsets trade-analytics,diagnostics`)
- `toolset-config.json` schema (persistent toolset preferences)
- Default toolset: `core` (diagnostics + settings + discovery = 8-12 tools always loaded)

**§5.12: Adaptive Client Detection**
- Detection flowchart (Anthropic → dynamic → static, the 3-path tree from the proposal)
- `clientInfo.name` → mode mapping table
- `ZORIVEST_CLIENT_MODE` env var override
- `defer_loading` behavior for Anthropic clients
- `notifications/tools/list_changed` behavior for dynamic clients

**§5.13: Adaptive Design Patterns**
- Pattern A: Response compression — `responseFormat` session flag, detailed vs concise
- Pattern B: Tiered descriptions — rich (200-400 chars) vs minimal (50-100 chars)
- Pattern D: Server instructions — per-client guidance templates
- Pattern E: Safety confirmation — server-side 2-step gate for annotation-unaware clients
  - Cross-ref to `get_confirmation_token` tool in `05j`

> Patterns C (composites) and F (PTC) are deferred to Sessions 5 and 6.

**§5.14: Registration Flow Update**
- Updated `server.tool(...)` call pattern including annotations object
- How `withGuard()` + `withMetrics()` + annotations compose together
- Conditional registration logic based on detected client mode

**Category table update** (lines 14-25):
- Add row for `05j-mcp-discovery.md` with `discovery` category, 4 tools
- Update totals: 50→54 specified, 64→68 total

**Exit criteria update** (lines 726-741):
- Add: all tools have annotations
- Add: `--toolsets` flag correctly filters tool registration
- Add: client detection selects appropriate mode
- Add: meta-tools return accurate toolset state

---

### Tool Index

#### [MODIFY] [mcp-tool-index.md](file:///p:/zorivest/docs/build-plan/mcp-tool-index.md)

**New columns added to main table:**
- `Annotations` — compact `R`/`D`/`I` flags (ReadOnly/Destructive/Idempotent)
- `Toolset` — which toolset group the tool belongs to
- `Always Loaded` — `✅` or `—` (deferred)

**4 new tool rows:**
- `list_available_toolsets` | Specified | `discovery` | R I | Always
- `describe_toolset` | Specified | `discovery` | R I | Always
- `enable_toolset` | Specified | `discovery` | — I | Always
- `get_confirmation_token` | Specified | `discovery` | R I | Always

**New section: Toolset Definitions**
- Table mapping toolset names to categories, tool counts, and default-loaded status
- Replicates the authoritative definitions from `05-mcp-server.md §5.11`

**Category summary update:**
- Add `discovery` row: 4 specified, 0 planned, 0 future, 4 total
- Update grand totals

---

## Files NOT Changed in This Session

All other 37 build-plan files. Session 2 handles `05a`–`05i` annotation sweep, Session 3 handles indexes/testing/build-matrix, Session 4 handles REST API and infrastructure.

## Verification Plan

```bash
# New file exists
test -f docs/build-plan/05j-mcp-discovery.md

# Category table totals are consistent
rg "discovery" docs/build-plan/05-mcp-server.md
rg "discovery" docs/build-plan/mcp-tool-index.md

# No broken cross-references
rg "05j-mcp-discovery" docs/build-plan/05-mcp-server.md
rg "05j" docs/build-plan/mcp-tool-index.md

# Tool count sanity
rg -c "list_available_toolsets|describe_toolset|enable_toolset|get_confirmation_token" docs/build-plan/05j-mcp-discovery.md
# Expected: 4+ hits
```
