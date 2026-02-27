# Session 3: Cross-cutting Indexes

## Goal

Update 5 cross-cutting index/strategy files to reflect Session 1's discovery tools (`05j`) and Session 2's annotation architecture.

> [!NOTE]
> **Baseline context:** This plan captures intended Session 3 deltas. Current repository state may already include some `05j`/discovery/toolset references from later session merges; validate against live files before reuse.

---

## Proposed Changes

### [MODIFY] [input-index.md](docs/build-plan/input-index.md)

**Add § 23: MCP Discovery & Toolset Management** after §22 (Service Daemon Controls).

4 discovery tools have inputs:
- `describe_toolset` → `toolset_name` (string)
- `enable_toolset` → `toolset_name` (string), `enable` (bool)
- `get_confirmation_token` → `tool_name` (string), `parameters` (object)
- `list_available_toolsets` → no inputs (parameterless)

**Update Summary Statistics**: increment counts for new inputs + feature group, add `05j` to files referenced.

---

### [MODIFY] [output-index.md](docs/build-plan/output-index.md)

**Add § 19: MCP Discovery & Toolset Outputs** after §18 (Service Daemon).

Output rows for all 4 discovery tools:
- `list_available_toolsets` → toolset array with name, description, enabled, tool_count
- `describe_toolset` → tool list with annotations per tool
- `enable_toolset` → confirmation with enabled state
- `get_confirmation_token` → token string for destructive ops

**Update Summary Statistics**: increment total to 173 (was 164, +9 discovery outputs).

---

### [MODIFY] [testing-strategy.md](docs/build-plan/testing-strategy.md)

**Add "TypeScript MCP Tests (Discovery Meta-Tools)" subsection.** 4 entries:
- `list_available_toolsets` — returns full registry
- `describe_toolset` — returns tool details with annotations
- `enable_toolset` — toggles toolset, blocked when locked
- `get_confirmation_token` — server-side token generation + refresh

---

### [MODIFY] [build-priority-matrix.md](docs/build-plan/build-priority-matrix.md)

**Add 2 new P0 items** after item 15i:
- `15j` — Discovery meta-tools — Vitest
- `15k` — `ToolsetRegistry` module + adaptive client detection — Vitest

**Update item 13 description** to mention discovery tools alongside existing categories.

---

### [MODIFY] [mcp-planned-readiness.md](docs/build-plan/mcp-planned-readiness.md)

**Add Annotations Status section** + `Annotations` column in summary table. All 12 Planned tools have annotations (from Session 2).

> This file does not gain discovery tool-name references by design — it tracks Planned → Specified readiness for the 12 Planned tools, not discovery meta-tools (which are already Specified in `05j`).

---

## Verification Plan

```powershell
# 1. Discovery tool references in 4/5 files (readiness excluded by design — see note above)
$files = @(
  'docs\build-plan\input-index.md',
  'docs\build-plan\output-index.md',
  'docs\build-plan\testing-strategy.md',
  'docs\build-plan\build-priority-matrix.md'
)
foreach ($f in $files) {
  $hits = (Select-String 'list_available_toolsets|describe_toolset|enable_toolset|get_confirmation_token' $f).Count
  if ($hits -eq 0) { Write-Output "FAIL: $f has 0 discovery tool refs" }
  else { Write-Output "PASS: $f has $hits discovery tool refs" }
}

# 2. 05j references (expected: ≥1 each in 4 files)
foreach ($f in $files) {
  $c = (Select-String '05j' $f).Count
  if ($c -eq 0) { Write-Output "FAIL: $f has 0 05j refs" }
  else { Write-Output "PASS: $f has $c 05j refs" }
}

# 3. Output-index total = 173 (was 164, added 9 discovery outputs)
$outMatch = (Select-String 'Total computed outputs \| 173' docs\build-plan\output-index.md).Count
if ($outMatch -eq 1) { Write-Output "PASS: output-index total = 173" }
else { Write-Output "FAIL: output-index total != 173" }

# 4. Item 13 mentions discovery
$item13 = Select-String '^\| \*\*13\*\*.*discovery' docs\build-plan\build-priority-matrix.md
if ($item13) { Write-Output "PASS: item 13 mentions discovery" }
else { Write-Output "FAIL: item 13 missing discovery mention" }

# 5. mcp-planned-readiness.md has Annotations Status section
$annot = (Select-String 'Annotations Status' docs\build-plan\mcp-planned-readiness.md).Count
if ($annot -ge 1) { Write-Output "PASS: readiness has Annotations Status" }
else { Write-Output "FAIL: readiness missing Annotations Status" }
```
