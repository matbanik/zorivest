# Task — mcp-guard-metrics-discovery

> Project: MEU-39, MEU-38, MEU-41 | Date: 2026-03-09

## MEU-39: Performance Metrics Middleware

- [x] Write metrics.test.ts (RED phase — tests codify FIC AC-1 through AC-8)
- [x] Implement `mcp-server/src/middleware/metrics.ts` (GREEN phase)
- [x] Replace stub metricsCollector in diagnostics-tools.ts with real import (AC-9)
- [x] Verify diagnostics tests still pass after import swap

## MEU-38: MCP Guard Middleware

- [x] Write guard.test.ts (RED phase — tests codify FIC AC-1 through AC-5)
- [x] Implement `mcp-server/src/middleware/mcp-guard.ts` (GREEN phase)

## MEU-38+39: Middleware Composition Proof

- [x] Wire `withMetrics(withGuard(handler))` on at least one registered tool
- [x] Write composition test proving both middleware layers execute (AC-10)

## MEU-41: Discovery Meta-Tools

- [x] Implement `mcp-server/src/toolsets/registry.ts` (ToolsetRegistry class — data structure only)
- [x] Write discovery-tools.test.ts (RED phase — tests codify FIC AC-1 through AC-11)
- [x] Implement `mcp-server/src/tools/discovery-tools.ts` (GREEN phase — 4 tools)
  - `get_confirmation_token` uses flat payload `{ token, action, params_summary, expires_in_seconds, instruction }`
  - `get_confirmation_token` returns isError for non-destructive/unknown actions
  - `enable_toolset` blocked when MCP Guard is locked (testing-strategy L374)
- [x] Wire discovery tools into `mcp-server/src/index.ts`

## Verification

- [x] `cd mcp-server && npx tsc --noEmit` — clean TypeScript compilation
- [x] `cd mcp-server && npm run lint` — 2 warnings (expected for composition `as any` in trade-tools.ts)
- [x] `cd mcp-server && npm run build` — clean production build
- [x] `cd mcp-server && npx vitest run` — all MCP tests pass (74/74, 9 files)
- [x] `uv run pytest tests/ -v` — full Python regression passes (648 passed, 1 skipped)
- [x] MEU gate: `uv run python tools/validate_codebase.py --scope meu` — 3/8 pass (Python checks), step 4 fails with Windows npx spawn (documented waiver)

## Post-MEU Deliverables

- [ ] Codex validation handoff (reviewer)
- [x] Create handoff: `037-2026-03-09-mcp-perf-metrics-bp05s5.9.md`
- [x] Create handoff: `038-2026-03-09-mcp-guard-bp05s5.6.md`
- [x] Create handoff: `039-2026-03-09-mcp-discovery-bp05js5j.md`
- [x] Update `docs/BUILD_PLAN.md` — MEU-38, 39, 41 status
- [x] Update `.agent/context/meu-registry.md` — MEU-38, 39, 41 status
- [x] Create reflection at `docs/execution/reflections/` — 2026-03-09-mcp-guard-metrics-discovery-reflection.md
- [x] Update metrics table at `docs/execution/metrics.md` — MEU-38/39/41 row appended
- [x] Save session state to pomera_notes — Memory/Session/mcp-guard-metrics-discovery-2026-03-09
- [x] Propose commit messages — feat(mcp-server): guard, metrics, discovery
