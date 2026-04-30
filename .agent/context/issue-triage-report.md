# Known Issue Triage Report — 2026-04-30

## Summary
- Total issues reviewed: 14
- Archived in Step 1: 2 (`[MCP-TOOLAUDIT]`, `[TRADE-CASCADE]`)
- Remaining active: 12
- Actionable (new/expanded MEUs): 2
- Upstream/deferred: 2
- Architecture decisions needed: 0 (resolved during triage)
- Workaround-OK (no action): 5
- Blocked: 1
- Tech debt: 2

## Archival Actions Performed (Step 1)

Issues verified as resolved and moved to `known-issues-archive.md`:

1. **[MCP-TOOLAUDIT]** — ✅ Audit PASS (46 tested, 44 pass, 0 fail). All 4 critical review findings (F1–F4) resolved in P2.5f. Remaining items are informational (provider API key config, low-priority `delete_watchlist` gap). **Verification:** Confirmed CompoundToolRouter + 18 compound tool files in `mcp-server/src/compound/`.

2. **[TRADE-CASCADE]** — ✅ Resolved 2026-04-29. Cascade delete for trades with linked reports/images. **Verification:** `cascade="all, delete-orphan"` confirmed in `models.py`, `delete_for_owner()` confirmed in `ports.py` + `repositories.py`, cleanup logic in `trade_service.py`. 4 regression tests (2 integration, 2 unit).

## Classification Table (Active Issues)

| Issue ID | Severity | Component | Classification | Target | Priority | Notes |
|----------|----------|-----------|---------------|--------|----------|-------|
| STUB-RETIRE | Low | api | `BLOCKED` | MEU-104–116, MEU-110, MEU-123–126 | — | Stubs retire when real services are implemented |
| MCP-TOOLDISCOVERY | Medium | mcp-server | `MEU-EXPAND` | MEU-TD1 `mcp-tool-discovery-audit` | P3 | Already planned ⬜, build-plan item 5.I |
| MCP-TOOLCAP | Critical | mcp-server | `WORKAROUND-OK` | — | — | Three-tier + 85→13 consolidation resolved. Permanent design. |
| MCP-ZODSTRIP | Critical | mcp-server | `UPSTREAM` | TS-SDK #1291, #1380, PR #1603 | — | Raw shape workaround stable. Monitor SDK releases. |
| MCP-AUTHRACE | Critical | mcp-server | `MEU-NEW` | New MEU in 05-mcp-server.md | P1 | Architecture decided 2026-04-30: singleton TokenRefreshManager |
| MCP-WINDETACH | Critical | infrastructure | `UPSTREAM` | Node.js #5146, #36808 | — | Windows Job Objects workaround. 10-year upstream bug. |
| MCP-HTTPBROKEN | High | mcp-server | `WORKAROUND-OK` | — | — | stdio primary transport. HTTP avoided by design. |
| MCP-DIST-REBUILD | High | mcp-server | `WORKAROUND-OK` | — | — | By design. `npm run build` after src changes. |
| UI-ESMSTORE | Medium | ui | `WORKAROUND-OK` | — | — | Pinned to `electron-store@8`. Stable. |
| E2E-AXEELECTRON | High | ui (E2E) | `WORKAROUND-OK` | — | — | `file://` URL + `page.evaluate()`. Working in 5 test files. |
| E2E-AXESILENT | Medium | ui (E2E) | `TECH-DEBT` | — | P4 | Low impact. Add structured try/catch pattern. |
| E2E-ELECTRONLAUNCH | High | ui (E2E) | `TECH-DEBT` | — | P3 | CI needs `xvfb-run`. Resolution path clear. |

## Recommended Project Batches

### Batch 1: `mcp-discoverability-audit` — Priority P3

- **Issues addressed**: [MCP-TOOLDISCOVERY]
- **Expanded MEUs**: MEU-TD1 — full audit of all 13 compound tool descriptions; enrich with workflow context, `policy_json` examples, resource references, prerequisite state, return shapes, error conditions
- **Build-plan section**: `docs/build-plan/05-mcp-server.md` §5.11+ (build-priority-matrix item 5.I)
- **Complexity**: M (audit 13 compound tools, rewrite descriptions, add examples)
- **Dependencies**: P2.5f consolidation complete ✅. No blocking dependencies.
- **Next step**: Invoke `/create-plan` with MEU-TD1 scope

### Batch 2: `e2e-ci-hardening` — Priority P3-P4

- **Issues addressed**: [E2E-ELECTRONLAUNCH], [E2E-AXESILENT]
- **New MEUs**: Potential new MEU for CI pipeline E2E infrastructure
  - `xvfb-run` integration for headless CI environments
  - Structured error handling for accessibility scanner crashes
- **Build-plan section**: Could extend `docs/build-plan/testing-strategy.md` or create CI-specific section
- **Complexity**: S
- **Dependencies**: None. Independent of feature work.
- **Next step**: Determine if this justifies a standalone MEU or can be folded into an existing CI/testing MEU

## Architecture Decisions Required

Issues needing human/ADR resolution before MEU scoping:

- **[MCP-AUTHRACE]** — Token refresh race condition under concurrent tool execution
  - **Decision needed**: How to architecturally prevent race conditions when multiple MCP tools trigger token refresh simultaneously
  - **Option A**: In-process mutex with proactive JWT expiry check (simple, current partial workaround direction). Single-threaded Node.js event loop makes this viable. Pre-refresh 30s before expiry to avoid concurrent triggers.
  - **Option B**: Dedicated token service / singleton refresh manager that queues refresh requests and deduplicates them. More complex but more robust for future multi-instance scenarios.
  - **Option C**: Short-lived session tokens with MCP-level caching. Avoids refresh entirely during a session but requires reconnection handling.
  - **Recommendation**: **Option A** — simplest, fits the current single-instance architecture (Zorivest is a local desktop app). The "in-memory mutex" described in the issue workaround is the right direction; it just needs to be formally implemented and tested. Upgrade to Option B only if multi-instance deployment becomes a requirement.
  - **Priority**: P1 — Critical severity, but standalone (doesn't block other MEUs). Should be addressed before any auth-dependent MCP features ship to production users.

## No Action Required

Issues classified as UPSTREAM, WORKAROUND-OK, or BLOCKED:

| Issue ID | Classification | Rationale |
|----------|---------------|-----------|
| STUB-RETIRE | `BLOCKED` | Stubs retire naturally when real services (Analytics, Review, Tax) are implemented in their respective MEUs. No standalone work needed. |
| MCP-TOOLCAP | `WORKAROUND-OK` | P2.5f consolidation (85→13 tools) permanently resolved the IDE limit problem. Three-tier strategy remains as architectural insurance. |
| MCP-ZODSTRIP | `UPSTREAM` | SDK bug in `@modelcontextprotocol/sdk`. Raw shape workaround is stable. Monitor TS-SDK PR #1603 for upstream fix. |
| MCP-WINDETACH | `UPSTREAM` | Node.js bug open since 2016. Windows Job Objects workaround in place. No local fix possible. |
| MCP-HTTPBROKEN | `WORKAROUND-OK` | stdio is the primary transport by design. HTTP transport risks documented and avoided. |
| MCP-DIST-REBUILD | `WORKAROUND-OK` | Operational pattern (build before run) is inherent to compiled TypeScript. Not fixable; documented for developer awareness. |
| UI-ESMSTORE | `WORKAROUND-OK` | `electron-store@8` pin is stable. Upgrade path depends on electron-vite adding ESM support. |
| E2E-AXEELECTRON | `WORKAROUND-OK` | `file://` URL pattern works reliably in all 5 E2E test files. Revisit if `@axe-core/playwright` adds Electron support. |
