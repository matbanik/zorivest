# Critical Review: Build Plan Expansion Ideas

**Reviewed file:** `_inspiration/import_research/Build Plan Expansion Ideas.md`  
**Review date:** 2026-02-20  
**Method:** Assumption audit + independent web validation + Zorivest fit scoring

## Executive Verdict

The document is directionally strong and technically feasible overall, but it overstates feasibility in several places and over-prioritizes scope relative to Zorivest's current phase (still Phase 1 domain implementation).  

Summary:
- `26/26` ideas are implementable in some form.
- `9/26` are strong near-term fit.
- `11/26` are good ideas but should be deferred until core ingestion/analytics are stable.
- `6/26` require assumption corrections before planning.

## Severity-Ranked Findings

### Critical

1. **OpenFIGI throughput assumption is incorrect**
- **Where:** §5 (`lines 290-291`, `line 321`)
- **Issue:** The doc states "free, unlimited with API key." OpenFIGI documents request limits (not unlimited).
- **Validation:** OpenFIGI API docs show request/job limits for both keyed and unkeyed access.
- **Impact:** Resolver design and import throughput estimates are currently optimistic and may fail under batch imports.
- **Fix:** Treat OpenFIGI as rate-limited dependency; add durable cache + retry queue + background backfill.

2. **US options settlement modeled as `T+0` appears wrong**
- **Where:** §23 (`line 1189`)
- **Issue:** `settlement_days: int  # T+1 for US equities, T+0 for US options` conflicts with current settlement guidance.
- **Validation:** SEC T+1 framework and options education materials point to next-business-day settlement for listed options.
- **Impact:** Incorrect settlement modeling can break buying-power and cash-availability logic.
- **Fix:** Default to `T+1` for listed options unless broker-specific override proves otherwise.

### High

3. **Execution-quality feature assumes data access that most users will not have**
- **Where:** §10 (`lines 586-619`)
- **Issue:** NBBO-at-fill scoring needs high-granularity quote history; this is often paid, delayed, or unavailable for retail APIs.
- **Validation:** Rule 605/606 reforms improve public reporting but do not replace per-trade NBBO history for end users.
- **Impact:** High risk of "designed but not operable" analytics.
- **Fix:** Gate this feature behind available quote data providers; otherwise degrade to broker-level proxy metrics.

4. **PFOF impact analysis is valid only as probabilistic, not trade-deterministic**
- **Where:** §11 (`lines 631-675`)
- **Issue:** Broker-level route classes are useful heuristics, but routing varies by order type/venue and reports are aggregate.
- **Validation:** FINRA/SEC Rule 606 disclosures are aggregate reports (quarterly publication with monthly breakdown), not per-trade truth.
- **Impact:** Overconfident "you lost X due to PFOF" conclusions can be misleading.
- **Fix:** Label output as estimate, include confidence band, and surface methodology in report UI.

5. **Bank import scope is oversized for current roadmap**
- **Where:** §26 (`lines 1324-1331`, `lines 1993-2009`)
- **Issue:** CSV+OFX+QIF+PDF+CAMT + 15-bank config registry is multi-quarter maintenance scope.
- **Validation:** Firefly's ecosystem shows this becomes a long-lived config-maintenance program.
- **Impact:** High delivery risk if attempted at P1 while core domain is still greenfield.
- **Fix:** Phase into `26A` (CSV + OFX/QFX + manual mapping), `26B` (QIF), `26C` (PDF/CAMT).

### Medium

6. **Alpaca auth description is incomplete**
- **Where:** §24 (`line 1230`)
- **Issue:** The text implies Basic Auth as primary; Alpaca docs also support/encourage explicit API headers.
- **Impact:** Integration examples may diverge from typical SDK/header usage.
- **Fix:** Document both methods and standardize implementation on headers for clarity.

7. **Dedup incremental rule can drop corrected/backfilled records**
- **Where:** §6 (`line 366`)
- **Issue:** "Only insert timestamps > latest existing" fails with late broker corrections and out-of-order imports.
- **Impact:** Silent data loss risk.
- **Fix:** Use idempotency hash + broker execution id + bounded lookback window, not monotonic timestamp cutoff.

8. **AI debate/persona value is promising but not proven superior**
- **Where:** §12 (`lines 686-719`)
- **Issue:** Recent multi-agent literature shows mixed gains versus simpler ensembling/voting.
- **Impact:** Could add cost/latency without consistent quality gains.
- **Fix:** Ship as opt-in weekly review experiment with quality telemetry, not default per-trade pipeline.

9. **PDF extraction plan is feasible but maintenance-heavy**
- **Where:** §19 and §26 PDF paths
- **Issue:** Per-broker layouts drift frequently; OCR fallback adds operational complexity.
- **Impact:** Long-term support burden out of proportion to early-stage value.
- **Fix:** Treat PDF parsing as last-mile fallback, not primary ingestion path.

## Assumption Validation (Independent Web Check)

| Assumption in doc | Result | Notes |
|---|---|---|
| OpenFIGI is "free, unlimited with key" | **Fail** | OpenFIGI docs publish request/job limits; model as rate-limited dependency. |
| Rule 605/606 reporting can power routing analysis | **Partial** | Feasible for aggregate context; not sufficient for deterministic per-trade attribution. |
| Rule 605 timeline in practice | **Updated** | SEC extended Rule 605 compliance to **Aug 1, 2026** (from Dec 14, 2025). |
| Alpaca auth model | **Partial** | Both header-based and Basic are documented; prefer headers in implementation. |
| Tradier rate limit assumptions | **Pass** | Public docs confirm standard vs market-data buckets. |
| tabula-py requires Java | **Pass** | Docs explicitly require Java runtime. |
| ofxtools handles OFX SGML + XML | **Pass** | Project docs explicitly support OFXv1 SGML and OFXv2 XML. |

## Feature-by-Feature Fit for Zorivest

Scales:
- **Feasibility:** High / Medium / Low
- **Fit:** Strong / Moderate / Weak

| # | Feature | Feasibility | Fit | Recommendation |
|---|---|---|---|---|
| 1 | IBroker Interface Pattern | High | Strong | Keep. Foundational abstraction. |
| 2 | Unified Adapter Layer | High | Strong | Keep with strict canonical schema contract tests. |
| 3 | Round-Trip Execution Matching | High | Strong | Keep; core for reliable trade history normalization. |
| 4 | Tax-Lot Accounting | High | Strong | Keep in existing P3 tax phase; no priority bump. |
| 5 | CUSIP/ISIN/SEDOL Resolver | Medium | Moderate | Keep; remove "AI ticker guess" from default chain. |
| 6 | Smart Deduplication | High | Strong | Keep; revise timestamp-only incremental logic. |
| 7 | MFE/MAE/BSO Auto-Enrichment | Medium | Moderate | Keep after market-data baseline is stable. |
| 8 | Multi-Leg Options Grouping | Medium | Moderate | Keep; add manual override UI for incomplete legs. |
| 9 | Transaction Ledger & Fee Cataloging | High | Strong | Keep; high analytical value. |
| 10 | Execution Quality Score | Medium | Moderate | Defer until quote-data availability is proven. |
| 11 | PFOF Impact Analysis | Medium | Moderate | Keep as probabilistic report only. |
| 12 | Multi-Persona AI Review | High | Moderate | Pilot-only, opt-in, cost-capped. |
| 13 | Expectancy & Edge Dashboard | High | Strong | Keep; high user value and low data friction. |
| 14 | Drawdown Probability Table | High | Strong | Keep alongside expectancy module. |
| 15 | SQN | High | Moderate | Keep as secondary metric in analytics pack. |
| 16 | Bidirectional Trade-Journal Linking | High | Moderate | Keep if journaling depth is product priority. |
| 17 | Mistake Tracking + Cost | High | Strong | Keep; strong behavior-change feedback loop. |
| 18 | Broker CSV Import Framework | High | Strong | Keep; immediate value and broad coverage. |
| 19 | PDF Broker Statement Extraction | Medium | Weak | Defer; high support burden vs early value. |
| 20 | Monthly P&L Calendar Report | High | Moderate | Keep as low-risk UI enhancement. |
| 21 | Strategy Breakdown Report | High | Strong | Keep; aligns with coaching/AI narrative goals. |
| 22 | Cost of Free Report | Medium | Moderate | Defer until fee + execution data quality matures. |
| 23 | Broker Constraint Modeling | Medium | Moderate | Start minimal (PDT, settlement, leverage); full model later. |
| 24 | Alpaca Direct API Integration | High | Moderate | Keep; good for paper/live sync and testing. |
| 25 | Tradier Direct API Integration | High | Moderate | Keep as optional adapter after top broker coverage. |
| 26 | Bank Statement Import | Medium | Moderate | Split into phased delivery; do not ship full scope at once. |

## Suggested Re-Prioritization for Zorivest

1. **Near-term (after core P0):** 1, 2, 3, 6, 9, 13, 14, 17, 18  
2. **Middle-term:** 4, 5, 7, 8, 15, 20, 21, 24, 25  
3. **Later / gated:** 10, 11, 12, 19, 22, 23, 26 (full scope)

## Source Links (Independent Validation)

- QuantConnect brokerage architecture: https://www.quantconnect.com/docs/v2/lean-engine/contributions/brokerages/creating-the-brokerage  
- CCXT unified API/manual: https://github.com/ccxt/ccxt/wiki/Manual/075e7b319ba37f1ac1f3a8a329af70d6a2c436d9  
- IRS Publication 550 (lot methods, wash-sale treatment): https://www.irs.gov/pub/irs-pdf/p550.pdf  
- OpenFIGI API documentation and limits: https://www.openfigi.com/api/documentation  
- SEC Rule 605 amendments (2024): https://www.sec.gov/rules-regulations/2024/03/disclosure-order-execution-information  
- SEC Rule 605 compliance extension to Aug 1, 2026 (2025): https://www.sec.gov/rules-regulations/2025/09/disclosure-order-execution-information  
- FINRA Rule 606 dataset overview: https://www.finra.org/finra-data/about-606  
- FINRA Regulatory Notice 24-05 (Rule 6151 centralization): https://www.finra.org/sites/default/files/2024-02/Regulatory_Notice_24-05.pdf  
- Alpaca authentication: https://docs.alpaca.markets/docs/authentication  
- Alpaca API usage limit support note: https://alpaca.markets/support/usage-limit-api-calls  
- Tradier rate limiting: https://documentation.tradier.com/brokerage-api/overview/rate-limiting  
- Tradier gain/loss endpoint: https://documentation.tradier.com/brokerage-api/accounts/get-account-gain-loss  
- SEC T+1 FAQ: https://www.sec.gov/exams/educationhelpguidesfaqs/t1-faq  
- OIC T+1 context article: https://www.optionseducation.org/news/understanding-t-1-conversion  
- ofxtools docs (OFXv1 SGML + OFXv2 XML): https://ofxtools.readthedocs.io/en/latest/  
- tabula-py requirements (Java): https://tabula-py.readthedocs.io/en/stable/getting_started.html  
- pikepdf security/encryption handling: https://pikepdf.readthedocs.io/en/latest/topics/security.html  
- Firefly import-configurations repo (config-maintenance precedent): https://github.com/firefly-iii/import-configurations  
- Obsidian URI reference (for link model feasibility): https://help.obsidian.md/Extending+Obsidian/Obsidian+URI  
- Multi-agent debate reliability caveats (2025 papers): https://arxiv.org/abs/2508.17536
