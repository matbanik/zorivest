---
project: approval-security
date: "2026-04-27"
meus: [PH11, PH12, PH13]
status: complete
verbosity: standard
---
<!-- CACHE BOUNDARY -->

# Approval Security — Handoff

## Summary

All 3 MEUs (PH11, PH12, PH13) are complete with 8/8 MEU gate passes each. Full test suite: 2395 passed, 23 skipped.

## Changed Files

### PH11: Approval CSRF Token
```diff
# ui/src/main/approval-token-manager.ts
+ generateApprovalToken() — 64-char hex, 5min TTL, single-use, policy-scoped
+ validateApprovalToken() — consume + expiry + scope checks
+ startCleanupInterval() — periodic expired token cleanup
+ Runtime type guards: non-string/empty policyId/token → TypeError

# ui/src/main/index.ts
+ IPC handler: generate-approval-token
+ Internal HTTP server: /internal/validate-token (127.0.0.1 only)
+ Boundary validation: extra-field rejection, type checks

# packages/api/src/zorivest_api/middleware/approval_token.py (NEW)
+ ApprovalTokenMiddleware — validates X-Approval-Token header
+ ApprovalTokenValidator — callback to Electron validation server

# packages/api/src/zorivest_api/main.py
~ Wired ApprovalTokenValidator into app.state via ZORIVEST_APPROVAL_CALLBACK_PORT
~ Wired email_config_checker into PolicyEmulator from EmailProviderService

# ui/src/main/__tests__/approval-token-manager.test.ts (NEW)
+ 9 tests: AC-1 through AC-4, AC-8, boundary validation (Finding #3)

# ui/src/renderer/src/features/scheduling/__tests__/approval-flow.test.tsx (NEW)
+ 2 tests: IPC call + header injection, null token rejection
```

```diff
# mcp-server/src/tools/scheduling-tools.ts
+ delete_policy tool (z.object().strict(), withConfirmation, confirmation_token)
+ update_policy tool (z.object().strict(), policy_id + policy_json)
+ get_email_config tool (read-only, SMTP status via API)

# mcp-server/src/middleware/confirmation.ts
+ "delete_policy" added to DESTRUCTIVE_TOOLS set

# mcp-server/src/toolsets/seed.ts
+ 3 new tools in scheduling toolset (6→9)

# mcp-server/tests/scheduling-gap-fill.test.ts (NEW)
+ 9 tests: schema validation, annotations, strict mode, descriptions

# mcp-server/tests/scheduling-tools.test.ts
~ Updated tool count assertions (6→9)
```

### PH12: Email Status Endpoint
```diff
# packages/api/src/zorivest_api/routes/email_settings.py
+ EmailStatusResponse model
+ GET /settings/email/status endpoint (AC-20)

# openapi.committed.json
~ Regenerated with new endpoint
```

### PH13: Emulator Validate Hardening
```diff
# packages/core/src/zorivest_core/services/policy_emulator.py
+ email_config_checker param (Callable[[], bool] | None)
+ EXPLAIN SQL schema check (SQL_SCHEMA_ERROR)
+ SMTP readiness check (SMTP_NOT_CONFIGURED)
+ Step wiring validation (STEP_WIRING_ERROR)

# packages/core/src/zorivest_core/domain/emulator_models.py
~ Updated error_type field description with 3 new types

# tests/unit/test_emulator_validate_hardening.py (NEW)
+ 8 tests: AC-26 through AC-33
```

## Test Evidence

| Suite | Result |
|-------|--------|
| scheduling-gap-fill.test.ts | 9 passed |
| scheduling-tools.test.ts | 7 passed |
| test_emulator_validate_hardening.py | 8 passed |
| test_policy_emulator.py (regression) | 12 passed |
| Full Python suite | 2395 passed, 23 skipped |
| MEU gate PH12 | 8/8 PASS |
| MEU gate PH13 | 8/8 PASS |
| tsc --noEmit | clean |
| MCP build | 74 tools, 10 toolsets |
| OpenAPI spec | regenerated |
| Anti-placeholder | clean |

## FAIL_TO_PASS Evidence

| Finding | Test | RED Output | GREEN Output |
|---------|------|------------|-------------|
| #1 (High) | `test_app_state_emulator_has_email_checker` | `AssertionError: _email_config_checker is None` | PASSED |
| #1 (High) | `test_app_state_emulator_checker_returns_bool` | (blocked by #1) | PASSED |
| #2 (Med) | `test_local_file_send_without_smtp_no_error` | `AssertionError: local_file send steps must not trigger SMTP validation` | PASSED |
| #2 (Med) | `test_mixed_channels_only_email_triggers_smtp_check` | (blocked by #2) | PASSED |
| #3 (Med) | `rejects non-string policyId in generateApprovalToken` | `AssertionError: expected to throw` | PASSED |
| #3 (Med) | `rejects empty string policyId in generateApprovalToken` | `AssertionError: expected to throw` | PASSED |
| #3 (Med) | `rejects non-string token in validateApprovalToken` | `AssertionError: expected to throw` | PASSED |
| #3 (Med) | `rejects non-string policyId in validateApprovalToken` | `AssertionError: expected to throw` | PASSED |

## Commands run / Commands Executed

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_emulator_validate_hardening.py -x --tb=short -v` | 12 passed |
| `npx vitest run src/main/__tests__/approval-token-manager.test.ts` | 17 passed |
| `uv run pytest tests/ -x --tb=short -q` | 2395 passed, 23 skipped |
| `uv run pyright packages/` | 0 errors |
| `uv run ruff check packages/` | All checks passed |
| `cd ui; npx tsc --noEmit` | clean |

## Decisions

1. **email_config_checker is optional** (`None` default) for backward compatibility with existing emulator instantiation sites.
2. **z.object().strict()** used for MCP tool schemas (not field-level Zod properties) — tests access `.shape` for field validation.
3. **Schema version 2** required for query-step test policies due to PolicyDocument model_validator.
4. **Abstract NotImplementedError** in `step_registry.py` is accepted (L88) — standard Python ABC pattern, not a placeholder.

## Risks / Known Issues

1. **HTTP callback extra-field rejection is hard reject (400)**: Future API versions adding fields to the callback body will need to update `index.ts` allowedKeys set. This is a strict-by-default choice per AGENTS.md boundary input contract.
2. **email_config_checker queries DB on every emulator run**: The checker calls `EmailProviderService.get_config()` which opens a UoW. For high-frequency emulator usage, a cached checker with TTL could be considered. Current usage (manual emulation) does not warrant this.
