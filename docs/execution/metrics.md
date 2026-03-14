# Execution Efficiency Metrics

> Append a row after each session's meta-reflection. Track trends to calibrate prompts.

## Session Metrics

| Date | MEU(s) | Tool Calls | Time to First Green | Tests Added | Codex Findings | Handoff Score | Rule Adherence | Prompt→Commit (min) | Notes |
|------|--------|------------|---------------------|-------------|---------------|---------------|----------------|---------------------|-------|
| 2026-03-06 | MEU-1 | ~50 | ~8 min | 9 | 0 (approved) | 7/7 | 100% | ~15 min | Pilot — bootstrap + TDD validated |
| 2026-03-07 | MEU-2 | ~40 | ~3 min | 17 | 0 (approved) | 7/7 | 100% | ~10 min | Pure enums — fastest MEU type |
| 2026-03-07 | MEU-3/4/5 | ~60 | ~5 min | 58 | — (pending review) | 7/7 | 90% | ~30 min | 3-MEU project: entities + VOs + ports |
| 2026-03-07 | MEU-9/10/11 | ~100 | ~5 min | 55 | 0 (approved) | 7/7 | 90% | ~60 min | 3-MEU project: portfolio balance + display mode + account review |
| 2026-03-07 | MEU-2A/3A/1A | ~80 | ~3 min | 57 | 3 (resolved) | 9/9 | 80% | ~45 min | 3-MEU logging infra: filters + redaction + manager. Codex caught missing exports + narrow gate scope |
| 2026-03-08 | MEU-20/21/22 | ~120 | ~5 min | 51 | 2 High + 2 Medium (resolved) | 7/7 | 90% | ~90 min | 3-MEU backup-recovery-config-image: restore/repair, config export, image processing. Codex caught validate_import contract drift + missing repair test |
| 2026-03-08 | MEU-23/24/25/26 | ~150 | ~6 min | 64 | 1 Crit + 3 High + 2 Med (resolved) | 7/7 | 85% | ~120 min | 4-MEU REST API foundation: app factory, trade/account/auth CRUD, 2 correction passes. Codex caught non-canonical tags, DI stub drift, missing image upload |
| 2026-03-09 | MEU-27/28/29/30 | ~180 | ~5 min | 79 | 2 High + 3 Med (resolved, 3 rounds) | 7/7 | 85% | ~150 min | 4-MEU API settings/analytics/tax/system. Codex caught SimpleNamespace serialization, shutdown no-op, slash paths, psutil dep, settings dict shape |
| 2026-03-09 | MEU-31/32/33 | ~120 | ~4 min | 17 | 2 High + 3 Med (resolved, 2 rounds) | 7/7 | 90% | ~90 min | 3-MEU MCP server foundation: scaffold + trade/calculator/settings tools + integration test. Codex caught binary screenshot contract, stale port harness, annotation spec drift |
| 2026-03-09 | MEU-38/39/41 | ~200 | ~5 min | 74 | 1 Crit + 3 High + 5 Med (resolved, 4 rounds) | 7/7 | 85% | ~180 min | 3-MEU MCP guard/metrics/discovery: middleware HOFs, metrics collector, discovery meta-tools. Codex caught AC-6 spec gap, evidence drift, lint disclosure, closeout procrastination |
| 2026-03-10 | MEU-36/37/40 | ~150 | ~10 min | 29 | 5 Med (resolved, 4 rounds) | 7/7 | 85% | ~180 min | 3-MEU MCP planning/accounts/gui: TDD tools + ESM fix + middleware CallToolResult refactor. Codex caught PATH lookup gap, wait_for_close, ESM compat, lint suppression vs removal |
| 2026-03-10 | MEU-42 | ~200 | ~8 min | 46 | 8 rounds (3 High + 5 Med + 6 Low, all resolved) | 7/7 | 90% | ~240 min | ToolsetRegistry + adaptive client detection. MCP-local token store, 8 correction rounds for cross-plan doc alignment + evidence drift |
| 2026-03-11 | MEU-56/57/58 | ~120 | ~5 min | 48 | 1 High + 3 Med + 1 Low (resolved, 2 rounds) | 7/7 | 90% | ~90 min | 3-MEU market data foundation: AuthMethod + ProviderConfig + MarketDataPort + 4 DTOs + API key encryption. Codex caught Any return types, missing round-trip tests, stale counts, validator npx crash |
| 2026-03-11 | MEU-59/62/60 | ~200 | ~5 min | 147 | 1 High + 1 Med (resolved, 4 rounds) | 7/7 | 90% | ~120 min | 3-MEU market data infra: provider registry + rate limiter + connection service. 4 plan correction rounds for core→infra violation, bash→PowerShell, plan–code sync. Git commit policy codified. |
| 2026-03-11 | MEU-61/63/64 | ~250 | ~5 min | 58 | 3 High + 2 Med (resolved, 4 rounds) | 7/7 | 85% | ~180 min | 3-MEU market data service + API + MCP tools. 4 correction rounds: app.state wiring, MCP contract drift (configure→disconnect, name→provider_name, readOnlyHint), AV search normalizer, core→infra violation, stub services, TS2353 suppression, closeout artifacts. |
| 2026-03-12 | MEU-53/66/67 | ~200 | ~5 min | 74 | 2 High + 2 Med (resolved, 3 rounds) | 7/7 | 90% | ~150 min | 3-MEU trade reports+plans: MCP tools, TradePlan entity+service+API, plan↔trade linking. Codex caught URL drift (/plans→/trade-plans), MCP field alias gap, missing linking validation, no dedup rejection. |
| 2026-03-13 | MEU-68/69 | ~150 | ~5 min | 55 | 2 High + 5 Med + 1 Low (resolved, 3 rounds) | 7/7 | 85% | ~180 min | 2-MEU watchlist entity+service+API + MCP tools. Codex caught missing entity tests, AC-9 cascade label, MCP count drift, pyright scope. Evidence-freshness recursion was the main lesson. |
| 2026-03-13 | MEU-77/78/79/80 | ~200 | ~5 min | 143 | 2 High + 2 Med + 1 Low (resolved, 4 rounds) | 7/7 | 85% | ~300 min | 4-MEU scheduling domain foundation: enums, policy models, step registry, policy validator. Codex caught malformed ref acceptance, list-of-list recursion gap, StepBase import surface, get_all_steps() dict/class contract drift, stale doc references. |
| 2026-03-13 | MEU-96/99 | ~180 | ~5 min | 66 | 1 High + 3 Med + 1 Low (resolved, 2 rounds) | 7/7 | 85% | ~120 min | 2-MEU broker import foundation: IBKR FlexQuery XML + CSV framework (TOS, NinjaTrader) + ImportService. Codex caught fractional strike floor division, BOM path gap, weak AC-9 assertion, stale evidence counts. |

## Measurement Definitions

### Handoff Score (X/7)
Count how many of these 7 required sections are substantively filled (not blank/placeholder):
1. Scope
2. Feature Intent Contract (with ACs)
3. Design Decisions (with at least one decision + reasoning)
4. Changed Files (with descriptions)
5. Commands Executed (with results)
6. FAIL_TO_PASS Evidence
7. Test Mapping (AC → test function)

### Rule Adherence (%)
At session end, score: (rules followed / rules applicable) × 100.
Sample the top 10 most-relevant rules from AGENTS.md + GEMINI.md for the session's task type. Document which rules were checked in the reflection file.

### Trend Alerts
- Handoff Score below 5/7 for 2+ consecutive sessions → review template compliance
- Rule Adherence below 70% for any rule across 3+ sessions → candidate for removal or rewording

## Trend Notes

_Updated after second session when comparisons become possible._
