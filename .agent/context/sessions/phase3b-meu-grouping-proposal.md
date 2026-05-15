# Phase 3B–3E MEU Session Grouping Proposal

> Based on [phase3-feasibility-analysis.md](file:///p:/zorivest/.agent/context/sessions/phase3-feasibility-analysis.md), [build-priority-matrix.md §P3](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md), and [domain-model-reference.md §Module B–G](file:///p:/zorivest/docs/build-plan/domain-model-reference.md).

---

## Status: Phase 3A Complete ✅

All 7 MEUs (123–129) approved. 3196 tests passing, pyright/ruff clean. TaxLot, TaxProfile, gains calculator, loss carryforward, options pairing, and YTD P&L are all implemented and tested.

**Foundation available for 3B:**
- `TaxLot` entity with `wash_sale_adjustment` field (already plumbed, set to `Decimal(0)`)
- `TaxProfile` entity with `wash_sale_method: WashSaleMatchingMethod` enum (CONSERVATIVE | AGGRESSIVE)
- `TaxProfile.include_drip_wash_detection`, `include_spousal_accounts` toggles
- `TaxService` with working `close_lots()`, `get_taxable_gains()`, `simulate_impact()`
- `SqlTaxLotRepository` with full CRUD

---

## Dependency Graph

```
3A (COMPLETE ✅)
  │
  ├──► 3B: Wash Sale Engine (7 MEUs: 130–136)
  │      │
  │      └──► 3C: Tax Optimization Tools (6 MEUs: 137–142)
  │                 │
  │                 └──► 3E: Reports + API/MCP/GUI (9 MEUs: 148–156)
  │
  └──► 3D: Quarterly Payments & Brackets (5 MEUs: 143–147)
             │
             └──► 3E (also consumes 3D)
```

> [!TIP]
> **3B and 3D are parallel.** Neither depends on the other. Session planning should exploit this.

---

## Proposed Session Grouping

### Session 1: Wash Sale Foundation (3 MEUs)

| MEU | Build Plan | Description | Complexity | Risk |
|-----|:----------:|-------------|:----------:|:----:|
| MEU-130 | Item 57 | `WashSaleChain` entity + basic 30-day detection algorithm | High | ✅ |
| MEU-131 | Item 58 | Wash sale chain tracking (deferred loss rolling) | High | ✅ |
| MEU-132 | Item 59 | Cross-account wash sale aggregation | Medium | ✅ |

**Rationale:** These three form the structural core — entity + algorithm + multi-account scope. MEU-130 establishes `WashSaleChain`, `WashSaleEntry`, and the 30-day window detection. MEU-131 adds the chain state machine (disallowed → absorbed → released). MEU-132 extends to cross-account scanning using the existing `Account.is_tax_advantaged` flag. All three share test fixtures and domain context.

**Estimated test count:** ~45–55 (detection edge cases dominate: same-day, boundary days 30/31, partial lots, multiple lots in window)

**Key deliverables:**
- `WashSaleChain` + `WashSaleEntry` domain entities
- `WashSaleDetector` service (30-day window scanner)
- `SqlWashSaleChainRepository` + `WashSaleChainModel` ORM
- `TaxService.find_wash_sales()`, `.scan_wash_sales()` orchestration
- IRA permanent loss destruction logic (cross-account)

---

### Session 2: Wash Sale Extensions (4 MEUs)

| MEU | Build Plan | Description | Complexity | Risk |
|-----|:----------:|-------------|:----------:|:----:|
| MEU-133 | Item 60 | Options-to-stock wash sale matching (configurable) | Medium | ⚠️ |
| MEU-134 | Item 61 | DRIP wash sale detection | Medium | ⚠️ |
| MEU-135 | Item 62 | Auto-rebalance + spousal cross-wash warnings | Low | ✅ |
| MEU-136 | Item 63 | Wash sale prevention alerts (proactive pre-trade) | Medium | ✅ |

**Rationale:** These extend the core engine with specialized matching rules and UX-facing alerts. MEU-133 and MEU-134 carry the ⚠️ risk flags from feasibility analysis (options fields verified in 3A, DRIP model needs `TaxLot.acquisition_source` enum). MEU-135 and MEU-136 are lower complexity — they consume the existing detection engine and produce alert/warning objects.

**Estimated test count:** ~35–45

**Key deliverables:**
- Options-to-stock substantially-identical matching (toggled by `TaxProfile.wash_sale_method`)
- DRIP acquisition source enum + dividend reinvestment detection
- `TaxService.simulate_impact()` → `wash_sale_risk` field enrichment (pre-trade alerts)
- Spousal account cross-wash check (gated by `TaxProfile.include_spousal_accounts`)
- Auto-rebalance conflict detection (DCA/rebalance schedule vs. harvested loss window)

**Risk mitigations:**
- MEU-133: Options fields already verified working in MEU-128 (`parse_option_symbol()`, `OptionDetails`)
- MEU-134: If DRIP transaction type not yet importable, design `AcquisitionSource` enum defensively with `DRIP` variant + manual tagging path

---

### Session 3: Quarterly Payments & Tax Brackets (5 MEUs)

| MEU | Build Plan | Description | Complexity | Risk |
|-----|:----------:|-------------|:----------:|:----:|
| MEU-143 | Item 70 | `QuarterlyEstimate` entity + safe harbor calculation | Medium | ✅ |
| MEU-144 | Item 71 | Annualized income method (Form 2210 Schedule AI) | Medium | ✅ |
| MEU-145 | Item 72 | Quarterly due date tracker + underpayment penalty | Low | ✅ |
| MEU-146 | Item 73 | Marginal tax rate calculator (federal + state) | Medium | ✅ |
| MEU-147 | Item 74 | NIIT (3.8% surtax) threshold alert | Low | ✅ |

**Rationale:** Phase 3D is fully self-contained — pure computation with calendar logic, zero risk. All 5 MEUs are medium-to-low complexity with deterministic tax math. This is the safest session in the entire phase and could be parallelized with Session 2 if capacity allows.

**Estimated test count:** ~40–50

**Key deliverables:**
- `QuarterlyEstimate` entity + `SqlQuarterlyEstimateRepository`
- Safe harbor calculator (100%/110% prior year vs. 90% current year)
- Annualized income method (proportional quarterly payments)
- Due date engine (Apr 15, Jun 15, Sep 15, Jan 15) + penalty accrual
- Federal bracket lookup tables (2025/2026) + state rate integration
- NIIT threshold check ($200K/$250K MAGI)
- `TaxService.quarterly_estimate()`, `.record_payment()`, `.estimate()`

---

### Session 4: Tax Optimization Tools (6 MEUs)

| MEU | Build Plan | Description | Complexity | Risk |
|-----|:----------:|-------------|:----------:|:----:|
| MEU-137 | Item 64 | Pre-trade "what-if" tax simulator | Medium | ✅ |
| MEU-138 | Item 65 | Tax-loss harvesting scanner | Medium | ✅ |
| MEU-139 | Item 66 | Tax-smart replacement suggestions | Low | ✅ |
| MEU-140 | Item 67 | Lot matcher / close specific lots UI logic | Medium | ✅ |
| MEU-141 | Item 68 | Post-trade lot reassignment window (T+1) | Medium | ✅ |
| MEU-142 | Item 69 | ST vs LT tax rate dollar comparison | Low | ✅ |

**Rationale:** Phase 3C is the "optimization tools" layer — all of it consumes the wash sale engine (3B) and gains calculator (3A). MEU-137 extends the existing `TaxService.simulate_impact()` with full wash-sale-aware simulation. MEU-138–139 form a harvest scanner pair. MEU-140–141 handle lot selection/reassignment. MEU-142 is a pure computation adding the "wait N days to save $X" tip. Grouping all 6 works because they share the same service context.

**Estimated test count:** ~35–45

**Key deliverables:**
- Full `simulate_impact()` with wash sale risk + replacement suggestions
- `harvest_scan()` portfolio scanner (filter wash-conflicting positions)
- Static replacement lookup table (VOO↔IVV, QQQ↔QQQM, etc.)
- Lot selection API for SpecID method
- T+1 reassignment window check + undo
- ST→LT savings calculator with user bracket

---

### Session 5: Reports & Full-Stack Wiring (9 MEUs)

| MEU | Build Plan | Description | Complexity | Risk |
|-----|:----------:|-------------|:----------:|:----:|
| MEU-148 | Item 75 | Tax REST API: swap `StubTaxService` → real `TaxService` | Medium | ✅ |
| MEU-149 | Item 76 | Tax MCP tools: 4 stub actions → 8 real tools | Medium | ✅ |
| MEU-150 | Item 77 | Year-end tax position summary report | Low | ✅ |
| MEU-151 | Item 78 | Deferred loss carryover report | Low | ✅ |
| MEU-152 | Item 79 | Tax alpha savings summary | Low | ✅ |
| MEU-153 | Item 80 | Error check / transaction audit | Medium | ✅ |
| MEU-154 | Item 81 | Tax GUI: 10 React components (Wave 11 E2E) | High | ✅ |
| MEU-155 | Item 81a | Calculator expansion (conditional) | Low | ✅ |
| MEU-156 | Item 82 | Section 475/1256/Forex toggles | Low | ✅ |

> [!WARNING]
> **Session 5 is the largest and highest-risk session.** It touches all 4 integration surfaces (service→API→MCP→GUI). Consider splitting into **5a** (MEU-148–153: backend wiring + reports) and **5b** (MEU-154–156: GUI + conditional features) if session capacity is a concern.

**Potential split:**

| Sub-session | MEUs | Scope | Estimated tests |
|-------------|------|-------|:---------------:|
| **5a** — Backend wiring + reports | MEU-148–153 | Swap stubs, 4 reports, transaction audit | ~30–40 |
| **5b** — GUI + conditionals | MEU-154–156 | 10 React components, Wave 11 E2E, section toggles | ~25–35 (11 E2E + unit) |

---

## Execution Calendar

```
                    ┌─ Session 1 ─┐
                    │ MEU-130–132  │
                    │ Wash Core    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
     ┌─ Session 2 ──┐        ┌── Session 3 ──┐
     │ MEU-133–136   │        │ MEU-143–147   │
     │ Wash Ext      │        │ Qtrly + Rates │
     └───────┬───────┘        └───────┬───────┘
              │                       │
              └───────────┬───────────┘
                          ▼
                 ┌─ Session 4 ──┐
                 │ MEU-137–142  │
                 │ Optimization │
                 └───────┬──────┘
                         ▼
                ┌── Session 5 ──┐
                │ MEU-148–156   │
                │ Reports/Wire  │
                └───────────────┘
```

**Critical path:** Session 1 → Session 2 → Session 4 → Session 5 (4 sessions sequential)
**Parallelizable:** Session 3 can run alongside Session 2

---

## Risk Summary

| Risk | Session | Mitigation |
|------|:-------:|------------|
| `WashSaleChain` entity design complexity (30-day bidirectional window) | 1 | Research IRS Pub 550 + IBKR implementation before FIC |
| Options-to-stock "substantially identical" gray area | 2 | Configurable toggle (Conservative/Aggressive) already in `TaxProfile` |
| DRIP transaction type not yet importable | 2 | Design `AcquisitionSource` enum with `DRIP` variant; manual tagging fallback |
| Session 5 size (9 MEUs across 4 surfaces) | 5 | Split into 5a (backend) + 5b (GUI) if needed |
| MCP compound tool refactor (4→8 actions) | 5 | Build plan spec [05h-mcp-tax.md](file:///p:/zorivest/docs/build-plan/05h-mcp-tax.md) has complete TypeScript implementations |
| Wave 11 E2E test infrastructure | 5 | Test IDs + nav rail already defined in feasibility analysis |

---

## Open Questions for Human Decision

1. **Session 2 + 3 parallelization:** Should we attempt both in the same session (if context allows) since they're independent, or keep them separate for TDD discipline?

2. **Session 5 split:** Should 3E be split into 5a (backend wiring + reports) and 5b (GUI + conditionals), or executed as one large session?

3. **Pre-build research:** The wash sale 30-day window algorithm has significant edge cases (partial lots, same-day trades, corporate actions). Should we run `/pre-build-research` before Session 1 to extract IRS Pub 550 rules into a decision table?
