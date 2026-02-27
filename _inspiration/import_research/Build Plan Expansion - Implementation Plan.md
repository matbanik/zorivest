# Integration Plan: Expansion Ideas → Build Plan

Integrate 26 features from [Build Plan Expansion Ideas](file:///p:/zorivest/_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) into [docs/build-plan/](file:///p:/zorivest/docs/build-plan).

---

## Feature → Target File Mapping

| # | Feature | Action | Primary Target Files | Priority |
|---|---------|--------|---------------------|----------|
| 1 | IBroker Interface | **ADD** | `01`, `03`, `domain-model-ref` | P1 |
| 2 | Unified Adapter Layer | **ADD** | `03`, `04`, `05` | P1 |
| 3 | Round-Trip Execution Matching | **ADD** | `01`, `03`, `domain-model-ref` | P1 |
| 4 | Tax-Lot Accounting | **MERGE** with existing Phase 3A | `01` items 50–56 (domain/service anchor) + `06g` (GUI consumer) | P2 |
| 5 | CUSIP/ISIN/SEDOL Resolver | **ADD** | `01`, `03`, `08` | P2 |
| 6 | Smart Deduplication | **ENHANCE** | `03` (TradeService dedup) | P1 |
| 7 | MFE/MAE/BSO | **ADD** | `01`, `03`, `08`, `06b` | P1 |
| 8 | Multi-Leg Options Grouping | **ADD** | `01`, `03`, `domain-model-ref` | P2 |
| 9 | Transaction Ledger & Fees | **ADD** | `01`, `02`, `03`, `domain-model-ref` | P1 |
| 10 | Execution Quality Score | **ADD** | `03`, `08`, `output-index` | P2 |
| 11 | PFOF Impact Analysis | **ADD** | `03`, `output-index` | P2 |
| 12 | Multi-Persona AI Review | **ADD** | `03`, `05` | P2 |
| 13 | Expectancy & Edge Dashboard | **ADD** | `03`, `06b`, `output-index` | P1 |
| 14 | Drawdown Probability | **ADD** | `03`, `output-index` | P1 |
| 15 | SQN | **ADD** | `03`, `04`, `05`, `output-index` | P2 |
| 16 | Bidirectional Trade-Journal | **ENHANCE** | `03`, `04`, `05`, `06b` (TradeReport) | P2 |
| 17 | Mistake Tracking | **ADD** | `01`, `03`, `06b`, `domain-model-ref` | P1 |
| 18 | Broker CSV Import | **ADD** | `02`, `03`, `04`, `05`, `06b` | P1 |
| 19 | PDF Broker Statement | **ADD** | `03`, `dependency-manifest` | P3 |
| 20 | Monthly P&L Calendar | **ADD** | `06b`, `output-index` | P2 |
| 21 | Strategy Breakdown Report | **ADD** | `03`, `06b`, `output-index` | P1 |
| 22 | "Cost of Free" Report | **ADD** | `03`, `04`, `05`, `output-index` | P2 |
| 23 | Broker Constraint Modeling | **ADD** | `01`, `domain-model-ref` | P2 |
| 24 | Alpaca Direct API | **ADD** | `03`, `04`, `05`, `08` | P2 |
| 25 | Tradier Direct API | **ADD** | `03`, `04`, `05`, `08` | P2 |
| 26 | Bank Statement Import | **ADD** | `01`, `02`, `03`, `04`, `05`, `06d`, `domain-model-ref` | P1 (phased) |

---

## Proposed Changes by Target File

### [MODIFY] [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md)

Add 8 new entity blocks to the entity map:

| Entity | Source § | Action | Details |
|--------|---------|--------|---------|
| `RoundTrip` | §3 | ADD after Trade | Groups executions into round-trips (entry group → exit group) with computed P&L |
| `IdentifierMapping` | §5 | ADD | CUSIP/ISIN/SEDOL → ticker cache with source, resolved_at, confidence |
| `TransactionLedger` / `FeeEntry` | §9 | ADD | Per-trade fee decomposition: commission, exchange, regulatory, ECN, clearing |
| `ExcursionMetrics` | §7 | ADD as Trade extension | MFE, MAE, BSO fields on Trade entity (or separate 1:1 table) |
| `OptionsStrategy` | §8 | ADD | Multi-leg grouping: strategy_type enum (vertical, iron condor, etc.), leg references |
| `MistakeEntry` | §17 | ADD | Mistake category enum, estimated cost attribution, linked trade_id |
| `BrokerModel` | §23 | ADD | PDT rules, settlement days, margin reqs, commission schedule, routing type |
| `BankTransaction` | §26 | ADD | Date, amount, description, category, dedup_hash, source, reference_id |

Also extend existing `Account` entity to add `sub_accounts`, `institution`, `balance_source` fields for bank account support (§26).

---

### [MODIFY] [01-domain-layer.md](file:///p:/zorivest/docs/build-plan/01-domain-layer.md)

**Step 1.2 enums — ADD new enums:**

| Enum | Source § | Values |
|------|---------|--------|
| `TransactionCategory` | §26 | deposit, withdrawal, transfer_in/out, fee, interest, dividend, ach_debit/credit, wire_in/out, check, card_purchase, refund, other |
| `BalanceSource` | §26 | MANUAL, CSV_IMPORT, OFX_IMPORT, PDF_IMPORT |
| `RoutingType` | §23 | PFOF, DMA, HYBRID |
| `MistakeCategory` | §17 | EARLY_EXIT, LATE_EXIT, OVERSIZED, NO_STOP, REVENGE_TRADE, FOMO_ENTRY, etc. |
| `StrategyType` | §8 | VERTICAL, IRON_CONDOR, BUTTERFLY, CALENDAR, STRADDLE, STRANGLE, CUSTOM |
| `CostBasisMethod` | §4 | FIFO, LIFO, HIFO, LIFO_BY_LOT, MIN_TAX, SPEC_ID, AVG_COST, MAX_ST_LOSS |

**Step 1.5 ports — ADD new port interfaces:**

| Port | Source § | Methods |
|------|---------|---------|
| `BrokerPort` (IBroker) | §1 | `get_account()`, `get_positions()`, `get_orders()`, `get_bars()`, `get_order_history()` |
| `BankImportPort` | §26 | `parse_statement()`, `detect_format()`, `detect_bank()` |
| `IdentifierResolverPort` | §5 | `resolve(id_type, id_value) → ticker` |

---

### [MODIFY] [02-infrastructure.md](file:///p:/zorivest/docs/build-plan/02-infrastructure.md)

**ADD new SQLAlchemy models / tables:**

| Table | Source § | Key Columns |
|-------|---------|-------------|
| `round_trips` | §3 | id, account_id, instrument, entry_avg_price, exit_avg_price, quantity, realized_pnl, status |
| `transaction_ledger` | §9 | id, trade_exec_id, fee_type, amount, currency |
| `identifier_cache` | §5 | id_type, id_value, ticker, exchange, resolved_at, source |
| `excursion_metrics` | §7 | trade_exec_id, mfe_dollars, mfe_pct, mae_dollars, mae_pct, bso_pct |
| `mistake_entries` | §17 | id, trade_id, category, estimated_cost, notes, created_at |
| `broker_configs` | §23 | broker_id, name, config_json (PDT rules, settlement, etc.) |
| `bank_transactions` | §26 | id, account_id, date, post_date, description, amount, category, dedup_hash, source, reference_id |
| `bank_import_configs` | §26 | bank_id, name, country, config_yaml |
| `options_strategies` | §8 | id, name, strategy_type, leg_exec_ids, created_at |

**ADD new repository implementations:**

- `RoundTripRepository`, `TransactionLedgerRepository`, `IdentifierCacheRepository`
- `ExcursionMetricsRepository`, `MistakeRepository`, `BankTransactionRepository`
- `BrokerConfigRepository`, `OptionsStrategyRepository`, `BankImportConfigRepository`

---

### [MODIFY] [03-service-layer.md](file:///p:/zorivest/docs/build-plan/03-service-layer.md)

**ADD new services** (with test stubs):

| Service | Source §§ | Key Methods | Dependencies |
|---------|----------|-------------|-------------|
| `BrokerAdapterService` | §1, §2 | `sync_account(broker)`, `import_trades(broker)`, `get_positions(broker)` | BrokerPort, TradeService |
| `RoundTripService` | §3 | `match_round_trips(executions)`, `get_round_trips(account, date_range)` | RoundTripRepo |
| `DeduplicationService` | §6 | `check_duplicate(execution)` — hash + exec_id + lookback window | TradeRepo |
| `ExcursionService` | §7 | `calculate_mfe_mae(trade, bars)`, `enrich_trade(trade)` | MarketDataService |
| `IdentifierResolverService` | §5 | `resolve(id_type, value)` — cache → OpenFIGI → Finnhub → AI | IdentifierCacheRepo |
| `OptionsGroupingService` | §8 | `detect_strategy(legs)`, `group_legs(executions)` | TradeRepo |
| `TransactionLedgerService` | §9 | `decompose_fees(trade)`, `get_fee_summary(account, period)` | LedgerRepo |
| `ExecutionQualityService` | §10 | `score_execution(trade, nbbo)` — gated on data availability | MarketDataService |
| `PFOFAnalysisService` | §11 | `generate_report(account, period)` — probabilistic estimates | ExecutionQualityService |
| `AIReviewService` | §12 | `multi_persona_review(trade)` — opt-in only | LLM provider |
| `ExpectancyService` | §13 | `calculate_expectancy(trades)`, `edge_metrics(trades)` | TradeRepo |
| `DrawdownService` | §14 | `drawdown_probability_table(trades, simulations)` | Monte Carlo |
| `MistakeTrackingService` | §17 | `classify_mistake(trade)`, `cost_attribution(trade)` | MistakeRepo |
| `StrategyBreakdownService` | §21 | `breakdown_by_strategy(trades)` | TradeRepo |
| `SQNService` | §15 | `calculate_sqn(trades) → {sqn_value, sqn_grade}` | TradeRepo |
| `CostOfFreeService` | §22 | `generate_report(account, period) → PFOF_cost + fee_impact + total_hidden_cost` | ExecutionQualityService, TransactionLedgerService |
| `BankImportService` | §26 | `import_statement(file)`, `detect_format(file)`, `detect_bank(csv)` | BankTransactionRepo |

**ENHANCE existing:**
- `TradeReportService` — add §16 bidirectional linking: `link_trade_to_journal(trade_id, journal_entry_id)`, `get_linked_journal(trade_id)`
- `TradeService` — integrate `DeduplicationService` (§6), replace timestamp-only logic with hash + exec_id + 30-day lookback

---

### [MODIFY] [04-rest-api.md](file:///p:/zorivest/docs/build-plan/04-rest-api.md)

**ADD new route groups:**

| Route Group | Source §§ | Key Endpoints |
|-------------|----------|--------------|
| `/brokers/` | §1, §2, §24, §25 | `GET /brokers` (list adapters), `POST /brokers/{id}/sync` (sync account), `GET /brokers/{id}/positions` |
| `/analytics/` | §10, §11, §13, §14, §15, §21, §22 | `GET /analytics/expectancy`, `GET /analytics/drawdown`, `GET /analytics/sqn`, `GET /analytics/execution-quality`, `GET /analytics/pfof-report`, `GET /analytics/strategy-breakdown`, `GET /analytics/cost-of-free` |
| `/round-trips/` | §3 | `GET /round-trips`, `GET /round-trips/{id}` |
| `/identifiers/` | §5 | `POST /identifiers/resolve` (batch resolve) |
| `/import/` | §18, §19 | `POST /import/csv` (broker CSV), `POST /import/pdf` (broker PDF) |
| `/banking/` | §26 | `POST /banking/import`, `GET /banking/accounts`, `POST /banking/transactions`, `PUT /banking/accounts/{id}/balance` |
| `/mistakes/` | §17 | `POST /mistakes`, `GET /mistakes?trade_id=`, `GET /mistakes/summary` |
| `/fees/` | §9 | `GET /fees/summary?account_id=&period=` |

---

### [MODIFY] [05-mcp-server.md](file:///p:/zorivest/docs/build-plan/05-mcp-server.md)

**ADD new MCP tool registrations:**

| Tool | Source § | REST Proxy |
|------|---------|-----------|
| `sync_broker_account` | §1, §2 | `POST /brokers/{id}/sync` |
| `import_broker_csv` | §18 | `POST /import/csv` |
| `get_round_trips` | §3 | `GET /round-trips` |
| `resolve_identifiers` | §5 | `POST /identifiers/resolve` |
| `get_excursion_metrics` | §7 | `GET /trades/{id}/excursions` |
| `get_execution_quality` | §10 | `GET /analytics/execution-quality` |
| `get_pfof_report` | §11 | `GET /analytics/pfof-report` |
| `ai_review_trade` | §12 | `POST /analytics/ai-review` |
| `get_expectancy` | §13 | `GET /analytics/expectancy` |
| `get_drawdown_table` | §14 | `GET /analytics/drawdown` |
| `track_mistake` | §17 | `POST /mistakes` |
| `get_strategy_breakdown` | §21 | `GET /analytics/strategy-breakdown` |
| `get_sqn` | §15 | `GET /analytics/sqn` |
| `get_cost_of_free` | §22 | `GET /analytics/cost-of-free` |
| `link_trade_journal` | §16 | `POST /trades/{id}/journal-link` |
| `import_bank_statement` | §26 | `POST /banking/import` |
| `update_bank_balance` | §26 | `PUT /banking/accounts/{id}/balance` |
| `submit_bank_transactions` | §26 | `POST /banking/transactions` |
| `list_bank_accounts` | §26 | `GET /banking/accounts` |

---

### [MODIFY] [06b-gui-trades.md](file:///p:/zorivest/docs/build-plan/06b-gui-trades.md)

**ENHANCE trade table columns:**
- ADD `mfe` / `mae` columns (§7) — show MFE/MAE values when enriched
- ADD `execution_quality` badge column (§10) — A/B/C/D/F grade
- ADD `mistake_flag` indicator (§17) — ⚠️ icon if mistake tagged

**ADD new panels/tabs:**
- "Round Trips" tab (§3) — grouped view of entry/exit execution pairs
- "Fee Breakdown" expandable row (§9) — commission, exchange, regulatory, ECN
- "Expectancy Dashboard" section (§13) — win rate, avg win/loss, expectancy per trade
- "Monthly P&L Calendar" component (§20) — calendar heatmap of daily P&L
- "Strategy Breakdown" tab (§21) — P&L by strategy_name

---

### [MODIFY] [06d-gui-accounts.md](file:///p:/zorivest/docs/build-plan/06d-gui-accounts.md)

**ADD bank account management:**
- Bank account list with balance, last updated, institution (§26)
- "Import Statement" button → file picker → import preview dashboard (§26)
- Manual column mapping GUI for unknown CSV formats (§26)
- Manual balance update form (§26)
- Manual transaction entry form (§26)

**ADD broker connections section:**
- Broker adapter list with sync status (§1, §24, §25)
- "Add Broker" → config form (API key entry)
- "Sync Now" button per broker

---

### [MODIFY] [08-market-data.md](file:///p:/zorivest/docs/build-plan/08-market-data.md)

**ADD new providers to provider registry:**

| Provider | Source § | Data Types |
|----------|---------|-----------|
| OpenFIGI | §5 | Identifier resolution (CUSIP/ISIN/SEDOL → ticker) — rate-limited, cache required |
| Alpaca | §24 | Orders, positions, account, bars, options chains, corporate actions, crypto |
| Tradier | §25 | Orders, positions, account, gain/loss, options chains, bars |

**ENHANCE provider configuration:**
- Add broker-specific auth patterns (Alpaca header-based, Tradier bearer token)
- Add rate limit configurations per new provider

---

### [MODIFY] [build-priority-matrix.md](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md)

**ADD items to existing priority sections:**

#### P1 — Build Soon (after core P0 items 1-16)

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| 83 | IBroker port interface (Protocol) | No | §1 — Type definitions for broker adapter pattern |
| 84 | BrokerAdapterService + registry | ✅ Yes | §1, §2 — Unified adapter layer |
| 85 | Round-trip execution matching | ✅ Yes | §3 — Groups executions into trades |
| 86 | Smart deduplication (hash + lookback) | ✅ Yes | §6 — Enhance TradeService |
| 87 | MFE/MAE/BSO auto-enrichment | ✅ Yes | §7 — Requires market data bars |
| 88 | Transaction ledger & fee decomposition | ✅ Yes | §9 — Per-trade fee breakdown |
| 89 | Expectancy & edge dashboard | ✅ Yes | §13 — Win rate, avg win/loss, edge |
| 90 | Drawdown probability table | ✅ Yes | §14 — Monte Carlo simulation |
| 91 | Mistake tracking + cost attribution | ✅ Yes | §17 — Behavior feedback loop |
| 92 | Broker CSV import framework | ✅ Yes | §18 — Multi-broker parser |
| 93 | Strategy breakdown report | ✅ Yes | §21 — P&L by strategy |
| 94 | Bank import Phase 26A (CSV + OFX) | ✅ Yes | §26 — Core bank statement import |

#### P2 — Build Later

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| 95 | CUSIP/ISIN/SEDOL resolver + OpenFIGI | ✅ Yes | §5 — Rate-limited, needs cache |
| 96 | Multi-leg options grouping | ✅ Yes | §8 — Strategy detection |
| 97 | Execution quality score | ✅ Yes | §10 — Gated on NBBO data |
| 98 | PFOF impact analysis | ✅ Yes | §11 — Probabilistic estimates |
| 99 | Multi-persona AI review | ✅ Yes | §12 — Opt-in experiment |
| 100 | SQN calculation | ✅ Yes | §15 — System quality metric |
| 101 | Bidirectional trade-journal linking | ✅ Yes | §16 — Deep-link trade ↔ journal |
| 102 | Monthly P&L calendar | ✅ Yes | §20 — Calendar heatmap |
| 103 | "Cost of Free" report | ✅ Yes | §22 — PFOF + fee analysis |
| 104 | Broker constraint modeling (PDT, settlement) | ✅ Yes | §23 — Start minimal |
| 105 | Alpaca direct API integration | ✅ Yes | §24 — Paper + live |
| 106 | Tradier direct API integration | ✅ Yes | §25 — Optional adapter |
| 107 | Bank import Phase 26B (QIF) | ✅ Yes | §26 — Legacy format |

#### P3 — Build Later Still

| Order | What | Tests First? | Notes |
|-------|------|-------------|-------|
| 108 | PDF broker statement extraction | ✅ Yes | §19 — Last-resort fallback |
| 109 | Bank import Phase 26C (PDF + CAMT.053) | ✅ Yes | §26 — Highest complexity |

---

### [MODIFY] [input-index.md](file:///p:/zorivest/docs/build-plan/input-index.md)

**ADD new input groups** (after existing §12):

| # | Group | Key Inputs | Source § |
|---|-------|-----------|---------|
| 13 | Broker Connection | broker_id, api_key, api_secret, environment (live/paper) | §1, §24, §25 |
| 14 | CSV Import | file_path, broker_hint, account_id, date_range_filter | §18 |
| 15 | Bank Statement Import | file_path, format (auto/csv/ofx/pdf), account_id, bank_hint | §26 |
| 16 | Manual Bank Transaction | account_id, date, amount, description, category | §26 |
| 17 | Mistake Tag | trade_id, mistake_category, estimated_cost, notes | §17 |
| 18 | AI Review Request | trade_id, review_type (single/weekly), budget_cap | §12 |
| 19 | Identifier Resolution | id_type (CUSIP/ISIN/SEDOL), id_value, exchange_hint | §5 |

---

### [MODIFY] [output-index.md](file:///p:/zorivest/docs/build-plan/output-index.md)

**ADD new output groups** (after existing §11):

| # | Group | Key Outputs | Source § |
|---|-------|------------|---------|
| 12 | Excursion Metrics | mfe_dollars, mfe_pct, mae_dollars, mae_pct, bso_pct | §7 |
| 13 | Execution Quality | price_improvement_cents, slippage_bps, fill_vs_midpoint, effective_spread, grade | §10 |
| 14 | Expectancy Dashboard | win_rate, avg_win, avg_loss, expectancy_per_trade, edge_ratio, kelly_pct | §13 |
| 15 | Drawdown Probability | probability_table (max_dd × confidence), recommended_risk_pct | §14 |
| 16 | SQN | sqn_value, sqn_grade (Holy Grail/Excellent/Good/Average/Poor) | §15 |
| 17 | PFOF Impact | pfof_excess_cost, dma_avg_slippage, pfof_avg_slippage, confidence_band | §11 |
| 18 | Strategy Breakdown | per_strategy: trade_count, win_rate, expectancy, total_pnl | §21 |
| 19 | Monthly P&L Calendar | daily_pnl_grid (month × day matrix with colors) | §20 |
| 20 | Fee Summary | total_fees, fee_by_type, fee_by_broker, fee_pct_of_pnl | §9 |
| 21 | Mistake Summary | mistakes_by_category, total_cost_of_mistakes, trend | §17 |
| 22 | Round-Trip Summary | total_round_trips, open_count, avg_holding_period, win_rate | §3 |
| 23 | Bank Import Result | imported_count, duplicate_count, flagged_count, balance_match | §26 |

---

### [MODIFY] [dependency-manifest.md](file:///p:/zorivest/docs/build-plan/dependency-manifest.md)

**ADD new Python dependencies:**

| Package | Version | Purpose | Source § |
|---------|---------|---------|---------|
| `ofxtools` | ≥0.9 | OFX/QFX bank statement parsing | §26 |
| `pdfplumber` | ≥0.11 | PDF table extraction | §19, §26 |
| `tabula-py` | ≥2.9 | PDF table extraction (optional, JRE) | §19, §26 |
| `pikepdf` | ≥9.0 | PDF decryption | §26 |
| `quiffen` | ≥2.0 | QIF format parsing | §26 |
| `chardet` | ≥5.0 | Encoding auto-detection | §18, §26 |
| `lxml` | ≥5.0 | CAMT.053 XML parsing | §26 |
| `alpaca-py` | ≥0.30 | Alpaca broker API SDK | §24 |

---

> [!IMPORTANT]
> **Scale advisory:** This plan covers ~120 individual entries across 14 files. Execution should be broken into batches:
> 1. **Batch 1:** `domain-model-reference.md` + `01-domain-layer.md` (entities + enums + ports)
> 2. **Batch 2:** `02-infrastructure.md` + `03-service-layer.md` (tables + services)
> 3. **Batch 3:** `04-rest-api.md` + `05-mcp-server.md` (routes + tools)
> 4. **Batch 4:** `06b-gui-trades.md` + `06d-gui-accounts.md` (GUI)
> 5. **Batch 5:** `08-market-data.md` (providers)
> 6. **Batch 6:** Indexes (`build-priority-matrix.md`, `input-index.md`, `output-index.md`, `dependency-manifest.md`)

## Verification Plan

### Manual Verification
- After each batch, verify the modified file renders clean markdown
- Cross-check that every § from the expansion doc has at least one entry in the target files
- Verify no duplicate entries (e.g., tax-lot accounting already partially exists in Phase 3A)
- Confirm build-priority-matrix item numbering is sequential and gap-free

---

## Design Decisions: Priority Change Log

> Added per CR1-1 review finding. Documents each priority change from the source Ideas doc.

| Feature | Ideas Priority | Plan Priority | Rationale |
|---------|---------------|--------------|----------|
| §1 IBKR Interface | P0 | P1 | Core trading works without broker API; P0 reserved for calculator/entities |
| §2 Unified Adapter | P0 | P1 | Same — adapter layer is "Build Soon" not "Build Now" |
| §3 Round-Trip Matching | P0 | P1 | Useful but not blocking core trade CRUD |
| §20 Monthly P&L Calendar | P3 | P2 | Low implementation cost, high user value |
| §23 Broker Constraints | P3 | P2 | PDT rules are critical for US traders, worth promoting |
| §24 Alpaca | P1 | P2 | Optional broker, not core path |
| §25 Tradier | P1 | P2 | Optional broker, not core path |

---

## REST ↔ MCP Parity Table

> Added per CR1-4 review finding. Cross-references every expansion REST endpoint with its MCP tool.

| REST Endpoint | MCP Tool | Source § |
|--------------|----------|----------|
| `GET /brokers` | — (GUI-only) | §1 |
| `POST /brokers/{id}/sync` | `sync_broker_account` | §1, §2 |
| `GET /brokers/{id}/positions` | — (GUI-only) | §1 |
| `GET /analytics/expectancy` | `get_expectancy` | §13 |
| `GET /analytics/drawdown` | `get_drawdown_table` | §14 |
| `GET /analytics/sqn` | `get_sqn` | §15 |
| `GET /analytics/execution-quality` | `get_execution_quality` | §10 |
| `GET /analytics/pfof-report` | `get_pfof_report` | §11 |
| `GET /analytics/strategy-breakdown` | `get_strategy_breakdown` | §21 |
| `GET /analytics/cost-of-free` | `get_cost_of_free` | §22 |
| `POST /analytics/ai-review` | `ai_review_trade` | §12 |
| `GET /round-trips` | `get_round_trips` | §3 |
| `GET /round-trips/{id}` | — (detail via same tool) | §3 |
| `POST /identifiers/resolve` | `resolve_identifiers` | §5 |
| `POST /import/csv` | `import_broker_csv` | §18 |
| `POST /import/pdf` | `import_broker_pdf` | §19 |
| `POST /banking/import` | `import_bank_statement` | §26 |
| `GET /banking/accounts` | `list_bank_accounts` | §26 |
| `POST /banking/transactions` | `submit_bank_transactions` | §26 |
| `PUT /banking/accounts/{id}/balance` | `update_bank_balance` | §26 |
| `POST /mistakes` | `track_mistake` | §17 |
| `GET /mistakes/summary` | — (GUI-only) | §17 |
| `GET /fees/summary` | — (via analytics) | §9 |
| `POST /trades/{id}/journal-link` | `link_trade_journal` | §16 |
| `GET /trades/{id}/excursions` | `get_excursion_metrics` | §7 |
