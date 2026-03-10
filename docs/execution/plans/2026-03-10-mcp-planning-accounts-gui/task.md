# Task — mcp-planning-accounts-gui

> Project: `mcp-planning-accounts-gui` | MEU-36, MEU-37, MEU-40

## MEU-36: Trade Planning Tool

- [x] Write FIC — `rg 'create_trade_plan' docs/execution/plans/2026-03-10-mcp-planning-accounts-gui/implementation-plan.md`
- [x] Write planning-tools.test.ts (RED) — `cd mcp-server && npx vitest run tests/planning-tools.test.ts`
- [x] Implement planning-tools.ts (GREEN) — `cd mcp-server && npx vitest run tests/planning-tools.test.ts`

## MEU-37: Account Tools

- [x] Write FIC — `rg 'sync_broker' docs/execution/plans/2026-03-10-mcp-planning-accounts-gui/implementation-plan.md`
- [x] Write accounts-tools.test.ts (RED) — `cd mcp-server && npx vitest run tests/accounts-tools.test.ts`
- [x] Implement accounts-tools.ts (GREEN) — `cd mcp-server && npx vitest run tests/accounts-tools.test.ts`

## MEU-40: GUI Launch Tool

- [x] Write FIC — `rg 'launch_gui' docs/execution/plans/2026-03-10-mcp-planning-accounts-gui/implementation-plan.md`
- [x] Write gui-tools.test.ts (RED) — `cd mcp-server && npx vitest run tests/gui-tools.test.ts`
- [x] Implement gui-tools.ts (GREEN) — `cd mcp-server && npx vitest run tests/gui-tools.test.ts`

## Integration & Closeout

- [x] Update index.ts + seed.ts — `cd mcp-server && npx tsc --noEmit && npx vitest run`
- [x] Update BUILD_PLAN.md — `rg "MEU-36" docs/BUILD_PLAN.md && rg "MEU-37" docs/BUILD_PLAN.md && rg "MEU-40" docs/BUILD_PLAN.md`
- [x] MEU gate — `uv run python tools/validate_codebase.py --scope meu` *(waiver: Windows FileNotFoundError when spawning npx — tracked environment issue)*
- [x] TypeScript blocking checks — `cd mcp-server && npx tsc --noEmit && npx eslint src/ && npx vitest run && npm run build`
- [x] Python regression — `uv run pytest tests/ -v`
- [x] Create handoffs — `if (!(Test-Path .agent/context/handoffs/040-2026-03-10-planning-tools-bp05ds5d.md)) { throw 'missing 040' }; if (!(Test-Path .agent/context/handoffs/041-2026-03-10-accounts-tools-bp05fs5f.md)) { throw 'missing 041' }; if (!(Test-Path .agent/context/handoffs/042-2026-03-10-gui-tools-bp05s5.10.md)) { throw 'missing 042' }`
- [x] Update MEU registry — `rg "MEU-36" .agent/context/meu-registry.md && rg "MEU-37" .agent/context/meu-registry.md && rg "MEU-40" .agent/context/meu-registry.md`
- [x] Create reflection (from `docs/execution/reflections/TEMPLATE.md`) — `if (!(Test-Path docs/execution/reflections/2026-03-10-mcp-planning-accounts-gui-reflection.md)) { throw 'missing reflection' }`
- [x] Update metrics.md — `cd mcp-server; npx vitest run 2>&1; cd ..; rg "test" docs/execution/metrics.md`
- [x] Prepare commit messages — `rg "commit" .agent/context/handoffs/040-2026-03-10-planning-tools-bp05ds5d.md`
