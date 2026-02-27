# Session 4: Infrastructure Integration

## Goal

Update 6 infrastructure and cross-reference files with discovery tool references, toolset architecture, and annotation cross-links (+ `gui-actions-index` confirmed unchanged). Discovery tools are **MCP-only** (no REST endpoints, no Python services, no GUI), so most changes are cross-reference additions rather than new specs.

---

## Proposed Changes

### [MODIFY] [00-overview.md](docs/build-plan/00-overview.md)

1. **Phase 5 row** (line 70): Add "discovery meta-tools, toolset registry" to Key Deliverables.
2. **Cross-References table** (line 83): Add row for `05j-mcp-discovery.md` and `mcp-tool-index.md`.

---

### [MODIFY] [04-rest-api.md](docs/build-plan/04-rest-api.md)

**No new REST endpoints needed** — discovery tools are MCP-only and don't call the Python backend. Add a note after the existing MCP Guard section (§4.6, ~line 590) clarifying that discovery/toolset tools operate entirely within the TypeScript MCP layer with no REST dependencies.

---

### [MODIFY] [02-infrastructure.md](docs/build-plan/02-infrastructure.md)

**No new DB models needed** — toolset state is in-memory on the MCP server, not persisted in SQLite. Add a note after the `McpGuardModel` section (~line 212) documenting that toolset registry state is MCP-server-side only (TypeScript in-memory), not a Python infrastructure concern.

---

### [MODIFY] [03-service-layer.md](docs/build-plan/03-service-layer.md)

**No new Python services** — discovery tools operate entirely in TypeScript. Add a note in the Outputs section (~line 246) noting that toolset/discovery logic lives in the MCP server (Phase 5), not the Python service layer.

---

### [MODIFY] [06f-gui-settings.md](docs/build-plan/06f-gui-settings.md)

1. **§6f.9 MCP Server Status** (line 701): Update "Registered tools: 22" wireframe to include toolset count and active toolset info from `list_available_toolsets`.
2. **Data Sources table** (line 730): Add row for toolset registry data sourced from `list_available_toolsets` MCP tool.

---

### [NO CHANGE] [07-distribution.md](docs/build-plan/07-distribution.md)

**No changes needed** — discovery tools ship as part of the existing MCP server npm package with no packaging changes. The file's pre-existing "dist-info discovery" text (L158) is unrelated to toolset architecture.

---

### [MODIFY] [dependency-manifest.md](docs/build-plan/dependency-manifest.md)

**No new dependencies** — discovery tools use existing `@modelcontextprotocol/sdk` and `zod`. Add a note under Phase 5 (line 38) that discovery meta-tools require no additional packages.

---

### [NO CHANGE] [gui-actions-index.md](docs/build-plan/gui-actions-index.md)

Discovery tools are MCP-only with no GUI triggers. The index correctly tracks only GUI actions. **No changes needed.**

---

## Verification Plan

```powershell
# 1. Discovery/toolset references in 6 modified files
# NOTE: 07-distribution.md excluded — no Session 4 content added there;
#       its pre-existing "dist-info discovery" text is unrelated.
$files = @(
  'docs\build-plan\00-overview.md',
  'docs\build-plan\04-rest-api.md',
  'docs\build-plan\02-infrastructure.md',
  'docs\build-plan\03-service-layer.md',
  'docs\build-plan\06f-gui-settings.md',
  'docs\build-plan\dependency-manifest.md'
)
foreach ($f in $files) {
  $hits = (Select-String 'toolset|discovery|05j' $f).Count
  if ($hits -eq 0) { Write-Output "FAIL: $f has 0 refs" }
  else { Write-Output "PASS: $f has $hits refs" }
}

# 2. gui-actions-index unchanged (no discovery refs expected)
$gui = (Select-String 'toolset|discovery|05j' docs\build-plan\gui-actions-index.md).Count
if ($gui -eq 0) { Write-Output "PASS: gui-actions-index correctly unchanged" }
else { Write-Output "FAIL: gui-actions-index unexpectedly modified" }

# 3. Overview cross-refs: both 05j AND mcp-tool-index present
$xref05j = (Select-String '05j-mcp-discovery' docs\build-plan\00-overview.md).Count
if ($xref05j -ge 1) { Write-Output "PASS: overview has 05j cross-ref" }
else { Write-Output "FAIL: overview missing 05j cross-ref" }
$xrefIdx = (Select-String 'mcp-tool-index' docs\build-plan\00-overview.md).Count
if ($xrefIdx -ge 1) { Write-Output "PASS: overview has mcp-tool-index cross-ref" }
else { Write-Output "FAIL: overview missing mcp-tool-index cross-ref" }
```
