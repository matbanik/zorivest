# MCP Tool Audit Report

**Date:** 2026-04-29  
**Agent:** Antigravity (Gemini)  
**Backend Version:** 0.1.0  
**MCP Server Node:** v22.20.0  
**Total Tools:** 13 compound tools across 4 toolsets  
**Consolidation Score:** 1.08 (13 / 12 ideal) — **Excellent**

## Scorecard

| Category | Tested | Passed | Failed | Partial | Skip |
|----------|--------|--------|--------|---------|------|
| Accounts CRUD | 7 | 7 | 0 | 0 | 0 |
| Trades CRUD | 5 | 5 | 0 | 0 | 0 |
| Watchlists CRUD | 4 | 4 | 0 | 0 | 0 |
| Templates CRUD | 6 | 6 | 0 | 0 | 0 |
| Market Data | 5 | 3 | 0 | 0 | 2 |
| Analytics | 8 | 8 | 0 | 0 | 0 |
| Planning | 1 | 1 | 0 | 0 | 0 |
| Ops / DB | 4 | 4 | 0 | 0 | 0 |
| Core / System | 5 | 5 | 0 | 0 | 0 |
| Tax (501 stubs) | 1 | 1 | 0 | 0 | 0 |
| **TOTAL** | **46** | **44** | **0** | **0** | **2** |

## CRUD Matrix

| Resource | Create | Get | Update | Delete | Other |
|----------|--------|-----|--------|--------|-------|
| Accounts | ✅ | ✅ | ✅ | ✅ (token) | Balance ✅, Archive ✅, Checklist ✅ |
| Trades | ✅ (token) | ✅ (via list) | — | ✅ (token) | — |
| Reports | ✅ | ✅ | — | — | 404 for missing ✅ |
| Watchlists | ✅ | ✅ | — | N/A | Add ✅, Remove ✅ |
| Templates | ✅ | ✅ | ✅ | ✅ | Preview ✅ |
| Policies | — | ✅ (list) | — | — | — |
| Plans | — | ✅ (list) | — | — | — |

## Functional Test Results

| Tool | Action | Status | Notes |
|------|--------|--------|-------|
| zorivest_system | diagnose | ✅ PASS | Backend reachable, DB unlocked |
| zorivest_system | settings_get | ✅ PASS | Returns 6 settings |
| zorivest_system | email_config | ✅ PASS | Gmail configured |
| zorivest_system | confirm_token | ✅ PASS | Tokens generated for delete_account, create_trade, delete_trade |
| zorivest_system | toolsets_list | ✅ PASS | 4 toolsets, 13 tools |
| zorivest_system | toolset_describe | ✅ PASS | All 4 toolsets described |
| zorivest_analytics | position_size | ✅ PASS | Correct calculation (40 shares) |
| zorivest_analytics | expectancy | ✅ PASS | Returns metrics |
| zorivest_analytics | sqn | ✅ PASS | Returns grade |
| zorivest_analytics | fee_breakdown | ✅ PASS | Returns breakdown |
| zorivest_analytics | drawdown | ✅ PASS | 10k simulations |
| zorivest_analytics | cost_of_free | ✅ PASS | Returns hidden costs |
| zorivest_analytics | strategy_breakdown | ✅ PASS | Returns strategies |
| zorivest_analytics | pfof_impact | ✅ PASS | Returns estimate (requires account_id) |
| zorivest_market | search | ✅ PASS | Apple → 6 results (Yahoo) |
| zorivest_market | quote | ✅ PASS | AAPL $270.17 |
| zorivest_market | providers | ✅ PASS | 14 providers (3 enabled) |
| zorivest_market | news | ⏭️ SKIP | 503 — Finnhub 422; no news-capable provider |
| zorivest_market | filings | ⏭️ SKIP | 503 — SEC API not configured |
| zorivest_db | list_tables | ✅ PASS | Full schema returned |
| zorivest_db | validate_sql (valid) | ✅ PASS | SELECT accepted |
| zorivest_db | validate_sql (DDL) | ✅ PASS | DROP TABLE **blocked** |
| zorivest_db | step_types | ✅ PASS | Pipeline step types returned |
| zorivest_tax | estimate | ✅ PASS | 501 Not Implemented (expected) |
| zorivest_plan | list | ✅ PASS | 3 plans returned |
| zorivest_policy | list | ✅ PASS | Policies returned |

## Toolset Inventory (Post-Correction)

| Toolset | Tools | Count | Status |
|---------|-------|-------|--------|
| core | zorivest_system | 1 | always_loaded ✅ |
| trade | zorivest_trade, zorivest_analytics, zorivest_report | 3 | default ✅ |
| data | zorivest_account, zorivest_market, zorivest_watchlist, zorivest_import, zorivest_tax | 5 | deferred ✅ |
| ops | zorivest_policy, zorivest_template, zorivest_db, **zorivest_plan** | 4 | deferred ✅ |

> ✅ `zorivest_plan` successfully relocated from `trade` → `ops` (Finding 1 verified)

## Regression Delta (vs Baseline)

| Tool | Previous | Current | Classification |
|------|----------|---------|----------------|
| zorivest_analytics | `fees, pfof, strategy` | `fee_breakdown, pfof_impact, strategy_breakdown` | **RENAMED** (v3.1) |
| zorivest_market | `sec_filings, disconnect_provider` | `filings, disconnect` | **RENAMED** (v3.1) |
| zorivest_report | `get_for_trade` | `get` | **RENAMED** (v3.1) |
| zorivest_plan | toolset: trade | toolset: ops | **RELOCATED** |

No regressions detected. All changes are intentional corrections from the v3.1 contract alignment.

## Issues Log

| # | Severity | Tool | Issue | Notes |
|---|----------|------|-------|-------|
| 1 | LOW | zorivest_watchlist | No delete_watchlist action | Known design limitation |
| 2 | LOW | zorivest_market (news) | 503 from Finnhub | Provider-specific; no news fallback |
| 3 | LOW | zorivest_market (filings) | SEC API not configured | Requires API key setup |
| 4 | INFO | zorivest_template (delete) | Not in confirmation gate registry | Deletion works without token |
| 5 | INFO | MCP-Audit-Watch (id=3) | Residual watchlist from prior audit | No delete tool to clean up |

## Consolidation Score

```
Current tools:  13
Ideal target:   12
Score:          13 / 12 = 1.08
Rating:         ✅ Excellent (< 2.0)
```

## Cleanup Verification

| Entity | Created | Deleted | Status |
|--------|---------|---------|--------|
| Account `89431b76` | ✅ | ✅ (token) | Clean |
| Trade `MCP-AUDIT-20260429` | ✅ | ✅ (token) | Clean |
| Report for trade | ✅ | ✅ (cascade) | Clean |
| Template `mcp-audit-20260429` | ✅ | ✅ | Clean |
| Watchlist `MCP-Audit-20260429` (id=4) | ✅ | ❌ No delete tool | **Residual** |

> [!NOTE]
> Watchlist id=4 remains as residual — no `delete_watchlist` action exists. Manual DB cleanup recommended if needed.
