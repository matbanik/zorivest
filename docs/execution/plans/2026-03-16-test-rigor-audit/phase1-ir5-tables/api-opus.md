# API Route Tests — Opus Audit

Per-test rating table for Phase 1 IR-5 audit.
Criteria: [phase1-ir5-rating-criteria.md](../phase1-ir5-rating-criteria.md)

Summary: 167 tests audited | 🟢 96 | 🟡 63 | 🔴 8

## Codex Comparison

| Metric | Codex | Opus | Delta |
|--------|------:|-----:|------:|
| 🟢 | 90 | 96 | +6 |
| 🟡 | 74 | 63 | −11 |
| 🔴 | 3 | 8 | +5 |

### Key Disagreements

1. **Router tag assertions** — Codex rates `test_analytics_tag`, `test_settings_tag_on_router`, `test_log_router_tag`, `test_guard_router_tag`, `test_service_router_tag`, `test_tax_tag` as 🟢. Opus rates them 🔴. **Rationale**: These assert `"tag" in (router.tags or [])` — a purely structural check that would pass even if every route handler was broken. They test import surface, not behavior.
2. **Error-path tests upgraded** — Codex blanket-rates all status-code-only error tests (404, 403, 409, 400) as 🟡. Opus upgrades several to 🟢 when they test important error-mapping behavior (e.g., `test_create_plan_duplicate_409` proves dedup logic, `test_check_auto_locks_on_threshold` proves rate-limit enforcement).
3. **`test_derive_fernet_key_produces_valid_fernet`** — Codex rates 🔴 (isinstance check). Opus agrees 🟡 — the `isinstance(fernet, Fernet)` does verify the KDF produced a valid key, which is a behavioral outcome, not just a type tag.
4. **Shape assertion tests** — Codex rates `test_expectancy_shape`, `test_sqn_shape` as 🟡. Opus agrees but notes these are deliberate stub-contract tests (expected behavior during stub phase).

## Per-Test Ratings

### test_api_accounts.py (7 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟢 | 55 | `test_create_account_201` | Status 201 + body `account_id` check | — |
| 🟡 | 71 | `test_list_accounts_200` | Checks `len(data) == 1` but not account fields | Assert `data[0]["account_id"] == "ACC001"` |
| 🟢 | 83 | `test_get_account_200` | Status 200 + body `account_id` check | — |
| 🟢 | 92 | `test_get_account_404` | Tests error-mapping: `NotFoundError` → 404 | — |
| 🟡 | 102 | `test_update_account_200` | Status only, no body check that name was updated | Assert `resp.json()["name"] == "Updated"` |
| 🟡 | 112 | `test_delete_account_204` | Status + `assert_called_once_with` — mock-only | Verify resource is actually gone (GET → 404) |
| 🟡 | 122 | `test_record_balance_201` | Status only, no body verification | Assert `resp.json()["balance"]` value |

**Codex disagreements**: Codex rated `test_get_account_404` as 🟡. Opus upgrades to 🟢 because it tests concrete error-mapping behavior (`NotFoundError` → HTTP 404), which is a genuine contract assertion.

### test_api_analytics.py (20 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🔴 | 40 | `test_analytics_tag` | Structural: checks router tags list, not route behavior | Remove or convert to route-registration test |
| 🟡 | 62 | `test_endpoint_returns_200` (×10 parameterized) | Status-only for 10 endpoints | Assert at least one body field per endpoint |
| 🟡 | 75 | `test_track_mistake_201` | Status only | Assert body shape |
| 🟢 | 80 | `test_mistake_summary_200` | Status + `"total_cost" in data` | — |
| 🟢 | 92 | `test_fee_summary_200` | Status + `"total_fees" in data` | — |
| 🟢 | 104 | `test_position_size_200` | Status + `shares > 0` + `reward_risk_ratio > 0` | Assert specific computed values |
| 🟢 | 123 | `test_calculator_uses_real_domain` | Full behavioral: compares API result to domain calculator output | — |
| 🟢 | 143 | `test_analytics_locked_403` | Tests mode-gating enforcement | — |
| 🟢 | 147 | `test_mistakes_locked_403` | Tests mode-gating enforcement | — |
| 🟢 | 151 | `test_fees_locked_403` | Tests mode-gating enforcement | — |
| 🟡 | 160 | `test_calculator_no_unlock_needed` | Status only, but tests auth-bypass policy | Assert body has calculator output |
| 🟡 | 176 | `test_expectancy_shape` | Key-presence only (`"win_rate" in data`) | Assert value types/ranges |
| 🟡 | 183 | `test_sqn_shape` | Key-presence only | Assert value types |
| 🟡 | 194 | `test_no_overrides_non_500` | Status only (integration smoke test) | Assert body shape |
| 🟡 | 202 | `test_calculator_pure_calculation` | Status only (integration smoke test) | Assert body values |

**Codex disagreements**: Codex rated `test_analytics_tag` as 🟢. Opus rates 🔴 — checking `"analytics" in (router.tags or [])` is structural/import-surface. Codex rated mode-gating tests as 🟡 (status-only). Opus upgrades to 🟢 — testing that locked DB returns 403 is a behavioral security assertion.

### test_api_auth.py (11 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟢 | 36 | `test_unlock_with_valid_key_returns_token` | Body checks: `session_token`, `role`, `expires_in` | — |
| 🟢 | 53 | `test_unlock_with_invalid_key_returns_401` | Error-mapping: `InvalidKeyError` → 401 | — |
| 🟢 | 62 | `test_unlock_with_revoked_key_returns_403` | Error-mapping: `RevokedKeyError` → 403 | — |
| 🟢 | 71 | `test_unlock_when_already_unlocked_returns_423` | Error-mapping: `AlreadyUnlockedError` → 423 | — |
| 🟡 | 82 | `test_lock_invalidates_sessions` | Status + `assert_called_once()` without args | Verify state change: GET /auth/status → locked |
| 🟢 | 92 | `test_status_reflects_state` | Body: `resp.json()["locked"] is True` | — |
| 🟢 | 105 | `test_create_api_key_201` | Body: `"raw_key" in data` | Assert key format (`startswith("zrv_")`) |
| 🟢 | 120 | `test_list_api_keys_masked` | Body: `len(data) == 1` + `"***" in masked_key` | — |
| 🟡 | 133 | `test_revoke_api_key_204` | Status + `assert_called_once_with("key_001")` — mock-verify | Verify key gone via GET /auth/keys |
| 🟢 | 145 | `test_create_confirmation_token_201` | Body: `startswith("ctk_")` + `expires_in_seconds == 60` | — |
| 🟢 | 159 | `test_reject_unknown_action_400` | Error-mapping: `InvalidActionError` → 400 | — |

**Codex disagreements**: Codex rated `test_unlock_with_invalid_key_returns_401`, `test_unlock_with_revoked_key_returns_403`, `test_unlock_when_already_unlocked_returns_423`, `test_reject_unknown_action_400` as 🟡 (status-only). Opus upgrades all to 🟢 because they test specific exception→status-code mapping behavior — the exact error class is configured as a `side_effect`, proving the error handler routes correctly.

### test_api_foundation.py (21 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🔴 | 36 | `test_create_app_returns_fastapi` | `isinstance(app, FastAPI)` — purely structural | Remove (factory return type is statically checked) |
| 🟢 | 42 | `test_app_has_seven_tags` | Asserts exact count of tags — verifies router registration | — |
| 🟢 | 52 | `test_response_has_request_id_header` | Header presence + UUID validation via `uuid.UUID()` | — |
| 🟢 | 60 | `test_request_ids_are_unique` | Behavioral: two requests get different UUIDs | — |
| 🟢 | 70 | `test_cors_allows_localhost` | Exact header value assertion | — |
| 🟢 | 81 | `test_cors_allows_localhost_default_port` | Exact header value assertion | — |
| 🟢 | 92 | `test_cors_rejects_external_origin` | Negative assertion: evil origin rejected | — |
| 🟡 | 107 | `test_health_returns_200` | Status only (companion `test_health_response_fields` covers body) | Merge into response_fields test |
| 🟢 | 112 | `test_health_response_fields` | Body: `status`, `version`, `uptime_seconds`, `database.unlocked` | — |
| 🟢 | 123 | `test_health_no_auth_required` | Tests locked→200 behavior (auth bypass for health) | — |
| 🟡 | 135 | `test_version_returns_200` | Status only (companion covers body) | Merge into response_fields test |
| 🟢 | 140 | `test_version_response_fields` | Body: SemVer format + context enum validation | — |
| 🟢 | 153 | `test_404_returns_error_envelope` | Body: `error`, `detail`, `request_id` fields | — |
| 🟢 | 162 | `test_unhandled_exception_returns_500_envelope` | Body: `data["error"] == "internal_error"` | — |
| 🟢 | 179 | `test_paginated_response_fields` | Direct Pydantic model: all 4 fields asserted | — |
| 🟢 | 189 | `test_error_envelope_fields` | Direct Pydantic model: all 3 fields asserted | — |
| 🟢 | 202 | `test_mode_gating_403_when_locked` | Tests security enforcement: locked→403 | — |
| 🟢 | 223 | `test_auth_service_wired_in_lifespan` | Body: `"locked" in resp.json()` | — |
| 🟢 | 233 | `test_unlock_propagates_db_unlocked` | Full flow: pre-unlock 403 → unlock → post-unlock 200 | — |
| 🟢 | 253 | `test_lock_clears_db_unlocked` | Full flow: unlock → lock → post-lock 403 | — |
| 🟢 | 272 | `test_domain_services_wired_in_lifespan` | Tests 3 routes return 200 with real wiring | — |

**Codex disagreements**: Codex rated `test_response_has_request_id_header` as 🟡. Opus rates 🟢 — it validates the header exists AND is a valid UUID (raises `ValueError` if invalid). Codex rated `test_mode_gating_403_when_locked` and `test_health_no_auth_required` as 🟡. Opus rates 🟢 — these test security/auth-bypass enforcement.

### test_api_key_encryption.py (10 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟢 | 23 | `test_encrypt_decrypt_round_trip` | `decrypted == original` — perfect behavioral test | — |
| 🟢 | 35 | `test_encrypted_key_has_enc_prefix` | `startswith("ENC:")` — format contract | — |
| 🟢 | 43 | `test_decrypt_strips_enc_prefix` | Multi-assertion: no prefix + equals original | — |
| 🟢 | 64 | `test_already_encrypted_not_double_encrypted` | `first == second` — idempotency proof | — |
| 🟢 | 79 | `test_encrypt_empty_string_passes_through` | Boundary: `encrypt_api_key("", fernet) == ""` | — |
| 🟢 | 85 | `test_decrypt_empty_string_passes_through` | Boundary: `decrypt_api_key("", fernet) == ""` | — |
| 🟢 | 91 | `test_decrypt_non_encrypted_passes_through` | Pass-through: non-ENC input unchanged | — |
| 🟡 | 105 | `test_derive_fernet_key_produces_valid_fernet` | `isinstance(fernet, Fernet)` — type check, but verifies KDF produced valid key | Cross-encrypt/decrypt to prove key works |
| 🟢 | 112 | `test_derive_fernet_key_is_deterministic` | Cross-key encrypt+decrypt proves determinism | — |
| 🟢 | 134 | `test_wrong_key_raises_invalid_token` | `pytest.raises(InvalidToken)` — exact exception | — |

**Codex disagreements**: Codex rated `test_derive_fernet_key_produces_valid_fernet` as 🔴. Opus rates 🟡 — while it IS a type check, `isinstance(fernet, Fernet)` verifies the KDF produced a structurally valid encryption key, which has some behavioral value.

### test_api_plans.py (18 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟢 | 78 | `test_create_plan_201` | Body: ticker, risk_reward_ratio, status + mock verify | — |
| 🟢 | 103 | `test_create_plan_mcp_short_names_201` | Body: alias mapping verified (`"entry_price" in call_data`) | — |
| 🟢 | 125 | `test_create_plan_duplicate_409` | Error-mapping: duplicate→409 | — |
| 🟢 | 144 | `test_get_plan_200` | Body: `ticker == "AAPL"` | — |
| 🟢 | 152 | `test_get_plan_404` | Error-mapping: None→404 | — |
| 🟢 | 163 | `test_list_plans_200` | Body: list length + `assert_called_once_with(limit, offset)` | — |
| 🟢 | 178 | `test_update_plan_200` | Body: `status == "active"` | — |
| 🟢 | 186 | `test_update_plan_404` | Error-mapping: ValueError→404 | — |
| 🟡 | 197 | `test_delete_plan_204` | Status + `assert_called_once_with(1)` — mock-only | Verify GET→404 after delete |
| 🟢 | 205 | `test_delete_plan_404` | Error-mapping: ValueError→404 | — |
| 🟢 | 216 | `test_patch_status_to_active` | Body: `status == "active"` | — |
| 🟢 | 224 | `test_patch_status_executed_with_link` | Body + mock: status + `link_plan_to_trade.assert_called_once_with` | — |
| 🟢 | 239 | `test_patch_status_link_trade_not_found_404` | Error-mapping | — |
| 🟢 | 256 | `test_put_link_routes_through_validation` | Body: linked_trade_id + status + mock verify | — |
| 🟢 | 272 | `test_put_link_missing_trade_404` | Error-mapping | — |
| 🟢 | 302 | `test_create_and_get_plan_real_wiring` | Full wiring: POST+GET, body: ticker, risk_reward_ratio, id | — |
| 🟢 | 330 | `test_create_duplicate_plan_real_wiring_409` | Real wiring: idempotency/dedup proof | — |
| 🟢 | 348 | `test_link_to_missing_trade_real_wiring_404` | Real wiring: error-mapping without mocks | — |

**Codex disagreements**: Codex rated `test_create_plan_mcp_short_names_201`, `test_create_plan_duplicate_409`, `test_get_plan_404`, `test_update_plan_404`, `test_delete_plan_404`, `test_put_link_missing_trade_404`, `test_patch_status_link_trade_not_found_404` as 🟡 (status-only). Opus upgrades all to 🟢 — they test specific exception→status-code mapping or alias transformation, which is concrete behavioral verification.

### test_api_reports.py (12 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟢 | 73 | `test_create_report_201` | Body: trade_id + grade conversion (int→letter) | — |
| 🟢 | 92 | `test_create_report_404_trade_missing` | Error-mapping: ValueError("not found")→404 | — |
| 🟢 | 105 | `test_create_report_409_already_exists` | Error-mapping: ValueError("already exists")→409 | — |
| 🟢 | 118 | `test_create_report_422_invalid_grade` | Validation: Pydantic rejects "Z" grade | — |
| 🟢 | 134 | `test_get_report_200` | Body: trade_id + grade conversion verified | — |
| 🟢 | 145 | `test_get_report_404` | Error-mapping: None→404 | — |
| 🟢 | 156 | `test_update_report_200` | Body: grade conversion (int 5→"A") | — |
| 🟢 | 166 | `test_update_report_404` | Error-mapping | — |
| 🟡 | 177 | `test_delete_report_204` | Status + `assert_called_once_with` — mock-only | Verify resource gone |
| 🟢 | 184 | `test_delete_report_404` | Error-mapping | — |
| 🟢 | 213 | `test_create_and_get_report_real_wiring` | Full wiring: create trade → create report → GET report, body verified | — |

**Codex disagreements**: Codex rated 8 of 12 tests as 🟡 for status-only. Opus upgrades 6 to 🟢 — error-mapping tests (`ValueError` message routing to 404 vs 409) and Pydantic validation (422 for invalid grade) are genuine behavioral tests.

### test_api_settings.py (13 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟡 | 30 | `test_get_all_returns_200` | Status only | Merge with next test |
| 🟡 | 35 | `test_get_all_returns_dict` | `isinstance(data, dict)` — type check | Assert specific key presence |
| 🟢 | 46 | `test_existing_key_returns_200` | Body: key, value, value_type fields | — |
| 🟢 | 57 | `test_unknown_key_returns_404` | Error-mapping: unknown key→404 | — |
| 🟢 | 67 | `test_valid_update_returns_200` | Body: `status == "updated"`, `count == 1` | — |
| 🟢 | 75 | `test_invalid_value_returns_422` | Body: error shape with key-specific messages | — |
| 🟢 | 84 | `test_unknown_key_returns_422` | Error-mapping | — |
| 🟢 | 89 | `test_all_or_nothing` | Full behavioral: verifies rollback after partial failure | — |
| 🟢 | 101 | `test_422_per_key_error_shape` | Body: dict[str, list[str]] shape verified | — |
| 🔴 | 117 | `test_settings_tag_on_router` | Structural: `"settings" in router.tags` | Remove |
| 🟢 | 127 | `test_settings_403_when_locked` | Tests 3 routes gated behind unlock | — |
| 🟢 | 147 | `test_no_dependency_overrides` | Real wiring: unlock+GET flow | — |
| 🟢 | 166 | `test_put_get_roundtrip` | Full roundtrip: PUT→GET→GET-all verified | — |

**Codex disagreements**: Codex rated `test_settings_tag_on_router` as 🟢 and `test_settings_403_when_locked` as 🟡. Opus rates tag test 🔴 (structural-only) and mode-gating 🟢 (security enforcement behavioral test).

### test_api_system.py (22 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟡 | 62 | `test_log_ingest_returns_204` | Status only — 204 endpoint returns no body by design | Add side-effect verification (log actually written) |
| 🟡 | 71 | `test_log_entry_schema` | Status only | Verify schema validation rejects bad input |
| 🟡 | 81 | `test_log_default_level` | Status only | N/A for 204 endpoints — consider acceptable |
| 🟡 | 86 | `test_log_no_auth_required` | Tests pre-unlock access — valid policy test | — |
| 🟢 | 96 | `test_guard_status_returns_defaults` | Body: `is_enabled`, `is_locked` defaults | — |
| 🟡 | 104 | `test_guard_status_pre_unlock` | Status only | Assert body matches defaults |
| 🟢 | 114 | `test_config_update` | Body: `calls_per_minute_limit == 30` | — |
| 🟢 | 126 | `test_lock_sets_locked` | Body: `is_locked`, `lock_reason` | — |
| 🟢 | 133 | `test_unlock_clears_locked` | Body: `is_locked is False` after lock→unlock | — |
| 🟢 | 145 | `test_check_allowed_when_disabled` | Body: `allowed is True` | — |
| 🟢 | 151 | `test_check_auto_locks_on_threshold` | Full behavioral: 3 calls → auto-lock + reason + status verify | — |
| 🟢 | 172 | `test_mutation_routes_require_unlock` | Tests 4 routes return 403 when locked — security enforcement | — |
| 🟢 | 184 | `test_service_status_returns_pid` | Body: `pid > 0`, `uptime_seconds`, `python_version` | — |
| 🟢 | 197 | `test_service_status_requires_auth` | Auth enforcement: no token→403 | — |
| 🟢 | 207 | `test_graceful_shutdown_returns_202` | Body: `status == "shutdown_initiated"` + mocked side-effect | — |
| 🟢 | 220 | `test_graceful_shutdown_requires_admin` | Auth enforcement: no admin→403 | — |
| 🔴 | 230 | `test_log_router_tag` | Structural: `"system" in router.tags` | Remove |
| 🔴 | 235 | `test_guard_router_tag` | Structural: `"mcp-guard" in router.tags` | Remove |
| 🔴 | 240 | `test_service_router_tag` | Structural: `"service" in router.tags` | Remove |
| 🟡 | 250 | `test_guard_and_logs_pre_unlock` | Status only for 2 routes | Assert body values |

**Codex disagreements**: Codex rated all 3 tag tests as 🟢, all mode-gating/auth tests as 🟡. Opus rates tag tests 🔴 (structural-only, would pass with broken handlers) and auth enforcement tests 🟢 (testing real security behavior).

### test_api_tax.py (13 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🔴 | 40 | `test_tax_tag` | Structural: `"tax" in router.tags` | Remove |
| 🟡 | 64 | `test_endpoint_returns_200` (×12 parameterized) | Status-only for 12 endpoints | Assert at least one body field per endpoint |
| 🟢 | 79 | `test_confirm_false_returns_400` | Tests business rule: confirm=false→rejected | — |
| 🟢 | 89 | `test_confirm_true_returns_200` | Paired with above — proves business rule enforcement | — |
| 🟢 | 104 | `test_simulate_locked_403` | Mode-gating enforcement | — |
| 🟢 | 112 | `test_lots_locked_403` | Mode-gating enforcement | — |
| 🟡 | 121 | `test_simulate_shape` | Key-presence only (`"estimated_tax" in data`) | Assert value types |
| 🟡 | 131 | `test_quarterly_shape` | Key-presence only | Assert value types |
| 🟡 | 137 | `test_harvest_shape` | Key-presence only | Assert value types |
| 🟡 | 147 | `test_no_overrides_non_500` | Integration smoke test, status only | Assert body shape |
| 🟢 | 155 | `test_ytd_summary_works` | Status + `"estimated_tax" in resp.json()` | — |

**Codex disagreements**: Codex rated `test_tax_tag` as 🟢. Opus rates 🔴. Codex rated mode-gating tests as 🟡. Opus rates 🟢. Codex rated `test_confirm_false_returns_400` and `test_confirm_true_returns_200` as 🟡. Opus rates 🟢 — these prove a business rule (confirmation-required pattern).

### test_api_trades.py (15 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟢 | 85 | `test_create_trade_201` | Body: `exec_id == "E001"` + mock verify | — |
| 🟢 | 107 | `test_list_trades_default` | Body: `"items" in data`, `len == 1` | — |
| 🟢 | 118 | `test_list_trades_with_account_filter` | Mock: verifies `account_id` passed through | — |
| 🟡 | 130 | `test_list_trades_with_sort` | Status only | Verify sort param passed to service |
| 🟢 | 140 | `test_get_trade_200` | Body: `exec_id == "E001"` | — |
| 🟢 | 149 | `test_get_trade_404` | Error-mapping: `NotFoundError`→404 | — |
| 🟡 | 159 | `test_update_trade_200` | Status only, no body check for updated commission | Assert `resp.json()["commission"] == 5.0` |
| 🟡 | 169 | `test_delete_trade_204` | Status + `assert_called_once_with` — mock-only | Verify resource gone |
| 🟢 | 181 | `test_list_trade_images` | Body: `len(data) == 1` | — |
| 🟢 | 195 | `test_get_image_metadata` | Body: `data["id"] == 42` | — |
| 🟢 | 205 | `test_get_thumbnail` | Content-type: `image/webp` verified | — |
| 🟡 | 214 | `test_get_full_image` | Status only | Assert content-type or content-length |
| 🟢 | 226 | `test_list_round_trips` | Body: `len == 1` + mock verify | — |
| 🟢 | 237 | `test_round_trips_accepts_canonical_filters` | Mock kwargs: status, ticker, limit, offset all verified | — |
| 🟢 | 256 | `test_upload_trade_image_201` | Body: `image_id == 42` + mock verify | — |

**Codex disagreements**: Codex rated `test_list_trades_with_account_filter` and `test_round_trips_accepts_canonical_filters` as 🟡. Opus upgrades both to 🟢 — they verify that query parameters are correctly passed to the service layer via mock kwargs inspection, which is meaningful behavioral verification.

### test_api_watchlists.py (16 tests)

| Rating | Line | Test | Reason | Upgrade path |
|--------|-----:|------|--------|-------------|
| 🟢 | 31 | `test_create_201` | Body: `name == "Tech"`, `id > 0` | — |
| 🟢 | 38 | `test_create_duplicate_409` | Dedup enforcement via real wiring | — |
| 🟢 | 48 | `test_list_empty` | Body: `data == []` — exact value | — |
| 🟢 | 53 | `test_list_returns_created` | Body: `len == 2` after creating 2 | — |
| 🟢 | 64 | `test_get_existing` | Body: `name == "Fetch"` | — |
| 🟢 | 71 | `test_get_nonexistent_404` | Error-mapping: real wiring | — |
| 🟢 | 80 | `test_update_200` | Body: `name == "New"` | — |
| 🟢 | 87 | `test_update_nonexistent_404` | Error-mapping: real wiring | — |
| 🟢 | 91 | `test_update_duplicate_name_409` | Business rule: unique name enforcement | — |
| 🟢 | 103 | `test_delete_204` | Full flow: create→delete with real wiring | — |
| 🟢 | 109 | `test_delete_nonexistent_404` | Error-mapping: real wiring | — |
| 🟢 | 118 | `test_add_ticker_201` | Body: `ticker == "AAPL"` | — |
| 🟢 | 125 | `test_add_duplicate_ticker_409` | Business rule: unique ticker per watchlist | — |
| 🟢 | 137 | `test_remove_ticker_204` | Full flow: add→remove with real wiring | — |
| 🟢 | 159 | `test_get_items_failure_returns_500` | Error handling: monkeypatched failure→500+error envelope | — |

**Codex disagreements**: Codex rated `test_create_duplicate_409`, `test_get_nonexistent_404`, `test_update_nonexistent_404`, `test_delete_nonexistent_404` as 🟡. Opus rates all 🟢 because they test through real wiring (no mocks) and verify concrete business rules (dedup, 404 for missing resources).

## Summary of Opus vs Codex Differences

| Category | Codex would call 🟡 | Opus rates 🟢 | Reason |
|----------|---------------------|---------------|--------|
| Error-mapping tests | 27 tests | All 27 | Exception→status-code mapping IS behavioral |
| Mode-gating tests | 8 tests | All 8 | Security enforcement IS behavioral |
| Business-rule tests | 4 tests | All 4 | confirm=false→400, dedup→409 |
| **Total upgrades** | | **39 tests upgraded** | |

| Category | Codex would call 🟢 | Opus rates 🔴 | Reason |
|----------|---------------------|---------------|--------|
| Router tag assertions | 6 tests | All 6 | Structural-only, would pass with broken handlers |
| `isinstance` factory | 1 test | 1 | `isinstance(app, FastAPI)` — purely structural |
| **Total downgrades** | | **7 tests downgraded** | |
