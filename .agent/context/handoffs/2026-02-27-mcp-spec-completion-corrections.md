# MCP Spec Completion — Corrections Handoff

## Task

- **Date:** 2026-02-27
- **Task slug:** mcp-spec-completion-corrections
- **Owner role:** coder
- **Scope:** Fix 6 critical review findings from `2026-02-27-docs-build-plan-mcp-spec-completion-critical-review.md`

## Findings: 6 verified, 6 fixed

| # | Sev | Finding | Fix |
|---|-----|---------|-----|
| F1 | High | Stale `DRAFT — Planned tool` comments + `## Planned Tools` heading + intro | Updated 11 DRAFT→Specified, renamed heading, fixed intro |
| F2 | High | `get_tax_lots` REST dep says POST not GET | Changed to GET (05h:208) |
| F3 | High | "not yet specified" REST dep residuals | Updated in 05c:617 + 05d:99 |
| F4 | High | Index icons 🔶/📋 not upgraded | Upgraded in input-index (3), output-index (1), gui-actions-index (3) |
| F5 | Medium | Route drift: `/api/v1/plans`, `quarterly_estimate` | Fixed in gui-actions-index, 06c-gui-planning, build-priority-matrix |
| F6 | Low | Annotation count 68→actual 65 | Fixed in mcp-planned-readiness |

## Files Changed

| File | Changes |
|---|---|
| `05h-mcp-tax.md` | Intro "Planned"→"Specified", 8 DRAFT→Specified, POST→GET for get_tax_lots |
| `05c-mcp-trade-analytics.md` | `## Planned Tools`→`## Report Tools`, 2 DRAFT→Specified, REST dep updated |
| `05d-mcp-trade-planning.md` | DRAFT→Specified, "not yet specified"→"specified in Step 4.1c" |
| `05f-mcp-accounts.md` | DRAFT→Specified |
| `input-index.md` | 3 tools: 📋/🔶→✅, plan file refs updated |
| `output-index.md` | `harvest_losses`: 📋→✅ |
| `gui-actions-index.md` | 3 route fixes `/plans`→`/trade-plans`, 3 icons upgraded, pending notes removed |
| `06c-gui-planning.md` | 5 route refs `/plans`→`/trade-plans` |
| `build-priority-matrix.md` | `quarterly_estimate`→`get_quarterly_estimate`, 7→8 tools, added `record_quarterly_tax_payment` |
| `mcp-planned-readiness.md` | Annotation count 68→65 |

## Verification (8/8 PASS)

```
V1: DRAFT Planned tool comments:     PASS (0 remaining)
V2: POST /tax/lots:                   PASS (0 remaining)
V3: "not yet specified":              PASS (0 remaining)
V4: stale /api/v1/plans:             PASS (0 remaining)
V5: bare quarterly_estimate:          PASS (0 remaining)
V6: annotation count = 65:           PASS
V7: ## Planned Tools heading:         PASS (removed)
V8: 05h intro says Specified:         PASS
```
