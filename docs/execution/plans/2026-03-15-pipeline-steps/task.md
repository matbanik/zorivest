# Task List — Pipeline Steps

> Project: `2026-03-15-pipeline-steps`
> MEUs: 85, 86, 87

---

## Dependency Bootstrap

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Add Phase 9 library deps to pyproject.toml | coder | `packages/core/pyproject.toml`, `packages/infrastructure/pyproject.toml` | `rg -e "pandera" -e "aiolimiter" -e "tenacity" -e "jinja2" -e "plotly" -e "pandas" packages/core/pyproject.toml packages/infrastructure/pyproject.toml` returns ≥6 matches | done |
| 2 | Verify core environment resolves | tester | Terminal output | `uv sync && uv run python -c "import pandera, aiolimiter, tenacity, jinja2, plotly, pandas; print('OK')"` prints OK | done |
| 3 | Install rendering extras and verify | tester | Terminal output | `uv sync --extra rendering && uv run python -c "import playwright, kaleido; print('OK')"` prints OK | done |
| 4 | Playwright Chromium install | tester | Terminal output | `uv run playwright install chromium` exits 0 | done |
| 5 | Kaleido render proof | tester | Terminal output | `uv run python -c "import plotly.graph_objects as go; fig = go.Figure(); fig.to_image(format='png'); print('Kaleido OK')"` prints Kaleido OK | done |

## MEU-85: FetchStep

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_fetch_step.py` | `uv run pytest tests/unit/test_fetch_step.py -v 2>&1` contains FAILED | done |
| 2 | Create `pipeline_steps/__init__.py` with eager imports | coder | `packages/core/src/zorivest_core/pipeline_steps/__init__.py` | `uv run python -c "from zorivest_core.pipeline_steps import fetch_step"` exits 0 | done |
| 3 | Create `fetch_step.py` (Green phase) | coder | `packages/core/src/zorivest_core/pipeline_steps/fetch_step.py` | `uv run pytest tests/unit/test_fetch_step.py -k "AC_F1 or AC_F2 or AC_F12" -v` — 0 failures | done |
| 4 | Create `criteria_resolver.py` | coder | `packages/core/src/zorivest_core/services/criteria_resolver.py` | `uv run pytest tests/unit/test_fetch_step.py -k "AC_F4 or AC_F5" -v` — 0 failures | done |
| 5 | Append `FetchResult` + `FRESHNESS_TTL` + `is_market_closed()` to `pipeline.py` | coder | `packages/core/src/zorivest_core/domain/pipeline.py` | `uv run pytest tests/unit/test_fetch_step.py -k "AC_F3 or AC_F6 or AC_F7 or AC_F8" -v` — 0 failures | done |
| 6 | Add `PipelineStateRepository` + UoW exposure | coder | `scheduling_repositories.py`, `unit_of_work.py` | `uv run pytest tests/unit/test_fetch_step.py -k "AC_F13 or AC_F14" -v` — 0 failures | done |
| 7 | Create `pipeline_rate_limiter.py` | coder | `packages/infrastructure/src/zorivest_infra/market_data/pipeline_rate_limiter.py` | `uv run pytest tests/unit/test_fetch_step.py -k "AC_F9" -v` — 0 failures | done |
| 8 | Create `http_cache.py` | coder | `packages/infrastructure/src/zorivest_infra/market_data/http_cache.py` | `uv run pytest tests/unit/test_fetch_step.py -k "AC_F10" -v` — 0 failures | done |
| 9 | All AC-F* tests pass | tester | Terminal output | `uv run pytest tests/unit/test_fetch_step.py -v` — 0 failures | done |
| 10 | Step registration verification | tester | Terminal output | `uv run pytest tests/unit/test_fetch_step.py -k "AC_F15" -v` — 0 failures | done |
| 11 | Create handoff 070 | coder | `.agent/context/handoffs/070-2026-03-15-fetch-step-bp09s9.4.md` | `Test-Path .agent/context/handoffs/*fetch-step*` returns True | done |

## MEU-86: TransformStep

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_transform_step.py` | `uv run pytest tests/unit/test_transform_step.py -v 2>&1` contains FAILED | done |
| 2 | Create `transform_step.py` (Green phase) | coder | `packages/core/src/zorivest_core/pipeline_steps/transform_step.py` | `uv run pytest tests/unit/test_transform_step.py -k "AC_T1 or AC_T2 or AC_T12" -v` — 0 failures | done |
| 3 | Create `field_mappings.py` | coder | `packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py` | `uv run pytest tests/unit/test_transform_step.py -k "AC_T3 or AC_T4" -v` — 0 failures | done |
| 4 | Create `validation_gate.py` | coder | `packages/core/src/zorivest_core/services/validation_gate.py` | `uv run pytest tests/unit/test_transform_step.py -k "AC_T5 or AC_T6 or AC_T7" -v` — 0 failures | done |
| 5 | Create `write_dispositions.py` | coder | `packages/infrastructure/src/zorivest_infra/repositories/write_dispositions.py` | `uv run pytest tests/unit/test_transform_step.py -k "AC_T8 or AC_T9" -v` — 0 failures | done |
| 6 | Create `precision.py` | coder | `packages/core/src/zorivest_core/domain/precision.py` | `uv run pytest tests/unit/test_transform_step.py -k "AC_T10 or AC_T11" -v` — 0 failures | done |
| 7 | Live UoW persistence test | tester | `tests/unit/test_transform_step.py` | `uv run pytest tests/unit/test_transform_step.py -k "AC_T13" -v` — 0 failures | done |
| 8 | All AC-T* tests pass | tester | Terminal output | `uv run pytest tests/unit/test_transform_step.py -v` — 0 failures | done |
| 9 | Create handoff 071 | coder | `.agent/context/handoffs/071-2026-03-15-transform-step-bp09s9.5.md` | `Test-Path .agent/context/handoffs/*transform-step*` returns True | done |

## MEU-87: StoreReportStep + RenderStep

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Write tests (Red phase) | coder | `tests/unit/test_store_render_step.py` | `uv run pytest tests/unit/test_store_render_step.py -v 2>&1` contains FAILED | done |
| 2 | Create `store_report_step.py` (Green phase) | coder | `packages/core/src/zorivest_core/pipeline_steps/store_report_step.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR1 or AC_SR9 or AC_SR13" -v` — 0 failures | done |
| 3 | Create `report_spec.py` | coder | `packages/core/src/zorivest_core/domain/report_spec.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR3 or AC_SR4" -v` — 0 failures | done |
| 4 | Create `sql_sandbox.py` | coder | `packages/infrastructure/src/zorivest_infra/security/sql_sandbox.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR5 or AC_SR6 or AC_SR7" -v` — 0 failures | done |
| 5 | Extend `ReportRepository.create()` for snapshot fields | coder | `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR15" -v` — 0 failures | done |
| 6 | Create `render_step.py` (Green phase) | coder | `packages/core/src/zorivest_core/pipeline_steps/render_step.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR2 or AC_SR10" -v` — 0 failures | done |
| 7 | Create `template_engine.py` | coder | `packages/infrastructure/src/zorivest_infra/rendering/template_engine.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR8" -v` — 0 failures | done |
| 8 | Create `chart_renderer.py` | coder | `packages/infrastructure/src/zorivest_infra/rendering/chart_renderer.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR11" -v` — 0 failures | done |
| 9 | Create `pdf_renderer.py` | coder | `packages/infrastructure/src/zorivest_infra/rendering/pdf_renderer.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR12" -v` — 0 failures | done |
| 10 | Live UoW persistence test | tester | `tests/unit/test_store_render_step.py` | `uv run pytest tests/unit/test_store_render_step.py -k "AC_SR14" -v` — 0 failures | done |
| 11 | All AC-SR* tests pass | tester | Terminal output | `uv run pytest tests/unit/test_store_render_step.py -v` — 0 failures | done |
| 12 | Create handoff 072 | coder | `.agent/context/handoffs/072-2026-03-15-store-render-step-bp09s9.6+9.7.md` | `Test-Path .agent/context/handoffs/*store-render-step*` returns True | done |

## Post-MEU Deliverables

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | MEU gate | tester | Gate pass output | `uv run python tools/validate_codebase.py --scope meu` — 0 errors | done |
| 2 | Update meu-registry | coder | `.agent/context/meu-registry.md` | `rg -c -e "MEU-85" -e "MEU-86" -e "MEU-87" .agent/context/meu-registry.md` returns ≥3 | done |
| 3 | Update BUILD_PLAN | coder | `docs/BUILD_PLAN.md` | `rg -e "MEU-85.*✅" -e "MEU-86.*✅" -e "MEU-87.*✅" docs/BUILD_PLAN.md` returns ≥3 matches | done |
| 4 | Full regression | tester | Terminal output | `uv run pytest tests/ --tb=no -q` — 0 failures | done |
| 5 | Anti-placeholder scan | tester | Scan output | `rg -e "TODO" -e "FIXME" -e "NotImplementedError" packages/core/src/zorivest_core/pipeline_steps/ packages/core/src/zorivest_core/domain/precision.py packages/core/src/zorivest_core/domain/report_spec.py packages/core/src/zorivest_core/services/criteria_resolver.py packages/core/src/zorivest_core/services/validation_gate.py` — 0 matches | done |
| 6 | Create reflection | coder | `docs/execution/reflections/2026-03-15-pipeline-steps-reflection.md` | `Test-Path docs/execution/reflections/2026-03-15-pipeline-steps-reflection.md` returns True | done |
| 7 | Update metrics | coder | `docs/execution/metrics.md` | `rg "pipeline-steps" docs/execution/metrics.md` returns match | done |
| 8 | Save session state | coder | Pomera note titled `Memory/Session/Zorivest-pipeline-steps-2026-03-15` | Agent-verified: `pomera_notes action=save title="Memory/Session/Zorivest-pipeline-steps-2026-03-15"` returns note ID, then `pomera_notes action=get note_id=<returned_id>` confirms title matches (MCP-only, not shell) | done |
| 9 | Prepare commit messages | coder | Commit messages file | `Test-Path docs/execution/plans/2026-03-15-pipeline-steps/commit-messages.md` returns True | done |
