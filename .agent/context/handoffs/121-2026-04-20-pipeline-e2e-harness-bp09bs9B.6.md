---
seq: "121"
date: "2026-04-20"
project: "2026-04-20-pipeline-e2e-harness"
meu: "MEU-PW8"
status: "complete"
action_required: "VALIDATE_AND_APPROVE"
template_version: "2.1"
verbosity: "standard"
plan_source: "docs/execution/plans/2026-04-20-pipeline-e2e-harness/implementation-plan.md"
build_plan_section: "bp09bs9B.6"
agent: "Claude Opus 4"
reviewer: "GPT-5.4 Codex"
predecessor: "120-2026-04-19-url-builders-cancellation-corrections.md"
---

# Handoff: 121-2026-04-20-pipeline-e2e-harness-bp09bs9B.6

> **Status**: `complete`
> **Action Required**: `VALIDATE_AND_APPROVE`

---

## Scope

**MEU**: MEU-PW8 — Pipeline E2E test harness + bug fixes + diagnostic analysis
**Build Plan Section**: [09b §9B.6](file:///p:/zorivest/docs/build-plan/09b-pipeline-hardening.md)
**Predecessor**: [120-url-builders-cancellation-corrections](120-2026-04-19-url-builders-cancellation-corrections.md)

---

## Acceptance Criteria

| AC | Description | Source | Test(s) | Status |
|----|-------------|--------|---------|--------|
| AC-1 | 7 test policy fixtures importable | Spec (§9B.6b) | `tests/fixtures/policies.py` | ✅ |
| AC-2 | 6 mock step classes registered | Spec (§9B.6c) | `tests/fixtures/mock_steps.py` | ✅ |
| AC-3 | Mock steps cleaned from registry after session | Spec (§9B.8) | `tests/conftest.py::cleanup_mock_steps` | ✅ |
| AC-4 | Full lifecycle success | Spec (§9B.6d) | `test_create_approve_run_success` | ✅ |
| AC-5 | Unapproved policy rejected | Spec (§9B.6d) | `test_run_unapproved_policy_rejected` | ✅ |
| AC-6 | Delete unschedules | Spec (§9B.6d) | `test_delete_policy_unschedules` | ✅ |
| AC-7 | Steps execute in order | Spec (§9B.6d) | `test_all_steps_execute_in_order` | ✅ |
| AC-8 | Ref resolution across steps | Spec (§9B.6d) | `test_ref_resolution_across_steps` | ✅ |
| AC-9 | Step output persisted to DB | Spec (§9B.6d) | `test_step_output_persisted_to_db` | ✅ |
| AC-10 | fail_pipeline aborts | Spec (§9B.6d) | `test_fail_pipeline_aborts` | ✅ |
| AC-11 | log_and_continue proceeds | Spec (§9B.6d) | `test_log_and_continue_proceeds` | ✅ |
| AC-12 | Dry-run skips side effects | Spec (§9B.6d) | `test_dry_run_skips_side_effects` | ✅ |
| AC-13 | Skip condition evaluated | Spec (§9B.6d) | `test_skip_condition_evaluated` | ✅ |
| AC-14 | Cancel running pipeline | Spec (§9B.6d) | `test_cancel_running_pipeline` | ✅ |
| AC-15 | Cancel idempotent on completed | Spec (§9B.6d) | `test_cancel_idempotent_on_completed` | ✅ |
| AC-16 | Unicode error messages no crash | Spec (§9B.6d) | `test_unicode_error_messages_no_crash` | ✅ |
| AC-17 | Run creates audit entry | Spec (§9B.6d) | `test_run_creates_audit_entry` | ✅ |
| AC-18 | Cancel creates audit entry | Spec (§9B.6d) | `test_cancel_creates_audit_entry` | ✅ |
| AC-19 | Retry exhaustion fails | Spec (§9B.6d) | `test_retry_exhaustion_fails` | ✅ |
| AC-20 | Zombie recovery | Spec (§9B.6d) | `test_startup_zombie_recovery` | ✅ |
| AC-21 | No dual-write records | Spec (§9B.6d) | `test_no_dual_write_records` | ✅ |
| AC-22 | Bytes output serializable | Spec (§9B.6d) | `test_bytes_output_serializable` | ✅ |

<!-- CACHE BOUNDARY -->

---

## Evidence

### Production Bugs Fixed (Beyond Original Scope)

| Bug | Root Cause | Fix | TDD Evidence |
|-----|-----------|-----|-------------|
| **BF-1: PIPE-DEDUP** | `compute_dedup_key()` produced identical keys when `snapshot_hash` absent → 2nd run silently skipped | `send_step.py:124-133` — fallback to `context.run_id` | `test_dedup_key_fallback_to_run_id`: RED→GREEN |
| **BF-2: SMTP security** | `get_smtp_runtime_config()` added `security` key but tests/wiring didn't account for it | Updated 3 test files to include `security` in expected keys | `test_smtp_config_includes_security_field`: RED→GREEN |

**Additional production changes in `send_step.py`** (documented for completeness):
- **First-error surfacing** (L73-96): `StepResult.error` now contains the first delivery error message for UI visibility, not just `PipelineStatus.FAILED` with `error=None`
- **SMTP credential/TLS passthrough** (L118-124, L162-164): `smtp_username`, `smtp_password`, and `security` are extracted from `smtp_config` dict and passed to `send_report_email()` to enable authenticated STARTTLS/SSL connections

### FAIL_TO_PASS Evidence

| Test | Red Output (hash/snippet) | Green Output | File:Line |
|------|--------------------------|--------------|-----------|
| `test_dedup_key_fallback_to_run_id` | `AssertionError: dedup keys identical across runs — both runs produce hash(report_id+channel+recipient+"")` | `1 passed` — distinct keys: `hash(...+run_id_1)` ≠ `hash(...+run_id_2)` | `tests/unit/test_send_step.py:570` |
| `test_smtp_config_includes_security_field` | `AssertionError: 'security' not in {'host', 'port', 'sender', 'username', 'password'}` | `1 passed` — security key present with default `'STARTTLS'` | `tests/unit/test_smtp_runtime_config.py:130` |

### Diagnostic Analysis Reports

| Report | Key Finding | New Issues |
|--------|------------|------------|
| [Template Rendering](file:///p:/zorivest/.agent/context/scheduling/template_rendering_gap_analysis.md) | 3-layer disconnection: `EMAIL_TEMPLATES` unused, `template_engine` unread by SendStep, `body_template` treated as literal | [TEMPLATE-RENDER] |
| [Data Flow](file:///p:/zorivest/.agent/context/scheduling/data_flow_gap_analysis.md) | No real step chain integration test; 48 use cases catalogued (44/48 implemented) | [PIPE-E2E-CHAIN], [PIPE-CACHEUPSERT], [PIPE-CURSORS] |

### Commands Executed

| Command | Exit Code | Key Output |
|---------|-----------|------------|
| `uv run pytest tests/integration/test_pipeline_e2e.py -v` | 0 | 19 passed |
| `uv run pytest tests/ -x --tb=short -q` | 0 | 2087 passed, 15 skipped |
| `uv run pyright packages/` | 0 | 0 errors, 0 warnings |
| `uv run ruff check packages/ tests/` | 0 | 0 errors |
| `uv run python tools/validate_codebase.py --scope meu` | 0 | 8/8 blocking checks passed |

> **Note**: `pyright packages/` (production code only) is the MEU-scoped gate. `pyright packages/ tests/` shows 7 errors in `tests/security/test_encryption_integrity.py` — pre-existing issue related to optional `sqlcipher3` dependency, outside MEU-PW8 scope.

### Quality Gate Results

```
pyright (packages/): 0 errors, 0 warnings
ruff: 0 violations
pytest: 2087 passed, 15 skipped, 0 failed
anti-placeholder: 0 matches
anti-deferral: 0 matches
tsc: 0 errors
eslint: 0 warnings
vitest: all passed
```

---

## Changed Files

| File | Action | Lines | Summary |
|------|--------|-------|---------|
| `tests/fixtures/__init__.py` | new | 1 | Package init |
| `tests/fixtures/policies.py` | new | ~120 | 7 policy dict fixtures |
| `tests/fixtures/mock_steps.py` | new | ~80 | 6 mock step classes |
| `tests/conftest.py` | modified | +40 | Pipeline service stack fixtures + mock cleanup |
| `tests/integration/test_pipeline_e2e.py` | new | ~400 | 19 integration tests across 8 classes |
| `packages/core/src/zorivest_core/pipeline_steps/send_step.py` | modified | 73-165 | Dedup key fallback (L124-133), first-error surfacing (L73-96), SMTP credential/TLS passthrough (L118-124, L162-164) |
| `tests/unit/test_send_step.py` | modified | +30 | Dedup fallback tests |
| `tests/unit/test_smtp_runtime_config.py` | modified | 68-71, 130-137 | Security field in expected keys |
| `tests/integration/test_pipeline_wiring.py` | modified | 45-51 | Security field in SMTP config |
| `.agent/context/known-issues.md` | modified | +38 | 4 new issues from gap analyses |
| `docs/BUILD_PLAN.md` | modified | 332 | MEU-PW8 ⬜→🟡 |

---

## Codex Validation Report

_Left blank for reviewer agent._

---

## History

| Event | Date | Agent | Detail |
|-------|------|-------|--------|
| Created | 2026-04-20 | Claude Opus 4 | Initial handoff |
| Extended | 2026-04-20 | Claude Opus 4 | Added bug fixes + diagnostic analysis |
| Submitted for review | 2026-04-20 | Claude Opus 4 | Sent to GPT-5.4 Codex |
| Corrections applied | 2026-04-20 | Claude Opus 4 | F1: 4 ruff fixes + evidence counts corrected. F2: full send_step.py delta documented. F3: FAIL_TO_PASS section added |
