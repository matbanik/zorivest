# Integration Tests

Per-test rating table for Phase 1 IR-5 audit.

Summary: 48 tests audited | 🟢 39 | 🟡 7 | 🔴 2

| Rating | File | Line | Test | Reason |
|---|---|---:|---|---|
| 🟢 | `tests/integration/test_backup_integration.py` | 47 | `TestFullBackupCycle.test_full_backup_cycle` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/integration/test_backup_integration.py` | 116 | `TestFullBackupCycle.test_wrong_passphrase_cannot_read` | couples to private or internal state |
| 🟢 | `tests/integration/test_backup_recovery_integration.py` | 100 | `TestFullCycle.test_create_and_verify` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_backup_recovery_integration.py` | 115 | `TestFullCycle.test_create_and_restore` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_backup_recovery_integration.py` | 155 | `TestFullCycle.test_wrong_passphrase_fails` | specific exception behavior asserted |
| 🟢 | `tests/integration/test_backup_recovery_integration.py` | 170 | `TestFullCycle.test_maintenance_hooks_called` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_backup_recovery_integration.py` | 194 | `TestFullCycle.test_verify_then_restore_roundtrip` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_database_connection.py` | 20 | `TestDeriveKey.test_deterministic_with_same_salt` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_database_connection.py` | 26 | `TestDeriveKey.test_32_bytes` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_database_connection.py` | 30 | `TestDeriveKey.test_different_passwords_different_keys` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_database_connection.py` | 36 | `TestDeriveKey.test_different_salts_different_keys` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_database_connection.py` | 45 | `TestCreateEncryptedConnection.test_create_and_use_database` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_database_connection.py` | 59 | `TestCreateEncryptedConnection.test_wal_mode_enabled` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_database_connection.py` | 70 | `TestCreateEncryptedConnection.test_reopen_database` | exact behavior asserted despite weaker auxiliary checks |
| 🔴 | `tests/integration/test_database_connection.py` | 93 | `TestEncryptionContract.test_sqlcipher_availability_flag` | type or presence checks only without value assertions |
| 🟢 | `tests/integration/test_database_connection.py` | 102 | `TestEncryptionContract.test_encrypted_db_unreadable_by_plain_sqlite` | specific exception behavior asserted |
| 🟡 | `tests/integration/test_database_connection.py` | 121 | `TestEncryptionContract.test_fallback_produces_plaintext_warning` | right target, but weak assertions only |
| 🟢 | `tests/integration/test_repositories.py` | 84 | `TestTradeRepository.test_save_and_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/integration/test_repositories.py` | 100 | `TestTradeRepository.test_exists` | right target, but weak assertions only |
| 🟢 | `tests/integration/test_repositories.py` | 112 | `TestTradeRepository.test_list_all` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 125 | `TestTradeRepository.test_list_for_account` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/integration/test_repositories.py` | 147 | `TestTradeRepository.test_exists_by_fingerprint_since` | right target, but weak assertions only |
| 🟢 | `tests/integration/test_repositories.py` | 166 | `TestImageRepository.test_save_and_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 176 | `TestImageRepository.test_get_for_owner` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 186 | `TestImageRepository.test_delete` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_repositories.py` | 196 | `TestImageRepository.test_get_thumbnail` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 209 | `TestAccountRepository.test_save_and_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 219 | `TestAccountRepository.test_list_all` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 232 | `TestBalanceSnapshotRepository.test_save_and_list_for_account` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 255 | `TestRoundTripRepository.test_save_and_list_for_account` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 288 | `TestTradeReportRepository.test_save_and_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/integration/test_repositories.py` | 316 | `TestTradeReportRepository.test_get_for_trade_returns_none_when_missing` | couples to private or internal state |
| 🟢 | `tests/integration/test_repositories.py` | 323 | `TestTradeReportRepository.test_update` | exact behavior asserted despite weaker auxiliary checks |
| 🟡 | `tests/integration/test_repositories.py` | 361 | `TestTradeReportRepository.test_delete` | couples to private or internal state |
| 🟢 | `tests/integration/test_repositories.py` | 390 | `TestTradePlanRepository.test_save_and_get` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 423 | `TestTradePlanRepository.test_get_returns_none_when_missing` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_repositories.py` | 427 | `TestTradePlanRepository.test_list_all` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 446 | `TestTradePlanRepository.test_update` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_repositories.py` | 474 | `TestTradePlanRepository.test_delete` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_unit_of_work.py` | 27 | `TestUnitOfWork.test_commit_persists_data` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_unit_of_work.py` | 50 | `TestUnitOfWork.test_rollback_discards_data` | specific value or behavioral assertions |
| 🟡 | `tests/integration/test_unit_of_work.py` | 71 | `TestUnitOfWork.test_context_manager_closes_session` | couples to private or internal state |
| 🔴 | `tests/integration/test_unit_of_work.py` | 82 | `TestUnitOfWork.test_all_repos_available` | type or presence checks only without value assertions |
| 🟢 | `tests/integration/test_unit_of_work.py` | 103 | `TestUnitOfWork.test_trade_with_account_fk` | exact behavior asserted despite weaker auxiliary checks |
| 🟢 | `tests/integration/test_unit_of_work.py` | 137 | `TestUnitOfWork.test_exit_on_exception_rollbacks` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_wal_concurrency.py` | 22 | `TestWalMode.test_wal_mode_enabled` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_wal_concurrency.py` | 33 | `TestWalMode.test_synchronous_normal` | specific value or behavioral assertions |
| 🟢 | `tests/integration/test_wal_concurrency.py` | 48 | `TestPerThreadSessions.test_concurrent_read_write` | exact behavior asserted despite weaker auxiliary checks |
