# Implementation Context: Resolved Decisions & Approach

> **Status:** All 17 questionnaire answers processed. Research synthesis complete. 10 research-derived features incorporated. Critical review findings resolved (v3).

---

## Day-1 Baseline Contract

> [!IMPORTANT]
> This section resolves Critical-1, High-1, and Q1–Q3 from the [pre-implementation critical review](file:///p:/zorivest/.agent/context/handoffs/2026-03-06-mcp-resolved-plan-preimplementation-critical-review.md). These decisions are frozen before implementation begins.

### Transport

| Aspect | Decision |
|---|---|
| Protocol | **Streamable HTTP** (MCP spec 2025-06-18) |
| Day-1 scope | localhost only (`http://localhost:8766/mcp`) |
| Remote future | Design connection/auth interfaces for remote from day-1. Implementation deferred. |
| stdio | Not supported. HTTP-only per user decision. |

### Day-1 Client Target

| Aspect | Decision |
|---|---|
| Primary client | **Antigravity** (this agent) |
| Client mode | `dynamic` — supports `notifications/tools/list_changed` |
| Tool count cap | **None for Antigravity.** Load all default toolsets without artificial 37-tool Cursor ceiling. |
| Detection model | **Capability-first, name-fallback.** Check `capabilities.tools.listChanged` and other capability fields first. Fall back to `clientInfo.name` matching only when capabilities are absent. |
| Cursor/Windsurf sizing | Applied ONLY when client is detected as static (no `listChanged` support). The 37-tool cap is a defensive fallback, not the design target. |

### Auth Bootstrap & Secret Lifecycle

```
IDE Config                          MCP Server (TS, :8766)              Python API (:8765)
─────────                          ──────────────────────              ─────────────────
Authorization: Bearer zrv_sk_...   
     │                              
     │── HTTP POST /mcp ──────────▶ Extract API key from               
                                    request Authorization header        
                                         │                              
                                    First request only:                 
                                    POST /auth/unlock {api_key}  ──────▶ Validates key
                                         │                              Returns session_token
                                         ▼                              
                                    Store session_token in memory       
                                    (short-lived, e.g. 1h TTL)         
                                         │                              
                                    Subsequent REST calls:              
                                    Authorization: Bearer <session_token>
                                         │                              
                                    On 401 from Python API:             
                                    Re-extract API key from CURRENT     
                                    incoming MCP request header          
                                    → POST /auth/unlock again           
                                    → Get new session_token             
```

| Rule | Detail |
|---|---|
| **API key storage** | Never stored by MCP server. Extracted from each incoming HTTP request's `Authorization` header on-demand. |
| **Session token storage** | Stored in-memory. Short TTL. Resets on server restart. |
| **Re-authentication** | On 401 from Python API, extract API key from the CURRENT incoming MCP request and re-authenticate. No cached secret replay. |
| **Token audience** | Session token is audience-bound to `http://localhost:8765` (Python API). |
| **Future remote** | Upgrade to OAuth 2.1 PKCE flow per MCP spec authorization section. Auth interfaces designed for this from day-1. |

> This resolves the apparent contradiction in `05-mcp-server.md:283`. The MCP server "never stores the raw API key" because the key flows through from the IDE in each HTTP request. "Re-authenticates using the original header value" means extracting from the current request, not replaying a cached copy.

### Response Contract

| Layer | Format | When |
|---|---|---|
| **Day-1** | `content: [{ type: 'text', text: JSON.stringify(data) }]` | All tools from Phase 5 launch |
| **Phase 5.E** | Add TypeScript `outputSchema` interfaces (internal contract enforcement) | After initial tools are stable |
| **Post SDK #911 resolution** | Dual-format: `content[].text` (backward compat) + `structuredContent` (typed) | When client handling of `structuredContent` stabilizes |

> Tools MUST always include `content[].text` with serialized JSON, even after adding `structuredContent`. This ensures backward compatibility per MCP tools spec and addresses the inconsistent client handling documented in TypeScript SDK issue #911.

### Default Tool Cohort

| Client Mode | Default Loadout | Rationale |
|---|---|---|
| **Antigravity / dynamic** | `core` + `discovery` + all default toolsets (trade-analytics, trade-planning) | No artificial cap. Dynamic loading available for deferred toolsets. |
| **Anthropic** | `core` + `discovery` (15 tools). All others deferred + BM25 searchable. | Anthropic's `defer_loading` annotation handles large catalogs natively. |
| **Static (Cursor, Windsurf, unknown)** | `core` + `discovery` + user-selected via `--toolsets`. Max 37 tools. | Defensive cap for tool-limited clients. |

---

## Pinned SDK Version & Issue Matrix

> Resolves High-3 from the critical review. Friction inventory items become dynamic inputs linked to SDK version, not static architectural premises.

| Aspect | Decision |
|---|---|
| **Pinned SDK** | `@modelcontextprotocol/sdk@^1.26.0` (v1.x production line) |
| **v2 policy** | Do NOT upgrade to v2 (`main` is pre-alpha). Pin to v1.x until v2 is GA. |
| **Issue tracking process** | At the start of each implementation phase, check status of all friction inventory issues against pinned SDK version. Update FR-* items accordingly. |
| **Known issue status (as of 2026-03-06)** | #1106 closed ✅, #1291 open 🔴, #1564 open 🔴, #911 open 🔴 |

---

## Resolved Decisions Summary

### Architectural Decisions (Changed from Original Plan)

| Decision | Original | User Decision | Impact |
|---|---|---|---|
| **Transport** | stdio-first | **HTTP-only** (Streamable HTTP) | Session management, auth lifecycle immediate. See Day-1 Baseline Contract above. |
| **Auth** | Defer | **Auth from day-1**, even localhost | API key → session token exchange. See auth lifecycle above. |
| **Trade safety** | withConfirmation | **Not applicable** — Zorivest does not execute trades | `withConfirmation` applies only to data-destructive operations (deleting records), not financial execution. |
| **Middleware** | 3 stages, defer | **4+ stages**, formalize pipeline | Pipeline stage registry justified. Named stages: `auth → guard → metrics → handler`. |

### Domain A: Deployment & Client Targeting

| Item | Answer |
|---|---|
| **IDE priority** | Antigravity → VS Code+ChatGPT Codex → VS Code+Claude Code → VS Code+Cline → Kiro → Cursor |
| **Platform** | Windows first, cross-platform later. Remote hosting as future requirement. |
| **Access** | Local-only initially, but **design for remote** from the start. |

### Domain B: First Vertical Slice

| Item | Answer |
|---|---|
| **First slice** | Trade entry/tracking (create, read, update) |
| **Production threshold** | Works for personal daily use + smooth UX |
| **Data providers** | Yahoo Finance, TradingView (free, minimal/no API). Default out-of-box. |

### Domain C: MCP Server Scope

| Item | Answer |
|---|---|
| **Tool ordering** | Simplest first → most complex last |
| **Auth** | Required from day-1 even for localhost |
| **Health monitoring** | Yes — integrated with diagnose MCP tool + new health route |

### Domain D: Dual-Agent Workflow

| Item | Answer |
|---|---|
| **Reviewer model** | **GPT-5.4** (locked — resolves Medium-1 governance drift) |
| **Reviewer capability** | Run commands, execute tests, create handoff docs with test improvements |

**Reviewer validation priority order:**

| Rank | Validation Type |
|---|---|
| 1 | Contract tests pass/fail |
| 2 | Security posture review |
| 3 | Adversarial edge case generation |
| 4 | Code style/pattern consistency |
| 5 | Documentation accuracy |

### Domain E: Safety

| Item | Answer |
|---|---|
| **Trade confirmation** | Not needed. Zorivest does not execute trades. |
| **Destructive operations** | Standard data-deletion confirmation for record management only |

### Domain F: FastMCP Features (Resolved Sequence)

| Rank | Feature | Rationale |
|---|---|---|
| 1 | Multi-dimensional tags | Foundation for pipeline conditions, metrics filtering, search indexing |
| 2 | Pipeline stage registry | 4+ stages confirmed. Formalize early. |
| 3 | Output schemas | Internal contract enforcement first, client-facing after SDK #911 resolves |
| 4 | BM25 tool search | Category browsing sufficient initially. BM25 when catalog has real content. |
| 5 | Health check route | Trivially simple once HTTP server exists. |

---

## Research-Enhanced Additions

> 10 features from the [research synthesis](file:///p:/zorivest/_inspiration/agentic_mcp_research/research-synthesis-correlation.md), placed in build plan execution order.

### Phase 5: MCP Server

| Order | Feature | Source | Insert After | Dependency Rationale |
|---|---|---|---|---|
| 5.A | **Multi-Dimensional Tags** | Tier 1, FastMCP | Item 13 (TS MCP tools) | Tag schema before any tool registers. Foundation for pipeline, BM25, metrics. |
| 5.B | **Pipeline Stage Registry** | Tier 1, FastMCP | Item 15e (MCP Guard) | Named stages need guard/metrics first. Formalizes composition into pluggable registry. |
| 5.C | **Health Check Route** | Tier 1, FastMCP | Item 15f (zorivest_diagnose) | `/health` on port 8766. Service daemon needs it for liveness probes. |
| 5.D | **Schema Drift Detection** | Tier 1, MXCP | Item 14 (MCP+REST integration) | CI script: Zod ↔ Pydantic comparison. Phase 5 exit criterion, formalized as CI in Phase 7. |
| 5.E | **Structured Output Schemas** | Tier 2, FastMCP v3 | Item 15k (ToolsetRegistry) | Internal TypeScript interfaces first. Dual-format `text` + `structuredContent` after SDK #911. |
| 5.F | **BM25 Tool Search** | Tier 1, FastMCP | Item 15k (ToolsetRegistry) | Indexes tags from 5.A. Powers Anthropic discovery mode. |
| 5.G | **Keyword-Triggered Loading** | Tier 2, Kiro Powers | After 5.F (BM25) | "tax" mention → suggest `enable_toolset('tax')`. Requires toolsets + client detection. |
| 5.H | **IDE Config Templates** | Tier 2, Ecosystem | After 15k (client detection) | Auto-generate per-IDE MCP configs. Requires client detection to know IDE types. |

### Post-Phase 8: Market Data

| Order | Feature | Source | Insert After | Dependency Rationale |
|---|---|---|---|---|
| 8.A | **Code Mode Enhancement** | Tier 2, Cloudflare | Item 29 (Market data MCP) | Expand PTC beyond Anthropic analytics. Requires stable tools from Phases 5 + 8. |

### Post-Phase 9: Scheduling

| Order | Feature | Source | Insert After | Dependency Rationale |
|---|---|---|---|---|
| 9.A | **Recursive Orchestration** | Tier 3, mcp-agent | Item 49 (Security guardrails) | Multi-agent MCP chaining for automated pipelines. Requires scheduling engine maturity. |

---

## Directives to Codify in .agent Files

| Directive | Where to Add |
|---|---|
| "Time is not a constraint in agentic development cycles" | `GEMINI.md`, `AGENTS.md` — Execution Contract |
| "Token usage is not a constraint (subscription-based)" | `GEMINI.md`, `AGENTS.md` — Execution Contract |
| "Quality / wisdom / expert experience metrics are above all" | `GEMINI.md` — Quality-First Policy |
| "Do not bring up time or token usage in design discussions" | `GEMINI.md`, `AGENTS.md` — anti-pattern rule |
| "Zorivest does NOT execute trades — it plans and evaluates" | `AGENTS.md` — Project Context |
| "GPT-5.4 is the standing reviewer/tester baseline" | `GEMINI.md` — Dual-Agent section |
| "Reviewer runs commands and creates handoff docs for findings" | `GEMINI.md` — Reviewer capability |

---

## Critical Review Resolution Log

> Tracks how each finding from the [pre-implementation critical review](file:///p:/zorivest/.agent/context/handoffs/2026-03-06-mcp-resolved-plan-preimplementation-critical-review.md) was resolved.

| Finding | Severity | Resolution |
|---|---|---|
| **Critical-1:** Auth lifecycle contradictory | Critical | Resolved. New "Auth Bootstrap & Secret Lifecycle" section clarifies API key passthrough model. Key flows from IDE header on each request, never stored by MCP server. |
| **High-1:** Client baseline sized for Cursor | High | Resolved. Day-1 client = Antigravity (dynamic, no tool cap). Detection changed to capability-first, clientInfo.name as fallback. 37-tool cap only for static/unknown clients. |
| **High-2:** Structured output maturity overstated | High | Resolved. Phased rollout: text-only day-1 → internal TypeScript interfaces → dual-format after SDK #911. Contract tests assert both envelopes. |
| **High-3:** Friction inventory as static premise | High | Resolved. New "Pinned SDK Version & Issue Matrix" section. Friction items checked against pinned SDK version at each phase start. Issue #1106 closed, #1291/#1564/#911 still open. |
| **Medium-1:** Governance drift (GPT-5.3 vs 5.4) | Medium | Resolved. GPT-5.4 locked as reviewer baseline. `current-focus.md` update pending. |
| **Q1:** Day-1 client target | Open Q | Answered: Antigravity only. Already stated in A1 answer. |
| **Q2:** Bootstrap secret lifecycle after 401 | Open Q | Answered: Extract API key from current incoming MCP request → re-auth. See auth lifecycle diagram. |
| **Q3:** Output schemas internal vs client-facing | Open Q | Answered: Internal contract aid first (Phase 5.E), client-facing after SDK #911 resolves. |

---

## Next Steps

1. Update `docs/build-plan/05-mcp-server.md` with Day-1 Baseline Contract changes (auth clarification, capability-first detection, response contract)
2. Update `current-focus.md` to lock GPT-5.4 and remove "undecided" status
3. Codify the 7 directives into `.agent` files
4. Add pinned SDK issue matrix to `friction-inventory.md` or new tracking file
5. Update `build-priority-matrix.md` with the 10 research-derived items
