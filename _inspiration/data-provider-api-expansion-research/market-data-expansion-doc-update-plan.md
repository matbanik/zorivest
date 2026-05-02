# Market Data Expansion — Documentation Update Plan

> **Date**: 2026-05-01 | **Source**: [market-data-research-synthesis.md](file:///p:/zorivest/_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md)
> **Scope**: Remove Benzinga, add 13 MEUs across 6 layers, create MCP rebuild skill, update mcp-audit

---

## 1. Benzinga Removal (Cross-Cutting)

**Decision** `[Human-approved, 2026-05-01]`: User decided to remove Benzinga due to pricing concerns. While Benzinga does advertise free/trial API keys on its public landing page, the required datasets for Zorivest (earnings, fundamentals, corporate actions) are enterprise-tier only ($99+/mo per dataset via Massive.com). News-only access via free tier is insufficient — Finnhub already covers news at no cost. The user's exclusion decision is the authoritative source.

**Provider count change**: 12 API-key → **11 API-key** + 2 free (Yahoo, TradingView) = **13 total**

### Files to Update

| File | Change |
|------|--------|
| [08-market-data.md](file:///p:/zorivest/docs/build-plan/08-market-data.md) | Remove Benzinga `ProviderConfig` entry (L303-312), update goal (14→13 providers), remove from architecture diagram, auth table, connection testing table |
| [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md) | Update Phase 8 row: "14 market data providers" → "13 market data providers (11 API-key + 2 free)" |
| [build-priority-matrix.md](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md) | Update item 24 note: "12 providers" → "11 providers" |
| [market-data-research-synthesis.md](file:///p:/zorivest/_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md) | Remove Benzinga column from §1 capability matrix, remove from §2 recommendations, remove from §3 rate limits, update §4 builder families |
| [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md) | Update MEU-59 description: "12 providers" → "11 providers" |
| [06f-gui-settings.md](file:///p:/zorivest/docs/build-plan/06f-gui-settings.md) | Remove Benzinga from provider list wireframe (L35) |
| [06-gui.md](file:///p:/zorivest/docs/build-plan/06-gui.md) | Update exit criterion: "all 12 providers" → "all 11 API-key providers" (L491) |
| [policy-authoring-guide.md](file:///p:/zorivest/docs/guides/policy-authoring-guide.md) | Remove Benzinga from provider capabilities table (L615) |
| [01a-logging.md](file:///p:/zorivest/docs/build-plan/01a-logging.md) | Remove Benzinga from code comment example (L521) |

> [!NOTE]
> **Code changes** (`provider_registry.py`, `normalizers.py`, MCP compound tool) are deferred to execution — this plan covers documentation only.

---

## 2. New MEU Assignments (MEU-182 → MEU-194)

### Layer 1: Domain Models (2 MEUs)

| MEU | Slug | Description | Complexity | Deps |
|-----|------|-------------|:----------:|------|
| MEU-182 | `market-expansion-dtos` | 7 new DTOs (OHLCV, Fundamentals, Earnings, Dividends, Splits, Insider, EconomicCalendar) + updated `MarketDataPort` with 8 new methods | Low | None |
| MEU-183 | `market-expansion-tables` | 4 new SQLAlchemy models (MarketEarnings, MarketDividends, MarketSplits, MarketInsider) + Alembic migrations | Medium | MEU-182 |

### Layer 2: URL Builders (3 MEUs)

| MEU | Slug | Description | Complexity | Deps |
|-----|------|-------------|:----------:|------|
| MEU-184 | `provider-capabilities` | `ProviderCapabilities` dataclass (builder_mode, auth_mode, multi_symbol_style, pagination_style, extractor_shape, supported_data_types, free_tier) + extend all 11 registry entries | Low | None |
| MEU-185 | `simple-get-builders` | 5 Simple GET builders: `AlpacaUrlBuilder`, `FMPUrlBuilder`, `EODHDUrlBuilder`, `APINinjasUrlBuilder`, `TradierUrlBuilder` | Medium | MEU-184 |
| MEU-186 | `special-pattern-builders` | 4 special-pattern builders: `AlphaVantageUrlBuilder` (function-dispatch), `NasdaqDataLinkUrlBuilder` (dataset/table), `OpenFIGIUrlBuilder` (POST-body), `SECAPIUrlBuilder` (POST-body) | High | MEU-184 |

### Layer 3: Extractors + Field Mappings (3 MEUs)

| MEU | Slug | Description | Complexity | Deps |
|-----|------|-------------|:----------:|------|
| MEU-187 | `extractors-standard` | Standard JSON envelope extractors for Alpaca, FMP, EODHD, API Ninjas, Tradier + ~25 field mapping tuples | Medium | MEU-185 |
| MEU-188 | `extractors-complex` | Complex extractors: Alpha Vantage (date-keyed dicts + CSV earnings), Finnhub (parallel arrays), Nasdaq DL (parallel arrays + column_names), Polygon (ms timestamps) + ~20 field mappings | High | MEU-186 |
| MEU-189 | `extractors-post-body` | POST-based extractors: OpenFIGI v3 (warning key rename), SEC API (Lucene response) + ~10 field mappings | Medium | MEU-186 |

### Layer 4: Service Methods + Normalizers (2 MEUs)

| MEU | Slug | Description | Complexity | Deps |
|-----|------|-------------|:----------:|------|
| MEU-190 | `service-methods-core` | 3 high-value methods: `get_ohlcv` (primary: Alpaca), `get_fundamentals` (primary: FMP), `get_earnings` (primary: Finnhub) + normalizers per provider fallback chain | High | MEU-187, 188 |
| MEU-191 | `service-methods-extended` | 5 additional methods: `get_dividends`, `get_splits`, `get_insider`, `get_economic_calendar`, `get_company_profile` + normalizers | Medium | MEU-190 |

### Layer 5: API Routes + MCP Actions (1 MEU)

| MEU | Slug | Description | Complexity | Deps |
|-----|------|-------------|:----------:|------|
| MEU-192 | `market-routes-mcp` | 8 new `GET /api/v1/market-data/{type}` endpoints + 8 new action mappings in `zorivest_market` compound tool + update `zorivest_db` `provider_capabilities` action | Medium | MEU-191 |

#### Boundary Input Contract — MEU-192 (REST + MCP Surface)

> Required per AGENTS.md §Boundary Input Contract for external-input MEUs.

| Boundary | Schema Owner | Field Constraints | Extra-Field Policy | Error Mapping |
|----------|-------------|-------------------|-------------------|---------------|
| `GET /api/v1/market-data/ohlcv?ticker=X&from=Y&to=Z&interval=D` (+ 7 similar) | Pydantic `MarketDataQueryParams` (new) | `ticker`: str, 1-10 chars, uppercase; `from`/`to`: ISO date; `interval`: enum `1d,1w,1mo`; `provider`: optional str from registry | `extra="forbid"` | Invalid params → 422; provider not found → 404; upstream API error → 502 |
| MCP `zorivest_market(action: "ohlcv", ticker: "X", ...)` (+ 7 similar) | Zod schema in compound tool `.inputSchema` | Same field rules as REST; `action` enum extended | `.strict()` | Invalid → MCP error response with 422 detail |
| Provider API responses (ingested) | Per-provider extractor validates envelope shape | Type coercion for timestamps (ms→s), numeric strings→float | `extra="allow"` (pass-through) | Malformed response → logged warning + empty result |

> **Source-backed exception for provider responses** `[Research-backed]`: Provider API responses are external, untrusted inputs with highly variable schemas across 11 providers. Applying `extra="forbid"` at the ingestion boundary would cause hard failures on any upstream schema addition — a routine occurrence with financial APIs. The industry-standard pattern for ETL/ingestion pipelines is to accept unknown fields at the raw response layer and enforce strict schemas at the normalizer→DTO boundary (ref: [Pydantic docs — Model Config `extra`](https://docs.pydantic.dev/latest/concepts/config/#extra-attributes): "For APIs that you don't control, `extra='allow'` or `extra='ignore'` is recommended"). Validation strictness (`extra="forbid"`) is enforced at the REST/MCP input boundary (rows 1-2 above) and at the DB write boundary (MEU-193 BIC).

**Create/Update Parity — MEU-192**: Market data endpoints are read-only queries (`GET` only). No create or update paths exist for this MEU. The single `MarketDataQueryParams` schema enforces identical validation for all query variations. If future PUT/PATCH endpoints are added, they must use a dedicated Pydantic model with the same field constraints as the query schema.

### Layer 6: Pipeline Persistence + Scheduling (2 MEUs)

| MEU | Slug | Description | Complexity | Deps |
|-----|------|-------------|:----------:|------|
| MEU-193 | `market-store-step` | New `MarketDataStoreStep` pipeline step: route normalized data to canonical DB tables, extend `DbWriteAdapter` with market data write paths | Medium | MEU-192 |
| MEU-194 | `scheduling-recipes` | 10 pre-built policy templates (nightly OHLCV, pre-market quotes, weekly fundamentals, daily earnings, etc.) seeded via migration | Low | MEU-193 |

#### Boundary Input Contract — MEU-193 (Pipeline Store Step)

| Boundary | Schema Owner | Field Constraints | Extra-Field Policy | Error Mapping |
|----------|-------------|-------------------|-------------------|---------------|
| Pipeline policy JSON `steps[].config` for `market_data_store` type | Pydantic `MarketDataStoreConfig` (new) | `data_type`: enum matching canonical table names; `ticker`: str; `dedup_window_hours`: int 1-720 | `extra="forbid"` | Invalid config → policy validation error at VALIDATE phase (not runtime 500) |
| Normalized DTO → SQLAlchemy write | Per-table SQLAlchemy model column constraints | All numeric fields: `Numeric(18,8)`; timestamps: `DateTime(timezone=True)`; ticker: `String(10)` | Extra columns rejected by model | Constraint violation → logged error + skip row (no partial writes) |

**Create/Update Parity — MEU-193**: The `MarketDataStoreStep` supports two write modes: `INSERT` (new records) and `UPSERT` (dedup by ticker+timestamp). Both modes use the same `MarketDataStoreConfig` schema with identical field constraints. The dedup window (`dedup_window_hours`) applies uniformly to both paths. No partial-update path exists — records are always full-row writes.

### Dependency Chain

```
MEU-182 → MEU-183 ─┐
                    ├→ MEU-190 → MEU-191 → MEU-192 → MEU-193 → MEU-194
MEU-184 → MEU-185 → MEU-187 ─┤
      └→ MEU-186 → MEU-188 ─┤
               └→ MEU-189 ─┘
```

---

## 3. Document Inventory — Create/Update

### New Documents to Create

| Document | Path | Purpose |
|----------|------|---------|
| **Phase 8a Spec** | `docs/build-plan/08a-market-data-expansion.md` | Detailed build spec for all 6 layers — the source of truth for MEU-182→194 |
| **MCP Rebuild Skill** | `.agent/skills/mcp-rebuild/SKILL.md` | Canonical commands for rebuilding MCP server + restart notification protocol |

### Existing Documents to Update

| Document | Path | Changes |
|----------|------|---------|
| BUILD_PLAN.md | `docs/BUILD_PLAN.md` | Add Phase 8a row, 13 new MEU entries in P1.5a section, update summary table totals |
| build-priority-matrix.md | `docs/build-plan/build-priority-matrix.md` | Add P1.5a section with 13 items between P1.5 and P2; update header count "221 items" → "234 items" |
| 08-market-data.md | `docs/build-plan/08-market-data.md` | Remove Benzinga, add "See 08a for expansion" forward-reference |
| meu-registry.md | `.agent/context/meu-registry.md` | Add Phase 8a section with 13 MEU entries |
| mcp-audit SKILL.md | `.agent/skills/mcp-audit/SKILL.md` | Add Phase 3a (Provider API Validation) + Phase 3b (Report Pipeline Validation); update consolidation score formula `/ 12` → `/ 13` |
| mcp-audit workflow | `.agent/workflows/mcp-audit.md` | Add Steps 4a/4b for live API testing + pipeline testing, update exit criteria; update consolidation score formula `/ 12` → `/ 13` |
| research synthesis | `_inspiration/.../market-data-research-synthesis.md` | Remove Benzinga from all tables |

---

## 4. New Skill: MCP Server Rebuild

**Path**: `.agent/skills/mcp-rebuild/SKILL.md`

### Proposed Content

```yaml
name: MCP Server Rebuild
description: Canonical commands for rebuilding the Zorivest MCP server and
  notifying the user to restart Antigravity IDE for live testing.
```

**Key sections**:

1. **Build Commands** — `cd mcp-server && npm run build` with redirect-to-file pattern
2. **Restart Notification** — Emit a clear message to the user: "MCP server rebuilt. Please restart Antigravity to pick up changes, then confirm when ready."
3. **Post-Restart Verification** — `zorivest_system(action:"diagnose")` → verify `mcp_server.connected`, tool count matches expected
4. **Live API Testing Checklist** — For each configured provider: call `zorivest_market(action:"test_provider", provider_name: "X")`, record pass/fail
5. **Quick Reference Table** — Build → Notify → Wait → Diagnose → Test

---

## 5. MCP Audit Updates

### New Phase 3a: Provider API Validation

Insert between current Phase 3 (Functional) and Phase 4 (Regression):

```markdown
### Phase 3a: Provider API Validation (Live)

For each market data provider with a configured API key:

1. Call `zorivest_market(action: "test_provider", provider_name: "{name}")` → record success/fail
2. For each data type the provider supports (per ProviderCapabilities):
   - Call the corresponding MCP action (e.g., `action: "quote"`, `action: "ohlcv"`)
   - Validate response shape matches expected DTO fields
   - Record: provider, data_type, status, response_time, error
3. Test fallback chain: if primary fails, verify fallback provider responds

Exit: All configured providers tested; response shapes validated.
```

### New Phase 3b: Report Pipeline Validation

```markdown
### Phase 3b: Report Pipeline Validation

1. Create a test policy with fetch→transform→send chain:
   - FetchStep: quote data for AAPL from best available provider
   - TransformStep: field mapping + Pandera validation
   - StoreStep (if MEU-193 complete): persist to market_quotes table
2. Run policy with dry_run: true → verify PARSE+VALIDATE+SIMULATE pass
3. Verify pipeline_state_repo has cursor entry
4. Clean up: delete test policy

Exit: At least one end-to-end pipeline validates successfully.
```

### Updated Exit Criteria

Add to existing list:
- [ ] All configured providers respond to `test_provider` health check
- [ ] At least one provider returns valid data for each supported data type
- [ ] Pipeline dry-run completes for a fetch→transform chain (if pipeline MEUs complete)

---

## 6. Resolved Decision Gates

All decisions resolved `[Human-approved, 2026-05-01]`:

| Gate | Decision | Rationale |
|------|----------|-----------|
| D1: MEU Numbering | **MEU-182 through MEU-194** (13 MEUs) | Next available after MEU-181 |
| D2: Phase Naming | **Phase 8a — Market Data Expansion** | Sub-phase of Phase 8, consistent with 9a→9h pattern |
| D3: Database Tables | **Separate tables** (MarketDividends, MarketSplits, MarketEarnings, MarketInsider) | Query simplicity; each table has distinct column shapes |
| D4: Priority Level | **P1.5a** (after P1.5 Market Data, before P2 Planning) | Extends market data foundation before consuming layers |
| D5: Scope Gating | **Keep MEU-193/194 in P1.5a** | Pipeline runner works today without daemon; recipes use manual "Run Now" until Phase 10 |

---

## 7. Execution Task Table

| # | Task | owner_role | Deliverable | Validation | Status |
|---|------|------------|-------------|------------|--------|
| 1 | Remove Benzinga from `market-data-research-synthesis.md` | coder | Updated tables with Benzinga column removed | `rg -i benzinga _inspiration/.../market-data-research-synthesis.md` → 0 matches | `[ ]` |
| 2 | Remove Benzinga from `08-market-data.md` + update counts 14→13 | coder | Updated spec with 13 providers | `rg -i benzinga docs/build-plan/08-market-data.md` → 0 matches | `[ ]` |
| 3 | Remove Benzinga from `06f-gui-settings.md`, `06-gui.md`, `policy-authoring-guide.md`, `01a-logging.md` | coder | Updated downstream refs | `rg -i benzinga docs/build-plan/06f-gui-settings.md docs/build-plan/06-gui.md docs/guides/policy-authoring-guide.md docs/build-plan/01a-logging.md` → 0 matches | `[ ]` |
| 4 | Update `BUILD_PLAN.md` provider counts + `meu-registry.md` MEU-59 | coder | Consistent 13-provider count | `rg "14 market" docs/BUILD_PLAN.md` → 0 matches | `[ ]` |
| 5 | Create `08a-market-data-expansion.md` | coder | New Phase 8a spec | `Test-Path docs/build-plan/08a-market-data-expansion.md` → True | `[ ]` |
| 6 | Update `build-priority-matrix.md` — add P1.5a + fix header count | coder | 13 new items + "234 items" header | `rg "221 items" docs/build-plan/build-priority-matrix.md` → 0 matches | `[ ]` |
| 7 | Update `BUILD_PLAN.md` — add Phase 8a row + 13 MEU entries | coder | Phase 8a visible in index | `rg "Phase 8a" docs/BUILD_PLAN.md` → ≥1 match | `[ ]` |
| 8 | Update `meu-registry.md` — add MEU-182→194 | coder | 13 new entries | `rg "MEU-194" .agent/context/meu-registry.md` → ≥1 match | `[ ]` |
| 9 | Create `.agent/skills/mcp-rebuild/SKILL.md` | coder | New skill file | `Test-Path .agent/skills/mcp-rebuild/SKILL.md` → True | `[ ]` |
| 10 | Update `.agent/skills/mcp-audit/SKILL.md` — add Phases 3a/3b + fix `/ 12` → `/ 13` | coder | Updated audit skill | `rg "/ 12" .agent/skills/mcp-audit/SKILL.md` → 0 matches AND `rg "Phase 3a" .agent/skills/mcp-audit/SKILL.md` → ≥1 match | `[ ]` |
| 11 | Update `.agent/workflows/mcp-audit.md` — add Steps 4a/4b + fix `/ 12` → `/ 13` | coder | Updated audit workflow | `rg "/ 12" .agent/workflows/mcp-audit.md` → 0 matches AND `rg "Step 4a" .agent/workflows/mcp-audit.md` → ≥1 match | `[ ]` |
| 12 | Cross-doc sweep: verify no stale Benzinga/count refs remain | tester | Clean `rg` output | `rg -i "benzinga" docs .agent` → only historical refs in `docs/execution/plans/` | `[ ]` |
| 13 | Save session state to pomera_notes | orchestrator | `Memory/Session/Zorivest-market-data-expansion-doc-2026-05-01` | `pomera_notes(action="search", search_term="market-data-expansion*")` → ≥1 | `[ ]` |
| 14 | Create handoff | reviewer | `.agent/context/handoffs/` updated | `Test-Path` → True | `[ ]` |
