# API Route Tests

Per-test rating table for Phase 1 IR-5 audit.

Summary: 167 tests audited | 🟢 90 | 🟡 74 | 🔴 3

| Rating | File | Line | Test | Reason |
|---|---|---:|---|---|
| 🟢 | `tests/unit/test_api_accounts.py` | 55 | `TestCreateAccount.test_create_account_201` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_accounts.py` | 71 | `TestListAccounts.test_list_accounts_200` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_accounts.py` | 83 | `TestGetAccount.test_get_account_200` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_accounts.py` | 92 | `TestGetAccount.test_get_account_404` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_accounts.py` | 102 | `TestUpdateAccount.test_update_account_200` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_accounts.py` | 112 | `TestDeleteAccount.test_delete_account_204` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_accounts.py` | 122 | `TestRecordBalance.test_record_balance_201` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_analytics.py` | 40 | `TestAnalyticsRouterTag.test_analytics_tag` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_analytics.py` | 62 | `TestAnalyticsEndpoints.test_endpoint_returns_200` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_analytics.py` | 75 | `TestMistakesRoutes.test_track_mistake_201` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_analytics.py` | 80 | `TestMistakesRoutes.test_mistake_summary_200` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_analytics.py` | 92 | `TestFeesRoute.test_fee_summary_200` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_analytics.py` | 104 | `TestCalculatorRoute.test_position_size_200` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_analytics.py` | 123 | `TestCalculatorDomain.test_calculator_uses_real_domain` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_analytics.py` | 143 | `TestModeGating.test_analytics_locked_403` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_analytics.py` | 147 | `TestModeGating.test_mistakes_locked_403` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_analytics.py` | 151 | `TestModeGating.test_fees_locked_403` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_analytics.py` | 160 | `TestCalculatorNoAuth.test_calculator_no_unlock_needed` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_analytics.py` | 176 | `TestStubShapes.test_expectancy_shape` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_api_analytics.py` | 183 | `TestStubShapes.test_sqn_shape` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_api_analytics.py` | 194 | `TestAnalyticsIntegration.test_no_overrides_non_500` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_analytics.py` | 202 | `TestAnalyticsIntegration.test_calculator_pure_calculation` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_auth.py` | 36 | `TestUnlock.test_unlock_with_valid_key_returns_token` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_auth.py` | 53 | `TestUnlock.test_unlock_with_invalid_key_returns_401` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_auth.py` | 62 | `TestUnlock.test_unlock_with_revoked_key_returns_403` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_auth.py` | 71 | `TestUnlock.test_unlock_when_already_unlocked_returns_423` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_auth.py` | 82 | `TestLock.test_lock_invalidates_sessions` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_auth.py` | 92 | `TestAuthStatus.test_status_reflects_state` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_auth.py` | 105 | `TestApiKeyManagement.test_create_api_key_201` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_auth.py` | 120 | `TestApiKeyManagement.test_list_api_keys_masked` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_auth.py` | 133 | `TestApiKeyManagement.test_revoke_api_key_204` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_auth.py` | 145 | `TestConfirmationTokens.test_create_confirmation_token_201` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_auth.py` | 159 | `TestConfirmationTokens.test_reject_unknown_action_400` | status-code assertion without response body verification |
| 🔴 | `tests/unit/test_api_foundation.py` | 36 | `TestAppFactory.test_create_app_returns_fastapi` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_api_foundation.py` | 42 | `TestAppFactory.test_app_has_seven_tags` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_foundation.py` | 52 | `TestRequestIdMiddleware.test_response_has_request_id_header` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_api_foundation.py` | 60 | `TestRequestIdMiddleware.test_request_ids_are_unique` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_foundation.py` | 70 | `TestCors.test_cors_allows_localhost` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_foundation.py` | 81 | `TestCors.test_cors_allows_localhost_default_port` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_foundation.py` | 92 | `TestCors.test_cors_rejects_external_origin` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_foundation.py` | 107 | `TestHealthEndpoint.test_health_returns_200` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_foundation.py` | 112 | `TestHealthEndpoint.test_health_response_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_foundation.py` | 123 | `TestHealthEndpoint.test_health_no_auth_required` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_foundation.py` | 135 | `TestVersionEndpoint.test_version_returns_200` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_foundation.py` | 140 | `TestVersionEndpoint.test_version_response_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_foundation.py` | 153 | `TestErrorEnvelope.test_404_returns_error_envelope` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_foundation.py` | 162 | `TestErrorEnvelope.test_unhandled_exception_returns_500_envelope` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_foundation.py` | 179 | `TestSchemas.test_paginated_response_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_foundation.py` | 189 | `TestSchemas.test_error_envelope_fields` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_foundation.py` | 202 | `TestModeGating.test_mode_gating_403_when_locked` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_foundation.py` | 223 | `TestAppStateWiring.test_auth_service_wired_in_lifespan` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_foundation.py` | 233 | `TestAppStateWiring.test_unlock_propagates_db_unlocked` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_foundation.py` | 253 | `TestAppStateWiring.test_lock_clears_db_unlocked` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_foundation.py` | 272 | `TestAppStateWiring.test_domain_services_wired_in_lifespan` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 23 | `TestEncryptDecryptRoundTrip.test_encrypt_decrypt_round_trip` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 35 | `TestEncryptDecryptRoundTrip.test_encrypted_key_has_enc_prefix` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 43 | `TestEncryptDecryptRoundTrip.test_decrypt_strips_enc_prefix` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 64 | `TestIdempotentEncrypt.test_already_encrypted_not_double_encrypted` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 79 | `TestPassThrough.test_encrypt_empty_string_passes_through` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 85 | `TestPassThrough.test_decrypt_empty_string_passes_through` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 91 | `TestPassThrough.test_decrypt_non_encrypted_passes_through` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_api_key_encryption.py` | 105 | `TestDeriveFernetKey.test_derive_fernet_key_produces_valid_fernet` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 112 | `TestDeriveFernetKey.test_derive_fernet_key_is_deterministic` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_key_encryption.py` | 134 | `TestWrongKeyRaises.test_wrong_key_raises_invalid_token` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_api_plans.py` | 78 | `TestCreatePlan.test_create_plan_201` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_plans.py` | 103 | `TestCreatePlan.test_create_plan_mcp_short_names_201` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_plans.py` | 125 | `TestCreatePlan.test_create_plan_duplicate_409` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_plans.py` | 144 | `TestGetPlan.test_get_plan_200` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_plans.py` | 152 | `TestGetPlan.test_get_plan_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_plans.py` | 163 | `TestListPlans.test_list_plans_200` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_plans.py` | 178 | `TestUpdatePlan.test_update_plan_200` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_plans.py` | 186 | `TestUpdatePlan.test_update_plan_404` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_plans.py` | 197 | `TestDeletePlan.test_delete_plan_204` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_plans.py` | 205 | `TestDeletePlan.test_delete_plan_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_plans.py` | 216 | `TestPatchPlanStatus.test_patch_status_to_active` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_plans.py` | 224 | `TestPatchPlanStatus.test_patch_status_executed_with_link` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_plans.py` | 239 | `TestPatchPlanStatus.test_patch_status_link_trade_not_found_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_plans.py` | 256 | `TestPlanLinkingViaPUT.test_put_link_routes_through_validation` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_plans.py` | 272 | `TestPlanLinkingViaPUT.test_put_link_missing_trade_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_plans.py` | 302 | `TestPlanRouteWiring.test_create_and_get_plan_real_wiring` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_plans.py` | 330 | `TestPlanRouteWiring.test_create_duplicate_plan_real_wiring_409` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_plans.py` | 348 | `TestPlanRouteWiring.test_link_to_missing_trade_real_wiring_404` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_reports.py` | 73 | `TestCreateReport.test_create_report_201` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_reports.py` | 92 | `TestCreateReport.test_create_report_404_trade_missing` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_reports.py` | 105 | `TestCreateReport.test_create_report_409_already_exists` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_reports.py` | 118 | `TestCreateReport.test_create_report_422_invalid_grade` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_reports.py` | 134 | `TestGetReport.test_get_report_200` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_reports.py` | 145 | `TestGetReport.test_get_report_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_reports.py` | 156 | `TestUpdateReport.test_update_report_200` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_reports.py` | 166 | `TestUpdateReport.test_update_report_404` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_reports.py` | 177 | `TestDeleteReport.test_delete_report_204` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_reports.py` | 184 | `TestDeleteReport.test_delete_report_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_reports.py` | 213 | `TestReportRouteWiring.test_create_and_get_report_real_wiring` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_settings.py` | 30 | `TestGetAllSettings.test_get_all_returns_200` | status-code assertion without response body verification |
| 🔴 | `tests/unit/test_api_settings.py` | 35 | `TestGetAllSettings.test_get_all_returns_dict` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_api_settings.py` | 46 | `TestGetSettingByKey.test_existing_key_returns_200` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_settings.py` | 57 | `TestGetSettingByKey.test_unknown_key_returns_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_settings.py` | 67 | `TestBulkUpdateSettings.test_valid_update_returns_200` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_settings.py` | 75 | `TestBulkUpdateSettings.test_invalid_value_returns_422` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_settings.py` | 84 | `TestBulkUpdateSettings.test_unknown_key_returns_422` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_settings.py` | 89 | `TestBulkUpdateSettings.test_all_or_nothing` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_settings.py` | 101 | `TestBulkUpdateSettings.test_422_per_key_error_shape` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_settings.py` | 117 | `TestSettingsTag.test_settings_tag_on_router` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_settings.py` | 127 | `TestSettingsModeGating.test_settings_403_when_locked` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_settings.py` | 147 | `TestSettingsIntegration.test_no_dependency_overrides` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_settings.py` | 166 | `TestSettingsRoundtrip.test_put_get_roundtrip` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_system.py` | 62 | `TestLogIngestion.test_log_ingest_returns_204` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_system.py` | 71 | `TestLogIngestion.test_log_entry_schema` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_system.py` | 81 | `TestLogIngestion.test_log_default_level` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_system.py` | 86 | `TestLogIngestion.test_log_no_auth_required` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_system.py` | 96 | `TestMcpGuardStatus.test_guard_status_returns_defaults` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_system.py` | 104 | `TestMcpGuardStatus.test_guard_status_pre_unlock` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_system.py` | 114 | `TestMcpGuardConfig.test_config_update` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_system.py` | 126 | `TestMcpGuardLockUnlock.test_lock_sets_locked` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_system.py` | 133 | `TestMcpGuardLockUnlock.test_unlock_clears_locked` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_system.py` | 145 | `TestMcpGuardCheck.test_check_allowed_when_disabled` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_system.py` | 151 | `TestMcpGuardCheck.test_check_auto_locks_on_threshold` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_system.py` | 172 | `TestMcpGuardAuth.test_mutation_routes_require_unlock` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_system.py` | 184 | `TestServiceStatus.test_service_status_returns_pid` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_system.py` | 197 | `TestServiceStatus.test_service_status_requires_auth` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_system.py` | 207 | `TestGracefulShutdown.test_graceful_shutdown_returns_202` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_system.py` | 220 | `TestGracefulShutdown.test_graceful_shutdown_requires_admin` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_system.py` | 230 | `TestSystemTags.test_log_router_tag` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_system.py` | 235 | `TestSystemTags.test_guard_router_tag` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_system.py` | 240 | `TestSystemTags.test_service_router_tag` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_system.py` | 250 | `TestSystemIntegration.test_guard_and_logs_pre_unlock` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_tax.py` | 40 | `TestTaxRouterTag.test_tax_tag` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_tax.py` | 64 | `TestTaxEndpoints.test_endpoint_returns_200` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_tax.py` | 79 | `TestQuarterlyPayment.test_confirm_false_returns_400` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_tax.py` | 89 | `TestQuarterlyPayment.test_confirm_true_returns_200` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_tax.py` | 104 | `TestTaxModeGating.test_simulate_locked_403` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_tax.py` | 112 | `TestTaxModeGating.test_lots_locked_403` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_tax.py` | 121 | `TestStubShapes.test_simulate_shape` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_api_tax.py` | 131 | `TestStubShapes.test_quarterly_shape` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_api_tax.py` | 137 | `TestStubShapes.test_harvest_shape` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_api_tax.py` | 147 | `TestTaxIntegration.test_no_overrides_non_500` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_tax.py` | 155 | `TestTaxIntegration.test_ytd_summary_works` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_trades.py` | 85 | `TestCreateTrade.test_create_trade_201` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_trades.py` | 107 | `TestListTrades.test_list_trades_default` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_trades.py` | 118 | `TestListTrades.test_list_trades_with_account_filter` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_trades.py` | 130 | `TestListTrades.test_list_trades_with_sort` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_trades.py` | 140 | `TestGetTrade.test_get_trade_200` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_trades.py` | 149 | `TestGetTrade.test_get_trade_404` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_trades.py` | 159 | `TestUpdateTrade.test_update_trade_200` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_trades.py` | 169 | `TestDeleteTrade.test_delete_trade_204` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_trades.py` | 181 | `TestTradeImages.test_list_trade_images` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_trades.py` | 195 | `TestGlobalImages.test_get_image_metadata` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_trades.py` | 205 | `TestGlobalImages.test_get_thumbnail` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_api_trades.py` | 214 | `TestGlobalImages.test_get_full_image` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_trades.py` | 226 | `TestRoundTrips.test_list_round_trips` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_api_trades.py` | 237 | `TestRoundTrips.test_round_trips_accepts_canonical_filters` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_trades.py` | 256 | `TestImageUpload.test_upload_trade_image_201` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_watchlists.py` | 31 | `TestCreateWatchlist.test_create_201` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_watchlists.py` | 38 | `TestCreateWatchlist.test_create_duplicate_409` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_watchlists.py` | 48 | `TestListWatchlists.test_list_empty` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_watchlists.py` | 53 | `TestListWatchlists.test_list_returns_created` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_api_watchlists.py` | 64 | `TestGetWatchlist.test_get_existing` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_watchlists.py` | 71 | `TestGetWatchlist.test_get_nonexistent_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_watchlists.py` | 80 | `TestUpdateWatchlist.test_update_200` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_watchlists.py` | 87 | `TestUpdateWatchlist.test_update_nonexistent_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_watchlists.py` | 91 | `TestUpdateWatchlist.test_update_duplicate_name_409` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_watchlists.py` | 103 | `TestDeleteWatchlist.test_delete_204` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_api_watchlists.py` | 109 | `TestDeleteWatchlist.test_delete_nonexistent_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_api_watchlists.py` | 118 | `TestAddTicker.test_add_ticker_201` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_watchlists.py` | 125 | `TestAddTicker.test_add_duplicate_ticker_409` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_watchlists.py` | 137 | `TestRemoveTicker.test_remove_ticker_204` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_api_watchlists.py` | 159 | `TestGetWatchlistItemLoadFailure.test_get_items_failure_returns_500` | specific value or behavioral assertions |
