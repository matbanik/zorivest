# Phase 3A Session Division Plan

> 7 MEUs → 3 sessions, optimized for LLM context load and TDD discipline.

---

## MEU Complexity Profile

| MEU | Slug | Complexity | Est. Tests | Est. Code Lines | Key Challenge |
|-----|------|:----------:|:----------:|:---------------:|---------------|
| 123 | `tax-lot-entity` | Low-Med | 10-15 | ~200 | 8 CostBasisMethod enum values + entity fields |
| 124 | `tax-profile` | Low | 8-12 | ~150 | FilingStatus enum + bracket/state settings |
| 125 | `tax-lot-tracking` | **HIGH** | 25-40 | ~500 | 8 cost-basis algorithms (FIFO→Max ST Loss) |
| 126 | `tax-gains-calc` | Medium | 15-20 | ~200 | ST/LT classification + rate tables |
| 127 | `tax-loss-carry` | Medium | 12-18 | ~200 | $3K/yr cap, IRA/401K exclusion, year rollover |
| 128 | `options-assignment` | Med-High | 15-25 | ~250 | Options-specific domain knowledge |
| 129 | `ytd-pnl` | Low-Med | 10-15 | ~150 | Aggregation query, depends on 126+127 |

### Dependency Graph

```
MEU-123 (TaxLot entity) ──┬──→ MEU-125 (lot tracking) ──→ MEU-126 (gains calc) ──┬──→ MEU-129 (YTD P&L)
                          │                                                       │
MEU-124 (TaxProfile)  ────┼──────────────────────────────→ MEU-127 (loss carry) ──┘
                          │
                          └──→ MEU-128 (options assignment)
```

---

## Context Load Model

### Fixed Overhead (Every Session)

| Component | Tokens |
|-----------|:------:|
| AGENTS.md rules + workflow protocol | ~13K |
| Build plan references (matrix, feasibility) | ~8K |
| Handoff/reflection templates | ~3K |
| Prior session context (handoff read) | ~8-12K |
| TDD cycle tool outputs (3× quality gates) | ~15K |
| **Fixed subtotal** | **~50K** |

### Per-MEU Work Tokens

| MEU | FIC | Tests (Red) | Implementation (Green) | Per-MEU Total |
|-----|:---:|:-----------:|:----------------------:|:-------------:|
| 123 | 1.0K | 3K | 4K | **8K** |
| 124 | 0.8K | 2K | 3K | **6K** |
| 125 | 1.5K | 8K | 12K | **22K** |
| 126 | 1.0K | 4K | 5K | **10K** |
| 127 | 1.0K | 4K | 5K | **10K** |
| 128 | 1.2K | 5K | 6K | **12K** |
| 129 | 0.8K | 3K | 4K | **8K** |

---

## Recommended: 3 Sessions

### Session 1 — "Tax Foundation"
**MEUs:** Pre-flight audit + MEU-123 + MEU-124

| Phase | Work | Tokens |
|-------|------|:------:|
| Pre-flight audit | Inspect Trade entity for fill/option/DRIP fields | ~20K |
| MEU-123 | TaxLot entity + CostBasisMethod enum + SQLAlchemy model + repo | ~8K |
| MEU-124 | TaxProfile entity + FilingStatus enum + model + repo | ~6K |
| Fixed overhead | | ~50K |
| **Session total** | | **~84K** |

> **Theme:** Resolve all domain risks, lock the entity foundation.
> **Handoff:** "Entities, enums, models, repos complete. Pre-flight risks resolved. Ready for algorithmic work."

**Why this grouping works:**
- Pre-flight audit MUST happen before any code (feasibility doc recommends 1-2 days)
- MEU-123 and MEU-124 are entity definitions — same skill, same pattern, high cohesion
- Answering the option-field question early de-risks MEU-128 in Session 3
- Session stays light enough to be thorough on the pre-flight

---

### Session 2 — "Lot Tracking & Classification"
**MEUs:** MEU-125 + MEU-126

| Phase | Work | Tokens |
|-------|------|:------:|
| MEU-125 | 8 cost-basis lot assignment methods + holding period | ~22K |
| MEU-126 | ST/LT classification + gains calculator | ~10K |
| Prior context (S1 entities) | Read from handoff + reference files | ~12K |
| Fixed overhead | | ~50K |
| **Session total** | | **~94K** |

> **Theme:** The algorithmic core — assign lots, calculate gains.
> **Handoff:** "All 8 cost-basis methods implemented and tested. Gains calculator working. Phase 3A core engine functional."

**Why this grouping works:**
- MEU-125 is the **heaviest single MEU** in all of 3A — it gets a session with only one lightweight companion
- MEU-126 (gains calc) is a natural continuation: it _consumes_ lot tracking output as input
- The tests for MEU-126 serve as integration validation for MEU-125
- If MEU-125 runs long, MEU-126 can be deferred (escape hatch → Session 3)

> [!WARNING]
> **Escape hatch:** If MEU-125's 8 cost-basis methods hit the 50% context checkpoint before MEU-126 starts, defer MEU-126 to Session 3. Session 3 would then become 4 MEUs (126+127+128+129, ~110K) — still within safe bounds.

---

### Session 3 — "Tax Rules & Reporting"
**MEUs:** MEU-127 + MEU-128 + MEU-129

| Phase | Work | Tokens |
|-------|------|:------:|
| MEU-127 | Capital loss carryforward + account exclusion | ~10K |
| MEU-128 | Options assignment/exercise cost basis pairing | ~12K |
| MEU-129 | YTD P&L by symbol (ST vs LT breakdown) | ~8K |
| Prior context (S1-S2 entities + lot tracking) | Read from handoff + reference files | ~16K |
| Fixed overhead | | ~50K |
| **Session total** | | **~96K** |

> **Theme:** Tax rule application — consume the foundation built in S1-S2.
> **Handoff:** "Phase 3A complete. 7/7 MEUs done. Ready for Phase 3B (Wash Sale Engine)."

**Why this grouping works:**
- Three MEUs but all medium-weight — none is a context hog
- MEU-127 (loss carry) and MEU-128 (options) are independent of each other — can be done in either order
- MEU-129 (YTD P&L) is the lightest MEU, a natural session closer
- Clean exit: Phase 3A complete, handoff to 3B

---

## Alternative Plans (Considered & Rejected)

| Plan | Sessions | Rejected Because |
|------|:--------:|------------------|
| 2 sessions (123+124+125 / 126-129) | 2 | Session 1: ~120K with pre-flight — tight. Session 2: 4 MEUs — too many for TDD discipline |
| 4 sessions (123+124 / 125 / 126+127 / 128+129) | 4 | Session 1 underloaded (just entities). Handoff overhead per session (~30 min) ×4 is wasteful |
| Linear (1 per session) | 7 | Massive handoff overhead, context rebuilding cost dominates |

---

## Risk Matrix

| Risk | Session | Probability | Mitigation |
|------|:-------:|:-----------:|------------|
| Option fields missing from Trade entity | S1 | 40% | Pre-flight audit resolves this. Extend MEU-123 scope if needed |
| MEU-125 exceeds session budget (8 algorithms) | S2 | 25% | Escape hatch: defer MEU-126 to S3 |
| DRIP transaction type missing | S3 (affects 3B not 3A) | 50% | Design `acquisition_source` enum in S1 even if import path comes later |
| Prior-session context staleness | S2, S3 | 15% | Handoff docs + `pomera_notes` + file re-reads |

---

## Session Execution Order

```
Session 1: Tax Foundation
├── Pre-flight audit (domain inspection)
├── MEU-123: TaxLot + CostBasisMethod
├── MEU-124: TaxProfile + FilingStatus
└── Handoff → pomera_notes

Session 2: Lot Tracking & Classification
├── MEU-125: 8 cost-basis lot assignment methods ← HEAVIEST
├── MEU-126: ST/LT classification + gains calc
└── Handoff → pomera_notes

Session 3: Tax Rules & Reporting
├── MEU-127: Capital loss carryforward
├── MEU-128: Options assignment cost basis
├── MEU-129: YTD P&L aggregation
└── Phase 3A complete → handoff to 3B
```
