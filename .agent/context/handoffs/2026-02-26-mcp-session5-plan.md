# Session 5: Consolidation & Composites

## Goal

Add CRUD consolidation notes to `05a` and `05g`, a composite bifurcation appendix to `05c`, and verify naming compliance across all 3 files. These document how constrained-client MCP implementations can merge tools — the discrete tools remain canonical.

---

## Proposed Changes

### [MODIFY] [05a-mcp-zorivest-settings.md](docs/build-plan/05a-mcp-zorivest-settings.md)

**Add CRUD Consolidation Note** after the `update_settings` tool section (~L93):

Per the proposal (L93): `get_settings`/`update_settings` → potential `manage_settings` merge for constrained clients. Add a note documenting:
- Constrained-client consolidation: `manage_settings(action: 'get'|'update', ...)` as an alternative surface for Cursor-class clients
- Discrete tools remain canonical (annotation-aware clients use them directly)
- Emergency tools (`emergency_stop`, `emergency_unlock`) are explicitly **not** merge candidates (different safety posture)

---

### [MODIFY] [05g-mcp-scheduling.md](docs/build-plan/05g-mcp-scheduling.md)

**Add CRUD Consolidation Note** after the tool definitions (~L287):

Per the proposal (L92): Symmetrical CRUD candidates `create_policy`/`list_policies`/`update_policy_schedule` could merge. Add:
- Constrained-client consolidation: `manage_policy(action: 'create'|'list'|'update_schedule', ...)` 
- `run_pipeline`, `preview_report`, `get_pipeline_history` are operational tools — not CRUD merge candidates
- Discrete tools remain canonical

---

### [MODIFY] [05c-mcp-trade-analytics.md](docs/build-plan/05c-mcp-trade-analytics.md)

**Add Composite Bifurcation Appendix** at end of file (~L667):

Per resolved design decision #4 (composite placement = appendix in `05c`). Document:
- Pattern C composite for constrained clients: single `query_trade_analytics(metric: '...', ...)` tool that dispatches to the 12 analytics endpoints
- Enum of supported metrics: `round_trips`, `mfe_mae`, `fee_breakdown`, `execution_quality`, `pfof_impact`, `expectancy`, `drawdown`, `strategy_breakdown`, `sqn`, `cost_of_free`
- Trade CRUD (`create_trade`, `list_trades`) and screenshot tools stay separate (different toolset posture)
- Cross-ref to Pattern F (PTC routing) for Anthropic-class clients as alternative
- Note: composite is generated from discrete tool specs (single source of truth)

---

### Naming Compliance

All 3 files already use underscore-only naming (verified). No changes needed.

---

## Verification Plan

```powershell
# 1. CRUD consolidation notes present in 05a and 05g
$crud05a = (Select-String 'manage_settings|CRUD.*consolidat|constrained.client' docs\build-plan\05a-mcp-zorivest-settings.md).Count
if ($crud05a -ge 1) { Write-Output "PASS: 05a has CRUD consolidation note" }
else { Write-Output "FAIL: 05a missing CRUD consolidation" }

$crud05g = (Select-String 'manage_policy|CRUD.*consolidat|constrained.client' docs\build-plan\05g-mcp-scheduling.md).Count
if ($crud05g -ge 1) { Write-Output "PASS: 05g has CRUD consolidation note" }
else { Write-Output "FAIL: 05g missing CRUD consolidation" }

# 2. Composite appendix in 05c
$comp = (Select-String 'Composite|bifurcat|query_trade_analytics|constrained.client' docs\build-plan\05c-mcp-trade-analytics.md).Count
if ($comp -ge 2) { Write-Output "PASS: 05c has composite appendix ($comp refs)" }
else { Write-Output "FAIL: 05c missing composite appendix" }

# 3. Naming compliance (no dots/hyphens in tool names)
foreach ($f in @('05a-mcp-zorivest-settings.md','05c-mcp-trade-analytics.md','05g-mcp-scheduling.md')) {
  $bad = (Select-String "server\.tool\(\s*'" "docs\build-plan\$f" | Where-Object { $_.Line -match "'[^']*[\.\-][^']*'" }).Count
  if ($bad -eq 0) { Write-Output "PASS: $f naming compliant" }
  else { Write-Output "FAIL: $f has $bad non-compliant names" }
}

# 4. Semantic: CRUD notes reference only canonical tool names
$badName05g = (Select-String 'get_run_history' docs\build-plan\05g-mcp-scheduling.md).Count
if ($badName05g -eq 0) { Write-Output "PASS: 05g uses canonical tool names" }
else { Write-Output "FAIL: 05g references non-existent get_run_history" }

$badName05c = (Select-String 'record_trade' docs\build-plan\05c-mcp-trade-analytics.md).Count
if ($badName05c -eq 0) { Write-Output "PASS: 05c uses canonical tool names" }
else { Write-Output "FAIL: 05c references non-existent record_trade" }

# 5. Semantic: composite metric count matches claim
$enumLines = Get-Content docs\build-plan\05c-mcp-trade-analytics.md | Select-String "'[a-z_]+'" | Where-Object { $_.LineNumber -ge 685 -and $_.LineNumber -le 695 }
$metricCount = ($enumLines | ForEach-Object { [regex]::Matches($_.Line, "'([a-z_]+)'") } | Measure-Object).Count
$claimedCount = ((Select-String '(\d+) analytics endpoints' docs\build-plan\05c-mcp-trade-analytics.md).Matches[0].Groups[1].Value)
if ($metricCount -eq [int]$claimedCount) { Write-Output "PASS: metric count ($metricCount) matches claim ($claimedCount)" }
else { Write-Output "FAIL: metric count ($metricCount) != claim ($claimedCount)" }
```
