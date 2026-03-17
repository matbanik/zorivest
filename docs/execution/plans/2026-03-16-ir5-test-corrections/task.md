# Task List — IR-5 Test Corrections

> Project: `2026-03-16-ir5-test-corrections`
> Scope: 285 weak tests (71 🔴, 214 🟡) across 72 files → all upgraded to 🟢

---

## Batch 1: Domain Tests (53 weak: 41🔴 + 12🟡, 15 files)

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Upgrade `test_ports.py` (8🔴 3🟡) — type-guard → value assertions | coder | `tests/unit/test_ports.py` | `uv run pytest tests/unit/test_ports.py -v` — 0 failures | `[ ]` |
| 2 | Upgrade `test_market_data_entities.py` (6🔴) — type → value | coder | `tests/unit/test_market_data_entities.py` | `uv run pytest tests/unit/test_market_data_entities.py -v` — 0 failures | `[ ]` |
| 3 | Upgrade `test_exceptions.py` (6🔴) — type → message + attr assertions | coder | `tests/unit/test_exceptions.py` | `uv run pytest tests/unit/test_exceptions.py -v` — 0 failures | `[ ]` |
| 4 | Upgrade `test_events.py` (5🔴) — type → payload value assertions | coder | `tests/unit/test_events.py` | `uv run pytest tests/unit/test_events.py -v` — 0 failures | `[ ]` |
| 5 | Upgrade `test_commands_dtos.py` (4🔴) — type → field equality | coder | `tests/unit/test_commands_dtos.py` | `uv run pytest tests/unit/test_commands_dtos.py -v` — 0 failures | `[ ]` |
| 6 | Upgrade `test_pipeline_enums.py` (3🔴) — membership → value | coder | `tests/unit/test_pipeline_enums.py` | `uv run pytest tests/unit/test_pipeline_enums.py -v` — 0 failures | `[ ]` |
| 7 | Upgrade `test_scheduling_models.py` (2🔴 6🟡) — type + weak → value | coder | `tests/unit/test_scheduling_models.py` | `uv run pytest tests/unit/test_scheduling_models.py -v` — 0 failures | `[ ]` |
| 8 | Upgrade `test_entities.py` (2🔴) — type → value | coder | `tests/unit/test_entities.py` | `uv run pytest tests/unit/test_entities.py -v` — 0 failures | `[ ]` |
| 9 | Upgrade `test_enums.py` (2🔴) — membership → value | coder | `tests/unit/test_enums.py` | `uv run pytest tests/unit/test_enums.py -v` — 0 failures | `[ ]` |
| 10 | Upgrade small domain files (6 files × 1 weak each) | coder | `test_value_objects.py`, `test_pipeline_models.py`, `test_calculator.py`, `test_portfolio_balance.py`, `test_models.py`, `test_display_mode.py` | `uv run pytest tests/unit/test_value_objects.py tests/unit/test_pipeline_models.py tests/unit/test_calculator.py tests/unit/test_portfolio_balance.py tests/unit/test_models.py tests/unit/test_display_mode.py -v` — 0 failures | `[ ]` |
| 11 | Batch 1 regression gate | tester | Terminal output | `uv run pytest tests/unit/ --tb=no -q` — 0 failures | `[ ]` |

## Batch 2: API Tests (84 weak: 3🔴 + 81🟡, 13 files)

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Upgrade `test_api_analytics.py` (10🟡) — status-code → contract | coder | `tests/unit/test_api_analytics.py` | `uv run pytest tests/unit/test_api_analytics.py -v` — 0 failures | `[ ]` |
| 2 | Upgrade `test_api_tax.py` (9🟡) — status-code → contract | coder | `tests/unit/test_api_tax.py` | `uv run pytest tests/unit/test_api_tax.py -v` — 0 failures | `[ ]` |
| 3 | Upgrade `test_api_system.py` (9🟡) — status-code → contract | coder | `tests/unit/test_api_system.py` | `uv run pytest tests/unit/test_api_system.py -v` — 0 failures | `[ ]` |
| 4 | Upgrade `test_api_trades.py` (8🟡) — status-code → contract | coder | `tests/unit/test_api_trades.py` | `uv run pytest tests/unit/test_api_trades.py -v` — 0 failures | `[ ]` |
| 5 | Upgrade `test_api_plans.py` (8🟡) — status-code → contract | coder | `tests/unit/test_api_plans.py` | `uv run pytest tests/unit/test_api_plans.py -v` — 0 failures | `[ ]` |
| 6 | Upgrade `test_api_reports.py` (7🟡) — status-code → contract | coder | `tests/unit/test_api_reports.py` | `uv run pytest tests/unit/test_api_reports.py -v` — 0 failures | `[ ]` |
| 7 | Upgrade `test_api_foundation.py` (1🔴 5🟡) — type + status → contract | coder | `tests/unit/test_api_foundation.py` | `uv run pytest tests/unit/test_api_foundation.py -v` — 0 failures | `[ ]` |
| 8 | Upgrade `test_api_auth.py` (6🟡) — status-code → contract | coder | `tests/unit/test_api_auth.py` | `uv run pytest tests/unit/test_api_auth.py -v` — 0 failures | `[ ]` |
| 9 | Upgrade `test_api_settings.py` (1🔴 4🟡) — type + status → contract | coder | `tests/unit/test_api_settings.py` | `uv run pytest tests/unit/test_api_settings.py -v` — 0 failures | `[ ]` |
| 10 | Upgrade `test_api_accounts.py` (4🟡) + `test_api_watchlists.py` (4🟡) | coder | 2 files | `uv run pytest tests/unit/test_api_accounts.py tests/unit/test_api_watchlists.py -v` — 0 failures | `[ ]` |
| 11 | Upgrade `test_api_key_encryption.py` (1🔴) + `test_market_data_api.py` (7🟡) | coder | 2 files | `uv run pytest tests/unit/test_api_key_encryption.py tests/unit/test_market_data_api.py -v` — 0 failures | `[ ]` |
| 12 | Batch 2 regression gate | tester | Terminal output | `uv run pytest tests/unit/test_api_*.py --tb=no -q` — 0 failures | `[ ]` |

## Batch 3: Service Tests (48 weak: 13🔴 + 35🟡, 16 files)

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Upgrade `test_settings_validator.py` (13🟡) — weak → exact validation assertions | coder | `tests/unit/test_settings_validator.py` | `uv run pytest tests/unit/test_settings_validator.py -v` — 0 failures | `[ ]` |
| 2 | Upgrade `test_report_service.py` (2🔴 3🟡) — no-op + mock → behavioral | coder | `tests/unit/test_report_service.py` | `uv run pytest tests/unit/test_report_service.py -v` — 0 failures | `[ ]` |
| 3 | Upgrade `test_settings_resolver.py` (5🟡) — weak + private → public interface | coder | `tests/unit/test_settings_resolver.py` | `uv run pytest tests/unit/test_settings_resolver.py -v` — 0 failures | `[ ]` |
| 4 | Upgrade `test_settings_registry.py` (1🔴 3🟡) — type + private → value | coder | `tests/unit/test_settings_registry.py` | `uv run pytest tests/unit/test_settings_registry.py -v` — 0 failures | `[ ]` |
| 5 | Upgrade `test_ref_resolver.py` (4🟡) — weak → exact assertions | coder | `tests/unit/test_ref_resolver.py` | `uv run pytest tests/unit/test_ref_resolver.py -v` — 0 failures | `[ ]` |
| 6 | Upgrade `test_analytics.py` (3🔴) + `test_rate_limiter.py` (2🔴 1🟡) | coder | 2 files | `uv run pytest tests/unit/test_analytics.py tests/unit/test_rate_limiter.py -v` — 0 failures | `[ ]` |
| 7 | Upgrade small service files (9 files × 1-2 weak each) | coder | `test_service_extensions.py`, `test_settings_cache.py`, `test_system_service.py`, `test_provider_connection_service.py`, `test_market_data_service.py`, `test_watchlist_service.py`, `test_settings_service.py`, `test_image_service.py`, `test_account_review.py` | `uv run pytest tests/unit/test_service_extensions.py tests/unit/test_settings_cache.py tests/unit/test_system_service.py tests/unit/test_provider_connection_service.py tests/unit/test_market_data_service.py tests/unit/test_watchlist_service.py tests/unit/test_settings_service.py tests/unit/test_image_service.py tests/unit/test_account_review.py -v` — 0 failures | `[ ]` |
| 8 | Batch 3 regression gate | tester | Terminal output | `uv run pytest tests/unit/ --tb=no -q` — 0 failures | `[ ]` |

## Batch 4: Infra / Pipeline Tests (78 weak: 12🔴 + 66🟡, 16 files)

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Upgrade `test_policy_validator.py` (21🟡) — weak → exact violation assertions | coder | `tests/unit/test_policy_validator.py` | `uv run pytest tests/unit/test_policy_validator.py -v` — 0 failures | `[ ]` |
| 2 | Upgrade `test_logging_config.py` (1🔴 8🟡) — type + weak + private → value | coder | `tests/unit/test_logging_config.py` | `uv run pytest tests/unit/test_logging_config.py -v` — 0 failures | `[ ]` |
| 3 | Upgrade `test_csv_import.py` (2🔴 5🟡) — type + weak → value | coder | `tests/unit/test_csv_import.py` | `uv run pytest tests/unit/test_csv_import.py -v` — 0 failures | `[ ]` |
| 4 | Upgrade `test_logging_formatter.py` (1🔴 5🟡) — type + weak → value | coder | `tests/unit/test_logging_formatter.py` | `uv run pytest tests/unit/test_logging_formatter.py -v` — 0 failures | `[ ]` |
| 5 | Upgrade `test_config_export.py` (6🟡) — weak + private → public interface | coder | `tests/unit/test_config_export.py` | `uv run pytest tests/unit/test_config_export.py -v` — 0 failures | `[ ]` |
| 6 | Upgrade `test_scheduling_repos.py` (1🔴 4🟡) — type + private → value | coder | `tests/unit/test_scheduling_repos.py` | `uv run pytest tests/unit/test_scheduling_repos.py -v` — 0 failures | `[ ]` |
| 7 | Upgrade `test_backup_manager.py` (5🟡) — private state → public interface | coder | `tests/unit/test_backup_manager.py` | `uv run pytest tests/unit/test_backup_manager.py -v` — 0 failures | `[ ]` |
| 8 | Upgrade `test_backup_recovery.py` (4🟡) — weak → exact assertions | coder | `tests/unit/test_backup_recovery.py` | `uv run pytest tests/unit/test_backup_recovery.py -v` — 0 failures | `[ ]` |
| 9 | Upgrade `test_step_registry.py` (2🔴 1🟡) — type + no-op → postcondition | coder | `tests/unit/test_step_registry.py` | `uv run pytest tests/unit/test_step_registry.py -v` — 0 failures | `[ ]` |
| 10 | Upgrade `test_fetch_step.py` (1🔴 2🟡) — type + weak → value | coder | `tests/unit/test_fetch_step.py` | `uv run pytest tests/unit/test_fetch_step.py -v` — 0 failures | `[ ]` |
| 11 | Upgrade small infra files (6 files) — `test_provider_registry.py` (2🔴), `test_ibkr_flexquery.py` (1🔴 1🟡), `test_store_render_step.py` (2🟡), `test_market_provider_settings_repo.py` (1🔴), `test_transform_step.py` (1🟡), `test_image_processing.py` (1🟡) | coder | 6 files | `uv run pytest tests/unit/test_provider_registry.py tests/unit/test_ibkr_flexquery.py tests/unit/test_store_render_step.py tests/unit/test_market_provider_settings_repo.py tests/unit/test_transform_step.py tests/unit/test_image_processing.py -v` — 0 failures | `[ ]` |
| 12 | Batch 4 regression gate | tester | Terminal output | `uv run pytest tests/unit/ --tb=no -q` — 0 failures | `[ ]` |

## Batch 5: Integration Tests (9 weak: 2🔴 + 7🟡, 4 files)

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Upgrade `test_repositories.py` (4🟡) — weak + private → value | coder | `tests/integration/test_repositories.py` | `uv run pytest tests/integration/test_repositories.py -v` — 0 failures | `[ ]` |
| 2 | Upgrade `test_unit_of_work.py` (1🔴 1🟡) — type + private → value | coder | `tests/integration/test_unit_of_work.py` | `uv run pytest tests/integration/test_unit_of_work.py -v` — 0 failures | `[ ]` |
| 3 | Upgrade `test_database_connection.py` (1🔴 1🟡) + `test_backup_integration.py` (1🟡) | coder | 2 files | `uv run pytest tests/integration/test_database_connection.py tests/integration/test_backup_integration.py -v` — 0 failures | `[ ]` |
| 4 | Batch 5 regression gate | tester | Terminal output | `uv run pytest tests/integration/ --tb=no -q` — 0 failures | `[ ]` |

## Batch 6: MCP + UI Tests (13 weak: 0🔴 + 13🟡, 8 files)

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Upgrade MCP tests — `confirmation.test.ts` (2🟡), `discovery-tools.test.ts` (1🟡), `gui-tools.test.ts` (1🟡), `metrics.test.ts` (1🟡) | coder | 4 MCP test files | `cd mcp-server && npm test` — 0 failures | `[ ]` |
| 2 | Upgrade UI tests — `CommandPalette.test.tsx` (3🟡), `app.test.tsx` (2🟡), `commandRegistry.test.ts` (2🟡), `python-manager.test.ts` (1🟡) | coder | 4 UI test files | `cd ui && npm test` — 0 failures | `[ ]` |
| 3 | Batch 6 regression gate | tester | Terminal output | `cd mcp-server && npm test && cd ../ui && npm test` — 0 failures | `[ ]` |

## Closeout

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Full Python regression | tester | Terminal output | `uv run pytest tests/ --tb=no -q` — 0 failures | `[ ]` |
| 2 | Full TypeScript regression | tester | Terminal output | `cd mcp-server && npm test && cd ../ui && npm test` — 0 failures | `[ ]` |
| 3 | Type checking | tester | Terminal output | `uv run pyright packages/` — 0 errors | `[ ]` |
| 4 | IR-5 re-audit on modified files | reviewer | `re-audit-results.csv` | `python -c "import csv; weak=[r for r in csv.reader(open('docs/execution/plans/2026-03-16-ir5-test-corrections/re-audit-results.csv',encoding='utf-8-sig')) if len(r)>=6 and ('🔴' in r[5] or '🟡' in r[5])]; print(f'Remaining weak: {len(weak)}'); assert len(weak)==0"` | `[ ]` |
| 5 | Update pattern analysis with final counts | coder | `phase1-ir5-pattern-analysis.md` | `python -c "import csv; rows=list(csv.reader(open('docs/execution/plans/2026-03-16-ir5-test-corrections/re-audit-results.csv','r',encoding='utf-8-sig'))); weak=[r for r in rows[1:] if len(r)>=6 and ('🔴' in r[5] or '🟡' in r[5])]; assert len(weak)==0, f'{len(weak)} weak tests remain'"` | `[ ]` |
| 6 | Verify and update `docs/BUILD_PLAN.md` | coder | `docs/BUILD_PLAN.md` | `rg -n -e ir5 -e IR-5 -e "weak test" -e "test rigor" docs/BUILD_PLAN.md docs/build-plan/` — verify references are current | `[ ]` |
