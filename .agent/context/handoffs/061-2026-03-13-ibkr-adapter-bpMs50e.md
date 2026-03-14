# MEU-96: IBKR FlexQuery Adapter

## Task

- **Date:** 2026-03-13
- **Task slug:** ibkr-adapter
- **Build plan ref:** P2.75 item 50e
- **Scope:** IBKR FlexQuery XML parser + shared import domain types

## Inputs

- **User request:** Build IBKR FlexQuery import adapter as part of broker import foundation
- **Specs referenced:** [Build Plan Expansion Ideas §1](../../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) (IBroker Interface), [implementation plan](../../docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/implementation-plan.md) FIC-96
- **ADRs:** [ADR-0003](../../docs/decisions/ADR-0003-batch-import-error-isolation.md) (graceful degradation)
- **Dependencies installed:** `defusedxml`, `chardet` → `packages/infrastructure/pyproject.toml`

## Role Plan

1. orchestrator
2. coder
3. tester
4. reviewer (Codex)

## Coder Output

### Changed Files

| File | Action | Description |
|---|---|---|
| `packages/core/src/zorivest_core/domain/enums.py` | MODIFY | Added `BrokerType` (11 brokers), `AssetClass` (7 classes), `ImportStatus` (3 states) |
| `packages/core/src/zorivest_core/domain/import_types.py` | NEW | `RawExecution`, `ImportError`, `ImportResult` Pydantic models |
| `packages/core/src/zorivest_core/application/ports.py` | MODIFY | Added `BrokerFileAdapter`, `CSVBrokerAdapter` Protocols + `Path`/`BrokerType`/`ImportResult` imports |
| `packages/infrastructure/src/zorivest_infra/broker_adapters/__init__.py` | NEW | Package init |
| `packages/infrastructure/src/zorivest_infra/broker_adapters/ibkr_flexquery.py` | NEW | `IBKRFlexQueryAdapter` — FlexQuery XML parser |
| `tests/conftest.py` | MODIFY | Added 10 fixtures (FlexQuery XML variants, CSV samples, XXE attack) |
| `tests/unit/test_ibkr_flexquery.py` | NEW | 33 tests across 8 test classes |
| `tests/unit/test_ports.py` | MODIFY | Updated expected protocol count 16→18, added `pathlib` to allowed imports |

### Design Decisions

- IBKR commission stored as positive (IBKR reports negative via `ibCommission`)
- `base_amount = price × abs(quantity) × fxRateToBase` quantized to 2 decimal places
- Option symbol normalization: IBKR `"AAPL  260320C00200000"` → OCC `"AAPL 260320 C 200"` (strike ÷ 1000)
- `defusedxml.ElementTree` used for all XML parsing (mitigates XXE — OWASP AC-6)
- `getroot()` None guard added for pyright compliance

## Tester Output

### Commands Run

```
uv run pytest tests/unit/test_ibkr_flexquery.py -v            # 34 passed
uv run pytest tests/ --tb=no -q                                # 1232 passed, 1 skipped
uv run pyright packages/core/.../enums.py .../import_types.py .../ports.py .../broker_adapters/   # 0 errors
uv run ruff check <all touched files>                          # 0 remaining (10 auto-fixed)
rg "TODO|FIXME|NotImplementedError" packages/.../broker_adapters/   # 0 matches
```

### Pass/Fail Matrix

| AC | Description | Tests | Status |
|---|---|---|---|
| AC-1 | `parse_file()` returns `ImportResult` | `TestParseFileBasic` (4 tests) | ✅ |
| AC-2 | `RawExecution` fields (broker, UTC, Decimal) | `TestRawExecutionFields` (8 tests) | ✅ |
| AC-3 | Options → OCC symbol normalization | `TestSymbolNormalization` (3 tests) | ✅ |
| AC-4 | Asset class classification (STK/OPT/FUT/CASH) | `TestAssetClassification` (4 tests) | ✅ |
| AC-5 | Graceful degradation (ADR-0003) | `TestErrorHandling` (5 tests) | ✅ |
| AC-6 | XXE prevention (defusedxml) | `TestXXEPrevention` (1 test) | ✅ |
| AC-7 | Multi-currency (fxRateToBase) | `TestMultiCurrency` (4 tests) | ✅ |
| AC-8 | `raw_data` audit trail | `TestRawDataPreservation` (2 tests) + `TestAdapterProtocol` (3 tests) | ✅ |

### Regression

- **Before:** 1166 passed, 1 skipped (baseline from prior session)
- **After:** 1232 passed, 1 skipped (+66 new tests, 0 regressions)

- Evidence bundle location: This handoff
- FAIL_TO_PASS / PASS_TO_PASS result: 34 FAIL_TO_PASS (Red → Green), 1198 PASS_TO_PASS
- Mutation score: Not run
- Contract verification status: Codex review pending

## Reviewer Output

- Findings by severity: Pending Codex review
- Open questions: None
- Verdict: `pending`
- Residual risk: None identified
- Anti-deferral scan result: 0 TODOs/FIXMEs

## Approval Gate

- **Human approval required for merge/release/deploy:** yes
- **Approval status:** pending
- **Approver:**
- **Timestamp:**

## Final Summary

- **Status:** Implementation complete, ready for Codex validation
- **Test evidence:** 34/34 MEU-96 tests pass, 1232/1232 full regression
- **Quality gates:** pyright 0 errors, ruff 0 issues, 0 TODOs
- **Next steps:** Codex validation → handoff approval → post-MEU deliverables
