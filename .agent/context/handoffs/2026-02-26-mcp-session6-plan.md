# Session 6: PTC & Advanced

## Goal

Add Programmatic Tool Calling (PTC) routing documentation for Anthropic-class clients and a GraphQL-style composite evaluation to the analytics category. Two files modified.

---

## Proposed Changes

### [MODIFY] [05c-mcp-trade-analytics.md](docs/build-plan/05c-mcp-trade-analytics.md)

**Add two appendices** after the existing Composite Bifurcation appendix (~L720):

1. **Appendix: PTC Routing (Anthropic Clients)** — Pattern F from proposal:
   - `allowed_callers: ["code_execution"]` on all 11 read-only analytics tools
   - Agent writes Python to batch-call REST endpoints via `asyncio.gather()`
   - 37% token reduction (Anthropic-measured)
   - Only for Anthropic-class clients that support PTC; others use discrete or composite tools
   - Cross-ref to `05j` for client detection

2. **Appendix: GraphQL-Style Evaluation** — Tier 3 item 8 from proposal:
   - Evaluation of `query_analytics(query: "...")` structured query pattern
   - Pros: reduces 19→1-2 tools, works on all clients
   - Cons: higher hallucination risk on query syntax, harder to validate
   - Decision: **Deferred** — composite bifurcation (Pattern C, already implemented in Session 5) covers constrained clients; PTC covers Anthropic. GraphQL adds complexity without sufficient marginal benefit at current scale.

---

### [MODIFY] [05j-mcp-discovery.md](docs/build-plan/05j-mcp-discovery.md)

**Add PTC Routing section** at end of file (~L366):

- Section: `## PTC Routing (Anthropic Clients)`
- Documents `allowed_callers` annotation for analytics tools
- Explains client detection trigger: Anthropic-class clients get PTC-enabled tool list
- Cross-ref back to `05c` appendix for tool-level details

---

## Verification

```powershell
# 1. PTC content in 05c
$ptc05c = (Select-String 'PTC|Programmatic Tool Calling|allowed_callers|code_execution' docs\build-plan\05c-mcp-trade-analytics.md).Count
if ($ptc05c -ge 2) { Write-Output "PASS: 05c has PTC appendix ($ptc05c refs)" }
else { Write-Output "FAIL: 05c missing PTC content" }

# 2. GraphQL evaluation in 05c
$gql = (Select-String 'GraphQL|query_analytics|Deferred' docs\build-plan\05c-mcp-trade-analytics.md).Count
if ($gql -ge 2) { Write-Output "PASS: 05c has GraphQL evaluation ($gql refs)" }
else { Write-Output "FAIL: 05c missing GraphQL evaluation" }

# 3. PTC section in 05j
$ptc05j = (Select-String 'PTC|allowed_callers|Programmatic Tool Calling' docs\build-plan\05j-mcp-discovery.md).Count
if ($ptc05j -ge 2) { Write-Output "PASS: 05j has PTC section ($ptc05j refs)" }
else { Write-Output "FAIL: 05j missing PTC section" }

# 4. Cross-refs between 05c and 05j
$xref_c_to_j = (Select-String '05j-mcp-discovery' docs\build-plan\05c-mcp-trade-analytics.md).Count
$xref_j_to_c = (Select-String '05c-mcp-trade-analytics' docs\build-plan\05j-mcp-discovery.md).Count
if ($xref_c_to_j -ge 2) { Write-Output "PASS: 05c→05j cross-refs ($xref_c_to_j)" }
else { Write-Output "FAIL: 05c→05j insufficient" }
if ($xref_j_to_c -ge 1) { Write-Output "PASS: 05j→05c cross-ref" }
else { Write-Output "FAIL: 05j→05c missing" }

# 5. PTC eligibility semantics: 11 read-only analytics tools; enrich_trade_excursion excluded
$elig05c = (Select-String '11 read-only analytics tools' docs\build-plan\05c-mcp-trade-analytics.md).Count
$excl05c = (Select-String 'enrich_trade_excursion.*readOnlyHint: false' docs\build-plan\05c-mcp-trade-analytics.md).Count
$elig05j = (Select-String 'All 11 read-only analytics tools' docs\build-plan\05j-mcp-discovery.md).Count
$excl05j = (Select-String 'enrich_trade_excursion.*readOnlyHint: false' docs\build-plan\05j-mcp-discovery.md).Count
if (($elig05c -ge 1) -and ($excl05c -ge 1) -and ($elig05j -ge 1) -and ($excl05j -ge 1)) {
  Write-Output "PASS: PTC eligibility/exclusion semantics aligned (11 read-only + enrich exclusion)"
}
else { Write-Output "FAIL: PTC eligibility/exclusion semantics drift" }

# 6. Guard against stale wording and non-portable session links
$legacy12_05c = (Select-String 'all 12 analytics tools|All 12 analytics tools' docs\build-plan\05c-mcp-trade-analytics.md).Count
$legacy12_05j = (Select-String 'all 12 analytics tools|All 12 analytics tools' docs\build-plan\05j-mcp-discovery.md).Count
$agentRefs = (Select-String '\.agent/context/handoffs' docs\build-plan\05c-mcp-trade-analytics.md).Count
if (($legacy12_05c -eq 0) -and ($legacy12_05j -eq 0)) { Write-Output "PASS: no stale 'all 12 analytics tools' wording" }
else { Write-Output "FAIL: stale 'all 12 analytics tools' wording detected" }
if ($agentRefs -eq 0) { Write-Output "PASS: no .agent handoff links in 05c appendix" }
else { Write-Output "FAIL: .agent handoff links still present in 05c appendix" }
```
