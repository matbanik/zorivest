---
meu: 87
slug: store-render-step
phase: 9
priority: P1
status: ready_for_review
agent: antigravity
iteration: 1
files_changed: 10
tests_added: 15
tests_passing: 15
---

# MEU-87: StoreReportStep + RenderStep

## Scope

Implements StoreReportStep and RenderStep — the report persistence and rendering pipeline stages. Includes ReportSpec DSL (discriminated union of DataTable/MetricCard/Chart sections), SQL sandbox with default-deny authorizer, Jinja2 template engine with financial filters, Plotly candlestick chart renderer with dual output (HTML + PNG), Playwright-based PDF rendering, and ReportRepository snapshot persistence.

Build plan reference: [09-scheduling.md §9.6, §9.7](file:///p:/zorivest/docs/build-plan/09-scheduling.md)

## Feature Intent Contract

### Intent Statement
The report storage and rendering stages that persist report snapshots and produce HTML/PDF output with charts, templates, and security-sandboxed SQL queries.

### Acceptance Criteria
- AC-SR1: StoreReportStep auto-registers with type_name="store_report"
- AC-SR2: RenderStep auto-registers with type_name="render"
- AC-SR3: ReportSpec validates all 3 discriminated union section types
- AC-SR4: DataTableSection rejects max_rows > 1000
- AC-SR5: report_authorizer allows SELECT (action code 21)
- AC-SR6: report_authorizer denies INSERT/UPDATE/DELETE/DROP (action codes 18, 23, 9, 11)
- AC-SR7: create_sandboxed_connection sets PRAGMA query_only = 1
- AC-SR8: create_template_engine registers currency ($1,234.57) and percent (12.34%) filters
- AC-SR9: StoreReportStep Params validates report_name required
- AC-SR10: RenderStep Params defaults output_format to "both"
- AC-SR11: render_candlestick returns html + valid PNG data URI (prefix + payload > 100 chars)
- AC-SR12: render_pdf creates output directory, produces PDF file with non-zero size (Playwright)
- AC-SR13: Both steps declare side_effects=True
- AC-SR14: Live UoW: ReportRepository.create() persists snapshot_json and snapshot_hash
- AC-SR15: ReportRepository.create() accepts and round-trips snapshot fields

### Negative Cases
- Must NOT: Allow INSERT/UPDATE/DELETE/DROP through the SQL authorizer
- Must NOT: Accept max_rows > 1000 on DataTableSection

### Test Mapping
| Criterion | Test File | Test Function |
|-----------|-----------|---------------|
| AC-SR1 | `tests/unit/test_store_render_step.py` | `test_AC_SR1_store_report_step_auto_registers` |
| AC-SR2 | `tests/unit/test_store_render_step.py` | `test_AC_SR2_render_step_auto_registers` |
| AC-SR3 | `tests/unit/test_store_render_step.py` | `test_AC_SR3_report_spec_validates_sections` |
| AC-SR4 | `tests/unit/test_store_render_step.py` | `test_AC_SR4_data_table_max_rows_limit` |
| AC-SR5 | `tests/unit/test_store_render_step.py` | `test_AC_SR5_authorizer_allows_select` |
| AC-SR6 | `tests/unit/test_store_render_step.py` | `test_AC_SR6_authorizer_denies_writes` |
| AC-SR7 | `tests/unit/test_store_render_step.py` | `test_AC_SR7_sandboxed_connection_query_only` |
| AC-SR8 | `tests/unit/test_store_render_step.py` | `test_AC_SR8_template_engine_filters` |
| AC-SR9 | `tests/unit/test_store_render_step.py` | `test_AC_SR9_store_report_params` |
| AC-SR10 | `tests/unit/test_store_render_step.py` | `test_AC_SR10_render_step_params_defaults` |
| AC-SR11 | `tests/unit/test_store_render_step.py` | `test_AC_SR11_render_candlestick_keys` |
| AC-SR12 | `tests/unit/test_store_render_step.py` | `test_AC_SR12_render_pdf_creates_directory` |
| AC-SR13 | `tests/unit/test_store_render_step.py` | `test_AC_SR13_both_steps_have_side_effects` |
| AC-SR14 | `tests/unit/test_store_render_step.py` | `test_AC_SR14_live_uow_report_snapshot` |
| AC-SR15 | `tests/unit/test_store_render_step.py` | `test_AC_SR15_report_repo_snapshot_fields` |

## Design Decisions & Known Risks

- **Decision**: Replaced WeasyPrint with Playwright for PDF rendering — **Reasoning**: WeasyPrint requires GTK/Pango system dependencies (MSYS2 on Windows). Playwright auto-downloads Chromium, has no system deps, excellent CSS fidelity, and Apache 2.0 license. Same `render_pdf()` interface preserved.
- **Decision**: `report_authorizer` uses raw sqlite3 action codes — **Reasoning**: Direct sqlite3 authorizer API is the only way to enforce read-only at the connection level.
- **Decision**: ReportSpec uses Pydantic discriminated unions — **Reasoning**: `section_type` field enables polymorphic serialization and validation.
- **Decision**: `render_candlestick` produces dual output (HTML + PNG) — **Reasoning**: HTML for interactive viewing, PNG data URI for embedding in PDF reports.
- **Risk**: AC-SR12 test exercises full Playwright→Chromium→PDF path; CI environments without Chromium will fail. Mitigation: `playwright install chromium` is required in CI setup.

## Changed Files

| File | Action | Description |
|------|--------|-------------|
| `packages/core/src/zorivest_core/pipeline_steps/store_report_step.py` | Created | StoreReportStep with Params (report_name, spec) |
| `packages/core/src/zorivest_core/pipeline_steps/render_step.py` | Created | RenderStep with Params (template, output_format="both") |
| `packages/core/src/zorivest_core/domain/report_spec.py` | Created | ReportSpec DSL with DataTableSection, MetricCardSection, ChartSection |
| `packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py` | Created | report_authorizer + create_sandboxed_connection |
| `packages/infrastructure/src/zorivest_infra/rendering/template_engine.py` | Created | Jinja2 env with currency/percent filters |
| `packages/infrastructure/src/zorivest_infra/rendering/chart_renderer.py` | Created | render_candlestick with Plotly dual output |
| `packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py` | Created | render_pdf via Playwright headless Chromium |
| `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` | Modified | ReportRepository.create() accepts snapshot_json/snapshot_hash |
| `packages/infrastructure/pyproject.toml` | Modified | Rendering extras: weasyprint→playwright>=1.50 |
| `tests/unit/test_store_render_step.py` | Created | 15 tests covering AC-SR1 through AC-SR15 |

## Additional Changes (Post-Implementation)

### Playwright Refactor
WeasyPrint was replaced with Playwright across 8 files. Changes propagated to:
- `pyproject.toml` rendering extras
- `implementation-plan.md` (7 references)
- `task.md` (2 bootstrap items unblocked)
- `dependency-manifest.md` (2 references)
- `output-index.md` (1 reference)
- `09-scheduling.md` (3 references: §9.7d header, code sample, dep table)

### Test Strengthening
6 tests across MEU-85/87 were strengthened from 🟡 Adequate to 🟢 Strong after IR-5 audit. AC-SR12 was upgraded from 🔴 Weak (try/except safety net) to 🟢 Strong (full PDF verification).

## Commands Executed

| Command | Result | Notes |
|---------|--------|-------|
| `uv run pytest tests/unit/test_store_render_step.py -v` | PASS (15/15) | All green |
| `uv sync --extra rendering` | OK | Playwright 1.58.0 installed, WeasyPrint removed |
| `uv run python -c "import playwright, kaleido; print('OK')"` | OK | Import verified |
| `uv run playwright install chromium` | OK | Chromium 145.0.7632.6 downloaded |
| `uv run pytest tests/ --tb=no -q` | PASS (1356/1356, 1 skip) | Full regression |

## FAIL_TO_PASS Evidence

| Test | Before | After |
|------|--------|-------|
| `test_store_render_step.py` (15 tests) | FAIL (module not found) | PASS |

## Test Rigor Audit (IR-5)

| Test | Rating | Notes |
|------|--------|-------|
| AC-SR1 | 🟢 | Registry key + identity |
| AC-SR2 | 🟢 | Registry key + identity |
| AC-SR3 | 🟢 | 3 section types + discriminated union |
| AC-SR4 | 🟢 | Boundary: 1000 OK, 1001 fails |
| AC-SR5 | 🟢 | Raw action code 21 |
| AC-SR6 | 🟢 | 4 deny action codes |
| AC-SR7 | 🟢 | Real connection, PRAGMA value |
| AC-SR8 | 🟢 | Both filters with formatted output |
| AC-SR9 | 🟢 | Positive + negative |
| AC-SR10 | 🟢 | Default value check |
| AC-SR11 | 🟢 | Data URI prefix + payload > 100 chars |
| AC-SR12 | 🟢 | Directory + file + size + return value (Playwright) |
| AC-SR13 | 🟢 | Both steps attribute check |
| AC-SR14 | 🟢 | Live UoW round-trip 2 fields |
| AC-SR15 | 🟢 | Repo-level round-trip 2 fields |

---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
