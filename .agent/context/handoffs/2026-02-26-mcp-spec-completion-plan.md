# MCP Tool Specification Completion Plan

## Goal

Promote all 12 **Planned** and 2 **Future** MCP tools to **Specified** status by filling the gaps identified in `mcp-planned-readiness.md`.

## Current State

| Count | Status | Gap Summary |
|---|---|---|
| 56 | **Specified** | Complete — no action needed |
| 12 | **Planned** | Draft MCP specs exist. Missing: REST endpoints (`04-rest-api.md`), some service methods (`03-service-layer.md`) |
| 2 | **Future** | Draft MCP specs exist. Blocked on Phase 1A logging architecture |

All 14 tools already have `server.tool()` code blocks, Zod schemas, annotation blocks, and output shapes. The primary gap is **downstream contract specs** (REST + service layer) and **index entry upgrades**.

---

## Proposed Batches

### Batch 1: Tax tools (8 tools) — `05h` + `04-rest-api` + `03-service-layer`

Highest volume, all in one category file. All drafts complete.

| Tool | REST Endpoint Needed | Service Method |
|---|---|---|
| `simulate_tax_impact` | `POST /api/v1/tax/simulate` | `TaxService.simulate_impact()` |
| `estimate_tax` | `POST /api/v1/tax/estimate` | `TaxService.estimate()` |
| `find_wash_sales` | `POST /api/v1/tax/wash-sales` | `TaxService.find_wash_sales()` |
| `get_tax_lots` | `GET /api/v1/tax/lots` | `TaxService.get_lots()` |
| `get_quarterly_estimate` | `GET /api/v1/tax/quarterly` | `TaxService.quarterly_estimate()` |
| `record_quarterly_tax_payment` | `POST /api/v1/tax/quarterly/payment` | `TaxService.record_payment()` |
| `harvest_losses` | `GET /api/v1/tax/harvest` | `TaxService.harvest_scan()` |
| `get_ytd_tax_summary` | `GET /api/v1/tax/ytd-summary` | `TaxService.ytd_summary()` |

**Changes:**
- `04-rest-api.md`: Add 8 endpoint specs under new §4.7 Tax API
- `03-service-layer.md`: Add `TaxService` with 8 methods
- `05h-mcp-tax.md`: Change `[Planned]` → `[Specified]` on all 8 tools; standardize error posture

---

### Batch 2: Report + Planning tools (3 tools) — `05c` + `05d` + `04-rest-api` + `03-service-layer`

| Tool | REST Endpoint Needed | Service Method |
|---|---|---|
| `create_report` | `POST /api/v1/trades/{id}/report` | `ReportService.create()` |
| `get_report_for_trade` | `GET /api/v1/trades/{id}/report` | `ReportService.get_for_trade()` |
| `create_trade_plan` | `POST /api/v1/trade-plans` | `TradePlanService.create()` |

**Changes:**
- `04-rest-api.md`: Add 3 endpoint specs
- `03-service-layer.md`: Add `ReportService` + `TradePlanService`
- `05c`/`05d`: Change `[Planned]` → `[Specified]`

---

### Batch 3: Accounts tool (1 tool) — `05f`

| Tool | REST Endpoint Needed | Service Method |
|---|---|---|
| `get_account_review_checklist` | None (uses existing endpoints) | None (composite query) |

**Changes:**
- `05f-mcp-accounts.md`: Change `[Planned]` → `[Specified]`

---

### Batch 4: Future → Specified logging tools (2 tools) — `05a`

| Tool | REST Endpoint Needed | Service Method |
|---|---|---|
| `get_log_settings` | Uses existing `/api/v1/settings?prefix=logging` | None |
| `update_log_level` | Uses existing `PUT /api/v1/settings` | None |

> [!IMPORTANT]
> These depend on Phase 1A logging architecture. **Decision needed:** promote to Specified now (since draft specs are complete and they use existing settings endpoints), or keep as Future until Phase 1A is implemented?

**Changes (if promoted):**
- `05a-mcp-zorivest-settings.md`: Change `[Future]` → `[Specified]`

---

### Batch 5: Cross-cutting updates (indexes + tracker)

After all tool promotions, update:

| File | Update |
|---|---|
| `mcp-tool-index.md` | Change `Planned`/`Future` → `Specified` in catalog rows (L69-82), update category counts (L93-107), update unique tool count note (L107) |
| `mcp-planned-readiness.md` | Mark all gaps as resolved, update summary table |
| `input-index.md` | Upgrade status markers 🔶/📋 → ✅ for promoted tools |
| `output-index.md` | Upgrade status markers for promoted tools |
| `gui-actions-index.md` | Upgrade status markers for promoted tools with GUI triggers |
| `build-priority-matrix.md` | Update readiness scores |

---

## Scope

| Batch | Tools | Files Modified | Effort |
|---|---|---|---|
| 1 – Tax | 8 | `05h`, `04-rest-api`, `03-service-layer` | **Medium** |
| 2 – Reports/Plans | 3 | `05c`, `05d`, `04-rest-api`, `03-service-layer` | **Medium** |
| 3 – Accounts | 1 | `05f` | **Low** |
| 4 – Logging | 2 | `05a` | **Low** (decision needed) |
| 5 – Indexes | — | `mcp-tool-index`, `mcp-planned-readiness`, `input-index`, `output-index`, `gui-actions-index`, `build-priority-matrix` | **Medium** |

## Open Questions

1. **Logging tools (Batch 4):** Promote to Specified now or keep as Future?
2. **Execution scope:** Execute all 5 batches in this session, or scope to a subset?
