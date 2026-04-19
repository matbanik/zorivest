---
seq: 116
date: "2026-04-19"
meu: "MEU-PW4"
slug: "charmap-fix"
build_plan_ref: "09b §9B.2"
verbosity: "standard"
---

# Handoff: MEU-PW4 — Pipeline Charmap Fix

> **Status:** ✅ Complete
> **Build Plan:** `docs/build-plan/09b-pipeline-hardening.md` §9B.2
> **Matrix Position:** 49.7

## Summary

Fixed `[PIPE-CHARMAP]`: Windows `cp1252` encoding crash in pipeline logging. Structlog now outputs UTF-8 on Windows, and `_persist_step()` uses bytes-safe JSON serialization.

## Changed Files

| File | Change |
|------|--------|
| `packages/api/src/zorivest_api/logging_config.py` | **[NEW]** `configure_structlog_utf8()` — reconfigures stderr to UTF-8, wires UnicodeDecoder processor |
| `packages/core/src/zorivest_core/services/pipeline_runner.py` | Added `_safe_json_output()` — bytes→base64, datetime→isoformat fallback serializer |
| `packages/api/src/zorivest_api/main.py` | Wired `configure_structlog_utf8()` call in lifespan startup |
| `tests/unit/test_structlog_utf8.py` | **[NEW]** 14 tests covering AC-1 through AC-6 + renderer selection, safe_json edge cases, persist_step bytes handling |

## Acceptance Criteria Evidence

| AC | Description | Evidence |
|----|-------------|----------|
| AC-1 | `configure_structlog_utf8()` sets stderr encoding to UTF-8 | `test_AC1_reconfigure_stderr_utf8` ✅ |
| AC-2 | UnicodeDecoder processor in chain | `test_AC2_unicode_decoder_in_processors` ✅ |
| AC-3 | Called once in lifespan startup | Wired in `main.py` lifespan, verified by import test |
| AC-4 | `_safe_json_output()` handles bytes→base64 | `test_AC4_safe_json_handles_bytes` ✅ |
| AC-5 | `_safe_json_output()` handles datetime→ISO | `test_AC5_safe_json_handles_datetime` ✅ |
| AC-6 | Non-ASCII log messages don't crash | `test_AC6_non_ascii_log_no_crash` ✅ |

## Quality Gate

- **pyright:** 0 errors
- **ruff:** All checks passed
- **pytest:** 14/14 PW4 tests pass; 2026 total passed
