# Reflection: Market Data Service + API + MCP Tools

**Date:** 2026-03-11
**MEUs:** 61, 63, 64
**Project:** `market-data-service-api-mcp`

## What Went Well

- **Normalizer registration pattern** — Constructor injection for normalizers keeps core layer clean and testable.
- **Stub service pattern** — `StubMarketDataService`/`StubProviderConnectionService` followed the established `stubs.py` pattern perfectly.
- **MCP tool corrections** — Replacing `configure_market_provider` → `disconnect_market_provider` and fixing `name` → `provider_name` aligned the implementation with the canonical spec.

## What Needed Correction (4 Rounds)

| Round | Key Fix | Root Cause |
|-------|---------|------------|
| 1 | AV search normalizer, core→infra violation, MCP tool name swap | Implementation diverged from spec |
| 2 | `name`→`provider_name`, `readOnlyHint`, BUILD_PLAN sync | Spec details missed in initial pass |
| 3 | Stub services replacing `None` | Pattern mismatch vs other services |
| 4 | TS2353 `@ts-expect-error`, closeout artifacts | Gate failure + incomplete deliverables |

## Lessons Learned

1. **Verify service construction pattern before commit** — All services in `main.py` use stubs; market data services shouldn't have been `None`.
2. **Check spec field names** — `name` vs `provider_name` is exactly the kind of detail that spec-first TDD should catch.
3. **Suppress known TS errors per-file** — `@ts-expect-error` with reason comment is better than a codebase-wide waiver.

## Rules Adherence (85%)

- ✅ TDD-first (tests written before implementation)
- ✅ No `TODO`/`FIXME` left behind
- ✅ Constructor injection for normalizers
- ✅ Handoff template fields complete
- ⚠️ Spec field names not verified against canonical docs before initial implementation
- ⚠️ Closeout artifacts deferred across multiple rounds
