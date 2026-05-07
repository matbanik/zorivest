---
project: "2026-05-05-api-surface-pipeline-automation"
date: "2026-05-05"
source: "docs/build-plan/08a-market-data-expansion.md §8a.11–8a.13 + corrective (capability wiring)"
meus: ["MEU-192", "MEU-193", "MEU-194", "MEU-207"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Phase 8a Layer 5–6 — API Surface + Pipeline Automation + Capability Wiring

> **Project**: `2026-05-05-api-surface-pipeline-automation`
> **Build Plan Section(s)**: 08a-market-data-expansion.md §Step 8a.11 (Routes+MCP), §Step 8a.12 (Store Step), §Step 8a.13 (Scheduling Recipes), §corrective 30.15 (Capability Wiring)
> **Status**: `draft`

---

## Goal

Complete the final 3 implementation MEUs of Phase 8a by wiring the 8 service methods from Layer 4 (MEU-190/191) to REST endpoints and MCP tool actions (MEU-192), creating a pipeline step for persisting market data to DB tables (MEU-193), and seeding 10 pre-built scheduling recipe policies (MEU-194). MEU-207 is a corrective MEU (matrix 30.15) that closes a cross-layer wiring gap: injecting the existing `NORMALIZERS` registry into the `MarketDataService` constructor and updating `provider_capabilities.py` `supported_data_types` to match the implemented normalizer coverage. This completes the full data pipeline: fetch → normalize → expose via API/MCP → persist → schedule.

---

## Resolved Design Decisions

> [!NOTE]
> The following spec divergences have been resolved. Each divergence is documented with its source classification.

1. **Pandera → Pydantic validators** `[Research-backed]`: Build plan §8a.12 specifies Pandera validation. Pandera is not in `pyproject.toml` and would be a new dependency solely for tabular validation that Pydantic already covers. **Resolution:** Use per-table Pydantic `BaseModel` validators that enforce identical constraints (field types, ranges, non-null). Pandera's added value (statistical checks, pandas-native validation) is unnecessary for row-level DTO validation. The Pydantic ecosystem is already the project's validation standard (`extra="forbid"`, Field constraints). This is a tool substitution, not a scope reduction.
2. **Alembic → seed script** `[Local Canon]`: Build plan §8a.13 says "seeded via Alembic migration." Alembic is not configured in this project — all schema changes use `Base.metadata.create_all()` (Local Canon established in Phase 8). **Resolution:** Create `tools/seed_scheduling_recipes.py` that inserts 10 PolicyDocument records via the existing scheduling service layer. Recipes are inserted with `approved=false` (human-in-the-loop gate preserved). Idempotent by policy name.
3. **Options chain recipe #9** `[Human-approved]`: The build plan includes a "Daily options chain" recipe (Tradier/Polygon). No `get_options_chain()` service method exists yet. **Resolution:** Create the recipe with `enabled=false` and a note that the options service method is a future MEU. The recipe structure validates against PolicyDocument but won't execute until the service is wired. User approved this approach during plan review.

---

## Proposed Changes

### MEU-192 — REST Routes + MCP Actions (`market-routes-mcp`)

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| REST query params | Pydantic `MarketDataExpansionParams` | ticker: 1-10 chars upper+dot; interval: enum; dates: ISO 8601; limit: 1-1000 | `extra="forbid"` |
| MCP tool input | Zod `.strict()` on zorivest_market inputSchema | Same constraints via Zod `.regex()`, `.enum()`, `.int().min().max()` | `.strict()` |
| Provider API responses | Per-provider extractors (Layer 3) | `extra="allow"` | Malformed → logged warning + empty result |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | 8 new GET endpoints return correct DTOs from service methods | Spec §8a.11 | Missing ticker → 422; provider not found → 404 |
| AC-2 | `MarketDataExpansionParams` rejects extra fields with 422 | Spec §8a.11 BIC | Extra field `foo=bar` → 422 |
| AC-3 | `ticker` field validates 1-10 chars uppercase alpha + dot | Spec §8a.11 field constraints | Empty ticker → 422; `TOOLONG12345` → 422 |
| AC-4 | `interval` field validates against enum set | Spec §8a.11 field constraints | `interval=2h` → 422 |
| AC-5 | `start_date` must be ≤ `end_date` when both provided | Spec §8a.11 field constraints | start > end → 422 |
| AC-6 | Service errors map to 502, not 500 | Spec §8a.11 error mapping | Provider timeout → 502 |
| AC-7 | 8 new MCP actions added to `zorivest_market` with `.strict()` schemas | Spec §8a.11 + M1, M2 | Invalid action → MCP error |
| AC-8 | MCP description includes workflow, prerequisite, returns, errors | M7 standard | Grep for ≥3 of 4 markers |
| AC-9 | OpenAPI spec regenerated without drift | G8 standard | `--check` passes |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 8 endpoint paths and response types | Spec | Table in §8a.11 |
| Query parameter validation rules | Spec | Field constraints table in §8a.11 |
| Error mapping (422/404/502) | Spec | BIC in §8a.11 |
| Provider passthrough (optional) | Local Canon | Follows existing `/quote` endpoint pattern |
| Interval enum values | Spec | `1m,5m,15m,30m,1h,1d,1w,1M` |
| MCP tool description format | Local Canon (M7) | Emerging standards G |
| Query params model name `MarketDataExpansionParams` | Local Canon | Build-plan §8a.11 uses `MarketDataQueryParams`; renamed to `MarketDataExpansionParams` to distinguish from existing base market data params and scope to expansion endpoints only. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/routes/market_data.py` | modify | Add 8 new GET endpoints + `MarketDataExpansionParams` model |
| `mcp-server/src/compound/market-tool.ts` | modify | Add 8 new action routes + extend schema + update description |
| `tests/unit/test_market_routes.py` | new | Tests for 8 new endpoints (query validation, error mapping) |
| `mcp-server/tests/compound/market-tool.test.ts` | modify | Extend existing test file with 8 new MCP action tests |
| `openapi.committed.json` | modify | Regenerated spec |

---

### MEU-193 — Market Data Store Step (`market-store-step`)

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Pipeline `steps[].params` (build-plan says `steps[].config`; local code uses `PolicyStep.params` — resolved as Local Canon) | Pydantic `MarketDataStoreConfig` | data_type: enum; write_mode: enum; batch_size: 1-5000; ticker: 1-10 chars | `extra="forbid"` |
| DTO → SQLAlchemy write | Column constraints (Numeric, DateTime, String) | Extra columns rejected | Constraint violation → logged error + skip row |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `MarketDataStoreStep` registered in step registry as `market_data_store` | Spec §8a.12 | Unknown step type → policy validation error |
| AC-2 | Config validates data_type against enum (ohlcv, earnings, dividends, splits, insider, fundamentals) | Spec §8a.12 | `data_type=invalid` → VALIDATE error |
| AC-3 | Auto-mapping resolves data_type to correct target table | Spec §8a.12 | ohlcv → market_ohlcv, earnings → market_earnings, etc. |
| AC-4 | INSERT mode writes new rows without dedup | Spec §8a.12 | Duplicate rows both persisted |
| AC-5 | UPSERT mode deduplicates by ticker+timestamp/date | Spec §8a.12 | Duplicate row → existing row updated |
| AC-6 | Per-table validators reject malformed data before write | Spec §8a.12 (Pandera → Pydantic) | Missing required field → logged error + skip row |
| AC-7 | `batch_size` controls write commit frequency | Spec §8a.12 | 5 records with batch_size=2 → 3 commits |
| AC-8 | Extra fields in config rejected | Spec §8a.12 BIC | `extra_field=true` → VALIDATE error |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Step type name and config schema | Spec | §8a.12 |
| INSERT vs UPSERT semantics | Spec | §8a.12 |
| Data validation before write | Spec → Research-backed | Pandera not available → use Pydantic validators (same constraints) |
| Target table auto-mapping | Spec | §8a.12 |
| DbWriteAdapter pattern | Spec | Reuse existing `DbWriteAdapter` (`packages/infrastructure/src/zorivest_infra/adapters/db_write_adapter.py`) |
| Config field path `steps[].config` vs `PolicyStep.params` | Local Canon | Build-plan §8a.12 says `steps[].config`; local code (`pipeline.py:81`, `pipeline_runner.py:314`) uses `PolicyStep.params`. Resolved to match executable local canon. |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/core/src/zorivest_core/pipeline_steps/market_data_store_step.py` | new | MarketDataStoreStep + MarketDataStoreConfig |
| `packages/core/src/zorivest_core/pipeline_steps/__init__.py` | modify | Export new step |
| `packages/core/src/zorivest_core/domain/step_registry.py` | modify | Register `market_data_store` type |
| `packages/core/src/zorivest_core/domain/enums.py` | modify | Add `market_data_store` to StepType if needed |
| `tests/unit/test_market_data_store_step.py` | new | Config validation, table mapping, write modes |

---

### MEU-194 — Scheduling Recipes (`scheduling-recipes`)

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| Policy JSON structure | Pydantic `PolicyDocument` | All PolicyDocument rules | `extra="forbid"` |
| Seed script input | Hardcoded in script | N/A (no external input) | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | 10 scheduling recipes defined with correct cron, provider, fallback per spec | Spec §8a.13 | Recipe content matches build plan table |
| AC-2 | All 10 recipes pass PolicyDocument validation | Spec + G22 | Malformed recipe → validation error |
| AC-3 | Recipes seeded with `approved=false` (human-in-the-loop) | Local Canon | No recipe auto-approved |
| AC-4 | Recipes use `schema_version: 2` for query/compose steps where needed | Local Canon | Schema version mismatch → validation error |
| AC-5 | Seed script is idempotent (re-running doesn't create duplicates) | Local Canon | Run twice → same 10 records |
| AC-6 | Recipe #9 (options chain) created with `enabled=false` | Human-approved | Step references unimplemented service → disabled by default |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| 10 recipe definitions (cron, provider, fallback) | Spec | §8a.13 table |
| Seeding mechanism | Local Canon | Alembic not available → Python seed script via service layer |
| Approval state | Local Canon | `approved=false` per human-in-the-loop policy |
| Idempotency | Local Canon | Dedup by recipe name on insert |
| Options chain recipe | Human-approved | `enabled=false` pending service method |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `tools/seed_scheduling_recipes.py` | new | 10 PolicyDocument definitions + seed logic |
| `tests/unit/test_scheduling_recipes.py` | new | Recipe validation, idempotency, approval state |

---

### MEU-207 — Capability Mapping Enrichment (`capability-wiring`)

#### Problem Statement

The `NORMALIZERS` registry in `normalizers.py` (lines 861-902) contains fully implemented normalizer functions for 8 data types across 14 provider×type combinations. However, the `MarketDataService` constructor in `main.py` (line 292-301) never injects this registry — the `normalizers=` kwarg is omitted. Additionally, `provider_capabilities.py` `supported_data_types` tuples only list a subset of what each provider actually supports per the research consensus matrix.

This means: expansion data types (earnings, fundamentals, dividends, splits, insider, economic_calendar, company_profile) fall back to Yahoo-only or return 502 "No provider available" even when normalizers exist.

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| `main.py` constructor kwarg | Python dict type annotation | Keys must be valid data_type strings; values must be `dict[str, Callable]` | Type-checked at runtime |
| `provider_capabilities.py` | `ProviderCapabilities` frozen dataclass | `supported_data_types` must be `tuple[str, ...]` with valid data type names | Frozen dataclass — immutable after construction |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `NORMALIZERS` dict injected as `normalizers=` kwarg in `MarketDataService()` constructor in `main.py` | Research §7 + Local Canon (normalizers.py L861) | Service with `normalizers=None` → expansion data types return 502 |
| AC-2 | `provider_capabilities.py` `supported_data_types` updated to match Expected Capability Tuples table below | Local Canon (derived from NORMALIZERS registry) | Missing data_type in tuple → provider skipped for that type |
| AC-3 | Every key in `NORMALIZERS` dict has a matching entry in `supported_data_types` for that provider | Local Canon (alignment invariant) | Normalizer exists but capability not advertised → dead code |
| AC-4 | Existing Yahoo-first data types (ohlcv, fundamentals, dividends, splits) still work with Yahoo fallback + API-key chain | Regression | Yahoo failure → API-key provider succeeds |

> **Inclusion rule**: MEU-207 updates `supported_data_types` only for providers that have at least one entry in the `NORMALIZERS`, `QUOTE_NORMALIZERS`, `NEWS_NORMALIZERS`, or `SEARCH_NORMALIZERS` registries, or have a dedicated service-level normalizer (e.g., `sec_normalizer`). Providers with no entry in any normalizer registry are **not touched** by MEU-207 — their existing `supported_data_types` from MEU-184 are preserved as-is. Data types claimed by the research matrix but lacking runtime normalizer support are NOT advertised — they represent future work.

#### Expected Capability Tuples — MEU-207 Scope (Normalizer-Derived)

These tuples are **set by MEU-207** based on cross-referencing `normalizers.py` registries (L233-248, L861-902) with dedicated service paths:

| Provider | Expected `supported_data_types` | Sources |
|----------|--------------------------------|--------|
| Alpha Vantage | `("earnings", "economic_calendar", "fundamentals", "quote", "ticker_search")` | NORMALIZERS[earnings/econ_cal/fundamentals], QUOTE_NORMALIZERS, SEARCH_NORMALIZERS |
| Polygon.io | `("dividends", "ohlcv", "quote", "splits")` | NORMALIZERS[ohlcv/dividends/splits], QUOTE_NORMALIZERS |
| Finnhub | `("company_profile", "earnings", "economic_calendar", "insider", "news", "quote")` | NORMALIZERS[earnings/econ_cal/insider/company_profile], QUOTE_NORMALIZERS, NEWS_NORMALIZERS |
| Financial Modeling Prep | `("company_profile", "dividends", "earnings", "economic_calendar", "fundamentals", "insider", "splits", "ticker_search")` | NORMALIZERS[all 8 types], SEARCH_NORMALIZERS |
| EODHD | `("company_profile", "dividends", "fundamentals", "ohlcv", "quote", "splits")` | NORMALIZERS[ohlcv/fundamentals/dividends/splits/company_profile], QUOTE_NORMALIZERS |
| SEC API | `("insider", "sec_filings")` | NORMALIZERS[insider], dedicated `sec_normalizer` constructor arg (L113) |
| API Ninjas | `("quote",)` | QUOTE_NORMALIZERS only |
| Alpaca | `("ohlcv",)` | NORMALIZERS[ohlcv] only |

#### Unchanged Providers (MEU-184 Carry-Forward — Not Modified by MEU-207)

These providers have no entry in any normalizer registry. Their existing `supported_data_types` from MEU-184 are preserved without modification:

| Provider | Existing `supported_data_types` | Rationale |
|----------|--------------------------------|-----------|
| Nasdaq Data Link | `("fundamentals",)` | Structural dataset provider — no normalizer-based dispatch; existing MEU-184 value |
| OpenFIGI | `("identifier_mapping",)` | Dedicated POST-body identifier resolver — no normalizer-based dispatch; existing MEU-184 value |
| Tradier | `("ohlcv", "quote")` | No normalizer in any registry — existing MEU-184 value preserved |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Normalizer injection pattern | Local Canon | Follow existing `quote_normalizers=QUOTE_NORMALIZERS` pattern in `main.py` |
| Capability tuple data | Local Canon | Derived from normalizer registries in `normalizers.py` (L233-248, L861-902) |
| Provider fallback chain priority | Research §2 | Best-source recommendations table |
| Yahoo-first behavior preserved | Local Canon | `_YAHOO_DATA_TYPES` frozenset in `market_data_service.py` |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `packages/api/src/zorivest_api/main.py` | modify | Add `normalizers=NORMALIZERS` kwarg to `MarketDataService()` constructor (1 line + 1 import) |
| `packages/infrastructure/src/zorivest_infra/market_data/provider_capabilities.py` | modify | Update `supported_data_types` tuples for 8 normalizer-backed providers to match normalizer registry coverage; 3 structural providers unchanged |
| `tests/unit/test_capability_wiring.py` | new | Verify normalizer injection, capability-normalizer alignment, expansion data type dispatch |

---

### Ad-Hoc Pipeline Hardening (Post-MEU, 2026-05-05/06)

> [!NOTE]
> The following fixes were discovered during live pipeline testing after MEU-192/193/194/207 were complete. They are not part of any MEU scope but are critical production hardening for the pipeline end-to-end flow.

#### AH-1: ComposeStep Resilience (compose_step.py)

**Problem**: When an optional upstream step fails with `on_error="log_and_continue"`, its output is never stored. ComposeStep's `context.get_output(step_id)` then raises `KeyError`, crashing the entire pipeline.

**Fix**: Wrapped `get_output()` in try/except KeyError — missing sources are skipped with a structured `compose_step.source_missing` warning log. Pipeline continues with partial data.

**Files**: `compose_step.py` L72-82, `test_compose_step.py` AC-5.4

#### AH-2: Bytes Serialization Fix (secure_jinja.py, template_engine.py)

**Problem**: Some provider HTTP responses contain `bytes` objects in their decoded JSON (httpx returns bytes for certain content types). When Jinja2's `|tojson` filter serializes these, Python's `json.dumps()` raises `TypeError: Object of type bytes is not JSON serializable`.

**Fix**: Created `_pipeline_safe_dumps()` (secure_jinja.py L107-129) with a custom `default` handler that decodes `bytes → str` (UTF-8) and `datetime → ISO 8601`. Registered as `env.policies['json.dumps_function']` in both `HardenedSandbox` and the infrastructure `template_engine.py`.

**Files**: `secure_jinja.py` L107-129+L151, `template_engine.py` L42-44

#### AH-3: API Key Name Mismatch (market_data_adapter.py)

**Problem**: The adapter's `_resolve_headers()` and `_inject_query_param_key()` used `config.name` (display name, e.g., "Massive") to look up API keys in the database. But keys are stored under the canonical registry key (e.g., "Polygon.io"). This caused `None` key lookups → HTTP 401 on every Polygon/Massive request.

**Fix**: Both methods now accept the registry `provider_key` string and use it for API key lookup, falling back to `config.name` for backward compatibility. All 4 call sites in `fetch()` and `_fetch_multi_ticker()` updated.

**Files**: `market_data_adapter.py` L133, L149, L347-401

#### AH-4: Alpaca Connection Validator (provider_connection_service.py)

**Problem**: The Alpaca test endpoint in the registry is `/v2/stocks/AAPL/snapshot` on `data.alpaca.markets` (Market Data API), which returns `{"latestTrade": {...}, "latestQuote": {...}}`. But `_validate_alpaca()` checked for `"id"` — the Trading API `/v2/account` response shape. No `"id"` key exists → "Connected but unexpected response".

**Fix**: Updated `_validate_alpaca()` to check for `latestTrade` or `latestQuote` keys instead of `id`. Also preserves `"code" not in data` check for auth errors.

**Files**: `provider_connection_service.py` L203-213

#### AH-5: Alpaca Test Suite Update (test_provider_connection_service.py)

**Problem**: `TestAlpacaValidation` class tested against the old `{"id": "acct-123"}` response shape, which no longer matches the validator.

**Fix**: Updated 3 existing tests + added 1 new test (`test_quote_only_response`) to match the snapshot response shape. All 45 tests pass.

**Files**: `test_provider_connection_service.py` TestAlpacaValidation class (4 tests)

#### AH-6: Email Template v3 (full-fundamentals-research DB template)

**Problem**: Pipeline email rendered raw JSON for Key Fundamentals (Alpha Vantage), Dividends (Polygon), Earnings (Finnhub). Each provider wraps data in different envelopes (`{"results":[...]}`, `{"historical":[...]}`, `{"data":[...]}`) that were not unwrapped before template rendering.

**Fix**: Updated the email template with:
- Envelope unwrapping for Polygon/FMP/Finnhub response structures
- `is defined` guards for all optional sections (compose skip support)
- Error card for Alpha Vantage API key issues
- Provider label update "Massive (Polygon.io)"

**Files**: `full-fundamentals-research` email template (stored in DB, updated via API)

---

## Out of Scope


- GUI views for the 8 new market data endpoints (future GUI MEU)
- `get_options_chain()` service method (future MEU; recipe #9 created disabled)
- Alembic migration infrastructure setup
- Pandera dependency installation (using Pydantic validators instead)
- Provider-specific rate limiting enhancements
- Economic calendar country routing beyond US default

---

## BUILD_PLAN.md Audit

After execution:
- MEU-207 row added to Phase 8a section in `docs/BUILD_PLAN.md` with matrix ref `30.15`
- MEU-207 row added to `docs/build-plan/build-priority-matrix.md` as `30.15`
- Phase 8a completion count updates from `15/15` to `16/16` (corrective MEU)
- MEU-192, 193, 194 remain `✅`; MEU-207 marked `✅` on completion

Validation:

```powershell
rg "MEU-207" docs/BUILD_PLAN.md  # Expected: 1 row with 30.15
rg "30.15" docs/build-plan/build-priority-matrix.md  # Expected: 1 row
```

---

## Verification Plan

### 1. Python Type Checks
```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 2. Python Lint
```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 3. Python Tests
```powershell
uv run pytest tests/ -x --tb=short -v *> C:\Temp\zorivest\pytest.txt; Get-Content C:\Temp\zorivest\pytest.txt | Select-Object -Last 40
```

### 4. OpenAPI Spec Check
```powershell
uv run python tools/export_openapi.py --check openapi.committed.json *> C:\Temp\zorivest\openapi.txt; Get-Content C:\Temp\zorivest\openapi.txt
```

### 5. MCP Server Build
```powershell
cd mcp-server; npm run build *> C:\Temp\zorivest\mcp-build.txt; Get-Content C:\Temp\zorivest\mcp-build.txt | Select-Object -Last 10
```

### 6. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" packages/ *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```

### 7. MEU Gate
```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

---

## Open Questions

None — all spec divergences resolved in [Resolved Design Decisions](#resolved-design-decisions) above.

---

## Research References

- [08a-market-data-expansion.md](file:///p:/zorivest/docs/build-plan/08a-market-data-expansion.md) — Primary spec for all 3 MEUs
- [p1.5a-meu-grouping-proposal.md](file:///p:/zorivest/_inspiration/data-provider-api-expansion-research/p1.5a-meu-grouping-proposal.md) — MEU grouping rationale
- [market-data-research-synthesis.md](file:///p:/zorivest/_inspiration/data-provider-api-expansion-research/market-data-research-synthesis.md) — Provider research
- [M2 (API ↔ MCP Parity)](file:///p:/zorivest/.agent/docs/emerging-standards.md) — Emerging standard
- [M7 (Tool Description Workflow Context)](file:///p:/zorivest/.agent/docs/emerging-standards.md) — Emerging standard
- [G8 (OpenAPI Spec Regen)](file:///p:/zorivest/.agent/docs/emerging-standards.md) — Emerging standard
