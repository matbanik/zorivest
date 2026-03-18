# Handoff 076 — Scheduling Guardrails (MEU-90)

> Date: 2026-03-18
> Phase: 9 (§9.9)
> Status: ✅ Complete

## Scope

Pipeline guardrail service with 4 rate-limit/approval checks:
- `check_can_create_policy()` — policy creation rate limit
- `check_can_execute()` — execution rate limit
- `check_policy_approved()` — approval + hash integrity verification
- `check_can_send_email()` — email send rate limit

## Files Created

| File | Purpose |
|------|---------|
| `packages/core/src/zorivest_core/services/pipeline_guardrails.py` | `PipelineRateLimits` dataclass + `PipelineGuardrails` class with Protocol-based `AuditCounter` + `PolicyLookup` |
| `tests/unit/test_pipeline_guardrails.py` | 16 unit tests covering all 4 check methods |

## Architecture Decisions

- **Protocol-based ports**: `AuditCounter` for time-window queries, `PolicyLookup` for approval lookups — no direct DB dependency
- **`PipelineRateLimits` dataclass**: configurable limits (`max_policy_creates_per_day=20`, `max_pipeline_executions_per_hour=60`, `max_emails_per_day=50`, `max_report_queries_per_hour=100`) with sensible defaults

## Evidence

```
uv run pytest tests/unit/test_pipeline_guardrails.py -v
# 16 passed
```
