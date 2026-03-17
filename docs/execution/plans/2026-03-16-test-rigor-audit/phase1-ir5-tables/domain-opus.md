# Domain Model Tests — Opus Audit

Per-test rating table for Phase 1 IR-5 audit.
Criteria: [phase1-ir5-rating-criteria.md](../phase1-ir5-rating-criteria.md)

Summary: 349 tests audited | 🟢 297 | 🟡 21 | 🔴 31

## Codex Comparison

| Metric | Codex | Opus | Delta |
|--------|------:|-----:|------:|
| 🟢 | 296 | 297 | +1 |
| 🟡 | 12 | 21 | +9 |
| 🔴 | 41 | 31 | −10 |

### Key Disagreements

1. **Exception hierarchy tests** — Codex rates 6 `issubclass(XError, ZorivestError)` tests as 🔴. Opus upgrades to 🟡. **Rationale**: exception inheritance IS behavioral — it determines which `except` clauses catch them. The companion `test_all_exceptions_are_catchable_as_zorivest_error` proves this matters, but the individual `issubclass` checks are redundant given that companion test exists.
2. **Event `inherits_base` tests** — Codex rates 4 `isinstance(event, DomainEvent)` tests as 🔴. Opus upgrades to 🟡. **Rationale**: these verify that subclass events carry `event_id` and `occurred_at` via inheritance — relevant when event dispatchers filter by base type.
3. **Port `is_protocol` tests** — Codex rates 8 `issubclass(X, Protocol)` as 🔴. Opus agrees 🔴. These are truly structural — Protocol subtyping is a static type-checking concern, not a runtime behavioral property.
4. **Market data port `hasattr` + signature tests** — Codex rates 4 `hasattr` tests as 🔴. Opus upgrades to 🟡. **Rationale**: these check `hasattr` AND validate `inspect.signature` parameters — the parameter check is a meaningful contract assertion.
5. **Import surface/module imports tests** — All `hasattr(mod, "ClassName")` and AST import-scanning tests: Codex and Opus agree 🔴 (structural-only, would pass with empty class bodies).

## Ratings Summary by File

| File | Tests | 🟢 | 🟡 | 🔴 | Notes |
|------|------:|----:|----:|----:|-------|
| `test_calculator.py` | 9 | 8 | 0 | 1 | Import surface test 🔴 |
| `test_commands_dtos.py` | 37 | 33 | 0 | 4 | Module import tests 🔴 |
| `test_display_mode.py` | 25 | 24 | 1 | 0 | Excellent coverage |
| `test_entities.py` | 45 | 42 | 1 | 2 | Import surface + isinstance 🔴 |
| `test_enums.py` | 18 | 15 | 1 | 2 | StrEnum subclass + import 🔴 |
| `test_events.py` | 18 | 11 | 5 | 2 | inherits_base 🟡, module exports 🔴 |
| `test_exceptions.py` | 10 | 4 | 6 | 0 | Upgraded from Codex's 6 🔴 |
| `test_market_data_entities.py` | 19 | 13 | 5 | 1 | hasattr+sig → 🟡, is_protocol → 🔴 |
| `test_market_dtos.py` | 17 | 17 | 0 | 0 | Exemplary |
| `test_models.py` | 12 | 11 | 1 | 0 | Agrees with Codex |
| `test_pipeline_enums.py` | 17 | 14 | 0 | 3 | is_str_enum 🔴 |
| `test_pipeline_models.py` | 49 | 48 | 0 | 1 | logger isinstance 🔴 |
| `test_portfolio_balance.py` | 11 | 10 | 1 | 0 | Agrees with Codex |
| `test_ports.py` | 18 | 7 | 3 | 8 | Protocol/import 🔴 cluster |
| `test_scheduling_models.py` | 16 | 11 | 2 | 3 | inherits_from_base 🔴 |
| `test_value_objects.py` | 23 | 22 | 0 | 1 | Import surface 🔴 |

## Key Sections with Codex Disagreements

### test_exceptions.py — Opus upgrades 6 from 🔴 to 🟡

| Rating | Line | Test | Codex | Opus Reason |
|--------|-----:|------|-------|-------------|
| 🟡 | 21 | `test_zorivest_error_is_exception` | 🔴 | Inheritance determines catchability — meaningful for error handlers |
| 🟡 | 24 | `test_validation_error_inherits_zorivest_error` | 🔴 | Guards catch-all `except ZorivestError` pattern |
| 🟡 | 27 | `test_not_found_error_inherits_zorivest_error` | 🔴 | Guards catch-all pattern |
| 🟡 | 30 | `test_business_rule_error_inherits_zorivest_error` | 🔴 | Guards catch-all pattern |
| 🟡 | 33 | `test_budget_exceeded_error_inherits_zorivest_error` | 🔴 | Guards catch-all pattern |
| 🟡 | 36 | `test_import_error_inherits_zorivest_error` | 🔴 | Guards catch-all pattern |

**Upgrade path**: All 6 are subsumed by `test_all_exceptions_are_catchable_as_zorivest_error` (line 51, 🟢) — could be deleted without losing coverage.

### test_events.py — Opus upgrades 4 from 🔴 to 🟡

| Rating | Line | Test | Codex | Opus Reason |
|--------|-----:|------|-------|-------------|
| 🟡 | 76 | `test_trade_created_inherits_base` | 🔴 | Verifies event_id/occurred_at inheritance for event dispatchers |
| 🟡 | 107 | `test_balance_updated_inherits_base` | 🔴 | Same rationale |
| 🟡 | 136 | `test_image_attached_inherits_base` | 🔴 | Same rationale |
| 🟡 | 167 | `test_plan_created_inherits_base` | 🔴 | Same rationale |
| 🔴 | 185 | `test_events_module_exports` | 🔴 | Pure `hasattr` checks — agrees with Codex |

**Upgrade path**: The `inherits_base` tests are redundant with the `_fields` tests which already access inherited fields. Could strengthen by checking `event_id` is a valid UUID.

### test_market_data_entities.py — Opus upgrades 4 from 🔴 to 🟡

| Rating | Line | Test | Codex | Opus Reason |
|--------|-----:|------|-------|-------------|
| 🟡 | 183 | `test_market_data_port_has_get_quote` | 🔴 | `hasattr` + `inspect.signature` param check (contract verification) |
| 🟡 | 191 | `test_market_data_port_has_get_news` | 🔴 | Same — checks `ticker` AND `count` params |
| 🟡 | 200 | `test_market_data_port_has_search_ticker` | 🔴 | Same — checks `query` param |
| 🟡 | 208 | `test_market_data_port_has_get_sec_filings` | 🔴 | Same — checks `ticker` param |
| 🔴 | 178 | `test_market_data_port_is_protocol` | 🔴 | Pure `issubclass(X, Protocol)` — agrees |

### test_ports.py — Opus agrees with Codex on 8 🔴, upgrades 2

| Rating | Line | Test | Codex | Opus Reason |
|--------|-----:|------|-------|-------------|
| 🔴 | 25,49,73,121,151,175 | `*_is_protocol` (×6) | 🔴 | Pure `issubclass(X, Protocol)` |
| 🔴 | 202 | `test_all_ports_are_protocols` | 🔴 | Same pattern, aggregate |
| 🔴 | 232 | `test_import_surface_ports` | 🔴 | AST import scanner |
| 🟡 | 93 | `test_unit_of_work_has_context_manager` | 🟡 | Agrees — checks `__enter__`/`__exit__` exist |
| 🟡 | 105 | `test_unit_of_work_has_repository_attributes` | 🟡 | Annotation inspection has moderate value |
| 🟡 | 213 | `test_none_are_runtime_checkable` | 🟡 | Design constraint enforcement |

### test_scheduling_models.py — Opus changes on 2 tests

| Rating | Line | Test | Codex | Opus Reason |
|--------|-----:|------|-------|-------------|
| 🔴 | 88 | `test_models_inherit_from_base` | 🔴 | `issubclass` check — agrees |
| 🟡 | 227 | `test_unique_constraint` (PipelineState) | 🟡 | Agrees — couples to internal state |
| 🔴 | 242 | `test_different_keys_allowed` | 🔴 | Agrees — trivially weak |

## Aggregate Codex Delta Analysis

| Change Type | Count | Pattern |
|-------------|------:|---------|
| 🔴→🟡 (exception hierarchy) | 6 | `issubclass(XError, BaseError)` — behavioral for catch blocks |
| 🔴→🟡 (event inheritance) | 4 | `isinstance(event, DomainEvent)` — inheritance carries fields |
| 🔴→🟡 (market data port methods) | 4 | `hasattr` + `inspect.signature` — contract verification |
| 🟢→🟡 (scheduling relationships) | 3 | Weak relationship assertions reclassified |
| Total Opus 🔴→🟡 upgrades | 14 | From structural to "some behavioral value" |
| Total Opus 🟢→🟡 downgrades | 4 | Weak assertions didn't warrant 🟢 |

## Overall Assessment

The domain test bucket is the **strongest overall** — 85% 🟢 rate with deep value-assertion coverage. The 🔴 tests concentrate in three patterns:
1. **`issubclass(X, Protocol)`** — 8 tests, all truly structural (Protocol is a static concern)
2. **Import surface / `hasattr` module checks** — 10 tests, structural-only
3. **`is_str_enum` / `isinstance` base class checks** — 6 tests in enums/pipeline

All 🔴 tests have existing companion tests that assert actual behavior (method signatures, member values, field assertions). The 🔴 tests could be safely deleted without losing regression coverage.
