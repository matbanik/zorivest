# Architectural patterns shaping the MCP ecosystem

**The MCP ecosystem has converged on a small number of powerful architectural primitives — Provider/Transform pipelines, meta-tool patterns, and code-mode execution — that collectively solve the protocol's hardest problems: tool proliferation, state management, and multi-tenancy.** After analyzing 13 major projects spanning five languages, the clearest signal is that the most innovative MCP implementations share a counterintuitive insight: exposing fewer tools, not more, produces better agent behavior. The projects below represent genuinely novel architecture, not API wrappers, and their patterns are transferable to any MCP server regardless of language or domain.

---

## FastMCP: the three-primitive composition engine

**Project:** [jlowin/fastmcp](https://github.com/jlowin/fastmcp) → PrefectHQ | Python | **~22,800★** | v3.1.0 (March 2026) | Production

```
┌──────────────────────────────────────────────┐
│  User Code (@mcp.tool decorators)            │
├──────────────────────────────────────────────┤
│  FastMCP Server (orchestrator)               │
│  ┌──────────┬──────────┬────────────────┐    │
│  │ToolMgr   │ResMgr    │PromptMgr       │    │
│  └──────────┴──────────┴────────────────┘    │
├──────────────────────────────────────────────┤
│  Provider Layer                              │
│  Local│FileSystem│OpenAPI│Proxy│FastMCP      │
├──────────────────────────────────────────────┤
│  Transform Layer                             │
│  Namespace│ToolTransform│Visibility│Version  │
├──────────────────────────────────────────────┤
│  Middleware Layer (Auth│Ping│Custom)          │
├──────────────────────────────────────────────┤
│  Transport (stdio│StreamableHTTP│In-Memory)  │
└──────────────────────────────────────────────┘
```

**Key innovation:** FastMCP v3 collapsed mounting, proxying, filtering, namespacing, and visibility — previously five distinct subsystems — into combinations of just **three primitives: Components, Providers, and Transforms**. A Provider answers "where do tools come from?" A Transform modifies what passes through. Everything else — including server composition — emerges from combining these two.

The decorator pattern extracts JSON Schema from Python type hints via Pydantic's `TypeAdapter`, excluding dependency-injected parameters like `ctx: Context` automatically. In v3, decorators return the original function (not a Tool object), meaning tool functions remain importable and unit-testable as regular Python:

```python
@mcp.tool(tags={"premium"}, version="2.0", auth=require_scopes("admin"))
def analyze(data: str, ctx: Context) -> dict:
    """Analyze data with premium features."""
    return {"result": process(data)}

# Still callable as a normal function
result = analyze("test data", mock_ctx)
```

The **transform pipeline** operates at three levels: provider-level (namespace a mounted sub-server), server-level (global visibility rules), and session-level (per-user feature gating). Session-level transforms enable progressive disclosure — tools tagged `premium` start hidden globally, then individual sessions unlock them via `ctx.enable_components(tags={"premium"})`, triggering automatic `ToolListChangedNotification`.

**CodeMode** (v3.1, experimental) is FastMCP's answer to the "too many tools" problem. It replaces the full tool catalog with BM25 search meta-tools. The LLM searches for relevant tools, inspects their schemas, writes Python code calling multiple tools in sequence, and the code executes server-side. This eliminates both context crowding and round-trip overhead.

**Extracted principles:**
- **Composition over configuration** — features emerge from primitive combinations, not feature flags
- **Functions stay functions** — decorators should not destroy the decorated object's identity
- **Two-level separation** — Transforms shape *what exists*; Middleware handles *how requests execute*
- **In-memory transport for testing** — `Client(server)` exercises the full protocol with zero network overhead

**Anti-patterns avoided:** global mutable state (uses `ContextVar`), tight tool-server coupling (FileSystemProvider discovers standalone `@tool`-decorated files), unbounded state growth (session state has 1-day TTL).

**Risks:** Minor versions may include breaking changes. Auth module (`fastmcp.server.auth`) explicitly exempted from stability guarantees. CodeMode relies on LLM code-writing ability and has unresolved security implications for server-side execution.

---

## GitHub MCP Server: dynamic toolset discovery at scale

**Project:** [github/github-mcp-server](https://github.com/github/github-mcp-server) | Go 1.24 | **~26,900★** | Production

```
┌────────────────────────────────────────────────┐
│  Transport (stdio local │ HTTP remote)         │
├────────────────────────────────────────────────┤
│  Middleware Pipeline                           │
│  ErrorCtx → UserAgent → DependencyInjection   │
├────────────────────────────────────────────────┤
│  Inventory System                              │
│  ┌──────────────────────────────────────────┐  │
│  │ Toolset Groups (repos│issues│PRs│actions)│  │
│  │ Read/Write Classification per tool       │  │
│  │ Dynamic Toolset Discovery (3 meta-tools) │  │
│  └──────────────────────────────────────────┘  │
├────────────────────────────────────────────────┤
│  Tool Handlers (Go functions, 3 API clients)   │
│  REST (go-github) │ GraphQL │ Raw HTTP         │
└────────────────────────────────────────────────┘
```

**Key innovation:** The **dynamic toolset discovery** pattern directly addresses the "too many tools" problem at scale. With 100+ tools, GitHub's server exposes only **3 meta-tools** when `GITHUB_DYNAMIC_TOOLSETS=1`: `list_available_toolsets`, `get_toolset_tools`, and `enable_toolset`. The LLM first discovers what's available, then activates only what it needs. This creates a two-phase interaction that keeps the initial context footprint minimal while preserving access to the full catalog.

GitHub layers **five independent filtering mechanisms** that compose additively:

- **Static toolset configuration** (`GITHUB_TOOLSETS="repos,issues"`) — coarse-grained groups
- **Dynamic toolset discovery** — LLM-driven progressive activation
- **OAuth scope auto-filtering** — tools auto-hide when the token lacks required permissions
- **Read-only mode** (`GITHUB_READ_ONLY=1`) — enforced at registration time, not runtime
- **Lockdown mode** — content filtering for public repos with `RepoAccessCache`

The Inventory is constructed via a builder pattern that creates an **immutable** tool registry. Tools are Go functions returning a `(Tool, Handler)` tuple, keeping definition and implementation co-located. Tool descriptions use translation helpers (`t("TOOL_DESCRIPTION", "fallback")`) enabling internationalization — a pattern no other MCP server implements.

The **"consolidated tool" pattern** in the Projects toolset uses a single tool with a `method` parameter (e.g., `method: "list" | "get" | "update"`) to reduce tool count while maintaining full functionality. This is a pragmatic middle ground between one-tool-per-operation and code-mode approaches.

**Extracted principles:**
- **Defense in depth** — multiple independent security/filtering layers, each removable without breaking others
- **Immutability after construction** — builder pattern prevents runtime mutation of the tool registry
- **Configuration over code** — all behavior controlled via environment variables and headers
- **Deployment-agnostic core** — same `pkg/github/` code serves both hosted HTTP and local stdio

**Risks:** Go language choice limits community contribution from the predominantly TypeScript/Python MCP ecosystem. Dynamic toolsets are local-only (not available on the hosted remote server). Snapshot tests (`__toolsnaps__/`) may be fragile across schema changes.

---

## Cloudflare: Code Mode and edge-native MCP

**Project:** [cloudflare/mcp](https://github.com/cloudflare/mcp) + Agents SDK | TypeScript | Production

```
Agent                           Cloudflare MCP Server
  │                                    │
  ├──search({code: "..."})────────────►│ Execute JS against OpenAPI spec
  │◄──[matching endpoints]─────────────│
  │                                    │
  ├──execute({code: "..."})───────────►│ Execute JS against Cloudflare API
  │◄──[API response]───────────────────│   (sandboxed V8 isolate)
```

**Key innovation: Code Mode reduces 2,594 tools consuming 1.17M tokens to 2 tools consuming 1,069 tokens** — a **99.9% reduction**. Instead of exposing the Cloudflare API as individual MCP tools, the server exposes `search()` and `execute()`. The LLM writes JavaScript that queries the OpenAPI spec and calls the API directly. As Kenton Varda explains: "LLMs have seen vastly more real-world code than synthetic tool-call examples."

The execution sandbox uses **V8 isolates via the Dynamic Worker Loader** — not containers. Key properties: millisecond startup, no filesystem or environment variable access, network blocked by default (only authorized bindings are accessible). This is security by architecture, not by filtering.

Cloudflare provides **three distinct server patterns** at different complexity levels:

1. **`createMcpHandler()`** — stateless, ~15 lines, Streamable HTTP transport
2. **`McpAgent` class** — stateful Durable Object per session with SQL storage and WebSocket hibernation (sleep during inactivity, wake on request)
3. **Raw transport** — direct use of the MCP SDK

The **McpAgent** pattern is architecturally significant: each client session gets its own Durable Object instance with per-session SQLite. This solves state management without external infrastructure. Jurisdiction pinning (`"eu"` or `"fedramp"`) enables data residency compliance.

**Extracted principles:**
- **Token efficiency above all** — fixed context footprint regardless of API surface size
- **Security by architecture** — sandboxed isolates + bindings, not network filtering or token validation
- **Stateful when needed, stateless by default** — two clear, non-overlapping patterns
- **The code-generation paradigm** — let LLMs do what they're best at (writing code) rather than what they're adequate at (tool calling)

**Risks:** Code Mode's Dynamic Worker Loader is still in closed beta for production. V8 isolate sandboxing is Cloudflare-specific infrastructure. Deep vendor lock-in to Workers, Durable Objects, and KV.

---

## Vercel AI SDK: the client-side adapter pattern

**Project:** [vercel/ai](https://github.com/vercel/ai) + `@ai-sdk/mcp` | TypeScript | **~20,600★** | AI SDK 6 | Stable

**Key innovation:** Vercel's approach is purely **client-side MCP consumption** with a dual-mode type safety system. `mcpClient.tools()` dynamically discovers tools from any MCP server and converts them to native AI SDK format. For production, explicit Zod schemas can be overlaid for compile-time type guarantees:

```typescript
// Dynamic discovery (development)
const tools = await mcpClient.tools();

// Static schema overlay (production)
const tools = await mcpClient.tools({
  schemas: {
    'get-weather': {
      inputSchema: z.object({ location: z.string() }),
      outputSchema: z.object({ temperature: z.number() }),
    },
  },
});
```

The companion **`mcp-to-ai-sdk`** CLI acts as "shadcn for MCP" — it generates static AI SDK tool definitions from any MCP server, vendoring tool schemas into your codebase. This addresses the security concern of dynamic tool discovery (schema drift, prompt injection) by locking schemas at build time. Generated tools support dependency injection of custom MCP clients, enabling testing and multi-environment deployment.

**Extracted principles:**
- **Progressive type safety** — start with dynamic discovery, add explicit schemas for production
- **Security by vendoring** — lock tool schemas in your codebase to prevent drift/injection
- **Provider-agnostic** — same MCP tools work with OpenAI, Anthropic, Google, any AI SDK provider
- **Lifecycle awareness** — explicit `close()` patterns for resource cleanup

---

## Supabase and Stripe: two approaches to API-as-tools

### Supabase MCP (~2,500★, TypeScript, monorepo)

**Key innovation: SQL as the universal interface.** Rather than generating per-table tools, Supabase exposes just `execute_sql` (for queries) and `apply_migration` (for DDL, tracked in migration history). This leverages LLM SQL generation capabilities and keeps tool count at **29 total**, managed via **URL-based feature group filtering** (`?features=database,docs`) that reduces from 19.3K tokens to 4.2K tokens.

The **two-step cost confirmation** pattern (`get_cost` → `confirm_cost` before `create_project`) is a transferable safety mechanism for any MCP server handling financial operations. Read-only mode uses a dedicated `supabase_read_only_user` Postgres role — enforcement at the database level, not the application level.

### Stripe MCP (~1,200★, TypeScript + Python)

**Key innovation: remote-first architecture with RAK-based permission filtering.** In v0.9.0+, the local `@stripe/mcp` package is a **thin stdio-to-remote proxy** — tool definitions, permissions, and execution all live on `mcp.stripe.com`. Stripe's existing Restricted API Key infrastructure controls which tools are exposed: if a key lacks `invoices:write`, invoice write tools simply don't appear.

The **meta-tools pattern** (`search_stripe_resources`, `fetch_stripe_resources`, `search_stripe_documentation`) provides escape hatches for operations not covered by the curated **28-tool** subset. The **`resource.action` addressing syntax** (`customers.create`, `invoices.read`) enables intuitive hierarchical tool selection via the `--tools` CLI flag.

**Comparative principle:** Both projects deliberately expose a **curated subset** of their full API surfaces. Supabase achieves breadth through SQL generality; Stripe achieves it through meta-tools. Both are superior to 1:1 API-endpoint-to-tool mapping.

---

## Spring AI MCP: enterprise annotation patterns

**Project:** spring-projects/spring-ai + community modules | Java 17+ | GA (1.1.2)

```java
@Component
public class CalculatorTools {
    @PreAuthorize("isAuthenticated()")
    @McpTool(name = "add", description = "Add two numbers")
    public int add(
        @McpToolParam(description = "First number", required = true) int a,
        @McpToolParam(description = "Second number", required = true) int b) {
        return a + b;
    }
}
```

**Key innovation: dual annotation bridge.** Both `@McpTool` (MCP-specific) and `@Tool` (Spring AI generic) can expose tools via MCP — existing Spring AI function calling tools surface through MCP with zero changes via `MethodToolCallbackProvider`. Boot starters auto-scan all beans, detect annotated methods, and register them. `SyncMcpToolProvider` handles blocking methods; `AsyncMcpToolProvider` handles `Mono`/`Flux` return types.

Spring's `@PreAuthorize` integrates per-tool authorization with Spring Security's full capabilities. The community `mcp-security` module provides OAuth 2.1 resource server support, API-key authentication, and method-level security on MCP tool methods.

**Extracted principles:**
- **Ecosystem leverage** — reuses Spring Security, WebMVC/WebFlux, Micrometer, not custom implementations
- **Sync/Async duality** — every capability has both blocking and reactive variants
- **Configuration-driven** — `spring.ai.mcp.server.*` properties in `application.yml` control all behavior

---

## rmcp (Rust): compile-time protocol correctness

**Project:** [modelcontextprotocol/rust-sdk](https://github.com/modelcontextprotocol/rust-sdk) | Rust | **~3,000★** | v0.15.0 | Official SDK

```rust
#[tool_router]
impl Calculator {
    #[tool(description = "Calculate the sum of two numbers")]
    async fn sum(&self, #[tool(param)] req: SumRequest) -> String {
        format!("Result: {}", req.a + req.b)
    }
}

#[tool_handler]
impl ServerHandler for Calculator { /* ... */ }
```

**Key innovation: compile-time schema generation and role-parameterized type safety.** The `#[tool]` + `#[tool_router]` + `#[tool_handler]` macro triad generates JSON schemas at compile time via `schemars::JsonSchema` derive — impossible to have schema/code drift. `Service<RoleServer>` vs `Service<RoleClient>` enforces at the type level which role can call which methods. The `IntoContents` trait enables any return type to auto-convert to MCP `CallToolResult`.

Performance: **4,700+ QPS native, sub-millisecond latency**, Docker images as small as **11MB**. WASI compilation targets (`wasm32-wasip2`) enable WebAssembly deployment, though Tokio doesn't compile to `wasm32-unknown-unknown`.

**Extracted principles:**
- **Zero-cost abstractions** — macros generate code at compile time, no runtime reflection
- **Type safety over convention** — the compiler enforces protocol correctness, not runtime checks
- **Feature-gated modularity** — Cargo features control which transports and capabilities compile

---

## mcp-agent: recursive orchestration over MCP

**Project:** [lastmile-ai/mcp-agent](https://github.com/lastmile-ai/mcp-agent) | Python | **~8,000★** | Apache-2.0

**Key innovation: "Everything is an AugmentedLLM."** Every workflow pattern — Router, Parallel, Evaluator-Optimizer, Orchestrator, Swarm — is itself an `AugmentedLLM`, enabling recursive composition. An orchestrator agent can delegate to a parallel workflow which contains router agents, each backed by different MCP servers.

```python
agent = Agent(
    name="researcher",
    server_names=["brave-search", "filesystem"],
    instruction="Research and compile reports"
)
async with agent:
    llm = await agent.attach_llm(OpenAIAugmentedLLM)
    result = await llm.generate_str("Summarize the latest AI news")
```

The framework manages MCP server connection lifecycle, aggregates tools from multiple servers into unified namespaces, and integrates **Temporal** for durable execution (pause, resume, recover workflows). The **Deep Orchestrator** pattern adds policy guardrails, knowledge extraction, adaptive replanning, and budget management (tokens, cost, time) for long-horizon research tasks.

**Extracted principles:**
- **Protocol, not framework** — MCP handles execution; orchestration logic lives above
- **Programmatic control flow** — if/while statements, not graph DSLs
- **Recursive composability** — any workflow pattern can contain any other

---

## Tool marketplaces and the federated registry model

Three distinct approaches have emerged for MCP tool discovery:

**Smithery** (2,000+ servers listed, 541★ CLI) operates as a hosted registry with `@smithery/toolbox` — an MCP server that lets agents **dynamically discover and connect to other MCP servers**. The agent searches by description or semantic query, and the toolbox lazy-loads relevant servers. This bridges the "too many tools" problem at the ecosystem level.

**mcp.run** by Dylibso takes a radically different approach: all MCP tools run as **WebAssembly modules**. The `mcpx` dynamic server installs once; tools are added via registry without reconfiguring clients. Wasm sandboxing prevents data exfiltration — a fundamental security advantage over `npx`/`uvx` execution.

The **Official MCP Registry** (backed by Anthropic, GitHub, Microsoft) uses a **federated model**: a community-driven metadata repository with namespace authentication (reverse DNS: `io.github.username/server`). Downstream marketplaces consume it via REST API and add curation, ratings, and security scanning. It's not intended for direct consumption by host apps — it's infrastructure for infrastructure.

---

## How the ecosystem solves the "too many tools" problem

This is the most discussed architectural challenge. Each tool definition consumes **~250-350 tokens**; performance degrades past ~40 tools and "falls off a cliff" past 60. Six distinct approaches have emerged:

- **Dynamic toolset discovery** (GitHub) — 3 meta-tools for progressive activation
- **Code Mode** (Cloudflare, FastMCP) — LLM writes code against a type-safe API instead of making tool calls; **99.9% token reduction** for large APIs
- **RAG over tools** (Writer MCP Gateway) — embed tool descriptions in vector space, inject only top-k by semantic distance; **3x improvement in selection accuracy, 50%+ token reduction**
- **Feature group filtering** (Supabase, Stripe) — URL params or CLI flags scope to relevant tool subsets
- **Meta-tools** (Stripe, Stainless, Speakeasy) — 3 generic tools (`list`, `describe`, `execute`) replace hundreds of specific ones
- **Fine-tuning** — train the model to internalize tool schemas, eliminating prompt-time injection entirely

The **RAG-MCP** pattern and **Code Mode** represent genuinely novel approaches. RAG-MCP treats tool selection as a retrieval problem rather than an enumeration problem. Code Mode reframes tool calling entirely — instead of structured JSON tool calls, the LLM writes code that chains multiple API calls with data flowing through variables rather than back through the neural network.

---

## State management across multi-step sessions

The ecosystem has converged on a **three-model architecture**:

1. **Server-side state cache** (Redis/DynamoDB) — full session state retrieved by session ID. Best for compliance-heavy workflows. FastMCP supports this via pluggable `session_state_store`.
2. **Client-side ephemeral pointers** — minimal identifiers in conversation context, bulk data server-side. Best for stateless, scalable architectures.
3. **Durable Object per session** (Cloudflare) — each session gets its own SQLite database with WebSocket hibernation. Zero external infrastructure, but Cloudflare-specific.

FastMCP's session state (`ctx.get_state()`/`ctx.set_state()`) is async in v3, keyed by session ID automatically with **1-day TTL** to prevent unbounded growth. Spring AI injects `McpSyncRequestContext` for server-side logging, progress, and sampling. The Rust SDK uses `RequestContext<RoleServer>` with role-parameterized context.

The critical unsolved problem: **horizontal scaling with session state**. Streamable HTTP replaced SSE, but sticky sessions are an optimization, not a correctness mechanism. No standard MCP-level mechanism exists for session migration or state serialization across server instances.

---

## Authentication patterns converging on OAuth 2.1

The MCP authorization spec (revised June 2025) mandates OAuth 2.1 with **Protected Resource Metadata** (RFC 9728), **Dynamic Client Registration**, and **PKCE (S256)**. Three patterns dominate:

FastMCP's **OAuthProxy** (~1,100 lines) solves a problem unique to MCP: clients use random localhost ports, but upstream OAuth providers require pre-registered redirect URIs. The proxy translates DCR to work with Google, GitHub, Azure, and Auth0. Stripe reuses its existing **Restricted API Key** infrastructure — permissions on the key directly control which tools appear. Cloudflare provides four distinct auth patterns from simplest (Cloudflare Access) to most complex (custom OAuth provider).

The emerging frontier is **identity chaining across trust domains** (User → AI host → MCP client → MCP server → upstream API) using JWT Identity Assertion Grants. And **sequence-aware authorization** — validating not just individual token scopes but the cumulative effect of chained tool calls — is identified as a critical open problem by GitGuardian.

---

## AI-first API design: descriptions are the interface

The fundamental insight: **APIs are designed for developers who read docs once and learn; MCP tools are consumed by LLMs that must understand everything from the description alone, on every call.** This demands:

- **Context-aware dynamic descriptions** (Ragie) — tool descriptions generated based on the tenant's actual data, auto-updating when data changes
- **LLM-powered description rewriting** (Writer) — AI rewrites API docs into LLM-optimized tool descriptions
- **OpenAPI extensions** (Speakeasy `x-speakeasy-mcp`) — per-parameter LLM guidance like "You can find the IDs by first using the listDrivers tool"
- **Surface area hashing** (community proposal) — hash the tool's name + description + schema in CI to detect when any change alters the agent's contract

A critical emerging realization: **in MCP, a description change is effectively a breaking change** because it alters the LLM's selection logic — even without schema modifications. SEP-1575 proposes explicit tool-level semantic versioning to address this.

---

## Top 5 architectural principles across all projects

**1. Fewer tools, smarter interfaces.** Every high-quality MCP implementation deliberately constrains its tool surface. Cloudflare covers 2,594 API endpoints with 2 tools. Supabase covers all database operations with 2 tools. Stripe uses 3 meta-tools as escape hatches. GitHub uses dynamic discovery to start with 3. The pattern is universal: **expose workflow-level capabilities, not resource-level operations**.

**2. Composition from minimal primitives.** FastMCP's Provider + Transform, mcp-agent's "everything is an AugmentedLLM," and Rust's trait-based `ServerHandler + ToolRouter` all demonstrate that a small number of composable primitives produces more flexible architecture than feature-specific subsystems. The fewer the primitives, the more combinations are possible.

**3. Type systems generate schemas, not vice versa.** Python type hints → Pydantic → JSON Schema. Rust structs → schemars → JSON Schema. Java annotations → reflection → JSON Schema. Zod schemas → TypeScript types + JSON Schema. In every mature implementation, **the programming language's type system is the single source of truth**, and schemas are derived artifacts.

**4. Security by architecture, not by policy.** Cloudflare's V8 isolate sandboxing (no network, no filesystem, only bindings), Supabase's database-level read-only role, Stripe's RAK-based server-side filtering, and mcp.run's Wasm sandboxing all enforce security through structural constraints rather than runtime policy checks.

**5. Progressive disclosure over upfront enumeration.** Dynamic toolset discovery, feature group filtering, session-level visibility transforms, RAG-based tool retrieval, and code-mode meta-tools all implement the same principle: **start minimal, expand on demand**. This respects both context window constraints and the cognitive limitations of current LLMs.

### Complementary principles that should be combined

- **Provider/Transform pipelines** (FastMCP) + **dynamic toolset discovery** (GitHub) = a server that both composes from multiple sources and progressively exposes capabilities
- **Code Mode** (Cloudflare) + **RAG over tools** (Writer) = semantic retrieval to find relevant tools, then code-mode execution to chain them efficiently
- **Annotation-driven registration** (Spring/Rust) + **FileSystem discovery** (FastMCP) = declarative tool definition with hot-reload capability
- **Static schema vendoring** (Vercel `mcp-to-ai-sdk`) + **compile-time schema generation** (Rust schemars) = end-to-end type safety from server definition through client consumption

### Principles that conflict (requiring a choice)

- **Code Mode** (LLM writes code) vs **Structured tool calls** (LLM fills schemas): Code Mode handles more tools and chains better, but introduces code execution security risks and requires LLMs proficient in the target language. Structured calls are safer and more predictable but scale poorly past 40 tools.
- **Convention-based discovery** (mcp-framework's directory scanning) vs **Explicit registration** (FastMCP's decorator pattern): Convention reduces boilerplate but hides tool registration logic; explicit registration is verbose but transparent and debuggable.
- **Remote-first** (Stripe's server-side truth) vs **Local-first** (stdio with embedded logic): Remote-first centralizes control and simplifies updates but adds network dependency and latency; local-first enables offline use and lower latency but distributes complexity to every client.
- **Enterprise DI frameworks** (Spring's IoC + auto-config) vs **Minimal composition** (Rust's struct fields, FastMCP's standalone decorators): Enterprise patterns provide observability, security, and service discovery out of the box but add JVM overhead and coupling; minimal approaches are faster and more portable but require building infrastructure.

---

## The recommended "inspiration stack"

For a maximally modular, future-proof, agentic-friendly MCP server, combine these patterns:

| Layer | Pattern | Source |
|-------|---------|--------|
| **Tool definition** | Decorator/annotation with type-derived schemas | FastMCP (`@mcp.tool`) or rmcp (`#[tool]`) |
| **Tool organization** | Provider + Transform pipeline with namespace composition | FastMCP v3 |
| **Tool scaling** | Dynamic toolset discovery (meta-tools) + RAG retrieval fallback | GitHub MCP Server + Writer MCP Gateway |
| **Complex APIs** | Code Mode for large API surfaces (>50 endpoints) | Cloudflare |
| **State** | Session-scoped state with external store + TTL | FastMCP (Redis-backed `session_state_store`) |
| **Auth** | OAuth 2.1 resource server with per-tool authorization | Spring AI MCP Security + FastMCP OAuthProxy |
| **Testing** | In-memory transport + snapshot testing for schemas | FastMCP + GitHub (`__toolsnaps__/`) |
| **Safety** | Database-level read-only roles + two-step confirmation for destructive ops | Supabase + Stripe RAK |
| **Client consumption** | Dynamic discovery for dev, static vendoring for production | Vercel AI SDK (`mcp-to-ai-sdk`) |
| **Orchestration** | Recursive AugmentedLLM composition with durable execution | mcp-agent + Temporal |
| **Deployment** | Stateless by default, stateful Durable Objects when needed | Cloudflare Agents SDK |
| **Discovery** | Federated registry with namespace authentication | Official MCP Registry + Smithery |

This stack separates concerns cleanly: tool definition is language-idiomatic (decorators or macros), tool organization uses composable primitives, scaling uses progressive disclosure, and the client-side consumption pattern ensures type safety without sacrificing flexibility. The critical insight is that no single project has solved everything — but the patterns are complementary, and the best architecture cherry-picks from each.