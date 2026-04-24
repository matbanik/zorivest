# 09f — Policy Emulator

> Phase: P2.5c · MEU-PH8
> Prerequisites: All Tier 1–3 gaps (MEU-PH1 through MEU-PH7)
> Unblocks: MCP emulator tools (05g), full agent-first authoring workflow
> Resolves: [PIPE-NOEMULATOR]
> Source: [retail-trader-policy-use-cases.md](../../_inspiration/policy_pipeline_wiring-research/retail-trader-policy-use-cases.md) Gap H
> Status: ⬜ planned

---

## 9F.1 PolicyEmulator (MEU-PH8)

### 9F.1a Purpose

4-phase dry-run engine for AI policy authoring. The emulator validates policy JSON through PARSE → VALIDATE → SIMULATE → RENDER without executing real API calls, sending emails, or writing to production database.

> [!CAUTION]
> **The emulator is a security boundary, not just a dev convenience.** All three independent reviews identified the "headline attack" (F33): `QueryStep → RenderStep({{ q1 | tojson }})` can bulk-exfiltrate entire tables through MCP response — no SSTI escape needed. The emulator MUST ship with output containment from day one, or it is a net-negative security feature.

### 9F.1b Design

New file: `packages/core/src/zorivest_core/services/policy_emulator.py`

```python
class PolicyEmulator:
    """4-phase dry-run engine for AI policy authoring."""

    def __init__(self, sandbox: SqlSandbox, template_engine: HardenedSandbox,
                 template_repo: EmailTemplateRepository):
        self._sandbox = sandbox
        self._engine = template_engine
        self._template_repo = template_repo

    async def emulate(self, policy_json: dict,
                      phases: list[str] = ["PARSE", "VALIDATE", "SIMULATE", "RENDER"]
                     ) -> EmulatorResult:
        result = EmulatorResult()

        # PHASE 1: PARSE
        if "PARSE" in phases:
            try:
                policy = PolicyDocument(**policy_json)
                result.phase = "PARSE"
            except ValidationError as e:
                result.valid = False
                result.errors.append(EmulatorError(
                    phase="PARSE", error_type="SCHEMA_INVALID", message=str(e)
                ))
                return result

        # PHASE 2: VALIDATE
        if "VALIDATE" in phases:
            val_errors = validate_policy(policy)
            for step in policy.steps:
                if step.type == "query":
                    for q in step.params.get("queries", []):
                        sql_errors = self._sandbox.validate_sql(q["sql"])
                        val_errors.extend(sql_errors)
                if step.type == "send":
                    tmpl_name = step.params.get("body_template")
                    if tmpl_name:
                        tmpl = self._template_repo.get_by_name(tmpl_name)
                        if not tmpl:
                            val_errors.append(f"Template '{tmpl_name}' not found")
            ref_errors = self._check_ref_integrity(policy)
            if val_errors or ref_errors:
                result.valid = False
                for e in val_errors + ref_errors:
                    result.errors.append(EmulatorError(
                        phase="VALIDATE", error_type="VALIDATION_FAILED", message=str(e)
                    ))
            result.phase = "VALIDATE"

        # PHASE 3: SIMULATE
        if "SIMULATE" in phases and result.valid:
            mock_context = StepContext(run_id="emulator", policy_id="emulator")
            for step_def in policy.steps:
                mock_output = self._get_mock_output(step_def)
                mock_context.outputs[step_def.id] = mock_output
            result.mock_outputs = {k: _anonymize(v) for k, v in mock_context.outputs.items()}
            result.phase = "SIMULATE"

        # PHASE 4: RENDER
        if "RENDER" in phases and result.valid:
            for step_def in policy.steps:
                if step_def.type == "send":
                    inline = step_def.params.get("body_template_inline")
                    if inline:
                        rendered = self._engine.render_safe(inline, mock_context.outputs)
                        result.template_preview_hash = hashlib.sha256(
                            rendered.encode()
                        ).hexdigest()
            result.phase = "RENDER"

        return result
```

### 9F.1c Phase Responsibilities

| Phase | What It Does | Security Property |
|-------|-------------|-------------------|
| **PARSE** | Validates policy JSON against `PolicyDocument` Pydantic model | Schema enforcement, step-count cap |
| **VALIDATE** | Runs all 8+ validation rules, pre-parses SQL via AST allowlist, checks ref integrity, verifies template existence | Semantic validation, SQL safety |
| **SIMULATE** | Executes step graph with mock/anonymized data | No production data exposed |
| **RENDER** | Compiles templates with simulated data, returns SHA-256 hash | Agent gets validity signal without seeing data |

---

## 9F.2 Output Containment (MEU-PH8)

### 9F.2a Controls

| Control | Spec | Purpose |
|---------|------|---------|
| Per-call MCP response cap | 4 KiB max for emulator tool responses | Prevents bulk data exfil in single call |
| Cumulative session budget | 64 KiB per policy-hash per session, rate-limited to 10 calls/min | Defeats chunked exfil (F35) |
| SHA-256 hashed RENDER | RENDER phase returns `sha256(rendered_html)`, not raw content | Agent gets validity signal without seeing data |
| Sanitized error wrapper | Generic error codes only; stack traces to local log file | No PII in MCP responses |
| Anonymized snapshot DB | SIMULATE uses synthetic/anonymized data, not production rows | Production data never enters agent context |

### 9F.2b Implementation

New file: `packages/core/src/zorivest_core/services/emulator_budget.py`

```python
from dataclasses import dataclass, field
from collections import defaultdict
import time

MAX_BYTES_PER_SESSION = 64 * 1024  # 64 KiB
MAX_CALLS_PER_MINUTE = 10

@dataclass
class SessionBudget:
    """Tracks cumulative byte usage per policy-hash per session."""
    _usage: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _call_times: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def check_budget(self, policy_hash: str, response_bytes: int) -> None:
        # Rate limit
        now = time.monotonic()
        recent = [t for t in self._call_times[policy_hash] if now - t < 60]
        if len(recent) >= MAX_CALLS_PER_MINUTE:
            raise SecurityError("Rate limit exceeded: 10 calls/min per policy")
        self._call_times[policy_hash] = recent + [now]

        # Byte budget
        projected = self._usage[policy_hash] + response_bytes
        if projected > MAX_BYTES_PER_SESSION:
            raise SecurityError(
                f"Session byte budget exceeded: {projected} > {MAX_BYTES_PER_SESSION}"
            )
        self._usage[policy_hash] = projected
```

---

## 9F.3 Structured Error Schema (MEU-PH8)

### 9F.3a Design

New models in `packages/core/src/zorivest_core/domain/emulator_models.py`:

```python
from pydantic import BaseModel
from typing import Literal

class EmulatorError(BaseModel):
    """Structured error from a specific emulation phase."""
    phase: Literal["PARSE", "VALIDATE", "SIMULATE", "RENDER"]
    step_id: str | None = None
    error_type: str              # "REF_UNRESOLVED", "SQL_BLOCKED", "TEMPLATE_MISSING", etc.
    field: str | None = None     # "steps[2].params.criteria.tickers"
    message: str
    suggestion: str | None = None

class EmulatorResult(BaseModel):
    """Complete emulation result with structured errors."""
    valid: bool = True
    phase: str = ""
    errors: list[EmulatorError] = []
    warnings: list[EmulatorError] = []
    mock_outputs: dict | None = None
    template_preview_hash: str | None = None
    bytes_used: int = 0
```

### 9F.3b Error Type Registry

| Error Type | Phase | Meaning |
|-----------|-------|---------|
| `SCHEMA_INVALID` | PARSE | Policy JSON doesn't match Pydantic model |
| `STEP_COUNT_EXCEEDED` | PARSE | >20 steps |
| `REF_UNRESOLVED` | VALIDATE | Step reference points to non-existent step |
| `SQL_BLOCKED` | VALIDATE | SQL failed AST allowlist |
| `TEMPLATE_MISSING` | VALIDATE | Referenced template not in DB |
| `VARIABLE_UNUSED` | VALIDATE | Declared variable never referenced (warning) |
| `SIMULATE_ERROR` | SIMULATE | Mock execution failed |
| `RENDER_ERROR` | RENDER | Template compilation failed |
| `OUTPUT_TOO_LARGE` | RENDER | Rendered output exceeds 256 KiB |

---

## 9F.4 Source Type Metadata (MEU-PH8)

Every step output includes a `_source_type` metadata field for future taint tracking:

```python
context.outputs[step_def.id] = {
    **step_result.output,
    "_source_type": step.source_type,  # "db" | "provider" | "computed"
}
```

| Step Type | source_type |
|-----------|-------------|
| `fetch` | `provider` |
| `query` | `db` |
| `transform` | `computed` |
| `compose` | `computed` |
| `render` | `computed` |

---

## 9F.5 Tests

New files:
- `tests/unit/test_policy_emulator.py`
- `tests/unit/test_emulator_budget.py`

### Emulator Tests

| Test | Assertion |
|------|-----------|
| `test_parse_valid_policy` | Valid JSON passes PARSE phase |
| `test_parse_invalid_schema` | Invalid JSON returns structured `EmulatorError` |
| `test_validate_ref_integrity` | Broken ref returns `REF_UNRESOLVED` error |
| `test_validate_sql_blocked` | INSERT in query step returns `SQL_BLOCKED` |
| `test_validate_template_exists` | Referenced template found → no error |
| `test_validate_template_missing` | Missing template → `TEMPLATE_MISSING` |
| `test_simulate_produces_mock_outputs` | Mock context populated for all steps |
| `test_render_returns_hash` | RENDER returns SHA-256, not raw content |
| `test_render_inline_template` | Inline template compiles with simulated data |
| `test_phase_subset` | Can run individual phases (e.g., PARSE only) |
| `test_early_stop_on_parse_error` | Parse failure prevents VALIDATE/SIMULATE/RENDER |

### Budget Tests

| Test | Assertion |
|------|-----------|
| `test_budget_tracks_bytes` | Cumulative bytes tracked per policy hash |
| `test_budget_rejects_over_limit` | >64 KiB raises `SecurityError` |
| `test_rate_limit_enforced` | >10 calls/min raises `SecurityError` |
| `test_budget_per_policy_hash` | Different policy hashes have independent budgets |

---

## 9F.6 Exit Criteria

- [ ] `policy_emulator.py` exists with 4-phase dry-run
- [ ] `emulator_budget.py` exists with session budget + rate limiting
- [ ] `emulator_models.py` exists with `EmulatorError` + `EmulatorResult`
- [ ] Output containment: RENDER returns SHA-256, not raw content
- [ ] MCP responses capped at 4 KiB
- [ ] Cumulative session budget: 64 KiB per policy-hash
- [ ] `_source_type` metadata added to step outputs
- [ ] All 15 tests pass (11 emulator + 4 budget)
