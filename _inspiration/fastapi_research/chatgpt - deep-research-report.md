# Organizing Large FastAPI REST Layers for Shared Backends

## Evidence from large open-source FastAPI codebases

A consistent theme across mature FastAPI applications is that the “REST layer” is rarely a monolithic file once the API grows beyond a handful of route groups. Instead, production projects converge on a small set of repeatable patterns:

- a **thin composition root** (often `main.py` / `server.py` / `api.py`) that wires routers together, mounts sub-applications, and configures middleware; citeturn28search9turn33search1  
- many **small router modules** (usually one router per resource or capability slice) that remain readable and testable; citeturn33search5turn17search8  
- **Pydantic schema organization** that is either (a) centralized (shared schema packages) or (b) co-located within each domain package, depending on team preferences and the desired coupling; citeturn35view0turn34view0turn35view1  
- explicit handling of **cross-cutting concerns** at router boundaries (router-level dependencies for auth, mode-gating, org scoping), plus app-level middleware for CORS/logging/metrics. citeturn22view0turn16view0turn13view0  

Below are concrete examples (with directory-style summaries) from open projects that exceed “10+ route groups” and serve multiple internal/external consumers (UI/dashboard, CLI/SDK, background services, etc.).

**entity["organization","Prefect","workflow orchestration"] (multi-consumer: Python SDK + dashboard/UI + background services)**  
Prefect’s server constructs an API app by composing a large router list (`API_ROUTERS`) and then mounts it under `/api`, while also mounting a UI app at `/`. citeturn13view0turn10search5 This is exactly the “shared backend for multiple consumers” scenario: Prefect explicitly documents that its REST API is consumed by clients such as the Python SDK and the server dashboard. citeturn10search5  

Concrete routing organization:

- **How many route files / groups?** Prefect enumerates **23 routers** in `API_ROUTERS` (flows, flow runs, deployments, logs, workers, admin, UI slices, etc.). citeturn13view0  
- **How routes are grouped:** primarily **resource-centric** (flows, deployments, logs…), with a small set of **UI-oriented routers** alongside core resources (e.g., `api.ui.*`). citeturn13view0  
- **Where schemas live:** separate shared package `prefect.server.schemas`, imported by router modules (example: `flows.py` uses `schemas.actions.*`, `schemas.core.*`, `schemas.filters.*`). citeturn35view0  
- **Cross-cutting concerns:** global dependencies (minimum API version enforcement) applied when including routers; middleware for CORS/GZip; dedicated health/version endpoints; exception handlers; and conditional request limiting for SQLite to reduce write contention. citeturn13view0turn10search12  

Illustrative structure (simplified from the server wiring and module paths): citeturn13view0turn35view0  
```text
src/prefect/server/
  api/
    server.py              # builds FastAPI apps; mounts /api and / (UI)
    flows.py               # router = PrefectRouter(prefix="/flows", tags=["Flows"])
    flow_runs.py
    task_runs.py
    deployments.py
    logs.py
    workers.py
    ... (many more)
  schemas/                 # shared Pydantic schemas (actions/core/filters/etc.)
  models/                  # persistence-facing “models” layer called by routers
```

**entity["company","Netflix","streaming company"] Dispatch (multi-consumer: web UI + CLI + plugin system)**  
Dispatch is a canonical example of a “big FastAPI app” that leans hard into modular organization: it creates multiple FastAPI apps (main app, frontend app, API app), mounts the API under `/api/v1`, and (optionally) serves a SPA frontend via mounted static files. citeturn22view0turn17search9 The Netflix Tech Blog introduction explicitly calls out Dispatch’s core components, including **Python with FastAPI** plus a **VueJS UI** and Postgres. citeturn17search9 The project also ships a CLI for operational tasks (configuration, server, scheduler, plugins, DB, shell). citeturn20search6  

Concrete routing organization:

- **How many route files / groups?** The central `api.py` composes **52 router inclusions** (a large set of domain/resource routers) and imports **47 routers from per-domain `views.py` modules**, plus auth/user routers. citeturn22view1  
- **How routes are grouped:** a blend of **resource-ish grouping** (incidents, cases, projects, tags, workflows…) *and* a **domain package pattern**: each domain typically has a `views.py` router plus adjacent `models.py`, `service.py`, `flows.py`. citeturn22view1turn34view0  
- **Where schemas live:** strongly **co-located**. Example: `dispatch/incident/views.py` imports request/response models like `IncidentCreate`, `IncidentRead`, `IncidentUpdate` from the incident package’s `.models`. citeturn34view0  
- **Cross-cutting concerns:**  
  - API-level auth is applied via router dependencies (e.g., org-scoped routers included with `Depends(get_current_user)`), plus an organization slug path prefix strategy. citeturn22view1  
  - app-level middleware + instrumentation: GZip, rate limiting (SlowAPI), Sentry middleware, metrics middleware, and a DB session middleware that scopes sessions per request and commits/rolls back safely. citeturn22view0turn22view1  
  - health check endpoint defined on the API router (`/healthcheck`). citeturn22view1  

Illustrative structure (simplified from the app composition and domain imports): citeturn22view0turn22view1turn34view0  
```text
src/dispatch/
  main.py                  # creates app + frontend + api; mounts /api/v1 and /
  api.py                   # central API router compositor; includes many routers
  auth/
    views.py               # (user_router, auth_router)
    service.py
    permissions.py
  incident/
    views.py               # router = APIRouter(); endpoints for incidents
    models.py              # IncidentCreate/Read/Update, pagination schemas, etc.
    service.py             # business/data orchestration called by views
    flows.py               # background workflows triggered by endpoints
  case/
    views.py
    type/views.py
    priority/views.py
    ...
  project/
    views.py
  ... (many more domain packages)
```

**entity["organization","Freqtrade","crypto trading bot"] (multi-consumer: CLI + REST API + web UI + lightweight client)**  
Freqtrade is a trading/bot platform that ships a built-in FastAPI webserver for both API access and UI serving (“FreqUI”). The docs explicitly mention the UI served by the built-in webserver and that API clients are encouraged to use a dedicated lightweight `freqtrade-client`. citeturn14search4turn14search1  

Concrete routing organization:

- **How many route files / groups?** In its API server wiring (`webserver.py`), Freqtrade includes **12 routers** into the FastAPI app (public v1 router, auth router, authenticated v1 router, trading router, webserver router, backtest router, background tasks router, history/pairlists/download routers, websocket router, and a UI router that must be included last). citeturn16view0  
- **How routes are grouped:** a **capability/mode split** is explicit:
  - trading-only routes are gated with a dependency like `is_trading_mode`
  - webserver-mode endpoints (e.g., backtesting/download tasks) are gated with `is_webserver_mode`
  - authentication is separated and applied via router-level dependencies (HTTP basic or JWT). citeturn16view0  
- **Where schemas live:** a large Pydantic schema module (`api_schemas.py`) sits adjacent to router modules under `freqtrade/rpc/api_server/` and is imported by route modules (e.g., `api_v1.py`). citeturn16view1turn35view1  
- **Cross-cutting concerns:** CORS middleware, a custom exception handler for RPC errors, OpenAPI tags metadata describing groups like Auth, Trades, Backtest, FreqAI, Webserver, etc. citeturn16view0  

Illustrative structure (simplified from the API server imports / include_router wiring): citeturn16view0turn16view1turn35view1  
```text
freqtrade/rpc/api_server/
  webserver.py             # constructs FastAPI app; include_router(...) wiring
  api_auth.py              # login/auth router
  api_v1.py                # main v1 router (authenticated)
  api_background_tasks.py
  api_backtest.py
  api_download_data.py
  api_pair_history.py
  api_pairlists.py
  api_trading.py
  api_webserver.py
  api_ws.py                # websocket endpoints
  api_schemas.py            # Pydantic models for request/response payloads
  web_ui.py                # UI router ("MUST be last")
  deps.py                  # dependency functions (mode gating, etc.)
```

**entity["organization","Open WebUI","open-source ai interface"] (multi-consumer: SPA UI + API + compatibility surfaces)**  
Open WebUI is a large FastAPI backend powering a SPA and multiple functional areas. Its backend `main.py` imports **27 router modules** (analytics, audio, images, models, tools, users, etc.), and defines both public and authenticated endpoints (e.g., `/api/config`, `/api/version`, task endpoints, chat endpoints). citeturn29view0turn30view0turn30view1 It also provides health endpoints (`/health`, `/health/db`) and mounts static assets (and mounts a SPA build directory when present). citeturn30view1  

Concrete routing organization (from the observable composition points):

- **How many route files / groups?** At least **27 router modules** are imported from `open_webui.routers` alone, in addition to significant inline route definitions in `main.py` (chat actions, config/version, tasks, OAuth callbacks, etc.). citeturn29view0turn30view0turn30view1  
- **How routes are grouped:** by **domain/capability slices** (audio, images, retrieval, tools, users…), plus specialized API surfaces (OpenAI/compat and other adapters are reflected in router modules and main wiring; a core PR discussion references router inclusion and endpoint dispatch behavior). citeturn29view0turn28search3  
- **Cross-cutting concerns:** broad middleware use (CORS, sessions, compression, auditing middleware), plus dependency-based auth (`get_verified_user`) on sensitive endpoints; health checks; and SPA/static mounting. citeturn29view0turn30view0turn30view1  

Illustrative structure (based on module paths and app mounting): citeturn29view0turn30view1  
```text
backend/open_webui/
  main.py                  # app wiring, many endpoints, imports routers/*
  routers/
    analytics.py
    audio.py
    images.py
    ollama.py
    openai.py
    retrieval.py
    pipelines.py
    tasks.py
    auths.py
    chats.py
    users.py
    tools.py
    ... (many more)
  models/                  # persistence/domain models
  internal/                # DB/session helpers
  utils/                   # cross-cutting utilities + middleware helpers
```

**Official FastAPI “bigger applications” wiring pattern (project generator / template influence)**  
FastAPI’s own documentation demonstrates the “one router per module” approach and a thin composition root that calls `app.include_router(...)` for each group. citeturn33search5turn17search8 This guidance is echoed in community answers referencing the project generator layout (an `api.py` that imports endpoint modules and includes their routers), and it is explicitly how FastAPI expects “multiple files” to be structured. citeturn24search14turn28search9  

A key takeaway for your situation: even the official examples assume that **route modularity is normal**, and that the composition layer’s job is to stitch routers together, not to contain all endpoint definitions. citeturn33search5turn28search9  

## Patterns for shared-backend vs BFF in multi-consumer systems

A shared backend serving multiple consumers (desktop UI + MCP server + CLI/background workers) sits on a spectrum between:

- a **general-purpose shared API backend**, where all consumers speak the same API surface; and  
- **Backends for Frontends (BFFs)**, where each consumer (web, mobile, specialized agent layer) has a tailored backend that aggregates/optimizes calls for that consumer.

**entity["people","Sam Newman","microservices author"]’s BFF framing** describes a common journey: teams start with one general-purpose API and “add more functionality as required” to support new UI interactions; the BFF pattern is a response to the tension and complexity that can arise when a single API backend must satisfy divergent client needs. citeturn32search0turn32search6  

Major platform guidance aligns with that framing:

- **entity["company","Microsoft","software company"]’s Azure Architecture Center** positions “Backends for Frontends” as a way to avoid repeatedly customizing one backend for multiple frontends by introducing dedicated backends tailored to each client/interface. citeturn32search2  
- **entity["company","Amazon Web Services","cloud provider"]** similarly summarizes BFF as “one backend per user experience” rather than one general-purpose API backend. citeturn32search8  
- **entity["people","Martin Fowler","software author"]** notes that BFF can be extended beyond “web vs mobile” to “a backend for each micro frontend,” reinforcing that “frontend” is about differing client surfaces and needs, not only device type. citeturn32search4  

### Where the MCP layer fits

In your architecture, the TypeScript MCP server already acts like an **agent-oriented adapter layer**: it calls the REST API and exposes tools for agentic IDE interaction. Conceptually, that MCP server is very close to a BFF, because it can:
- choose higher-level tool semantics than raw REST resources,
- aggregate multiple REST calls into one tool action,
- provide agent-safe guardrails and rate limiting,
- insulate the REST API from rapid iteration in agent workflows.

This implies a strong default: keep the FastAPI REST layer organized around **domain/resources**, while letting the MCP server own “agent ergonomics.” That’s the same split you can observe in multi-consumer projects where one surface is “compatibility” or “UI convenience” rather than the canonical domain API:

- Prefect’s REST API is organized around core orchestration resources, but it also includes `api.ui.*` routers (UI convenience slice) inside the overall router list. citeturn13view0turn10search5  
- Open WebUI imports a wide set of capability routers and also supports specialized surfaces (reflected in router modules and main wiring; PR discussion highlights endpoint dispatch and router ordering concerns). citeturn29view0turn28search3  
- Freqtrade draws a firm line between “trading mode” and “webserver mode,” applying different router-level dependencies for those usage contexts while still sharing one backend. citeturn16view0turn14search4  

### Is there a standard for aligning route organization with consumer organization?

In the projects above, the dominant “standard” is:

- **Organize routes by domain/resource first** (stable, shared contract). citeturn13view0turn22view1turn35view0  
- Add **consumer-specific slices sparingly**, and keep them clearly labeled (e.g., `ui` routers, “compat” routers, “webserver mode” routers). citeturn13view0turn16view0turn28search3  

That approach minimizes churn when consumers evolve or multiply, while still allowing targeted optimizations for a special consumer when needed.

## Router vs sub-application choices in FastAPI

FastAPI provides two primary composition mechanisms that matter for large apps:

- `app.include_router(...)` for **routers** (same OpenAPI, same app lifecycle, same middleware stack unless overridden at router level). citeturn33search5turn17search8  
- `app.mount(path, subapp)` for **sub-applications** (independent app, independent OpenAPI/docs, independent routing space). citeturn33search1turn33search8  

The official guidance is explicit that mounting is for **independent** applications with their own OpenAPI and docs. citeturn33search1 The static files documentation reiterates that mounted apps are independent and will not appear in the main OpenAPI schema. citeturn33search8  

Two practical “production” implications show up in real projects:

- **Mounting is frequently used to separate API vs UI** (or API vs static assets):  
  - Dispatch mounts `/api/v1` and `/` (frontend), and configures separate FastAPI instances (main/app/frontend/api) with their own middleware. citeturn22view0turn22view1  
  - Prefect mounts `/api` (REST API) and `/` (UI). citeturn13view0  
  - Open WebUI mounts `/static` and mounts the SPA build directory at `/` when it exists. citeturn30view1  

- **Router inclusion remains the default for “internal modularity”** inside the API surface: route splitting for maintainability, not for OpenAPI separation. citeturn33search5turn17search8  

A subtle lifecycle point: FastAPI’s lifespan events are executed for the **main application**, not for mounted sub-applications. citeturn33search15 That matters if you mount sub-apps expecting them to share startup/shutdown behavior (DB initialization, background worker startup, dependency wiring). In practice, many large projects either:
- keep lifespans on the main app and treat subapps as routing partitions, or  
- explicitly manage initialization within each subapp if needed. citeturn13view0turn22view0turn33search15  

### Granularity and “self-contained routers” opinions (maintainers + community)

FastAPI’s docs and reference material consistently position `APIRouter` as the main tool for grouping path operations and structuring an app across multiple files. citeturn17search8turn33search5  

In community/maintainer discussion, “router modularity” is commonly treated as best achieved with simple functions that return routers rather than heavy abstractions. For example, in a FastAPI Discussion thread, **entity["people","Sebastián Ramírez","FastAPI creator"]** suggests that many “router customization” goals can be achieved with straightforward functions that build a router, define endpoints, and then include it with prefixes/tags/dependencies—without needing extra framework complexity. citeturn24search4  

A well-known community guide, **entity["people","zhanymkanov","software engineer"]’s fastapi-best-practices**, is explicitly written from experience building production systems and includes an opinionated “project structure” section. citeturn33search0 In an issue discussion about large/fintech APIs, a contributor describes isolating “api files” under `src/api` so the API layer can be removed/inspected independently of the rest of the application (middleware/models/events), reflecting a “thin API layer” mindset similar to your own delegation-only REST layer. citeturn33search14  

## Mapping real-world patterns to Zorivest route-splitting options

You’re building entity["company","Zorivest","desktop trading journal"] with a shared FastAPI backend consumed by:
- a desktop Electron/React GUI, and  
- a TypeScript MCP server that calls the REST API.

Given that shape, your four options differ mainly on *what you treat as the “primary axis”* for modularity: consumer, UI module, REST resources, or bounded contexts.

### Option A — mirror MCP categories

**What it optimizes:** the agent/tool mental model (diagnostics, planning, scheduling, behavioral, etc.).

**Pros**
- Strong alignment with the MCP tool taxonomy; can make your API spec docs feel “tool-first,” which is useful if you expect frequent agent-driven iteration and want to keep tool surfaces stable.  
- Mirrors patterns where multi-consumer backends carve out explicit slices for “special modes” or “special surfaces,” like Freqtrade’s trading-mode vs webserver-mode routers (dependency-gated) and Open WebUI’s multiple capability routers plus adapter surfaces. citeturn16view0turn29view0turn28search3  

**Cons**
- Higher risk of **REST drift**: route files become “use-case buckets,” and resource boundaries blur, which can make it harder to keep consistent CRUD semantics, pagination, caching, and client generation predictable across consumers. Prefect and Dispatch mostly avoid consumer-first router partitioning for their core APIs, using consumer-specific slices only sparingly (e.g., Prefect’s `api.ui.*`). citeturn13view0turn22view1  
- Since your MCP server is already an adapter/broker, you can keep consumer alignment in the MCP layer and keep the REST API domain-centric—reducing churn in the core API when MCP tools evolve.

**Closest observed analogs**
- Freqtrade’s “mode-gated router groups” are conceptually similar to consumer/mode partitioning inside one API. citeturn16view0  
- Prefect’s small `api.ui.*` slice is a “consumer convenience” add-on to a resource-centric API. citeturn13view0  
- Open WebUI’s discrete capability routers and compatibility layers reflect a backend that serves multiple client surfaces. citeturn29view0turn28search3  

### Option B — mirror GUI modules

**What it optimizes:** the desktop product’s UI information architecture.

**Pros**
- Tight cohesion between UI features and API router ownership can reduce cognitive overhead for feature teams (a “vertical slice” feel) when most work is UI-driven.
- Can pair nicely with Dispatch-style domain packages *if* your UI modules align cleanly with domain boundaries (e.g., “planning” maps to trade plans + reports). citeturn34view0turn22view1  

**Cons**
- A shared API should not assume the GUI is the only—or even primary—client. Prefect explicitly calls out that its API is consumed by both SDK clients and a dashboard; its route grouping is not “dashboard-page-first.” citeturn10search5turn13view0  
- UI modules often change as UX evolves; tying router boundaries too tightly to UI navigation can cause churn in the API layer even when the domain hasn’t changed.

**Closest observed analogs**
- Dispatch’s UI is domain-oriented; its API routers map to domain entities (incidents, cases, projects), not to “screens,” but the end result often still aligns with UI modules because the UI itself is built around those entities. citeturn22view1turn17search9  

### Option C — REST resource-centric

**What it optimizes:** a stable shared contract for multiple consumers.

**Pros**
- Most consistent with observed “shared backend” success cases: Prefect’s routers are by resource (flows, deployments, logs…), and Dispatch composes many resource routers into an org-scoped API. citeturn13view0turn22view1turn35view0  
- Plays best with OpenAPI-driven client generation and long-lived SDKs because tags/prefixes tend to be stable and predictable. FastAPI explicitly leans into OpenAPI generation and SDK generation workflows. citeturn33search13turn32search3  

**Cons**
- Resource-centric grouping can become awkward if your domain has “workflow” endpoints that cut across resources (e.g., “import trades” touches accounts + trades + broker mappings). Teams typically solve this by adding explicit action subroutes (e.g., `/trades/import`, `/accounts/{id}/sync`) or by introducing a small number of “workflow/task” routers. This is visible in Dispatch’s endpoint set (report generation endpoints, flows triggered by requests) and in Freqtrade’s backtest/download task endpoints. citeturn34view0turn16view0  

**Closest observed analogs**
- Prefect is a clean example of resource-centric routing with separate schema and model layers. citeturn35view0turn13view0  
- Dispatch’s `api.py` includes many resource routers (incidents, cases, projects, tags…), though the implementation is organized in domain packages. citeturn22view1turn34view0  
- Freqtrade has a resource-like `api_v1` surface plus capability routers for backtesting/webserver/trading. citeturn16view0turn16view1  

### Option D — hybrid domain-aligned (bounded contexts)

**What it optimizes:** cohesive ownership and separation of concerns across a modular monolith.

**Pros**
- Most similar to Dispatch’s “domain package” approach: a domain folder contains models/schemas, service layer helpers, and router definitions (`views.py`), keeping everything needed for that bounded context together. citeturn34view0turn22view1  
- Supports your stated architecture (thin REST delegation layer + service layer). Domains become natural “service owners,” with routers acting as adapters into those services.

**Cons**
- Requires discipline to avoid “mega-domains” (e.g., a `trades` context that becomes a dumping ground). Dispatch mitigates this by having many finely sliced packages (incident, incident_cost, incident_role, etc.) and then composing them centrally. citeturn22view1turn34view0  
- When domains share many schema fragments, you may be pulled toward either a shared schema package (Prefect-style) or carefully managed cross-domain schema imports, otherwise schemas become tightly coupled across domains. citeturn35view0turn34view0  

**Closest observed analogs**
- Dispatch is the most direct match: domain packages with adjacent `models/service/flows/views`, then a central `api.py` that wires everything together and applies auth/org scoping. citeturn22view1turn34view0turn22view0  

### A pragmatic synthesis for your specific Zorivest context

Given:
- you already have an MCP adapter layer (TS server) that can “speak tools,” and  
- your GUI is not a browser SPA but a desktop client that can evolve quickly,  

the pattern that best matches the mature open-source examples is typically:

- Choose **Option C or Option D** as the *code organization axis* for your FastAPI routers (resource-centric or bounded context). citeturn13view0turn22view1turn35view0  
- Add a small, explicit **“infra/system” router** for cross-cutting endpoints (health/version/logging/status), as seen across Prefect, Dispatch, and Open WebUI. citeturn13view0turn22view1turn30view1  
- If the MCP server needs special aggregations, keep them in the MCP server first; only introduce `/mcp/*` endpoints in FastAPI when you can justify them as (a) performance-critical, (b) transactionally safer, or (c) security boundary improvements—mirroring how mature systems add narrow consumer-specific slices rather than reorganizing the whole API around that consumer. citeturn13view0turn16view0turn32search0  

## Spec boundaries vs Python package boundaries and contract-first workflows

Your final question is essentially: “Should my documentation/spec split dictate the Python package structure?”

### What FastAPI’s model suggests (code-first, OpenAPI-derived)

FastAPI’s default posture is code-first: it generates an OpenAPI schema from your declared routes/models. citeturn32search3 It also provides guidance on generating client SDKs because the system is OpenAPI-based. citeturn33search13 In this world, **router/module boundaries are implementation choices**: your OpenAPI tags and paths will reflect how you include routers, but you are not forced into a spec-first file layout. citeturn33search5turn17search8  

In practice, the big codebases above tend to keep a fairly direct mapping: “router module boundaries ≈ conceptual endpoint group boundaries,” because it keeps lifecycle, auth dependencies, tests, and ownership clean. citeturn35view0turn22view1turn16view0  

### What contract-first teams do (OpenAPI-first)

Contract-first teams invert the flow: the OpenAPI contract is the source of truth, and code is generated or scaffolded from it.

A recent engineering write-up from **entity["company","Malt","ml platform company"]** describes a contract-first strategy with FastAPI and **OpenAPI Generator**, including automated code generation from the OpenAPI contract. citeturn32search5turn33search3 The **entity["organization","OpenAPI Generator","code generation tool"]** project itself describes generation of client libraries, server stubs, and documentation from an OpenAPI spec. citeturn33search21  

In this workflow, **spec boundaries often influence code boundaries** (e.g., tags become controller files), because code generation tools typically group operations by tags or paths.

### Practical guidance for Zorivest’s “spec docs” vs implementation

Given your current state (“04a-api-*.md” spec sections, and a single giant route specification file), a proven approach is:

- Treat the **spec-doc split as a forcing function** for code modularity *only if it matches stable ownership boundaries* (bounded contexts/resources). This is what you see in Dispatch and Prefect: the router/module graph mirrors stable domain/resource partitions. citeturn22view1turn35view0  
- If the spec-doc split is **consumer-shaped** (Option A/B), keep it as documentation organization if it helps humans—*but* don’t feel obligated to make it your Python package structure unless you are deliberately introducing BFF-like sub-surfaces inside the API. Sam Newman’s BFF discussion is effectively a warning that “one big API customized for all clients” can become messy; reorganizing the entire API around one client can reintroduce that mess at the code level. citeturn32search0turn32search8  
- If you plan to become truly contract-first later, consider aligning your OpenAPI tags and `operationId` strategy early (FastAPI explicitly supports OpenAPI-based client generation, where stable IDs matter). citeturn33search13turn17search8  

In short: **make each sub-file become a Python module when it represents a stable domain/resource boundary; otherwise keep spec organization independent.** This mirrors what large systems do: thin composition roots with many routers, and domain/resource modules as the unit of ownership and testability. citeturn13view0turn22view1turn16view0  

## Source index

```text
FastAPI docs
- Bigger Applications - Multiple Files: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Sub Applications - Mounts: https://fastapi.tiangolo.com/advanced/sub-applications/
- Static Files (mounting vs routers): https://fastapi.tiangolo.com/tutorial/static-files/
- Generating SDKs (clients): https://fastapi.tiangolo.com/advanced/generate-clients/
- APIRouter reference: https://fastapi.tiangolo.com/reference/apirouter/
- Lifespan events note re sub-apps: https://fastapi.tiangolo.com/advanced/events/

Project examples
- Prefect server API wiring (server.py): https://raw.githubusercontent.com/PrefectHQ/prefect/fe331da61f275cb67d7684e3ec155085bbb8cbbe/src/prefect/server/api/server.py
- Prefect flows router example (flows.py): https://raw.githubusercontent.com/PrefectHQ/prefect/fe331da61f275cb67d7684e3ec155085bbb8cbbe/src/prefect/server/api/flows.py
- Prefect REST API overview (multi-consumer note): https://docs.prefect.io/v3/api-ref/rest-api

- Dispatch (main app wiring): https://raw.githubusercontent.com/Netflix/dispatch/master/src/dispatch/main.py
- Dispatch (API router composition): https://raw.githubusercontent.com/Netflix/dispatch/master/src/dispatch/api.py
- Dispatch (domain router example: incident/views.py): https://raw.githubusercontent.com/Netflix/dispatch/master/src/dispatch/incident/views.py
- Netflix Tech Blog intro to Dispatch: https://netflixtechblog.com/introducing-dispatch-da4b8a2a8072
- Dispatch CLI docs: https://netflix.github.io/dispatch/docs/administration/cli

- Freqtrade API server wiring (webserver.py): https://raw.githubusercontent.com/freqtrade/freqtrade/develop/freqtrade/rpc/api_server/webserver.py
- Freqtrade API schemas (api_schemas.py): https://raw.githubusercontent.com/freqtrade/freqtrade/develop/freqtrade/rpc/api_server/api_schemas.py
- Freqtrade REST API docs (client guidance): https://www.freqtrade.io/en/stable/rest-api/
- Freqtrade UI (“FreqUI”) docs: https://www.freqtrade.io/en/2021.9/rest-api/

- Open WebUI backend main: https://raw.githubusercontent.com/open-webui/open-webui/main/backend/open_webui/main.py

BFF / shared vs tailored backends
- Sam Newman BFF pattern page: https://samnewman.io/patterns/architectural/bff/
- Azure Architecture Center BFF pattern: https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends
- AWS blog on BFF pattern: https://aws.amazon.com/blogs/mobile/backends-for-frontends-pattern/
- Martin Fowler on Micro Frontends (BFF extension): https://martinfowler.com/articles/micro-frontends.html

Contract-first / OpenAPI-first
- Malt Engineering contract-first write-up: https://blog.malt.engineering/design-generate-deploy-our-contract-first-api-strategy-with-fastapi-and-openapi-15bb3e855dff
- OpenAPI Generator project: https://github.com/OpenAPITools/openapi-generator

Community opinion references
- FastAPI maintainer discussion (router encapsulation): https://github.com/fastapi/fastapi/discussions/8991
- fastapi-best-practices repo: https://github.com/zhanymkanov/fastapi-best-practices
- fastapi-best-practices issue re large/fintech API structuring: https://github.com/zhanymkanov/fastapi-best-practices/issues/63
```
