# Known Issue Triage Report — 2026-04-30

## Summary
- Total issues reviewed: 9
- Archived in Step 1: 0
- Remaining active: 9
- Actionable (new/expanded MEUs): 0
- Upstream/deferred: 3
- Workaround-sufficient: 3
- Blocked on future work: 2
- Technical debt (low priority): 1
- Architecture decisions needed: 0

## Archival Actions Performed (Step 1)

No issues qualified for archival. All 9 were verified against the codebase:

| Issue ID | Verification Method | Result |
|----------|-------------------|--------|
| STUB-RETIRE | `rg StubAnalyticsService/StubReviewService/StubTaxService` in packages/ | All 3 stubs still active in stubs.py + main.py |
| MCP-ZODSTRIP | `rg z.object` in mcp-server/src/ | 18 files use z.object — raw shape workaround in place |
| MCP-WINDETACH | `rg detached` in ui/src/ | No matches — Windows Job Objects workaround confirmed |
| MCP-HTTPBROKEN | `rg stdio` in mcp-server/src/ | StdioServerTransport confirmed as sole transport |
| MCP-DIST-REBUILD | Architectural review | By-design — TypeScript compilation required |
| UI-ESMSTORE | `rg electron-store` in ui/package.json | Pinned to `^8.2.0` (CJS) |
| E2E-AXEELECTRON | `rg axe-core` in ui/ | 5 E2E test files use file:// workaround |
| E2E-AXESILENT | Process awareness issue | No code fix possible |
| E2E-ELECTRONLAUNCH | Environment-specific | E2E verified locally; CI resolution known but unimplemented |

## Classification Table (Active Issues)

| Issue ID | Severity | Component | Classification | Target | Priority | Notes |
|----------|----------|-----------|---------------|--------|----------|-------|
| STUB-RETIRE | Low | api | `BLOCKED` | MEU-104–116, MEU-110, MEU-123–126 | P4 | Stubs retire when analytics/review/tax services are implemented (P2.75/P3) |
| MCP-ZODSTRIP | Critical | mcp-server | `UPSTREAM` | TS-SDK #1291, #1380, PR #1603 | N/A | Raw shape convention workaround is stable |
| MCP-WINDETACH | Critical | infrastructure | `UPSTREAM` | Node.js #5146, #36808 | N/A | Windows Job Objects workaround in place |
| MCP-HTTPBROKEN | High | mcp-server | `WORKAROUND-OK` | — | N/A | Design decision: stdio-only transport |
| MCP-DIST-REBUILD | High | mcp-server | `WORKAROUND-OK` | — | N/A | By-design: `npm run build` before IDE restart |
| UI-ESMSTORE | Medium | ui | `UPSTREAM` | electron-store maintainer | N/A | Pinned to v8 (last CJS version) |
| E2E-AXEELECTRON | High | ui (E2E) | `WORKAROUND-OK` | — | N/A | file:// URL + page.evaluate() workaround functional |
| E2E-AXESILENT | Medium | ui (E2E) | `TECH-DEBT` | — | P4 | Wrap axe scans in error handling + "scan completed" assertion |
| E2E-ELECTRONLAUNCH | High | ui (E2E) | `BLOCKED` | CI infrastructure | P3 | xvfb-run resolution path known but unimplemented |

## Recommended Project Batches

**No project batches recommended.** All 9 active issues are classified as upstream, workaround-sufficient, blocked, or low-priority tech debt. None require immediate MEU creation or expansion.

## Architecture Decisions Required

None.

## No Action Required

| Issue ID | Classification | Rationale |
|----------|---------------|-----------|
| STUB-RETIRE | BLOCKED | Stubs retire naturally when analytics (MEU-104–116), review (MEU-110), and tax (MEU-123–126) services are implemented in P2.75/P3 phases |
| MCP-ZODSTRIP | UPSTREAM | TS-SDK bug (#1291, #1380). Raw shape convention workaround is stable and verified. Track upstream progress. |
| MCP-WINDETACH | UPSTREAM | Node.js bug (#5146, #36808) open since 2016. Windows Job Objects workaround is permanent. No local fix possible. |
| MCP-HTTPBROKEN | WORKAROUND-OK | Intentional design decision to use stdio transport exclusively. HTTP transport failure modes are irrelevant to Zorivest's architecture. |
| MCP-DIST-REBUILD | WORKAROUND-OK | TypeScript MCP server inherently requires compilation. The documented `npm run build` workflow is the expected developer experience. Could be addressed by watch mode in P2.6. |
| UI-ESMSTORE | UPSTREAM | electron-store v9+ is ESM-only, incompatible with electron-vite CJS main process. Pin to v8 is stable. Track when electron-vite adds full ESM support. |
| E2E-AXEELECTRON | WORKAROUND-OK | The file:// URL + page.evaluate() workaround achieves identical accessibility scanning results. No loss of functionality. |
| E2E-AXESILENT | TECH-DEBT | Low-severity cleanup. Could batch with other E2E test improvements in a future debt-reduction project. |
| E2E-ELECTRONLAUNCH | BLOCKED | Resolution path (xvfb-run) is known but blocked on CI infrastructure setup. E2E tests work locally. Will be addressed when CI hardening work begins. |

## Observations

### known-issues.md Health
- **Line count:** 122 (target: < 100) — slightly over but no issues can be pruned
- **Archive health:** 41 entries properly archived with resolution dates
- **No premature archival detected** in known-issues-archive.md

### Build Plan Next Steps
Per `current-focus.md`, the project is at a natural transition point after MEU-PH14 completion. The next logical work items from `build-priority-matrix.md` are:
1. **P2:** MEU-171 `dashboard-service` + MEU-172 `gui-home-dashboard` (both ⬜ planned)
2. **P2.5:** MEU-174 `websocket-infrastructure` (⬜ planned)
3. **P2.6:** MEU-91–95b service daemon & tray icon (all ⬜ planned)
4. **Research items:** MEU-165a/b workspace setup (🔲 planned)
