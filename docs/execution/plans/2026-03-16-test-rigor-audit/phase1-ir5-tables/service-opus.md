# Service Layer Tests — Opus Audit

Per-test rating table for Phase 1 IR-5 audit.
Criteria: [phase1-ir5-rating-criteria.md](../phase1-ir5-rating-criteria.md)

Summary: 268 tests audited | 🟢 227 | 🟡 35 | 🔴 6

## Codex Comparison

| Metric | Codex | Opus | Delta |
|--------|------:|-----:|------:|
| 🟢 | 220 | 227 | +7 |
| 🟡 | 35 | 35 | 0 |
| 🔴 | 13 | 6 | −7 |

### Key Disagreements

1. **Delete tests** — Codex rates 5 delete-success tests as 🔴 ("trivially weak / no assertions"). Opus upgrades to 🟡. **Rationale**: Each verifies `repo.delete.assert_called_once_with(correct_id)` + `commit.assert_called_once()` — this IS a meaningful service-layer contract (correct ID dispatched, transaction committed). Weak but not tautological.
2. **Rate limiter behavioral tests** — Codex rates `test_blocks_when_full` and `test_burst_completes_without_blocking` as 🔴 ("private patch"). Opus upgrades both to 🟢. **Rationale**: These patch `asyncio.sleep` (a public stdlib API, not a private attribute) and verify it's called/not-called — that IS the behavioral contract of a rate limiter.
3. **Module export `hasattr` tests** — Codex rates 3 module export tests as 🔴. Opus agrees on 2, upgrades 1 from 🟡 to 🟢 where it also checks `no_unexpected_exports`.
4. **Unknown-provider error** — Codex rates `test_unknown_provider_raises` as 🔴 ("swallows exceptions"). Opus upgrades to 🟡 — the test does verify `pytest.raises(ValueError)` which is a concrete contract assertion.

## Sections with Codex Disagreements

### Delete Tests — Opus upgrades 5 from 🔴 to 🟡

| Rating | File | Line | Test | Codex | Opus Reason |
|--------|------|-----:|------|-------|-------------|
| 🟡 | `test_report_service.py` | 170 | `test_delete_removes_report` | 🔴 | `delete(42)` + `commit` + `__enter__` verified |
| 🟡 | `test_report_service.py` | 428 | `test_delete_plan_success` | 🔴 | `delete(1)` + `commit` verified |
| 🟡 | `test_service_extensions.py` | 140 | `test_delete_trade_success` | 🔴 | `delete("E001")` + `commit` verified |
| 🟡 | `test_service_extensions.py` | 183 | `test_delete_account_success` | 🔴 | `delete("ACC001")` + `commit` verified |
| 🟡 | `test_image_service.py` | 28 | `test_attach_image_success` | 🟡 | Agrees — mock call without value checks |

**Upgrade path for all 4**: Add post-condition verification (GET → NotFoundError, or verify repo state).

### Rate Limiter — Opus upgrades 2 from 🔴 to 🟢

| Rating | File | Line | Test | Codex | Opus Reason |
|--------|------|-----:|------|-------|-------------|
| 🟢 | `test_rate_limiter.py` | 38 | `test_blocks_when_full` | 🔴 | After N calls, N+1 triggers `asyncio.sleep` — behavioral |
| 🟢 | `test_rate_limiter.py` | 73 | `test_burst_completes_without_blocking` | 🔴 | N calls complete without sleep — behavioral |

### Market Data & System — Opus agrees/adjusts

| Rating | File | Line | Test | Codex | Opus Reason |
|--------|------|-----:|------|-------|-------------|
| 🔴 | `test_market_data_service.py` | 299 | `test_rate_limiter_called_before_http_request` | 🔴 | Agrees — patches private `_http_get`, mock-only |
| 🟡 | `test_provider_connection_service.py` | 380 | `test_unknown_provider_raises` | 🔴 | `pytest.raises(ValueError)` IS a contract assertion |
| 🔴 | `test_system_service.py` | 29 | `test_calculate_returns_frozen_dataclass` | 🔴 | Agrees — `isinstance` + 6× `hasattr` without values |
| 🔴 | `test_analytics.py` | 353 | `test_results_module_exports` | 🔴 | Agrees — pure `hasattr` |
| 🔴 | `test_analytics.py` | 376 | `test_expectancy_module_exports` | 🔴 | Agrees — pure `hasattr` |
| 🔴 | `test_analytics.py` | 382 | `test_sqn_module_exports` | 🔴 | Agrees — pure `hasattr` |
| 🔴 | `test_settings_registry.py` | 59 | `test_every_entry_is_setting_spec` | 🔴 | Agrees — pure `isinstance` |

## Aggregate Codex Delta Analysis

| Change Type | Count | Pattern |
|-------------|------:|---------|
| 🔴→🟡 (delete-success tests) | 4 | `delete(id)` + `commit` mock verification |
| 🔴→🟢 (rate limiter) | 2 | `asyncio.sleep` behavioral mocking |
| 🔴→🟡 (unknown provider) | 1 | `pytest.raises(ValueError)` is a contract |
| Total changes | 7 | 7 of 13 Codex 🔴s upgraded |

## Overall Assessment

The service bucket is **strong** — 85% 🟢 rate. The 🔴s that remain are:
1. Module export `hasattr` checks (3 tests) — could be deleted without losing coverage
2. `isinstance` + `hasattr` field check (1 test) — subsumed by companion test
3. Private `_http_get` mock (1 test) — implementation-coupled
4. `isinstance(SettingSpec)` check (1 test) — structural only

Service tests are generally well-designed with proper UoW mocking, exception verification, and behavioral assertions. The main weakness is delete-path tests that verify mock calls without post-conditions.
