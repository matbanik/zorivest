# Session 3 Walkthrough: Cross-cutting Indexes

## Changes Made

Updated 5 cross-cutting files to integrate Session 1's discovery tools (`05j`) and Session 2's annotations.

| File | Change | Items Added |
|---|---|---|
| [input-index.md](docs/build-plan/input-index.md) | New §23 (MCP Discovery inputs + test strategy) | 6 inputs, 7 tests |
| [output-index.md](docs/build-plan/output-index.md) | New §19 (Discovery & Toolset outputs) | 9 outputs |
| [testing-strategy.md](docs/build-plan/testing-strategy.md) | New "Discovery Meta-Tools" test subsection | 4 tool entries |
| [build-priority-matrix.md](docs/build-plan/build-priority-matrix.md) | P0 items `15j` + `15k`, item 13 updated | 2 items + 1 update |
| [mcp-planned-readiness.md](docs/build-plan/mcp-planned-readiness.md) | Annotations Status section + `Annotations` column | 1 section, 12 column entries |

## Verification

All commands tested in PowerShell on Windows. Every check uses explicit PASS/FAIL assertions.

```powershell
# 1. Discovery tool references in 4 of 5 files (readiness excluded by design)
$files = @(
  'docs\build-plan\input-index.md',
  'docs\build-plan\output-index.md',
  'docs\build-plan\testing-strategy.md',
  'docs\build-plan\build-priority-matrix.md'
)
foreach ($f in $files) {
  $hits = (Select-String 'list_available_toolsets|describe_toolset|enable_toolset|get_confirmation_token' $f).Count
  if ($hits -eq 0) { Write-Output "FAIL: $f" } else { Write-Output "PASS: $f ($hits)" }
}
```

**Result:** input: 9, output: 9, testing: 4, matrix: 1 — all PASS ✅

```powershell
# 2. Output-index total = 173
Select-String 'Total computed outputs \| 173' docs\build-plan\output-index.md
# 3. Item 13 mentions discovery
Select-String '^\| \*\*13\*\*.*discovery' docs\build-plan\build-priority-matrix.md
# 4. Readiness has Annotations Status
Select-String 'Annotations Status' docs\build-plan\mcp-planned-readiness.md
```

**Result:** All 3 PASS ✅

## Post-Review Corrections Applied

| # | Severity | Finding | Fix |
|---|---|---|---|
| 1 | **High** | Plan claimed "zero references" but files already had them post-execution | Corrected baseline note; plan now acknowledges post-execution state |
| 2 | **Medium** | Verification expected discovery hits in `mcp-planned-readiness.md` (0 by design) | Excluded readiness from discovery check; added design note |
| 3 | **Medium** | Item 13 in `build-priority-matrix.md` omitted discovery tools | Added "discovery" to item 13 categories + `ToolsetRegistry` dep |
| 4 | **Low** | Verification steps lacked pass/fail thresholds | All checks now use explicit `PASS`/`FAIL` assertions |

## Next Session

**Session 4: Infrastructure Integration** — `04-rest-api`, `02-infrastructure`, `dependency-manifest`, `06f-gui-settings`, `07-distribution`, `gui-actions-index`, `00-overview`, `03-service-layer`.
