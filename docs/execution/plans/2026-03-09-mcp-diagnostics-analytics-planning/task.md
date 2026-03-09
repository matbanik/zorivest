# Task — mcp-diagnostics-analytics-planning

> Project: `mcp-diagnostics-analytics-planning` | MEUs: 34, 35 | Date: 2026-03-09
>
> MEU-36 deferred (draft spec + P2 REST). Report tools deferred (P1 REST).

## MEU-34: mcp-diagnostics

- [x] Write `diagnostics-tools.ts` with `zorivest_diagnose` tool (safe-fetch, stub metrics, partial-availability)
- [x] Write `diagnostics-tools.test.ts` (7 tests: reachable, unreachable, no-key-leak, providers-404, verbose, summary, unauth-partial)
- [x] Register `registerDiagnosticsTools()` in `index.ts`
- [x] Verify: `cd mcp-server && npx vitest run tests/diagnostics-tools.test.ts` green
- [~] MEU gate: `uv run python tools/validate_codebase.py --scope meu` — **WAIVED**: `FileNotFoundError: [WinError 2]` spawning `npx tsc --noEmit`. `tsc --noEmit` passes directly. Infra blocker, not code defect.
- [x] Create handoff `035-2026-03-09-mcp-diagnostics-bp05bs5b.md`

## MEU-35: mcp-trade-analytics

- [x] Write `analytics-tools.ts` with 12 analytics tools
- [x] Write `analytics-tools.test.ts` (12+ tests: one per tool endpoint/param/envelope)
- [x] Register `registerAnalyticsTools()` in `index.ts`
- [x] Verify: `cd mcp-server && npx vitest run tests/analytics-tools.test.ts` green
- [~] MEU gate: `uv run python tools/validate_codebase.py --scope meu` — **WAIVED**: same infra blocker as MEU-34.
- [x] Create handoff `036-2026-03-09-mcp-trade-analytics-bp05cs5c.md`

## Post-Project

- [x] Update `docs/BUILD_PLAN.md` + `meu-registry.md`: MEU-34/35 → 🔄 ready_for_review (MEU-36 stays ⬜)
- [x] Full regression: `cd mcp-server && npx vitest run` — 39 tests, 6 files, all green
- [x] Create reflection file at `docs/execution/reflections/`
- [x] Review deliverables (reviewer role) — `ready_for_review` verdict after 4 passes, 9 findings resolved
- [x] Save session + propose commit messages — pomera note #387 updated
