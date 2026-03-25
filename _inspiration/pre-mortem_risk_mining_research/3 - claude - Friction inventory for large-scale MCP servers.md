# Friction inventory for large-scale MCP servers

**The single biggest threat to Zorivest's 68-tool architecture is Cursor's hard 40-tool cap**, which silently drops tools beyond that limit across all connected servers. Every large MCP server project eventually collides with this wall, and only one — GitHub's official MCP server — has shipped a production-grade workaround: dynamic toolset discovery via meta-tools. Beyond tool limits, this research surfaces 13 confirmed Zod schema bugs in the TypeScript SDK, confirms that `notifications/tools/list_changed` is unsupported by Claude Desktop and Cursor, and reveals that no financial MCP server has implemented server-side trade confirmation — they all rely on client-side human-in-the-loop and paper trading modes.

This report inventories **10 real projects** across TypeScript, Python, hybrid architectures, and the finance domain, mapping each against Zorivest's 10 friction areas. Findings are sourced from GitHub issues, PRs, forum threads, and official documentation.

---

## The two largest TypeScript MCP servers and what broke

### 1. wrenchpilot/it-tools-mcp — 121 tools

**GitHub:** https://github.com/wrenchpilot/it-tools-mcp | **Stars:** 19 | **Commits:** 258 | **License:** MIT

**Architecture:** TypeScript MCP server using `@modelcontextprotocol/sdk` with Zod validation. **121 tools** organized across **14 category directories** under `src/tools/` (network/23, text/19, dataFormat/12, crypto/9, encoding/8, utility/7, math/6, development/6, ansible/5, docker/5, idGenerators/4, physics/3, forensic/3, color/2). All tools registered at startup via central `src/index.ts`. Transport: stdio only (Docker-first deployment with security hardening — non-root user, read-only filesystem, memory caps).

**Top 5 friction points:**
1. **No tool-limit mitigation at all.** With 121 tools, this server is broken in Cursor (40-tool cap drops 81 tools), degraded in Windsurf (100-tool cap), and hits Claude Desktop's ~100-tool soft limit. No dynamic loading, no toolset filtering, no workaround implemented.
2. **All 121 tools registered at startup** — no lazy loading, no deferred registration. Every client session loads every tool regardless of need.
3. **No middleware layer** — no auth, no rate limiting, no metrics wrapping. Tools execute directly.
4. **No `list_changed` capability** — cannot dynamically enable/disable tool groups.
5. **Zero open issues** — paradoxically a signal of low real-world usage at scale, not stability.

**Learn from:** The 14-category directory structure is a clean organizational model — each category exports tools with Zod schemas from its own `index.ts`. Docker security hardening (no-new-privileges, cap-drop ALL, read-only filesystem) is production-quality.

**Avoid:** Registering all tools unconditionally. At 121 tools, this server demonstrates exactly the anti-pattern Zorivest must avoid.

### 2. SmartBear/smartbear-mcp — 67 tools

**GitHub:** https://github.com/SmartBear/smartbear-mcp | **Stars:** 18 | **Commits:** 485 | **License:** MIT

**Architecture:** TypeScript MCP server with **67 tools** spanning 9 SmartBear product hubs (BugSnag, Reflect, Swagger/API Hub, PactFlow, Pact Broker, QMetry, Zephyr, Collaborator, Studio). Each hub is a separate integration module requiring its own API key. Transport: stdio. SDK: `@modelcontextprotocol/sdk`.

**Top 5 friction points:**
1. **Exceeds Cursor's 40-tool limit** with no documented workaround. At 67 tools, 27 are silently inaccessible in Cursor.
2. **VS Code env injection bug** (documented in anthropics/claude-code#28090): Environment variables from global `~/.claude/mcp.json` are NOT passed to the server process in the VS Code extension. Tools register but fail at runtime with missing credentials.
3. **No toolset selection within the server** — all configured hub tools are always exposed. Partial mitigation: omitting API keys for unused products reduces tool count, but this is manual.
4. **No dynamic tool management** — no `list_changed`, no on-demand loading.
5. **9 open PRs suggest active but incomplete development** — architecture is still evolving.

**Learn from:** The env-var-gated hub activation is a primitive but functional form of conditional tool registration. The enterprise-grade CI (pre-commit hooks, CODEOWNERS, Biome linter, Vitest coverage, SECURITY.md) sets a high bar. Multi-hub architecture maps cleanly to Zorivest's 10 categories.

**Avoid:** Relying on environment variables as the only mechanism for tool filtering. This requires users to manually manage which hubs are active.

| Friction Area | it-tools-mcp | SmartBear |
|---|---|---|
| 1. Registration at scale | All 121 at startup ❌ | All 67 at startup ❌ |
| 2. Middleware composition | None ❌ | None ❌ |
| 3. Dynamic toolset loading | None ❌ | None ❌ |
| 4. Auth bootstrap | None (utility tools) | Per-hub API keys ✅ |
| 5. Client detection | None ❌ | None ❌ |
| 6. Transport (Streamable HTTP) | stdio only | stdio only |
| 7. Zod schema edges | Uses Zod, no reported issues | Uses Zod, no reported issues |
| 8. Binary content | Not applicable | Not applicable |
| 9. Cross-platform process mgmt | Docker-first ✅ | Docker + npx ✅ |
| 10. IDE tool limits | Broken in Cursor ❌ | Broken in Cursor ❌ |

---

## GitHub's MCP server sets the gold standard for tool-limit workarounds

### 3. github/github-mcp-server — 101 tools (reference implementation)

**GitHub:** https://github.com/github/github-mcp-server | **Language:** Go | **Stars:** 15k+

Although written in Go (not TypeScript), this is **the most important reference project** for Zorivest because it's the only major server that has shipped a production solution to the tool-count problem.

**The dynamic toolsets pattern:** With `--dynamic-toolsets` (or `GITHUB_DYNAMIC_TOOLSETS=1`), the server starts with only **3 meta-tools**: `list_available_toolsets`, `get_toolset_tools`, and `enable_toolset`. The LLM discovers what toolsets exist, inspects their contents, and enables only what's needed. When a toolset is enabled, the server sends `notifications/tools/list_changed` and the client refreshes.

**Default reduction (October 2025):** The team changed defaults from all tools to only 5 toolset groups (context, repos, issues, pull_requests, users), cutting from **101 tools / 64,648 tokens** to **52 tools / 30,300 tokens** — a 49% tool reduction and 53% token savings.

**Critical limitations of dynamic toolsets:**
- **Not available on the remote MCP server** (`api.githubcopilot.com/mcp/`) — local-only feature (Issue #1108)
- **Requires `list_changed` client support** — Claude Desktop and Cursor don't support it, severely limiting utility
- **Extra round-trips** — enabling a toolset costs 1-2 additional LLM calls before actual work
- **LLM-dependent quality** — weaker models may fail to use meta-tools effectively

**Direct relevance to Zorivest:** This is the pattern to implement. Zorivest's 68 tools across 10 categories map perfectly to a dynamic toolsets approach where the server starts with category-discovery meta-tools, then loads category tools on demand. But the `list_changed` support gap means Zorivest also needs a static fallback mode.

---

## The most mature Python MCP server proxies to a REST API

### 4. homeassistant-ai/ha-mcp — 80+ tools

**GitHub:** https://github.com/homeassistant-ai/ha-mcp | **Stars:** ~1,000 | **Commits:** 743 | **Open Issues:** 34

**Architecture:** Python MCP server using FastMCP (which wraps the official `mcp` SDK) with **80+ tools** across entity management, automation, dashboards, areas/floors/zones, labels, todo/calendar, system operations, templates, logbook, notifications, and integration lifecycle. Transports: stdio, HTTP, SSE (via separate fastmcp config files). **Crucially, this is itself a hybrid architecture** — the MCP server proxies all operations to Home Assistant's REST and WebSocket APIs.

**Top 5 hardest issues:**
1. **Resource file packaging bug** (Issue #225): `dashboard_guide.md` and `card_types.json` missing when installed via pip — path resolution fails in packaged distributions. Runtime errors on import.
2. **Potential deprecation risk** (Discussion #477): Official Home Assistant team reached out about feature overlap — HA Core may implement native MCP, potentially obsoleting this server.
3. **Docker networking complexity**: Container-to-host networking for HA access requires `host.docker.internal` or `--network host`, a recurring support burden.
4. **Concurrent operation performance**: Documentation warns about slowness with simultaneous AI operations; recommends monitoring HA system resources.
5. **Custom component requirement**: Filesystem access tools require installing a separate HA custom component (`ha_mcp_tools`), fragmenting the install process.

**Learn from:** Comprehensive E2E test suite organized into `basic/`, `workflows/`, `error_handling/` directories. Structured error returns (`{"success": False, "error": "Path not allowed: {path}"}`). The proxy-to-REST-API architecture is directly analogous to Zorivest's TypeScript→Python pattern.

---

## Hybrid architecture projects validate the proxy pattern

### 5. thoughtworks/mcp4openapi — TypeScript MCP → REST API

**GitHub:** https://github.com/thoughtworks/mcp4openapi | **Stars:** 5 | **Commits:** 59

**Architecture:** The **closest analog to Zorivest's architecture**. Three components: a TypeScript MCP server (`mcp-openapi/`) auto-generates tools from OpenAPI specs, a Node.js REST API (`sample-banking-api/`) with JWT auth and banking data, and a test client. The MCP server acts as a transparent proxy — each OpenAPI operation becomes an MCP tool. **61/61 tests passing.**

**Key design decisions:**
- **1:1 OpenAPI-to-MCP mapping**: Each REST endpoint automatically becomes a tool — no manual tool definition
- **Auth token passthrough**: MCP server passes JWT tokens from the client through to the backend API
- **Custom prompts augmentation**: Config files add MCP prompts to enrich auto-generated tools
- **Dual transport**: stdio and HTTP modes

**ThoughtWorks' insight:** "MCP capabilities like tools and resources are a direct 1:1 mapping for RESTful APIs and can be dynamically generated based on their specifications in OpenAPI." This validates Zorivest's approach of proxying to a Python REST API — the MCP layer can be generated from the API spec.

### 6. gujord/OpenAPI-MCP — most mature OpenAPI proxy

**GitHub:** https://github.com/gujord/OpenAPI-MCP | **Stars:** 58 | **Language:** Python

The **most feature-rich OpenAPI-to-MCP proxy** found. Comprehensive OAuth2 Client Credentials flow with automatic token caching/renewal, plus API Key, Bearer, Basic, and Custom Header auth. Dual transport (stdio and HTTP). Resource registration from OpenAPI component schemas. **Dry-run mode** for previewing requests without execution — directly relevant to Zorivest's trading safety needs.

**Error handling reference:** "Comprehensive exception hierarchy with proper JSON-RPC error codes and structured error responses" — the most mature error handling of all proxy projects.

### 7. microsoft/mcp-gateway — enterprise gateway

**GitHub:** https://github.com/microsoft/mcp-gateway | **Language:** Go/TypeScript

Enterprise-grade reverse proxy for MCP servers in Kubernetes. Azure Entra ID auth with RBAC roles (`mcp.admin`, `mcp.engineer`). Session-aware stateful routing with distributed session store. Tool Gateway Router acts as intelligent router to registered tool servers. **Most relevant for:** auth bootstrap lifecycle, transport compatibility, and cross-platform deployment patterns.

### 8. mkbhardwas12/mcp-bridgekit — "nginx for MCP tools"

**GitHub:** https://github.com/mkbhardwas12/mcp-bridgekit | **Language:** Python + TypeScript

FastAPI server bridging stdio MCP servers to HTTP with Redis job queue. **Unique long-running operation pattern**: tool calls exceeding 25 seconds are automatically queued as background jobs; user gets a `job_id` instantly and polls for results. Per-user session isolation. Prometheus metrics endpoint. **Most relevant for:** Zorivest's cross-language bridging and long-running trading operations.

---

## Financial MCP servers rely entirely on paper trading for safety

### 9. alpacahq/alpaca-mcp-server — official trading server

**GitHub:** https://github.com/alpacahq/alpaca-mcp-server | **Stars:** ~496 | **Forks:** ~149

**Architecture:** Full trading server for stocks, ETFs, crypto, and options via Alpaca's API. Tools include `place_stock_order`, `place_crypto_order`, `place_option_order`, `exercise_options_position`, plus portfolio management and market data. Auth via `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` environment variables.

**Safety patterns (and their gaps):**
- **Paper trading is the primary safety mechanism** — switch between paper ($100K simulated) and live by changing API keys. No server-side distinction between modes.
- **No built-in confirmation step** — orders execute immediately when the tool is called.
- **No dry-run mode** — no way to preview an order before submission.
- **No server-side annotations** for `destructiveHint` — relies entirely on client-side human-in-the-loop.
- **Risk disclaimers in docs** note "model assumptions can impact performance and accuracy."
- Alpaca's recommendation: "Review and confirm orders directly on your Alpaca dashboard."

**Critical lesson for Zorivest:** The complete absence of server-side trade confirmation in the most popular trading MCP server represents a **market gap** Zorivest can fill. Implementing `destructiveHint: true` annotations plus a server-side confirmation token flow for trade execution would be a genuine differentiator.

### 10. Interactive Brokers MCP ecosystem — 5+ implementations

Multiple IBKR MCP servers with varying safety postures:
- **Hellek1/ib-mcp** (https://github.com/Hellek1/ib-mcp): **Deliberately read-only** — "Ideal for feeding financial data into LLM workflows while keeping trading disabled." The most conservative safety choice.
- **code-rabi/interactive-brokers-mcp** (https://github.com/code-rabi/interactive-brokers-mcp): Full trading with OAuth, headless auth, and paper trading via `IB_PAPER_TRADING=true`.
- **ArjunDivecha/ibkr-mcp-server**: "Trading Operations — Place, modify, cancel orders (with safety checks)" but safety check details unspecified.
- **GaoChX/ibkr-mcp-server**: Notes "implement proper risk controls in production environments" — acknowledging the gap.

**Pattern observed:** The IBKR ecosystem splits into read-only data servers and full-execution servers. No middle ground (dry-run, confirmation tokens) exists.

---

## IDE tool limits are confirmed, and the numbers are exact

Every major IDE enforces hard tool-count caps. Zorivest's 68 tools exceed Cursor's limit and consume most of every other client's budget.

| IDE Client | Tool Limit | Zorivest Impact | Source |
|---|---|---|---|
| **Cursor** | **40 total** (all servers combined) | 28 tools silently dropped | forum.cursor.com/t/67976 |
| **Windsurf** | **100 total** | Fits but leaves only 32 for other servers | docs.windsurf.com |
| **Claude Desktop** | **~100** (soft) | Fits, but LLM quality degrades | modelcontextprotocol discussions/537 |
| **VS Code / Copilot** | **128 total** | Fits, safest target | microsoft/vscode/issues/290356 |
| **LLM selection quality** | **Degrades at ~20, fails at ~46** | Zorivest's 68 tools far exceed this | speakeasy.com analysis |

**Community workarounds found:**
- **Dynamic toolsets** (GitHub MCP server): Start with 3 meta-tools, LLM enables groups on demand
- **mcp-hub-mcp proxy**: Consolidates all tools behind 2 meta-tools (`list-all-tools`, `call-tool`), bypassing the limit entirely (forum.cursor.com/t/78040)
- **Code Mode** (Cloudflare MCP): Expose just 2 tools (`search` + `execute`) where the LLM writes code against the full API
- **Spec proposals in progress**: SEP-1300 (Tool Filtering with Groups and Tags) and SEP-1821 (Dynamic Tool Discovery via query parameter on tools/list)

**Recommendation for Zorivest:** Implement a three-tier strategy: (1) Static mode with environment-variable-based category selection for Cursor users (expose ≤40 tools), (2) Dynamic toolsets mode with meta-tools for VS Code/Copilot users, (3) Full registration for clients with high limits. Detect the client via `clientInfo` and auto-select the appropriate tier.

---

## `list_changed` notifications have critical client support gaps

The `notifications/tools/list_changed` mechanism — essential for dynamic tool loading — is only supported by **2 of 5 major clients**.

| Client | list_changed Support | Evidence |
|---|---|---|
| **VS Code / Copilot** | ✅ Confirmed | Microsoft docs: "subscribes to notifications/tools/list_changed, resets tool permissions, refetches tool list" |
| **Visual Studio** | ✅ Confirmed | learn.microsoft.com docs confirm |
| **Claude Desktop** | ❌ Not supported | MCP maintainer @jspahrsummers confirmed Dec 2024; still broken as of v0.9.2 (late 2025) |
| **Cursor** | ❓ Unconfirmed | No documentation found confirming support |
| **Windsurf** | ❓ Unconfirmed | No documentation found |

**Critical edge case:** VS Code resets all prior tool permissions when `list_changed` fires — treating dynamic tool changes as a potential "rug-pull attack." Users must re-approve tools after every toolset change. This creates friction for dynamic toolset loading.

**Stale tool list risk:** If a client caches tools and ignores `list_changed`, calling a tool that no longer exists returns a protocol error. The spec doesn't define graceful behavior for this case — it's up to server implementations to handle calls to unregistered tools.

---

## Annotations have narrow but actionable client support

Tool annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) are "hints only" per the spec — "clients should never make security-critical decisions based solely on annotations." But two clients do use them:

- **VS Code:** Tools with `readOnlyHint: true` skip the confirmation dialog entirely. All other tools require user approval. This directly improves UX.
- **ChatGPT Dev Mode:** Tools without `readOnlyHint: true` show a "WRITE" badge. Setting it removes the badge and unnecessary confirmation prompts.
- **Cursor, Windsurf:** No documented annotation support.

**No server-side confirmation token pattern exists in the MCP spec.** Custom implementations found:
- **CoSig** (https://github.com/skyforest/cosig): WebAuthn co-signing — `@require_approval()` decorator triggers YubiKey/Touch ID tap before destructive tools execute.
- **Claude Code hooks pattern**: Script-based permission request hook that classifies tool names as safe/destructive by keyword matching and auto-approves or prompts accordingly.
- **WorkOS recommendation**: Tag actions by sensitivity (LOW/MED/HIGH); HIGH actions require explicit approval via authenticated UI + MFA.

**Relevance to Zorivest:** Annotate every tool. Set `readOnlyHint: true` on all read-only market data tools (VS Code will skip confirmation for these). Set `destructiveHint: true` on `place_order`, `cancel_order`, and similar. Then implement a custom `withConfirmation` middleware for annotation-unaware clients — returning a confirmation token that must be passed back to execute.

---

## Middleware patterns are framework-specific, not spec-level

**Middleware is NOT part of the MCP specification.** It's entirely framework-specific. The most mature implementation is FastMCP's pipeline model (Python), which Zorivest's TypeScript `withGuard→withMetrics→withConfirmation` pattern should emulate.

**FastMCP's middleware architecture** (https://gofastmcp.com/servers/middleware):
- **Pipeline/onion model**: Request → Middleware A → Middleware B → Handler → B → A → Response
- **Hook hierarchy**: Message-level (`on_message`) → Type-level (`on_request`) → Operation-level (`on_call_tool`, `on_list_tools`)
- **Built-in classes**: LoggingMiddleware, TimingMiddleware, ResponseCachingMiddleware, **RateLimitingMiddleware**, ErrorHandlingMiddleware
- **Denial pattern**: Middleware rejects by NOT calling `call_next()` — raising `McpError(ErrorData(...))` or returning an error result
- **Error semantics**: Raising `McpError` before `call_next()` sends error to client. Raising after `call_next()` only logs — the response is already sent. **ErrorHandlingMiddleware should always be added first** to catch downstream errors.
- **Composition**: Parent middleware runs for ALL requests (including mounted child servers). Child middleware only runs for that child's tools. This enables global auth + per-service logging.

**Per-tool authorization patterns found:**
- **ToolHive** uses Amazon Cedar policy language for `Action::"call_tool"` + `Resource::"{tool_name}"` evaluation
- **Cerbos + FastMCP**: Queries Cerbos PDP at session start to determine per-user tool access, dynamically enabling/disabling tools
- **RBAC with Keycloak**: Each tool registered with explicit access requirements; a `get_my_permissions` meta-tool lets users inspect their roles
- **Red Hat MCP Gateway (Envoy-based)**: Identity-based tool filtering at gateway level with OAuth2 Token Exchange (RFC 8693)

**Circuit breaker patterns:** IBM's MCP Context Forge (https://github.com/IBM/mcp-context-forge/issues/301) has a detailed circuit breaker spec: CLOSED → OPEN (after N failures) → HALF_OPEN (after timeout), with <10ms fast failure when open and per-server configurable thresholds. No other MCP project ships a circuit breaker.

**Rate limiting:** The recommended pattern is token-bucket for burst handling, with per-tool granularity (tighter limits on expensive operations like trade execution, looser on reads). Redis-backed counters for distributed setups.

---

## Zod schema edge cases are a minefield in the TypeScript SDK

The MCP TypeScript SDK has **13 confirmed Zod-related bugs**, several at P0/P1 severity. These are real risks for Zorivest's 68-tool Zod schema surface:

**Show-stoppers:**
- **Zod v4 incompatibility** (Issues #555, #925, #906): SDK internally calls `_parse` and `_def.value`, which v4 restructured. The SDK now requires Zod v4 with backwards compat for v3.25+, but version mismatches cause `_parse is not a function` errors.
- **Field descriptions silently lost** (Issue #1143): `.describe()` on optional fields in Zod 4 schemas doesn't propagate to the JSON Schema output in `listTools`. LLMs lose parameter context.
- **JSON Schema draft mismatch** (Issue #745): SDK generates draft-07, Claude Code requires draft-2020-12. Returns `400` errors.
- **Transform functions stripped** (Issue #702): `z.union([z.array(z.string()), z.string()]).transform(...)` loses union branches during JSON Schema conversion.

**Subtle traps:**
- **All-optional schemas break** (Issue #400): When every field is optional, models call without `arguments` at all. Zod validation fails — the SDK doesn't default to `{}`.
- **Top-level unions rejected** (PR #816): `z.union(...)` can't be used at the tool input level — `registerTool` requires `ZodRawShape`.
- **`.passthrough()` everywhere** (Issue #182): Almost every Zod schema in the SDK uses `.passthrough()`, breaking type safety.
- **`server.tool()` silently strips arguments** (Issue #1291/1380): Certain ZodObject schemas cause all parameters to disappear.

**Recommendation:** Pin Zod to the exact version the SDK targets (currently v4). Avoid transforms, unions at root level, and all-optional schemas. Test every tool's JSON Schema output against what clients actually receive via `tools/list`.

---

## Binary content handling is base64-only with a 1MB ceiling

MCP supports image content exclusively via inline base64 encoding (`{"type": "image", "data": "<base64>", "mimeType": "image/png"}`). **No URL-based image support** exists (Feature Request modelcontextprotocol/issues/793).

**Hard limits:**
- **Claude Desktop: ~1MB** per tool-returned content (base64 or text). Larger images cause errors.
- **Base64 overhead: 33%** — a 750KB image becomes ~1MB as base64, hitting the limit.
- **No `FileContent` type** in the protocol — developers "abuse the image response to pass non-image binary data."
- **Token explosion**: A moderate base64-encoded file can reach 1.95M tokens, far exceeding context windows.

**For Zorivest:** Return chart images at reduced resolution (<750KB pre-encoding). For larger visualizations, return markdown links to hosted images. Consider implementing a resource URI pattern where charts are served via MCP resources rather than inline tool results.

---

## Consolidated friction matrix across all 10 projects

| Friction Area | Best Reference | Key Finding |
|---|---|---|
| **1. Registration at scale** | GitHub MCP Server | Dynamic toolsets with 3 meta-tools; default to 52/101 tools |
| **2. Middleware composition** | FastMCP (Python) | Pipeline/onion model with hook hierarchy; ErrorHandling first |
| **3. Dynamic toolset loading** | GitHub MCP Server | Works in VS Code only; Claude Desktop and Cursor don't support `list_changed` |
| **4. Auth bootstrap** | microsoft/mcp-gateway | Azure Entra ID + RBAC; per-tool OAuth scopes emerging (SEP-1880) |
| **5. Client detection** | None found | No project implements `clientInfo`-based adaptive behavior — Zorivest would be first |
| **6. Transport (Streamable HTTP)** | MCP TypeScript SDK | SSE and Streamable HTTP are NOT cross-compatible; sticky sessions required; Python SDK has Cloud Run issues |
| **7. Zod schema edges** | TypeScript SDK issues | 13 bugs: v4 compat, lost descriptions, draft mismatch, stripped transforms |
| **8. Binary content** | MCP spec | Base64-only, 1MB Claude Desktop cap, 33% encoding overhead |
| **9. Cross-platform process** | mcp-bridgekit | Redis job queue for long-running ops; per-user session isolation |
| **10. IDE tool limits** | Cursor forums + GitHub MCP | 40 (Cursor), 100 (Windsurf), ~100 (Claude), 128 (VS Code); LLM degrades at ~20 |

---

## What Zorivest should build that nobody else has

Three opportunities emerge where Zorivest can lead rather than follow. First, **adaptive client detection** — no project currently reads `clientInfo` to adjust behavior. Zorivest should detect Cursor and auto-reduce to ≤40 tools, detect VS Code and enable dynamic toolsets, and fall back to full registration for unknown clients. Second, **server-side trade confirmation** — every trading MCP server found relies exclusively on client-side human-in-the-loop. A `withConfirmation` middleware that returns a confirmation token with order preview details, requiring a second tool call to execute, would be genuinely novel. Third, **composable TypeScript middleware** mirroring FastMCP's pipeline model but in TypeScript — `withGuard→withMetrics→withConfirmation→handler` with proper error semantics (throw before `next()` = client error, throw after = log only).

The hybrid TypeScript→Python architecture is well-validated by ThoughtWorks' mcp4openapi, gujord's OpenAPI-MCP, and ha-mcp's pattern. The OpenAPI spec as the contract between languages eliminates serialization issues and enables auto-generation of tool definitions. The 68-tool scale is achievable but demands dynamic toolset discovery as a first-class feature, not an afterthought.
