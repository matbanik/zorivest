# Infra and Pipeline Tests

Per-test rating table for Phase 1 IR-5 audit.

Summary: 425 tests audited | 🟢 340 | 🟡 73 | 🔴 12

| Rating | File | Line | Test | Reason |
|---|---|---:|---|---|
| 🟢 | `tests/unit/test_backup_manager.py` | 64 | `TestBackupManifest.test_manifest_to_dict` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_manager.py` | 78 | `TestBackupManifest.test_manifest_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_manager.py` | 88 | `TestBackupResult.test_success_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_manager.py` | 94 | `TestBackupResult.test_failed_result` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_manager.py` | 103 | `TestKDFParams.test_kdf_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_manager.py` | 108 | `TestKDFParams.test_kdf_to_dict` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_manager.py` | 118 | `TestSQLCipherMeta.test_sqlcipher_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_manager.py` | 123 | `TestSQLCipherMeta.test_sqlcipher_to_dict` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_manager.py` | 132 | `TestGFSConstants.test_gfs_values` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_manager.py` | 144 | `TestSnapshot.test_create_snapshot` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_manager.py` | 161 | `TestCreateBackup.test_create_backup_success` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_manager.py` | 170 | `TestCreateBackup.test_backup_contains_manifest` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_backup_manager.py` | 176 | `TestCreateBackup.test_backup_is_encrypted_zip` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_backup_manager.py` | 183 | `TestCreateBackup.test_no_databases_returns_failure` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_manager.py` | 193 | `TestCreateBackup.test_snapshot_files_cleaned_up` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_manager.py` | 205 | `TestListBackups.test_list_backups` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_backup_manager.py` | 218 | `TestGFSRotation.test_no_rotation_when_under_limit` | couples to private or internal state |
| 🟢 | `tests/unit/test_backup_manager.py` | 223 | `TestGFSRotation.test_gfs_rotation_removes_excess` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_manager.py` | 249 | `TestGFSRotation.test_gfs_rotation_proves_5_4_3_tiering` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_backup_manager.py` | 357 | `TestBackupSecurity.test_wrong_password_fails_verification` | couples to private or internal state |
| 🟡 | `tests/unit/test_backup_manager.py` | 383 | `TestBackupSecurity.test_manifest_hash_integrity` | couples to private or internal state |
| 🟢 | `tests/unit/test_backup_manager.py` | 402 | `TestBackupSecurity.test_kdf_domain_separation` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_manager.py` | 413 | `TestBackupSecurity.test_kdf_uses_argon2id` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_backup_manager.py` | 422 | `TestBackupSecurity.test_verify_backup_checks_file_presence` | couples to private or internal state |
| 🟢 | `tests/unit/test_backup_recovery.py` | 170 | `TestRestore.test_restore_zvbak_success` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_recovery.py` | 190 | `TestRestore.test_restore_wrong_passphrase` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_backup_recovery.py` | 205 | `TestRestore.test_restore_tampered_backup` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_backup_recovery.py` | 220 | `TestRestore.test_maintenance_hooks_called` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_backup_recovery.py` | 246 | `TestVerify.test_verify_valid_backup` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_backup_recovery.py` | 260 | `TestVerify.test_verify_corrupted_backup` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_backup_recovery.py` | 275 | `TestVerify.test_verify_nonexistent_file` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_recovery.py` | 295 | `TestRepair.test_repair_healthy_database` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_recovery.py` | 306 | `TestRepair.test_repair_corrupted_database` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_backup_recovery.py` | 341 | `TestRepair.test_repair_nonexistent_database` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_backup_recovery.py` | 361 | `TestLegacy.test_legacy_zip_format` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_backup_recovery.py` | 381 | `TestLegacy.test_legacy_db_format` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_backup_recovery.py` | 396 | `TestLegacy.test_legacy_db_gz_format` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_config_export.py` | 82 | `TestBuildExport.test_export_has_required_keys` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_config_export.py` | 97 | `TestBuildExport.test_export_includes_only_portable_keys` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_config_export.py` | 115 | `TestBuildExport.test_export_excludes_secret_sensitivity` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_config_export.py` | 124 | `TestBuildExport.test_export_excludes_sensitive` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_config_export.py` | 133 | `TestBuildExport.test_export_excludes_non_exportable` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_config_export.py` | 152 | `TestBuildExport.test_export_with_real_registry` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_config_export.py` | 171 | `TestValidateImport.test_accepted_keys` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_config_export.py` | 181 | `TestValidateImport.test_rejected_keys` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_config_export.py` | 192 | `TestValidateImport.test_unknown_keys` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_config_export.py` | 203 | `TestValidateImport.test_mixed_categories` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_config_export.py` | 218 | `TestValidateImport.test_round_trip` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_config_export.py` | 240 | `TestPortableSymmetry.test_is_portable_true_for_exportable_nonsensitive` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_config_export.py` | 247 | `TestPortableSymmetry.test_is_portable_false_for_sensitive` | couples to private or internal state |
| 🟡 | `tests/unit/test_config_export.py` | 253 | `TestPortableSymmetry.test_is_portable_false_for_secret` | couples to private or internal state |
| 🟡 | `tests/unit/test_config_export.py` | 259 | `TestPortableSymmetry.test_is_portable_false_for_unknown` | couples to private or internal state |
| 🟢 | `tests/unit/test_config_export.py` | 272 | `TestImportValidation.test_importvalidation_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_config_export.py` | 283 | `TestImportValidation.test_importvalidation_frozen` | specific exception behavior asserted |
| 🟡 | `tests/unit/test_csv_import.py` | 24 | `TestCSVParserBaseEncoding.test_detect_utf8_encoding` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_csv_import.py` | 31 | `TestCSVParserBaseEncoding.test_detect_latin1_encoding` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_csv_import.py` | 39 | `TestCSVParserBaseEncoding.test_strip_bom` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_csv_import.py` | 53 | `TestThinkorSwimParser.test_detect_tos_headers` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 59 | `TestThinkorSwimParser.test_reject_non_tos_headers` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 64 | `TestThinkorSwimParser.test_broker_type` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_csv_import.py` | 68 | `TestThinkorSwimParser.test_parse_file_returns_import_result` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 73 | `TestThinkorSwimParser.test_parse_file_extracts_trades` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_csv_import.py` | 79 | `TestThinkorSwimParser.test_stock_trade_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_csv_import.py` | 89 | `TestThinkorSwimParser.test_option_trade_symbol_normalized` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_csv_import.py` | 96 | `TestThinkorSwimParser.test_sell_side_detected` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_csv_import.py` | 102 | `TestThinkorSwimParser.test_empty_csv_handling` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_csv_import.py` | 110 | `TestThinkorSwimParser.test_headers_only_csv` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_csv_import.py` | 124 | `TestNinjaTraderParser.test_detect_ninjatrader_headers` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 130 | `TestNinjaTraderParser.test_reject_non_ninjatrader_headers` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 135 | `TestNinjaTraderParser.test_broker_type` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_csv_import.py` | 139 | `TestNinjaTraderParser.test_parse_file_returns_import_result` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 144 | `TestNinjaTraderParser.test_parse_file_extracts_trades` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_csv_import.py` | 150 | `TestNinjaTraderParser.test_strategy_tag_in_raw_data` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_csv_import.py` | 156 | `TestNinjaTraderParser.test_mfe_mae_in_raw_data` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_csv_import.py` | 163 | `TestNinjaTraderParser.test_long_trade_side` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_csv_import.py` | 169 | `TestNinjaTraderParser.test_short_trade_side` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_csv_import.py` | 182 | `TestImportServiceRouting.test_import_xml_routes_to_ibkr` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 189 | `TestImportServiceRouting.test_import_csv_auto_detects_tos` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 197 | `TestImportServiceRouting.test_import_csv_auto_detects_ninjatrader` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 205 | `TestImportServiceRouting.test_broker_hint_overrides_detection` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 211 | `TestImportServiceRouting.test_unknown_csv_raises_error` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_csv_import.py` | 221 | `TestImportServiceRouting.test_auto_detect_csv_broker` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 229 | `TestImportServiceRouting.test_unknown_format_auto_detect` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_csv_import.py` | 246 | `TestEdgeCases.test_empty_file` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_csv_import.py` | 253 | `TestEdgeCases.test_csv_with_bom` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_csv_import.py` | 267 | `TestEdgeCases.test_bom_csv_through_import_service` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_fetch_step.py` | 22 | `test_AC_F1_fetch_step_auto_registers` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_fetch_step.py` | 40 | `test_AC_F2_params_validates_required_fields` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_fetch_step.py` | 63 | `test_AC_F3_fetch_result_content_hash` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_fetch_step.py` | 82 | `test_AC_F4_criteria_resolver_relative_dates` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_fetch_step.py` | 107 | `test_AC_F5_criteria_resolver_incremental` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_fetch_step.py` | 146 | `test_AC_F6_fetch_result_cache_status_default` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_fetch_step.py` | 163 | `test_AC_F7_freshness_ttl_all_data_types` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_fetch_step.py` | 179 | `test_AC_F8_is_market_closed_weekend` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_fetch_step.py` | 188 | `test_AC_F8_is_market_closed_after_hours` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_fetch_step.py` | 197 | `test_AC_F8_is_market_open_during_hours` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_fetch_step.py` | 212 | `test_AC_F9_rate_limiter_per_provider` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_fetch_step.py` | 244 | `test_AC_F10_http_cache_304_revalidated` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_fetch_step.py` | 273 | `test_AC_F11_fetch_step_cache_hit` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_fetch_step.py` | 309 | `test_AC_F12_params_rejects_invalid_batch_size` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_fetch_step.py` | 331 | `test_AC_F13_uow_pipeline_state_attribute` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_fetch_step.py` | 359 | `test_AC_F14_pipeline_state_repo_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_fetch_step.py` | 412 | `test_AC_F15_step_registration_via_import` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_fetch_step.py` | 430 | `test_AC_F16_fetch_step_execute_resolves_criteria` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_fetch_step.py` | 477 | `test_AC_F17_fetch_step_calls_provider_adapter` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_fetch_step.py` | 522 | `test_AC_F18_fetch_step_db_query_criteria_with_connection` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_fetch_step.py` | 581 | `test_AC_F19_fetch_step_raises_without_adapter` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_ibkr_flexquery.py` | 25 | `TestParseFileBasic.test_parse_valid_flexquery_returns_import_result` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 30 | `TestParseFileBasic.test_parse_valid_flexquery_has_correct_trade_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 37 | `TestParseFileBasic.test_parse_valid_flexquery_status_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 42 | `TestParseFileBasic.test_parse_valid_flexquery_broker_is_ibkr` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 54 | `TestRawExecutionFields.test_stock_trade_broker_type` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 60 | `TestRawExecutionFields.test_stock_trade_account_id` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 66 | `TestRawExecutionFields.test_stock_trade_exec_time_utc` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 73 | `TestRawExecutionFields.test_stock_trade_decimal_price` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 80 | `TestRawExecutionFields.test_stock_trade_decimal_quantity` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 86 | `TestRawExecutionFields.test_stock_trade_decimal_commission` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 93 | `TestRawExecutionFields.test_buy_side` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 99 | `TestRawExecutionFields.test_sell_side` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 112 | `TestSymbolNormalization.test_stock_symbol_passthrough` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 117 | `TestSymbolNormalization.test_option_symbol_to_occ` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_ibkr_flexquery.py` | 124 | `TestSymbolNormalization.test_fractional_strike_preserved` | couples to private or internal state |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 138 | `TestAssetClassification.test_stk_maps_to_equity` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 143 | `TestAssetClassification.test_opt_maps_to_option` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 148 | `TestAssetClassification.test_fut_maps_to_future` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 153 | `TestAssetClassification.test_cash_maps_to_forex` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 165 | `TestErrorHandling.test_malformed_row_produces_import_error` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 170 | `TestErrorHandling.test_malformed_row_status_partial` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 175 | `TestErrorHandling.test_malformed_row_valid_trades_still_parsed` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 182 | `TestErrorHandling.test_completely_malformed_xml_returns_failed` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 188 | `TestErrorHandling.test_empty_trades_section` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 202 | `TestXXEPrevention.test_xxe_attack_does_not_expose_file_content` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 215 | `TestMultiCurrency.test_usd_trade_currency` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 220 | `TestMultiCurrency.test_usd_trade_base_currency` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 225 | `TestMultiCurrency.test_eur_trade_currency` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 231 | `TestMultiCurrency.test_eur_trade_base_amount_populated` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 247 | `TestRawDataPreservation.test_raw_data_has_original_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 254 | `TestRawDataPreservation.test_raw_data_preserves_order_ref` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 267 | `TestAdapterProtocol.test_broker_type_property` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 271 | `TestAdapterProtocol.test_option_contract_multiplier` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_ibkr_flexquery.py` | 277 | `TestAdapterProtocol.test_future_contract_multiplier` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 75 | `TestValidateImage.test_accept_png` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 83 | `TestValidateImage.test_accept_jpeg` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 91 | `TestValidateImage.test_accept_gif` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 99 | `TestValidateImage.test_accept_webp` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 107 | `TestValidateImage.test_size_limit_exceeded` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_image_processing.py` | 115 | `TestValidateImage.test_unsupported_format` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_image_processing.py` | 121 | `TestValidateImage.test_invalid_data` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_image_processing.py` | 133 | `TestStandardizeToWebp.test_png_to_webp` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 142 | `TestStandardizeToWebp.test_jpeg_to_webp` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 149 | `TestStandardizeToWebp.test_preserves_alpha` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_image_processing.py` | 156 | `TestStandardizeToWebp.test_converts_palette_to_rgb` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_image_processing.py` | 163 | `TestStandardizeToWebp.test_webp_passthrough` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 177 | `TestGenerateThumbnail.test_thumbnail_within_bounds` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 185 | `TestGenerateThumbnail.test_thumbnail_preserves_aspect` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 193 | `TestGenerateThumbnail.test_thumbnail_is_webp` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_image_processing.py` | 200 | `TestGenerateThumbnail.test_thumbnail_small_image` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 22 | `TestMaskApiKeyAC5.test_masks_normal_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 25 | `TestMaskApiKeyAC5.test_masks_empty_string` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 28 | `TestMaskApiKeyAC5.test_masks_long_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 31 | `TestMaskApiKeyAC5.test_masks_short_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 38 | `TestSanitizeUrlAC6.test_replaces_key_in_url` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_log_redaction.py` | 44 | `TestSanitizeUrlAC6.test_replaces_multiple_occurrences` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_log_redaction.py` | 50 | `TestSanitizeUrlAC6.test_preserves_surrounding_text` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 59 | `TestSanitizeUrlShortKeyAC7.test_empty_key_returns_unchanged` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 63 | `TestSanitizeUrlShortKeyAC7.test_short_key_4_chars_returns_unchanged` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 67 | `TestSanitizeUrlShortKeyAC7.test_short_key_3_chars_returns_unchanged` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 71 | `TestSanitizeUrlShortKeyAC7.test_short_key_1_char_returns_unchanged` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_log_redaction.py` | 76 | `TestSanitizeUrlShortKeyAC7.test_5_char_key_does_replace` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_config.py` | 32 | `TestFeaturesRegistry.test_features_count` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_config.py` | 35 | `TestFeaturesRegistry.test_trades_prefix` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 38 | `TestFeaturesRegistry.test_accounts_prefix` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 41 | `TestFeaturesRegistry.test_marketdata_prefix` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 44 | `TestFeaturesRegistry.test_uvicorn_prefix` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 47 | `TestFeaturesRegistry.test_all_expected_features_present` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 63 | `TestGetFeatureLogger.test_returns_named_logger` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 68 | `TestGetFeatureLogger.test_unknown_feature_raises_value_error` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_logging_config.py` | 82 | `TestGetLogDirectory.test_returns_path` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 87 | `TestGetLogDirectory.test_directory_exists_after_call` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 92 | `TestGetLogDirectory.test_contains_zorivest_logs` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_config.py` | 107 | `TestBootstrap.test_creates_bootstrap_file` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_logging_config.py` | 123 | `TestBootstrap.test_bootstrap_log_written` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_logging_config.py` | 160 | `TestConfigureFromSettings.test_creates_feature_files` | couples to private or internal state |
| 🟡 | `tests/unit/test_logging_config.py` | 174 | `TestConfigureFromSettings.test_feature_routing` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_logging_config.py` | 196 | `TestConfigureFromSettings.test_catchall_routing` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_logging_config.py` | 211 | `TestConfigureFromSettings.test_settings_level_respected` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_logging_config.py` | 232 | `TestConfigureFromSettings.test_default_rotation_values` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_logging_config.py` | 246 | `TestUpdateFeatureLevel.test_update_gates_messages` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_logging_config.py` | 292 | `TestShutdown.test_shutdown_stops_listener` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_logging_config.py` | 320 | `TestThreadSafety.test_concurrent_logging` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_logging_filters.py` | 21 | `TestFeatureFilter.test_accepts_matching_prefix` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_filters.py` | 35 | `TestFeatureFilter.test_accepts_exact_prefix` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_filters.py` | 49 | `TestFeatureFilter.test_rejects_non_matching_prefix` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_filters.py` | 63 | `TestFeatureFilter.test_rejects_unrelated_logger` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_filters.py` | 88 | `TestCatchallFilter.test_accepts_non_feature_record` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_filters.py` | 102 | `TestCatchallFilter.test_rejects_known_feature_record` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_filters.py` | 116 | `TestCatchallFilter.test_rejects_exact_prefix_match` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_filters.py` | 130 | `TestCatchallFilter.test_accepts_with_empty_known_prefixes` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_logging_formatter.py` | 42 | `TestJsonFormatter.test_output_is_valid_json` | type or presence checks only without value assertions |
| 🟡 | `tests/unit/test_logging_formatter.py` | 49 | `TestJsonFormatter.test_output_is_single_line` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_logging_formatter.py` | 55 | `TestJsonFormatter.test_contains_all_standard_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_formatter.py` | 66 | `TestJsonFormatter.test_non_reserved_extras_included` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_logging_formatter.py` | 74 | `TestJsonFormatter.test_reserved_attrs_excluded` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_logging_formatter.py` | 83 | `TestJsonFormatter.test_underscore_prefixed_excluded` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_logging_formatter.py` | 90 | `TestJsonFormatter.test_exception_info_serialized` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_logging_formatter.py` | 106 | `TestJsonFormatter.test_no_exception_key_when_no_exception` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_logging_formatter.py` | 113 | `TestJsonFormatter.test_timestamp_is_utc_iso8601` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_logging_formatter.py` | 122 | `TestJsonFormatter.test_level_is_string_name` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_formatter.py` | 129 | `TestJsonFormatter.test_message_uses_getMessage` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_redaction.py` | 38 | `TestRedactionRegexPatterns.test_url_query_param_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 46 | `TestRedactionRegexPatterns.test_bearer_token_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 53 | `TestRedactionRegexPatterns.test_fernet_encrypted_value_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 60 | `TestRedactionRegexPatterns.test_jwt_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 67 | `TestRedactionRegexPatterns.test_aws_access_key_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 74 | `TestRedactionRegexPatterns.test_connection_string_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 82 | `TestRedactionRegexPatterns.test_credit_card_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 89 | `TestRedactionRegexPatterns.test_ssn_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 96 | `TestRedactionRegexPatterns.test_zorivest_api_key_redaction` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 110 | `TestRedactionKeyDenylist.test_password_key_redacted` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_redaction.py` | 117 | `TestRedactionKeyDenylist.test_api_key_key_redacted` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_redaction.py` | 124 | `TestRedactionKeyDenylist.test_nested_dict_redaction` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_redaction.py` | 140 | `TestRedactionBehavior.test_filter_always_returns_true` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_logging_redaction.py` | 146 | `TestRedactionBehavior.test_msg_modified_in_place` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 154 | `TestRedactionBehavior.test_non_reserved_extras_scanned` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 160 | `TestRedactionBehavior.test_string_args_redacted` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_logging_redaction.py` | 171 | `TestRedactionBehavior.test_clean_message_unchanged` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_api.py` | 101 | `TestGetQuote.test_returns_200_with_quote` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_market_data_api.py` | 108 | `TestGetQuote.test_missing_ticker_returns_422` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_market_data_api.py` | 112 | `TestGetQuote.test_locked_db_returns_403` | status-code assertion without response body verification |
| 🟡 | `tests/unit/test_market_data_api.py` | 116 | `TestGetQuote.test_service_error_returns_503` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_market_data_api.py` | 130 | `TestGetNews.test_returns_200_with_news` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_market_data_api.py` | 137 | `TestGetNews.test_with_ticker_filter` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_market_data_api.py` | 148 | `TestSearchTicker.test_returns_200_with_results` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_market_data_api.py` | 155 | `TestSearchTicker.test_missing_query_returns_422` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_market_data_api.py` | 166 | `TestGetSecFilings.test_returns_200_with_filings` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_market_data_api.py` | 180 | `TestListProviders.test_returns_200` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_market_data_api.py` | 188 | `TestConfigureProvider.test_returns_configured` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_market_data_api.py` | 197 | `TestConfigureProvider.test_unknown_provider_returns_404` | status-code assertion without response body verification |
| 🟢 | `tests/unit/test_market_data_api.py` | 211 | `TestTestProvider.test_returns_success` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_data_api.py` | 223 | `TestRemoveProviderKey.test_returns_removed` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_provider_settings_repo.py` | 29 | `TestMarketProviderSettingsRepoCRUD.test_save_and_get_round_trip` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_provider_settings_repo.py` | 50 | `TestMarketProviderSettingsRepoCRUD.test_get_unknown_returns_none` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_market_provider_settings_repo.py` | 55 | `TestMarketProviderSettingsRepoCRUD.test_list_all_returns_all` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_market_provider_settings_repo.py` | 76 | `TestMarketProviderSettingsRepoCRUD.test_delete_removes_entry` | specific value or behavioral assertions |
| 🔴 | `tests/unit/test_market_provider_settings_repo.py` | 94 | `TestMarketProviderSettingsRepoCRUD.test_delete_nonexistent_is_noop` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_market_provider_settings_repo.py` | 99 | `TestMarketProviderSettingsRepoCRUD.test_save_updates_existing` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 225 | `TestNormalizeAlphaVantageQuote.test_full_response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 240 | `TestNormalizeAlphaVantageQuote.test_empty_global_quote` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 248 | `TestNormalizeAlphaVantageQuote.test_missing_fields_use_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_normalizers.py` | 263 | `TestNormalizePolygonQuote.test_full_response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 275 | `TestNormalizePolygonQuote.test_empty_results` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 282 | `TestNormalizePolygonQuote.test_missing_results_key` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 295 | `TestNormalizeFinnhubQuote.test_full_response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 309 | `TestNormalizeFinnhubQuote.test_empty_response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 323 | `TestNormalizeEodhdQuote.test_full_response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 338 | `TestNormalizeEodhdQuote.test_empty_response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 352 | `TestNormalizeApiNinjasQuote.test_full_response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 360 | `TestNormalizeApiNinjasQuote.test_empty_response` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 374 | `TestNormalizeFmpSearch.test_multiple_results` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 389 | `TestNormalizeFmpSearch.test_empty_list` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_normalizers.py` | 393 | `TestNormalizeFmpSearch.test_missing_optional_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 409 | `TestNormalizeAlphaVantageSearch.test_multiple_results` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 442 | `TestNormalizeAlphaVantageSearch.test_empty_best_matches` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_normalizers.py` | 446 | `TestNormalizeAlphaVantageSearch.test_missing_best_matches_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_normalizers.py` | 457 | `TestNormalizeSecFiling.test_multiple_filings` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 472 | `TestNormalizeSecFiling.test_empty_list` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_normalizers.py` | 476 | `TestNormalizeSecFiling.test_missing_optional_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 491 | `TestNormalizeBenzingaNews.test_multiple_articles` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 507 | `TestNormalizeBenzingaNews.test_empty_list` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_normalizers.py` | 511 | `TestNormalizeBenzingaNews.test_missing_optional_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 527 | `TestNormalizeFinnhubNews.test_multiple_articles` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_normalizers.py` | 544 | `TestNormalizeFinnhubNews.test_empty_list` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_normalizers.py` | 548 | `TestNormalizeFinnhubNews.test_missing_optional_fields` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 142 | `TestSequentialExecution.test_two_steps_run_sequentially` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 156 | `TestSequentialExecution.test_empty_steps_not_allowed` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 165 | `TestSkipConditions.test_skip_if_condition_met` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 190 | `TestDryRun.test_dry_run_skips_side_effect_steps` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 213 | `TestFailPipeline.test_fail_pipeline_stops_on_error` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 250 | `TestLogAndContinue.test_log_and_continue_proceeds` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 272 | `TestRetryThenFail.test_retry_succeeds_on_third_attempt` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 303 | `TestRetryThenFail.test_retry_exhausted_fails_pipeline` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 325 | `TestRefResolution.test_ref_resolved_from_prior_step` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 352 | `TestReturnStructure.test_return_dict_keys` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 371 | `TestUnknownStepType.test_unknown_step_type_fails` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 388 | `TestResumeFrom.test_resume_from_skips_prior_steps` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 432 | `TestTimeoutHandling.test_step_timeout_fails_pipeline` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 453 | `TestCancellationHandling.test_cancelled_pipeline_returns_cancelled` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 475 | `TestZombieRecovery.test_recover_zombies_no_uow_returns_empty` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_pipeline_runner.py` | 516 | `TestPersistenceWithUoW.test_run_persists_pipeline_run_and_steps` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_policy_validator.py` | 56 | `TestValidPolicy.test_valid_policy` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_policy_validator.py` | 61 | `TestValidPolicy.test_multi_step_valid` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_policy_validator.py` | 76 | `TestSchemaVersion.test_version_2_rejected` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_policy_validator.py` | 81 | `TestSchemaVersion.test_version_1_accepted` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_policy_validator.py` | 93 | `TestStepCount.test_ten_steps_accepted` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_policy_validator.py` | 106 | `TestUnknownStepType.test_unknown_type_rejected` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 113 | `TestUnknownStepType.test_known_type_accepted` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 127 | `TestReferentialIntegrity.test_valid_backward_ref` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 138 | `TestReferentialIntegrity.test_forward_ref_rejected` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 148 | `TestReferentialIntegrity.test_nested_ref_checked` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 157 | `TestReferentialIntegrity.test_malformed_ref_rejected` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 167 | `TestReferentialIntegrity.test_ref_in_nested_list` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 177 | `TestReferentialIntegrity.test_non_string_ref_rejected` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 187 | `TestReferentialIntegrity.test_non_string_ref_in_list_rejected` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 204 | `TestCronValidation.test_valid_cron` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 209 | `TestCronValidation.test_invalid_cron` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 214 | `TestCronValidation.test_six_field_cron` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 227 | `TestSQLBlocklist.test_clean_params` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 234 | `TestSQLBlocklist.test_blocked_keyword` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 241 | `TestSQLBlocklist.test_multiple_blocked` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 248 | `TestSQLBlocklist.test_punctuation_bypass_blocked` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 256 | `TestSQLBlocklist.test_semicolon_concat_blocked` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_policy_validator.py` | 271 | `TestContentHash.test_deterministic` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_policy_validator.py` | 277 | `TestContentHash.test_sha256_length` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_policy_validator.py` | 282 | `TestContentHash.test_different_docs_different_hash` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_policy_validator.py` | 298 | `TestSQLBlocklistConstant.test_keyword_present` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 308 | `TestRecursiveSQLScan.test_nested_dict` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 317 | `TestRecursiveSQLScan.test_nested_list` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_policy_validator.py` | 326 | `TestRecursiveSQLScan.test_deeply_nested` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_provider_registry.py` | 62 | `TestProviderRegistryAC1.test_registry_count` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_provider_registry.py` | 65 | `TestProviderRegistryAC1.test_registry_is_dict` | type or presence checks only without value assertions |
| 🔴 | `tests/unit/test_provider_registry.py` | 68 | `TestProviderRegistryAC1.test_all_values_are_provider_config` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 77 | `TestProviderRegistryAC2.test_provider_has_non_empty_base_url` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 82 | `TestProviderRegistryAC2.test_provider_has_non_empty_test_endpoint` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 87 | `TestProviderRegistryAC2.test_provider_has_non_empty_auth_param_name` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 92 | `TestProviderRegistryAC2.test_provider_has_positive_rate_limit` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 97 | `TestProviderRegistryAC2.test_provider_name_matches_key` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 105 | `TestProviderRegistryAC3.test_all_expected_names_present` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 109 | `TestProviderRegistryAC3.test_no_unexpected_names` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_registry.py` | 119 | `TestGetProviderConfigAC4.test_returns_provider_config_for_known` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_registry.py` | 124 | `TestGetProviderConfigAC4.test_returns_correct_config` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 128 | `TestGetProviderConfigAC4.test_raises_key_error_for_unknown` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_provider_registry.py` | 136 | `TestListProviderNamesAC5.test_returns_sorted_list` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 140 | `TestListProviderNamesAC5.test_returns_12_names` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_provider_registry.py` | 144 | `TestListProviderNamesAC5.test_matches_expected_names` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_provider_registry.py` | 156 | `TestAuthMethodsAC6.test_auth_method_matches_spec` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 81 | `TestPolicyRepository.test_create_and_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 90 | `TestPolicyRepository.test_get_by_name` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 99 | `TestPolicyRepository.test_list_all_with_enabled_filter` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 115 | `TestPolicyRepository.test_update` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 127 | `TestPolicyRepository.test_delete` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_scheduling_repos.py` | 148 | `TestPipelineRunRepository.test_create_and_get` | couples to private or internal state |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 160 | `TestPipelineRunRepository.test_find_zombies` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_scheduling_repos.py` | 179 | `TestPipelineRunRepository.test_list_by_policy` | couples to private or internal state |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 191 | `TestPipelineRunRepository.test_update_status` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_scheduling_repos.py` | 206 | `TestPipelineRunRepository.test_list_recent` | couples to private or internal state |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 223 | `TestReportRepository.test_create_and_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 235 | `TestReportRepository.test_get_versions_empty` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 251 | `TestFetchCacheRepository.test_upsert_insert` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 264 | `TestFetchCacheRepository.test_upsert_update` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 284 | `TestFetchCacheRepository.test_invalidate` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_scheduling_repos.py` | 301 | `TestAuditLogRepository.test_append_and_list` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_scheduling_repos.py` | 322 | `TestSessionPattern.test_all_repos_accept_session` | couples to private or internal state |
| 🔴 | `tests/unit/test_scheduling_repos.py` | 333 | `TestUnitOfWorkExtension.test_uow_has_scheduling_repos` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_step_registry.py` | 53 | `TestAutoRegistration.test_subclass_registers` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_step_registry.py` | 58 | `TestAutoRegistration.test_empty_type_name_skipped` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_step_registry.py` | 66 | `TestAutoRegistration.test_multiple_registrations` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_step_registry.py` | 78 | `TestDuplicateDetection.test_duplicate_raises` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_step_registry.py` | 90 | `TestGetStep.test_existing` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_step_registry.py` | 94 | `TestGetStep.test_missing` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_step_registry.py` | 104 | `TestHasStep.test_existing` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_step_registry.py` | 108 | `TestHasStep.test_missing` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_step_registry.py` | 118 | `TestListSteps.test_returns_dicts` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_step_registry.py` | 127 | `TestListSteps.test_dict_keys` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_step_registry.py` | 136 | `TestListSteps.test_side_effects_value` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_step_registry.py` | 149 | `TestBaseExecute.test_base_execute_raises` | specific exception behavior asserted |
| 🔴 | `tests/unit/test_step_registry.py` | 162 | `TestCompensate.test_default_compensate_noop` | trivially weak structure (private patch or no assertions) |
| 🟢 | `tests/unit/test_step_registry.py` | 176 | `TestParamsSchema.test_no_params_class` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_step_registry.py` | 182 | `TestParamsSchema.test_with_params_class` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/unit/test_step_registry.py` | 204 | `TestStepBaseProtocol.test_runtime_checkable` | type or presence checks only without value assertions |
| 🟢 | `tests/unit/test_step_registry.py` | 209 | `TestStepBaseProtocol.test_stepbase_importable_from_pipeline` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_step_registry.py` | 222 | `TestGetAllSteps.test_returns_classes` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_step_registry.py` | 229 | `TestGetAllSteps.test_classes_have_attributes` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_step_registry.py` | 238 | `TestGetAllSteps.test_multiple_classes` | specific value or behavioral assertions |
| 🟡 | `tests/unit/test_store_render_step.py` | 22 | `test_AC_SR1_store_report_step_auto_registers` | right target, but weak assertions only |
| 🟡 | `tests/unit/test_store_render_step.py` | 39 | `test_AC_SR2_render_step_auto_registers` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_store_render_step.py` | 56 | `test_AC_SR3_report_spec_validates_sections` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 85 | `test_AC_SR4_data_table_max_rows_limit` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_store_render_step.py` | 103 | `test_AC_SR5_authorizer_allows_select` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_store_render_step.py` | 117 | `test_AC_SR6_authorizer_denies_writes` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_store_render_step.py` | 132 | `test_AC_SR7_sandboxed_connection_query_only` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_store_render_step.py` | 151 | `test_AC_SR8_template_engine_filters` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 174 | `test_AC_SR9_store_report_params` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_store_render_step.py` | 193 | `test_AC_SR10_render_step_params_defaults` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_store_render_step.py` | 206 | `test_AC_SR11_render_candlestick_keys` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 236 | `test_AC_SR12_render_pdf_creates_directory` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_store_render_step.py` | 262 | `test_AC_SR13_both_steps_have_side_effects` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_store_render_step.py` | 276 | `test_AC_SR14_live_uow_report_snapshot` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 307 | `test_AC_SR15_report_repo_snapshot_fields` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_store_render_step.py` | 339 | `test_AC_SR16_store_report_step_execute_snapshot` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 385 | `test_AC_SR16b_store_report_step_executes_sandboxed_sql` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 436 | `test_AC_SR16c_store_report_persists_via_repository` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 483 | `test_AC_SR17_render_step_execute_produces_html` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 519 | `test_AC_SR17b_render_step_uses_template_engine` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 556 | `test_AC_SR17c_render_step_html_only_no_pdf` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 580 | `test_AC_SR18_store_report_step_raises_without_repository` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_store_render_step.py` | 601 | `test_AC_CR1_criteria_resolver_per_field_with_static` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_store_render_step.py` | 626 | `test_AC_SR20_execute_sandboxed_sql_raises_without_connection` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 31 | `TestTradeFingerprint.test_deterministic` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 38 | `TestTradeFingerprint.test_different_exec_id_same_fingerprint` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 44 | `TestTradeFingerprint.test_different_instrument_different_fingerprint` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 49 | `TestTradeFingerprint.test_different_action_different_fingerprint` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 54 | `TestTradeFingerprint.test_different_quantity_different_fingerprint` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 59 | `TestTradeFingerprint.test_different_price_different_fingerprint` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 64 | `TestTradeFingerprint.test_different_time_different_fingerprint` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 69 | `TestTradeFingerprint.test_different_account_different_fingerprint` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_trade_fingerprint.py` | 74 | `TestTradeFingerprint.test_returns_hex_string` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/unit/test_transform_step.py` | 21 | `test_AC_T1_transform_step_auto_registers` | right target, but weak assertions only |
| 🟢 | `tests/unit/test_transform_step.py` | 39 | `test_AC_T2_params_validates_required_target_table` | specific exception behavior asserted |
| 🟢 | `tests/unit/test_transform_step.py` | 57 | `test_AC_T3_field_mapping_with_extras` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_transform_step.py` | 90 | `test_AC_T4_field_mapping_empty_input` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 109 | `test_AC_T5_validate_valid_ohlcv` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_transform_step.py` | 132 | `test_AC_T6_validate_quarantines_invalid` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_transform_step.py` | 155 | `test_AC_T7_quality_below_threshold` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 165 | `test_AC_T7_quality_above_threshold` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 180 | `test_AC_T8_table_allowlist_rejects_unknown` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 200 | `test_AC_T9_validate_columns_rejects_unknown` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 218 | `test_AC_T10_micros_round_trip` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_transform_step.py` | 230 | `test_AC_T10_micros_precision_edge_cases` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 246 | `test_AC_T11_parse_monetary_precision` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 262 | `test_AC_T12_transform_step_side_effects` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 274 | `test_AC_T13_live_uow_write_append` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 319 | `test_AC_T14_transform_step_execute_validates_records` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 358 | `test_AC_T14b_transform_step_execute_quality_gate_rejects` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/unit/test_transform_step.py` | 392 | `test_AC_T15_transform_step_write_data_calls_db_writer` | specific value or behavioral assertions |
| 🟢 | `tests/unit/test_transform_step.py` | 439 | `test_AC_T16_transform_step_raises_without_writer` | specific exception behavior asserted |
