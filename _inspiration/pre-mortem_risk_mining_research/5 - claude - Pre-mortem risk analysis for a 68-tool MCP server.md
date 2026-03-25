# Pre-mortem risk analysis for a 68-tool MCP server

A large-scale MCP server with 68 tools will hit critical, well-documented failures across client tool caps, SDK stability, auth lifecycle, and process management — problems that are systemic rather than edge cases. **Cursor's 40-tool hard cap alone renders 41% of your toolset invisible**, and the TypeScript SDK's Streamable HTTP transport has fundamental architectural bugs in stateless mode, session management, and async tool handling. Token refresh is broken across virtually every MCP client-server combination, and cross-platform process detachment relies on Node.js APIs that have been documented as broken on Windows since 2016. This analysis maps 100+ specific GitHub issues, PRs, and community reports across your four risk vectors, organized by severity to support prioritized mitigation.

---

## Vector 1: The TypeScript SDK is a moving target with critical Zod and transport bugs

### Tool registration silently fails under specific conditions

The SDK itself imposes no tool count ceiling, but **`server.tool()` silently drops all parameters** if you pass a `z.object({...})` instead of a raw Zod shape (`{key: z.string()}`). This is documented in Issue #1291 and #1380 on `typescript-sdk` — the tool registers without error, appears in `tools/list`, but receives an empty argument object at invocation. For a 68-tool server where exhaustive testing of every parameter path is expensive, this silent failure mode is the highest-priority SDK risk.

A second schema-layer bug: `zodToJsonSchema` in SDK versions prior to recent patches generated **JSON Schema draft-07**, but Claude Code required **draft-2020-12**, producing hard `400` errors on every tool call (Issue #745). The `ListTools` handler itself has returned `{type: "string"}` instead of object schemas (Issue #1028), making tools appear to accept a single string rather than structured input.

### Zod version fragmentation creates deployment blockers

The Zod 3 → Zod 4 transition is labeled **P0 (broken core)** in Issue #555. SDK v1.x was built against Zod 3; projects on Zod 4 hit `_ZodNumber missing properties from ZodType` errors (Issue #796) and initialization failures where `McpServer` constructor throws "Schema method literal must be a string" because Zod 4 stores literals at `_def.values[0]` instead of `_def.value` (Issue #1380). Tool descriptions silently vanish with Zod 4 until the fix in v1.25.0 PR #1296. Union types with `.transform()` lose branches during JSON Schema conversion (Issue #702).

### Streamable HTTP transport has 5 distinct failure modes

This transport is not production-ready for scaled deployment:

- **Sticky sessions required** — in-memory session storage means any request hitting a different pod returns `400: No transport found for sessionId` (Issue #330, #273)
- **Stateless mode is broken** — `validateSession` always fails because `this._initialized` is perpetually false (Issue #340)
- **Async tool handlers time out** — any tool performing I/O gets `MCP error -32001: Request timed out` on Streamable HTTP (Issue #1106)
- **Notifications silently dropped** — when `enableJsonResponse: true`, progress notifications vanish (Issue #866)
- **Cross-client data leak** — security advisory GHSA-345p-7cg4-v4c7 (fixed in v1.26.0): reusing a single `StreamableHTTPServerTransport` across requests causes JSON-RPC message ID collisions and responses routed to wrong clients

### SDK v2 is weeks away, making v1.26.0 a dead-end investment

SDK v2 is on the `main` branch in pre-alpha, targeting **Q1 2026 stable release** (Issue #809). V2 decouples from Zod entirely, rewrites `protocol.ts`, and splits into multiple packages. V1.x gets 6 months of maintenance post-v2. Building 68 tools on `^1.26.0` guarantees a major migration. Additionally, the SDK causes **TypeScript compilation OOM** — 4GB+ heap exhaustion in CI/CD from 104 `.d.ts` files (Issue #985, labeled P0).

### `list_changed` and annotations are unreliable across clients

Dynamic tool loading via `notifications/tools/list_changed` has **no client support guarantee**. Discussion #1384 on the spec repo states plainly: "there is no guarantee that the client will do that." SDK client-side support for list_changed handlers was only added in v1.25.0 (PR #1206). Even clients that support it re-fetch ALL tools rather than accepting incremental updates (Discussion #94).

For `destructiveHint` annotations: only **ChatGPT Dev Mode** reliably displays badges and confirmation prompts. JetBrains Copilot doesn't honor `readOnlyHint` (Issue #724). Claude Desktop, Cursor, Windsurf, and Cline show no evidence of annotation-driven approval flows. Most official MCP servers don't even set annotations yet (Issue #2988).

| SDK risk | Severity | Key issues |
|----------|----------|------------|
| Silent argument stripping | Critical | #1291, #1380 |
| JSON Schema draft mismatch | Critical | #745 |
| Streamable HTTP stateless mode | Critical | #340, #412, #508 |
| Async tool timeout on HTTP transport | Critical | #1106 |
| Cross-client data leak (pre-1.26.0) | Critical | GHSA-345p-7cg4-v4c7 |
| Zod 3/4 initialization failure | Critical | #555 (P0), #1380 |
| SDK v2 migration overhead | High | #809 |
| TypeScript OOM in CI/CD | High | #985 (P0) |
| list_changed client support | High | Discussion #1384 |
| SSE backward compat breaks | Medium | #1233, PR #1216 |

---

## Vector 2: Python ecosystem shares the same scaling walls, with worse middleware composition

### FastMCP vs official SDK is an unresolved fork crisis

FastMCP 1.0 was absorbed into the official SDK as `mcp.server.fastmcp`, but FastMCP 2.x diverged into an independent project under `jlowin/fastmcp` (now 3,300+ issues). Issue #1068 on `python-sdk` is labeled **P0** and tracks the confusion. The official SDK is planning its own v2 rewrite. Teams must choose between the official SDK (which lacks middleware) and FastMCP 2.x (which has middleware but is a third-party dependency with its own breaking changes, including a **30% memory regression** in v2.14.1 per Issue #2638).

### Middleware composition is broken at multiple layers

The most critical middleware bug: mounting an MCP SSE app behind **any** Starlette `BaseHTTPMiddleware` — even a trivial pass-through — throws `AssertionError: Unexpected message` (python-sdk Issue #883, P1, 6+ thumbs-up). This affects guard and auth middleware patterns directly. In FastMCP specifically: middleware cannot access `request_context` after v2.13 (Issue #2393), headers set in Starlette middleware are invisible inside tool functions (Issue #817), session IDs return `None` in middleware (Issue #933), and `McpError` raised during initialization doesn't propagate as JSON-RPC errors (Issue #2552). Shared ASGI middleware state between FastAPI and FastMCP doesn't compose cleanly (Discussion #732).

### Memory leaks and session persistence are production blockers

Two confirmed memory leaks: continuous tool calls cause OOM in both FastMCP and raw SDK with streamable-http transport (Issue #1076), and stateless mode's task group never exits, growing the `_task` list unboundedly (Issue #756). Session persistence is **in-memory only** — `StreamableHTTPSessionManager` cannot use external stores, making horizontal scaling impossible (Issue #880, 17+ thumbs-up, P1). A FastMCP-specific crash: client timeout during tool execution produces `ClosedResourceError` that crashes the **entire server**, not just the session (Issue #823).

A race condition in StreamableHTTP's zero-buffer memory streams causes **deadlocks when tools return 3+ items** (Issue #1764). A separate race condition means ~1 in 5 post-initialization requests returns an empty tool list (Issue #1675, P1).

---

## Vector 3: Client tool caps are the hardest constraint, and 68 tools exceeds most of them

### Cursor's 40-tool cap silently truncates your server

Cursor enforces a **hard limit of 40 MCP tools total** across all connected servers. Tools beyond 40 are silently dropped — not errored, not warned, just invisible to the agent. This is confirmed across multiple Cursor forum threads (forum.cursor.com/t/tools-limited-to-40-total/67976, forum.cursor.com/t/mcp-40-tools-way-to-less/79686). A 68-tool server loses **28 tools (41%)** in Cursor. The community workaround is "mcp-hub-mcp," a proxy that exposes all tools through 2 meta-tools.

### Every other client imposes its own ceiling

**Windsurf** caps at **100 tools total** — your 68 tools fit alone but consume 68% of the budget, leaving only 32 slots for other MCP servers. Users already report "adding this instance would exceed max allowed tools" errors. **GitHub Copilot** allows **128 tools**. **ChatGPT** imposes a brutal **5,000-token cap for ALL tool definitions combined** — at ~500 tokens per tool, 68 tools require ~34,000 tokens and will be **hard-rejected**. **Gemini CLI** has a 512 function declaration API limit but strips `$schema` and `additionalProperties` from schemas, potentially breaking validation (Issue #19083). **Claude Code** has no hard cap but activates **Tool Search** (lazy loading) when tool definitions exceed ~10% of context, changing discovery behavior so the LLM must search for tools rather than seeing all 68 upfront.

### Token bloat degrades tool selection accuracy before hitting hard limits

At **~500 tokens per tool, 68 tools consume ~34,000 tokens** before any reasoning begins — 17% of a 200K context window, or 100%+ of a 32K window. An extreme real-world case: a MySQL MCP server with 106 tools generated **207KB of schema data (~54,600 tokens)** on every initialization. Documented degradation patterns include LLMs picking wrong tools from similarly-named sets, freezing on selection with too many similar options, and hallucinating tool names that don't exist (jentic.com, lunar.dev). Anthropic's own engineering blog showed agents consuming ~72K tokens for 50+ MCP tools.

### `clientInfo.name` parsing is fragile but the only detection mechanism

The Apify team created a community-maintained JSON workaround (`mcp-client-capabilities`) because the protocol provides insufficient client capability information. Known `clientInfo.name` values: Claude Desktop reports `"claude-ai"` with version `"0.1.0"`, MCP Inspector reports `"mcp-inspector"`. But proxy clients like mcp-remote may report their own name, custom frameworks report arbitrary strings, and values change between versions. PulseMCP's analysis concludes: "Most of the MCP ecosystem is stuck catering to the lowest common denominator."

### No standardized namespace or toolset pattern exists yet

SEP-986 proposes standardized tool name format but is **not yet adopted**. Different frameworks use different separators: MetaMCP uses `ServerName__toolName` (double underscore), Gemini CLI auto-prefixes with `serverAlias__`, LiteLLM prefixes with server name. The official SDKs have no built-in grouping — Issue #829 (python-sdk) and SEP-1300 (tool filtering with groups/tags) are proposals only. Issue #1681 acknowledges "as soon as a server grows beyond a couple of tools, authors start reinventing patterns."

---

## Vector 4: Auth token refresh is universally broken, and process management is worse

### OAuth token lifecycle fails across every major MCP integration

This is the single most consistently documented failure across the ecosystem. **Atlassian's MCP server** fails to refresh tokens, continuing to send expired access tokens and producing 401s (Issue #12) — users report tokens expiring after 12 minutes, requiring re-authentication twice per working day. **GitHub Copilot CLI** never uses the refresh token: it tries the cached expired token, gets 401, and gives up (Issue #1797). **Google ADK** lets tokens expire in long sessions with no automatic refresh (Issue #3761). **Cursor** marks MCP servers as "Logged out" on 401 with no automated recovery (forum.cursor.com/t/missing-refresh-token-logic-for-mcp-oauth/130765).

FastMCP has three distinct token refresh bugs: refreshed tokens don't update the auth context due to immutable `ContextVar` (Issue #1863), tokens loaded from storage never refresh proactively (Issue #1649), and expired tokens return **400 instead of 401**, causing Cursor to enter infinite retry loops (Issue #2461). The MCP Inspector itself enters infinite OAuth loops (Issue #633).

### Base64 images hit a hard client fragmentation wall

**Claude Desktop** crashes on base64 image responses exceeding **~1MB** (Discussion #1204, Servers Issue #297). The official filesystem MCP server "pretty much prevents using it to interact with image files." **Cursor cannot display base64 images from MCP tools at all** — confirmed by Cursor staff: "There's no way to use an image produced by an MCP server in the Agent right now" (forum.cursor.com/t/mcp-image-support/48801). Even when images are small enough to transmit, LLMs sometimes concatenate the base64 string directly into context, causing cost explosion (MCP Issue #1049). The protocol currently supports only base64 encoding — URL references are proposed but not yet in spec (Issue #793).

### Cross-platform process detachment is broken at both the MCP and Node.js layers

Every major MCP host has documented orphaned process bugs. **Claude Code** doesn't properly terminate MCP servers on exit (Issue #1935), with Windows-specific reports of orphaned Python/Node processes accumulating indefinitely (Issue #15211). **macOS orphan processes** have been detected running **3 days** after Claude Desktop was closed (Issue #19201). **MetaMCP** reports child processes of terminated servers remaining in memory until server crash (Issue #128).

At the Node.js layer, `child_process.fork()` with `detached: true` **does not work on Windows** — this is a bug filed in 2016 (Node Issue #5146), re-filed in 2020 (Issue #36808), and still unresolved. `detached: true` with `unref()` still prevents parent exit on Windows (Issue #5614). `windowsHide` is incompatible with `detached` (Issue #21825). Non-Node executables like PowerShell silently fail to detach (Issue #51018). The Windows "spawn npx ENOENT" error — where `child_process.spawn` cannot find `npx` because it's a shell script — is the single most common MCP setup failure on Windows, documented across Cursor, Cline (Issue #1948), and Claude Desktop.

### REST proxy timeout cascades have no protocol-level mitigation

The TypeScript SDK client has a **hard-coded 60-second timeout** that is not reset by server progress updates (Issue #245) — any REST API call taking longer fails even while the server actively sends progress. SEP-1539 formally acknowledges "cascade failure risks: poorly chosen client timeouts can cause cascade failures in microservice architectures." No protocol-level mechanism exists for servers to communicate expected durations. The Python SDK's streamable HTTP client hangs indefinitely on invalid JSON-RPC messages with no error propagation or cleanup (Issue #1144). No built-in rate limiting or backpressure semantics exist (Issue #1698).

---

## Conclusion: four structural risks require architectural mitigation, not patches

The evidence points to four risks that cannot be resolved through careful coding alone and require architectural decisions before implementation begins.

**Tool count is the binding constraint.** With Cursor at 40 tools, ChatGPT at ~10 tools worth of token budget, and measurable LLM accuracy degradation above 30 tools, a 68-tool flat registration is incompatible with the current ecosystem. The only viable patterns are dynamic toolset loading (if clients support `list_changed`, which most don't) or a meta-tool dispatch pattern (2-3 gateway tools that route to the full 68 internally). Client-adaptive behavior based on `clientInfo.name` is necessary but fragile.

**Streamable HTTP transport is not production-ready.** Between stateless mode bugs, sticky session requirements, async timeouts, and the recently-patched cross-client data leak, this transport requires careful workarounds and monitoring. Fallback to stdio for local clients is safer where possible.

**Auth token lifecycle must be managed entirely server-side.** No MCP client reliably handles token refresh. Your server must implement proactive token refresh before expiry, handle 401s internally with retry logic, and never surface auth failures as tool errors. This is a universal problem — Atlassian, GitHub Copilot, Google ADK, and Cursor all exhibit the same failure pattern.

**Process management requires platform-specific strategies.** Node.js `detached` is fundamentally broken on Windows for non-Node executables. Mitigation requires Windows Job Objects, macOS `launchd` or `disown` patterns, and Linux `setsid` — there is no cross-platform abstraction that works reliably. Budget for platform-specific spawn logic and orphan process monitoring.
