# Pipeline Steps — MEU-85 / MEU-86 / MEU-87

Implement the four concrete pipeline step types (FetchStep, TransformStep, StoreReportStep, RenderStep) plus their supporting infrastructure (CriteriaResolver, PipelineRateLimiter, HTTP cache, field mappings, Pandera validation, write dispositions, precision utils, ReportSpec DSL, SQL sandbox, Jinja2 templates, Plotly charts, Playwright PDF).

- **Project slug**: `2026-03-15-pipeline-steps`
- **Build-plan sections**: [09-scheduling.md](../../build-plan/09-scheduling.md) §9.4, §9.5, §9.6, §9.7
- **Handoffs**: 070 (MEU-85), 071 (MEU-86), 072 (MEU-87)

---

## Spec Sufficiency

All behaviors resolved from [09-scheduling.md](../../build-plan/09-scheduling.md). No human decision gates.

| Behavior | Source | Resolved? |
|----------|--------|-----------|
| FetchStep auto-registration, Params model, execute() | Spec §9.4a | ✅ |
| CriteriaResolver (relative/incremental/db_query) | Spec §9.4b | ✅ |
| PipelineRateLimiter (aiolimiter + tenacity + semaphore) | Spec §9.4c | ✅ |
| FetchResult provenance envelope + SHA-256 | Spec §9.4d | ✅ |
| HTTP cache revalidation (ETag/If-Modified-Since) | Spec §9.4e | ✅ |
| Freshness TTL per data type + is_market_closed() | Spec §9.4f | ✅ |
| TransformStep: field mapping + write dispositions | Spec §9.5a–d | ✅ |
| Pandera validation gate (OHLCV schema) | Spec §9.5c | ✅ |
| Financial precision (to_micros/from_micros) | Spec §9.5e | ✅ |
| StoreReportStep: sandboxed SQL, snapshot hash | Spec §9.6a+c | ✅ |
| ReportSpec DSL (DataTable/MetricCard/Chart) | Spec §9.6b | ✅ |
| RenderStep: Jinja2 + Plotly + Playwright PDF | Spec §9.7a–d | ✅ |
| Playwright PDF rendering | Research-backed | ✅ Auto-downloads Chromium; no system deps (GTK/Pango) needed. Apache 2.0 license |
| Kaleido for Plotly static PNG | Research-backed | ✅ Kaleido v1 needs Chrome/Chromium on system; `engine` param deprecated in Plotly 6.2+ |

---

## Task Table

See [task.md](./task.md) for the canonical task / owner_role / deliverable / validation / status table.

---

## Proposed Changes

### Dependency Bootstrap

> Addresses review finding F1. Required before any MEU tests can run.

#### [MODIFY] [pyproject.toml](file:///p:/zorivest/packages/core/pyproject.toml)

- Add `pandera>=0.22` to `dependencies`

#### [MODIFY] [pyproject.toml](file:///p:/zorivest/packages/infrastructure/pyproject.toml)

- Add `aiolimiter>=1.2`, `httpx>=0.28`, `jinja2>=3.1`, `pandas>=2.2`, `plotly>=6.0`, `tenacity>=9.0` to `dependencies`
- Add `[project.optional-dependencies] rendering` group: `kaleido>=1.0`, `playwright>=1.50`

> `kaleido` and `playwright` have Chromium dependencies. They are declared as optional `[rendering]` extras on the infrastructure package. Playwright auto-downloads Chromium via `playwright install chromium`. The rendering extras **must** be installed and verified before MEU-87 tests run — render-path tests are not skipped.

#### Environment Verification

```bash
# Core deps (required before MEU-85)
uv sync
uv run python -c "import pandera, aiolimiter, tenacity, jinja2, plotly, pandas; print('OK')"

# Rendering deps (required before MEU-87)
# NOTE: root pyproject.toml forwards rendering extra to zorivest-infra[rendering]
uv sync --extra rendering
uv run python -c "import playwright, kaleido; print('OK')"
uv run playwright install chromium   # Auto-downloads Chromium browser
uv run python -c "import plotly.graph_objects as go; fig = go.Figure(); fig.to_image(format='png'); print('Kaleido OK')"  # Proves Chrome/Chromium available
```

---

### MEU-85: FetchStep (`fetch-step`, matrix 44)

> Build-plan: [09-scheduling.md §9.4](../../build-plan/09-scheduling.md)

#### [NEW] [fetch_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py)

- `FetchStep(RegisteredStep)` with `type_name="fetch"`, `side_effects=False`
- `Params` Pydantic model: `provider`, `data_type`, `criteria`, `batch_size`, `use_cache`
- `execute()`: resolve criteria → check cache → call provider → return FetchResult envelope
- Integration with `CriteriaResolver` for dynamic criteria resolution
- Cache check via `FetchCacheRepository`

#### [NEW] [__init__.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/__init__.py)

- Eagerly imports all concrete step modules so `STEP_REGISTRY` is populated at import time:
  ```python
  from zorivest_core.pipeline_steps import fetch_step  # noqa: F401
  from zorivest_core.pipeline_steps import transform_step  # noqa: F401
  from zorivest_core.pipeline_steps import store_report_step  # noqa: F401
  from zorivest_core.pipeline_steps import render_step  # noqa: F401
  ```
- This ensures `get_step("fetch")` etc. work after `import zorivest_core.pipeline_steps`

#### [NEW] [criteria_resolver.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/criteria_resolver.py)

- `CriteriaResolver` class with 3 resolver types: `relative`, `incremental`, `db_query`
- `_resolve_relative()`: date math (e.g., `"today - 30d"`)
- `_resolve_incremental()`: high-water mark from `pipeline_state` table via `PipelineStateRepository`
- `_resolve_db_query()`: read-only SQL via sandboxed connection

#### [MODIFY] [scheduling_repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py)

- Add `PipelineStateRepository` class with `get(policy_id, provider_id, data_type, entity_key)` and `upsert(...)` methods
- Uses existing `PipelineStateModel` from `models.py:460`

#### [MODIFY] [unit_of_work.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/unit_of_work.py)

- Add `pipeline_state: PipelineStateRepository` attribute
- Import and instantiate in `__enter__`

#### [NEW] [pipeline_rate_limiter.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py)

- `PipelineRateLimiter` with `AsyncLimiter` per provider + global `Semaphore`
- `execute_with_limits()` with tenacity retry (exponential backoff + jitter)

#### [NEW] [http_cache.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/http_cache.py)

- `fetch_with_cache()`: ETag/If-Modified-Since revalidation, 304 handling

#### [MODIFY] [pipeline.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/pipeline.py)

- Append `FetchResult` dataclass with SHA-256 content hash
- Append `FRESHNESS_TTL` dict + `is_market_closed()` helper

#### [NEW] [test_fetch_step.py](file:///p:/zorivest/tests/unit/test_fetch_step.py)

Tests (TDD-first):
- AC-F1: FetchStep auto-registers with `type_name="fetch"`
- AC-F2: Params model validates required fields
- AC-F3: FetchResult computes SHA-256 content hash on init
- AC-F4: CriteriaResolver resolves relative dates (e.g., `-30d`)
- AC-F5: CriteriaResolver resolves incremental high-water marks
- AC-F6: FetchResult `cache_status` defaults to `"miss"`
- AC-F7: `FRESHNESS_TTL` has correct values for all 4 data types
- AC-F8: `is_market_closed()` returns True after 4 PM ET / weekends
- AC-F9: PipelineRateLimiter creates per-provider limiters
- AC-F10: HTTP cache returns `"revalidated"` on 304 response
- AC-F11: FetchStep with `use_cache=True` returns cache hit when available
- AC-F12: FetchStep Params rejects batch_size > 500 or < 1
- AC-F13: `uow.pipeline_state` attribute exists and returns `PipelineStateRepository`
- AC-F14: `PipelineStateRepository.get()` returns state or None
- AC-F15: After `import zorivest_core.pipeline_steps`, `get_step("fetch")` returns `FetchStep`

---

### MEU-86: TransformStep (`transform-step`, matrix 45)

> Build-plan: [09-scheduling.md §9.5](../../build-plan/09-scheduling.md)

#### [NEW] [transform_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py)

- `TransformStep(RegisteredStep)` with `type_name="transform"`, `side_effects=True`
- `Params`: mapping, write_disposition, target_table, validation_rules, quality_threshold
- `execute()`: apply mapping → validate → quality check → write data

#### [NEW] [field_mappings.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py)

- `FIELD_MAPPINGS` registry keyed by `(provider, data_type)`
- `apply_field_mapping()` with `_extra` key for unmapped fields

#### [NEW] [validation_gate.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py)

- `OHLCV_SCHEMA` Pandera schema
- `validate_dataframe()` returning `(valid, quarantined)` tuples

#### [NEW] [write_dispositions.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py)

- `TABLE_ALLOWLIST` for write security
- `write_append()`, `write_replace()`, `write_merge()` using SQLAlchemy Core

#### [NEW] [precision.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/precision.py)

- `to_micros()`, `from_micros()`, `parse_monetary()` — financial precision utilities

#### [NEW] [test_transform_step.py](file:///p:/zorivest/tests/unit/test_transform_step.py)

Tests (TDD-first):
- AC-T1: TransformStep auto-registers with `type_name="transform"`
- AC-T2: TransformStep Params validates required `target_table`
- AC-T3: `apply_field_mapping()` maps known fields + captures extras in `_extra`
- AC-T4: `apply_field_mapping()` returns empty dict for empty mapping
- AC-T5: `validate_dataframe()` passes all-valid OHLCV data
- AC-T6: `validate_dataframe()` quarantines invalid records (negative prices)
- AC-T7: Quality threshold < 0.8 → FAILED status
- AC-T8: `TABLE_ALLOWLIST` rejects unknown tables
- AC-T9: `_validate_columns()` rejects columns not in allowlist
- AC-T10: `to_micros()` / `from_micros()` round-trip precision
- AC-T11: `parse_monetary()` avoids float precision errors
- AC-T12: TransformStep `side_effects=True`
- AC-T13: Live UoW test: `write_append()` with in-memory SQLite creates rows

---

### MEU-87: StoreReportStep + RenderStep (`store-render-step`, matrix 46)

> Build-plan: [09-scheduling.md §9.6, §9.7](../../build-plan/09-scheduling.md)

#### [NEW] [store_report_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/store_report_step.py)

- `StoreReportStep(RegisteredStep)` with `type_name="store_report"`, `side_effects=True`
- Params: report_name, spec, data_queries
- Sandboxed SQL execution → snapshot hash → persist to ReportModel

#### [MODIFY] [scheduling_repositories.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py)

- Extend `ReportRepository.create()` to accept `snapshot_json` and `snapshot_hash` keyword args
- Persist those values to the existing `ReportModel` columns

#### [NEW] [report_spec.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/report_spec.py)

- `DataTableSection`, `MetricCardSection`, `ChartSection` Pydantic models
- `ReportSpec` Pydantic model with discriminated union sections

#### [NEW] [sql_sandbox.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py)

- `report_authorizer()` default-deny callback (SELECT/READ/FUNCTION only)
- `create_sandboxed_connection()` with `PRAGMA query_only`

#### [NEW] [render_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/render_step.py)

- `RenderStep(RegisteredStep)` with `type_name="render"`, `side_effects=True`
- Params: template, output_format, chart_settings
- Execute: render HTML via Jinja2 → render PDF via Playwright (optional)

#### [NEW] [template_engine.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/template_engine.py)

- `create_template_engine()` → Jinja2 Environment with `currency`/`percent` filters

#### [NEW] [chart_renderer.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/chart_renderer.py)

- `render_candlestick()` with dual output (HTML + static PNG)
- `CHART_RENDERERS` registry

#### [NEW] [pdf_renderer.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py)

- `render_pdf()` via Playwright headless Chromium (HTML → PDF file)

#### [NEW] [test_store_render_step.py](file:///p:/zorivest/tests/unit/test_store_render_step.py)

Tests (TDD-first):
- AC-SR1: StoreReportStep auto-registers with `type_name="store_report"`
- AC-SR2: RenderStep auto-registers with `type_name="render"`
- AC-SR3: ReportSpec model validates section types (discriminated union)
- AC-SR4: `DataTableSection` rejects max_rows > 1000
- AC-SR5: `report_authorizer()` allows SELECT
- AC-SR6: `report_authorizer()` denies INSERT/UPDATE/DELETE/DROP
- AC-SR7: `create_sandboxed_connection()` sets `query_only`
- AC-SR8: `create_template_engine()` registers currency/percent filters
- AC-SR9: StoreReportStep Params validates required fields
- AC-SR10: RenderStep Params defaults to `output_format="both"`
- AC-SR11: `render_candlestick()` returns dict with `html` and `png_data_uri` keys
- AC-SR12: `render_pdf()` creates output directory if missing
- AC-SR13: StoreReportStep and RenderStep both have `side_effects=True`
- AC-SR14: Live UoW test: `ReportRepository.create()` persists `snapshot_json` + `snapshot_hash`
- AC-SR15: `ReportRepository.create()` accepts and persists `snapshot_json` + `snapshot_hash`

---

### Post-MEU Deliverables

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Update Phase 9 status from ⚪ → 🟡 In Progress
- Update MEU-85/86/87 status to ✅ in the P2.5 table
- Update P2.5 completed count: 8 → 11
- Verify no stale references introduced

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

- Add MEU-85/86/87 rows to Phase 9 table with ✅ status
- Update execution order line

---

## Feature Intent Contracts (FIC)

### MEU-85: FetchStep

| AC | Criterion | Source |
|----|-----------|--------|
| AC-F1 | FetchStep registers as `type_name="fetch"` in STEP_REGISTRY | Spec §9.4a |
| AC-F2 | Params model requires `provider` and `data_type` | Spec §9.4a |
| AC-F3 | FetchResult computes SHA-256 content hash automatically | Spec §9.4d |
| AC-F4 | CriteriaResolver handles `relative` type with offset math | Spec §9.4b |
| AC-F5 | CriteriaResolver handles `incremental` type via pipeline_state | Spec §9.4b |
| AC-F6 | FetchResult defaults cache_status to "miss" | Spec §9.4d |
| AC-F7 | FRESHNESS_TTL: quote=3600, ohlcv=86400, news=900, fundamentals=86400 | Spec §9.4f |
| AC-F8 | `is_market_closed()` true after 4 PM ET and weekends | Spec §9.4f |
| AC-F9 | PipelineRateLimiter creates per-provider AsyncLimiter instances | Spec §9.4c |
| AC-F10 | HTTP 304 returns cached payload + "revalidated" status | Spec §9.4e |
| AC-F11 | Cache hit returns data without calling provider | Spec §9.4a |
| AC-F12 | batch_size constrained to [1, 500] | Spec §9.4a |
| AC-F13 | `uow.pipeline_state` attribute returns `PipelineStateRepository` | Spec §9.4b |
| AC-F14 | `PipelineStateRepository.get()` returns state or None | Spec §9.4b |
| AC-F15 | After `import zorivest_core.pipeline_steps`, `get_step("fetch")` returns FetchStep | Spec §9.4a |

### MEU-86: TransformStep

| AC | Criterion | Source |
|----|-----------|--------|
| AC-T1 | TransformStep registers as `type_name="transform"` | Spec §9.5a |
| AC-T2 | Params model requires `target_table` | Spec §9.5a |
| AC-T3 | Field mapping translates provider keys → canonical + extras in `_extra` | Spec §9.5b |
| AC-T4 | Empty mapping → empty output dict | Spec §9.5b |
| AC-T5 | Pandera OHLCV_SCHEMA validates clean data without errors | Spec §9.5c |
| AC-T6 | Invalid records (negative prices) are quarantined, not passed through | Spec §9.5c |
| AC-T7 | Quality below threshold → FAILED StepResult | Spec §9.5a |
| AC-T8 | TABLE_ALLOWLIST rejects unknown table names with ValueError | Spec §9.5d |
| AC-T9 | Column allowlist rejects disallowed columns | Spec §9.5d |
| AC-T10 | `to_micros(Decimal("1.234567"))` → 1234567, `from_micros(1234567)` → Decimal("1.234567") | Spec §9.5e |
| AC-T11 | `parse_monetary(1.1 + 2.2)` avoids float error; result ≈ 3.3 | Spec §9.5e |
| AC-T12 | TransformStep has `side_effects=True` | Spec §9.5a |
| AC-T13 | Live UoW `write_append()` creates rows in in-memory SQLite | Local Canon |

### MEU-87: StoreReportStep + RenderStep

| AC | Criterion | Source |
|----|-----------|--------|
| AC-SR1 | StoreReportStep registers as `type_name="store_report"` | Spec §9.6a |
| AC-SR2 | RenderStep registers as `type_name="render"` | Spec §9.7a |
| AC-SR3 | ReportSpec validates discriminated union of section types | Spec §9.6b |
| AC-SR4 | DataTableSection rejects max_rows > 1000 | Spec §9.6b |
| AC-SR5 | SQL authorizer allows SQLITE_SELECT | Spec §9.6c |
| AC-SR6 | SQL authorizer denies INSERT/UPDATE/DELETE/DROP | Spec §9.6c |
| AC-SR7 | Sandboxed connection sets PRAGMA query_only | Spec §9.6c |
| AC-SR8 | Template engine registers currency + percent Jinja2 filters | Spec §9.7b |
| AC-SR9 | StoreReportStep Params requires report_name + spec | Spec §9.6a |
| AC-SR10 | RenderStep Params defaults output_format to "both" | Spec §9.7a |
| AC-SR11 | Candlestick renderer returns dict with `html` and `png_data_uri` | Spec §9.7c |
| AC-SR12 | PDF renderer creates output directory if missing | Spec §9.7d |
| AC-SR13 | Both steps have `side_effects=True` | Spec §9.6a, §9.7a |
| AC-SR14 | Live UoW `ReportRepository.create()` persists `snapshot_json`/`snapshot_hash` | Local Canon |
| AC-SR15 | `ReportRepository.create()` accepts `snapshot_json` + `snapshot_hash` kwargs | Spec §9.6a |

---

## Verification Plan

### Automated Tests

All tests use the existing `uv run pytest` infrastructure. No `pytest-asyncio` — use `asyncio.run()` wrapper per project convention.

```bash
# MEU-85 tests
uv run pytest tests/unit/test_fetch_step.py -v

# MEU-86 tests
uv run pytest tests/unit/test_transform_step.py -v

# MEU-87 tests
uv run pytest tests/unit/test_store_render_step.py -v

# Full regression
uv run pytest tests/ -v

# Type checking
uv run pyright packages/core/src/zorivest_core/pipeline_steps/
uv run pyright packages/core/src/zorivest_core/domain/precision.py
uv run pyright packages/core/src/zorivest_core/domain/report_spec.py

# Lint
uv run ruff check packages/core/src/zorivest_core/pipeline_steps/
uv run ruff check packages/infrastructure/src/zorivest_infra/

# MEU gate
uv run python tools/validate_codebase.py --scope meu
```

### Test Strategy Notes

- **FetchStep**: Mock `CriteriaResolver` and `FetchCacheRepository` — test the step's orchestration logic, not HTTP calls
- **TransformStep**: Test field mapping and validation with real Pandera schemas. Include at least one live UoW test for `write_append()` with in-memory SQLite (AC-T13)
- **StoreReportStep**: Test SQL sandbox authorizer with real sqlite3 connection. Include at least one live UoW test for `ReportRepository.create()` with `snapshot_json`/`snapshot_hash` (AC-SR14)
- **RenderStep**: Test template engine creation, chart renderer output structure. Rendering extras (`kaleido`, `playwright`) must be installed before MEU-87 tests run (see Dependency Bootstrap). No `importorskip` — render tests fail if deps missing
- **Precision utils**: Pure function tests with exact Decimal comparisons
- **Step registration**: At least one test that `import zorivest_core.pipeline_steps` then verifies all 4 types in `STEP_REGISTRY` (AC-F15)

### Carry-Forward Rules (from latest reflection)

1. Always include a live UoW test for any step that interacts with persistence
2. Keep plan–contract alignment tight — no `asyncio.to_thread` claims unless actually used
3. Complete post-MEU deliverables promptly within the same session
