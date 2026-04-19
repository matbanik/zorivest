# Reflection — URL Builders + Pipeline Cancellation

**Date:** 2026-04-19
**MEUs:** MEU-PW6 (URL Builders), MEU-PW7 (Pipeline Cancellation)
**Duration:** ~1 session

## What Went Well

1. **TDD discipline held** — All 37 tests written first (Red), then implementation made them pass (Green). No test assertions were modified during Green phase.
2. **Registry pattern choice** — The `get_url_builder()` factory with protocol-based builders is clean and extensible. Adding a new provider requires only a new class + one dict entry.
3. **Boundary validation worked correctly** — The `Path(..., pattern=UUID_REGEX)` approach for the cancel endpoint produces proper 422 responses for malformed UUIDs.

## What Surprised Me

1. **`from __future__ import annotations` breaks FastAPI Path type inference** — Using `run_id: uuid.UUID` as a type hint doesn't work when PEP 604 annotations are enabled because the type becomes a string at runtime. Had to fall back to `Path(pattern=...)` with a regex. This is a known FastAPI issue but still caught me off guard.
2. **Test fixture async gaps** — The `audit_logger.log` mock needed `AsyncMock` since it's `await`ed. Quick fixture fix, not a test assertion change.

## What I'd Do Differently

1. **Start with the `__future__ annotations` constraint in mind** — Could have avoided the UUID type hint detour by checking the existing module's import style first.
2. **Adapter refactor should be its own MEU** — Tasks 3-4 (wiring builders into adapter) are integration work with different testing infrastructure needs. They don't belong in the same MEU as the builder registry.

## Emerging Standards

- **G20**: When using `from __future__ import annotations`, FastAPI path parameters must use `Path(pattern=...)` for validation instead of type hints like `uuid.UUID`.
