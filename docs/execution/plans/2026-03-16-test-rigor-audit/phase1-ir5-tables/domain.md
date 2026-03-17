# Domain Model Tests

Per-test rating table for Phase 1 IR-5 audit.

Summary: 349 tests audited | 🟢 296 | 🟡 12 | 🔴 41

| Rating | File | Line | Test | Reason |
|---|---|---:|---|---|
| 🟢 | `tests/unit/test_calculator.py` | 19 | `TestPositionSizeCalculator.test_basic_calculation` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_calculator.py` | 39 | `TestPositionSizeCalculator.test_zero_entry_returns_zero_shares` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_calculator.py` | 54 | `TestPositionSizeCalculator.test_risk_out_of_range_defaults_to_one_percent` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_calculator.py` | 67 | `TestPositionSizeCalculator.test_risk_zero_defaults_to_one_percent` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_calculator.py` | 79 | `TestPositionSizeCalculator.test_risk_negative_defaults_to_one_percent` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_calculator.py` | 93 | `TestPositionSizeCalculator.test_entry_equals_stop` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_calculator.py` | 108 | `TestPositionSizeCalculator.test_zero_balance` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_calculator.py` | 122 | `TestPositionSizeCalculator.test_frozen_dataclass` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_calculator.py` | 137 | `TestPositionSizeCalculator.test_import_surface` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 50 | `TestCreateTrade.test_create_trade_valid` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 70 | `TestCreateTrade.test_create_trade_with_optional_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 86 | `TestCreateTrade.test_create_trade_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 100 | `TestCreateTrade.test_create_trade_rejects_empty_exec_id` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 113 | `TestCreateTrade.test_create_trade_rejects_whitespace_exec_id` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 126 | `TestCreateTrade.test_create_trade_rejects_zero_quantity` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 139 | `TestCreateTrade.test_create_trade_rejects_negative_quantity` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 159 | `TestAttachImage.test_attach_image_valid` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 178 | `TestAttachImage.test_attach_image_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 192 | `TestAttachImage.test_attach_image_rejects_non_webp` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 205 | `TestAttachImage.test_attach_image_caption_defaults_to_empty` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 224 | `TestCreateAccount.test_create_account_valid` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 240 | `TestCreateAccount.test_create_account_with_all_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 257 | `TestCreateAccount.test_create_account_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 267 | `TestCreateAccount.test_create_account_rejects_empty_account_id` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 276 | `TestCreateAccount.test_create_account_rejects_empty_name` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 285 | `TestCreateAccount.test_create_account_rejects_whitespace_name` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 301 | `TestUpdateBalance.test_update_balance_valid` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 313 | `TestUpdateBalance.test_update_balance_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 323 | `TestUpdateBalance.test_update_balance_snapshot_datetime_defaults_to_now` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 340 | `TestQueries.test_get_trade` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 345 | `TestQueries.test_get_trade_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 351 | `TestQueries.test_list_trades_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 358 | `TestQueries.test_list_trades_with_filter` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 365 | `TestQueries.test_get_account` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_commands_dtos.py` | 370 | `TestQueries.test_list_accounts` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 375 | `TestQueries.test_get_image` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 380 | `TestQueries.test_list_images` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 393 | `TestTradeDTO.test_trade_dto_valid` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 410 | `TestTradeDTO.test_trade_dto_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 431 | `TestAccountDTO.test_account_dto_valid` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 447 | `TestAccountDTO.test_account_dto_null_balance` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 462 | `TestAccountDTO.test_account_dto_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 482 | `TestBalanceSnapshotDTO.test_balance_snapshot_dto_valid` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 494 | `TestBalanceSnapshotDTO.test_balance_snapshot_dto_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_commands_dtos.py` | 509 | `TestImageAttachmentDTO.test_image_attachment_dto_valid` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_commands_dtos.py` | 529 | `TestImageAttachmentDTO.test_image_attachment_dto_is_frozen` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_commands_dtos.py` | 552 | `TestModuleImports.test_commands_module_exists` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 561 | `TestModuleImports.test_commands_module_no_unexpected_exports` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_commands_dtos.py` | 573 | `TestModuleImports.test_queries_module_exists` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 584 | `TestModuleImports.test_queries_module_no_unexpected_exports` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_commands_dtos.py` | 595 | `TestModuleImports.test_dtos_module_exists` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_commands_dtos.py` | 604 | `TestModuleImports.test_dtos_module_no_unexpected_exports` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_display_mode.py` | 27 | `TestDisplayModeDataclass.test_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 33 | `TestDisplayModeDataclass.test_custom_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 43 | `TestDisplayModeDataclass.test_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_display_mode.py` | 56 | `TestFormatDollarNormal.test_basic_formatting` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 61 | `TestFormatDollarNormal.test_zero` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 66 | `TestFormatDollarNormal.test_cents` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 79 | `TestFormatDollarMasked.test_hides_dollars` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 84 | `TestFormatDollarMasked.test_hides_zero` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 97 | `TestFormatDollarPercentMode.test_percent_appended` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 106 | `TestFormatDollarPercentMode.test_percent_mode_without_total` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 120 | `TestFormatDollarHiddenWithPercent.test_hidden_dollars_with_percent` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 137 | `TestFormatDollarPercentHidden.test_percent_hidden` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 146 | `TestFormatDollarPercentHidden.test_all_hidden` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 168 | `TestFormatPercentage.test_visible_percentage` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 173 | `TestFormatPercentage.test_hidden_percentage` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 178 | `TestFormatPercentage.test_zero_percentage` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 191 | `TestTruthTable.test_row1_all_visible_no_percent` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 197 | `TestTruthTable.test_row2_all_visible_percent_on` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 205 | `TestTruthTable.test_row3_dollar_hidden_percent_on` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 213 | `TestTruthTable.test_row4_all_hidden_percent_on` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 223 | `TestTruthTable.test_row5_dollar_hidden_percent_off` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 229 | `TestTruthTable.test_row6_dollar_visible_percent_hidden_on` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_display_mode.py` | 245 | `TestDivisionByZero.test_zero_total_portfolio` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_display_mode.py` | 260 | `TestModuleImports.test_no_unexpected_imports` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_entities.py` | 94 | `TestTrade.test_trade_construction_with_required_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 106 | `TestTrade.test_trade_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 113 | `TestTrade.test_trade_with_explicit_optional_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 128 | `TestTradeAttachImage.test_attach_image_appends` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 135 | `TestTradeAttachImage.test_attach_multiple_images` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 150 | `TestAccount.test_account_construction_with_required_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 158 | `TestAccount.test_account_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 170 | `TestAccount.test_account_with_explicit_optional_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 194 | `TestBalanceSnapshot.test_balance_snapshot_construction` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 201 | `TestBalanceSnapshot.test_balance_snapshot_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_entities.py` | 213 | `TestImageAttachment.test_image_attachment_construction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 229 | `TestImageAttachment.test_image_attachment_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_entities.py` | 234 | `TestImageAttachment.test_image_attachment_custom_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 249 | `TestMimeTypeEnforcement.test_default_mime_type_is_webp` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 253 | `TestMimeTypeEnforcement.test_non_webp_mime_type_raises` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_entities.py` | 265 | `TestImportSurface.test_import_surface_entities` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_entities.py` | 303 | `TestModuleIntegrity.test_module_has_expected_classes` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 346 | `TestTradeReport.test_trade_report_construction_with_required_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 365 | `TestTradeReport.test_trade_report_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 371 | `TestTradeReport.test_trade_report_with_all_fields` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_entities.py` | 383 | `TestTradeReportType.test_trade_report_field_accepts_trade_report` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_entities.py` | 390 | `TestTradeReportType.test_trade_report_field_defaults_to_none` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 401 | `TestQualityGrade.test_quality_grade_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 411 | `TestQualityGrade.test_quality_int_map` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 416 | `TestQualityGrade.test_quality_grade_map` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 421 | `TestQualityGrade.test_roundtrip_conversion` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 431 | `TestEmotionalState.test_emotional_state_members` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 441 | `TestEmotionalState.test_emotional_state_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 446 | `TestEmotionalState.test_emotional_state_default_is_neutral` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 487 | `TestTradePlan.test_trade_plan_construction_with_all_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 512 | `TestTradePlan.test_trade_plan_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 518 | `TestTradePlan.test_trade_plan_with_images` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 527 | `TestTradePlanRiskReward.test_compute_risk_reward_bullish` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 536 | `TestTradePlanRiskReward.test_compute_risk_reward_bearish` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 545 | `TestTradePlanRiskReward.test_compute_risk_reward_zero_risk_returns_zero` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 557 | `TestConvictionLevel.test_conviction_level_members` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 564 | `TestConvictionLevel.test_conviction_level_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 573 | `TestPlanStatus.test_plan_status_members` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 580 | `TestPlanStatus.test_plan_status_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 621 | `TestWatchlist.test_watchlist_construction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 629 | `TestWatchlist.test_watchlist_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_entities.py` | 633 | `TestWatchlist.test_watchlist_with_tickers` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 642 | `TestWatchlistItem.test_watchlist_item_construction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_entities.py` | 650 | `TestWatchlistItem.test_watchlist_item_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_enums.py` | 27 | `TestModuleIntegrity.test_module_contains_expected_enum_classes` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_enums.py` | 68 | `TestStrEnumSubclass.test_all_enums_subclass_strenum` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_enums.py` | 84 | `TestCoreEnums.test_account_type_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 95 | `TestCoreEnums.test_trade_action_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 102 | `TestCoreEnums.test_conviction_level_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 111 | `TestCoreEnums.test_plan_status_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 121 | `TestCoreEnums.test_image_owner_type_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 129 | `TestCoreEnums.test_display_mode_flag_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 144 | `TestExpansionEnums.test_round_trip_status_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 152 | `TestExpansionEnums.test_identifier_type_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 161 | `TestExpansionEnums.test_fee_type_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 173 | `TestExpansionEnums.test_strategy_type_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 185 | `TestExpansionEnums.test_mistake_category_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 200 | `TestExpansionEnums.test_routing_type_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 208 | `TestExpansionEnums.test_transaction_category_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_enums.py` | 229 | `TestExpansionEnums.test_balance_source_members` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_enums.py` | 247 | `TestImportSurface.test_import_surface_only_enum` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_events.py` | 33 | `TestDomainEvent.test_domain_event_has_defaults` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_events.py` | 40 | `TestDomainEvent.test_domain_event_unique_ids` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_events.py` | 46 | `TestDomainEvent.test_domain_event_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_events.py` | 59 | `TestTradeCreated.test_trade_created_fields` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_events.py` | 76 | `TestTradeCreated.test_trade_created_inherits_base` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_events.py` | 83 | `TestTradeCreated.test_trade_created_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_events.py` | 96 | `TestBalanceUpdated.test_balance_updated_fields` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_events.py` | 107 | `TestBalanceUpdated.test_balance_updated_inherits_base` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_events.py` | 112 | `TestBalanceUpdated.test_balance_updated_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_events.py` | 125 | `TestImageAttached.test_image_attached_fields` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_events.py` | 136 | `TestImageAttached.test_image_attached_inherits_base` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_events.py` | 141 | `TestImageAttached.test_image_attached_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_events.py` | 154 | `TestPlanCreated.test_plan_created_fields` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_events.py` | 167 | `TestPlanCreated.test_plan_created_inherits_base` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_events.py` | 172 | `TestPlanCreated.test_plan_created_is_frozen` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_events.py` | 185 | `TestEventsModuleImports.test_events_module_exports` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_events.py` | 195 | `TestEventsModuleImports.test_events_module_no_unexpected_exports` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_exceptions.py` | 21 | `TestExceptionHierarchy.test_zorivest_error_is_exception` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_exceptions.py` | 24 | `TestExceptionHierarchy.test_validation_error_inherits_zorivest_error` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_exceptions.py` | 27 | `TestExceptionHierarchy.test_not_found_error_inherits_zorivest_error` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_exceptions.py` | 30 | `TestExceptionHierarchy.test_business_rule_error_inherits_zorivest_error` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_exceptions.py` | 33 | `TestExceptionHierarchy.test_budget_exceeded_error_inherits_zorivest_error` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_exceptions.py` | 36 | `TestExceptionHierarchy.test_import_error_inherits_zorivest_error` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_exceptions.py` | 39 | `TestExceptionHierarchy.test_hierarchy_has_exactly_six_classes` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_exceptions.py` | 51 | `TestExceptionHierarchy.test_all_exceptions_are_catchable_as_zorivest_error` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_exceptions.py` | 62 | `TestExceptionHierarchy.test_exception_message_preserved` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_exceptions.py` | 67 | `TestExceptionHierarchy.test_import_error_does_not_shadow_builtin` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_market_data_entities.py` | 25 | `TestAuthMethodEnum.test_auth_method_is_strenum` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 30 | `TestAuthMethodEnum.test_auth_method_has_exactly_4_members` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_data_entities.py` | 35 | `TestAuthMethodEnum.test_auth_method_query_param` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 40 | `TestAuthMethodEnum.test_auth_method_bearer_header` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 45 | `TestAuthMethodEnum.test_auth_method_custom_header` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 50 | `TestAuthMethodEnum.test_auth_method_raw_header` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 62 | `TestProviderConfig.test_provider_config_creation_all_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 82 | `TestProviderConfig.test_provider_config_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_market_data_entities.py` | 99 | `TestProviderConfig.test_provider_config_headers_template_dict` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_data_entities.py` | 116 | `TestProviderConfig.test_provider_config_default_timeout` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 132 | `TestProviderConfig.test_provider_config_signup_url_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 148 | `TestProviderConfig.test_provider_config_response_validator_key_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 164 | `TestProviderConfig.test_provider_config_missing_required_field_raises` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_market_data_entities.py` | 178 | `TestMarketDataPort.test_market_data_port_is_protocol` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_market_data_entities.py` | 183 | `TestMarketDataPort.test_market_data_port_has_get_quote` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_market_data_entities.py` | 191 | `TestMarketDataPort.test_market_data_port_has_get_news` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_market_data_entities.py` | 200 | `TestMarketDataPort.test_market_data_port_has_search_ticker` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_market_data_entities.py` | 208 | `TestMarketDataPort.test_market_data_port_has_get_sec_filings` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 216 | `TestMarketDataPort.test_market_data_port_methods_are_async` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_entities.py` | 226 | `TestMarketDataPort.test_market_data_port_return_annotations` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_dtos.py` | 22 | `TestMarketQuote.test_market_quote_required_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 30 | `TestMarketQuote.test_market_quote_optional_fields_default_none` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 43 | `TestMarketQuote.test_market_quote_all_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 64 | `TestMarketQuote.test_market_quote_json_round_trip` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 74 | `TestMarketQuote.test_market_quote_invalid_type_rejected` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_market_dtos.py` | 88 | `TestMarketNewsItem.test_market_news_item_required_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 95 | `TestMarketNewsItem.test_market_news_item_tickers_default_empty_list` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_dtos.py` | 103 | `TestMarketNewsItem.test_market_news_item_optional_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 111 | `TestMarketNewsItem.test_market_news_item_json_round_trip` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 127 | `TestTickerSearchResult.test_ticker_search_result_required_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 134 | `TestTickerSearchResult.test_ticker_search_result_optional_exchange_currency` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 141 | `TestTickerSearchResult.test_ticker_search_result_json_round_trip` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 157 | `TestSecFiling.test_sec_filing_required_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 165 | `TestSecFiling.test_sec_filing_provider_defaults_to_sec_api` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 172 | `TestSecFiling.test_sec_filing_optional_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_dtos.py` | 179 | `TestSecFiling.test_sec_filing_json_round_trip` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_models.py` | 66 | `TestSchemaCreation.test_create_all_tables` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_models.py` | 72 | `TestSchemaCreation.test_exactly_30_tables` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_models.py` | 81 | `TestColumnTypes.test_trade_commission_is_numeric` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_models.py` | 87 | `TestColumnTypes.test_trade_price_is_float` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_models.py` | 93 | `TestColumnTypes.test_balance_snapshot_balance_is_numeric` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_models.py` | 103 | `TestModelInsert.test_insert_account_and_trade` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_models.py` | 131 | `TestModelInsert.test_insert_image` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_models.py` | 152 | `TestRelationships.test_account_trades_relationship` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_models.py` | 178 | `TestRelationships.test_watchlist_items_cascade` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_models.py` | 203 | `TestMarketProviderSettingModel.test_market_provider_has_encrypted_api_secret_column` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_models.py` | 212 | `TestMarketProviderSettingModel.test_market_provider_insert_with_api_secret` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_pipeline_enums.py` | 23 | `TestPipelineStatus.test_is_str_enum` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 26 | `TestPipelineStatus.test_member_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 40 | `TestPipelineStatus.test_member_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 43 | `TestPipelineStatus.test_string_conversion` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 48 | `TestPipelineStatus.test_membership_lookup` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_pipeline_enums.py` | 60 | `TestStepErrorMode.test_is_str_enum` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 63 | `TestStepErrorMode.test_member_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 74 | `TestStepErrorMode.test_member_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 77 | `TestStepErrorMode.test_string_conversion` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 80 | `TestStepErrorMode.test_membership_lookup` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_pipeline_enums.py` | 92 | `TestDataType.test_is_str_enum` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 95 | `TestDataType.test_member_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 107 | `TestDataType.test_member_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 110 | `TestDataType.test_string_conversion` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 113 | `TestDataType.test_membership_lookup` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 127 | `TestSnakeCaseValues.test_values_are_lowercase` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_enums.py` | 134 | `TestSnakeCaseValues.test_values_are_snake_case` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 58 | `TestRefValue.test_valid_ref` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 62 | `TestRefValue.test_simple_ref` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 66 | `TestRefValue.test_invalid_ref_no_ctx` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 70 | `TestRefValue.test_invalid_ref_empty` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 74 | `TestRefValue.test_invalid_ref_spaces` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 85 | `TestRetryConfig.test_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 91 | `TestRetryConfig.test_max_attempts_range` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 95 | `TestRetryConfig.test_max_attempts_too_low` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 99 | `TestRetryConfig.test_max_attempts_too_high` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 103 | `TestRetryConfig.test_backoff_range` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 107 | `TestRetryConfig.test_backoff_too_low` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 118 | `TestSkipConditionOperator.test_member_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_models.py` | 136 | `TestSkipConditionOperator.test_member_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 146 | `TestPolicyStep.test_valid_step` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 151 | `TestPolicyStep.test_id_pattern_lowercase` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 155 | `TestPolicyStep.test_id_rejects_uppercase` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 159 | `TestPolicyStep.test_id_rejects_leading_number` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 163 | `TestPolicyStep.test_id_rejects_too_long` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 167 | `TestPolicyStep.test_id_accepts_max_length` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_models.py` | 172 | `TestPolicyStep.test_timeout_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 176 | `TestPolicyStep.test_timeout_range` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 180 | `TestPolicyStep.test_timeout_too_low` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 184 | `TestPolicyStep.test_timeout_too_high` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 188 | `TestPolicyStep.test_on_error_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 192 | `TestPolicyStep.test_skip_if_none_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 196 | `TestPolicyStep.test_required_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 207 | `TestTriggerConfig.test_minimal` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 213 | `TestTriggerConfig.test_misfire_grace_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 217 | `TestTriggerConfig.test_misfire_grace_range` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 221 | `TestTriggerConfig.test_misfire_grace_too_low` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 225 | `TestTriggerConfig.test_misfire_grace_too_high` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 229 | `TestTriggerConfig.test_coalesce_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 233 | `TestTriggerConfig.test_max_instances_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 237 | `TestTriggerConfig.test_max_instances_range` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 240 | `TestTriggerConfig.test_max_instances_too_high` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 251 | `TestPolicyDocument.test_minimal` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_models.py` | 256 | `TestPolicyDocument.test_schema_version_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 260 | `TestPolicyDocument.test_steps_min_length` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 264 | `TestPolicyDocument.test_steps_max_length` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_models.py` | 269 | `TestPolicyDocument.test_steps_too_many` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 274 | `TestPolicyDocument.test_name_constraints` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 282 | `TestPolicyDocument.test_unique_step_ids_pass` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_models.py` | 287 | `TestPolicyDocument.test_unique_step_ids_reject_duplicates` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 292 | `TestPolicyDocument.test_metadata_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 304 | `TestStepContext.test_get_output_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 309 | `TestStepContext.test_get_output_missing` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_models.py` | 314 | `TestStepContext.test_dry_run_default_false` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 318 | `TestStepContext.test_outputs_default_empty` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_pipeline_models.py` | 323 | `TestStepContext.test_logger_is_structlog` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 338 | `TestStepResult.test_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_models.py` | 346 | `TestStepResult.test_with_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 58 | `TestTotalPortfolioBalanceDataclass.test_fields_exist` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 68 | `TestTotalPortfolioBalanceDataclass.test_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 85 | `TestCalculateBasic.test_single_account_single_snapshot` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 91 | `TestCalculateBasic.test_multiple_accounts` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 109 | `TestEmptySnapshots.test_account_with_no_snapshots` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 115 | `TestEmptySnapshots.test_mixed_with_and_without_snapshots` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 131 | `TestNegativeBalances.test_negative_balance_reduces_total` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 146 | `TestNegativeBalances.test_all_negative` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 163 | `TestLatestByDatetime.test_uses_max_datetime_not_last_position` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_portfolio_balance.py` | 181 | `TestEmptyAccountsList.test_empty_list` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_portfolio_balance.py` | 194 | `TestModuleImports.test_no_unexpected_imports` | right target, but weak assertions only |
| 🔴 | `tests/unit/test_ports.py` | 25 | `TestTradeRepository.test_trade_repository_is_protocol` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_ports.py` | 30 | `TestTradeRepository.test_trade_repository_methods` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_ports.py` | 49 | `TestImageRepository.test_image_repository_is_protocol` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_ports.py` | 54 | `TestImageRepository.test_image_repository_methods` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_ports.py` | 73 | `TestUnitOfWork.test_unit_of_work_is_protocol` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_ports.py` | 78 | `TestUnitOfWork.test_unit_of_work_methods` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_ports.py` | 93 | `TestUnitOfWork.test_unit_of_work_has_context_manager` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_ports.py` | 105 | `TestUnitOfWork.test_unit_of_work_has_repository_attributes` | right target, but weak assertions only |
| 🔴 | `tests/unit/test_ports.py` | 121 | `TestBrokerPort.test_broker_port_is_protocol` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_ports.py` | 126 | `TestBrokerPort.test_broker_port_methods` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_ports.py` | 151 | `TestBankImportPort.test_bank_import_port_is_protocol` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_ports.py` | 156 | `TestBankImportPort.test_bank_import_port_methods` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_ports.py` | 175 | `TestIdentifierResolverPort.test_identifier_resolver_port_is_protocol` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_ports.py` | 180 | `TestIdentifierResolverPort.test_identifier_resolver_port_methods` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_ports.py` | 202 | `TestProtocolConvention.test_all_ports_are_protocols` | type or presence checks only without value assertions |
| 🟡 | `tests/unit/test_ports.py` | 213 | `TestProtocolConvention.test_none_are_runtime_checkable` | right target, but weak assertions only |
| 🔴 | `tests/unit/test_ports.py` | 232 | `TestImportSurface.test_import_surface_ports` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_ports.py` | 268 | `TestModuleIntegrity.test_module_has_exactly_18_protocol_classes` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_scheduling_models.py` | 82 | `TestTableCreation.test_all_scheduling_tables_exist` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_scheduling_models.py` | 88 | `TestTableCreation.test_models_inherit_from_base` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_scheduling_models.py` | 109 | `TestPolicyModel.test_policy_crud` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_scheduling_models.py` | 135 | `TestPolicyModel.test_policy_name_unique` | specific exception behavior asserted |
| 🟡 | `tests/unit/test_scheduling_models.py` | 169 | `TestRelationships.test_run_policy_relationship` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_scheduling_models.py` | 181 | `TestRelationships.test_step_run_relationship` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_scheduling_models.py` | 200 | `TestRelationships.test_run_fk_constraint` | specific exception behavior asserted |
| 🟡 | `tests/unit/test_scheduling_models.py` | 227 | `TestPipelineStateModel.test_unique_constraint` | couples to private or internal state |
| 🔴 | `tests/unit/test_scheduling_models.py` | 242 | `TestPipelineStateModel.test_different_keys_allowed` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_scheduling_models.py` | 263 | `TestFetchCacheModel.test_unique_constraint` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_scheduling_models.py` | 284 | `TestAuditLogModel.test_autoincrement_pk` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_scheduling_models.py` | 314 | `TestReportModels.test_report_version_relationship` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_scheduling_models.py` | 325 | `TestReportModels.test_report_delivery_relationship` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_scheduling_models.py` | 336 | `TestReportModels.test_dedup_key_unique` | couples to private or internal state |
| 🟢 | `tests/unit/test_scheduling_models.py` | 353 | `TestReportModels.test_cascade_delete` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_scheduling_models.py` | 381 | `TestReportVersioningTrigger.test_report_versioning_trigger` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_scheduling_models.py` | 422 | `TestAuditAppendOnlyTriggers.test_audit_no_update_trigger` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_scheduling_models.py` | 436 | `TestAuditAppendOnlyTriggers.test_audit_no_delete_trigger` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 27 | `TestMoney.test_money_construction` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 34 | `TestMoney.test_money_default_currency_is_usd` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 40 | `TestMoney.test_money_zero_amount_allowed` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 46 | `TestMoney.test_money_rejects_negative_amount` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 53 | `TestMoney.test_money_rejects_empty_currency` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 67 | `TestPositionSize.test_position_size_construction` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 79 | `TestPositionSize.test_position_size_rejects_negative_share_size` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 97 | `TestTicker.test_ticker_normalizes_to_uppercase` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 104 | `TestTicker.test_ticker_already_uppercase_unchanged` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 110 | `TestTicker.test_ticker_rejects_empty_symbol` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 117 | `TestTicker.test_ticker_rejects_whitespace_only_symbol` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 131 | `TestConviction.test_conviction_construction` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 145 | `TestImageData.test_image_data_construction` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 159 | `TestImageData.test_image_data_rejects_non_positive_width` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 166 | `TestImageData.test_image_data_rejects_non_positive_height` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 173 | `TestImageData.test_image_data_rejects_empty_data` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 187 | `TestFrozenEnforcement.test_money_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 194 | `TestFrozenEnforcement.test_position_size_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 205 | `TestFrozenEnforcement.test_ticker_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 212 | `TestFrozenEnforcement.test_conviction_is_frozen` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_value_objects.py` | 220 | `TestFrozenEnforcement.test_image_data_is_frozen` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_value_objects.py` | 234 | `TestImportSurface.test_import_surface_value_objects` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_value_objects.py` | 270 | `TestModuleIntegrity.test_module_has_expected_classes` | specific value or behavioral assertions |
