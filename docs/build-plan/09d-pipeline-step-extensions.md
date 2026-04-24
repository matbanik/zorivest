# 09d — Pipeline Step Extensions

> Phase: P2.5c · MEU-PH4, MEU-PH5, MEU-PH7
> Prerequisites: MEU-PH2 (SQL sandbox) for QueryStep
> Unblocks: Policy Emulator (09f)
> Resolves: [PIPE-NOQUERYSTEP], [PIPE-NOCOMPOSE], [PIPE-NOVARS], [PIPE-NOASSERT], schema_version v1→v2 migration
> Source: [retail-trader-policy-use-cases.md](../../_inspiration/policy_pipeline_wiring-research/retail-trader-policy-use-cases.md) Gaps C, D, F, G
> Status: ⬜ planned

---

## 9D.1 QueryStep (MEU-PH4)

### 9D.1a Purpose

Execute read-only SQL queries against the internal Zorivest DB. Output results as records (same shape as FetchStep output, compatible with TransformStep and SendStep).

### 9D.1b Design

New file: `packages/core/src/zorivest_core/pipeline_steps/query_step.py`

Follows the `RegisteredStep` pattern from [`fetch_step.py:42–49`](file:///p:/zorivest/packages/core/src/zorivest_core/pipeline_steps/fetch_step.py#L42-L49).

```python
class QueryStep(RegisteredStep):
    type_name = "query"
    side_effects = False  # read-only
    source_type = "db"    # output metadata for taint tracking (R5*)

    class Params(BaseModel):
        model_config = {"extra": "forbid"}
        queries: list[QueryDef]  # [{name, sql, binds}]
        output_key: str = "results"
        row_limit: int = Field(default=1000, le=5000)

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        p = self.Params(**params)
        sandbox = context.outputs["sql_sandbox"]  # ← Gap B provides this

        results = {}
        for q in p.queries:
            resolved_binds = RefResolver.resolve_dict(q.binds, context)
            rows = sandbox.execute(q.sql, resolved_binds)
            if len(rows) > p.row_limit:
                rows = rows[:p.row_limit]
            results[q.name] = rows

        return StepResult(status=PipelineStatus.SUCCESS, output={p.output_key: results})
```

**Policy JSON example:**

```json
{
  "id": "get_watchlist_tickers",
  "type": "query",
  "params": {
    "queries": [
      {
        "name": "tickers",
        "sql": "SELECT wi.ticker, wi.notes FROM watchlist_items wi JOIN watchlists w ON wi.watchlist_id = w.id WHERE w.name = :watchlist_name",
        "binds": { "watchlist_name": "Morning Watchlist" }
      }
    ],
    "output_key": "tickers"
  }
}
```

**Constraints:**

| Constraint | Enforcement |
|------------|-------------|
| Read-only (L1) | `sqlite3.Connection.set_authorizer()` — PRIMARY C-level control |
| Read-only (L2) | `mode=ro` SQLite URI parameter |
| Read-only (L3) | `PRAGMA query_only = ON` — defense-in-depth |
| SQL validation (L6) | `sqlglot` AST **allowlist** |
| Parameterized queries | Named `:param` binds — no string interpolation |
| Row limit | Max 1000 rows per query (configurable per-step, max 5000) |
| Timeout (L5) | `progress_handler` — 2-second hard abort |
| Multi-query | `queries` array (like `store_report.data_queries`) |
| Ref support | `binds` values can be `{ "ref": "ctx.step_id.field" }` |
| Fan-out cap | Max 5 queries per step; global pool max 10 per policy |

### 9D.1c Tests

New file: `tests/unit/test_query_step.py`

| Test | Assertion |
|------|-----------|
| `test_simple_select` | Returns rows as list of dicts |
| `test_row_limit_enforced` | >1000 rows truncated to limit |
| `test_parameterized_binds` | Named `:param` binds resolve correctly |
| `test_ref_binds` | `{"ref": "ctx.step_id.field"}` resolves via RefResolver |
| `test_multiple_queries` | Two queries return merged dict |
| `test_output_shape_compatible_with_transform` | Output works as TransformStep input |
| `test_fan_out_cap` | >5 queries per step raises validation error |
| `test_sandbox_integration` | Routes through SqlSandbox (not raw connection) |

### 9D.1d Exit Criteria

- [ ] `query_step.py` exists following RegisteredStep pattern
- [ ] Registered in `step_registry.py`
- [ ] All 8 tests pass
- [ ] Output shape compatible with TransformStep auto-discovery

---

## 9D.2 ComposeStep (MEU-PH5)

### 9D.2a Purpose

Merge outputs from multiple preceding steps into a single dict for template rendering. Supports section assembly for multi-section reports.

### 9D.2b Design

New file: `packages/core/src/zorivest_core/pipeline_steps/compose_step.py`

```python
class ComposeStep(RegisteredStep):
    type_name = "compose"
    side_effects = False
    source_type = "computed"

    class Params(BaseModel):
        model_config = {"extra": "forbid"}
        sources: list[SourceDef]  # [{step_id, key, rename?}]
        output_key: str = "composed"
        merge_strategy: Literal["dict_merge", "array_concat"] = "dict_merge"

    async def execute(self, params: dict, context: StepContext) -> StepResult:
        p = self.Params(**params)
        merged = {}
        for src in p.sources:
            upstream = context.get_output(src.step_id)
            data = upstream.get(src.key, upstream) if src.key else upstream
            target_key = src.rename or src.key or src.step_id
            if p.merge_strategy == "dict_merge":
                merged[target_key] = data
            elif p.merge_strategy == "array_concat":
                merged.setdefault("items", []).extend(data if isinstance(data, list) else [data])
        return StepResult(status=PipelineStatus.SUCCESS, output={p.output_key: merged})
```

**Policy JSON example:**

```json
{
  "id": "merge_report_data",
  "type": "compose",
  "params": {
    "sources": [
      { "step_id": "quotes", "key": "results", "rename": "market_data" },
      { "step_id": "watchlist", "key": "tickers", "rename": "watchlist" },
      { "step_id": "metrics", "key": "summary", "rename": "portfolio" }
    ],
    "output_key": "report_data",
    "merge_strategy": "dict_merge"
  }
}
```

### 9D.2c Tests

New file: `tests/unit/test_compose_step.py`

| Test | Assertion |
|------|-----------|
| `test_dict_merge` | Multiple sources merged into single dict |
| `test_array_concat` | Lists from multiple sources concatenated |
| `test_rename` | Source renamed via `rename` field |
| `test_missing_step_raises` | Non-existent `step_id` raises `KeyError` |
| `test_deep_copy_isolation` | Composed output is isolated from source |

### 9D.2d Exit Criteria

- [ ] `compose_step.py` exists following RegisteredStep pattern
- [ ] Registered in `step_registry.py`
- [ ] All 5 tests pass

---

## 9D.3 Variable Injection (MEU-PH7, part 1)

### 9D.3a Purpose

Enable parameterized policies without duplicating JSON. Users define variables at the policy level; steps reference them via `{"var": "name"}`.

### 9D.3b Design

**Changes to existing files:**

| File | Change |
|------|--------|
| `pipeline.py` → `PolicyDocument` | Add `variables: dict[str, Any] = Field(default_factory=dict)` |
| `ref_resolver.py` | Add `{"var": "name"}` resolution pattern alongside existing `{"ref": ...}` |

```python
# In PolicyDocument (pipeline.py)
class PolicyDocument(BaseModel):
    schema_version: int = Field(default=1, ge=1, le=2)  # v1 existing, v2 adds variables/query/compose/assert
    name: str = Field(..., min_length=1, max_length=128)
    variables: dict[str, Any] = Field(default_factory=dict)  # v2 only — validator rejects if schema_version < 2
    # ...

# In RefResolver (ref_resolver.py)
def _resolve_var(self, var_name: str, variables: dict) -> Any:
    if var_name not in variables:
        raise ValueError(f"Undefined variable: {var_name}")
    return variables[var_name]
```

### 9D.3c Tests

| Test | Assertion |
|------|-----------|
| `test_var_ref_resolves` | `{"var": "threshold"}` resolves to `variables["threshold"]` |
| `test_undefined_var_raises` | Undefined variable raises `ValueError` |
| `test_var_in_binds` | Variable reference in QueryStep binds resolves |

---

## 9D.4 Assertion Gates (MEU-PH7, part 2)

### 9D.4a Purpose

Pre-send data integrity validation. Assertions halt the pipeline if financial data doesn't meet quality thresholds.

### 9D.4b Design

Extend existing `TransformStep` with a `kind` discriminator.

**Changes to existing file:** `transform_step.py`

```python
class Params(BaseModel):
    kind: Literal["transform", "assertion"] = "transform"  # NEW
    assertions: list[AssertionDef] | None = None  # NEW

async def execute(self, params: dict, context: StepContext) -> StepResult:
    p = self.Params(**params)
    if p.kind == "assertion":
        return await self._run_assertions(p, context)
    # ... existing transform logic ...

async def _run_assertions(self, p: Params, context: StepContext) -> StepResult:
    failures = []
    for a in p.assertions:
        value = RefResolver.resolve(a.field_ref, context)
        result = ConditionEvaluator.evaluate(value, a.operator, a.expected)
        if not result:
            failures.append(AssertionFailure(field=a.field_ref, expected=a.expected, actual=value, severity=a.severity))
    fatals = [f for f in failures if f.severity == "fatal"]
    if fatals:
        return StepResult(status=PipelineStatus.FAILED, output={"assertion_failures": failures})
    return StepResult(status=PipelineStatus.SUCCESS, output={"assertion_results": failures})
```

### 9D.4c Tests

| Test | Assertion |
|------|-----------|
| `test_assertion_passes` | All assertions pass → `SUCCESS` |
| `test_assertion_fatal_failure` | Fatal assertion → `FAILED` + halts pipeline |
| `test_assertion_warning` | Non-fatal failure → `SUCCESS` with warnings |
| `test_arithmetic_expression` | `ConditionEvaluator` supports `abs()` and arithmetic |

---

## 9D.5 Step-Count Cap (MEU-PH7, part 3)

### 9D.5a Purpose

Prevent DoS via mega-policies. Cap at 20 steps per policy.

### 9D.5b Design

Add Pydantic validator to `PolicyDocument`:

```python
@field_validator("steps")
@classmethod
def cap_step_count(cls, v):
    if len(v) > 20:
        raise ValueError(f"Policy exceeds 20-step limit ({len(v)} steps)")
    return v

steps: list[PolicyStep] = Field(..., min_length=1, max_length=20)
```

### 9D.5c Tests

| Test | Assertion |
|------|-----------|
| `test_20_steps_allowed` | Policy with 20 steps validates |
| `test_21_steps_rejected` | Policy with 21 steps raises `ValidationError` |

### 9D.5d Exit Criteria (MEU-PH7 combined)

- [ ] `PolicyDocument` has `variables` field
- [ ] `RefResolver` supports `{"var": "name"}` pattern
- [ ] `TransformStep` supports `kind: assertion` discriminator
- [ ] `ConditionEvaluator` extended with arithmetic
- [ ] Step-count cap (20) enforced via Pydantic validator
- [ ] Schema v2 migration implemented per §9D.6
- [ ] All 11 tests pass (3 var + 4 assertion + 1 cap + 3 schema migration)

---

## 9D.6 Schema Version Migration (MEU-PH7, part 4)

### 9D.6a Problem

The `variables` field, new step types (`query`, `compose`), and assertion `kind` discriminator are v2-only features. Existing v1 policies must continue to validate and execute without modification.

> [!CAUTION]
> **Source mandate (retail-trader-policy-use-cases.md line 1760):** "The `variables`, `email_templates` DB entity, and new step types (`query`, `compose`, `assert`) require `schema_version: 2`. The `PolicyDocument` model, `policy_validator`, and all consumers must handle both v1 and v2 schemas during the migration period."

### 9D.6b Design — Dual-Schema Compatibility

**PolicyDocument changes:**

```python
class PolicyDocument(BaseModel):
    schema_version: int = Field(default=1, ge=1, le=2)
    # v2-only fields: present but empty on v1
    variables: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def enforce_version_features(self) -> "PolicyDocument":
        """Reject v2 features used with schema_version=1."""
        v2_step_types = {"query", "compose"}
        v2_assertion_kinds = {s for s in self.steps if s.params.get("kind") == "assertion"}

        has_v2_features = (
            bool(self.variables)
            or any(s.type in v2_step_types for s in self.steps)
            or bool(v2_assertion_kinds)
        )

        if has_v2_features and self.schema_version < 2:
            raise ValueError(
                "Features used require schema_version >= 2: "
                "variables, query/compose step types, or assertion kind. "
                "Set schema_version: 2 in your policy JSON."
            )
        return self
```

**PolicyValidator changes:**

| Rule | v1 Behavior | v2 Behavior |
|------|-------------|-------------|
| `variables` field | Ignored (empty dict) | Validated — unused vars emit warning |
| `query` step type | Rejected | Allowed (requires SQL sandbox) |
| `compose` step type | Rejected | Allowed |
| `kind: assertion` | Rejected | Allowed on TransformStep |
| `{"var": ...}` refs | Rejected | Resolved via `variables` dict |
| `body_template` DB lookup | Falls through to registry | Tries DB first, then registry |

**Migration path for existing policies:**

1. Existing v1 policies continue to work without changes — `schema_version` defaults to `1`
2. To use new features, user/agent sets `schema_version: 2` in the policy JSON
3. The `model_validator` rejects v2 features with v1 version — clear error message guides the fix
4. No automatic migration — v1→v2 is opt-in per policy
5. `PolicyValidator` uses `schema_version` to gate which step types and ref patterns are allowed

### 9D.6c Tests

| Test | Assertion |
|------|-----------|
| `test_v1_policy_still_validates` | Existing v1 policy with no v2 features passes |
| `test_v2_features_rejected_on_v1` | `variables` or `query` step with `schema_version: 1` raises `ValidationError` |
| `test_v2_features_accepted_on_v2` | Same features with `schema_version: 2` pass |
