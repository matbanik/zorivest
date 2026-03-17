# IR-5 Test Corrections — Upgrading 285 Weak Tests to 🟢

Systematically fix all 71 🔴 and 214 🟡 tests identified by the Phase 1 IR-5 audit across 72 test files, using the anti-pattern taxonomy from [phase1-ir5-pattern-analysis.md](../2026-03-16-test-rigor-audit/phase1-ir5-pattern-analysis.md).

- **Project slug**: `2026-03-16-ir5-test-corrections`
- **Source audit**: [phase1-ir5-per-test-ratings.csv](../2026-03-16-test-rigor-audit/phase1-ir5-per-test-ratings.csv)
- **Pattern analysis**: [phase1-ir5-pattern-analysis.md](../2026-03-16-test-rigor-audit/phase1-ir5-pattern-analysis.md)
- **Baseline**: 285 weak tests (71 🔴, 214 🟡) across 72 files
- **Target**: 0 🔴, 0 🟡 — all tests upgraded to 🟢

---

## User Review Required

> [!IMPORTANT]
> This project **modifies test assertions only** — no production code changes. All existing tests must continue to pass after assertion strengthening. If a test's assertion upgrade reveals that the production code has a bug, the bug is documented in a new `known-issues.md` entry but **not** fixed in this project scope.

> [!WARNING]
> Some 🟡 tests rated "couples to private or internal state" may require **refactoring the test to use a public interface** rather than simply adding assertions. These changes alter test structure, not just assertions.

---

## Spec-Sufficiency & Feature Intent Contract

### Source Resolution

All test corrections are specified from canonical project sources:

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---------------------|-------------|--------|:---------:|-------|
| Per-test 🔴/🟡 ratings and anti-pattern classification | Local Canon | `phase1-ir5-per-test-ratings.csv` | ✅ | IR-5 audit deliverable |
| Anti-pattern upgrade protocols (R1→value, Y3→contract, etc.) | Local Canon | §Upgrade Protocols (below) + `phase1-ir5-pattern-analysis.md` §Anti-Pattern Taxonomy | ✅ | Self-contained in this plan; taxonomy derived from audit |
| Per-file weak-test counts and batch assignment | Local Canon | `phase1-ir5-per-test-ratings.csv` | ✅ | Cross-referenced with batch tables below |
| Test pass/fail contract (no regressions) | Local Canon | `AGENTS.md` §Testing & TDD Protocol | ✅ | Test immutability rule |
| BUILD_PLAN maintenance | Local Canon | `.agent/workflows/create-plan.md:129-138` | ✅ | Mandatory planning task |

### Feature Intent Contract (per batch)

Each batch shares the same acceptance criteria:

| AC | Description | Source Base |
|----|-------------|:-----------:|
| AC-1 | All previously 🔴/🟡 tests in batch compile and pass after assertion upgrade | Local Canon |
| AC-2 | Each upgraded test asserts concrete values, not just types/presence/status-codes | Local Canon |
| AC-3 | No new test failures introduced in any file outside the batch scope | Local Canon |
| AC-4 | `uv run pyright packages/` reports 0 new errors from assertion changes | Local Canon |

### Stop Conditions

- **Stop and ask human**: if an assertion upgrade reveals a production bug (the test now fails because the implementation is wrong, not because the assertion is bad)
- **Stop and ask human**: if a test requires refactoring beyond assertion changes (e.g., adding fixtures, changing test structure, introducing new helpers)
- **Do not stop**: if an assertion upgrade causes the test itself to need a value update (the expected value was never checked before)

### Handoff Naming

Execution handoffs (next available sequence after 073):

| Batch | Handoff Path |
|-------|-------------|
| 1 | `.agent/context/handoffs/074-2026-03-17-ir5-corrections-b1-bp00s0.0.md` |
| 2 | `.agent/context/handoffs/075-2026-03-17-ir5-corrections-b2-bp00s0.0.md` |
| 3 | `.agent/context/handoffs/076-2026-03-17-ir5-corrections-b3-bp00s0.0.md` |
| 4 | `.agent/context/handoffs/077-2026-03-17-ir5-corrections-b4-bp00s0.0.md` |
| 5 | `.agent/context/handoffs/078-2026-03-17-ir5-corrections-b5-bp00s0.0.md` |
| 6 | `.agent/context/handoffs/079-2026-03-17-ir5-corrections-b6-bp00s0.0.md` |
| 7 (closeout) | `.agent/context/handoffs/080-2026-03-17-ir5-corrections-closeout-bp00s0.0.md` |

---

## Proposed Changes

The work is organized into 6 batches by category, ordered from highest concentration to lowest.

---

### Batch 1: Domain Tests (53 weak: 41🔴 + 12🟡)

Domain tests have the highest 🔴 concentration — mostly type-guard tests that verify `isinstance()` instead of checking actual values.

#### [MODIFY] [test_ports.py](file:///p:/zorivest/tests/unit/test_ports.py) — 8🔴 3🟡

**Anti-pattern R1:** Type-guard tests for domain ID ports. Replace `isinstance(TradeId("X"), str)` with `assert TradeId("X") == "X"`.

- Upgrade all `test_*_is_string` / `test_*_type` tests to check actual values
- Tighten `len(x) > 0` assertions to exact value checks

#### [MODIFY] [test_market_data_entities.py](file:///p:/zorivest/tests/unit/test_market_data_entities.py) — 6🔴

**Anti-pattern R1:** Entity construction tests checking `isinstance()` only. Add field-value assertions after construction.

#### [MODIFY] [test_exceptions.py](file:///p:/zorivest/tests/unit/test_exceptions.py) — 6🔴

**Anti-pattern R1:** Exception tests checking `isinstance(e, SomeError)`. Add message content and attribute assertions.

#### [MODIFY] [test_events.py](file:///p:/zorivest/tests/unit/test_events.py) — 5🔴

**Anti-pattern R1:** Event class tests checking type only. Add payload field value assertions.

#### [MODIFY] [test_commands_dtos.py](file:///p:/zorivest/tests/unit/test_commands_dtos.py) — 4🔴

**Anti-pattern R1:** Command/DTO construction tests checking presence only. Add field equality assertions.

#### [MODIFY] [test_pipeline_enums.py](file:///p:/zorivest/tests/unit/test_pipeline_enums.py) — 3🔴

**Anti-pattern R1:** Enum membership tests without value checks. Add exact `.value` comparisons.

#### [MODIFY] [test_scheduling_models.py](file:///p:/zorivest/tests/unit/test_scheduling_models.py) — 2🔴 6🟡

**Anti-patterns R1+Y1:** Model construction type checks + weak assertions. Add field-value assertions and tighten loose checks.

#### [MODIFY] [test_entities.py](file:///p:/zorivest/tests/unit/test_entities.py) — 2🔴

**Anti-pattern R1:** Type-presence checks on entity attributes.

#### [MODIFY] [test_enums.py](file:///p:/zorivest/tests/unit/test_enums.py) — 2🔴

**Anti-pattern R1:** Enum tests checking membership without values.

#### Small files (1 weak each):

| File | Rating | Anti-pattern |
|------|--------|-------------|
| [test_value_objects.py](file:///p:/zorivest/tests/unit/test_value_objects.py) | 1🔴 | R1: type check |
| [test_pipeline_models.py](file:///p:/zorivest/tests/unit/test_pipeline_models.py) | 1🔴 | R1: type check |
| [test_calculator.py](file:///p:/zorivest/tests/unit/test_calculator.py) | 1🔴 | R1: type check |
| [test_portfolio_balance.py](file:///p:/zorivest/tests/unit/test_portfolio_balance.py) | 1🟡 | Y1: weak assertion |
| [test_models.py](file:///p:/zorivest/tests/unit/test_models.py) | 1🟡 | Y1: weak assertion |
| [test_display_mode.py](file:///p:/zorivest/tests/unit/test_display_mode.py) | 1🟡 | Y1: weak assertion |

---

### Batch 2: API Tests (84 weak: 3🔴 + 81🟡)

API tests have the highest 🟡 concentration — mostly status-code-only assertions without response body verification.

#### [MODIFY] [test_api_analytics.py](file:///p:/zorivest/tests/unit/test_api_analytics.py) — 10🟡

**Anti-pattern Y3:** Status-code only. Add `response.json()` assertions checking response shape, field values, and error details.

#### [MODIFY] [test_api_tax.py](file:///p:/zorivest/tests/unit/test_api_tax.py) — 9🟡

**Anti-pattern Y3:** Status-code only on tax endpoint tests.

#### [MODIFY] [test_api_system.py](file:///p:/zorivest/tests/unit/test_api_system.py) — 9🟡

**Anti-pattern Y3:** Status-code only on system endpoint tests.

#### [MODIFY] [test_api_trades.py](file:///p:/zorivest/tests/unit/test_api_trades.py) — 8🟡

**Anti-pattern Y3:** Status-code only on trade CRUD tests.

#### [MODIFY] [test_api_plans.py](file:///p:/zorivest/tests/unit/test_api_plans.py) — 8🟡

**Anti-pattern Y3:** Status-code only on plan endpoint tests.

#### [MODIFY] [test_api_reports.py](file:///p:/zorivest/tests/unit/test_api_reports.py) — 7🟡

**Anti-pattern Y3:** Status-code only on report endpoint tests.

#### [MODIFY] [test_api_foundation.py](file:///p:/zorivest/tests/unit/test_api_foundation.py) — 1🔴 5🟡

**Anti-patterns R1+Y3:** Foundation middleware type checks + status-code assertions.

#### [MODIFY] [test_api_auth.py](file:///p:/zorivest/tests/unit/test_api_auth.py) — 6🟡

**Anti-pattern Y3:** Auth endpoint status-code only.

#### [MODIFY] [test_api_settings.py](file:///p:/zorivest/tests/unit/test_api_settings.py) — 1🔴 4🟡

**Anti-patterns R2+Y3:** Settings endpoint status-code + type checks.

#### [MODIFY] [test_api_accounts.py](file:///p:/zorivest/tests/unit/test_api_accounts.py) — 4🟡

**Anti-pattern Y3:** Account endpoint status-code only.

#### [MODIFY] [test_api_watchlists.py](file:///p:/zorivest/tests/unit/test_api_watchlists.py) — 4🟡

**Anti-pattern Y3:** Watchlist endpoint status-code only.

#### Small files:

| File | Rating | Anti-pattern |
|------|--------|-------------|
| [test_api_key_encryption.py](file:///p:/zorivest/tests/unit/test_api_key_encryption.py) | 1🔴 | R1: type check |
| [test_market_data_api.py](file:///p:/zorivest/tests/unit/test_market_data_api.py) | 7🟡 | Y3: status-code |

---

### Batch 3: Service Tests (48 weak: 13🔴 + 35🟡)

Service tests mix type-guard tests with mock-only and private-state-coupling patterns.

#### [MODIFY] [test_settings_validator.py](file:///p:/zorivest/tests/unit/test_settings_validator.py) — 13🟡

**Anti-pattern Y1:** Weak assertions on validation outcomes — tighten to exact error messages and field counts.

#### [MODIFY] [test_report_service.py](file:///p:/zorivest/tests/unit/test_report_service.py) — 2🔴 3🟡

**Anti-patterns R3+Y4:** No-op tests + mock-only assertions. Add concrete return-value and call-argument checks.

#### [MODIFY] [test_settings_resolver.py](file:///p:/zorivest/tests/unit/test_settings_resolver.py) — 5🟡

**Anti-pattern Y1+Y2:** Weak assertions + private state coupling.

#### [MODIFY] [test_settings_registry.py](file:///p:/zorivest/tests/unit/test_settings_registry.py) — 1🔴 3🟡

**Anti-patterns R1+Y2:** Type check on registry + private state coupling.

#### [MODIFY] [test_ref_resolver.py](file:///p:/zorivest/tests/unit/test_ref_resolver.py) — 4🟡

**Anti-pattern Y1:** Weak assertions on resolution results.

#### [MODIFY] [test_analytics.py](file:///p:/zorivest/tests/unit/test_analytics.py) — 3🔴

**Anti-pattern R1:** Type-guard tests on analytics functions.

#### [MODIFY] [test_rate_limiter.py](file:///p:/zorivest/tests/unit/test_rate_limiter.py) — 2🔴 1🟡

**Anti-patterns R1+R3:** Type check + no-op tests.

#### Small files:

| File | Rating | Anti-pattern |
|------|--------|-------------|
| [test_service_extensions.py](file:///p:/zorivest/tests/unit/test_service_extensions.py) | 2🔴 | R1: type checks |
| [test_settings_cache.py](file:///p:/zorivest/tests/unit/test_settings_cache.py) | 2🟡 | Y2: private state |
| [test_system_service.py](file:///p:/zorivest/tests/unit/test_system_service.py) | 1🔴 | R3: no-op |
| [test_provider_connection_service.py](file:///p:/zorivest/tests/unit/test_provider_connection_service.py) | 1🔴 | R3: no-op |
| [test_market_data_service.py](file:///p:/zorivest/tests/unit/test_market_data_service.py) | 1🔴 | R3: no-op |
| [test_watchlist_service.py](file:///p:/zorivest/tests/unit/test_watchlist_service.py) | 1🟡 | Y4: mock-only |
| [test_settings_service.py](file:///p:/zorivest/tests/unit/test_settings_service.py) | 1🟡 | Y4: mock-only |
| [test_image_service.py](file:///p:/zorivest/tests/unit/test_image_service.py) | 1🟡 | Y4: mock-only |
| [test_account_review.py](file:///p:/zorivest/tests/unit/test_account_review.py) | 1🟡 | Y4: mock-only |

---

### Batch 4: Infrastructure / Pipeline Tests (78 weak: 12🔴 + 66🟡)

Largest batch by test count. Concentrations in policy validator (21) and logging tests (14).

#### [MODIFY] [test_policy_validator.py](file:///p:/zorivest/tests/unit/test_policy_validator.py) — 21🟡

**Anti-pattern Y1:** All 21 tests use `assert result.is_valid` or `assert not result.is_valid` without checking specific error messages, violation counts, or paths. Tighten each to assert exact violation details.

#### [MODIFY] [test_logging_config.py](file:///p:/zorivest/tests/unit/test_logging_config.py) — 1🔴 8🟡

**Anti-patterns R1+Y1+Y2:** Type check on return value + weak assertions on log routing + private state checks.

#### [MODIFY] [test_csv_import.py](file:///p:/zorivest/tests/unit/test_csv_import.py) — 2🔴 5🟡

**Anti-patterns R1+Y1:** Type-only checks on parser return types + weak assertions on parsed data.

#### [MODIFY] [test_logging_formatter.py](file:///p:/zorivest/tests/unit/test_logging_formatter.py) — 1🔴 5🟡

**Anti-patterns R1+Y1:** Type check on JSON output + weak field assertions.

#### [MODIFY] [test_config_export.py](file:///p:/zorivest/tests/unit/test_config_export.py) — 6🟡

**Anti-patterns Y1+Y2:** Weak export assertions + private state (`_is_portable`) coupling.

#### [MODIFY] [test_scheduling_repos.py](file:///p:/zorivest/tests/unit/test_scheduling_repos.py) — 1🔴 4🟡

**Anti-patterns R1+Y2:** Type check on UoW repos + private state coupling.

#### [MODIFY] [test_backup_manager.py](file:///p:/zorivest/tests/unit/test_backup_manager.py) — 5🟡

**Anti-pattern Y2:** Private state coupling in GFS rotation and security tests.

#### [MODIFY] [test_backup_recovery.py](file:///p:/zorivest/tests/unit/test_backup_recovery.py) — 4🟡

**Anti-pattern Y1:** Weak assertions on verify/legacy operations.

#### [MODIFY] [test_step_registry.py](file:///p:/zorivest/tests/unit/test_step_registry.py) — 2🔴 1🟡

**Anti-patterns R1+R3:** Runtime-checkable type check + no-op compensate test.

#### [MODIFY] [test_fetch_step.py](file:///p:/zorivest/tests/unit/test_fetch_step.py) — 1🔴 2🟡

**Anti-patterns R1+Y1+Y3:** Type check on UoW attribute + weak/status-code assertions.

#### Small files:

| File | Rating | Anti-pattern |
|------|--------|-------------|
| [test_provider_registry.py](file:///p:/zorivest/tests/unit/test_provider_registry.py) | 2🔴 | R1: type checks |
| [test_ibkr_flexquery.py](file:///p:/zorivest/tests/unit/test_ibkr_flexquery.py) | 1🔴 1🟡 | R1+Y2 |
| [test_store_render_step.py](file:///p:/zorivest/tests/unit/test_store_render_step.py) | 2🟡 | Y1: weak |
| [test_market_provider_settings_repo.py](file:///p:/zorivest/tests/unit/test_market_provider_settings_repo.py) | 1🔴 | R3: no-op |
| [test_transform_step.py](file:///p:/zorivest/tests/unit/test_transform_step.py) | 1🟡 | Y1: weak |
| [test_image_processing.py](file:///p:/zorivest/tests/unit/test_image_processing.py) | 1🟡 | Y1: weak |

---

### Batch 5: Integration Tests (9 weak: 2🔴 + 7🟡)

#### [MODIFY] [test_repositories.py](file:///p:/zorivest/tests/integration/test_repositories.py) — 4🟡

**Anti-patterns Y1+Y2:** Weak assertions on repo CRUD round-trips + private state coupling.

#### [MODIFY] [test_unit_of_work.py](file:///p:/zorivest/tests/integration/test_unit_of_work.py) — 1🔴 1🟡

**Anti-patterns R1+Y2:** Type check on repos + private state coupling on session.

#### [MODIFY] [test_database_connection.py](file:///p:/zorivest/tests/integration/test_database_connection.py) — 1🔴 1🟡

**Anti-patterns R1+Y1:** Type check on availability flag + weak fallback assertion.

#### [MODIFY] [test_backup_integration.py](file:///p:/zorivest/tests/integration/test_backup_integration.py) — 1🟡

**Anti-pattern Y2:** Private state coupling.

---

### Batch 6: MCP + UI Tests (13 weak: 0🔴 + 13🟡)

#### [MODIFY] [confirmation.test.ts](file:///p:/zorivest/mcp-server/tests/confirmation.test.ts) — 2🟡

**Anti-pattern Y4:** Mock-only assertions on confirmation guard. Add concrete argument checks.

#### [MODIFY] [CommandPalette.test.tsx](file:///p:/zorivest/ui/src/renderer/src/components/__tests__/CommandPalette.test.tsx) — 3🟡

**Anti-pattern Y4:** Mock-only assertions on palette actions. Verify action arguments and DOM state.

#### [MODIFY] [app.test.tsx](file:///p:/zorivest/ui/src/renderer/src/__tests__/app.test.tsx) — 2🟡

**Anti-pattern Y1+Y4:** Weak structural checks + mock-only on render.

#### Small files:

| File | Rating | Anti-pattern |
|------|--------|-------------|
| [commandRegistry.test.ts](file:///p:/zorivest/ui/src/renderer/src/registry/__tests__/commandRegistry.test.ts) | 2🟡 | Y1+Y4: weak + mock |
| [python-manager.test.ts](file:///p:/zorivest/ui/src/main/__tests__/python-manager.test.ts) | 1🟡 | Y1: weak |
| [discovery-tools.test.ts](file:///p:/zorivest/mcp-server/tests/discovery-tools.test.ts) | 1🟡 | Y4: mock-only |
| [gui-tools.test.ts](file:///p:/zorivest/mcp-server/tests/gui-tools.test.ts) | 1🟡 | Y4: mock-only |
| [metrics.test.ts](file:///p:/zorivest/mcp-server/tests/metrics.test.ts) | 1🟡 | Y1: weak |

---

### Batch 7: Closeout & BUILD_PLAN Maintenance

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Check for stale IR-5 references in BUILD_PLAN | coder | `docs/BUILD_PLAN.md` | `rg -n -e ir5 -e IR-5 -e "weak test" -e "test rigor" docs/BUILD_PLAN.md docs/build-plan/` — update any stale references | `[ ]` |
| 2 | Validate no broken execution-plan links | coder | `docs/BUILD_PLAN.md` | `rg -n "2026-03-16-ir5-test-corrections" docs/BUILD_PLAN.md docs/build-plan/` — all links resolve | `[ ]` |

---

## Upgrade Protocols

Each anti-pattern has a standard fix protocol:

### R1: Type-Guard → Value Assertion

```diff
-assert isinstance(result, ExpectedType)
+assert result == expected_value
+assert result.field == "expected"
```

### R2/Y3: Status-Code → Contract Test

```diff
 assert resp.status_code == 200
+body = resp.json()
+assert body["field"] == expected
+assert "key" in body
```

### R3: No-Op → Idempotency/Postcondition

```diff
 obj.delete_nonexistent()
-# (no assertion)
+assert obj.count() == original_count  # idempotent
```

### Y1: Weak → Strong Assertion

```diff
-assert len(result) > 0
+assert len(result) == 3
+assert result[0].name == "expected"
```

### Y2: Private State → Public Interface

```diff
-assert obj._internal_flag is True
+assert obj.public_method() == expected_output
```

### Y4: Mock-Only → Argument Verification

```diff
-mock.assert_called()
+mock.assert_called_once_with(expected_arg1, key=expected_val)
```

---

## Verification Plan

### Automated Tests

After each batch, run the full regression suite to confirm no tests were broken:

```bash
# Per-batch verification (example: Batch 1)
uv run pytest tests/unit/test_ports.py tests/unit/test_market_data_entities.py tests/unit/test_exceptions.py tests/unit/test_events.py tests/unit/test_commands_dtos.py tests/unit/test_pipeline_enums.py tests/unit/test_scheduling_models.py tests/unit/test_entities.py tests/unit/test_enums.py tests/unit/test_value_objects.py tests/unit/test_pipeline_models.py tests/unit/test_calculator.py tests/unit/test_portfolio_balance.py tests/unit/test_models.py tests/unit/test_display_mode.py -v

# Full Python regression
uv run pytest tests/ --tb=no -q

# MCP tests (Batches 6)
cd mcp-server && npm test

# UI tests (Batch 6)
cd ui && npm test

# Type checking
uv run pyright packages/
```

### IR-5 Re-Audit

After all 6 batches are complete, re-run the IR-5 audit on modified files to verify 0 🔴, 0 🟡 remain:

```powershell
# Re-audit: extract previously-weak tests and verify upgrade
# Step 1: Get list of all previously 🔴/🟡 test functions from the CSV
python -c "
import csv
with open('docs/execution/plans/2026-03-16-test-rigor-audit/phase1-ir5-per-test-ratings.csv', encoding='utf-8-sig') as f:
    for row in csv.reader(f):
        if len(row) >= 6 and ('🔴' in row[5] or '🟡' in row[5]):
            print(f'{row[2]}::{row[1]}  {row[5]}  {row[6] if len(row)>6 else ""}')
"

# Step 2: For each function, verify the test file now contains concrete value assertions
# (manual reviewer inspection using the anti-pattern checklist)

# Step 3: Seed re-audit CSV from original ratings for reviewer to update
# The reviewer manually re-rates each previously-weak test after inspecting Step 2.
# This script creates the CSV scaffold; the reviewer edits the rating column in-place.
python -c "
import csv
src_csv = 'docs/execution/plans/2026-03-16-test-rigor-audit/phase1-ir5-per-test-ratings.csv'
out_csv = 'docs/execution/plans/2026-03-16-ir5-test-corrections/re-audit-results.csv'
with open(src_csv, encoding='utf-8-sig') as f:
    rows = list(csv.reader(f))
hdr, data = rows[0], rows[1:]
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(hdr)
    for r in data:
        w.writerow(r)
print(f'Wrote {len(data)} rows to {out_csv} — reviewer must update rating column for each re-audited test')
"

# Step 4: Verify 0 🔴 and 0 🟡 remain after reviewer updates the CSV
python -c "
import csv
with open('docs/execution/plans/2026-03-16-ir5-test-corrections/re-audit-results.csv', encoding='utf-8-sig') as f:
    weak = [r for r in csv.reader(f) if len(r)>=6 and ('🔴' in r[5] or '🟡' in r[5])]
    print(f'Remaining weak: {len(weak)}')
    assert len(weak) == 0, f'{len(weak)} tests still weak'
"
```

### Success Criteria

- All 285 previously weak tests upgraded to 🟢
- Zero new test failures introduced
- Full regression suite passes
- Type checking passes with no new errors
- `docs/BUILD_PLAN.md` verified for stale references: `rg -n -e ir5 -e IR-5 -e "weak test" -e "test rigor" docs/BUILD_PLAN.md docs/build-plan/`
