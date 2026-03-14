# ADR-0003: Batch Import Error Isolation — Graceful Degradation over Fail-Fast

> Status: proposed
> Date: 2026-03-13
> Deciders: Kael (agent) — pending human ratification via plan approval

## Context

The broker import pipeline (MEU-96, MEU-99) ingests trade data from FlexQuery XML and CSV files that may contain hundreds or thousands of rows. Real-world broker exports frequently contain malformed rows — partial fills with missing fields, encoding artifacts, or broker-specific edge cases that don't map cleanly to the canonical `RawExecution` schema.

Graceful degradation in batch data processing is a well-established industry pattern. ETL frameworks (Apache Spark, pandas, dbt), data pipeline tools (Airflow, Prefect), and broker import tools (TradeTally, Portfolio Performance) universally adopt partial-success semantics — parsing what can be parsed and reporting structured errors for what cannot — rather than aborting the entire batch on the first malformed row.

The design question: when the parser encounters a malformed row, should it:
- **Fail-fast**: raise an exception, aborting the entire import
- **Graceful degradation**: record the error and continue parsing remaining rows

## Decision

Adopt **graceful degradation** for batch import operations:

1. Malformed/missing fields produce `ImportError` entries in the `ImportResult.errors` list — they do not raise exceptions
2. When some rows error but others parse successfully, the result `status` is set to `ImportStatus.PARTIAL`
3. Each `ImportError` captures `row_number`, `field`, `message`, and `raw_line` for debugging
4. The caller receives a complete `ImportResult` with both successful `executions` and structured `errors`, enabling informed decisions about the import quality

## Consequences

### Positive
- Users don't lose an entire 500-trade import because of 3 malformed rows
- Error details are structured and auditable, not buried in exception traces
- `ImportResult.status` gives callers a clear signal: `SUCCESS` (all rows), `PARTIAL` (some errors), `FAILED` (no rows parsed)

### Negative
- Callers must check `errors` list and `status` field — silent partial imports are possible if callers ignore these
- More complex parser implementation vs. a simple `raise` on first error

### Risks
- A systematically malformed file (wrong broker format) could produce a `PARTIAL` result with mostly errors — callers should treat high error ratios as effective failures

## References

- Build plan section: P2.75 Broker Adapters & Import (MEU-96, MEU-99)
- Implementation plan: `docs/execution/plans/2026-03-13-ibkr-csv-import-foundation/implementation-plan.md` FIC-96 AC-5
- Handoff: `.agent/context/handoffs/2026-03-13-ibkr-csv-import-foundation-plan-critical-review.md`
- Primary sources:
  - [pandas `read_csv` — `on_bad_lines` parameter](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) (skip/warn on malformed rows instead of failing)
  - [Spark CSV data source — `PERMISSIVE` mode](https://spark.apache.org/docs/latest/sql-data-sources-csv.html) (collect corrupt records in `_corrupt_record` column)
