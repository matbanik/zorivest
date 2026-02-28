# Handoff: Service Layer Wholeness Corrections

**Date**: 2026-02-27
**Source**: [Critical Review](2026-02-27-build-plan-03-service-layer-wholeness-critical-review.md)
**Workflow**: `/planning-corrections`

---

## Design Decisions Made

| # | Decision | Choice |
|---|----------|--------|
| D1 | Report route shape | **A — Trade-scoped only** (`/trades/{exec_id}/report`) |
| D2 | Account/calculator routes in 04 | **B — Add stub route sections** (Step 4.10, 4.11) |
| D3 | MCP account-review naming | **A — Canonicalize to `get_account_review_checklist`** |

---

## Pass 1: Original Review Findings

| Finding | Severity | File(s) Modified | What Changed |
|---------|----------|-------------------|-------------|
| H1 | High | `04-rest-api.md` | Added Step 4.10 (Account Routes) and Step 4.11 (Calculator Routes) |
| H2 | High | `gui-actions-index.md` | Updated rows 4.1–4.3 to trade-scoped `/trades/{exec_id}/report`; added MCP tool ref |
| H3 | High | `03-service-layer.md` | Added `SQNService`, `CostOfFreeService`, `TradeReportService` stubs |
| H4 | High | `03-service-layer.md` | Added `BrokerImportService` (§18) and `PDFImportService` (§19) stubs |
| M1 | Medium | `domain-model-reference.md`, `06d-gui-accounts.md` | Renamed `start_account_review` → `get_account_review_checklist` |
| M2 | Medium | `05c-mcp-trade-analytics.md` | Removed "planned" and "not yet implemented" from PTC exclusion tables |
| L1 | Low | `04-rest-api.md` | Added `Literal` to `typing` import in trades.py snippet |
| M3 | — | N/A | **Refuted** — index summaries correctly reflect current state |

---

## Pass 2: Remaining Findings (user-identified)

| Finding | Severity | File(s) Modified | What Changed |
|---------|----------|-------------------|-------------|
| F1 | High | `04-rest-api.md` | Added `PUT /{exec_id}/report` and `DELETE /{exec_id}/report` route handlers |
| F2 | Medium | `04-rest-api.md` | Updated account router prefix to `/api/v1/accounts`, calculator to `/api/v1/calculator` |
| F3 | Medium | `gui-actions-index.md` | Fixed MCP guard config endpoint from `PUT /api/v1/mcp-guard` → `PUT /api/v1/mcp-guard/config` |
| F4 | Medium | N/A | **Not actionable** — index planned/modeled counts accurately reflect multi-phase project state |

---

## Verification Results

### Pass 1 (7/7 passed)

```
✅ No standalone /api/v1/reports references remain
✅ No start_account_review references remain
✅ No "not yet implemented" in 05c-mcp-trade-analytics.md
✅ All 5 new service stubs found in 03-service-layer.md
✅ No stale anchor/slug references
✅ No .agent/context/handoffs links in build-plan docs
✅ Literal import present in 04-rest-api.md
```

### Pass 2 (4/4 passed)

```
✅ PUT + DELETE report routes present at L143, L149
✅ Account prefix: /api/v1/accounts (L1086)
✅ Calculator prefix: /api/v1/calculator (L1143)
✅ MCP guard config: PUT /api/v1/mcp-guard/config (L169)
```
