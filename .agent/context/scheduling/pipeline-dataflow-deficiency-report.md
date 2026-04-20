# Pipeline Data-Flow Deficiency Report

> **Date:** 2026-04-20
> **Scope:** FetchStep → TransformStep → SendStep data handoff chain
> **Trigger:** User-reported "No quote data available" in email despite pipeline success status
> **Policy:** "Yahoo Finance Daily Quote Report" (ID: `51b4dc4f-a43a-41e0-9991-2e79246fc348`)

---

## 1. Executive Summary

The pipeline reports **success** on all 3 steps but emails contain "No quote data available" instead of actual quote data. Root cause: **six interconnected bugs** form a broken data-flow chain from HTTP fetch through to email template rendering. No single bug is the "cause" — the chain has never worked end-to-end for quote data because each step was built and unit-tested in isolation with hardcoded context keys that don't match the real pipeline wiring.

This is precisely the gap predicted by known issue [PIPE-E2E-CHAIN].

---

## 2. Pipeline Execution Evidence

### 2.1 Run Record (Most Recent)

```
run_id:       a87b04a3-e2c2-40df-8963-d82b5320e360
policy_id:    51b4dc4f-a43a-41e0-9991-2e79246fc348
status:       success ← MISLEADING
trigger_type: manual
started_at:   2026-04-20T18:01:14.478649
duration_ms:  4297
```

### 2.2 Step-Level Results

| Step ID | Type | Status | Duration | Notes |
|---------|------|--------|----------|-------|
| `fetch_yahoo_quotes` | fetch | success | 125ms | Likely cache hit (too fast for live HTTP) |
| `transform_quotes` | transform | success | 297ms | **0 records written** (silent) |
| `send_report` | send | success | 3875ms | Email delivered but with empty template |

### 2.3 Policy Step Definitions

```json
steps: [
  { "id": "fetch_yahoo_quotes", "type": "fetch",     "params": { "provider": "Yahoo Finance", "data_type": "quote", "criteria": { "tickers": ["AAPL","MSFT",...] } } },
  { "id": "transform_quotes",   "type": "transform",  "params": { "target_table": "market_quotes", "validation_rules": "quote" } },
  { "id": "send_report",        "type": "send",        "params": { "body_template": "daily_quote_summary", "channel": "email" } }
]
```

---

## 3. Discovered Issues (6)

### 3.1 [PIPE-STEPKEY] — TransformStep hardcodes `"fetch_result"` instead of resolving actual step output key

**Severity:** Critical (data flow broken)
**Files:** [transform_step.py:72](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py#L72), [transform_step.py:148](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py#L148)

**Mechanism:**
- `PipelineRunner` stores each step's output under its **step ID** from the policy JSON:
  ```python
  # pipeline_runner.py:237
  context.outputs[step_def.id] = step_result.output  # key = "fetch_yahoo_quotes"
  ```
- `TransformStep.execute()` reads data from a **hardcoded key**:
  ```python
  # transform_step.py:72
  source_content = context.outputs.get("fetch_result", {}).get("content", b"")
  ```
- `_apply_mapping()` also reads from the same hardcoded key:
  ```python
  # transform_step.py:148
  fetch_info = context.outputs.get("fetch_result", {})
  ```
- Since `"fetch_result"` never exists in `context.outputs`, both calls get `{}`, resulting in 0 records and no field mapping.

**Why tests didn't catch it:**
Unit tests in `test_transform_step.py` inject data directly as `context.outputs["fetch_result"]`, matching the hardcode. No integration test exercises the real `PipelineRunner` → `TransformStep` wiring.

**Evidence:** Lines [363](file:///p:/zorivest/tests/unit/test_transform_step.py#L363), [399](file:///p:/zorivest/tests/unit/test_transform_step.py#L399), [439](file:///p:/zorivest/tests/unit/test_transform_step.py#L439), [480](file:///p:/zorivest/tests/unit/test_transform_step.py#L480) all use `"fetch_result"`.

**Fix:** TransformStep must discover its predecessor's output key dynamically. Options:
1. **Convention-based:** Read from `context.outputs` by scanning for the previous step's output (requires step ordering metadata or a `source_step_id` param)
2. **Param-based:** Add `source_step_id` to TransformStep.Params so the policy explicitly declares `"source_step_id": "fetch_yahoo_quotes"`
3. **First-match:** Scan `context.outputs` for any dict containing a `"content"` key (fragile)

Option 2 is most explicit and spec-aligned.

---

### 3.2 [PIPE-TMPLVAR] — Email template expects `quotes` but no step produces a `quotes` key

**Severity:** Critical (template always renders empty)
**Files:** [email_templates.py:54](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/email_templates.py#L54), [send_step.py:243-252](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py#L243-L252)

**Mechanism:**
- The `daily_quote_summary` template checks:
  ```jinja2
  {% if quotes %}
    {% for q in quotes %}
      {{ q.symbol }} / {{ q.price }} / {{ q.change }} / {{ q.change_pct }} / {{ q.volume }}
    {% endfor %}
  {% else %}
    No quote data available for this run.
  {% endif %}
  ```
- `_resolve_body()` builds template context by merging `context.outputs`:
  ```python
  # send_step.py:249-251
  for key, value in context.outputs.items():
      if key not in render_ctx:
          render_ctx[key] = value
  ```
- At render time, `context.outputs` contains keys like `fetch_yahoo_quotes`, `transform_quotes`, `provider_adapter`, `smtp_config`, etc. — **never `quotes`**.
- Template gets `quotes=undefined` → `{% if quotes %}` is falsy → renders "No quote data available"

**Fix:** One of:
1. TransformStep or a new "prepare_template_context" step must extract parsed records and place them in `context.outputs["quotes"]`
2. Template should reference `context.outputs["transform_quotes"]["records"]` or similar
3. SendStep `_resolve_body()` should have a template-variable mapping config in the policy

---

### 3.3 [PIPE-RAWBLOB] — No response envelope extraction for Yahoo API responses

**Severity:** High (even if step key fixed, data is still raw bytes)
**Files:** [http_cache.py:61-63](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/http_cache.py#L61-L63), [fetch_step.py:117](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L117)

**Mechanism:**
- Yahoo Finance `/v6/finance/quote?symbols=AAPL,MSFT` returns:
  ```json
  {"quoteResponse": {"result": [{"symbol": "AAPL", "regularMarketPrice": 150.0, ...}], "error": null}}
  ```
- `fetch_with_cache()` stores `response.content` as raw bytes — the entire HTTP body including the envelope
- FetchStep stores this in `StepResult.output["content"]` as raw bytes
- TransformStep (if it could read the data) does `json.loads(source_content)` which would produce the **envelope dict** `{"quoteResponse": {...}}`, not the records list
- No component extracts `data["quoteResponse"]["result"]` to get the actual quote array

**Fix:** Need a **response extractor** per provider that unwraps the API envelope to yield the records array. This could be:
1. A method on the URL builder (e.g., `extract_records(raw_json, data_type)`)
2. A separate extractor registry
3. FetchStep post-processing hook

---

### 3.4 [PIPE-PROVNORM] — Provider name mismatch between registry and field mappings

**Severity:** Medium (field mapping silently no-ops)
**Files:** [field_mappings.py:53](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py#L53), [provider_registry.py:150](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py#L150)

**Mechanism:**
- Provider registry uses display names: `"Yahoo Finance"`, `"Polygon.io"`, `"Alpha Vantage"`
- Field mapping registry uses short keys: `"yahoo"`, `"polygon"`, `"ibkr"`
- When TransformStep calls `apply_field_mapping(provider="Yahoo Finance", data_type="quote")`:
  ```python
  # field_mappings.py:122
  mapping = FIELD_MAPPINGS.get(("Yahoo Finance", "quote"), {})  # → {} (no match!)
  ```
- All fields go into `_extra`, canonical mapping never applied
- Silently falls through to raw fields (no error raised)

**Fix:** Either:
1. Normalize provider names to lowercase slugs at the field mapping lookup
2. Add a `slug` field to ProviderConfig and use it consistently
3. Make field mappings use display names to match provider registry

---

### 3.5 [PIPE-QUOTEFIELD] — Template expects `symbol`/`price`/`change`/`change_pct` but canonical schema has different fields

**Severity:** Medium (even if all upstream issues fixed, template fields don't match)
**Files:** [email_templates.py:68-76](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/email_templates.py#L68-L76), [field_mappings.py:53-58](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py#L53-L58), [validation_gate.py:42-59](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py#L42-L59)

**Mechanism:**
- Template expects per-quote object with: `symbol`, `price`, `change`, `change_pct`, `volume`
- Yahoo field mapping produces canonical fields: `bid`, `ask`, `last`, `volume`
- Pandera Quote schema validates: `ticker`, `last`, `timestamp`, `provider`, `bid`, `ask`, `volume`
- Missing entirely from both mapping and schema: `price`, `change`, `change_pct`
- `symbol` → mapped to nothing (Yahoo sends `symbol` natively, but it's not in the mapping, so it goes to `_extra`)

**Field alignment gap:**

| Template expects | Yahoo sends | Field mapping produces | Pandera validates |
|---|---|---|---|
| `symbol` | `symbol` | `_extra.symbol` | `ticker` |
| `price` | `regularMarketPrice` | `last` | `last` |
| `change` | `regularMarketChange` | *(unmapped)* | *(not in schema)* |
| `change_pct` | `regularMarketChangePercent` | *(unmapped)* | *(not in schema)* |
| `volume` | `regularMarketVolume` | `volume` | `volume` |

**Fix:** Either:
1. Add `regularMarketChange` → `change` and `regularMarketChangePercent` → `change_pct` to Yahoo quote field mappings, and add `symbol` passthrough
2. Align template to use canonical field names (`last` instead of `price`, compute change % in template)
3. Add a template-specific data preparation step

---

### 3.6 [PIPE-SILENTPASS] — TransformStep returns SUCCESS with 0 records, masking upstream data loss

**Severity:** Medium (observability gap)
**Files:** [transform_step.py:83-93](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py#L83-L93)

**Mechanism:**
```python
# transform_step.py:83-93
if not records:
    return StepResult(
        status=PipelineStatus.SUCCESS,  # ← Should this be SUCCESS when 0 records?
        output={
            "records_written": 0,
            "records_quarantined": 0,
            "quality_ratio": 0.0,
        },
    )
```
- When upstream data is unavailable (PIPE-STEPKEY), TransformStep gets 0 records and returns SUCCESS
- Pipeline continues to SendStep, which renders empty template, sends email, reports SUCCESS
- User sees "success" across the board with no warning that zero data was processed
- The `quality_ratio: 0.0` is buried in step output, never surfaced to UI or logs

**Fix:**
1. Return `PipelineStatus.FAILED` or `WARNING` when `records == 0` and the step was not explicitly configured to allow empty datasets
2. At minimum, emit a `structlog.warning("transform_zero_records")` so it appears in logs
3. Consider adding a `min_records` param to TransformStep.Params (default: 1)

---

## 4. Dependency Graph

The issues form a serial chain — each must be resolved for the next to matter:

```
PIPE-STEPKEY ──→ PIPE-RAWBLOB ──→ PIPE-PROVNORM ──→ PIPE-QUOTEFIELD ──→ PIPE-TMPLVAR
    │                                                                         │
    └── PIPE-SILENTPASS (observability — independent of data flow) ────────────┘
```

**Resolution order:**
1. **PIPE-STEPKEY** — Fix TransformStep to find its source step output (unblocks all data flow)
2. **PIPE-RAWBLOB** — Add response envelope extraction (unblocks record parsing)
3. **PIPE-PROVNORM** — Normalize provider names for field mapping lookup
4. **PIPE-QUOTEFIELD** — Extend Yahoo quote mapping with `change`, `change_pct`, `symbol`
5. **PIPE-TMPLVAR** — Wire parsed quote records into template `quotes` variable
6. **PIPE-SILENTPASS** — Add zero-record warning/failure (independent, can be done anytime)

---

## 5. Test Gaps

| Issue | Existing Test | Gap |
|---|---|---|
| PIPE-STEPKEY | `test_transform_step.py` uses hardcoded `"fetch_result"` key | No test uses real PipelineRunner output key |
| PIPE-TMPLVAR | `test_send_step_template.py` injects `quotes` into context directly | No test verifies template receives data from real pipeline chain |
| PIPE-RAWBLOB | None | No test parses real Yahoo JSON envelope |
| PIPE-PROVNORM | None | No test calls `apply_field_mapping(provider="Yahoo Finance")` |
| PIPE-QUOTEFIELD | None | No test maps Yahoo quote fields to template-expected shape |
| PIPE-SILENTPASS | `test_transform_step.py` tests empty input → success | Test *validates* the broken behavior |

All gaps are manifestations of [PIPE-E2E-CHAIN] — the lack of integration tests that exercise the full data handoff chain.

---

## 6. MEU Recommendation

These 6 issues should be addressed as a single MEU or a tightly-coupled pair:

**Option A: Single MEU** — "Pipeline Data Flow Chain Fix" (~4-6 hours)
- Fix all 6 issues in dependency order
- Write 3-5 integration tests exercising the full chain with mocked HTTP
- Extends MEU-PW8 test harness

**Option B: Two MEUs** — Split by layer
- **MEU-PW12:** PIPE-STEPKEY + PIPE-RAWBLOB + PIPE-PROVNORM + PIPE-SILENTPASS (infrastructure/core fixes)
- **MEU-PW13:** PIPE-QUOTEFIELD + PIPE-TMPLVAR (template/presentation fixes)

Recommendation: **Option A** — the issues are so tightly coupled that splitting them would require interim stubs and wasted setup.

---

## 7. Files Examined

| File | Lines | Purpose |
|---|---|---|
| [pipeline_runner.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/pipeline_runner.py) | 100-260 | Step output storage mechanism |
| [fetch_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py) | 1-279 | FetchStep output shape |
| [transform_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/transform_step.py) | 1-190 | Source key resolution, mapping |
| [send_step.py](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/send_step.py) | 189-253 | Template context building |
| [email_templates.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/rendering/email_templates.py) | 1-150 | Template variable expectations |
| [field_mappings.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/field_mappings.py) | 1-136 | Provider key naming, field map |
| [validation_gate.py](file:///p:/zorivest/packages/core/src/zorivest_core/services/validation_gate.py) | 42-59 | Quote schema fields |
| [provider_registry.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/provider_registry.py) | 150-166 | Yahoo Finance config |
| [url_builders.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/url_builders.py) | 49-86 | Yahoo URL construction |
| [http_cache.py](file:///p:/zorivest/packages/infrastructure/src/zorivest_infra/market_data/http_cache.py) | 1-68 | Raw bytes storage |
| [test_transform_step.py](file:///p:/zorivest/tests/unit/test_transform_step.py) | 363-480 | Hardcoded `"fetch_result"` in fixtures |
