---
project: "2026-04-30-mcp-token-refresh"
date: "2026-04-30"
source: "docs/build-plan/05-mcp-server.md"
meus: ["MEU-PH14"]
status: "draft"
template_version: "2.0"
---

# Implementation Plan: MCP Token Refresh Manager (MEU-PH14)

> **Project**: `2026-04-30-mcp-token-refresh`
> **Build Plan Section(s)**: [05-mcp-server.md](../../../build-plan/05-mcp-server.md) (new §5.X — Token Refresh Infrastructure)
> **Status**: `draft`

---

## Goal

The MCP server currently bootstraps authentication once at startup via `POST /auth/unlock` and stores the session token with an `expiresAt` timestamp — but **never checks expiry or refreshes the token**. When the session token expires (default TTL: 3600s), all compound tool calls silently fail with 401 errors until the MCP server is restarted.

Under concurrent tool execution (common when AI agents batch multiple tool calls), the lack of a refresh mechanism creates a race condition: multiple tool handlers could independently detect expiry and simultaneously attempt to re-authenticate, causing redundant `/auth/unlock` calls and potential state corruption.

This MEU implements a singleton `TokenRefreshManager` that:
1. Centralizes all token access behind `getValidAccessToken()`
2. Proactively refreshes tokens approaching expiry (30s skew)
3. Deduplicates concurrent refresh requests via promise coalescing
4. Propagates refresh failures without deadlocking future attempts

**Issue resolved**: [MCP-AUTHRACE]

---

## User Review Required

> [!IMPORTANT]
> No breaking changes to external contracts. All MCP tool interfaces remain identical.
> The only behavioral change is internal: token refresh happens automatically and transparently.
>
> **Design decision already made** (2026-04-30): Option A+B hybrid — in-process singleton with interface for future distributed replacement. Documented in `known-issues.md`.

---

## Proposed Changes

### MEU-PH14: Token Refresh Manager

#### Boundary Inventory

This MEU introduces **no new external input surfaces**. The `TokenRefreshManager` is internal infrastructure that wraps existing auth flows. No new REST endpoints, MCP tool parameters, or user-facing inputs are added.

| Surface | Schema Owner | Field Constraints | Extra-Field Policy |
|---------|-------------|-------------------|-------------------|
| N/A — internal infrastructure only | N/A | N/A | N/A |

#### Acceptance Criteria

| AC | Description | Source | Negative Test |
|----|-------------|--------|---------------|
| AC-1 | `TokenRefreshManager` is a singleton implementing `ITokenProvider` interface with `getValidAccessToken(): Promise<string>` | Human-approved (known-issues.md [MCP-AUTHRACE] architecture decision) | Attempting to construct a second instance reuses the same singleton |
| AC-2 | Token is proactively refreshed when `expiresAt <= Date.now() + 30_000` (30s skew) | Human-approved (known-issues.md [MCP-AUTHRACE] contract §2) | Token with 29s remaining triggers refresh; token with 31s remaining does not |
| AC-3 | N concurrent `getValidAccessToken()` calls during refresh cause exactly 1 `POST /auth/unlock` call (promise coalescing) | Human-approved (known-issues.md [MCP-AUTHRACE] contract §3 — promise coalescing mandated by architecture decision) | 10 concurrent calls → mock verifies exactly 1 fetch call |
| AC-4 | All waiters receive the same refreshed token value | Human-approved (known-issues.md [MCP-AUTHRACE] required tests §2) | All 10 concurrent callers' resolved values are identical |
| AC-5 | Refresh failure clears in-flight promise and propagates error to all current waiters; subsequent calls attempt a fresh refresh (no deadlock) | Human-approved (known-issues.md [MCP-AUTHRACE] contract §4) | After a failed refresh, the next call triggers a new refresh attempt (not stuck on rejected promise) |
| AC-6 | Sequential calls after successful refresh reuse the updated token without re-calling `/auth/unlock` | Human-approved (known-issues.md [MCP-AUTHRACE] required tests §5) | Two sequential calls with valid token → 0 refresh calls |
| AC-7 | Individual compound tools do NOT call refresh/bootstrap directly — all token access goes through `fetchApi()` → `TokenRefreshManager` | Human-approved (known-issues.md [MCP-AUTHRACE] contract §5) | No `import.*bootstrapAuth` in compound tool files |
| AC-8 | `fetchApi()` and `fetchApiBinary()` use `await tokenRefreshManager.getValidAccessToken()` for auth headers | Local Canon (api-client.ts current architecture) | Remove manager → fetchApi fails to include auth headers |
| AC-9 | Existing test suites continue to pass (no behavioral regression) | Local Canon (test infrastructure) | `npx vitest run` → all tests pass |
| AC-10 | Integration proof: `fetchApi()`, `fetchApiBinary()`, `mcp-guard.ts` guard check, `diagnostics-tools.ts` safe-fetch, and `index.ts` startup all obtain auth tokens exclusively from `TokenRefreshManager.getValidAccessToken()` — verified by behavioral tests that mock the manager and assert the refreshed token appears in request headers | Local Canon (api-client.ts, mcp-guard.ts, diagnostics-tools.ts, system-tool.ts call sites) | Mock manager returns sentinel token → assert `Authorization: Bearer <sentinel>` in fetch calls |

#### Spec Sufficiency Table

| Behavior | Classification | Resolution |
|----------|---------------|------------|
| Token refresh = re-call `POST /auth/unlock` with stored API key | Local Canon | api-client.ts L36-60 + 04c-api-auth.md — no separate refresh endpoint exists; re-authentication via unlock is the canonical mechanism |
| Session token TTL = `expires_in` from unlock response (default 3600s) | Spec | 04c-api-auth.md L32: `expires_in: int # Seconds until token expires (default 3600)` |
| Proactive expiry skew = 30 seconds | Human-approved | known-issues.md [MCP-AUTHRACE] contract §2 |
| Singleton pattern with interface | Human-approved | known-issues.md [MCP-AUTHRACE] architecture decision: Option A+B hybrid |
| Promise coalescing for concurrent deduplication | Human-approved | known-issues.md [MCP-AUTHRACE] architecture decision mandates "deduplicate concurrent refreshes with a single in-flight promise." Implementation uses standard JS promise coalescing (no external deps). |
| Error propagation without deadlock | Human-approved | known-issues.md [MCP-AUTHRACE] contract §4: "On refresh failure: clear in-flight state, propagate same auth error to all waiters." Implementation: `.finally(() => this.refreshPromise = null)` — clears state regardless of success/failure |

#### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `mcp-server/src/utils/token-refresh-manager.ts` | new | `ITokenProvider` interface + `TokenRefreshManager` class: singleton, promise coalescing, proactive expiry, stored API key for re-auth |
| `mcp-server/src/utils/api-client.ts` | modify | Remove module-level `authState` and `bootstrapAuth()`; replace `getAuthHeaders()` with async `getAuthHeaders()` that delegates to `TokenRefreshManager.getValidAccessToken()`; update `fetchApi()` and `fetchApiBinary()` to await auth headers |
| `mcp-server/src/index.ts` | modify | Initialize `TokenRefreshManager` with API key instead of calling `bootstrapAuth()` directly |
| `mcp-server/src/compound/system-tool.ts` | modify | Update `getAuthHeaders()` call sites (L27,186) to `await getAuthHeaders()` |
| `mcp-server/src/middleware/mcp-guard.ts` | modify | Update `getAuthHeaders()` call sites (L15,44) to `await getAuthHeaders()` |
| `mcp-server/src/tools/diagnostics-tools.ts` | modify | Update `getAuthHeaders()` call sites (L14,75) to `await getAuthHeaders()` |
| `mcp-server/tests/token-refresh-manager.test.ts` | new | 9+ test cases covering AC-1 through AC-10 |
| `mcp-server/tests/integration.test.ts` | modify | Update any `bootstrapAuth` mocks to use new manager API; add AC-10 integration tests for `fetchApi`, `fetchApiBinary`, guard, diagnostics, and startup |
| `mcp-server/tests/compound/system-tool.test.ts` | modify | Update auth mocks for async `getAuthHeaders()` |
| `docs/build-plan/05-mcp-server.md` | modify | Add §5.X — Token Refresh Infrastructure; update existing auth snippets (L119,122,241,259,1015) to reflect new `TokenRefreshManager` API |
| `docs/build-plan/build-priority-matrix.md` | modify | Add P2.5g entry |
| `docs/BUILD_PLAN.md` | modify | Add MEU-PH14 row under new P2.5g section; update Phase 9 tracker; update MEU Summary table |
| `.agent/context/meu-registry.md` | modify | Add MEU-PH14 entry |
| `.agent/context/known-issues.md` | modify | Update [MCP-AUTHRACE] status to resolved, archive |
| `.agent/context/known-issues-archive.md` | modify | Add [MCP-AUTHRACE] archival record |

---

## Out of Scope

- Adding a dedicated `/auth/refresh` REST endpoint to the Python API (token renewal uses existing `/auth/unlock`)
- Distributed lock mechanisms or multi-instance token coordination (deferred to future MEU if needed)
- Broker-specific OAuth refresh flows (different concern: broker token management, not MCP session auth)
- UI changes (auth is MCP-internal)

---

## BUILD_PLAN.md Audit

This project adds:
1. New P2.5g section (1 MEU row: MEU-PH14)
2. Phase 9 tracker update to include P2.5g
3. MEU Summary table: +1 MEU, +1 completed

```powershell
rg "P2.5g|MEU-PH14|token-refresh" docs/BUILD_PLAN.md *> C:\Temp\zorivest\bp-audit.txt; Get-Content C:\Temp\zorivest\bp-audit.txt
```

Expected: 3+ matches after implementation.

---

## Verification Plan

### 1. Unit Tests (primary validation)
```powershell
cd mcp-server; npx vitest run tests/token-refresh-manager.test.ts *> C:\Temp\zorivest\vitest-trm.txt; Get-Content C:\Temp\zorivest\vitest-trm.txt | Select-Object -Last 30
```

### 2. Full MCP Test Suite (regression)
```powershell
cd mcp-server; npx vitest run *> C:\Temp\zorivest\vitest-full.txt; Get-Content C:\Temp\zorivest\vitest-full.txt | Select-Object -Last 40
```

### 3. TypeScript Type Check
```powershell
cd mcp-server; npx tsc --noEmit *> C:\Temp\zorivest\tsc.txt; Get-Content C:\Temp\zorivest\tsc.txt | Select-Object -Last 20
```

### 4. Lint
```powershell
cd mcp-server; npx eslint src/ --max-warnings 0 *> C:\Temp\zorivest\eslint.txt; Get-Content C:\Temp\zorivest\eslint.txt | Select-Object -Last 20
```

### 5. Build Dist
```powershell
cd mcp-server; npm run build *> C:\Temp\zorivest\build.txt; Get-Content C:\Temp\zorivest\build.txt | Select-Object -Last 10
```

### 6. AC-7 Enforcement (no direct bootstrapAuth imports in compound tools)
```powershell
rg "import.*bootstrapAuth" mcp-server/src/compound/ *> C:\Temp\zorivest\ac7.txt; Get-Content C:\Temp\zorivest\ac7.txt
```
Expected: 0 matches.

### 7. Anti-Placeholder Scan
```powershell
rg "TODO|FIXME|NotImplementedError" mcp-server/src/utils/token-refresh-manager.ts *> C:\Temp\zorivest\placeholder.txt; Get-Content C:\Temp\zorivest\placeholder.txt
```
Expected: 0 matches.

---

## Applicable Emerging Standards

| Standard | Applies | Enforcement |
|----------|---------|-------------|
| M4 — Build dist/ After Source Changes | ✅ | Verification Plan §5 |
| M5 — TDD Red Phase Must Fail for Right Reason | ✅ | Red phase: verify test failure message matches expected behavior gap |
| M6 — No Vacuous Test Assertions | ✅ | Each test must fail if the bug is reintroduced |

---

## Open Questions

> [!WARNING]
> **No open questions.** All design decisions are resolved via the architecture decision documented in `known-issues.md` and the spec sufficiency analysis above.

---

## Research References

- [known-issues.md [MCP-AUTHRACE]](file:///p:/zorivest/.agent/context/known-issues.md) — architecture decision (2026-04-30), required contract, required tests. This is the binding authority for all design decisions including promise coalescing and error propagation.
- [04c-api-auth.md](file:///p:/zorivest/docs/build-plan/04c-api-auth.md) — auth unlock flow, session token TTL
- [api-client.ts](file:///p:/zorivest/mcp-server/src/utils/api-client.ts) — current auth state management
- [system-tool.ts](file:///p:/zorivest/mcp-server/src/compound/system-tool.ts) — direct `getAuthHeaders()` caller (L27,186)
- [mcp-guard.ts](file:///p:/zorivest/mcp-server/src/middleware/mcp-guard.ts) — direct `getAuthHeaders()` caller (L15,44)
- [diagnostics-tools.ts](file:///p:/zorivest/mcp-server/src/tools/diagnostics-tools.ts) — direct `getAuthHeaders()` caller (L14,75)
