---
seq: "123"
date: "2026-04-21"
project: "pipeline-dataflow-hardening"
meu: "MEU-PW12, MEU-PW13"
status: "draft"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-04-21-pipeline-dataflow-hardening/implementation-plan.md"
build_plan_section: "bp09s49.4h-49.5h"
agent: "Antigravity (Gemini)"
reviewer: "GPT-5.4 Codex"
predecessor: "122-2026-04-20-pipeline-template-cursor-bp09s9B.7-9.md"
---

# Handoff: 123-2026-04-21-pipeline-dataflow-hardening-bp09s49.4h-49.5h

> **Status**: `draft`
> **Action Required**: `VALIDATE_AND_APPROVE`

---

## Scope

**MEU**: MEU-PW12 — Pipeline data-flow chain fix (response extractors, field mappings, step param boundary validation)
**MEU**: MEU-PW13 — Pipeline E2E integration tests (Fetch→Transform→Send chain verification)
**Build Plan Section**: P2.5 items 49.4h–49.5h (hardening of items 44–47)
**Predecessor**: [122-2026-04-20-pipeline-template-cursor-bp09s9B.7-9.md](122-2026-04-20-pipeline-template-cursor-bp09s9B.7-9.md)

---

## Acceptance Criteria

### MEU-PW12: Data-Flow Chain Fix

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-1 | TransformStep.Params has `source_step_id` for dynamic source resolution | Spec (09-scheduling.md §9.4) | `test_transform_step_pw12.py::TestDynamicSourceResolution::test_source_step_id_resolves_to_step_output` | ✅ |
| AC-2 | Response extractors unwrap Yahoo/AlphaVantage/generic envelopes | Spec (09-scheduling.md §9.4) | `test_response_extractors.py` (19 tests) | ✅ |
| AC-3 | Provider slug normalization resolves display names to registry keys | Local Canon (field_mappings.py) | `test_field_mappings.py::TestProviderSlugNormalization` | ✅ |
| AC-4 | Identity field mapping as generic fallback | Local Canon (field_mappings.py) | `test_field_mappings.py::TestFieldMappingRegistry::test_generic_mapping_exists`, `test_missing_mapping_returns_empty_graceful` | ✅ |
| AC-5 | Records enriched with provider and timestamp | Local Canon (transform_step.py) | `test_transform_step_pw12.py::TestRecordEnrichment::test_records_enriched_with_provider_and_timestamp` | ✅ |
| AC-6 | TransformStep output stored under `output_key` | Spec (09-scheduling.md §9.4) | `test_transform_step_pw12.py::TestOutputKeyAndPresentationMapping::test_records_stored_under_output_key` | ✅ |
| AC-7 | SendStep promotes pipeline outputs into template context | Spec (09-scheduling.md §9.7) | `test_pipeline_dataflow.py::TestFullPipelineChain::test_fetch_transform_send_happy_path` | ✅ |
| AC-8 | Zero records with `min_records > 0` returns WARNING | Spec (09-scheduling.md §9.4) | `test_transform_step_pw12.py::TestZeroRecordWarning::test_zero_records_min_records_gt_0_returns_warning` | ✅ |
| AC-9 | Invalid step params rejected at boundary (422, not runtime) | AGENTS.md §Boundary Input Contract | `test_policy_validator.py::TestStepParamsValidation::test_invalid_value_rejected`, `test_extra_key_rejected_when_extra_forbid`, `test_missing_required_field_rejected`, `test_batch_size_out_of_range_rejected` | ✅ |
| AC-10 | Source auto-discovery when `source_step_id` is None | Local Canon (pipeline_runner.py stores under step_def.id) | `test_transform_step_pw12.py::TestDynamicSourceResolution::test_auto_discover_fetch_output_when_source_step_id_none`, `test_auto_discover_skips_non_fetch_outputs` | ✅ |

### MEU-PW13: Integration Tests

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-E2E-1 | Full Fetch→Transform→Send chain runs without error (email channel, mocked SMTP) | Spec (09-scheduling.md §9.4) | `test_pipeline_dataflow.py::TestFullPipelineChain::test_fetch_transform_send_happy_path` | ✅ |
| AC-E2E-2 | Rendered email body (captured from send_report_email mock) contains actual ticker data (178.72, 415.2) | Spec (09-scheduling.md §9.4) | `test_pipeline_dataflow.py::TestFullPipelineChain::test_fetch_transform_send_happy_path` | ✅ |
| AC-E2E-3 | Yahoo envelope extraction produces 2 records | Spec (09-scheduling.md §9.4) | `test_pipeline_dataflow.py::TestEnvelopeUnwrapping::test_yahoo_quote_envelope_extracted` | ✅ |
| AC-E2E-4 | Canonical field mapping applies correctly | Local Canon (field_mappings.py) | `test_pipeline_dataflow.py::TestFieldMappingIntegration::test_yahoo_fields_mapped_to_canonical` | ✅ |
| AC-E2E-5 | Cache upsert receives mapped data | Local Canon (transform_step.py) | `test_pipeline_dataflow.py::TestFetchCacheIntegration::test_cache_upsert_called_after_fetch` | ✅ |
| AC-E2E-6 | Zero-record scenario produces WARNING status | Spec (09-scheduling.md §9.4) | `test_pipeline_dataflow.py::TestZeroRecordWarning::test_empty_response_with_min_records_returns_warning` | ✅ |

<!-- CACHE BOUNDARY -->
<!-- Content above this line is stable across revision passes (KV cache prefix). -->
<!-- Content below this line changes between passes (evidence, results, corrections). -->

---

## Evidence

### Production Bugs Discovered During Integration Testing

| # | Bug | Root Cause | Fix |
|---|-----|------------|-----|
| 1 | WARNING step output lost to downstream steps | `pipeline_runner.py` only stored output for `SUCCESS` status | Added `PipelineStatus.WARNING` to output storage condition (L233) |
| 2 | Response extractor lookup failed for Yahoo | `extract_records()` used display name "Yahoo Finance" but registry keyed on slug "yahoo" | Added `_PROVIDER_SLUG_MAP` normalization in `response_extractors.py` |
| 3 | `test_scheduling_service.py` TypeError post-PW12 | `_DummyParams` was a plain class — couldn't accept kwargs from `policy_validator._check_step_params()` | Made `_DummyParams` a Pydantic `BaseModel` with `extra="allow"` |
| 4 | TransformStep gets 0 records when `source_step_id` is None | Fallback key `"fetch_result"` doesn't exist — PipelineRunner stores under `step_def.id` | Added `_resolve_source()` with 3-tier resolution: explicit → auto-discover by FetchStep output shape → legacy fallback |

### FAIL_TO_PASS Evidence (TDD Red Phase)

**AC-10 auto-discovery** (2 tests written before fix):
```
FAILED tests/unit/test_transform_step_pw12.py::TestDynamicSourceResolution::test_auto_discover_fetch_output_when_source_step_id_none
  assert 0 == 2  (records_written was 0 because fallback key "fetch_result" didn't exist)
```
After `_resolve_source()` added: both `test_auto_discover_*` tests pass (19/19 in file).

**AC-E2E-2 render path** (test rewritten before assertion fix):
Previous test used `channel: "local_file"` which never calls `_resolve_body()`. Replaced with Tier 2 template rendering that asserts `"178.72"` (AAPL price) and `"415.2"` (MSFT price) appear in rendered HTML.

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `uv run pytest tests/ -x --tb=short` | 0 | 2154 passed, 15 skipped |
| `uv run pyright packages/` | 0 | 0 errors, 0 warnings, 0 informations |
| `uv run ruff check packages/` | 0 | All checks passed! |
| `rg "TODO\|FIXME\|NotImplementedError" packages/core/.../pipeline_steps/ packages/infrastructure/.../market_data/` | 0 | 0 matches |

### Quality Gate Results

```
pyright: 0 errors, 0 warnings, 0 informations
ruff: 0 violations
pytest: 2154 passed, 15 skipped, 0 failed
anti-placeholder: 0 matches
```

---

## Changed Files

| File | Action | Lines | Summary |
|------|--------|-------|---------|
| `packages/core/src/zorivest_core/pipeline_steps/transform_step.py` | modified | L91-129, L172 | Added `_resolve_source()` with 3-tier fallback (explicit → auto-discover → legacy). Fixed stale `source_key` reference in warning log. |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | modified | L233-237 | Store output for WARNING + SUCCESS statuses |
| `packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py` | modified | L173-181 | Add `_PROVIDER_SLUG_MAP` + slug normalization in `extract_records()` |
| `tests/unit/test_transform_step_pw12.py` | modified | L149-208 | Added 2 tests for source auto-discovery (AC-10) |
| `tests/integration/test_pipeline_dataflow.py` | modified | L175-242 | Replaced weak `local_file` send test with full `SendStep.execute()` email path — mocked `send_report_email` captures rendered `html_body`, asserts ticker data (AC-E2E-1, AC-E2E-2) |
| `tests/unit/test_scheduling_service.py` | modified | L16, L31-35 | `_DummyParams` → Pydantic BaseModel with `extra="allow"` |

```diff
# transform_step.py — _resolve_source() (NEW)
+    @staticmethod
+    def _resolve_source(source_step_id, context):
+        if source_step_id:
+            return context.outputs.get(source_step_id, {})
+        # Auto-discover by FetchStep output shape
+        for key, value in context.outputs.items():
+            if isinstance(value, dict) and "content" in value and "provider" in value:
+                return value
+        return context.outputs.get("fetch_result", {})  # legacy fallback

# transform_step.py — execute() refactored to use _resolve_source
-        source_key = p.source_step_id if p.source_step_id else "fetch_result"
-        source_output = context.outputs.get(source_key, {})
+        source_output = self._resolve_source(p.source_step_id, context)
```

```diff
# pipeline_runner.py — WARNING output persistence
-            if result.status == PipelineStatus.SUCCESS and result.output:
+            if result.status in (PipelineStatus.SUCCESS, PipelineStatus.WARNING) and result.output:
```

---

## Codex Validation Report

_Left blank for reviewer agent. Reviewer fills this section during `/validation-review`._

### Recheck Protocol

1. Read Scope + AC table
2. Verify each AC against Evidence section (file:line, not memory)
3. Run all Commands Executed and compare output
4. Run Quality Gate commands independently
5. Record findings below

### Findings

| # | Severity | Finding | File:Line | Recommendation | Status |
|---|----------|---------|-----------|----------------|--------|

### Verdict

`pending` — awaiting Codex validation

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | 2026-04-21 | Antigravity (Gemini) | Initial handoff: PW12 + PW13 combined |
| Submitted for review | 2026-04-21 | Antigravity (Gemini) | Sent to GPT-5.4 Codex |
