# Known Issue Triage Report — 2026-04-30

## Summary
- Total issues reviewed: 12
- Archived in Step 1: 2 (`MCP-TOOLDISCOVERY`, `MCP-TOOLCAP`)
- Remaining active: 10
- Actionable (new/expanded MEUs): 1
- Upstream/deferred: 2
- Architecture decisions needed: 0
- Workaround-ok: 5
- Blocked: 1
- Tech-debt: 1

## Archival Actions Performed (Step 1)

Issues verified as resolved and moved to `known-issues-archive.md`:

1. **[MCP-TOOLDISCOVERY]** — Resolved by MEU-TD1 ✅ 2026-04-30
   - Verification: `grep` confirmed all 13 compound tool files in `mcp-server/src/compound/` contain M7-pattern descriptions (WORKFLOW, Prerequisites, Return, Error conditions)
   - Server instructions expanded, M7 enforcement gate added to emerging-standards

2. **[MCP-TOOLCAP]** — Resolved by compound-tool consolidation (85→13) ✅ 2026-04-29
   - Verification: [MCP-TOOLPROLIFERATION] already archived confirming 85→13 consolidation complete. 13 compound tools fit ALL IDE limits natively (Cursor ≤40, VS Code, CLI/API all satisfied)
   - Three-tier strategy superseded — no longer needed

### Post-Archival State
- `known-issues.md`: 120 lines (target: <100; delta is from detailed [MCP-AUTHRACE] contract + [STUB-RETIRE] roadmap)
- 10 active issue headers remain

## Classification Table (Active Issues)

| Issue ID | Severity | Component | Classification | Target | Priority | Notes |
|----------|----------|-----------|---------------|--------|----------|-------|
| STUB-RETIRE | Low | api (stubs.py) | `BLOCKED` | P2.75/P3 MEUs | P4 | Resolves when analytics/review/tax services implemented |
| MCP-ZODSTRIP | Critical | mcp-server | `UPSTREAM` | TS-SDK #1291, #1380, PR #1603 | — | Raw shape workaround + startup assertion in place |
| MCP-AUTHRACE | Critical | mcp-server | `MEU-NEW` | New MEU needed | P2 | Architecture decided; needs implementation |
| MCP-WINDETACH | Critical | infrastructure | `UPSTREAM` | Node.js #5146, #36808 | — | Windows Job Objects workaround documented |
| MCP-HTTPBROKEN | High | mcp-server | `WORKAROUND-OK` | — | — | stdio primary transport; HTTP avoided |
| MCP-DIST-REBUILD | High | mcp-server | `WORKAROUND-OK` | — | — | By design; `npm run build` after src/ changes |
| UI-ESMSTORE | Medium | ui | `WORKAROUND-OK` | — | — | Pinned to electron-store@8 (CJS); verified in package.json |
| E2E-AXEELECTRON | High | ui (E2E) | `WORKAROUND-OK` | — | — | file:// URL + page.evaluate() workaround working |
| E2E-AXESILENT | Medium | ui (E2E) | `TECH-DEBT` | Batch with E2E work | P4 | Add try/catch scanner wrapper utility |
| E2E-ELECTRONLAUNCH | High | ui (E2E) | `WORKAROUND-OK` | — | — | Local E2E works; CI path: xvfb-run |

## Recommended Project Batches

### Batch 1: MCP Token Refresh Security — Priority P2

- **Issues addressed**: [MCP-AUTHRACE]
- **New MEUs**: MEU-PH14 `token-refresh-manager` — Implement singleton TokenRefreshManager with mutex, proactive-expiry, concurrent-refresh deduplication
- **Build-plan section**: `docs/build-plan/05-mcp-server.md` (new subsection §5.X — Token Refresh Infrastructure)
- **Complexity**: M (medium)
- **Dependencies**: Compound tool consolidation ✅ (all tool handlers exist)
- **Architecture decision**: Already made (2026-04-30) — Option A+B hybrid documented in known-issues.md
- **Required contract** (from issue):
  1. Centralize all access-token reads behind `TokenRefreshManager.getValidAccessToken()`
  2. Use refresh skew: refresh when `expires_at <= now + 30s`
  3. Deduplicate concurrent refreshes with a single in-flight promise
  4. On refresh failure: clear in-flight state, propagate same auth error to all waiters
  5. Individual tools must NOT call refresh directly
- **Required tests** (5 specified):
  1. N concurrent tools cause exactly 1 refresh call
  2. All waiters receive the refreshed token
  3. Refresh failure does not deadlock future refresh attempts
  4. Proactive expiry avoids near-expiry token use
  5. Sequential calls after refresh reuse the updated token
- **Next step**: Invoke `/create-plan` with this batch

## Architecture Decisions Required

None — the only actionable issue ([MCP-AUTHRACE]) already has its architecture decided:
- **Decision**: Option A+B hybrid — in-process singleton `TokenRefreshManager` with mutex/proactive-expiry mechanics, designed behind an interface for future distributed implementation
- **Decision date**: 2026-04-30
- **Status**: Ready for implementation (MEU-ready)

## No Action Required

| Issue ID | Classification | Rationale |
|----------|---------------|-----------|
| STUB-RETIRE | BLOCKED | Phase 3 stubs retire when their real services are implemented (MEU-104–116, MEU-110, MEU-123–126). No action possible until those phases are reached. |
| MCP-ZODSTRIP | UPSTREAM | SDK bug (TS-SDK #1291, #1380, PR #1603). Raw shape workaround + startup assertion prevents the issue. Monitor upstream for fix. |
| MCP-WINDETACH | UPSTREAM | Node.js bug since 2016 (#5146, #36808). Windows Job Objects workaround documented. No local fix possible. |
| MCP-HTTPBROKEN | WORKAROUND-OK | stdio is the primary transport. SDK version pinned. Stateless HTTP mode never used. |
| MCP-DIST-REBUILD | WORKAROUND-OK | Inherent to TypeScript compilation model. Build-after-change is documented process. |
| UI-ESMSTORE | WORKAROUND-OK | Pinned to electron-store@8 (last CJS version). Stable, no impact on functionality. |
| E2E-AXEELECTRON | WORKAROUND-OK | file:// URL + page.evaluate() pattern works reliably. Used in position-size and settings-market-data E2E tests. |
| E2E-AXESILENT | TECH-DEBT | Low-severity testing improvement. Can be batched into a future E2E infrastructure MEU when E2E test suite expands. |
| E2E-ELECTRONLAUNCH | WORKAROUND-OK | Local E2E verified. CI path documented (xvfb-run). Environment-specific, not a code bug. |

## Additional Observations

### MEU Registry Inconsistency (MC0–MC5)
The MEU registry shows MC0–MC5 (MCP Tool Consolidation) as `⬜ planned`, but [MCP-TOOLPROLIFERATION] is archived as resolved (2026-04-29) confirming the consolidation is complete. The compound tools are live and working (MCP audit passes 46/46). **Recommendation**: Update MC0–MC5 status to ✅ in `meu-registry.md` during next session.
