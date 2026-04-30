---
project: 2026-04-29-mcp-consolidation
meu: MC1
status: complete
date: 2026-04-29
verbosity: standard
---

# MC1 Handoff — zorivest_system Compound Tool

## Summary

MC1 implemented the `CompoundToolRouter` infrastructure and the `zorivest_system` compound tool, consolidating 9 individual MCP tools into a single tool with strict Zod validation per action. All tests pass, type checks clean, build succeeds.

## Deliverables

| # | Task | Status | Evidence |
|---|------|--------|----------|
| 5 | CompoundToolRouter | ✅ | 8/8 tests pass (`tests/compound/router.test.ts`) |
| 6 | zorivest_system (9 actions) | ✅ | 9/9 tests pass (`tests/compound/system-tool.test.ts`) |
| 7 | Tool count = 77 | ✅ | Count gate test pass (AC-1.6) |
| 8 | Clean build | ✅ | `npm run build` — 0 errors |

## Changed Files

```diff
# New files
+ mcp-server/src/compound/router.ts          # CompoundToolRouter class
+ mcp-server/src/compound/system-tool.ts      # zorivest_system (9 actions)
+ mcp-server/src/compound/index.ts            # barrel export
+ mcp-server/tests/compound/router.test.ts    # 8 unit tests
+ mcp-server/tests/compound/system-tool.test.ts  # 10 integration tests

# Modified files
~ mcp-server/src/toolsets/seed.ts             # core→compound, discovery removed
~ mcp-server/src/tools/scheduling-tools.ts    # get_email_config removed
~ mcp-server/tests/scheduling-tools.test.ts   # count 9→8
~ mcp-server/tests/scheduling-gap-fill.test.ts # email_config assertions updated
```

## Quality Gates

- **vitest**: 25 files, 275 tests, 0 failures
- **tsc --noEmit**: 0 errors
- **npm run build**: clean

## Tool Count Trace

| Metric | Value |
|--------|-------|
| Pre-MC1 | 85 registered tools |
| Removed | 9 (settings×2, diag, gui, discovery×4, email_config) |
| Added | 1 (zorivest_system) |
| Post-MC1 | **77** (verified by count gate test) |

## Design Decisions

1. **`ToolResult` aliased to SDK `CallToolResult`**: Avoids index-signature incompatibility between custom interface and registerTool handler return type.
2. **Router strips `action` before per-action validation**: Each sub-action schema only validates its own fields, keeping schema contracts isolated.
3. **Old register functions kept intact**: Source files (`diagnostics-tools.ts`, `settings-tools.ts`, etc.) still export working register functions — they're just no longer called from `seed.ts`. This preserves existing tests.

## Next Steps (MC2)

- Create `zorivest_trade` (6 actions from `trade-tools.ts`)
- Create `zorivest_report` (2 actions from `analytics-tools.ts`)
- Create `zorivest_analytics` (13 actions from `analytics-tools.ts`)
- Remove 21 old registrations → target count: 56
