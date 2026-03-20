# GUI Core P0 Completion — Reflection

**Date:** 2026-03-19 to 2026-03-20
**MEUs:** 46a, 50, 51
**Review Passes:** 2 (initial review + recheck)

## What Went Well

- Batch execution of 3 related MEUs reduced context-switching overhead
- MCP-REST proxy pattern (MEU-46a) was clean: 2 endpoints, manifest-based, graceful fallback
- TanStack Query + REST settings API is a solid persistence pattern that avoids Electron IPC complexity

## What Didn't Go Well

1. **Route restoration had a subtle async race**: `usePersistedState` uses `initialData` which makes `isLoading` always `false` from first render. Took 2 correction passes to discover the root cause (need `isFetching`, not `isLoading`).
2. **electron-store version references were inconsistently copied**: The `[UI-ESMSTORE]` scope cut note was copied to 4 files with an incorrect version claim (`@8 has ESM issues` instead of `v9+ is ESM-only`). Canon from `known-issues.md` was not consulted.
3. **Missing test coverage was accepted initially**: Route restoration and theme persistence were checked off without tests, which let the async bug survive undetected.

## Lessons Learned

- **`initialData` makes `isLoading` useless**: When TanStack Query has `initialData`, the query is never in "loading" state. Use `isFetching` to detect active background fetches.
- **Cross-reference canon before writing justification notes**: Any scope-cut justification that cites a known issue should be verified against `known-issues.md` before committing.
- **Tests are the only reliable evidence for async hooks**: Async React hooks have subtle timing behaviors that manual verification can't catch. Write tests first.

## Process Improvement

- Added **P1 — Paginated Responses Must Return Real DB Count** to `emerging-standards.md` with a full 6-layer implementation template.
- The `isLoading` vs `isFetching` distinction should be added to `known-issues.md` as a TanStack Query pitfall.

## Metrics

- Total files changed: ~15
- Tests added: 10 (5 route restoration + 5 theme)
- Tests total (UI): 133 (was 123)
- Review findings resolved: 9 (5 from pass 1 + 4 from recheck)
