# Known Issues → MEU Coverage Analysis

> Goal: Eliminate as many known issues as possible before proceeding with standard MEU execution.
> Date: 2026-04-12

---

## Issue-by-Issue Assessment

### 1. ✅ [TEST-DRIFT-MDS] — **Already Resolved (archive immediately)**

- **Claimed:** 5 tests in `test_market_data_service.py` fail due to wiring changes
- **Actual:** All 13 tests pass (verified just now — `13 passed in 0.30s`)
- **Action:** Archive to `known-issues-archive.md`. Zero MEU work needed.

---

### 2. [STUB-RETIRE] — Partially actionable now

**Current state of `stubs.py`:**

| Stub | Used in `main.py`? | Real service exists? | Action |
|------|:------------------:|:-------------------:|--------|
| `StubAnalyticsService` | ✅ L197 | ❌ (needs MEU-104–116) | Keep — blocked on domain MEUs |
| `StubReviewService` | ✅ L198 | ❌ (needs MEU-110) | Keep — blocked on domain MEUs |
| `StubTaxService` | ✅ L199 | ❌ (needs MEU-123–126) | Keep — blocked on domain MEUs |
| `StubMarketDataService` | ❌ **dead code** | ✅ `MarketDataService` (L208) | **Delete now** |
| `StubProviderConnectionService` | ❌ **dead code** | ✅ `ProviderConnectionService` (L219) | **Delete now** |

> [!TIP]
> The two dead stubs can be removed in a quick micro-MEU or folded into the pipeline wiring MEU below.

---

### 3. [SCHED-PIPELINE-WIRING] — **Biggest gap, needs new MEU**

**Current wiring in `main.py` L241:**
```python
pipeline_runner = PipelineRunner(uow, RefResolver(), ConditionEvaluator())
```

**Missing arguments (all Optional, all `None`):**

| Param | What it provides | Where it's consumed | What happens without it |
|-------|-----------------|--------------------|-----------------------|
| `provider_adapter` | Market data fetch capability | `FetchStep` → `context.outputs["provider_adapter"]` | `ValueError: provider_adapter required` |
| `smtp_config` | Email host/port/sender | `SendStep` → `context.outputs["smtp_config"]` | Falls back to `localhost:587` — will fail |
| `delivery_repository` | SHA-256 dedup for sent emails | `SendStep` → `context.outputs["delivery_repository"]` | No dedup — duplicate sends possible |

> [!IMPORTANT]
> Without these three wirings, **no pipeline can execute end-to-end**. The `Run Now` button in MEU-72's GUI will trigger a pipeline that crashes at `FetchStep`.

---

### 4. [MCP-TOOLDISCOVERY] — Needs new MEU (documentation pass)

Confirmed gaps in scheduling toolset descriptions. Similar gaps likely across all 9 toolsets:
- `accounts`, `trade-analytics`, `trade-planning`, `market-data`, `scheduling`, `settings`, `diagnostics`, `guard`, `discovery`

---

### 5. Mitigated/Workaround Issues — No MEU action possible

| Issue | Status | Why no action |
|-------|--------|--------------|
| [MCP-TOOLCAP] | Design mitigated | Three-tier strategy chosen |
| [MCP-ZODSTRIP] | Upstream SDK bug | Workaround in place |
| [MCP-AUTHRACE] | Architectural | In-memory mutex applied |
| [MCP-WINDETACH] | Upstream Node.js | Windows Job Objects workaround |
| [MCP-HTTPBROKEN] | Mitigated by Design | stdio primary, SDK pinned |
| [MCP-DIST-REBUILD] | By design | Build-then-restart workflow |
| [UI-ESMSTORE] | Workaround applied | Pinned to electron-store@8 |
| [E2E-AXEELECTRON] | Workaround applied | file:// URL + page.evaluate() |
| [E2E-AXESILENT] | Process awareness | Manual try/catch |
| [E2E-ELECTRONLAUNCH] | Environment-specific | CI uses xvfb-run |

---

## Proposed MEU Changes

### A. Existing MEUs to Update

None of the existing pending MEUs (MEU-74, 75, 76, 91–95) need modification to resolve known issues. The issues are orthogonal to their scope.

### B. New MEUs for Backend Services Wiring

#### MEU-PW1: `pipeline-runtime-wiring` — **Resolves [SCHED-PIPELINE-WIRING]**

> [!IMPORTANT]
> **This is the highest-value new MEU.** It bridges the gap between "all pipeline domain code is built" and "pipelines can actually execute."

| Field | Value |
|-------|-------|
| **Priority** | P2.5b (between P2.5a persistence-wiring and P2.6 service daemon) |
| **Depends on** | MEU-90a ✅, MEU-85 ✅, MEU-88 ✅, MEU-65a ✅, MEU-73 ✅ |
| **Build plan ref** | [09 §runner](build-plan/09-scheduling.md), [06e](build-plan/06e-gui-scheduling.md) |
| **Unblocks** | End-to-end pipeline execution, MEU-72 "Run Now" functionality |

**Scope:**

1. **Create `MarketDataProviderAdapter`** — bridge `MarketDataService` (already wired at L208) into the `provider_adapter` interface expected by `FetchStep`
2. **Wire `smtp_config` at startup** — read email provider settings from `EmailProviderService` (already wired at L228) and pass SMTP config dict to `PipelineRunner`
3. **Wire `delivery_repository`** — pass `uow.deliveries` repo to `PipelineRunner` for `SendStep` dedup
4. **Update `main.py`** — change PipelineRunner construction to include all three runtime deps
5. **Integration test** — end-to-end pipeline: `FetchStep → TransformStep → SendStep` with mocked SMTP and real DB
6. **Delete dead stubs** — remove `StubMarketDataService` and `StubProviderConnectionService` from `stubs.py` (fold in [STUB-RETIRE] partial cleanup)

**Estimated effort:** Medium (1 session)

---

#### MEU-TD1: `mcp-tool-discovery-audit` — **Resolves [MCP-TOOLDISCOVERY]**

| Field | Value |
|-------|-------|
| **Priority** | P2.5c (quality-of-life, parallel with anything) |
| **Depends on** | All MCP tool MEUs ✅ |
| **Build plan ref** | [05-mcp-server.md](build-plan/05-mcp-server.md) |

**Scope:**

1. **Audit all 9 toolset descriptions** against actual API contracts
2. **Enrich `server.instructions`** with toolset workflow summaries
3. **Add `policy_json` examples** to `create_policy` tool description
4. **Reference MCP resources** (`pipeline://policies/schema`, `pipeline://step-types`) from tool descriptions
5. **Add prerequisite state, return shape, and error conditions** to all tool descriptions
6. **Add workflow guidance** for multi-step operations (`create → approve → run`, trade plan lifecycle, etc.)

**Estimated effort:** Medium (1 session, mostly TypeScript string edits + Vitest)

---

## Recommended Execution Order

```
1. Archive [TEST-DRIFT-MDS]              ← immediate (0 effort)
2. MEU-PW1 pipeline-runtime-wiring       ← high value, resolves [SCHED-PIPELINE-WIRING] + partial [STUB-RETIRE]
3. MEU-TD1 mcp-tool-discovery-audit      ← medium value, resolves [MCP-TOOLDISCOVERY]
4. Resume standard MEU queue (MEU-74+)   ← normal execution
```

> [!NOTE]
> After these 2 new MEUs, the active issues list drops from **4 open + 10 mitigated** to **1 open (STUB-RETIRE, legitimately blocked on future domain MEUs) + 10 mitigated**. The mitigated issues are all upstream/environmental and require no code changes.

---

## Summary

| Known Issue | Resolution | MEU | Effort |
|-------------|-----------|-----|--------|
| [TEST-DRIFT-MDS] | **Archive** (already fixed) | None | 0 |
| [SCHED-PIPELINE-WIRING] | New MEU-PW1 `pipeline-runtime-wiring` | New | Medium |
| [STUB-RETIRE] (partial) | Dead stub deletion folded into MEU-PW1 | Folded | Trivial |
| [MCP-TOOLDISCOVERY] | New MEU-TD1 `mcp-tool-discovery-audit` | New | Medium |
| [STUB-RETIRE] (remaining) | Blocked on MEU-104–116, 123–126 | Existing roadmap | N/A |
| 10 mitigated issues | No action possible | N/A | N/A |

**Net result:** 3 of 4 active issues resolved before resuming standard execution.
