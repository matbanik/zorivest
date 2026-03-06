# Pre-mortem Risk Mining — Research Prompts

> **Goal:** Proactively discover friction points, edge cases, and hard-to-debug problems from analogous MCP server projects before we encounter them in Zorivest development.

---

## Methodology: Pre-mortem Risk Mining

The practice of proactively researching problems before they occur in your project combines three established techniques:

### 1. Pre-mortem Analysis (Gary Klein, 1998)
Imagine the project has already failed → work backward to identify all possible causes. Uses "prospective hindsight" to overcome planning optimism bias.

### 2. Issue Archaeology
Systematically mine GitHub issues, pull requests, and changelogs from analogous open-source projects to extract lessons learned, edge cases, and design problems that took significant effort to resolve.

### 3. Anticipatory Failure Determination (AFD)
From TRIZ methodology — instead of asking "what could go wrong?", ask "how can I *make* it fail?" This inversion produces more exhaustive failure inventories.

### Implementation Protocol

1. **Define friction areas** — map our architecture to specific risk categories
2. **Identify analogous projects** — find projects that have traveled similar paths
3. **Mine issues** — search for long-lived bugs, reverted designs, "won't fix" decisions
4. **Extract patterns** — categorize findings into friction types
5. **Map to build plan** — link each finding to our specific build plan sections
6. **Create mitigation inventory** — preemptive fixes or design adjustments

---

## Our 10 Friction Areas (from Build Plan)

| # | Friction Area | Build Plan Section | What Can Go Wrong |
|---|---|---|---|
| 1 | Tool registration at scale | §5.10, 05a–05j | 68 tools: naming conflicts, registration ordering, schema validation at volume |
| 2 | Middleware composition | §5.14 | Order-dependent wrapping (metrics→guard→confirmation), error propagation through layers |
| 3 | Dynamic toolset loading | §5.11–5.12 | `notifications/tools/list_changed` client handling, stale tool lists, race conditions |
| 4 | Auth bootstrap lifecycle | §5.7 | Session token expiry mid-session, re-auth during tool execution, ECONNREFUSED on startup |
| 5 | Adaptive client detection | §5.12–5.13 | IDE `clientInfo.name` reporting inconsistencies, unknown clients, mode fallback bugs |
| 6 | Transport compatibility | §5.7, dep manifest | Streamable HTTP vs STDIO quirks, connection drops, reconnection logic |
| 7 | Zod schema edge cases | All 05* files | Optional fields, default values, enum coercion, nested objects, array validation |
| 8 | Binary content handling | 05c (screenshots) | Base64 image encoding/decoding, size limits, mime type detection, MCP content blocks |
| 9 | Cross-platform process mgmt | §5.8 | GUI launch detachment, process tree inheritance, Windows/macOS/Linux differences |
| 10 | IDE tool count limits | §5.11 | Cursor 40-tool cap, Claude Code Tool Search integration, Windsurf quirks |

---

## Research Prompt 1: Python MCP Ecosystem (Gemini)

> **Assignment:** Mine Python MCP server projects for friction patterns.
> **Model:** Gemini 2.5 Pro (Deep Research mode)

```markdown
# Deep Research: Python MCP Server Friction Analysis

## Context
I'm building a financial trading MCP server (68 tools, 10 categories) using TypeScript
with the @modelcontextprotocol/sdk v1.x. I want to learn from the Python MCP ecosystem's
mistakes and hard-won lessons before I start implementation.

## Research Targets

### Primary Projects
1. **PrefectHQ/fastmcp** (GitHub) — The dominant Python MCP framework
   - Examine: issues, pull requests, discussions, changelogs from v1→v2→v3 migrations
   - Focus on: tool registration bugs, transport problems, auth edge cases, transform pipeline issues

2. **modelcontextprotocol/python-sdk** (GitHub) — The official Python MCP SDK
   - Examine: issues labeled "bug", issues open >30 days, breaking change PRs
   - Focus on: protocol-level problems, schema validation, content type handling

3. **Any Python MCP server with >20 tools** — Community implementations
   - Search for: large tool count projects, servers with middleware/guard patterns

### What to Extract

For each project, create a friction inventory organized by these categories:

**Category A: Tool Registration & Schema**
- Schema validation failures (type coercion, optional fields, defaults)
- Tool naming conflicts or collisions
- Dynamic tool addition/removal bugs
- Large tool count performance issues (>40 tools)

**Category B: Transport & Connection**
- STDIO vs HTTP vs SSE switching problems
- Connection drop/reconnection edge cases
- Timeout handling during long-running tools
- Concurrent tool call issues

**Category C: Auth & Security**
- Token lifecycle bugs (expiry, refresh, invalidation)
- Session state management across connections
- API key handling and secret exposure

**Category D: Content & Response**
- Binary content (images, files) encoding/decoding issues
- Large response truncation or memory problems
- Error response formatting inconsistencies

**Category E: Client Compatibility**
- IDE-specific bugs (Cursor, Claude Code, VS Code, etc.)
- Tool count limits per client
- Client-side tool caching stale data
- Annotation/hint handling differences across clients

### Output Format

For each finding, provide:
1. **Project + Issue/PR link**
2. **Friction category** (A–E)
3. **One-line summary**
4. **Resolution timeline** (how long it took to fix, or if still open)
5. **Root cause** (design flaw, edge case, client bug, protocol ambiguity)
6. **Our risk level** (High/Medium/Low based on architectural similarity)

### Search Strategy
- GitHub issue search: `is:issue label:bug` in each repo
- GitHub issue search: `is:issue is:closed sort:comments-desc` (most-discussed = most painful)
- Changelog entries with "breaking", "fix", "regression"
- Reddit r/mcp, r/LocalLLaMA discussions mentioning "bug", "issue", "problem"
- Stack Overflow tagged [model-context-protocol]
```

---

## Research Prompt 2: TypeScript MCP SDK & Ecosystem (ChatGPT)

> **Assignment:** Mine TypeScript MCP projects for friction patterns, focusing on the same SDK we use.
> **Model:** ChatGPT o3 (web search enabled)

```markdown
# Deep Research: TypeScript MCP Server Friction Analysis

## Context
I'm building a production MCP server using @modelcontextprotocol/sdk v1.x in TypeScript.
The server has 68 tools, uses Zod for schema validation, and proxies to a Python REST API.
I need to find friction patterns from projects using the same stack.

## Research Targets

### Primary Projects
1. **modelcontextprotocol/typescript-sdk** (GitHub) — The SDK we depend on
   - Search ALL issues and PRs, especially:
     - Breaking changes between versions
     - `server.tool()` API quirks
     - Transport layer bugs (STDIO, Streamable HTTP)
     - Schema validation edge cases with Zod
   - CRITICAL: Review issues related to v1→v2 migration path (anything we should prepare for)

2. **Large TypeScript MCP servers** (find at least 2 with >15 tools):
   - Search GitHub for: `@modelcontextprotocol/sdk` in package.json, TypeScript, >15 tools
   - Candidates to search for:
     - Community MCP servers for databases, file systems, cloud platforms
     - Any TS MCP server with middleware patterns
   - Look for: tool registration patterns, error handling approaches, testing strategies

### What to Extract

**Category A: Zod Schema Edge Cases**
- Find issues where Zod schemas caused unexpected validation failures
- Optional field handling (undefined vs null vs missing)
- Default values not applied correctly
- Enum validation with string coercion
- Nested object schemas and `.describe()` interactions
- Array min/max validation edge cases

**Category B: Transport & Protocol**
- Streamable HTTP connection lifecycle issues
- STDIO buffer overflow or encoding problems
- SSE (deprecated) to Streamable HTTP migration pain
- JSON-RPC 2.0 parsing edge cases
- Connection drop recovery behavior

**Category C: Tool Registration at Scale**
- Performance with >40 registered tools
- Tool list pagination behavior
- `notifications/tools/list_changed` client support matrix
- Dynamic tool registration/unregistration race conditions
- Duplicate tool name handling

**Category D: SDK Version Compatibility**
- Breaking changes in patch versions
- TypeScript compilation issues after SDK updates
- Import path changes between versions
- Zod version compatibility with SDK

**Category E: Testing Patterns**
- How other projects test MCP tools (mocking strategies)
- Integration testing with MCP Inspector
- CI/CD patterns for MCP servers

### Output Format
For each finding:
1. **Source** (repo + issue/PR number + link)
2. **Category** (A–E)
3. **Summary** (what happened)
4. **Was it a design flaw or an edge case?**
5. **Time to resolution** (days open, or "still open")
6. **Mitigation** (how was it fixed, or how should we prevent it)

### Additional Search Vectors
- npm: search for packages depending on @modelcontextprotocol/sdk
- GitHub code search: `McpServer` language:TypeScript
- GitHub code search: `server.tool` language:TypeScript
- GitHub Discussions in modelcontextprotocol org
```

---

## Research Prompt 3: Large-Scale MCP Implementation Patterns (Claude)

> **Assignment:** Deep analysis of large MCP implementations and middleware patterns.
> **Model:** Claude Opus 4.6 (Deep Research mode with web search)

```markdown
# Deep Research: Large-Scale MCP Server Architecture Friction

## Context
I'm building Zorivest, a financial trading MCP server with:
- 68 tools across 10 categories (trade-analytics, market-data, tax, scheduling, etc.)
- Custom middleware stack: withMetrics() → withGuard() → withConfirmation() → handler
- Adaptive client detection (Anthropic/dynamic/static modes)
- Dynamic toolset loading with notifications/tools/list_changed
- TypeScript server proxying to Python REST API
- Zod schemas for all tool inputs
- MCP annotations on every tool (readOnlyHint, destructiveHint, idempotentHint)

## Research Targets

### 1. Find 2 TypeScript MCP servers with the most tools
Search GitHub for the TypeScript MCP server projects with the highest tool count.
Look at their issues for:
- How they organized/categorized tools
- Registration performance at scale
- Client compatibility issues (especially Cursor's 40-tool limit)
- Any middleware or wrapping patterns they use

### 2. Find the most mature Python MCP server (NOT FastMCP itself)
Search for Python MCP servers that:
- Use the official `mcp` Python SDK (not FastMCP wrapper)
- Have >20 tools
- Have been in development for >6 months
Search their issues for design problems and edge cases.

### 3. Find any project with a hybrid architecture
Search for MCP server projects where:
- The MCP server is in one language (TypeScript/JavaScript)
- It proxies to a backend API in another language (Python/Go/Rust)
- This is exactly our architecture — any project doing this is gold

### What to Analyze

**Middleware & Guard Patterns:**
- How do large MCP servers handle authorization/permission for individual tools?
- Do any implement circuit breaker or rate limiting patterns?
- How is middleware composition handled (function wrapping vs pipeline)?
- What happens when middleware throws vs returns error content?

**Dynamic Tool Management:**
- Which IDEs actually support `notifications/tools/list_changed`?
- How quickly do clients refresh their tool list after notification?
- Any stale-tool-list bugs where a client calls a tool that no longer exists?
- How do deferred-loading tools interact with tool search?

**Annotation Handling:**
- Which IDE clients actually use `readOnlyHint`, `destructiveHint`?
- Do annotations affect tool sorting/presentation in any IDE?
- Has anyone implemented server-side confirmation tokens for annotation-unaware clients?

**Financial/Trading Domain (if any exist):**
- Find any MCP servers in the finance/trading domain
- How do they handle destructive operations (placing trades)
- Any safety patterns beyond standard MCP annotations

### Output Format
Structured friction inventory with:
1. Project name + GitHub URL
2. Stars/activity level (to gauge maturity)
3. Architecture summary (language, tool count, transport)
4. Top 5 hardest issues they faced (with links)
5. Design decisions they made that we should learn from
6. Design decisions they made that we should avoid
7. Specific relevance to our 10 friction areas (see list below)

### Our 10 Friction Areas for Mapping
1. Tool registration at scale (68 tools)
2. Middleware composition (withGuard→withMetrics→withConfirmation)
3. Dynamic toolset loading (list_changed notifications)
4. Auth bootstrap lifecycle (session tokens)
5. Adaptive client detection (clientInfo parsing)
6. Transport compatibility (Streamable HTTP)
7. Zod schema edge cases
8. Binary content handling (base64 images)
9. Cross-platform process management
10. IDE tool count limits (Cursor 40-tool cap)
```

---

## Research Prompt 4: Hybrid Architecture & REST Proxy Friction (Gemini)

> **Assignment:** Find projects with Python+TypeScript or similar multi-language MCP architectures.
> **Model:** Gemini 2.5 Pro (Deep Research mode)

```markdown
# Deep Research: Multi-Language MCP Architecture Friction

## Context
Zorivest uses a two-process MCP architecture:
- MCP Server: TypeScript, port 8766, uses @modelcontextprotocol/sdk
- Backend API: Python FastAPI, port 8765, owns database (SQLCipher)
- All MCP tools proxy via HTTP fetch() to REST endpoints
- Auth: MCP server bootstraps with API key → gets session token → includes in all REST calls

This hybrid pattern is unusual. I need to find similar architectures and mine them for problems.

## Research Targets

### 1. Any MCP server that proxies to a separate backend
Search for GitHub repos where:
- An MCP server (any language) wraps/proxies a REST API
- The MCP server is a thin layer converting MCP tool calls to HTTP requests
- Keywords: "mcp proxy", "mcp rest", "mcp gateway", "mcp bridge", "mcp wrapper"

### 2. FastAPI + TypeScript integrations (non-MCP)
Even outside MCP, find projects that combine:
- Python FastAPI backend
- TypeScript/Node.js frontend or middleware
- REST proxy patterns between them
Look for: type drift, auth token lifecycle issues, connection pooling, error translation

### 3. Multi-process MCP setups
Find any MCP implementation using multiple processes:
- Database server + MCP server as separate processes
- MCP server managing child processes or connecting to services
- Docker compose or similar multi-container MCP deployments

### What to Extract

**REST Proxy Friction:**
- HTTP fetch() reliability in long-running Node.js processes
- Connection pooling and keep-alive for frequent REST calls
- Request timeout vs MCP tool timeout coordination
- Error translation: HTTP status codes → MCP error content
- Retry logic for transient backend failures (ECONNREFUSED during restart)

**Type System Drift:**
- Zod (TypeScript) vs Pydantic (Python) schema divergence
- Enum value mismatches between languages
- Optional field handling differences (null vs undefined vs missing)
- Date/time serialization inconsistencies

**Auth Token Lifecycle:**
- Session token expiry during long tool execution
- Re-authentication while tools are in-flight
- Token storage in Node.js process memory vs environment
- Race conditions when multiple tools authenticate simultaneously

**Process Coordination:**
- MCP server startup before backend is ready (race condition)
- Backend restart while MCP server is active
- Graceful shutdown coordination between processes
- Health check polling from MCP → backend

**Performance:**
- Latency overhead of HTTP proxy per tool call
- JSON serialization/deserialization cost at volume
- Concurrent tool call fan-out to single backend
- Memory growth in long-running proxy processes

### Output Format
For each finding:
1. **Source project/article/discussion + link**
2. **Problem category** (Proxy/Types/Auth/Process/Performance)
3. **One-paragraph description of the problem**
4. **How it was discovered** (test, production incident, user report)
5. **Resolution** (fix, workaround, accepted limitation)
6. **Zorivest relevance** (which of our 10 friction areas + specific build plan section)
```

---

## Research Prompt 5: Pre-mortem Synthesis (Claude)

> **Assignment:** After prompts 1–4 produce results, synthesize into a Zorivest friction inventory.
> **Model:** Claude Opus 4.6 (extended thinking)

```markdown
# Synthesis: Zorivest MCP Server Pre-mortem Friction Inventory

## Instructions
You have received friction findings from 4 research vectors:
1. Python MCP ecosystem (FastMCP, official SDK, community)
2. TypeScript MCP SDK & ecosystem
3. Large-scale MCP implementations
4. Hybrid architecture & REST proxy patterns

## Task
Create a **Zorivest Friction Inventory** organized by our 10 friction areas.

For each friction area:

### Structure
1. **Risk Level**: 🔴 High / 🟡 Medium / 🟢 Low
2. **Evidence Sources**: List specific issues/PRs from research findings
3. **Most Likely Failure Scenario**: How this will bite us, specifically
4. **When It Will Surface**: During development, testing, or production
5. **Mitigation Strategy**: Concrete preventive action tied to a build plan section
6. **Test Case**: Specific test to write that would catch this early

### The 10 Friction Areas
1. Tool registration at scale (68 tools)
2. Middleware composition (withGuard→withMetrics→withConfirmation)
3. Dynamic toolset loading (list_changed notifications)
4. Auth bootstrap lifecycle (session tokens)
5. Adaptive client detection (clientInfo parsing)
6. Transport compatibility (Streamable HTTP)
7. Zod schema edge cases
8. Binary content handling (base64 images)
9. Cross-platform process management
10. IDE tool count limits (Cursor 40-tool cap)

### Additional Analysis
After the 10 friction areas, add:

**Unexpected Friction** — Problems that DON'T fit our 10 categories but emerged from research.
These are blind spots we haven't planned for.

**Design Decisions to Reconsider** — Findings that suggest our build plan may have made
a wrong call on a specific design choice. List the build plan section and the alternative.

**Confidence Assessment** — For each friction area, rate how confident we are in our
mitigation strategy: Strong (multiple evidence sources, clear fix), Moderate (some evidence,
reasonable fix), Weak (limited evidence, uncertain fix).

## Build Plan Context
[Attach: 05-mcp-server.md, mcp-tool-index.md, dependency-manifest.md, testing-strategy.md]
```

---

## Execution Order

| Step | Prompt | Model | Depends On | Expected Output |
|---|---|---|---|---|
| 1 | Research: Python MCP Ecosystem | Gemini Deep Research | — | Friction inventory (Python) |
| 2 | Research: TypeScript MCP SDK | ChatGPT o3 | — | Friction inventory (TypeScript) |
| 3 | Research: Large-Scale Implementations | Claude Opus 4.6 Research | — | Friction inventory (Scale) |
| 4 | Research: Hybrid Architecture | Gemini Deep Research | — | Friction inventory (Hybrid) |
| 5 | Synthesis: Pre-mortem Inventory | Claude Opus 4.6 Thinking | Steps 1–4 | **Zorivest Friction Inventory** |

Steps 1–4 can run in parallel. Step 5 requires all four to complete.

---

## After Research: Next Steps

1. **Create** `docs/build-plan/friction-inventory.md` from synthesis output
2. **Update** `testing-strategy.md` with friction-derived test cases
3. **Add** preventive items to `build-priority-matrix.md` where appropriate
4. **Create** `.agent/context/known-issues.md` entries for anticipated friction
5. **Review** build plan sections flagged for "Design Decisions to Reconsider"
