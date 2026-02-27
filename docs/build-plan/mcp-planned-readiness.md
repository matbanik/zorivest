# MCP Planned → Specified Readiness

All 12 formerly-Planned tools are now **Specified** — full MCP contracts, REST endpoints, and service methods are in place.

> **Status: ✅ Complete.** All tools now have draft `server.tool()` specs in their category files ([05c](05c-mcp-trade-analytics.md)–[05h](05h-mcp-tax.md)), REST endpoint specs in [04-rest-api.md](04-rest-api.md), and service layer methods in [03-service-layer.md](03-service-layer.md).

## What "Specified" Means

A tool is **Specified** when it has:
1. **`server.tool(...)` code block** in its category file with: name, description string, Zod input schema, handler returning typed MCP content
2. **Input schema** — every parameter named, typed, with defaults
3. **Output shape** — concrete JSON structure or MCP content type (text/image)
4. **Error posture** — what happens on invalid input, backend errors, auth failures
5. **Side effects documented** — writes, external calls, spend
6. **Index entries** — `input-index.md`, `output-index.md`, `gui-actions-index.md` rows updated from 🔶/📋 to ✅

---

## Tool Readiness

### 1. `create_report` — [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md) |
| Input schema | ✅ Zod: `trade_id`, `setup_quality`, `execution_quality`, `followed_plan`, `emotional_state`, `lessons_learned`, `tags[]` |
| Output shape | ✅ JSON with created report ID + echoed fields |
| Error posture | ✅ `isError: true` on failure |
| REST dependency | ✅ `POST /api/v1/trades/{id}/report` — specified in [04-rest-api.md](04-rest-api.md) |
| Service layer | ✅ `ReportService.create()` — specified in [03-service-layer.md](03-service-layer.md) |

---

### 2. `get_report_for_trade` — [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05c-mcp-trade-analytics.md](05c-mcp-trade-analytics.md) |
| Input schema | ✅ `trade_id` (string, required) |
| Output shape | ✅ `TradeReport` payload or `isError: true` not-found |
| REST dependency | ✅ `GET /api/v1/trades/{id}/report` — specified in [04-rest-api.md](04-rest-api.md) |

---

### 3. `create_trade_plan` — [05d-mcp-trade-planning.md](05d-mcp-trade-planning.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05d-mcp-trade-planning.md](05d-mcp-trade-planning.md) |
| Input schema | ✅ Zod: ticker, direction, conviction, strategy, entry/stop/target, conditions, timeframe, account_id |
| Output shape | ✅ Created plan with computed `risk_reward_ratio`, status |
| REST dependency | ✅ `POST /api/v1/trade-plans` — specified in [04-rest-api.md](04-rest-api.md) |
| Service layer | ✅ `TradePlanService.create()` — specified in [03-service-layer.md](03-service-layer.md) |

---

### 4. `get_account_review_checklist` — [05f-mcp-accounts.md](05f-mcp-accounts.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05f-mcp-accounts.md](05f-mcp-accounts.md) |
| Input schema | ✅ `scope` (enum), `stale_threshold_days` (default 7) |
| Output shape | ✅ JSON with account staleness checklist + suggested actions |
| REST dependency | ✅ Uses existing `/brokers` + `/banking/accounts` — no new endpoints needed |

---

### 5. `simulate_tax_impact` — [05h-mcp-tax.md](05h-mcp-tax.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05h-mcp-tax.md](05h-mcp-tax.md) |
| Input schema | ✅ Zod: ticker, action, quantity, price, account_id, cost_basis_method |
| Output shape | ✅ Lot-level preview, ST/LT split, estimated tax, wash risk, hold-savings |
| REST dependency | ✅ `POST /api/v1/tax/simulate` — specified in [04-rest-api.md](04-rest-api.md) Step 4.9 |

---

### 6. `estimate_tax` — [05h-mcp-tax.md](05h-mcp-tax.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05h-mcp-tax.md](05h-mcp-tax.md) |
| Input schema | ✅ Zod: tax_year, account_id, filing_status, include_unrealized |
| Output shape | ✅ Federal + state tax estimate with bracket breakdown |
| REST dependency | ✅ `POST /api/v1/tax/estimate` — specified in [04-rest-api.md](04-rest-api.md) Step 4.9 |

---

### 7. `find_wash_sales` — [05h-mcp-tax.md](05h-mcp-tax.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05h-mcp-tax.md](05h-mcp-tax.md) |
| Input schema | ✅ Zod: account_id, ticker, date_range_start, date_range_end |
| Output shape | ✅ Wash sale chains with disallowed amounts, affected tickers |
| REST dependency | ✅ `POST /api/v1/tax/wash-sales` — specified in [04-rest-api.md](04-rest-api.md) Step 4.9 |

---

### 8. `get_tax_lots` — [05h-mcp-tax.md](05h-mcp-tax.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05h-mcp-tax.md](05h-mcp-tax.md) |
| Input schema | ✅ Zod: account_id, ticker, status, sort_by |
| Output shape | ✅ Lot list with basis/holding/gain fields + summary |
| REST dependency | ✅ `GET /api/v1/tax/lots` — specified in [04-rest-api.md](04-rest-api.md) Step 4.9 |

---

### 9. `get_quarterly_estimate` — [05h-mcp-tax.md](05h-mcp-tax.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05h-mcp-tax.md](05h-mcp-tax.md) |
| Input schema | ✅ Zod: quarter, tax_year, estimation_method |
| Output shape | ✅ Required/paid/due/penalty/due_date |
| REST dependency | ✅ `GET /api/v1/tax/quarterly` — specified in [04-rest-api.md](04-rest-api.md) Step 4.9 |

---

### 10. `record_quarterly_tax_payment` — [05h-mcp-tax.md](05h-mcp-tax.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05h-mcp-tax.md](05h-mcp-tax.md) |
| Input schema | ✅ Zod: quarter, tax_year, payment_amount, confirm |
| Output shape | ✅ Recorded payment + updated cumulative totals |
| REST dependency | ✅ `POST /api/v1/tax/quarterly/payment` — specified in [04-rest-api.md](04-rest-api.md) Step 4.9 |

---

### 11. `harvest_losses` — [05h-mcp-tax.md](05h-mcp-tax.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05h-mcp-tax.md](05h-mcp-tax.md) |
| Input schema | ✅ Zod: account_id, min_loss_threshold, exclude_wash_risk |
| Output shape | ✅ Ranked opportunities + totals + wash risk |
| REST dependency | ✅ `GET /api/v1/tax/harvest` — specified in [04-rest-api.md](04-rest-api.md) Step 4.9 |

---

### 12. `get_ytd_tax_summary` — [05h-mcp-tax.md](05h-mcp-tax.md)

| Aspect | Status |
|--------|--------|
| Owner file | ✅ [05h-mcp-tax.md](05h-mcp-tax.md) |
| Input schema | ✅ Zod: tax_year, account_id |
| Output shape | ✅ Aggregated YTD summary (ST/LT, wash adjustments, estimates) |
| REST dependency | ✅ `GET /api/v1/tax/ytd-summary` — specified in [04-rest-api.md](04-rest-api.md) Step 4.9 |

---

## Annotations Status

> All 68 tools now have `#### Annotations` blocks with `readOnlyHint`, `destructiveHint`, `idempotentHint`, `toolset`, and `alwaysLoaded` fields.
> Completed in Session 2 of the MCP Integration Plan.

| Metric | Count |
|--------|-------|
| Total annotation blocks | 65 |
| Files annotated | 10 (`05a`–`05j`) |
| Destructive tools | 4 (`emergency_stop`, `service_restart`, `disconnect_market_provider`, `sync_broker`) |
| Toolsets defined | 8 (`core`, `trade-analytics`, `trade-planning`, `market-data`, `accounts`, `scheduling`, `tax`, `behavioral`) |
| Always-loaded toolsets | 1 (`core`: 11 tools in `05a` + `05b`) |

---

## Summary

| Tool | Category File | Status | REST Endpoint | Annotations |
|------|--------------|--------|---------------|-------------|
| `simulate_tax_impact` | [05h](05h-mcp-tax.md) | ✅ Specified | `POST /tax/simulate` | ✅ |
| `get_quarterly_estimate` | [05h](05h-mcp-tax.md) | ✅ Specified | `GET /tax/quarterly` | ✅ |
| `record_quarterly_tax_payment` | [05h](05h-mcp-tax.md) | ✅ Specified | `POST /tax/quarterly/payment` | ✅ |
| `get_tax_lots` | [05h](05h-mcp-tax.md) | ✅ Specified | `GET /tax/lots` | ✅ |
| `get_ytd_tax_summary` | [05h](05h-mcp-tax.md) | ✅ Specified | `GET /tax/ytd-summary` | ✅ |
| `harvest_losses` | [05h](05h-mcp-tax.md) | ✅ Specified | `GET /tax/harvest` | ✅ |
| `estimate_tax` | [05h](05h-mcp-tax.md) | ✅ Specified | `POST /tax/estimate` | ✅ |
| `find_wash_sales` | [05h](05h-mcp-tax.md) | ✅ Specified | `POST /tax/wash-sales` | ✅ |
| `get_report_for_trade` | [05c](05c-mcp-trade-analytics.md) | ✅ Specified | `GET /trades/{id}/report` | ✅ |
| `get_account_review_checklist` | [05f](05f-mcp-accounts.md) | ✅ Specified | Existing endpoints | ✅ |
| `create_report` | [05c](05c-mcp-trade-analytics.md) | ✅ Specified | `POST /trades/{id}/report` | ✅ |
| `create_trade_plan` | [05d](05d-mcp-trade-planning.md) | ✅ Specified | `POST /trade-plans` | ✅ |
