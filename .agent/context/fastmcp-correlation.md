# What to Steal from FastMCP — Inspiration Guide

> **Decision:** FastMCP will NOT be adopted as a dependency. This document captures design patterns and architectural ideas worth adapting into our custom TypeScript MCP server.
>
> Sources: [FastMCP v3 docs](https://gofastmcp.com), [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp)

---

## Architecture Context

Our MCP server is TypeScript, proxying to a Python REST API. FastMCP is Python-native. We're stealing *concepts*, not code.

```
Our Design:    IDE → MCP Server (TS, :8766) → REST API (Python, :8765) → SQLCipher
FastMCP:       IDE → FastMCP (Python) → Python logic (direct calls)
```

---

## 1  Tool Search Architecture

### How FastMCP Does It

FastMCP's `ToolSearchTransform` replaces `list_tools()` with two meta-tools:

- **`search_tools`** — finds tools matching a natural language query, returns their full definitions (name, schema, description)
- **`call_tool`** — executes a discovered tool by name (proxy pattern)

Two search strategies available:
- **Regex** — fast pattern matching on tool names/descriptions
- **BM25** — information retrieval ranking (term frequency × inverse document frequency), better for natural language queries

Configuration options: result limits, pinned tools (always visible), custom tool names.

### What to Steal

Adopt the **BM25 search strategy** for our Anthropic client mode (§5.12). Currently we planned a custom search implementation — FastMCP's approach is well-tested and the algorithm is well-documented.

### Development Implications from Build Plan

| Build Plan Reference | Implication |
|---|---|
| **§5.11** Toolset Configuration | Our `list_available_toolsets` / `describe_toolset` meta-tools already serve a similar purpose but are *category-oriented*, not *text-search-oriented*. We need both: category browsing for structured discovery + BM25 search for natural language queries. |
| **§5.12** Adaptive Client Detection | BM25 search applies only to `anthropic` mode clients. `dynamic` and `static` clients use `enable_toolset` or `--toolsets` respectively. The search must index *all* tools (including deferred/unloaded) to be useful. |
| **05j** Discovery meta-tools | `search_tools` would be a 5th discovery tool alongside our existing 4. Need to decide if it replaces `describe_toolset` or complements it. |
| **05c** Trade Analytics (19 tools) | The largest category — perfect test case for search relevance. "How much did I lose on PFOF?" should find `estimate_pfof_impact` and `get_cost_of_free`. |
| **Middleware composition** (§5.14) | The `call_tool` proxy pattern means search results bypass normal registration flow. Must ensure `withGuard()` and `withMetrics()` still wrap proxied calls. |

### Implementation Sketch

```typescript
// New: mcp-server/src/tools/search-tools.ts
// BM25 index built at startup from ALL registered + deferred tool definitions

interface SearchIndex {
  toolName: string;
  description: string;       // full description (rich tier)
  annotations: ToolAnnotations;
  toolset: string;           // category for context
  bm25Score?: number;        // computed at query time
}

// Tokenize descriptions + names → BM25 term frequency index
// Query: tokenize input → score each tool → return top-K
// Pin: core + discovery tools always appear in results
```

### Key Risk

BM25 relevance depends on tool description quality. Our [tiered description model](05-mcp-server.md#pattern-b-tiered-tool-descriptions) uses "rich" descriptions (200-400 chars) for Anthropic clients — these are the descriptions that should be indexed. Minimal descriptions (50-100 chars) for other clients would produce poor search results.

---

## 2  Tag-based Organization

### How FastMCP Does It

Tools are tagged at declaration time:

```python
@mcp.tool(tags={"trade-analytics", "read-only"})
def get_round_trips(...): ...
```

Tag filtering at runtime:
- `mcp.enable(tags={"trade-analytics"}, only=True)` — allowlist mode
- `mcp.disable(tags={"deprecated"})` — blocklist mode
- Combine: `mcp.enable(tags={"admin"}, only=True).disable(tags={"deprecated"})`

Tags are also used in server composition for mounted sub-servers.

### What to Steal

Add **multi-dimensional tagging** to our tool metadata beyond the current single-category `toolset` field. Tags would enable:
- Cross-cutting concerns: `read-only`, `destructive`, `network-bound`, `compute-heavy`
- Functional grouping: `trade-analytics` + `behavioral` (tools like `ai_review_trade` belong to both)
- Safety classification: `requires-confirmation`, `always-callable`, `guarded`

### Development Implications from Build Plan

| Build Plan Reference | Implication |
|---|---|
| **§5.11** Toolset definitions | Current model: each tool belongs to exactly one `toolset`. Tags would supplement (not replace) toolsets. Toolsets remain the unit of loading; tags are metadata for filtering/search. |
| **05c** Cross-category tools | `create_trade` is in both `trade-analytics` and `trade-planning`. `ai_review_trade` spans `trade-analytics` and `behavioral`. Tags make this explicit without duplicating tool registrations. |
| **§5.13** Pattern B: Tiered descriptions | Tags like `network-bound` replace the hardcoded `NETWORK_TOOLS` set in MetricsCollector (§5.9). Tags make the exclusion list data-driven instead of code-driven. |
| **mcp-tool-index.md** | The tool index already has a `Categories` column supporting multi-category. Tags formalize this in code. |
| **05a** Annotation blocks | Every tool already has annotation metadata (`readOnlyHint`, `destructiveHint`, etc.). Tags are complementary — annotations are MCP-protocol-level, tags are application-level. |

### Implementation Sketch

```typescript
// Extend tool registration to include tags
interface ToolDefinition {
  name: string;
  description: string;
  schema: z.ZodSchema;
  handler: ToolHandler;
  annotations: ToolAnnotations;
  toolset: string;           // primary category (for loading)
  tags: Set<string>;         // multi-dimensional metadata
}

// Tag-based filtering for MetricsCollector
const NETWORK_BOUND_TAG = 'network-bound';  // replaces hardcoded NETWORK_TOOLS set
```

### Key Risk

Tag proliferation — without discipline, tags become meaningless. Establish a controlled vocabulary:

| Tag Dimension | Allowed Values |
|---|---|
| I/O pattern | `read-only`, `write`, `destructive` |
| Performance | `network-bound`, `compute-heavy`, `fast` |
| Safety | `always-callable`, `requires-confirmation`, `guarded` |
| Content type | `returns-image`, `returns-json`, `returns-text` |

---

## 3  Transform Pipeline Concept

### How FastMCP Does It

Transforms are middleware layers that modify components as they flow through the server:

```
Provider → [Transform A] → [Transform B] → Client
```

Built-in transforms:
- **Namespace** — prefix tool names to prevent conflicts during composition
- **Tool Transformation** — rename tools, modify descriptions, reshape arguments
- **Tool Search** — replace large catalogs with on-demand search (see §1 above)
- **Enabled/Visibility** — runtime show/hide by key or tag
- **Resources as Tools** — expose resources to tool-only clients
- **Code Mode** (experimental) — replace many tools with `search` + `execute`

Each transform can intercept and modify tool calls via `call_next()` (middleware chaining).

### What to Steal

The **formalized middleware pipeline concept** validates and extends our existing `withGuard(withMetrics(handler))` composition pattern. Key insights:

1. **Named pipeline stages** — our ad-hoc wrapping becomes a declared pipeline
2. **Provider-level vs Server-level transforms** — separates "modify what tools exist" from "modify how tools behave"
3. **`call_next()` chaining** — cleaner than nested function wrapping for complex middleware stacks

### Development Implications from Build Plan

| Build Plan Reference | Implication |
|---|---|
| **§5.14** Middleware Composition Order | Current: `withMetrics() → withGuard() → withConfirmation() → handler`. This IS a transform pipeline — we should formalize it with named stages and a registry instead of manual wrapping. |
| **§5.6** Guard Middleware | `withGuard()` is a transform that intercepts calls and returns error content. Formalizing this as a pipeline stage makes it easier to test independently and to conditionally include/exclude. |
| **§5.9** Metrics Middleware | `withMetrics()` records timing + payload. As a pipeline stage, it would be the outermost layer (first to receive, last to return) — easier to reason about if explicitly ordered. |
| **§5.13** Pattern E: Safety Confirmation | `withConfirmation()` applies only to destructive tools on annotation-unaware clients. A pipeline registry makes this conditional inclusion declarative rather than imperative. |
| **05j** Confirmation tokens | Token validation happens in `withConfirmation()`. In a pipeline model, this is a named stage that can be tested, disabled, or replaced independently. |

### Implementation Sketch

```typescript
// Pipeline registry replaces ad-hoc function wrapping
interface PipelineStage {
  name: string;
  order: number;            // lower = outer (closer to caller)
  applies: (tool: ToolDefinition) => boolean;  // conditional inclusion
  wrap: (handler: ToolHandler, tool: ToolDefinition) => ToolHandler;
}

const pipeline: PipelineStage[] = [
  {
    name: 'metrics',
    order: 0,
    applies: () => true,    // always applied
    wrap: (handler, tool) => withMetrics(tool.name, handler),
  },
  {
    name: 'guard',
    order: 1,
    applies: (tool) => !tool.tags.has('always-callable'),
    wrap: (handler) => withGuard(handler),
  },
  {
    name: 'confirmation',
    order: 2,
    applies: (tool) => tool.annotations.destructiveHint && !clientSupportsAnnotations(),
    wrap: (handler, tool) => withConfirmation(tool.name, handler),
  },
];

// Registration: apply pipeline stages in order
function applyPipeline(handler: ToolHandler, tool: ToolDefinition): ToolHandler {
  return pipeline
    .filter(stage => stage.applies(tool))
    .sort((a, b) => b.order - a.order)  // inner-first wrapping
    .reduce((h, stage) => stage.wrap(h, tool), handler);
}
```

### Key Risk

Over-engineering for 68 tools. The pipeline is most valuable when:
- Middleware stages are conditional (guard doesn't apply to emergency tools, confirmation only on annotation-unaware clients)
- New stages may be added later (logging, rate-limiting, audit trail)
- Testing requires isolating individual stages

If the middleware stack stays at 3 stages, the current `withX(withY(handler))` pattern is adequate. Formalize only if we expect growth.

---

## 4  Other Patterns Worth Noting

### 4.1 Custom HTTP Routes

FastMCP allows `@mcp.custom_route("/health")` alongside MCP tools. We should consider adding a health check endpoint to our MCP server (currently only the Python API has `/health`).

**Build plan impact:** Minimal — add a `/health` route to the MCP HTTP server for monitoring.

### 4.2 Server Composition (Mount)

FastMCP's `mcp.mount()` composes multiple servers with namespacing. While we won't adopt composition (single-server model), the **namespace prefix concept** could apply if we ever need to expose third-party MCP servers alongside Zorivest tools.

**Build plan impact:** Future consideration only. No current plan change.

### 4.3 Structured Output Schemas

FastMCP v3 supports output schemas for tool results. Our tools currently return untyped `content: [{ type: 'text', text: JSON.stringify(data) }]`. Output schemas would enable client-side validation.

**Build plan impact:** The MCP SDK v1.25+ supports `outputSchema` (noted in §5 SDK Compatibility). Consider adopting for tools with well-defined response shapes.

---

## Appendix: Steal List Summary

| # | Feature | Source | Priority | Effort | Build Plan Impact |
|---|---|---|---|---|---|
| 1 | BM25 Tool Search | FastMCP ToolSearchTransform | 🔥 High | Medium | New discovery tool; index all 68 tool descriptions |
| 2 | Multi-dimensional tags | FastMCP tag-based filtering | Medium | Low | Metadata addition; replaces hardcoded sets |
| 3 | Pipeline stage registry | FastMCP transform pipeline | Medium | Medium | Formalizes existing middleware; enables conditional stages |
| 4 | Health check route | FastMCP custom_route | Low | Trivial | Monitor MCP server independently from Python API |
| 5 | Output schemas | MCP SDK v1.25+ | Low | Medium | Typed tool responses; defer to post-MVP |
