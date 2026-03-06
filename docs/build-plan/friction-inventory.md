# Zorivest Friction Inventory — Pre-mortem Risk Mining Results

> **Methodology:** Pre-mortem analysis + GitHub issue archaeology across 10 MCP server projects, 100+ specific issues/PRs, 5 independent research runs (Gemini×2, ChatGPT×1, Claude×2). Each finding maps to a build plan section and carries a confidence rating.
>
> **Research sources:** [`_inspiration/pre-mortem_risk_mining_research/`](file:///p:/zorivest/_inspiration/pre-mortem_risk_mining_research/)

---

## TL;DR — The Four Structural Risks

These cannot be mitigated through careful coding alone — they require **architectural decisions before implementation**.

| # | Structural Risk | Impact | Our Design Status |
|---|---|---|---|
| 1 | **Cursor's 40-tool hard cap** silently drops tools beyond limit | 28 of our 68 tools (41%) invisible | Dynamic toolsets designed (§5.6), client detection designed (§5.11) |
| 2 | **Streamable HTTP transport** has 5 distinct failure modes in the SDK | Session leaks, async timeouts, stateless mode broken | Build plan specifies HTTP-only (Streamable HTTP) transport (§5.7), auth lifecycle designed (§5.12–5.13) |
| 3 | **Auth token refresh** is universally broken across MCP clients | No client reliably handles token lifecycle | Server-side session token designed (§5.12–5.13) — but race conditions not addressed |
| 4 | **Node.js `detached` process** is broken on Windows since 2016 | Orphaned processes, database locks | Process isolation designed (§5.7) — Windows-specific spawning not addressed |

---

## Friction Area 1: Tool Registration at Scale

**Build plan:** §5.6 (toolsets), §5.8 (categories)  
**Confidence:** ██████████ 95% — extensively documented across all 5 research files

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-1.1 | `server.tool()` **silently strips all arguments** when passed `z.object({...})` instead of raw Zod shape | TS-SDK #1291, #1380, PR #1603 | 🔴 Critical |
| FR-1.2 | 68-tool flat registration consumed **~34,000 tokens** before any reasoning begins (17% of 200K context) | Claude Code #7328, Reddit, Anthropic engineering blog | 🔴 Critical |
| FR-1.3 | Eager module init causes **2.5s cold start** in Python SDK; same risk in TS with 68 Zod schema compilations | Python-SDK #1508 | 🟡 Medium |
| FR-1.4 | Tool schema non-determinism between restarts breaks LLM caching | FastMCP PR #3305/#3307 | 🟢 Low |

### Mitigations Already in Build Plan
- Dynamic toolset loading via `enable_toolset` + `list_changed` (§5.6) ✅
- Category-based tool organization (§5.8) ✅
- Tool Search via BM25/regex (inspired by FastMCP) — in `fastmcp-correlation.md` ✅

### Mitigations to Add
- **Tool registry wrapper** that enforces single schema authoring style and validates "no empty schemas" at startup
- **Lazy schema compilation** — defer Zod-to-JSON-Schema until first `tools/list` or per-tool invocation
- **Schema compatibility gate** in CI — run `tools/list` against MCP Inspector + target clients, reject `$ref`/`$defs`

---

## Friction Area 2: Middleware Composition

**Build plan:** §5.9 (guard), §5.10 (metrics)  
**Confidence:** ████████░░ 80% — FastMCP is the only mature reference; TS has no precedent

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-2.1 | Global auth middleware causes **entire `list_tools()` to fail** instead of filtering unauthorized items | FastMCP #3333 | 🔴 Critical |
| FR-2.2 | Starlette `BaseHTTPMiddleware` + MCP SSE throws `AssertionError: Unexpected message` | Python-SDK #883 (P1) | 🟠 High |
| FR-2.3 | Error raised **after** `call_next()` only logs — response already sent to client | FastMCP middleware docs | 🟡 Medium |
| FR-2.4 | No MCP project ships a **circuit breaker** — only IBM's MCP Context Forge has a spec (#301) | Research file 3 | 🟡 Medium |

### Mitigations Already in Build Plan
- `withGuard→withMetrics→withConfirmation→handler` pipeline (§5.9–5.10) ✅
- Circuit breaker with CLOSED→OPEN→HALF_OPEN states (§5.9) ✅

### Mitigations to Add
- **Discovery vs execution authorization decoupling** — `tools/list` must filter by scope, never fail entirely
- **Error handler must be first** in middleware chain — catching downstream errors before response is sent
- **Middleware ordering tests** — verify error semantics (before vs after `next()`)

---

## Friction Area 3: Dynamic Toolset Loading

**Build plan:** §5.6 (enable_toolset, list_changed)  
**Confidence:** █████████░ 90% — GitHub MCP server provides production reference

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-3.1 | `notifications/tools/list_changed` **not supported** by Claude Desktop or Cursor | MCP maintainer @jspahrsummers confirmed (Dec 2024); spec Discussion #1384 | 🔴 Critical |
| FR-3.2 | VS Code **resets all tool permissions** when `list_changed` fires — users must re-approve | Microsoft docs, Research file 3 | 🟠 High |
| FR-3.3 | GitHub MCP dynamic toolsets are **local-only** — not available on remote server (#1108) | GitHub MCP server | 🟡 Medium |
| FR-3.4 | Extra round-trips: enabling a toolset costs **1–2 additional LLM calls** before actual work | GitHub MCP server docs | 🟢 Low |

### Mitigations Already in Build Plan
- Dynamic toolsets designed with meta-tools (§5.6) ✅
- Client detection for adaptive behavior (§5.11) ✅

### Mitigations to Add
- **Static fallback mode** — environment-variable-based category selection for Cursor (≤40 tools)
- **Three-tier strategy**: (1) Static ≤40 for Cursor, (2) Dynamic toolsets for VS Code, (3) Full for high-limit clients
- **Test `list_changed` against actual target clients** — don't assume support

---

## Friction Area 4: Auth Bootstrap Lifecycle

**Build plan:** §5.12 (encryption), §5.13 (session management)  
**Confidence:** █████████░ 90% — universal failure pattern across MCP ecosystem

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-4.1 | **Token refresh race condition**: concurrent 401s trigger multiple overlapping refresh requests | Azure AD blog, Research file 4 | 🔴 Critical |
| FR-4.2 | Tokens expire during long tool execution — **mid-stream auth failure** corrupts operations | fast.io storage guide, Research file 4 | 🔴 Critical |
| FR-4.3 | ContextVars (Python) / global state **leaks across concurrent requests** | Python-SDK #1684 | 🟠 High |
| FR-4.4 | Reactive OAuth (wait for 401) causes **10-second performance regression** | Python-SDK #1274 | 🟠 High |
| FR-4.5 | Client elicitation timeouts as short as **60 seconds** — user can't complete MFA in time | Cursor forum #145618 | 🟡 Medium |
| FR-4.6 | Token stored in `process.env` causes **cross-session contamination** in multi-client scenarios | simplescraper.io guide | 🟡 Medium |
| FR-4.7 | **Every major MCP client** fails at token refresh: Atlassian (#12), GitHub Copilot (#1797), Google ADK (#3761), Cursor | Research file 5 | 🔴 Critical |

### Mitigations Already in Build Plan
- API key → session token exchange (§5.13) ✅
- SQLCipher encryption for data at rest (§5.12) ✅

### Mitigations to Add
- **In-memory mutex** for token refresh: lock on first 401, queue other requests, refresh once, drain queue
- **Proactive token refresh**: decode JWT `exp`, refresh when within 5-min buffer before any REST call
- **AsyncLocalStorage** for per-request identity isolation (instead of globals)
- **Token stored in connection instance memory**, not `process.env` or globals
- **Out-of-band auth** for confirmation flows: decouple from MCP elicitation timeout

---

## Friction Area 5: Client Detection / Adaptation

**Build plan:** §5.11 (patterns A–F)  
**Confidence:** ███████░░░ 70% — no project implements this; Zorivest would be first

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-5.1 | **No project implements `clientInfo`-based adaptive behavior** — Zorivest would be first | Research file 3 (10-project survey) | 🟡 Medium |
| FR-5.2 | `clientInfo.name` values are **unstable** — change between versions, proxies report own name | Apify `mcp-client-capabilities`, PulseMCP analysis | 🟠 High |
| FR-5.3 | ChatGPT imposes **5,000-token cap** for all tool definitions — 68 tools at ~500/tool = hard reject | Research file 5 | 🔴 Critical |
| FR-5.4 | Gemini CLI strips `$schema` and `additionalProperties` from schemas, potentially breaking validation | Gemini CLI #19083 | 🟡 Medium |

### Mitigations Already in Build Plan
- Client detection patterns A–F specified (§5.11) ✅

### Mitigations to Add
- **Fallback strategy** when `clientInfo.name` is unknown or spoofed — default to most restrictive tier
- **Client detection integration test matrix** — test with each target client specifically
- **Token budget calculation** per client — enforce per-client schema size limits

---

## Friction Area 6: Transport (Streamable HTTP)

**Build plan:** §5.7 (process isolation)  
**Confidence:** █████████░ 90% — 5 distinct failure modes documented in SDK

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-6.1 | **Stateless mode broken** — `validateSession` perpetually false | TS-SDK #340 | 🔴 Critical |
| FR-6.2 | Async tool handlers **timeout on Streamable HTTP** — any I/O produces `-32001` | TS-SDK #1106 | 🔴 Critical |
| FR-6.3 | **Cross-client data leak** (pre-v1.26.0) — session ID collision routes responses to wrong client | GHSA-345p-7cg4-v4c7 | 🔴 Critical |
| FR-6.4 | SSE streams disconnect every **~5 minutes** with lifecycle misuse | TS-SDK #1211 | 🟠 High |
| FR-6.5 | **STDIO hard-crash** on EPIPE when client disconnects before response | TS-SDK #1564 | 🟠 High |
| FR-6.6 | "Dead but connected" servers — hangs indefinitely, no lifecycle enforcement | Reddit r/mcp, marimo client | 🟠 High |
| FR-6.7 | Progress notifications **silently dropped** when `enableJsonResponse: true` | TS-SDK #866 | 🟡 Medium |
| FR-6.8 | Load balancer needs `mcp-stream-id` header for resumable streams | TS-SDK #892 (266 days open) | 🟡 Medium |

### Mitigations Already in Build Plan
- HTTP-only (Streamable HTTP) transport with auth lifecycle (§5.7, §5.12–5.13) ✅
- Process isolation with separate processes (§5.7) ✅

### Mitigations to Add
- **Pin SDK to exact version** — upgrade under "transport regression checklist"
- **EPIPE handler** on stdout.write + `process.on('uncaughtException')` for graceful crash recovery
- **Bidirectional health monitoring** — implement aggressive ping polling + AbortController timeouts
- **Session transport registry** — single registry of transport objects per session ID
- **Never use Streamable HTTP stateless mode** until SDK fix lands

---

## Friction Area 7: Zod Schema Edge Cases

**Build plan:** §5.6 (tool definitions)  
**Confidence:** █████████░ 90% — 13 confirmed bugs in TypeScript SDK

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-7.1 | **Zod v4 incompatibility**: `_parse is not a function`, `literal must be a string` | TS-SDK #555 (P0), #1380, #796 | 🔴 Critical |
| FR-7.2 | `$ref`/`$defs` in schemas **crash AJV validation** in `tools/list` | TS-SDK #1175, #1562 | 🔴 Critical |
| FR-7.3 | `.transform()` functions **lost during JSON Schema conversion** | TS-SDK #702 | 🟠 High |
| FR-7.4 | `.describe()` on optional fields **silently lost** with Zod 4 | TS-SDK #1143 | 🟠 High |
| FR-7.5 | JSON Schema **draft-07 vs draft-2020-12** mismatch — Claude Code returns `400` | TS-SDK #745 | 🟠 High |
| FR-7.6 | All-optional schemas: models call without `arguments` at all, Zod validation fails | TS-SDK #400 | 🟡 Medium |
| FR-7.7 | Top-level `z.union(...)` rejected — `registerTool` requires `ZodRawShape` | TS-SDK PR #816 | 🟡 Medium |
| FR-7.8 | LLM sends `"123"` where number expected — need **type coercion** at boundary | TS-SDK #1361 | 🟡 Medium |

### Mitigations to Add
- **Pin Zod to exact SDK-targeted version** (currently v4 with v3.25+ compat)
- **NEVER use** `.transform()`, `.preprocess()`, top-level unions, or all-optional schemas in tool inputs
- **Use `z.coerce.*`** for narrow fields (numbers, booleans) LLMs commonly mis-type
- **Schema export CI gate**: generate `tools/list`, assert all `inputSchema.type === "object"`, no `$ref`
- **Fully dereference** all schemas — strip `$defs`/`definitions` before export

---

## Friction Area 8: Binary Content / Response Limits

**Build plan:** §5.6 (tool responses)  
**Confidence:** ████████░░ 80% — hard limits confirmed but workarounds exist

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-8.1 | Claude Desktop **1MB cap** on tool-returned content — base64 33% overhead means ~750KB image limit | MCP Discussion #1204, Servers #297 | 🟠 High |
| FR-8.2 | MCP tool responses exceeding **25,000 tokens** cause complete tool call failure | Anthropic docs, RecceHQ blog | 🔴 Critical |
| FR-8.3 | Root-level JSON arrays **silently truncated** — only last element passed to LLM (Cursor bug) | Cursor forum #150134 | 🔴 Critical |
| FR-8.4 | **No URL-based image support** in MCP spec — base64 only | MCP Issues #793 | 🟡 Medium |
| FR-8.5 | Cursor **cannot display base64 images from MCP tools at all** | Cursor staff confirmation, forum #48801 | 🟠 High |

### Mitigations to Add
- **Response envelope pattern**: always `{"data": [...], "metadata": {"count": N}}` — never raw arrays
- **Response size gate**: intercept payload pre-serialization, auto-paginate if >80KB
- **Chart images at reduced resolution** (<750KB pre-encoding) or markdown links to hosted images
- **Pagination cursors** for large datasets — prompt LLM to query sequentially

---

## Friction Area 9: Cross-platform Process Management

**Build plan:** §5.7 (process isolation)  
**Confidence:** █████████░ 90% — fundamental Node.js bug on Windows since 2016

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-9.1 | `child_process.fork()` with `detached: true` **does not work on Windows** | Node #5146 (2016), #36808 (2020), still open | 🔴 Critical |
| FR-9.2 | Claude Code **orphaned processes** running 3 days after app closed (macOS) | Claude Code #19201 | 🟠 High |
| FR-9.3 | Uvicorn **ignores SIGTERM** under `--reload` or multi-worker — hangs, corrupts SQLCipher | FastAPI #6912 | 🟠 High |
| FR-9.4 | MCP server boots faster than backend — **ECONNREFUSED** on bootstrap auth | Claude-code #15945 | 🟠 High |
| FR-9.5 | Windows "spawn npx ENOENT" — **most common MCP setup failure** on Windows | Cline #1948, Cursor, Claude Desktop | 🟠 High |

### Mitigations Already in Build Plan
- Process isolation via separate processes (§5.7) ✅

### Mitigations to Add
- **Platform-specific spawn logic**: Windows Job Objects, macOS `disown`, Linux `setsid`
- **Exponential-backoff health polling** at startup — wait for `/health` 200 before `tools/list`
- **Authenticated `/internal/shutdown`** endpoint on Python backend — programmatic teardown
- **Orphan process monitor** — periodic PID health check with cleanup
- **Avoid `npx` in spawn** — resolve binary path directly

---

## Friction Area 10: IDE Tool Limits

**Build plan:** §5.11 (client detection)  
**Confidence:** ██████████ 95% — hard limits confirmed with exact numbers

### Exact Client Limits

| Client | Tool Limit | Zorivest Impact |
|---|---|---|
| **Cursor** | 40 total (all servers) | 28 tools dropped (41%) 🔴 |
| **ChatGPT** | ~10 tools (5,000-token definition cap) | 58 tools dropped (85%) 🔴 |
| **Windsurf** | 100 total | Fits alone, 32 slots remaining 🟡 |
| **Claude Desktop** | ~100 (soft) | Fits, quality degrades 🟡 |
| **VS Code / Copilot** | 128 total | Fits, safest target 🟢 |
| **LLM accuracy** | Degrades at ~20, fails at ~46 | 68 tools far exceeds 🔴 |

### Known Workarounds from Other Projects

| Pattern | Project | Mechanism |
|---|---|---|
| Dynamic toolsets | GitHub MCP Server | 3 meta-tools → LLM enables groups on demand |
| Meta-tool proxy | mcp-hub-mcp | 2 tools (`list-all-tools`, `call-tool`) bypass limit entirely |
| Code Mode | Cloudflare MCP | 2 tools (`search`, `execute`) — LLM writes code against full API |
| Tool Search | FastMCP | BM25/regex search over tool descriptions |

### Mitigations to Add
- **Three-tier strategy** embedded in client detection:
  - Tier 1 (Cursor/ChatGPT): Static ≤40 tools via env-var category selection
  - Tier 2 (VS Code): Dynamic toolsets with meta-tools
  - Tier 3 (CLI/API): Full 68-tool registration
- **Token budget calculator** — pre-compute schema token count, enforce per-client limits

---

## Friction Area 11: REST Proxy Network (NEW — Not in original 10)

**Build plan:** §5.7 (process isolation), §5.13 (session management)  
**Confidence:** ████████░░ 80% — multiple production reports

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-11.1 | **Ephemeral port exhaustion** — rapid fetch() calls leave sockets in TIME_WAIT | OneUptime blog, undici discussions | 🟠 High |
| FR-11.2 | `tools/list_changed` notification causes client to **silently reset custom timeouts** to 180s default | GitHub Copilot CLI #1378 | 🟠 High |
| FR-11.3 | HTTP status codes must be translated to **JSON-RPC error codes** — naive forwarding crashes sessions | LibreChat #8635 | 🟠 High |
| FR-11.4 | Backend restart while MCP server active → **cascading connection errors** | DZone containers, Research file 4 | 🟡 Medium |

### Mitigations to Add
- **Custom `http.Agent`** with `keepAlive: true`, `maxSockets`, socket timeout pruning
- **HTTP→JSON-RPC error translation middleware**: 400→-32602, 404→-32601, 500→-32603
- **Exponential backoff retry wrapper** for ECONNREFUSED/ECONNRESET
- **Continuous health polling** independent of tool invocations

---

## Friction Area 12: Type System Drift (NEW — Not in original 10)

**Build plan:** §5.6 (tool definitions), REST API contracts  
**Confidence:** ████████░░ 80% — well-documented cross-language friction

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-12.1 | Zod `.optional()` vs Pydantic optional: LLMs emit `null`, Zod expects `undefined` | Reddit r/reactjs, Research file 4 | 🟠 High |
| FR-12.2 | Enum **case sensitivity**: TS accepts "Active", Python Enum rejects (expects "active") | Kotlinlang discussions, Research file 4 | 🟡 Medium |
| FR-12.3 | DateTime **Z suffix vs +00:00**: TypeScript emits `Z`, Pydantic may reject | Pydantic #9518, Python discussions | 🟡 Medium |
| FR-12.4 | JSON Schema **dialect mismatch**: Zod emits draft-07 markers, Pydantic emits different  | Anthropic claude-agent-sdk #105 | 🟡 Medium |

### Mitigations to Add
- **Single schema source of truth** — generate from Pydantic, consume in TS without re-inferring
- **Use `z.nullish()`** for all optional fields (accepts both `null` and `undefined`)
- **Normalization middleware** — pre-flight: replace `Z` with `+00:00`, normalize enum case
- **Automated code generation** — derive Zod types from Python backend's OpenAPI spec

---

## Friction Area 13: Trade Safety (NEW — Market Gap)

**Build plan:** §5.9 (guard middleware), §5.10 (confirmation flow)  
**Confidence:** █████████░ 90% — every financial MCP server surveyed relies on client-side HITL only

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-13.1 | **No financial MCP server** implements server-side trade confirmation | Alpaca, IBKR ecosystem (5+ implementations) | 🟠 High |
| FR-13.2 | LLMs **hallucinate `confirmation=true`** to bypass conversational HITL prompts | Reddit r/mcp, Research file 1 | 🔴 Critical |
| FR-13.3 | Paper trading is **the only safety mechanism** in Alpaca's official server | Alpaca MCP docs | 🟡 Medium |
| FR-13.4 | CoSig project uses **WebAuthn co-signing** (YubiKey/Touch ID) for destructive tools | github.com/skyforest/cosig | 🟢 Info |

### Zorivest Opportunity
Our `withConfirmation` middleware with server-side confirmation tokens would be **genuinely novel** in the MCP trading ecosystem. This is a differentiator.

### Mitigations to Add
- **Server-side nonce workflow**: reject initial `execute_trade` → return preview + crypto nonce → require second call with nonce
- **Never rely on LLM conversational discipline** for financial authorization
- **Annotate every tool**: `readOnlyHint: true` for market data, `destructiveHint: true` for execution

---

## Friction Area 14: SDK Version Migration (NEW — Timeline Risk)

**Build plan:** All MCP-related sections  
**Confidence:** ████████░░ 80% — v2 is on `main` branch, v1 is maintenance mode

### Critical Findings

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FR-14.1 | SDK v2 **on `main` branch** — v1.x is dead-end with 6-month maintenance window | TS-SDK #809, README | 🟠 High |
| FR-14.2 | v2 **decouples from Zod** — "bring your own validator" (TS-SDK #1252) | TS-SDK #1252 | 🟡 Medium |
| FR-14.3 | v2 removes Zod result schema parameter from `Protocol.request()`, `Client.callTool()` | TS-SDK PR #1606 | 🟡 Medium |
| FR-14.4 | TypeScript compilation **OOM (16GB+)** with large schema type sets | TS-SDK #985 (P0) | 🟠 High |
| FR-14.5 | SSE transport **removed** — Streamable HTTP is the only option going forward | TS-SDK FAQ, docs | 🟡 Medium |

### Mitigations to Add
- **Adapter layer** isolating SDK-specific concerns (tool registration, transport binding, schema export)
- **Validation as interface** — writable for both Zod and future validators
- **Pin TypeScript version** as carefully as SDK version — watch for compilation OOM
- **Budget v2 migration** as explicit MEU after initial implementation

---

## Confidence Assessment Summary

| Friction Area | Confidence | Evidence Quality |
|---|---|---|
| 1. Registration at Scale | 95% | Multiple SDK issues + 3-project comparison |
| 2. Middleware Composition | 80% | FastMCP only reference; TS has no precedent |
| 3. Dynamic Toolset Loading | 90% | GitHub MCP server is production reference |
| 4. Auth Bootstrap | 90% | Universal failure across 5+ client ecosystems |
| 5. Client Detection | 70% | No project implements — speculative but informed |
| 6. Transport | 90% | 5 failure modes with SDK issue numbers |
| 7. Zod Schema | 90% | 13 confirmed bugs with reproductions |
| 8. Binary Content | 80% | Hard limits confirmed, workarounds exist |
| 9. Process Management | 90% | Fundamental Node.js bug since 2016 |
| 10. IDE Tool Limits | 95% | Exact numbers from 5 clients |
| 11. REST Proxy Network | 80% | Production reports from multiple sources |
| 12. Type System Drift | 80% | Well-documented cross-language friction |
| 13. Trade Safety | 90% | Every financial MCP surveyed lacks this |
| 14. SDK Version Migration | 80% | v2 is imminent, timeline is public |

---

## What Zorivest Should Build That Nobody Else Has

Three genuine opportunities where Zorivest leads rather than follows:

1. **Adaptive client detection** (`clientInfo.name` → tier selection) — no project does this
2. **Server-side trade confirmation** (`withConfirmation` + crypto nonce) — every trading MCP relies on client-side HITL
3. **Composable TypeScript middleware** (`withGuard→withMetrics→withConfirmation`) — FastMCP has this in Python, but TypeScript equivalent doesn't exist

---

## Cross-Reference: Research Files → Friction Areas

| Research File | Primary Friction Areas Covered |
|---|---|
| [1 - Gemini - Python MCP](file:///p:/zorivest/_inspiration/pre-mortem_risk_mining_research/1%20-%20gemini%20-%20Python%20MCP%20Friction%20Analysis.md) | 1, 2, 4, 6, 8, 10, 13 |
| [2 - ChatGPT - TypeScript SDK](file:///p:/zorivest/_inspiration/pre-mortem_risk_mining_research/2%20-%20chatgpt%20-%20TypeScript%20MCP%20Server%20Friction%20Analysis%20for%20@modelcontextprotocol-sdk%20v1.x.md) | 1, 6, 7, 14 |
| [3 - Claude - Large-scale MCP](file:///p:/zorivest/_inspiration/pre-mortem_risk_mining_research/3%20-%20claude%20-%20Friction%20inventory%20for%20large-scale%20MCP%20servers.md) | 1, 2, 3, 5, 8, 10, 13 |
| [4 - Gemini - Hybrid Architecture](file:///p:/zorivest/_inspiration/pre-mortem_risk_mining_research/4%20-%20gemini%20-%20MCP%20Architecture%20Friction%20Research.md) | 4, 9, 11, 12 |
| [5 - Claude - Pre-mortem Synthesis](file:///p:/zorivest/_inspiration/pre-mortem_risk_mining_research/5%20-%20claude%20-%20Pre-mortem%20risk%20analysis%20for%20a%2068-tool%20MCP%20server.md) | 3, 4, 5, 6, 7, 9, 10, 14 |

---

## Pinned SDK Version & Issue Matrix

> **Added 2026-03-06.** Friction inventory items are dynamic inputs linked to SDK version, not static architectural premises. This section ensures friction items are re-evaluated at each implementation phase start.

| Aspect | Decision |
|---|---|
| **Pinned SDK** | `@modelcontextprotocol/sdk@^1.26.0` (v1.x production line) |
| **v2 policy** | Do NOT upgrade to v2 (`main` is pre-alpha). Pin to v1.x until v2 is GA. |
| **Issue tracking process** | At the start of each implementation phase, check status of all tracked issues against pinned SDK version. Update FR-* items accordingly. |

### Tracked SDK Issues

| Issue | Status (2026-03-06) | Friction Items Affected | Impact |
|---|---|---|---|
| [#1106](https://github.com/modelcontextprotocol/typescript-sdk/issues/1106) | ✅ Closed | FR-6.1, FR-6.2 | Streamable HTTP session handling fixed |
| [#1291](https://github.com/modelcontextprotocol/typescript-sdk/issues/1291) | 🔴 Open | FR-1.1 | `server.tool()` silently strips arguments when passed `z.object({...})` instead of raw Zod shape |
| [#1564](https://github.com/modelcontextprotocol/typescript-sdk/issues/1564) | 🔴 Open | FR-6.5 | STDIO hard-crash on EPIPE when client disconnects before response |
| [#911](https://github.com/modelcontextprotocol/typescript-sdk/issues/911) | 🔴 Open | *(no existing FR)* | `structuredContent` handling inconsistent across clients — blocks dual-format response contract |

### Phase-Start Check Protocol

1. Run `npm view @modelcontextprotocol/sdk versions --json` to confirm latest v1.x
2. Check each tracked issue on GitHub for status changes
3. Update the table above with current status
4. If a tracked issue is resolved, update the corresponding FR-* friction items
5. If a new friction-relevant issue is discovered, add it to the table
