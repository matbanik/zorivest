---
project: ir5-test-corrections
slug: ir5-test-corrections
phase: cross-phase
status: execution_complete_closeout_pending
agent: antigravity
iteration: 3
files_changed: 72
tests_upgraded: 285
tests_passing: 1674
---

# IR-5 Test Corrections — Consolidated Execution Handoff

## Task

- **Date:** 2026-03-17
- **Task slug:** ir5-test-corrections
- **Owner role:** orchestrator
- **Scope:** Upgrade all 285 weak tests (71 🔴 + 214 🟡) identified in IR-5 audit to 🟢

> [!IMPORTANT]
> **Status: execution_complete_closeout_pending** — all 6 code-change batches are done and regression-verified, but the closeout tasks (re-audit, pattern-analysis update, BUILD_PLAN update) remain unchecked per [task.md](file:///p:/zorivest/docs/execution/plans/2026-03-16-ir5-test-corrections/task.md).

> [!NOTE]
> **Consolidated handoff.** The implementation plan originally specified 7 separate handoff files (074–080). Execution was performed in a single conversation and is delivered as this single consolidated artifact. The plan has been updated (§Handoff Naming) to reflect this consolidation decision.

## Inputs

- User request: Execute the IR-5 test corrections plan
- Specs/docs referenced:
  - [IR-5 implementation plan](file:///p:/zorivest/docs/execution/plans/2026-03-16-ir5-test-corrections/implementation-plan.md)
  - [IR-5 task list](file:///p:/zorivest/docs/execution/plans/2026-03-16-ir5-test-corrections/task.md)
  - [Pattern analysis](file:///p:/zorivest/docs/execution/plans/2026-03-16-test-rigor-audit/phase1-ir5-pattern-analysis.md)
  - [Per-test ratings CSV](file:///p:/zorivest/docs/execution/plans/2026-03-16-test-rigor-audit/phase1-ir5-per-test-ratings.csv)
- Constraints: Zero new regressions; only add/strengthen assertions, never remove

## Role Plan

1. orchestrator — batch sequencing, progress tracking
2. coder — apply assertion upgrades per anti-pattern
3. tester — regression gate per batch + full suite
4. reviewer — Codex validation pass

## Coder Output

### Changed Files — 72 files across 6 batches

File lists match the [implementation plan](file:///p:/zorivest/docs/execution/plans/2026-03-16-ir5-test-corrections/implementation-plan.md) scope exactly. All filenames verified against the actual `tests/unit/` and `tests/integration/` inventories.

**Batch 1 — Domain Tests (53 tests: 41🔴 + 12🟡, 15 files):**

| File | Tests Fixed | Anti-Patterns |
|------|------------|---------------|
| `tests/unit/test_ports.py` | 8🔴 3🟡 | R1: exact method set equality |
| `tests/unit/test_market_data_entities.py` | 6🔴 | R1: exact param lists |
| `tests/unit/test_exceptions.py` | 6🔴 | R1: message content assertions |
| `tests/unit/test_events.py` | 5🔴 | R1: payload field values |
| `tests/unit/test_commands_dtos.py` | 4🔴 | R1: field equality |
| `tests/unit/test_pipeline_enums.py` | 3🔴 | R1: exact `.value` |
| `tests/unit/test_scheduling_models.py` | 2🔴 6🟡 | R1+Y1: field-value |
| `tests/unit/test_entities.py` | 2🔴 | R1: field value |
| `tests/unit/test_enums.py` | 2🔴 | R1: value membership |
| `tests/unit/test_value_objects.py` | 1🔴 | R1: value equality |
| `tests/unit/test_pipeline_models.py` | 1🔴 | R1: field value |
| `tests/unit/test_calculator.py` | 1🔴 | R1: type → value |
| `tests/unit/test_portfolio_balance.py` | 1🟡 | Y1: weak → concrete |
| `tests/unit/test_models.py` | 1🟡 | Y1: weak → concrete |
| `tests/unit/test_display_mode.py` | 1🟡 | Y1: weak → concrete |

**Batch 2 — API Tests (84 tests: 3🔴 + 81🟡, 13 files):**

| File | Tests Fixed | Anti-Patterns |
|------|------------|---------------|
| `tests/unit/test_api_analytics.py` | 10🟡 | Y3: status → body |
| `tests/unit/test_api_tax.py` | 9🟡 | Y3: status → body |
| `tests/unit/test_api_system.py` | 9🟡 | Y3: status → body |
| `tests/unit/test_api_trades.py` | 8🟡 | Y3: status → body |
| `tests/unit/test_api_plans.py` | 8🟡 | Y3: status → body |
| `tests/unit/test_api_reports.py` | 7🟡 | Y3: status → body |
| `tests/unit/test_api_foundation.py` | 1🔴 5🟡 | R1+Y3 |
| `tests/unit/test_api_auth.py` | 6🟡 | Y3: status → body |
| `tests/unit/test_api_settings.py` | 1🔴 4🟡 | R2+Y3 |
| `tests/unit/test_api_accounts.py` | 4🟡 | Y3: status → body |
| `tests/unit/test_api_watchlists.py` | 4🟡 | Y3: status → body |
| `tests/unit/test_api_key_encryption.py` | 1🔴 | R1: type → value |
| `tests/unit/test_market_data_api.py` | 7🟡 | Y3: status → body |

**Batch 3 — Service Tests (48 tests: 13🔴 + 35🟡, 16 files):**

| File | Tests Fixed | Anti-Patterns |
|------|------------|---------------|
| `tests/unit/test_settings_validator.py` | 13🟡 | Y1: exact error messages |
| `tests/unit/test_report_service.py` | 2🔴 3🟡 | R3+Y4: no-op + mock → value |
| `tests/unit/test_settings_resolver.py` | 5🟡 | Y1+Y2: weak + private → value |
| `tests/unit/test_settings_registry.py` | 1🔴 3🟡 | R1+Y2: type + private → value |
| `tests/unit/test_ref_resolver.py` | 4🟡 | Y1: weak → concrete |
| `tests/unit/test_analytics.py` | 3🔴 | R1: type → signature + dataclass verification |
| `tests/unit/test_rate_limiter.py` | 2🔴 1🟡 | R1+R3: type + no-op → value |
| `tests/unit/test_service_extensions.py` | 2🔴 | R1: type → value |
| `tests/unit/test_settings_cache.py` | 2🟡 | Y2: private → value |
| `tests/unit/test_system_service.py` | 1🔴 | R3: no-op → value |
| `tests/unit/test_provider_connection_service.py` | 1🔴 | R3: no-op → value |
| `tests/unit/test_market_data_service.py` | 1🔴 | R3: no-op → value |
| `tests/unit/test_watchlist_service.py` | 1🟡 | Y4: mock → value |
| `tests/unit/test_settings_service.py` | 1🟡 | Y4: mock → value |
| `tests/unit/test_image_service.py` | 1🟡 | Y4: mock → value |
| `tests/unit/test_account_review.py` | 1🟡 | Y4: mock → value |

**Batch 4 — Infra/Pipeline Tests (78 tests: 12🔴 + 66🟡, 16 files):**

| File | Tests Fixed | Anti-Patterns |
|------|------------|---------------|
| `tests/unit/test_policy_validator.py` | 21🟡 | Y1: weak → concrete |
| `tests/unit/test_logging_config.py` | 1🔴 8🟡 | R1+Y1: type + weak → value |
| `tests/unit/test_csv_import.py` | 2🔴 5🟡 | R1+Y1: type + weak → value |
| `tests/unit/test_logging_formatter.py` | 1🔴 5🟡 | R1+Y1: type + weak → value |
| `tests/unit/test_config_export.py` | 6🟡 | Y1+Y2: weak + private → value |
| `tests/unit/test_scheduling_repos.py` | 1🔴 4🟡 | R1+Y2: type + private → value |
| `tests/unit/test_backup_manager.py` | 5🟡 | Y2: private → value |
| `tests/unit/test_backup_recovery.py` | 4🟡 | Y1: weak → concrete |
| `tests/unit/test_step_registry.py` | 2🔴 1🟡 | R1+R3: type + no-op → value |
| `tests/unit/test_fetch_step.py` | 1🔴 2🟡 | R1+Y1+Y3: mixed → value |
| `tests/unit/test_provider_registry.py` | 2🔴 | R1: type → value |
| `tests/unit/test_ibkr_flexquery.py` | 1🔴 1🟡 | R1+Y2 |
| `tests/unit/test_store_render_step.py` | 2🟡 | Y1: weak → concrete |
| `tests/unit/test_market_provider_settings_repo.py` | 1🔴 | R3: no-op → value |
| `tests/unit/test_transform_step.py` | 1🟡 | Y1: weak → concrete |
| `tests/unit/test_image_processing.py` | 1🟡 | Y1: weak → concrete |

**Batch 5 — Integration Tests (9 tests: 2🔴 + 7🟡, 4 files):**

| File | Tests Fixed | Anti-Patterns |
|------|------------|---------------|
| `tests/integration/test_repositories.py` | 4🟡 | Y1+Y2: weak + private → value |
| `tests/integration/test_unit_of_work.py` | 1🔴 1🟡 | R1+Y2: type + private → value |
| `tests/integration/test_database_connection.py` | 1🔴 1🟡 | R1+Y1: type + weak → value |
| `tests/integration/test_backup_integration.py` | 1🟡 | Y2: private → value |

**Batch 6 — MCP + UI Tests (13 tests: 0🔴 + 13🟡, 8 files):**

| File | Tests Fixed | Anti-Patterns |
|------|------------|---------------|
| `mcp-server/tests/confirmation.test.ts` | 2🟡 | Y4: mock-only → value |
| `mcp-server/tests/discovery-tools.test.ts` | 1🟡 | Y4: mock-only → call count |
| `mcp-server/tests/gui-tools.test.ts` | 1🟡 | Y4: mock-only → response value |
| `mcp-server/tests/metrics.test.ts` | 1🟡 | R1: type-check → method value |
| `ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx` | 3🟡 | Y1: presence → value |
| `ui/src/renderer/src/__tests__/app.test.tsx` | 2🟡 | Y1: presence → value |
| `ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts` | 2🟡 | Y1: presence → value |
| `ui/src/main/__tests__/python-manager.test.ts` | 1🟡 | R1: type → finite check |

**Grand total: 15 + 13 + 16 + 16 + 4 + 8 = 72 files, 285 tests upgraded.**

## Tester Output

### Full Regression (Post All Corrections)

| Suite | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| **Python** | 1435 | 2* | 15 |
| **MCP** | 183 | 0 | 0 |
| **UI** | 56 | 0 | 0 |
| **Total** | **1674** | **2*** | **15** |

\* 2 pre-existing failures (not regressions):
1. `test_AC_SR11_render_candlestick_keys` — `orjson` version missing `OPT_NON_STR_KEYS`
2. `test_AC_SR12_render_pdf_creates_directory` — `playwright` not installed (intentionally optional)

- **New regressions**: 0

### Codex-Flagged Tests (Passes 1–2 → Fixed)

| Test | Before | After |
|------|--------|-------|
| `test_trade_repository_is_protocol` | `expected <= actual` + `len >= 4` | `actual == expected` (exact 9-method set) |
| `test_trade_repository_methods` | `expected <= actual` (4-method subset) | `actual == expected` (exact 9-method set) |
| `test_image_repository_is_protocol` | `expected <= actual` + `len >= 5` | `actual == expected` (exact 6-method set) |
| `test_image_repository_methods` | `expected <= actual` (5-method subset) | `actual == expected` (exact 6-method set) |
| `test_unit_of_work_is_protocol` | `expected <= actual` (no error msg) | `actual == expected` (exact 2-method set) |
| `test_unit_of_work_methods` | `expected <= actual` | `actual == expected` (exact 2-method set) |
| `test_broker_port_is_protocol` | `expected <= actual` (no error msg) | `actual == expected` (exact 5-method set) |
| `test_broker_port_methods` | `expected <= actual` | `actual == expected` (exact 5-method set) |
| `test_bank_import_port_is_protocol` | `expected <= actual` (no error msg) | `actual == expected` (exact 3-method set) |
| `test_bank_import_port_methods` | `expected <= actual` | `actual == expected` (exact 3-method set) |
| `test_identifier_resolver_port_is_protocol` | `expected <= actual` (no error msg) | `actual == expected` (exact 2-method set) |
| `test_identifier_resolver_port_methods` | `expected <= actual` | `actual == expected` (exact 2-method set) |
| `test_market_data_port_has_get_quote` | `"ticker" in params` + `len == 2` | `params == ["self", "ticker"]` (exact) |
| `test_market_data_port_has_search_ticker` | `"query" in params` + `len == 2` | `params == ["self", "query"]` (exact) |
| `test_market_data_port_has_get_sec_filings` | `"ticker" in params` + `len >= 2` | `params == ["self", "ticker"]` (exact) |
| `test_results_module_exports` | `hasattr` + `isinstance(type)` | + `__dataclass_fields__` + field count |
| `test_expectancy_module_exports` | `hasattr` + `callable` | + signature: `"trades"` param |
| `test_sqn_module_exports` | `hasattr` + `callable` | + signature: `"trades"` param |

### Post-Correction Verification

```
rg "expected_methods <= actual_methods" tests/  → 0 hits ✅
rg "len(actual_methods) >=" tests/              → 0 hits ✅
uv run pytest tests/unit/test_ports.py          → 18 passed ✅
uv run pytest tests/unit/test_market_data_entities.py tests/unit/test_analytics.py → 47 passed ✅
uv run pytest tests/ --tb=no -q                 → 1435 passed, 2 failed (pre-existing), 15 skipped ✅
```

## Closeout Status (Unchecked)

The following closeout tasks remain incomplete:

- [ ] Type checking (`pyright`)
- [ ] IR-5 re-audit (`re-audit-results.csv`)
- [ ] Pattern analysis update
- [ ] BUILD_PLAN update

## Commands for Verification

```powershell
# Full Python regression
uv run pytest tests/ --tb=short -q

# Full MCP + UI regression
cd p:\zorivest\mcp-server && npm test
cd p:\zorivest\ui && npm test

# Verify zero weak assertion patterns remain
rg "expected_methods <= actual_methods" tests/
rg "len\(actual_methods\) >=" tests/
```

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending

## Final Summary

- Status: **execution_complete_closeout_pending**
- All 6 code-change batches complete, 285/285 tests upgraded across 72 files, zero new regressions
- All 18 Codex-flagged weak assertions (12 subset, 3 membership/len, 3 hasattr-only) resolved
- Closeout tasks remain: re-audit, pattern analysis, BUILD_PLAN update, type checking
---
## Codex Validation Report
{Left blank — Codex fills this section during validation-review workflow}
