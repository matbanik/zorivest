# TypeScript MCP Server Friction Analysis for @modelcontextprotocol/sdk v1.x

## Scope and sources

This research focused on production friction patterns when building TypeScript MCP servers with **@modelcontextprotocol/sdk v1.x**, **Zod** validation, and “many tools” scale (15+ tools), with special attention to upgrade hazards and the emerging v1→v2 migration path. The primary evidence base is the upstream TypeScript SDK’s public issue/PR tracker (roughly ~200 issues and ~130+ PRs visible in the repository UI), plus release notes and a small set of large, real-world TypeScript MCP servers using the SDK and Zod. citeturn22view0turn26view0turn16search0turn29view0turn28search0

Two “large server” reference projects used as comparators (both TypeScript, SDK-based, and 15+ tools) were:

- **mobile-next/mobile-mcp**: a mobile automation MCP server whose README enumerates a long tool surface (device/app/screen interaction utilities) and points to a central server implementation file; the repository also includes a `test/` directory and a Mocha configuration file, suggesting a conventional Node testing setup. citeturn29view0  
- **ethanolivertroy/fedramp-docs-mcp**: a documentation MCP server explicitly describing **21 tools**, Zod schemas living under `src/tools/`, and a testing strategy that includes deterministic Vitest tests using fixtures and integration tests against the upstream dataset. citeturn28search0

## Zod schema edge cases

**Source:** modelcontextprotocol/typescript-sdk issue #1562. citeturn24view0  
**Category:** A  
**Summary:** `schemaToJson()` can emit JSON Schema containing local `$ref` pointers (e.g., via `z.globalRegistry` or `z.lazy`). The report describes two concrete failure modes: (1) some LLM clients can’t resolve `$ref` and will “stringify” nested objects, yielding server-side argument validation failures; and (2) it aligns with a separate AJV validation failure report that breaks `tools/list` when `$ref`/`$defs` appear. citeturn24view0turn2search3  
**Design flaw or edge case?** Design mismatch / ecosystem edge: `$ref` is valid JSON Schema, but many model-facing “schema consumers” and some validators behave as if schemas must be fully inlined. citeturn24view0turn2search3  
**Time to resolution:** Still open (≈13 days as of March 5, 2026; opened Feb 20, 2026). citeturn24view0  
**Mitigation:** Prefer **fully dereferenced/inlined** tool schemas when targeting LLM-driven tool calling: introduce a build step or runtime post-processing that inlines local `$ref` (strip `$defs`/`definitions`), or avoid `z.globalRegistry`/recursive structures in **tool input** schemas until upstream provides an official deref option. citeturn24view0

**Source:** modelcontextprotocol/typescript-sdk issue #1175. citeturn2search3  
**Category:** A  
**Summary:** Starting around SDK v1.22.0, `tools/list` may fail with `Invalid reference token: $defs` when schemas include `"$ref": "#/$defs/..."` (AJV error). The issue ties the failure to the newer schema conversion path where `toJsonSchema` uses `z.toJSONSchema()` and emits `$defs` rather than `definitions`. citeturn2search3  
**Design flaw or edge case?** Design flaw in “wire-format expectations”: the SDK emits one valid JSON Schema dialect, but internal validation tooling (or runtime config) appears not aligned to it across versions. citeturn2search3  
**Time to resolution:** Still open (duration not computable from the snippet alone; issue remains open in the captured state). citeturn2search3  
**Mitigation:** In production servers, add a **schema compatibility test** in CI that runs `tools/list` end-to-end under the SDK version you pin, and validate the resulting schema using the same validator stack your clients use (or a “strictest” baseline). If you must ship today, avoid `$defs`-producing constructs or flatten schemas. citeturn2search3

**Source:** modelcontextprotocol/typescript-sdk issue #702. citeturn3view0  
**Category:** A  
**Summary:** Zod `.transform()` functions are lost during conversion to JSON Schema (an inherent limitation: JSON Schema can’t represent transformations). The specific break shown is a `z.union([z.array(z.string()), z.string()]).transform(...)` that collapses to just the array shape in JSON Schema, removing the string option and causing client validation failures when clients send a JSON-serialized array string. citeturn3view0  
**Design flaw or edge case?** Edge case rooted in a fundamental representational mismatch; however, it becomes a design hazard if developers assume Zod transforms will be reflected in tool schemas presented to clients. citeturn3view0  
**Time to resolution:** Closed, but the close date is not visible in the captured excerpt; opened Jun 27, 2025. citeturn3view0  
**Mitigation:** Avoid relying on `.transform()` or `.preprocess()` to communicate accepted wire formats to clients. If you need “string or array” acceptance, model that **explicitly** in the exported tool schema (e.g., union types without transforms) and do parsing inside the handler or a pre-validation hook you control. citeturn3view0

**Source:** modelcontextprotocol/typescript-sdk issue #754. citeturn2search4  
**Category:** A  
**Summary:** OAuth server metadata parsing can fail when fields that are treated as “arrays” by the schema are returned as `null` by an upstream provider (example: `contacts` being `null` rather than an array). This is a classic `undefined` vs `null` vs missing-field interop mismatch. citeturn2search4  
**Design flaw or edge case?** Edge case, but common in real-world integrations because OAuth/OIDC metadata is often produced by heterogeneous systems. citeturn2search4  
**Time to resolution:** Not determinable from the captured excerpt (the excerpt does not show open/close state timing details). citeturn2search4  
**Mitigation:** In auth-adjacent components, normalize inbound JSON before validating (e.g., convert `null` arrays to `[]`, `null` objects to `{}` where appropriate), or define Zod schemas that accept `null` and coerce, but only when it is safe and spec-tolerant. citeturn2search4

**Source:** modelcontextprotocol/typescript-sdk issue #1361. citeturn2search8  
**Category:** A  
**Summary:** There is explicit demand for type coercion when tool arguments arrive with wrong types (e.g., model outputs “123” where a number is expected). The issue frames this as a common LLM/tooling reality rather than a rare bug. citeturn2search8  
**Design flaw or edge case?** Ecosystem edge: strict validation is correct, but real-world model output frequently violates strict typing. citeturn2search8  
**Time to resolution:** Not determinable from the captured excerpt. citeturn2search8  
**Mitigation:** Add explicit “model-tolerant” layers at the boundary: use Zod coercion (`z.coerce.*`) and/or structured preprocessing for narrow fields (enums, numbers, booleans) while keeping internal business logic strictly typed. Document which fields are coercible to avoid silent semantic bugs. citeturn2search8

## Transport and protocol friction

**Source:** modelcontextprotocol/typescript-sdk issue #1564. citeturn23view0  
**Category:** B  
**Summary:** **STDIO server transport can hard-crash** on client disconnect: if a client closes the stdio pipes before the server writes a response, Node throws an unhandled `EPIPE` and the process dies. The issue explicitly characterizes this as a stability/DoS risk for local agents relying on stdio-based MCP servers. citeturn23view0  
**Design flaw or edge case?** Design flaw in transport robustness: expected behavior is to treat broken pipes as a normal disconnect and close gracefully. citeturn23view0  
**Time to resolution:** Still open (≈12 days as of March 5, 2026; opened Feb 21, 2026). citeturn23view0  
**Mitigation:** Wrap `stdout.write()` and/or attach `error` handlers at the transport boundary, then translate `EPIPE` into a controlled session close. For production, also add a **process-level** safety net: `process.on('uncaughtException')` and `process.on('unhandledRejection')` that logs and exits cleanly under a supervisor (systemd/Kubernetes) rather than leaving corruption. citeturn23view0

**Source:** modelcontextprotocol/typescript-sdk issue #553. citeturn18view0  
**Category:** B  
**Summary:** In a stateful **Streamable HTTP** setup (Express + session ID management), `initialize` succeeds, but subsequent `tool/call` requests can return JSON-RPC `-32601 Method not found` even when the server believes it is correctly reusing the transport. The issue includes a reproduction outline including required headers such as `mcp-session-id`. citeturn18view0  
**Design flaw or edge case?** Likely an edge case caused by subtle session/transport lifecycle miswiring (server-constructed transport reuse, server instantiation per session, or request routing). However, it’s a high-impact operational hazard because it appears as a protocol-level failure, not an application error. citeturn18view0  
**Time to resolution:** Still open (≈282 days as of March 5, 2026; opened May 27, 2025). citeturn18view0  
**Mitigation:** Make session ownership explicit: one MCP server instance per logical service, and one transport instance per session ID; ensure `server.connect(transport)` is done exactly once per transport lifecycle, not per request. Add a contract test that replays `initialize → tools/list → tool/call` across the same session ID. citeturn18view0

**Source:** modelcontextprotocol/typescript-sdk issue #892. citeturn14view0  
**Category:** B  
**Summary:** Streamable HTTP deployments that run multiple server nodes behind a load balancer need a reliable mapping from `sessionId` to a resumable stream (`streamId`). The issue proposes aligning on a specific header behavior (`mcp-stream-id`) so clients can reconnect and servers can route to the correct stream across instances. citeturn14view0  
**Design flaw or edge case?** Ecosystem/architecture edge: resumability and horizontal scaling require protocol details that aren’t strictly necessary for single-instance deployments. citeturn14view0  
**Time to resolution:** Still open (≈266 days as of March 5, 2026; opened Jun 12, 2025). citeturn14view0  
**Mitigation:** If you plan to scale horizontally, treat Streamable HTTP as requiring **sticky sessions** (LB affinity) until an upstream standard exists; otherwise, store transport/session state in a shared store keyed by `mcp-session-id` and implement reconnection semantics deliberately. citeturn14view0

**Source:** modelcontextprotocol/typescript-sdk issue #1211. citeturn17view0  
**Category:** B  
**Summary:** A Streamable HTTP server can experience periodic “SSE stream disconnected: TypeError: terminated” behavior (every ~5 minutes) in MCP clients. The report’s sample code creates a new `StreamableHTTPServerTransport` and calls `server.connect(transport)` inside request handlers, which risks mismatched lifecycle management and premature closes. citeturn17view0  
**Design flaw or edge case?** Edge case caused by lifecycles being easy to misuse; it appears frequently enough to be labeled as a bug and “ready for work.” citeturn17view0  
**Time to resolution:** Still open (≈93 days as of March 5, 2026; opened Dec 2, 2025). citeturn17view0  
**Mitigation:** Establish a single “session transport registry” and ensure GET(SSE)/POST/DELETE handlers all reference the same transport object for the same session ID; do not reconnect the server per request, and ensure the close handler closes *only* the relevant transport/session. citeturn17view0

**Source:** modelcontextprotocol/typescript-sdk release notes v1.23.1 and v1.24.3. citeturn16search0  
**Category:** B  
**Summary:** Release notes describe transport-level behavior changes that can show up as “it worked yesterday” regressions: a patch release disables SSE “priming events” after a protocol update because some 1.23.x clients crashed when parsing an empty SSE `data` field, and another release fixes Streamable HTTP server connection handling to properly release HTTP connections after POST responses. citeturn16search0  
**Design flaw or edge case?** Compatibility edge: subtle changes in wire behavior can break clients that assume stricter invariants (e.g., “SSE data is never empty”). citeturn16search0  
**Time to resolution:** Shipped via releases (exact PR open/close timing not extracted here). citeturn16search0  
**Mitigation:** Pin SDK versions in production and upgrade under a “transport regression checklist”: initialize, list tools, call a tool, verify SSE/HTTP behavior under disconnect/reconnect, and run under the exact MCP clients you support. citeturn16search0

## Tool registration at scale

**Source:** modelcontextprotocol/typescript-sdk issue #1585. citeturn26view0  
**Category:** C  
**Summary:** `server.tool(name, description, inputSchema, callback)` can **silently** misinterpret a *plain JSON Schema object* as `ToolAnnotations`. The result is a tool registered with no parameters (`{type:"object", properties:{}}`), and arguments passed by clients are stripped without any warning or compile-time TypeScript failure. The report includes an excerpt of the branch logic that routes “any non-null object” into annotations. citeturn26view0  
**Design flaw or edge case?** Design flaw: the failure mode is silent and produces a superficially valid tool entry, making debugging at 40–70 tool scale particularly painful. citeturn26view0  
**Time to resolution:** Still open (≈8 days as of March 5, 2026; opened Feb 25, 2026). citeturn26view0  
**Mitigation:** Add a server startup assertion that **every registered tool** has a non-empty `inputSchema.properties` where expected, and fail fast if a tool schema is empty. Also, standardize tool registration to accept only the Zod raw-shape style (or a single wrapper factory) to prevent accidental “JSON Schema as annotations” calls. citeturn26view0

**Source:** modelcontextprotocol/typescript-sdk PR #1603 (targets `v1.x`). citeturn2view2  
**Category:** C  
**Summary:** A closely related misregistration can happen when developers pass `z.object({...})` directly to `server.tool()` as `inputSchema`. The PR explains the root cause: `z.object()` fails the “raw shape” check, then falls through to the “object → annotations” branch, resulting in empty parameters and stripped arguments. The fix adds `extractZodObjectShape()` to detect ZodObject schemas (Zod v3 and v4) and extract `.shape` for correct tool registration; tests were added and the PR reports 1551 tests passing. citeturn2view2turn2view0  
**Design flaw or edge case?** Design flaw: a very natural Zod usage pattern (`z.object`) produces a silent, runtime-only failure. citeturn2view2  
**Time to resolution:** PR still open (≈5 days as of March 5, 2026; comment timestamp Feb 28, 2026). citeturn2view2  
**Mitigation:** In large servers, enforce a single registration convention (raw shape objects only) or adopt a wrapper that accepts either (raw shape | ZodObject) and normalizes to the SDK’s expected input by extracting `.shape`. citeturn2view2

**Source:** modelcontextprotocol/typescript-sdk issue #898. citeturn2search7  
**Category:** C  
**Summary:** There is demand for “tool removal” / unregistration support, implying current patterns assume “tool set is static for the life of the process.” This is a friction point for servers that want dynamic capability exposure (e.g., per-tenant tools, feature flags, auth-scoped tools). citeturn2search7  
**Design flaw or edge case?** Feature gap rather than a bug; but it becomes an operational hazard if servers attempt ad-hoc dynamic changes without first-class support. citeturn2search7  
**Time to resolution:** Not determinable from the captured excerpt. citeturn2search7  
**Mitigation:** Prefer **static tool catalogs** and implement auth gating *inside* tools (return structured “not authorized” errors) rather than exposing/removing tools dynamically. If you must do dynamic catalogs, document client expectations around caching and refresh, and test client behavior explicitly. citeturn2search7

**Source:** modelcontextprotocol/typescript-sdk issue #1488 and PR #1068 (client notification handling). citeturn2search1turn48view0  
**Category:** C  
**Summary:** Tool list change notifications are a recurring interop pain point: an issue reports the SDK overwriting advertised tool `listChanged` capability to `false` even when enabled (breaking client expectations), while a client-side PR adds options for tool-list-changed notifications but warns that handlers can overwrite each other if not configured carefully. citeturn2search1turn48view0  
**Design flaw or edge case?** Likely design/implementation bug(s) plus interop complexity—clients differ in support for `notifications/tools/list_changed`, and servers don’t always control caching behavior. citeturn2search1turn48view0  
**Time to resolution:** Issue timing not determinable from the captured excerpt; PR #1068 is merged (timing not computed here). citeturn2search1turn48view0  
**Mitigation:** Don’t assume client support for list change notifications. For a 68-tool server, implement a “tool search” tool (see below) and/or include tool-versioning metadata in descriptions so clients can detect drift without relying solely on notifications. citeturn2search1turn28search0

**Source:** ethanolivertroy/fedramp-docs-mcp repository documentation. citeturn28search0  
**Category:** C  
**Summary:** A proven pattern for 20+ tool servers is **explicit “tool search” + deferred loading**: the server documents 21 tools and recommends keeping a small set always loaded (e.g., discovery/health/lookup) while using a `search_tools` tool to discover the rest. It also emphasizes consistent error payloads (`code`, `message`, optional `hint`) across tools. citeturn28search0  
**Design flaw or edge case?** Not a flaw—this is a scaling strategy that reduces client friction and combats UI/tool-picker overload. citeturn28search0  
**Time to resolution:** Not applicable (project pattern). citeturn28search0  
**Mitigation:** For a 68-tool production server, strongly consider a “capability front door”: a **search/discovery tool** plus a documented baseline tool subset, and avoid forcing clients to eagerly ingest all tools. citeturn28search0

**Source:** mobile-next/mobile-mcp repository documentation. citeturn29view0  
**Category:** C  
**Summary:** Another scaling pattern is “tool taxonomy by operational domain”: the README organizes tools into Device Management / App Management / Screen Interaction / Input & Navigation and points users to a single server source file for parameter specs, which is a pragmatic way to make a large tool surface understandable and testable. citeturn29view0  
**Design flaw or edge case?** Not a flaw—this is documentation and ergonomics work that reduces friction when the tool count is high. citeturn29view0  
**Time to resolution:** Not applicable (project pattern). citeturn29view0  
**Mitigation:** Mirror this structure in your own server: consistent tool naming prefixes, category grouping in descriptions, and a single “developer spec” page that enumerates tools, schemas, and error shapes. citeturn29view0

## SDK version compatibility and v1→v2 migration path

**Source:** modelcontextprotocol/typescript-sdk repository README (branch guidance). citeturn1search5  
**Category:** D  
**Summary:** The repository explicitly signals that **`main` is v2 pre-alpha**, and recommends production users stay on **v1** (using the `v1.0.0` branch for v1 docs). It also communicates expectations around v2 timing and post-v2 bugfix support for v1. citeturn1search5  
**Design flaw or edge case?** Not a flaw; it’s a critical stability signal. The friction comes from developers accidentally tracking `main` or copying examples from the wrong branch. citeturn1search5  
**Time to resolution:** Not applicable (project lifecycle statement). citeturn1search5  
**Mitigation:** Pin to explicit v1-compatible package versions and treat any `main`-branch examples as **non-production** unless confirmed v1.x compatible. citeturn1search5turn16search0

**Source:** modelcontextprotocol/typescript-sdk issue #809. citeturn16search8  
**Category:** D  
**Summary:** The SDK v2 tracking issue lists intended breaking shifts: changing types (remove passthrough), renaming classes to align with the Python SDK, auth cleanup (including reconsideration of proxy OAuth provider patterns), and migration to Zod v4; it also flags these as a “wishlist” dependent on demand/timeline. citeturn16search8  
**Design flaw or edge case?** Not a flaw; it’s a forward roadmap. The risk is that production servers that couple deeply to today’s v1 API shapes (auth helpers, types) may face non-trivial refactors. citeturn16search8  
**Time to resolution:** Still open (≈224 days as of March 5, 2026; opened Jul 24, 2025). citeturn16search8  
**Mitigation:** Prepare by isolating SDK-specific concerns behind an internal adapter (tool registry, transport binding, schema exporting) so v2 refactors do not touch business logic and Python-proxy call paths. citeturn16search8

**Source:** modelcontextprotocol/typescript-sdk issue #1252. citeturn1view0  
**Category:** D  
**Summary:** v2 explicitly aims to **decouple from Zod** and allow “bring your own validator,” labeled as a v2-breaking-change enhancement. citeturn1view0  
**Design flaw or edge case?** Not a flaw; it’s an architectural direction to reduce dependency lock-in and version skew. citeturn1view0  
**Time to resolution:** Still open (≈87 days as of March 5, 2026; opened Dec 8, 2025). citeturn1view0  
**Mitigation:** Even if you stay on Zod, structure your server so “validation” is an interface (validate/coerce + schema export) that could swap to another validator or to a JSON-Schema-first flow in v2. citeturn1view0

**Source:** modelcontextprotocol/typescript-sdk PR #1606. citeturn30view0  
**Category:** D  
**Summary:** A v2 refactor PR removes the **Zod result schema parameter** from several public APIs (including `Protocol.request()`, `Client.callTool()`, and a streaming request API), replacing it with internal result schema resolution by method name and leaving “escape hatches” for internal use. The description labels this explicitly as a breaking change. citeturn30view0  
**Design flaw or edge case?** Not a flaw; it’s API simplification. The friction is for advanced consumers who depended on passing explicit schemas, especially in generic client libraries and test harnesses. citeturn30view0  
**Time to resolution:** Merged Mar 4, 2026 (PR lifecycle duration not computed here). citeturn30view0  
**Mitigation:** If you maintain internal MCP clients/harnesses, assume v2 will expect fewer schema arguments and more “method-driven” schema inference; keep your own request wrappers thin and avoid depending on schema parameters as part of your public surface. citeturn30view0

**Source:** modelcontextprotocol/typescript-sdk FAQ on SSE deprecation. citeturn2search9  
**Category:** D  
**Summary:** The upstream documentation states that **SSE transport has been removed** and recommends **Streamable HTTP** instead. This is a migration pressure point for servers and clients that previously used SSE semantics. citeturn2search9  
**Design flaw or edge case?** Not a flaw; it’s a transport evolution. The friction is operational: migrating middlewares, proxies, and client expectations. citeturn2search9turn18view0  
**Time to resolution:** Not applicable (documented policy). citeturn2search9  
**Mitigation:** Treat SSE-related code as legacy; invest in Streamable HTTP session/testing infrastructure, including reconnection/disconnect tests and reverse-proxy compatibility tests. citeturn2search9turn14view0

**Source:** modelcontextprotocol/typescript-sdk issue #689. citeturn2search5  
**Category:** D  
**Summary:** AJV code generation can break in environments where `eval` / `new Function` is disallowed (example: Cloudflare Workers). The issue proposes upgrading AJV and notes it’s planned for v2. citeturn2search5  
**Design flaw or edge case?** Edge case for restricted runtimes, but crucial if you deploy in serverless/edge environments. citeturn2search5  
**Time to resolution:** Not determinable from the captured excerpt. citeturn2search5  
**Mitigation:** If you might target restricted runtimes, proactively test your server bundle under those constraints. Otherwise, standard Node deployments will not surface this, but transitive dependencies may change with upgrades. citeturn2search5

**Source:** modelcontextprotocol/typescript-sdk issue #985. citeturn16search4  
**Category:** D  
**Summary:** A TypeScript compilation failure is reported where the typechecker runs out of memory when using `client.getPrompt` (the report indicates memory growth to ~16 GB). This kind of failure matters when you have a large codebase and many tool schemas/types. citeturn16search4  
**Design flaw or edge case?** Type-system edge case: complex generics + large unions can explode compile-time resource usage. citeturn16search4  
**Time to resolution:** Not determinable from the captured excerpt. citeturn16search4  
**Mitigation:** Keep your tool schema typings as simple as feasible (favor runtime validation over extremely deep compile-time inference), and pin TypeScript versions as carefully as you pin SDK versions. citeturn16search4

## Testing patterns and CI approaches

**Source:** modelcontextprotocol/typescript-sdk PR #1603. citeturn2view2turn2view0  
**Category:** E  
**Summary:** The upstream SDK uses regression tests to prevent silent tool-schema breakage: this PR adds tests verifying that `z.object()` auto-unwrap works and that arguments are passed correctly, and reports a full test suite run (1551 tests) passing. citeturn2view2turn2view0  
**Design flaw or edge case?** Not a flaw; it’s a mature response to a subtle registration bug. citeturn2view2  
**Time to resolution:** PR still open in the captured state (≈5 days old as of March 5, 2026). citeturn2view2  
**Mitigation:** Mirror this strategy: for every tool registration pattern you support (raw shapes, ZodObjects, annotations), write a unit test that asserts the emitted `tools/list` schema and that a `tools/call` passes arguments untouched. citeturn2view2turn26view0

**Source:** modelcontextprotocol/typescript-sdk PR #1472. citeturn16search3  
**Category:** E  
**Summary:** The SDK maintainers treat auth and protocol parsing as integration-test-worthy: this PR references a large body of tests (hundreds of client tests and integration tests) as part of validating behavioral changes. citeturn16search3  
**Design flaw or edge case?** Not a flaw; it indicates that many “bugs” are cross-component and require more than unit coverage. citeturn16search3  
**Time to resolution:** Not determinable from the captured excerpt. citeturn16search3  
**Mitigation:** For your server, integration-test the **full proxy path** (MCP → TypeScript → Python REST → TypeScript → MCP) with a golden set of tool calls and failure-mode simulations (timeouts, invalid payloads, schema coercion). citeturn16search3turn18view0

**Source:** ethanolivertroy/fedramp-docs-mcp repository documentation. citeturn28search0  
**Category:** E  
**Summary:** A scalable testing pattern for large tool suites is explicitly documented: deterministic Vitest tests using small fixtures (`tests/fixtures`) for repeatability, plus integration tests that clone and index the live upstream dataset to catch schema/parser drift. The same project also documents MCP Inspector usage for interactive and CLI testing (`tools/list`, `tools/call`). citeturn28search0  
**Design flaw or edge case?** Not a flaw; this addresses “drift” (upstream data changes) and “contract” stability (tool schemas and output shapes). citeturn28search0  
**Time to resolution:** Not applicable (project pattern). citeturn28search0  
**Mitigation:** Adopt a two-tier testing approach: (1) fast, deterministic fixtures for CI and (2) scheduled integration runs against real services (your Python API staging) to detect contract breaks early. citeturn28search0

**Source:** mobile-next/mobile-mcp repository listing and README. citeturn29view0  
**Category:** E  
**Summary:** The project structure includes a `test/` directory and a `.mocharc.yml`, suggesting Mocha-based tests; the README also centralizes parameter specifications in a single server file, which is conducive to black-box tool-call tests that exercise the published contract. citeturn29view0  
**Design flaw or edge case?** Not a flaw; it’s a maintainability pattern that matters at high tool counts. citeturn29view0  
**Time to resolution:** Not applicable (project pattern). citeturn29view0  
**Mitigation:** Keep a single source of truth for tool definitions and generate (or at least validate) documentation from it; then attach a test harness that enumerates all tools and runs schema + smoke-call checks in CI. citeturn29view0turn26view0

## Cross-cutting mitigations for a 68-tool production server

**Source:** modelcontextprotocol/servers issue #3051. citeturn27view0  
**Category:** A–D (cross-cutting)  
**Summary:** A real-world compatibility regression shows how “schema edge cases” become “client outage”: after upgrading a server, both OpenAI’s agent tooling and the MCP Inspector failed to list tools due to `inputSchema.type` not matching `"object"` expectations, and OpenAI rejected a tool schema reporting `type: "None"` for `parameters`. citeturn27view0  
**Design flaw or edge case?** Ecosystem compatibility edge: different clients place additional constraints on tool schema shapes beyond “valid JSON Schema,” and a server upgrade can surface as a client hard error rather than a degraded experience. citeturn27view0turn24view0  
**Time to resolution:** Still open (≈101 days as of March 5, 2026; opened Nov 24, 2025). citeturn27view0  
**Mitigation:** Treat tool schema compatibility as a first-class contract. Before upgrades, run a client-matrix test: `tools/list` against MCP Inspector plus at least the MCP clients you care about most, and assert that every tool’s `inputSchema.type` is `"object"` and that schemas are free of `$ref` unless the client explicitly supports them. citeturn27view0turn24view0  

More broadly, the friction patterns above converge on a few production-grade guardrails:

- Maintain a **tool registry wrapper** that enforces one schema authoring style and validates “no empty schemas,” preventing silent `server.tool()` misregistration at large tool counts. citeturn26view0turn2view2  
- Add a **schema export compatibility gate**: reject `$ref`/`$defs` for tool inputs unless you actively dereference, and verify with the same validators/clients you deploy against. citeturn24view0turn2search3  
- Make transport lifecycle a tested component: disconnect/reconnect, session reuse, and multi-request flows should be part of CI, especially for Streamable HTTP sessions and stdio crash resilience. citeturn23view0turn18view0turn14view0  
- Plan for v2 by isolating SDK interactions (transport binding, schema conversion/export, tool registration API) behind an adapter layer, since v2 is explicitly tracking breaking shifts (validator decoupling, API changes). citeturn1search5turn16search8turn1view0turn30view0