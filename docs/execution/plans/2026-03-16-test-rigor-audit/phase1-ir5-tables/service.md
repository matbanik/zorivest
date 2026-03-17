# Service Layer Tests

Per-test rating table for Phase 1 IR-5 audit.

Summary: 268 tests audited | 🟢 220 | 🟡 35 | 🔴 13

| Rating | File | Line | Test | Reason |
|---|---|---:|---|---|
| 🟢 | `tests/unit/test_account_review.py` | 59 | `TestAccountReviewItemDataclass.test_fields_exist` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 77 | `TestAccountReviewItemDataclass.test_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_account_review.py` | 98 | `TestAccountReviewResultDataclass.test_updated_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 109 | `TestAccountReviewResultDataclass.test_skipped_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 126 | `TestAccountReviewSummaryDataclass.test_fields_exist` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 149 | `TestPrepareReviewChecklist.test_broker_gets_api_fetch` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_account_review.py` | 159 | `TestPrepareReviewChecklist.test_bank_no_api_fetch` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 168 | `TestPrepareReviewChecklist.test_revolving_no_api_fetch` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 173 | `TestPrepareReviewChecklist.test_multiple_accounts_ordering` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_account_review.py` | 189 | `TestPrepareChecklistLatestBalance.test_latest_by_datetime` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 198 | `TestPrepareChecklistLatestBalance.test_no_snapshots_returns_none` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 212 | `TestApplyBalanceUpdate.test_creates_snapshot_and_returns_updated` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 226 | `TestApplyBalanceUpdate.test_update_from_no_snapshots` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_account_review.py` | 242 | `TestApplyBalanceUpdateDedup.test_same_balance_skips` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 253 | `TestApplyBalanceUpdateDedup.test_different_balance_updates` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 270 | `TestSkipAccount.test_skip_returns_skipped` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 284 | `TestSkipAccount.test_skip_no_snapshots` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 298 | `TestSummarizeReview.test_mixed_results` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_review.py` | 322 | `TestSummarizeReview.test_empty` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_account_review.py` | 338 | `TestModuleImports.test_no_unexpected_imports` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_account_service.py` | 29 | `TestCreateAccount.test_create_account` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_service.py` | 50 | `TestAddBalanceSnapshot.test_add_snapshot_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_account_service.py` | 72 | `TestAddBalanceSnapshot.test_add_snapshot_unknown_account` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_analytics.py` | 49 | `TestExpectancyResult.test_expectancy_result_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 63 | `TestExpectancyResult.test_expectancy_result_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_analytics.py` | 84 | `TestSQNResult.test_sqn_result_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 96 | `TestSQNResult.test_sqn_result_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_analytics.py` | 115 | `TestStrategyResult.test_strategy_result_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 126 | `TestStrategyResult.test_strategy_result_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_analytics.py` | 144 | `TestOutOfScopeResultTypes.test_drawdown_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 154 | `TestOutOfScopeResultTypes.test_excursion_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 164 | `TestOutOfScopeResultTypes.test_quality_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 173 | `TestOutOfScopeResultTypes.test_pfof_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 183 | `TestOutOfScopeResultTypes.test_cost_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 193 | `TestOutOfScopeResultTypes.test_all_out_of_scope_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_analytics.py` | 211 | `TestCalculateExpectancy.test_empty_trades_returns_zero` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 220 | `TestCalculateExpectancy.test_all_winning_trades` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 235 | `TestCalculateExpectancy.test_all_losing_trades` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 246 | `TestCalculateExpectancy.test_mixed_trades_expectancy` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 266 | `TestCalculateExpectancy.test_breakeven_trade_excluded_from_wins_and_losses` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 286 | `TestCalculateSQN.test_empty_trades_returns_zero` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 293 | `TestCalculateSQN.test_single_trade_returns_zero` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 299 | `TestCalculateSQN.test_identical_trades_zero_std` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 306 | `TestCalculateSQN.test_positive_sqn` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 320 | `TestCalculateSQN.test_sqn_grade_poor` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_analytics.py` | 333 | `TestCalculateSQN.test_sqn_grade_table` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_analytics.py` | 353 | `TestAnalyticsModuleImports.test_results_module_exports` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_analytics.py` | 364 | `TestAnalyticsModuleImports.test_results_module_no_unexpected_exports` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_analytics.py` | 376 | `TestAnalyticsModuleImports.test_expectancy_module_exports` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_analytics.py` | 382 | `TestAnalyticsModuleImports.test_sqn_module_exports` | type or presence checks only without value assertions |
| 🟡 | `tests/unit/test_image_service.py` | 28 | `TestAttachImage.test_attach_image_success` | mock call verified without argument or value checks |
| 🟢 | `tests/unit/test_image_service.py` | 53 | `TestAttachImage.test_attach_image_to_nonexistent_trade_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_image_service.py` | 74 | `TestGetTradeImages.test_get_images_for_trade` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_data_service.py` | 166 | `TestGetQuote.test_returns_quote_from_first_enabled_provider` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_data_service.py` | 181 | `TestGetQuote.test_fallback_to_next_provider_on_error` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_data_service.py` | 202 | `TestGetQuote.test_raises_market_data_error_when_all_providers_fail` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_market_data_service.py` | 216 | `TestGetQuote.test_skips_disabled_providers` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_service.py` | 231 | `TestGetQuote.test_skips_providers_without_api_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_service.py` | 253 | `TestGetNews.test_returns_news_from_enabled_provider` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_data_service.py` | 271 | `TestGetNews.test_raises_when_no_news_providers_available` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_market_data_service.py` | 285 | `TestGetSecFilings.test_raises_when_sec_not_configured` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_market_data_service.py` | 299 | `TestRateLimiting.test_rate_limiter_called_before_http_request` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 275 | `TestListProviders.test_returns_list_of_provider_status` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 285 | `TestListProviders.test_default_status_no_settings` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 296 | `TestListProviders.test_status_with_configured_provider` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 315 | `TestConfigureProvider.test_encrypts_and_stores_api_key` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 325 | `TestConfigureProvider.test_already_encrypted_key_passthrough` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 337 | `TestConfigureProvider.test_dual_key_alpaca` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 350 | `TestConfigureProvider.test_is_enabled_updates` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 365 | `TestConfigureProvider.test_patch_only_rate_limit` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_provider_connection_service.py` | 380 | `TestConfigureProvider.test_unknown_provider_raises` | swallows exceptions without exact postcondition checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 398 | `TestAlphaVantageValidation.test_global_quote_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 410 | `TestAlphaVantageValidation.test_time_series_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 427 | `TestPolygonValidation.test_results_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 438 | `TestPolygonValidation.test_status_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 453 | `TestFinnhubValidation.test_valid_response` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 464 | `TestFinnhubValidation.test_error_key_fails` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 482 | `TestFMPValidation.test_non_empty_list` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 493 | `TestFMPValidation.test_legacy_endpoint_403` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 511 | `TestEODHDValidation.test_code_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 526 | `TestNasdaqValidation.test_nested_datatable` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 543 | `TestSECValidation.test_list_with_cik` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 556 | `TestSECValidation.test_empty_list_succeeds` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 571 | `TestAPINinjasValidation.test_both_keys_present` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 588 | `TestBenzingaValidation.test_list_response` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 599 | `TestBenzingaValidation.test_dict_with_data` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 617 | `TestHTTPStatusInterpretation.test_200_unexpected_json` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 631 | `TestHTTPStatusInterpretation.test_401_invalid_api_key` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 645 | `TestHTTPStatusInterpretation.test_429_rate_limit` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 659 | `TestHTTPStatusInterpretation.test_timeout` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 673 | `TestHTTPStatusInterpretation.test_connection_error` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 694 | `TestRemoveApiKey.test_removes_and_disables` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 715 | `TestTestAllProviders.test_only_tests_providers_with_keys` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 730 | `TestTestAllProviders.test_respects_semaphore` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 753 | `TestConnectionUpdatesDB.test_updates_test_status` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 774 | `TestRateLimiterIntegration.test_rate_limiter_called` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 795 | `TestDualKeyStorage.test_stores_both_keys` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 815 | `TestGenericValidation.test_openfigi_generic` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 829 | `TestGenericValidation.test_tradier_generic` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_connection_service.py` | 843 | `TestGenericValidation.test_alpaca_generic` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_rate_limiter.py` | 22 | `TestRateLimiterAC1.test_max_per_minute_stored` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_rate_limiter.py` | 26 | `TestRateLimiterAC1.test_timestamps_deque_starts_empty` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_rate_limiter.py` | 34 | `TestRateLimiterAC2.test_wait_if_needed_is_coroutine` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_rate_limiter.py` | 38 | `TestRateLimiterAC2.test_blocks_when_full` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_rate_limiter.py` | 56 | `TestRateLimiterAC3.test_expired_timestamps_evicted` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_rate_limiter.py` | 73 | `TestRateLimiterAC4.test_burst_completes_without_blocking` | trivially weak structure (private patch or no assertions) |
| 🟡 | `tests/unit/test_rate_limiter.py` | 83 | `TestRateLimiterAC4.test_n_plus_1_blocks` | mock call verified without argument or value checks |
| 🟢 | `tests/unit/test_ref_resolver.py` | 40 | `TestRefResolver.test_resolve_simple_ref` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 49 | `TestRefResolver.test_resolve_nested_path` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 58 | `TestRefResolver.test_resolve_list_index` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 67 | `TestRefResolver.test_non_ref_dict_traversed` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 77 | `TestRefResolver.test_list_with_refs` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 84 | `TestRefResolver.test_missing_step_raises_keyerror` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_ref_resolver.py` | 91 | `TestRefResolver.test_missing_nested_key_raises_keyerror` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_ref_resolver.py` | 98 | `TestRefResolver.test_invalid_ref_no_ctx_prefix` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_ref_resolver.py` | 105 | `TestRefResolver.test_invalid_ref_only_ctx` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_ref_resolver.py` | 112 | `TestRefResolver.test_no_refs_passthrough` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 119 | `TestRefResolver.test_dict_with_ref_and_other_keys_not_a_ref` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 139 | `TestConditionEvaluator.test_eq` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 144 | `TestConditionEvaluator.test_ne` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 149 | `TestConditionEvaluator.test_gt` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 154 | `TestConditionEvaluator.test_lt` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 159 | `TestConditionEvaluator.test_ge` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 164 | `TestConditionEvaluator.test_le` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 169 | `TestConditionEvaluator.test_in` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 178 | `TestConditionEvaluator.test_not_in` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 187 | `TestConditionEvaluator.test_is_null` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ref_resolver.py` | 193 | `TestConditionEvaluator.test_is_not_null` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_ref_resolver.py` | 200 | `TestConditionEvaluator.test_returns_true_when_met` | couples to private or internal state |
| 🟡 | `tests/unit/test_ref_resolver.py` | 206 | `TestConditionEvaluator.test_missing_field_resolves_to_none` | couples to private or internal state |
| 🟡 | `tests/unit/test_ref_resolver.py` | 214 | `TestConditionEvaluator.test_missing_step_resolves_to_none` | couples to private or internal state |
| 🟡 | `tests/unit/test_ref_resolver.py` | 223 | `TestConditionEvaluator.test_unknown_operator_raises_valueerror` | couples to private or internal state |
| 🟢 | `tests/unit/test_report_service.py` | 53 | `TestReportServiceCreate.test_create_saves_report` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_report_service.py` | 78 | `TestReportServiceCreate.test_create_raises_if_trade_not_found` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_report_service.py` | 88 | `TestReportServiceCreate.test_create_raises_if_report_already_exists` | specific exception behavior asserted |
| 🟡 | `tests/unit/test_report_service.py` | 103 | `TestReportServiceGetForTrade.test_get_for_trade_returns_report` | mock call verified without argument or value checks |
| 🟢 | `tests/unit/test_report_service.py` | 120 | `TestReportServiceGetForTrade.test_get_for_trade_returns_none` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_report_service.py` | 134 | `TestReportServiceUpdate.test_update_merges_changes` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_report_service.py` | 156 | `TestReportServiceUpdate.test_update_raises_if_no_report` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_report_service.py` | 170 | `TestReportServiceDelete.test_delete_removes_report` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_report_service.py` | 189 | `TestReportServiceDelete.test_delete_raises_if_no_report` | specific exception behavior asserted |
| 🟡 | `tests/unit/test_report_service.py` | 223 | `TestPlanServiceCreate.test_create_plan_saves_and_returns` | mock call verified without argument or value checks |
| 🟡 | `tests/unit/test_report_service.py` | 250 | `TestPlanServiceGet.test_get_plan_returns_plan` | mock call verified without argument or value checks |
| 🟢 | `tests/unit/test_report_service.py` | 270 | `TestPlanServiceGet.test_get_plan_returns_none` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_report_service.py` | 284 | `TestPlanServiceList.test_list_plans_returns_list` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_report_service.py` | 300 | `TestPlanServiceUpdate.test_update_plan_merges_changes` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_report_service.py` | 323 | `TestPlanServiceUpdate.test_update_plan_raises_if_not_found` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_report_service.py` | 340 | `TestPlanServiceLink.test_link_plan_to_trade_happy_path` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_report_service.py` | 364 | `TestPlanServiceLink.test_link_plan_not_found` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_report_service.py` | 374 | `TestPlanServiceLink.test_link_trade_not_found` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_report_service.py` | 397 | `TestPlanServiceDedup.test_create_plan_duplicate_raises` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_report_service.py` | 428 | `TestPlanServiceDelete.test_delete_plan_success` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_report_service.py` | 446 | `TestPlanServiceDelete.test_delete_plan_not_found` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_service_extensions.py` | 82 | `TestListTrades.test_list_trades_default` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_service_extensions.py` | 96 | `TestListTrades.test_list_trades_with_filters` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_service_extensions.py` | 113 | `TestUpdateTrade.test_update_trade_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_service_extensions.py` | 127 | `TestUpdateTrade.test_update_trade_not_found` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_service_extensions.py` | 140 | `TestDeleteTrade.test_delete_trade_success` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_service_extensions.py` | 156 | `TestUpdateAccount.test_update_account_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_service_extensions.py` | 170 | `TestUpdateAccount.test_update_account_not_found` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_service_extensions.py` | 183 | `TestDeleteAccount.test_delete_account_success` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_service_extensions.py` | 199 | `TestGetImage.test_get_image_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_service_extensions.py` | 211 | `TestGetImage.test_get_image_not_found` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_service_extensions.py` | 224 | `TestGetFullImage.test_get_full_image_returns_bytes` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_service_extensions.py` | 239 | `TestGetImagesForOwner.test_get_images_for_owner` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_service_extensions.py` | 257 | `TestVersionModule.test_get_version_returns_semver` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_service_extensions.py` | 267 | `TestVersionModule.test_get_version_context_returns_valid_value` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_cache.py` | 18 | `TestCacheBasics.test_empty_cache_returns_none` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_cache.py` | 22 | `TestCacheBasics.test_populate_and_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_cache.py` | 29 | `TestCacheBasics.test_get_all_returns_copy` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_cache.py` | 40 | `TestCacheBasics.test_invalidate_clears_cache` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_cache.py` | 51 | `TestCacheTTL.test_stale_cache_returns_none` | couples to private or internal state |
| 🟡 | `tests/unit/test_settings_cache.py` | 58 | `TestCacheTTL.test_fresh_cache_returns_value` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_cache.py` | 67 | `TestCacheEmpty.test_get_all_empty_after_populate_empty` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_registry.py` | 43 | `TestRegistryCount.test_registry_has_24_entries` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_settings_registry.py` | 53 | `TestValueTypes.test_all_value_types_valid` | right target, but weak assertions only |
| 🔴 | `tests/unit/test_settings_registry.py` | 59 | `TestValueTypes.test_every_entry_is_setting_spec` | type or presence checks only without value assertions |
| 🟡 | `tests/unit/test_settings_registry.py` | 72 | `TestCategories.test_all_categories_valid` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_registry.py` | 78 | `TestCategories.test_all_categories_represented` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_registry.py` | 90 | `TestSeedDefaults.test_seed_populates_all_rows` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_registry.py` | 98 | `TestSeedDefaults.test_seed_values_match_registry` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_registry.py` | 113 | `TestSeedDefaults.test_seed_sets_description` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_registry.py` | 132 | `TestIdempotentSeeding.test_seed_is_idempotent` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_registry.py` | 143 | `TestIdempotentSeeding.test_seed_updates_existing_on_rerun` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_settings_registry.py` | 170 | `TestDynamicKey.test_dynamic_key_in_registry` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_registry.py` | 173 | `TestDynamicKey.test_dynamic_key_is_bool` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_registry.py` | 185 | `TestSensitivityEnum.test_three_sensitivity_levels` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_registry.py` | 188 | `TestSensitivityEnum.test_sensitivity_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_resolver.py` | 17 | `TestThreeTierResolution.test_user_value_wins` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_resolver.py` | 22 | `TestThreeTierResolution.test_default_value_when_no_user` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_resolver.py` | 27 | `TestThreeTierResolution.test_hardcoded_fallback` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_resolver.py` | 32 | `TestThreeTierResolution.test_unknown_key_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_settings_resolver.py` | 40 | `TestTypeParsing.test_parse_bool_true` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_resolver.py` | 45 | `TestTypeParsing.test_parse_bool_false` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_resolver.py` | 49 | `TestTypeParsing.test_parse_int` | couples to private or internal state |
| 🟡 | `tests/unit/test_settings_resolver.py` | 52 | `TestTypeParsing.test_parse_float` | couples to private or internal state |
| 🟡 | `tests/unit/test_settings_resolver.py` | 55 | `TestTypeParsing.test_parse_str` | couples to private or internal state |
| 🟡 | `tests/unit/test_settings_resolver.py` | 58 | `TestTypeParsing.test_parse_json` | couples to private or internal state |
| 🟡 | `tests/unit/test_settings_resolver.py` | 62 | `TestTypeParsing.test_parse_bool_invalid` | couples to private or internal state |
| 🟢 | `tests/unit/test_settings_resolver.py` | 73 | `TestExportability.test_non_sensitive_exportable` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_resolver.py` | 76 | `TestExportability.test_sensitive_not_exportable` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_resolver.py` | 79 | `TestExportability.test_unknown_key_not_exportable` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_resolver.py` | 86 | `TestResolvedSettingDataclass.test_resolved_setting_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_service.py` | 76 | `TestServiceGet.test_get_from_cache` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_service.py` | 87 | `TestServiceGet.test_get_from_db_on_cache_miss` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_service.py` | 96 | `TestServiceGet.test_get_hardcoded_fallback` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_service.py` | 108 | `TestServiceBulkUpsert.test_valid_upsert_commits` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_service.py` | 116 | `TestServiceBulkUpsert.test_invalid_upsert_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_settings_service.py` | 122 | `TestServiceBulkUpsert.test_upsert_invalidates_cache` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_service.py` | 136 | `TestServiceResetToDefault.test_reset_deletes_and_invalidates` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_service.py` | 153 | `TestServiceGetAllResolved.test_get_all_from_cache` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_service.py` | 164 | `TestServiceGetAllResolved.test_get_all_from_db_populates_cache` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_service.py` | 178 | `TestServiceGetAll.test_get_all_returns_raw_rows` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_settings_service.py` | 190 | `TestServiceGetAll.test_get_all_empty` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_settings_validator.py` | 21 | `TestTypeValidation.test_valid_bool` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_validator.py` | 25 | `TestTypeValidation.test_invalid_bool` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_validator.py` | 30 | `TestTypeValidation.test_valid_int` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_validator.py` | 34 | `TestTypeValidation.test_invalid_int` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_validator.py` | 45 | `TestFormatValidation.test_allowed_values_pass` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_validator.py` | 49 | `TestFormatValidation.test_allowed_values_reject` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_settings_validator.py` | 54 | `TestFormatValidation.test_min_value_reject` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_settings_validator.py` | 59 | `TestFormatValidation.test_max_value_reject` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_settings_validator.py` | 64 | `TestFormatValidation.test_string_length_reject` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_validator.py` | 69 | `TestFormatValidation.test_log_level_allowed` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_validator.py` | 73 | `TestFormatValidation.test_log_level_rejected` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_settings_validator.py` | 84 | `TestSecurityValidation.test_path_traversal_rejected` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_settings_validator.py` | 89 | `TestSecurityValidation.test_sql_injection_rejected` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_settings_validator.py` | 94 | `TestSecurityValidation.test_script_injection_rejected` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_validator.py` | 106 | `TestDynamicKeyResolution.test_dynamic_panel_key_resolves` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_validator.py` | 110 | `TestDynamicKeyResolution.test_unknown_key_rejected` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_validator.py` | 122 | `TestBulkValidation.test_bulk_all_valid` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_validator.py` | 126 | `TestBulkValidation.test_bulk_some_invalid` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_validator.py` | 135 | `TestValidationResult.test_valid_result` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_settings_validator.py` | 140 | `TestValidationResult.test_invalid_result` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_settings_validator.py` | 149 | `TestSettingsValidationError.test_error_attributes` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_system_service.py` | 13 | `TestSystemServiceCalculate.test_calculate_delegates` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_system_service.py` | 29 | `TestSystemServiceCalculate.test_calculate_returns_frozen_dataclass` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_trade_service.py` | 43 | `TestCreateTrade.test_create_trade_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_service.py` | 58 | `TestCreateTrade.test_create_trade_deduplicates_by_exec_id` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_trade_service.py` | 67 | `TestCreateTrade.test_create_trade_deduplicates_by_fingerprint` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_trade_service.py` | 79 | `TestGetTrade.test_get_trade_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_service.py` | 96 | `TestGetTrade.test_get_trade_not_found` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_trade_service.py` | 108 | `TestMatchRoundTrips.test_match_round_trips` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_watchlist_service.py` | 26 | `TestCreate.test_create_returns_watchlist_with_id` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_watchlist_service.py` | 32 | `TestCreate.test_create_sets_timestamps` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_watchlist_service.py` | 37 | `TestCreate.test_create_default_empty_description` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_watchlist_service.py` | 43 | `TestGet.test_get_existing` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_watchlist_service.py` | 49 | `TestGet.test_get_nonexistent_returns_none` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_watchlist_service.py` | 54 | `TestListAll.test_list_empty` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_watchlist_service.py` | 57 | `TestListAll.test_list_returns_all` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_watchlist_service.py` | 63 | `TestListAll.test_list_pagination` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_watchlist_service.py` | 71 | `TestUpdate.test_update_name` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_watchlist_service.py` | 76 | `TestUpdate.test_update_nonexistent_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 82 | `TestDelete.test_delete_existing` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_watchlist_service.py` | 87 | `TestDelete.test_delete_nonexistent_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 96 | `TestDuplicateName.test_create_duplicate_name_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 101 | `TestDuplicateName.test_update_to_duplicate_name_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 107 | `TestDuplicateName.test_update_same_name_ok` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_watchlist_service.py` | 118 | `TestAddTicker.test_add_ticker` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_watchlist_service.py` | 126 | `TestAddTicker.test_add_ticker_normalizes_case` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_watchlist_service.py` | 131 | `TestAddTicker.test_add_to_nonexistent_watchlist_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 137 | `TestRemoveTicker.test_remove_ticker` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_watchlist_service.py` | 144 | `TestRemoveTicker.test_remove_from_nonexistent_watchlist_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 150 | `TestGetItems.test_get_items_returns_all` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_watchlist_service.py` | 159 | `TestGetItems.test_get_items_nonexistent_watchlist_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 168 | `TestDuplicateTicker.test_add_duplicate_ticker_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 174 | `TestDuplicateTicker.test_case_insensitive_duplicate_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_watchlist_service.py` | 187 | `TestCascadeDelete.test_delete_watchlist_cascades_items` | exact behavior asserted despite weaker auxiliary checks |
