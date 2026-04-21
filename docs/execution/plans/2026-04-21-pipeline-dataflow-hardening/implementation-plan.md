---
project: "2026-04-21-pipeline-dataflow-hardening"
date: "2026-04-21"
source: "docs/build-plan/09-scheduling.md, docs/build-plan/09b-pipeline-hardening.md"
meus: ["MEU-PW12", "MEU-PW13"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: Pipeline Data-Flow Hardening

> **Project**: `2026-04-21-pipeline-dataflow-hardening`
> **Build Plan Section(s)**: [09 §9.4–9.8](../../../build-plan/09-scheduling.md), [09b §9B.6](../../../build-plan/09b-pipeline-hardening.md)
> **Status**: `draft`

---

## Goal

Fix 6 serial data-flow bugs that prevent market data from flowing through the FetchStep → TransformStep → SendStep chain. The pipeline currently reports SUCCESS while rendering "No quote data available" in email reports. An integration test harness validates the full chain end-to-end.

**Root cause**: Each step was built and unit-tested in isolation with hardcoded context keys that don't match the real PipelineRunner wiring. No integration test exercises the real data handoff.

**Bugs (dependency order)**:

| Bug ID | Summary |
|--------|---------|
| PIPE-STEPKEY | TransformStep uses hardcoded `"fetch_result"` key instead of dynamic step output ID |
| PIPE-RAWBLOB | FetchStep passes raw HTTP bytes; no provider envelope extraction |
| PIPE-PROVNORM | Provider display names ("Yahoo Finance") mismatch field mapping keys ("yahoo") |
| PIPE-QUOTEFIELD | Template expects `symbol, price, change` but field mapping produces `ticker, last` |
| PIPE-TMPLVAR | No step injects `quotes` variable into Jinja2 template context |
| PIPE-SILENTPASS | TransformStep returns SUCCESS with 0 records, masking upstream data loss |

**Evidence**: [Pipeline Data-Flow Deficiency Report](../../../../.agent/context/scheduling/pipeline-dataflow-deficiency-report.md)

---

## User Review Required

> [!IMPORTANT]
> **Backward Compatibility**: All new TransformStep params have defaults preserving existing behavior. No policy JSON schema changes are required for existing policies, but affected policies (e.g., Yahoo Daily Quote Report) will need `source_step_id` and `output_key` params added to their `transform` step definition for the fix to take effect.

> [!IMPORTANT]
> **SendStep Template Context Change**: `_resolve_body()` will promote keys from dict-valued step outputs into the Jinja2 render context (two-level merge). This is a behavioral change — previously only top-level `context.outputs` keys were available as template variables. Existing templates are unaffected because they already render "No data available" for missing keys. After the fix, templates gain access to inner step output keys (e.g., `quotes`, `records_written`).

---

## Proposed Changes

### MEU-PW12: Pipeline Data-Flow Chain Fix

#### Boundary Inventory

| Surface | Schema Owner | Field Constraints | Extra-Field Policy | Invalid-Input Error Code | Create/Update Parity | Source |
|---------|-------------|-------------------|-------------------|--------------------------|---------------------|--------|
| `policy_json.steps[].params` via REST `POST/PUT /api/v1/scheduling/policies` | `validate_policy()` → step-type `Params` model (Pydantic) | Per step type: e.g. TransformStep.Params enforces `min_records: int ≥ 0`, `quality_threshold: float [0.0–1.0]` | `extra="forbid"` on step Params models — unknown keys rejected at boundary | 422 via `validate_policy()` → `scheduling.py:137,180` | Same schema for create and update | Local Canon (`policy_validator.py:92`, `scheduling.py:137`) |
| `policy_json` via MCP `create_policy` tool | `z.record(z.unknown())` → `PolicyDocument` (Pydantic) → `validate_policy()` | Same as above | Same as above | MCP error response wrapping Pydantic 422 | Same schema | Local Canon (`scheduling_tools.ts`) |

> **Validation design**: `validate_policy()` (rule 7) iterates each step, looks up the step type in `STEP_REGISTRY`, and validates `step.params` against the step class's `Params` Pydantic model with `model_validate(step.params, strict=False)`. Invalid values (e.g., `min_records = -1`) and unknown extra keys raise `pydantic.ValidationError`, which is mapped to a `ValidationError(field, message)` and surfaced as 422. This ensures all external-input validation happens at the API boundary, not at runtime.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| TransformStep resolves source step by explicit param | Local Canon | [Deficiency report §3.1](../../../../.agent/context/scheduling/pipeline-dataflow-deficiency-report.md), Option 2 (param-based) |
| Response envelope extraction per provider | Research-backed + Local Canon | Yahoo Finance API v6 response format (`quoteResponse.result`); `response_validator_key` in [provider_registry.py](../../../../packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py) |
| Provider slug normalization | Local Canon | Display names in [provider_registry.py:150](../../../../packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py#L150), slugs in [field_mappings.py:53](../../../../packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py#L53) |
| Yahoo quote field mapping extensions | Local Canon | Template expectations in [email_templates.py:68-76](../../../../packages/infrastructure/src/zorivest_infra/rendering/email_templates.py#L68-L76), field gap analysis in [deficiency report §3.5](../../../../.agent/context/scheduling/pipeline-dataflow-deficiency-report.md) |
| Template variable wiring via output promotion | Local Canon | [Deficiency report §3.2](../../../../.agent/context/scheduling/pipeline-dataflow-deficiency-report.md), [SendStep._resolve_body()](../../../../packages/core/src/zorivest_core/pipeline_steps/send_step.py#L189) |
| Zero-record warning behavior | Local Canon | [Deficiency report §3.6](../../../../.agent/context/scheduling/pipeline-dataflow-deficiency-report.md) |
| Canonical-to-template field name mapping | Local Canon | [email_templates.py](../../../../packages/infrastructure/src/zorivest_infra/rendering/email_templates.py) uses `symbol, price`; [QUOTE_SCHEMA](../../../../packages/core/src/zorivest_core/services/validation_gate.py) uses `ticker, last` |
| Record enrichment with provider/timestamp | Local Canon | [QUOTE_SCHEMA](../../../../packages/core/src/zorivest_core/services/validation_gate.py) requires `ticker, last, timestamp, provider` — only `ticker` and `last` come from field mapping |
| Step params validated at API boundary (not runtime) | Local Canon | AGENTS.md §Boundary Input Contract: "invalid input → 422, not downstream 500". Mechanism: `validate_policy()` rule 7 in [policy_validator.py](../../../../packages/core/src/zorivest_core/domain/policy_validator.py) |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | TransformStep.Params has `source_step_id: str \| None = None`. When set, `execute()` reads source data from `context.outputs[source_step_id]`. When None, falls back to `"fetch_result"` for backward compatibility. | Local Canon | source_step_id points to nonexistent key → 0 records, no crash |
| AC-2 | `extract_records(raw: bytes, provider: str, data_type: str) → list[dict]` unwraps Yahoo quote envelope (`quoteResponse.result`), Polygon OHLCV envelope (`results`), and falls back to generic extraction. | Research-backed | Non-JSON bytes → empty list; missing envelope key → empty list |
| AC-3 | `apply_field_mapping()` normalizes provider display names to slugs via `_PROVIDER_SLUG_MAP` before FIELD_MAPPINGS lookup. `"Yahoo Finance"` → `"yahoo"`, `"Polygon.io"` → `"polygon"`. Unknown names pass through unchanged. | Local Canon | Existing slug-based calls still work correctly |
| AC-4 | Yahoo quote field mapping extended: `regularMarketChange → change`, `regularMarketChangePercent → change_pct`, `symbol → ticker`. | Local Canon | Records missing these fields still map remaining fields correctly |
| AC-5 | TransformStep enriches records with `provider` and `timestamp` from source step output metadata before Pandera validation. | Local Canon | Missing provider in source output → skips enrichment gracefully |
| AC-6 | TransformStep includes validated records in output under configurable `output_key` param (default `"records"`). Records use presentation names: `ticker→symbol`, `last→price`. | Local Canon | output_key not set → records stored under default `"records"` key |
| AC-7 | SendStep `_resolve_body()` promotes keys from dict-valued step outputs into template render context (two-level merge, first-wins for conflicts). | Local Canon | Dict output with key colliding with `generated_at` → existing key preserved |
| AC-8 | TransformStep returns `PipelineStatus.WARNING` (not SUCCESS) when records count is 0 and `min_records` param > 0. Emits `structlog.warning("transform_zero_records")`. Default `min_records=0` preserves backward compat. | Local Canon | min_records=0 + 0 records → SUCCESS (existing behavior) |
| AC-9 | `validate_policy()` rule 7: for each step with a known `type` in STEP_REGISTRY, validate `step.params` against the step class's `Params` model. Invalid values (e.g., `min_records=-1`) → `ValidationError` → 422 at API boundary. Unknown step types already rejected by rule 3. Steps without a Params class skip param validation. | Local Canon (AGENTS.md §Boundary Input Contract) | `min_records=-1` → 422; unknown extra key in transform params → 422; step type without Params class → no error |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [transform_step.py](../../../../packages/core/src/zorivest_core/pipeline_steps/transform_step.py) | modify | Add `source_step_id`, `output_key`, `min_records` params; dynamic source resolution; response extraction call; record enrichment; presentation mapping; zero-record warning (AC-1, AC-5, AC-6, AC-8) |
| [response_extractors.py](../../../../packages/infrastructure/src/zorivest_infra/market_data/response_extractors.py) | new | Per-provider JSON envelope extraction registry (AC-2) |
| [field_mappings.py](../../../../packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py) | modify | Add `_PROVIDER_SLUG_MAP` for display name normalization; extend Yahoo quote mappings (AC-3, AC-4) |
| [send_step.py](../../../../packages/core/src/zorivest_core/pipeline_steps/send_step.py) | modify | Two-level merge in `_resolve_body()` to promote dict-valued output keys into template context (AC-7) |
| [policy_validator.py](../../../../packages/core/src/zorivest_core/domain/policy_validator.py) | modify | Add rule 7: per-step param validation against step-type Params model at boundary (AC-9) |
| [test_response_extractors.py](../../../../tests/unit/test_response_extractors.py) | new | TDD tests for AC-2 |
| [test_transform_step_pw12.py](../../../../tests/unit/test_transform_step_pw12.py) | new | TDD tests for AC-1, AC-5, AC-6, AC-8 |
| [test_field_mappings.py](../../../../tests/unit/test_field_mappings.py) | modify | Add tests for AC-3, AC-4 |
| [test_send_step_template.py](../../../../tests/unit/test_send_step_template.py) | modify | Add tests for AC-7 |
| [test_policy_validator.py](../../../../tests/unit/test_policy_validator.py) | modify | Add tests for AC-9: boundary param validation |

---

### MEU-PW13: Pipeline E2E Chain Integration Tests

#### Boundary Inventory

> No external-input boundaries. This MEU creates test files only.

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Full FetchStep → TransformStep → SendStep chain validation | Local Canon | [Deficiency report §5](../../../../.agent/context/scheduling/pipeline-dataflow-deficiency-report.md), [data flow gap analysis](../../../../.agent/context/scheduling/data_flow_gap_analysis.md) |
| Mocked HTTP with real adapter | Local Canon | Uses `respx` library for httpx mock per existing test patterns |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-E2E-1 | Integration test exercises real PipelineRunner → FetchStep → TransformStep → SendStep chain with mocked HTTP (respx), real MarketDataProviderAdapter, real field mappings, real Pandera validation. | Local Canon | N/A |
| AC-E2E-2 | After chain execution, the rendered email body contains actual ticker symbols and price data (NOT "No quote data available"). | Local Canon | Empty API response → "No quote data available" |
| AC-E2E-3 | FetchStep upserts to cache after successful fetch; cache repo mock verifies `upsert()` called. | Spec | N/A |
| AC-E2E-4 | TransformStep correctly extracts records from Yahoo-format envelope through response extractor. | Research-backed | N/A |
| AC-E2E-5 | Field mapping normalization produces template-compatible output: `symbol`, `price`, `change`, `change_pct`, `volume` fields present. | Local Canon | N/A |
| AC-E2E-6 | Zero-record scenario (empty API response with `min_records=1`) returns WARNING status. | Local Canon | N/A |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| [test_pipeline_dataflow.py](../../../../tests/integration/test_pipeline_dataflow.py) | new | Full chain integration tests, 6 test functions |

---

## Out of Scope

- MCP template discoverability gap ([MCP-TOOLDISCOVERY]) — blocked on MEU-PW12 finalizing template variable contracts
- Yahoo OHLCV chart endpoint extraction — only quote extraction for this MEU
- Policy JSON migration for existing policies — documented but not auto-applied
- PIPE-URLBUILD and PIPE-NOCANCEL — separate MEUs

---

## BUILD_PLAN.md Audit

This project updates status of MEU-PW12 and MEU-PW13 from ⬜ to ✅ in the P2.5b table. No structural changes expected.

```powershell
rg "MEU-PW12|MEU-PW13" docs/BUILD_PLAN.md  # Expected: 2 matches (status column updates)
```

---

## Verification Plan

### 1. Unit Tests (per-MEU TDD)

```powershell
uv run pytest tests/unit/test_transform_step_pw12.py tests/unit/test_response_extractors.py tests/unit/test_field_mappings.py tests/unit/test_send_step_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-pw12.txt; Get-Content C:\Temp\zorivest\pytest-pw12.txt | Select-Object -Last 40
```

### 2. Existing Test Regression

```powershell
uv run pytest tests/unit/test_transform_step.py tests/unit/test_field_mappings.py tests/unit/test_send_step_template.py -x --tb=short -v *> C:\Temp\zorivest\pytest-regression.txt; Get-Content C:\Temp\zorivest\pytest-regression.txt | Select-Object -Last 40
```

### 3. Integration Tests (MEU-PW13)

```powershell
uv run pytest tests/integration/test_pipeline_dataflow.py -x --tb=short -v *> C:\Temp\zorivest\pytest-e2e.txt; Get-Content C:\Temp\zorivest\pytest-e2e.txt | Select-Object -Last 40
```

### 4. Type Check

```powershell
uv run pyright packages/ *> C:\Temp\zorivest\pyright.txt; Get-Content C:\Temp\zorivest\pyright.txt | Select-Object -Last 30
```

### 5. Lint

```powershell
uv run ruff check packages/ *> C:\Temp\zorivest\ruff.txt; Get-Content C:\Temp\zorivest\ruff.txt | Select-Object -Last 20
```

### 6. MEU Gate

```powershell
uv run python tools/validate_codebase.py --scope meu *> C:\Temp\zorivest\validate.txt; Get-Content C:\Temp\zorivest\validate.txt | Select-Object -Last 50
```

### 7. Anti-Placeholder Scan

```powershell
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/pipeline_steps/ packages/infrastructure/src/zorivest_infra/market_data/ *> C:\Temp\zorivest\placeholders.txt; Get-Content C:\Temp\zorivest\placeholders.txt
```

---

## Open Questions

None — all behaviors resolved from local canonical docs and the deficiency report.

---

## Research References

- [Pipeline Data-Flow Deficiency Report](../../../../.agent/context/scheduling/pipeline-dataflow-deficiency-report.md)
- [Data Flow Gap Analysis](../../../../.agent/context/scheduling/data_flow_gap_analysis.md)
- [MCP Template Discoverability Gap](../../../../.agent/context/scheduling/mcp-template-discoverability-gap.md)
- Yahoo Finance API v6 `/v6/finance/quote` response format (envelope: `quoteResponse.result`)
