# Pipeline Integration — MEU Segmentation Decision

> **Date:** 2026-04-12  
> **Input:** 6 scheduling context documents (integration-gap-analysis, known-issues-meu-analysis, meu-pw1-discovery, pipeline-dataflow-checklist, spec-vs-code-audit, validation-corrections)

---

## Decision: Split Into 3 MEUs

The original MEU-PW1 scope (22 items across service wiring, code defects, and data schemas) is **too large for one MEU**. Sequential thinking analysis identified 3 natural clusters with distinct concerns, test boundaries, and dependency gates.

### Why 3 MEUs (Not 1 or 2)

| Option | Assessment |
|--------|-----------|
| **1 MEU** | ❌ 22 items, 10+ files, 3 packages. Violates 1-session sizing. No coherent single test boundary. Creating 2 new services + fixing SMTP + cache integration + schema modeling = too many concerns. |
| **2 MEUs** (plumbing+fetch, schemas) | ⚠️ Possible but plumbing+fetch combined = 14 items including 2 new services, SMTP fix, cache stub, rate limiter, HTTP cache. Still too many concerns for one session. |
| **3 MEUs** (plumbing, fetch, schemas) | ✅ Each has clear ACs, coherent test boundary, 1-session effort. Delivers incremental value at each step. |

### Segmentation Criteria Used

1. **Dependency gates:** PW1 prerequisite for PW2 (constructor expansion). PW3 independent.
2. **Concern isolation:** Wiring (PW1) vs new service (PW2) vs data modeling (PW3).
3. **Test boundary clarity:** Each MEU has one integration test scenario.
4. **Effort sizing:** Each is S-M, achievable in one focused session.
5. **Incremental value:** Each MEU delivers measurable operational progress.

---

## The 3 MEUs

### MEU-PW1: `pipeline-runtime-wiring`
> **Scope:** [meu-pw1-scope.md](file:///p:/zorivest/.agent/context/scheduling/meu-pw1-scope.md)

| Aspect | Detail |
|--------|--------|
| **Matrix** | P2.5 item 49.4 (existing) |
| **Items** | 10 (W-2 to W-9, D-1, D-5) |
| **Effort** | S-M |
| **Creates** | `DbWriteAdapter` (thin wrapper), `get_smtp_runtime_config()` method |
| **Result** | 4 of 5 step types operational (transform, store_report, render, send) |
| **Test** | Pipeline with store_report→render→send completes without ValueError |

---

### MEU-PW2: `fetch-step-integration`
> **Scope:** [meu-pw2-scope.md](file:///p:/zorivest/.agent/context/scheduling/meu-pw2-scope.md)

| Aspect | Detail |
|--------|--------|
| **Matrix** | P2.5 item 49.5 (new) |
| **Depends** | MEU-PW1 |
| **Items** | 4 (W-1, D-2, D-3, D-4) |
| **Effort** | M |
| **Creates** | `MarketDataProviderAdapter` (new service), `MarketDataAdapterPort` |
| **Result** | 5 of 5 step types operational (full pipeline) |
| **Test** | Pipeline with fetch→transform completes with mocked HTTP |

---

### MEU-PW3: `market-data-schemas`
> **Scope:** [meu-pw3-scope.md](file:///p:/zorivest/.agent/context/scheduling/meu-pw3-scope.md)

| Aspect | Detail |
|--------|--------|
| **Matrix** | P2.5 item 49.6 (new) |
| **Depends** | None (independent) |
| **Items** | 6 (S-1 to S-6) |
| **Effort** | S-M |
| **Creates** | 4 ORM models, 3 Pandera schemas, field mappings for 3 data types |
| **Result** | All market data validated and type-constrained at write time |
| **Test** | Schema validation passes/fails correctly for all 4 data types |

---

## Dependency Graph

```
MEU-PW1 ──→ MEU-PW2
  │            │
  │            ↓
  │       Full pipeline
  │       (all 5 steps)
  ↓
  4/5 steps operational

MEU-PW3 (independent — runs anytime)
  ↓
  Data quality hardened
```

## Value Delivery Ladder

```
Current:     0/5 steps operational (crash on any pipeline)
   ↓ PW1
After PW1:   4/5 steps operational (report pipelines work)
   ↓ PW2
After PW2:   5/5 steps operational (data fetch pipelines work)
   ↓ PW3
After PW3:   5/5 steps + data quality hardened (proper types, indexes, validation)
```

---

## Item Coverage Matrix

All 22 items from [integration-gap-analysis.md](file:///p:/zorivest/.agent/context/scheduling/integration-gap-analysis.md) are covered:

| Item | Category | MEU |
|------|----------|-----|
| W-1 | Provider adapter | PW2 |
| W-2 | Db write adapter | PW1 |
| W-3 | Report repo wire | PW1 |
| W-4 | Db connection wire | PW1 |
| W-5 | Pipeline state wire | PW1 |
| W-6 | Template engine wire | PW1 |
| W-7 | Delivery repo wire | PW1 |
| W-8 | SMTP config wire | PW1 |
| W-9 | Constructor expansion | PW1 |
| D-1 | SMTP key mismatch | PW1 |
| D-2 | Cache stub impl | PW2 |
| D-3 | Rate limiter integration | PW2 |
| D-4 | HTTP cache integration | PW2 |
| D-5 | Dead stubs deletion | PW1 |
| S-1 | OHLCV ORM model | PW3 |
| S-2 | Quotes ORM model | PW3 |
| S-3 | News ORM model | PW3 |
| S-4 | Fundamentals ORM model | PW3 |
| S-5 | 3 Pandera schemas | PW3 |
| S-6 | Field mappings | PW3 |

**22/22 covered. 0 items dropped.**

---

## Build Priority Matrix Updates Needed

| Item | Entry | Action |
|------|-------|--------|
| 49.4 | MEU-PW1 `pipeline-runtime-wiring` | **Refine** — update notes to remove provider adapter (moved to PW2) |
| 49.5 | MEU-PW2 `fetch-step-integration` | **Add new row** |
| 49.6 | MEU-PW3 `market-data-schemas` | **Add new row** |

---

## Recommended Execution Order

```
1. MEU-PW1 (pipeline-runtime-wiring)     ← highest value, unblocks 4/5 steps
2. MEU-PW2 (fetch-step-integration)      ← depends on PW1, completes pipeline
3. MEU-PW3 (market-data-schemas)         ← can run anytime, quality hardening
```

> [!NOTE]
> PW3 is deferrable. A pipeline works correctly without ORM models — data just lands in tables without type constraints or indexes. PW3 should be done before production use but is not a blocking requirement for development or testing.
