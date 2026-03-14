# IBKR & CSV Import Foundation — MEU-96 + MEU-99

> **Project slug:** `ibkr-csv-import-foundation`
> **MEUs:** MEU-96 (`ibkr-adapter`), MEU-99 (`csv-import`)
> **Build-plan sections:** P2.75 — [build-priority-matrix.md](../../build-plan/build-priority-matrix.md) items 50e, 53e
> **Source specs:** [Build Plan Expansion Ideas §1](../../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) (IBroker Interface Pattern), [§18](../../../_inspiration/import_research/Build%20Plan%20Expansion%20Ideas.md) (Broker CSV Import Framework)

---

## Problem Statement

Zorivest currently has no broker import infrastructure. Traders need to ingest historical trade data from their brokerage accounts — either via IBKR's structured FlexQuery XML export or via CSV files from multiple brokers. This project builds the foundational import pipeline: shared domain types, the IBKR FlexQuery XML adapter, and a universal CSV import framework with broker auto-detection and two reference parsers.

---

## Proposed Changes

### Shared Import Foundation (established in MEU-96)

#### [MODIFY] [enums.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py)

Add 3 new StrEnum classes:

- `BrokerType` — registered broker identifiers (`ibkr`, `thinkorswim`, `ninjatrader`, `webull`, `lightspeed`, `etrade`, `tastytrade`, `alpaca`, `tradier`, `schwab`, `generic`)
- `AssetClass` — instrument classification (`EQUITY`, `OPTION`, `FUTURE`, `FOREX`, `CRYPTO`, `BOND`, `MUTUAL_FUND`)
- `ImportStatus` — import job result (`SUCCESS`, `PARTIAL`, `FAILED`)

---

#### [NEW] [import_types.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/import_types.py)

Core Pydantic models for the import pipeline:

- `RawExecution` — canonical ingestion record:
  - `broker: BrokerType`
  - `account_id: str`
  - `exec_time: datetime` (UTC-normalized)
  - `symbol: str` (normalized ticker)
  - `asset_class: AssetClass`
  - `side: TradeAction` (BOT/SLD, reuses existing enum)
  - `quantity: Decimal`
  - `price: Decimal`
  - `commission: Decimal = Decimal("0")`
  - `fees: Decimal = Decimal("0")` (non-commission fees)
  - `currency: str = "USD"` (ISO 4217 — original trade currency)
  - `base_currency: str = "USD"` (account base currency)
  - `base_amount: Decimal | None = None` (price × qty in base currency, populated when broker provides FX rate)
  - `contract_multiplier: Decimal = Decimal("1")`
  - `order_id: str | None = None` (broker's order reference)
  - `raw_data: dict[str, str] = {}` (preserved original fields for audit)

- `ImportError` — per-row error:
  - `row_number: int | None`
  - `field: str`
  - `message: str`
  - `raw_line: str = ""`

- `ImportResult` — aggregated result:
  - `status: ImportStatus`
  - `broker: BrokerType`
  - `executions: list[RawExecution]`
  - `errors: list[ImportError]`
  - `total_rows: int`
  - `parsed_rows: int`
  - `skipped_rows: int`

---

#### [MODIFY] [ports.py](file:///p:/zorivest/packages/core/src/zorivest_core/application/ports.py)

Extend the existing `ports.py` (which already contains `BrokerPort`, `BankImportPort`, `IdentifierResolverPort` at L254-289) with two new import-specific Protocols:

- `BrokerFileAdapter` Protocol (added after `IdentifierResolverPort`):
  - `broker_type: BrokerType` (property)
  - `parse_file(file_path: Path) -> ImportResult`

- `CSVBrokerAdapter(BrokerFileAdapter)` Protocol (extends for CSV-specific):
  - `detect(headers: list[str]) -> bool`
  - `parse_rows(rows: list[dict[str, str]]) -> list[RawExecution]`

> **Architecture note:** These extend the existing broker abstractions rather than creating a parallel file. The existing `BrokerPort` handles live API operations; `BrokerFileAdapter` handles file-based imports. Both coexist in `ports.py`.

---

### MEU-96: IBKR FlexQuery Adapter

#### [NEW] [ibkr_flexquery.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/broker_adapters/ibkr_flexquery.py)

IBKR FlexQuery XML parser:

- `IBKRFlexQueryAdapter` class implementing `BrokerFileAdapter`:
  - `broker_type = BrokerType.IBKR`
  - `parse_file(file_path: Path) -> ImportResult` — parses FlexQuery Activity XML
  - `_parse_trade_element(elem: Element) -> RawExecution` — maps XML trade node
  - `_normalize_symbol(raw: str, asset_class: str) -> str` — IBKR symbology → OCC standard
  - `_parse_ibkr_datetime(value: str) -> datetime` — IBKR's `YYYYMMDD;HHMMSS` format
  - `_classify_asset_class(code: str) -> AssetClass` — IBKR asset category codes

Uses `defusedxml.ElementTree` for secure XML parsing (mitigates XXE attacks).

Key FlexQuery XML structure handled:
```xml
<FlexQueryResponse>
  <FlexStatements>
    <FlexStatement>
      <Trades>
        <Trade accountId="..." symbol="..." dateTime="..." 
               quantity="..." tradePrice="..." ibCommission="..."
               assetCategory="STK" .../>
      </Trades>
    </FlexStatement>
  </FlexStatements>
</FlexQueryResponse>
```

---

#### [NEW] [test_ibkr_flexquery.py](file:///p:/zorivest/tests/unit/test_ibkr_flexquery.py)

~25 tests:
- FlexQuery XML parsing (valid stock, option, future trades)
- Symbol normalization (options → OCC format)
- DateTime parsing (IBKR format)
- Asset class classification (STK, OPT, FUT, CASH)
- Fee/commission extraction
- Multi-currency trade handling
- Error handling: malformed XML, missing required fields, empty trades section
- ImportResult correctness (status, counts, error list)
- Security: XXE attack prevention (defusedxml)

---

### MEU-99: CSV Import + Broker Auto-Detection

#### [NEW] [csv_base.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/broker_adapters/csv_base.py)

CSV parser framework:

- `CSVParserBase` ABC implementing `CSVBrokerAdapter`:
  - `detect(headers: list[str]) -> bool` — abstract, per-broker header fingerprint
  - `parse_rows(rows: list[dict[str, str]]) -> list[RawExecution]` — abstract
  - `parse_file(file_path: Path) -> ImportResult` — concrete: detect encoding → read CSV → call parse_rows → aggregate result
  - `_detect_encoding(file_path: Path) -> str` — chardet-based encoding detection
  - `_strip_bom(content: str) -> str` — UTF-8 BOM removal

---

#### [NEW] [tos_csv.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/broker_adapters/tos_csv.py)

ThinkorSwim CSV parser (P1 reference):

- `ThinkorSwimCSVParser(CSVParserBase)`:
  - Header fingerprint: `["Exec Time", "Spread", "Side", "Qty"]`
  - Multi-section CSV handling (detect "Trade History" section header)
  - Options symbol parsing (TOS `.AAPL260116C225` format → OCC standard)
  - Commission calculation: `(Price - Net Price) × Qty`

---

#### [NEW] [ninjatrader_csv.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/broker_adapters/ninjatrader_csv.py)

NinjaTrader CSV parser (P1 reference):

- `NinjaTraderCSVParser(CSVParserBase)`:
  - Header fingerprint: `["Trade-#", "Instrument", "Account", "Strategy"]`
  - Pre-paired round-trip format (entry+exit already matched)
  - Built-in MFE/MAE preservation (stored in `raw_data` for future enrichment)
  - Strategy tag extraction from `Strategy` column

---

#### [NEW] [import_service.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/import_service.py)

> **Layer note:** `ImportService` stays in `core/services/` because it orchestrates domain logic (adapter selection, result aggregation). The concrete file-parsing adapters live in `infrastructure/src/zorivest_infra/broker_adapters/` since they perform I/O.

Import orchestrator:

- `ImportService`:
  - `__init__(adapters: list[BrokerFileAdapter])` — registry of available adapters
  - `import_file(file_path: Path, broker_hint: BrokerType | None = None) -> ImportResult`
    - If `broker_hint` provided → use matching adapter directly
    - If None and file is CSV → auto-detect via header fingerprints
    - If None and file is XML → try IBKR FlexQuery
    - Route to appropriate adapter's `parse_file()`
  - `auto_detect_csv_broker(file_path: Path) -> BrokerType`
    - Read first 10 lines for header detection
    - Try each registered CSVParser's `detect()` method
    - Raise `UnknownBrokerFormat` if no match

- `UnknownBrokerFormat(Exception)` — raised when auto-detection fails

---

#### [NEW] [test_csv_import.py](file:///p:/zorivest/tests/unit/test_csv_import.py)

~30 tests:
- CSVParserBase encoding detection (UTF-8, Latin-1, BOM handling)
- TOS parser: header detection, trade parsing, multi-section CSV, options symbol conversion
- NinjaTrader parser: header detection, pre-paired format, strategy tag, MFE/MAE preservation
- ImportService: auto-detection routing, broker_hint override, XML routing, unknown format error
- Edge cases: empty CSV, CSV with only headers, mixed encoding, extra columns

---

#### [MODIFY] [conftest.py](file:///p:/zorivest/tests/conftest.py)

Extend the existing `tests/conftest.py` (currently 60 bytes) with shared import test fixtures:
- Sample FlexQuery XML string (3 stock trades, 1 option trade)
- Sample TOS CSV content (multi-section, stock + option trades)
- Sample NinjaTrader CSV content (paired round-trip format)
- `tmp_path` fixtures that write sample data to temp files

---

### BUILD_PLAN.md Maintenance

#### [MODIFY] [BUILD_PLAN.md](file:///p:/zorivest/docs/BUILD_PLAN.md)

- Update MEU-96 and MEU-99 status from ⬜ to ✅
- Update MEU Summary table: P2.75 Completed from `0` to `2`

> Validation: After update, verify no stale references remain by checking that the total count (170) is unchanged and completed sum increases by 2 (58 → 60).

---

## Spec Sufficiency

### MEU-96: IBKR FlexQuery Adapter

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| FlexQuery XML schema (Activity Flex report) | Research-backed | [IBKR FlexQuery docs](https://www.interactivebrokers.com/en/software/reportguide/reportguide.htm) | ✅ |
| RawExecution output contract | Spec | §1 IBroker interface → `List[RawExecution]`, §2 UnifiedTradeSchema | ✅ |
| Symbol normalization (options → OCC) | Spec | §1 challenges table, §18 cross-cutting | ✅ |
| Fee decomposition (ibCommission, ibOrderRef) | Research-backed | IBKR FlexQuery XML field reference | ✅ |
| Multi-currency (store original + base) | Spec + Research-backed | §2 challenges (27 currencies) defines contract; IBKR `fxRateToBase` field per [FlexQuery XML reference](https://www.interactivebrokers.com/en/software/reportguide/reportguide.htm) provides implementation mechanism | ✅ |
| Secure XML parsing (XXE prevention) | Research-backed | [OWASP XXE Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html) | ✅ |

### MEU-99: CSV Import + Broker Auto-Detection

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| CSVParser ABC (detect + parse) | Spec | §18 Universal Parser Architecture | ✅ |
| Auto-detection via header fingerprints | Spec | §18 `auto_detect_broker` function | ✅ |
| TOS parser (multi-section, options) | Spec | §18 Supported Brokers table (TOS row) | ✅ |
| NinjaTrader parser (pre-paired) | Spec | §18 Supported Brokers table (NT row) | ✅ |
| Encoding handling (chardet, BOM) | Spec | §18 cross-cutting challenges | ✅ |
| ImportService orchestration | Spec | §1 BrokerFactory pattern, §18 auto-detect | ✅ |

---

## Feature Intent Contracts

### FIC-96: IBKR FlexQuery Adapter

| AC | Description | Source |
|---|---|---|
| AC-1 | `IBKRFlexQueryAdapter.parse_file()` returns `ImportResult` with extracted `RawExecution` list from valid FlexQuery XML | Spec |
| AC-2 | Each `RawExecution` has `broker=BrokerType.IBKR`, UTC-normalized `exec_time`, and `Decimal` price/quantity/commission | Spec |
| AC-3 | Options symbols normalize from IBKR format to OCC standard (`SYMBOL YYMMDD C/P STRIKE`) | Spec |
| AC-4 | Asset class correctly classified from IBKR `assetCategory` codes (`STK`→`EQUITY`, `OPT`→`OPTION`, `FUT`→`FUTURE`, `CASH`→`FOREX`) | Spec |
| AC-5 | Malformed/missing XML fields produce `ImportError` entries in result (not exceptions); `status=ImportStatus.PARTIAL` when some rows error | Research-backed (ETL partial-success pattern: [pandas `on_bad_lines`](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html), [Spark CSV `PERMISSIVE` mode](https://spark.apache.org/docs/latest/sql-data-sources-csv.html); documented in [ADR-0003](../../../docs/decisions/ADR-0003-batch-import-error-isolation.md)) |
| AC-6 | XML parsing uses `defusedxml` to prevent XXE attacks | Research-backed (OWASP XXE Prevention) |
| AC-7 | Multi-currency trades populate `currency` (original) per §2 spec; `base_currency` and `base_amount` populated via IBKR `fxRateToBase` | Spec (§2 challenges: store original + base) + Research-backed (IBKR FlexQuery `fxRateToBase` field) |
| AC-8 | `raw_data` dict preserves original XML attributes for audit trail | Spec |

### FIC-99: CSV Import + Broker Auto-Detection

| AC | Description | Source |
|---|---|---|
| AC-1 | `CSVParserBase` provides concrete `parse_file()` that handles encoding detection and delegates to subclass `parse_rows()` | Spec |
| AC-2 | `ThinkorSwimCSVParser.detect()` returns `True` for TOS header fingerprint, `False` for others | Spec |
| AC-3 | TOS parser extracts trades from multi-section CSV by detecting "Trade History" section header | Spec |
| AC-4 | TOS options symbols (`.AAPL260116C225`) normalize to OCC standard | Spec |
| AC-5 | `NinjaTraderCSVParser` handles pre-paired round-trip format with entry/exit in same row | Spec |
| AC-6 | NinjaTrader parser preserves MFE/MAE values in `raw_data` dict | Spec |
| AC-7 | `ImportService.auto_detect_csv_broker()` correctly identifies TOS and NT from CSV headers | Spec |
| AC-8 | `ImportService.import_file()` with `broker_hint` bypasses auto-detection | Spec |
| AC-9 | Unknown CSV format raises `UnknownBrokerFormat` with headers in error message | Spec |
| AC-10 | BOM-encoded and Latin-1 encoded CSVs parse correctly | Spec |

---

## Task Table

| # | Task | Owner | Deliverable | Validation | Status |
|---|---|---|---|---|---|
| 1 | Add `BrokerType`, `AssetClass`, `ImportStatus` enums | coder | Modified `enums.py` | Pyright clean, enum membership tests | ⬜ |
| 2 | Create `RawExecution`, `ImportError`, `ImportResult` Pydantic models | coder | New `import_types.py` | Pyright clean, model validation tests | ⬜ |
| 3 | Add `BrokerFileAdapter`, `CSVBrokerAdapter` Protocols to existing `ports.py` | coder | Modified `ports.py` | Pyright clean, protocol structural tests | ⬜ |
| 4 | Write MEU-96 tests (Red phase) | tester | New `test_ibkr_flexquery.py` + fixtures in `conftest.py` | ~25 tests, all FAIL (Red) | ⬜ |
| 5 | Implement `IBKRFlexQueryAdapter` (Green phase) | coder | New `ibkr_flexquery.py` | All AC-1 through AC-8 tests pass | ⬜ |
| 6 | Create MEU-96 handoff | coder | `061-2026-03-13-ibkr-adapter-bpMs50e.md` | Template completeness | ⬜ |
| 7 | Write MEU-99 tests (Red phase) | tester | New `test_csv_import.py` + fixtures in `conftest.py` | ~30 tests, all FAIL (Red) | ⬜ |
| 8 | Implement `CSVParserBase` ABC (Green phase) | coder | New `csv_base.py` | AC-1, AC-10 tests pass | ⬜ |
| 9 | Implement `ThinkorSwimCSVParser` (Green phase) | coder | New `tos_csv.py` | AC-2, AC-3, AC-4 tests pass | ⬜ |
| 10 | Implement `NinjaTraderCSVParser` (Green phase) | coder | New `ninjatrader_csv.py` | AC-5, AC-6 tests pass | ⬜ |
| 11 | Implement `ImportService` (Green phase) | coder | New `import_service.py` | AC-7, AC-8, AC-9 tests pass | ⬜ |
| 12 | Create MEU-99 handoff | coder | `062-2026-03-13-csv-import-bpMs53e.md` | Template completeness | ⬜ |
| 13 | Update `BUILD_PLAN.md` MEU status + summary counts | coder | Modified `BUILD_PLAN.md` | Total 170 unchanged, completed 58→60 | ⬜ |
| 14 | Update `meu-registry.md` | coder | Modified `meu-registry.md` | MEU-96, MEU-99 rows added | ⬜ |
| 15 | Run MEU gate | tester | Gate pass evidence | `uv run python tools/validate_codebase.py --scope meu` | ⬜ |
| 16 | Create reflection file | reviewer | `docs/execution/reflections/2026-03-13-ibkr-csv-import-reflection.md` | All sections populated | ⬜ |
| 17 | Update metrics table | coder | Modified `docs/execution/metrics.md` | New row added | ⬜ |
| 18 | Save session to pomera_notes | coder | Pomera note ID | Note saved successfully | ⬜ |
| 19 | Prepare commit messages | coder | Proposed messages | Semantic, atomic | ⬜ |

---

## Verification Plan

### Automated Tests

All tests run via:

```bash
# MEU-96 tests
uv run pytest tests/unit/test_ibkr_flexquery.py -v

# MEU-99 tests  
uv run pytest tests/unit/test_csv_import.py -v

# Full regression
uv run pytest tests/ -v

# Type checking (scoped to touched files)
uv run pyright packages/core/src/zorivest_core/domain/enums.py packages/core/src/zorivest_core/domain/import_types.py packages/core/src/zorivest_core/application/ports.py packages/infrastructure/src/zorivest_infra/broker_adapters/ packages/core/src/zorivest_core/services/import_service.py

# Lint check
uv run ruff check packages/core/src/zorivest_core/domain/ packages/core/src/zorivest_core/services/ packages/core/src/zorivest_core/application/ packages/infrastructure/src/zorivest_infra/broker_adapters/

# Anti-placeholder scan
rg "TODO|FIXME|NotImplementedError" packages/infrastructure/src/zorivest_infra/broker_adapters/ packages/core/src/zorivest_core/services/import_service.py packages/core/src/zorivest_core/domain/import_types.py

# MEU gate
uv run python tools/validate_codebase.py --scope meu
```

### Test Coverage Summary

| Test File | Tests | Covers |
|---|---|---|
| `test_ibkr_flexquery.py` | ~25 | FIC-96 AC-1 through AC-8 |
| `test_csv_import.py` | ~30 | FIC-99 AC-1 through AC-10 |
| Existing tests (regression) | ~200+ | No regressions from new enums/types |

---

## Dependencies

New Python packages required (add to `packages/infrastructure/pyproject.toml`):

| Package | Version | Purpose |
|---|---|---|
| `defusedxml` | `>=0.7.1` | XXE-safe XML parsing for FlexQuery |
| `chardet` | `>=5.0.0` | CSV encoding auto-detection |

---

## Handoff Files

| MEU | Handoff Path |
|---|---|
| MEU-96 | `.agent/context/handoffs/061-2026-03-13-ibkr-adapter-bpMs50e.md` |
| MEU-99 | `.agent/context/handoffs/062-2026-03-13-csv-import-bpMs53e.md` |
