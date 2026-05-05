# Known Issue Triage Report — 2026-05-03

## Summary
- Total issues reviewed: 12
- Archived in Step 1: 0 (no fully resolved issues found)
- Remaining active: 12
- Actionable (new/expanded MEUs): 2
- Upstream/deferred: 3
- Workaround-OK: 4
- Tech debt: 2
- Blocked: 2
- Architecture decisions needed: 0

## Archival Actions Performed (Step 1)

**No issues were archived.** All 12 active issues were verified against the codebase and none are fully resolved:

- **[STUB-RETIRE]** — `StubAnalyticsService`, `StubReviewService`, `StubTaxService` still active in `stubs.py`, `main.py`, `dependencies.py` (14 references).
- **[MCP-ZODSTRIP]** — Upstream TS-SDK #1291/#1380/PR #1603 still open. Startup assertion workaround in place.
- **[MCP-WINDETACH]** — Upstream Node.js #5146/#36808 still open (since 2016).
- **[MCP-HTTPBROKEN]** — Mitigated by design (stdio primary). No Streamable HTTP references in codebase.
- **[MCP-DIST-REBUILD]** — By design (`"main": "dist/index.js"` in package.json).
- **[UI-ESMSTORE]** — Pinned at `"electron-store": "^8.2.0"` (CJS). Upstream v9+ still ESM-only.
- **[E2E-AXEELECTRON]** — axe-core referenced in 5 E2E test files. `file://` workaround still active.
- **[E2E-AXESILENT]** — Process awareness issue. No automated fix in place.
- **[E2E-ELECTRONLAUNCH]** — Environment-specific. No CI xvfb setup yet.
- **[MKTDATA-POLYGON-REBRAND]** — `provider_registry.py` still uses `https://api.polygon.io/v2`. MEU-195 planned.
- **[MKTDATA-YAHOO-UNOFFICIAL]** — Partially resolved (OHLCV done). Remaining: fundamentals, earnings, dividends, splits, news fix.
- **[MKTDATA-TRADINGVIEW-NOPUBLICAPI]** — Partially resolved (quote+fundamentals+POST runtime). Remaining: exchange routing, batching, caching, technicals.

## Classification Table (Active Issues)

| Issue ID | Severity | Component | Classification | Target | Priority | Notes |
|----------|----------|-----------|---------------|--------|----------|-------|
| STUB-RETIRE | Low | api | `BLOCKED` | MEU-104-116, MEU-110, MEU-123-126 | P4 | Retires when analytics/review/tax services built |
| MCP-ZODSTRIP | Critical | mcp-server | `UPSTREAM` | TS-SDK #1291/#1380 | — | Startup assertion workaround sufficient |
| MCP-WINDETACH | Critical | infrastructure | `UPSTREAM` | Node.js #5146/#36808 | — | Job Objects workaround in place |
| MCP-HTTPBROKEN | High | mcp-server | `WORKAROUND-OK` | — | — | stdio is primary transport by design |
| MCP-DIST-REBUILD | High | mcp-server | `WORKAROUND-OK` | — | — | By design; npm run build + restart |
| UI-ESMSTORE | Medium | ui | `UPSTREAM` | electron-store v9+ | — | Pinned to v8 CJS; adequate indefinitely |
| E2E-AXEELECTRON | High | ui (E2E) | `WORKAROUND-OK` | — | — | file:// + page.evaluate() pattern |
| E2E-AXESILENT | Medium | ui (E2E) | `TECH-DEBT` | E2E test hardening | P4 | Wrap axe scan in structured try/catch |
| E2E-ELECTRONLAUNCH | High | ui (E2E) | `BLOCKED` | CI pipeline setup | P3 | xvfb-run needed in CI; local works |
| MKTDATA-POLYGON-REBRAND | Low | infrastructure | `MEU-EXPAND` | MEU-195 (planned) | P3 | Simple domain swap; independent |
| MKTDATA-YAHOO-UNOFFICIAL | Med/High | infrastructure | `MEU-EXPAND` | MEU-190/191 scope | P2 | Remaining Yahoo data types piggyback on Phase 8a L4 |
| MKTDATA-TRADINGVIEW-NOPUBLICAPI | Medium | infrastructure | `TECH-DEBT` | Future mini-MEU | P4 | POST runtime resolved (MEU-189); remaining items opportunistic |

## Recommended Project Batches

### Batch 1: `phase-8a-layer4-service-methods` — Priority P2

- **Issues addressed**: [MKTDATA-YAHOO-UNOFFICIAL] (remaining expansion items), [MKTDATA-POLYGON-REBRAND]
- **Existing MEUs**: MEU-190 `service-methods-core`, MEU-191 `service-methods-extended`, MEU-195 `polygon-massive-migration`
- **Scope expansion**: MEU-190/191 acceptance criteria should include Yahoo-specific data types (fundamentals via v10/quoteSummary, earnings, dividends via v8/chart?events=div, splits). These are same-endpoint expansions, not new providers.
- **Build-plan section**: `docs/build-plan/08a-market-data-expansion.md` (items 30.9, 30.10, 30.14)
- **Complexity**: M (MEU-190/191) + S (MEU-195) = overall M
- **Dependencies**: MEU-182-189 all complete. No blockers.
- **Next step**: Invoke `/create-plan` with this batch. Already identified as next priority in `current-focus.md`.

### Batch 2: `e2e-ci-infrastructure` — Priority P3

- **Issues addressed**: [E2E-ELECTRONLAUNCH]
- **New MEUs**: Mini-MEU for CI E2E configuration (xvfb-run wrapper, GitHub Actions workflow)
- **Build-plan section**: CI/DevOps (no existing section — would need `docs/build-plan/07a-ci-e2e.md` or piggyback on existing CI docs)
- **Complexity**: S
- **Dependencies**: None
- **Next step**: Defer until CI pipeline work is prioritized. Not blocking any current development.

## No Action Required

Issues classified as UPSTREAM, WORKAROUND-OK, BLOCKED, or TECH-DEBT with no near-term action:

| Issue ID | Classification | Rationale |
|----------|---------------|-----------|
| STUB-RETIRE | `BLOCKED` | Stubs retire when real services are implemented (P2.75 analytics, P3 tax). No action until those phases. |
| MCP-ZODSTRIP | `UPSTREAM` | TS-SDK bug. Startup assertion prevents silent failures. Monitor PRs. |
| MCP-WINDETACH | `UPSTREAM` | Node.js bug since 2016. Job Objects workaround is permanent. |
| MCP-HTTPBROKEN | `WORKAROUND-OK` | stdio transport is the design choice. HTTP transport avoided entirely. |
| MCP-DIST-REBUILD | `WORKAROUND-OK` | By-design rebuild requirement. Documented in skill (mcp-rebuild). |
| UI-ESMSTORE | `UPSTREAM` | electron-store v8 pin is stable. v9+ ESM-only is a library decision. |
| E2E-AXEELECTRON | `WORKAROUND-OK` | file:// axe-core injection works. No upstream fix expected. |
| E2E-AXESILENT | `TECH-DEBT` | Low-severity process awareness. Can batch into future E2E hardening. |
| E2E-ELECTRONLAUNCH | `BLOCKED` | CI-specific. Local dev unaffected. Defer until CI pipeline project. |
| MKTDATA-TRADINGVIEW-NOPUBLICAPI | `TECH-DEBT` | Core integration done. Expansion items (exchange routing, batching, technicals) are opportunistic. |

## Known-Issues.md Cleanup Recommendation

**Current line count: 211 lines (target: <100)**

The file is bloated by two research-tracking entries that have outgrown the issue format:

| Entry | Current Lines | Recommended Lines | Action |
|-------|:---:|:---:|--------|
| MKTDATA-YAHOO-UNOFFICIAL | ~43 | ~10 | Condense: move detailed tables/research to build-plan docs |
| MKTDATA-TRADINGVIEW-NOPUBLICAPI | ~45 | ~10 | Condense: move detailed tables/research to build-plan docs |
| MKTDATA-POLYGON-REBRAND | ~17 | ~8 | Condense: research findings belong in build-plan |
| Archived table | ~45 | ~45 | Keep as-is (ID/date/summary rows) |

**Recommended action**: After this triage is approved, condense the three market data entries and move their detailed research/capability tables into `08a-market-data-expansion.md` or a dedicated research doc. This would bring the file to ~100 lines.
