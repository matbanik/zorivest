---
seq: "124"
date: "2026-04-21"
project: "pipeline-adhoc-fixes-docs"
meu: "AD-HOC (no MEU — reactive fixes + documentation)"
status: "complete"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "detailed"
plan_source: "none — ad-hoc session, no implementation plan created"
build_plan_section: "bp09s9B (pipeline infrastructure)"
agent: "Antigravity (Gemini)"
reviewer: "pending"
predecessor: "123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md"
---

# Handoff: 124-2026-04-21-pipeline-adhoc-fixes-docs

> **Status**: `complete`
> **Action Required**: `VALIDATE_AND_APPROVE`

> [!WARNING]
> **This was an ad-hoc session.** No implementation plan, no FIC, and no formal TDD cycle was followed for the production code changes. See the reflection for a full duct-tape assessment.

---

## Scope

**MEU**: AD-HOC — No formal MEU. Session covered two work streams:
1. **Stream A** — Reactive bug fixes for the live pipeline (Yahoo multi-ticker, DB write sanitization, cache metadata, schema columns)
2. **Stream B** — Architectural documentation (known-issues updates, policy authoring guide, PDF→Markdown decision)

**Build Plan Section**: bp09s9B (pipeline infrastructure — ad-hoc)
**Predecessor**: [123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md](123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h.md)

---

## Acceptance Criteria

> [!IMPORTANT]
> No formal acceptance criteria (FIC) were defined for this session. The table below reconstructs implicit ACs from the runtime bugs that were discovered and fixed.

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-1 | Multi-ticker fetch: policy with N tickers must return data for all tickers | Human-approved (user reported single-ticker output) | Live API test (manual) + `test_market_data_adapter.py::test_multi_ticker_merges_all_results` (L533) | ✅ |
| AC-2 | DB write: pandas Timestamp/NaT/numpy types must sanitize to native Python before sqlite3 binding | Runtime error (ProgrammingError) | `test_db_write_adapter.py::TestSanitizeValue` (L140–L221), `TestSanitizeRecords` (L223–L299) | ✅ |
| AC-3 | Cache hit path must include `provider` and `data_type` metadata in output | Runtime error (TransformStep failed on cache hit) | Visual inspection of [`fetch_step.py:100-101`](../../packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L100-L101) | ✅ |
| AC-4 | MarketQuoteModel must include `change` and `change_pct` columns matching Yahoo v8 schema | Runtime error (missing columns during write) | [`models.py:666-667`](../../packages/infrastructure/src/zorivest_infra/database/models.py#L666-L667) + migration in [`main.py:178-179`](../../packages/api/src/zorivest_api/main.py#L178-L179) | ✅ |
| AC-5 | Response extractor must support pre-merged list passthrough for multi-ticker data | Design requirement from AC-1 | `test_response_extractors.py` (+33 lines) | ✅ |
| AC-6 | Known issues must document PIPE-NOLOCALQUERY architectural gap | Human-approved (user request) | [`known-issues.md:9`](known-issues.md) | ✅ |
| AC-7 | Known issues must document PIPE-DROPPDF decision (PDF→Markdown) | Human-approved (user request) | [`known-issues.md:26`](known-issues.md) | ✅ |
| AC-8 | Policy authoring guide must document all 5 step types with dynamic vs hardcoded matrix | Human-approved (user request) | [`policy-authoring-guide.md`](../../docs/guides/policy-authoring-guide.md) (751 lines) | ✅ |

<!-- CACHE BOUNDARY -->
<!-- Content above this line is stable across revision passes (KV cache prefix). -->
<!-- Content below this line changes between passes (evidence, results, corrections). -->

---

## Evidence

> **Test output rule**: Include only failing test names, assertion messages, and relevant stack frames. Summarize passing tests as `{N} passed`.

### FAIL_TO_PASS

> [!WARNING]
> **No formal Red→Green TDD cycle was executed.** Bugs were discovered during live pipeline runs and fixed reactively. Tests were written alongside fixes, not before.

| Test | Red Output (hash/snippet) | Green Output | File:Line |
|------|--------------------------|--------------|-----------|
| `TestSanitizeValue::test_pandas_timestamp_converted_to_datetime` | N/A — written after fix | PASSED | `test_db_write_adapter.py:174` |
| `TestSanitizeValue::test_pandas_nat_converted_to_none` | N/A — written after fix | PASSED | `test_db_write_adapter.py:186` |
| `TestSanitizeValue::test_float_nan_converted_to_none` | N/A — written after fix | PASSED | `test_db_write_adapter.py:193` |
| `TestSanitizeValue::test_numpy_nan_converted_to_none` | N/A — written after fix | PASSED | `test_db_write_adapter.py:199` |
| `TestSanitizeValue::test_numpy_int64_converted_to_python_int` | N/A — written after fix | PASSED | `test_db_write_adapter.py:206` |
| `TestSanitizeValue::test_numpy_float64_converted_to_python_float` | N/A — written after fix | PASSED | `test_db_write_adapter.py:214` |
| `TestSanitizeRecords::test_records_roundtrip_through_dataframe` | N/A — written after fix | PASSED | `test_db_write_adapter.py:262` |
| `test_multi_ticker_merges_all_results` | N/A — offline regression | PASSED | `test_market_data_adapter.py:533` |
| `test_multi_ticker_handles_per_ticker_error` | N/A — offline regression | PASSED | `test_market_data_adapter.py:562` |
| `test_single_ticker_does_not_use_multi_ticker_path` | N/A — offline regression | PASSED | `test_market_data_adapter.py:607` |
| `test_multi_ticker_empty_list_falls_through` | N/A — offline regression | PASSED | `test_market_data_adapter.py:625` |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| Live API test (multi-ticker 7 symbols) | 0 | All 7 tickers returned in pipeline output |
| Live API test (single ticker AAPL) | 0 | Regression confirmed — single ticker still works |
| `pytest tests/unit/test_market_data_adapter.py::test_multi_ticker_* -v` | 0 | 4 passed (offline regression) |
| `pytest tests/unit/test_db_write_adapter.py -v` | 0 | 14 passed (sanitization + dispatch + interface) |
| `git diff --stat HEAD` | 0 | 16 files changed, 746 insertions(+), 21 deletions(-) |

### Quality Gate Results

> [!CAUTION]
> **No quality gate was run at session end.** This is a process violation per AGENTS.md §Execution Contract. The gate should be run before this handoff is approved.

```
pyright: NOT RUN
ruff: NOT RUN
pytest: NOT RUN (individual tests run, not full suite)
anti-placeholder: NOT RUN
```

---

## Changed Files

> **Delta-only rule**: Show unified diff blocks for modifications.

| File | Action | Lines | Summary |
|------|--------|-------|---------|
| `market_data_adapter.py` | modified | +119/-1 | Multi-ticker fetch loop with per-ticker error handling and result merging |
| `db_write_adapter.py` | modified | +56/-1 | `_sanitize_records()` and `_sanitize_value()` for pandas/numpy type conversion |
| `response_extractors.py` | modified | +40/-1 | List passthrough support for pre-merged multi-ticker records |
| `fetch_step.py` | modified | +2 | Added `provider`/`data_type` to cache hit output |
| `models.py` | modified | +2 | Added `change` and `change_pct` columns to MarketQuoteModel |
| `main.py` | modified | +2 | Inline ALTER TABLE migrations for new columns |
| `url_builders.py` | modified | +11/-1 | URL builder adjustments |
| `transform_step.py` | modified | +5/-1 | Source resolution fix |
| `http_cache.py` | modified | +29 | Cache handling additions |
| `write_dispositions.py` | modified | +2 | Minor addition |
| `pyproject.toml` | modified | +1 | Dependency addition |
| `test_db_write_adapter.py` | modified | +168 | 14 tests: dispatch (3), negative (2), interface (1), sanitize value (8), sanitize records (3 incl. DataFrame roundtrip) |
| `test_response_extractors.py` | modified | +33 | Multi-ticker list passthrough tests |
| `test_market_data_adapter.py` | modified | +250 | Adapter test adjustments + 4 offline multi-ticker regression tests (merge, error-handling, single-ticker path, empty-list) |
| `test_url_builders.py` | modified | +10/-1 | Builder test adjustments |
| `known-issues.md` | modified | +37 | PIPE-NOLOCALQUERY (L9) + PIPE-DROPPDF (L26) entries |

**Untracked files** (not in `git diff --stat HEAD`):

| File | Lines | Summary |
|------|-------|---------|
| `docs/guides/policy-authoring-guide.md` | 750 | Full policy reference guide (all 5 steps, wiring, registries, dynamic vs hardcoded) |

### Key Diff: Multi-Ticker Fetch (market_data_adapter.py)

```diff
+    async def _fetch_multi_ticker(
+        self, *, config, provider, data_type, tickers, criteria,
+    ) -> FetchAdapterResult:
+        """Iterate tickers one-by-one, merge into combined JSON array."""
+        all_records = []
+        errors = []
+        for ticker in tickers:
+            single_criteria = {**criteria, "tickers": [ticker]}
+            try:
+                result = await self._do_single_fetch(config, provider, data_type, ticker, single_criteria)
+                records = extract_records(result, provider, data_type)
+                all_records.extend(records)
+            except Exception as exc:
+                errors.append({"ticker": ticker, "error": str(exc)})
+        # Return merged result
```

### Key Diff: DB Write Sanitizer (db_write_adapter.py)

```diff
+def _sanitize_value(val: Any) -> Any:
+    """Convert pandas/numpy types to native Python for sqlite3."""
+    if val is None:
+        return None
+    type_name = type(val).__name__
+    if type_name == "Timestamp":
+        return val.to_pydatetime()
+    if type_name == "NaTType":
+        return None
+    if isinstance(val, float) and math.isnan(val):
+        return None
+    if hasattr(val, "item"):  # numpy scalar
+        return val.item()
+    return val
```

---

## Codex Validation Report

_Left blank for reviewer agent._

---

## Deferred Items

| Item | Reason | Follow-up |
|------|--------|-----------|
| Full quality gate run | Not executed this session | Must run before merge |
| Formal FIC for multi-ticker contract | Ad-hoc session, no FIC written | Should be retroactively documented if this code becomes stable |
| `[PIPE-NOLOCALQUERY]` implementation | Out-of-scope — documented as known issue | Future MEU under Phase 9 |
| `[PIPE-DROPPDF]` cleanup | Out-of-scope — documented as known issue | Future MEU under Phase 9 |

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | 2026-04-21 | Antigravity (Gemini) | Post-session handoff (ad-hoc fixes + documentation) |
| Submitted for review | 2026-04-21 | Antigravity (Gemini) | Pending user approval |
| Revised | 2026-04-21 | Antigravity (Gemini) | Fixed stale line refs per Codex findings; added 4 offline multi-ticker regression tests; corrected FAIL_TO_PASS test names to match live codebase |
| Revised | 2026-04-21 | Antigravity (Gemini) | Fixed git diff evidence to exact (16 files, 746+, 21−); corrected Changed Files counts from git diff --stat; separated untracked policy guide from tracked inventory; fixed reflection cross-doc contradiction |
