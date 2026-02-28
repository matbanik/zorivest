# **Architectural Blueprint for Scalable FastAPI Backends: Domain-Driven Design, Documentation Granularity, and Multi-Consumer REST APIs**

The architectural design of modern trading platforms requires the seamless integration of high-performance backend services, real-time user interfaces, and advanced agentic artificial intelligence capabilities. In an ecosystem where a Python backend—utilizing FastAPI, a SQLCipher database, and a dedicated service layer—must simultaneously serve an Electron/React Desktop Graphical User Interface (GUI) and a TypeScript-based Model Context Protocol (MCP) server, structural organization becomes the paramount engineering concern.

When a central REST API documentation specification reaches unmanageable lengths—such as a monolithic 1,102-line file containing over 13 diverse route groups including trade execution, tax calculations, and settings management—it indicates a critical juncture in the software development lifecycle. Such monoliths degrade cognitive mapping for human developers and exceed the optimal context windows for AI-assisted coding agents, leading to hallucinations and fragmented implementations. This comprehensive report analyzes industry-standard organizational strategies for large-scale FastAPI projects, evaluates the trade-offs of domain-centric versus layered architectures, and provides concrete methodologies for structuring both the codebase and the accompanying specification documentation to support a dual-consumer model.

## **1\. Organizational Strategies in Large-Scale FastAPI Production Projects**

The evolution of FastAPI from a lightweight microframework to an enterprise-grade backend solution has resulted in the emergence of distinct organizational patterns. Unlike strictly opinionated frameworks such as Django or Ruby on Rails, FastAPI does not enforce a rigid directory structure, treating the application as a highly flexible composition of routers and dependency injection graphs.1 Consequently, analyzing real-world open-source deployments provides the most accurate blueprint for scaling complex applications such as financial trading platforms.

### **1.1 The Netflix Dispatch Pattern: Domain-Driven Modularity**

Netflix Dispatch, an open-source crisis management orchestration framework built on FastAPI, represents the industry gold standard for scaling complex Python backends.3 As the repository grew to support numerous integrations and internal processes, the engineering team transitioned away from traditional grouping by file type, adopting a deeply modular, domain-driven structure.3

In the Dispatch architecture, the src/ directory contains individual packages representing bounded contexts or specific business capabilities.3 A typical domain package (e.g., incident/, auth/, or task/) encapsulates everything required for that feature to function independently. The structural paradigm intentionally co-locates the router, the database models, and the business logic.

**Concrete Directory Structure Example (Netflix Dispatch Pattern):**

fastapi-project/

├── alembic/ \# Database migrations

├── src/

│ ├── main.py \# Application factory and router registration

│ ├── database.py \# Database connection pooling

│ ├── auth/ \# Bounded Context: Authentication

│ │ ├── router.py \# FastAPI APIRouter and endpoints

│ │ ├── schemas.py \# Pydantic validation models

│ │ ├── models.py \# SQLAlchemy database models

│ │ ├── service.py \# Core business logic

│ │ ├── dependencies.py \# Router-specific injection dependencies

│ │ └── exceptions.py \# Domain-specific HTTP exceptions

│ ├── trades/ \# Bounded Context: Trade Management

│ │ ├── router.py

│ │ ├── schemas.py

│ │ ├── models.py

│ │ └── service.py

│ └── tax/ \# Bounded Context: Tax Engine

│ ├── router.py

│ └──...

This structure allows a single engineering team to work entirely within one directory when adding a new feature, significantly reducing the cognitive friction associated with navigating across a vast repository.3 Furthermore, it establishes a clear path toward microservice extraction; if a domain such as the tax calculation engine becomes heavily loaded, its entire folder can be lifted and deployed as an independent service with minimal uncoupling required.

### **1.2 Tiangolo's Full-Stack FastAPI Template: Layered Architecture**

Sebastián Ramírez (the creator of FastAPI) maintains the official full-stack-fastapi-template, which employs a traditional layered, technical architecture.2 This pattern is heavily influenced by conventional Model-View-Controller (MVC) paradigms and categorizes code by its technical responsibility rather than its business function.

A standard implementation of this template organizes the app/ directory into horizontal layers. While highly structured, it separates the data validation from the routing, and the routing from the database models.

**Concrete Directory Structure Example (Tiangolo Layered Pattern):**

backend/

├── app/

│ ├── api/

│ │ ├── dependencies.py \# Global API dependencies

│ │ └── v1/

│ │ ├── api.py \# Central router inclusion

│ │ └── endpoints/ \# All route definitions

│ │ ├── users.py

│ │ ├── trades.py

│ │ └── tax.py

│ ├── core/ \# Global configuration and security

│ │ ├── config.py

│ │ └── security.py

│ ├── crud/ \# Database interaction layer

│ │ ├── crud\_user.py

│ │ └── crud\_trade.py

│ ├── models/ \# SQLAlchemy models

│ │ ├── user.py

│ │ └── trade.py

│ └── schemas/ \# Pydantic models

│ ├── user.py

│ └── trade.py

While this structure promotes strict separation of concerns at the technical level, it introduces significant friction for scaling monoliths. Implementing a new feature requires developers to open, modify, and manage state across four or five different directories simultaneously.6 As the application expands, folders like schemas/ and models/ become bloated catch-alls for the entire system's definitions.

### **1.3 Open-Source Trading Platforms: Dual Interface and Router-to-Provider Abstraction**

For financial and trading platforms, two open-source architectures provide profound insights into handling high-throughput, data-intensive backends.

**OpenBB (Open Data Platform):** OpenBB utilizes FastAPI to route requests to over 100 endpoints connected to various financial data providers.9 Their architecture utilizes a highly nested APIRouter implementation. OpenBB separates the API layer from the data provisioning layer using a "Transform-Extract-Transform" (TET) pipeline.9 A master openbb-core acts as the hub, while individual domains (e.g., openbb-equity, openbb-economy) act as sub-routers.9 This demonstrates how financial platforms handle massive endpoint expansion: by creating hierarchical routers that delegate entirely to a robust, heavily abstracted service layer.

**Open Paper Trading MCP:** The open-paper-trading-mcp repository is highly relevant to the Zorivest architecture, as it explicitly implements a dual-interface model: a REST API (FastAPI) and an AI agent toolset (MCP) backed by the exact same service layer.10

To avoid mounting conflicts and ensure independent scalability, this project utilizes a split-server initialization approach, launching the FastAPI server on port 2080 and the independent MCP server on port 2081\.10 Both interfaces inject the same TradingService through a unified dependency management system, ensuring that whether a human user executes a trade via the web client or an LLM executes a trade via the MCP tool, the core business rules and PostgreSQL database sessions remain absolutely identical.

### **1.4 Enterprise Domain-Driven Design (DDD) Implementations**

Enterprise implementations of Domain-Driven Design (DDD) in FastAPI take modularity a step further by entirely decoupling the business core from the web framework itself.11 In strict DDD Python projects, the domain layer does not import FastAPI or Pydantic; it relies solely on pure Python dataclasses and abstract base classes.

**Concrete Directory Structure Example (Enterprise DDD Pattern):**

src/

├── shared\_kernel/ \# Value objects shared across domains

└── trading\_journal/ \# Bounded Context

├── domain/ \# Pure business logic

│ ├── entities/ \# Trade, Account

│ ├── value\_objects/ \# Currency, TickerSymbol

│ └── repositories/ \# Abstract interfaces for DB

├── application/ \# Orchestrates use cases

│ └── use\_cases/ \# ExecuteTradeUseCase

├── infrastructure/ \# Concrete implementations

│ └── database/ \# SQLAlchemyRepository mapping

└── presentation/ \# Delivery mechanisms

├── rest\_api/ \# FastAPI routers

└── mcp\_server/ \# MCP tool definitions

In this architecture, the presentation/ folder clearly demonstrates how multiple consumers (REST API and MCP) can sit on top of the same application layer without entangling their logic. The ExecuteTradeUseCase is called by both the FastAPI route handler and the MCP tool executor. While academically pristine, strict DDD introduces massive boilerplate overhead.13 For a fast-moving desktop application, a pragmatic, module-based DDD approach (similar to Netflix Dispatch) is generally preferred over a strict architectural implementation.

## **2\. Trade-Offs in Modular Monolith Architecture**

For a desktop trading journal like Zorivest, which functions as a modular monolith before potentially scaling into distributed services, selecting the right architectural paradigm is a critical foundational decision. The trade-offs between Domain-per-package, Layer-per-folder, and Hybrid structures dictate the system's long-term maintainability, developer velocity, and resistance to technical debt.

### **2.1 Layer-per-Folder (Technical Grouping)**

The layered architecture groups code strictly by its functional role in the software stack (all routers together, all schemas together, all database models together).8

**Advantages:**

* **Rapid Initial Onboarding:** New developers immediately understand where to place a new database model or a new REST endpoint, as the structural rules are strictly defined by technical taxonomy.8  
* **Centralized Infrastructure:** It is easier to enforce global database patterns, migration tracking (via Alembic), or generic base classes when all models inherit from the same centralized models/base.py location.7  
* **Simplified Imports:** Circular import dependencies are less frequent because the dependency flow is strictly top-down (Routers \-\> Services \-\> Models).

**Disadvantages:**

* **High Coupling, Low Cohesion:** A change to the "Trades" feature requires context-switching between routers/trades.py, schemas/trades.py, models/trades.py, and services/trades.py.8 The business concept of a "Trade" is scattered across the repository.  
* **Scalability Bottlenecks:** As the application grows to encompass dozens of domains (brokers, tax, analytics, behavioral, discovery), the schemas and routers folders become massively bloated and unmanageable.3

### **2.2 Domain-per-Package (Functional Grouping / Domain-Driven)**

The domain-driven approach groups files by business capability or bounded context.3 A tax/ folder contains its own router.py, schemas.py, service.py, and models.py.

**Advantages:**

* **High Cohesion:** Everything related to calculating tax estimates or generating quarterly reports lives in one directory. The mental model of the codebase aligns directly with the business logic.8  
* **Strict Boundary Enforcement:** By encapsulating dependencies within the domain, cross-domain pollution is minimized. If the analytics domain needs data from trades, it calls the trades.service rather than querying the trades.model directly, enforcing clean internal APIs and preventing spaghetti code.3  
* **Refactoring Velocity:** Deleting, rewriting, or versioning a feature is localized to a single directory. If the "Behavioral" module needs to be replaced, the developer simply deletes the behavioral/ folder without hunting for orphaned schemas.8

**Disadvantages:**

* **Shared Resource Ambiguity:** Code that applies across multiple domains (e.g., common pagination schemas, generic HTTP exception handlers, or user authentication) requires a dedicated shared/ or core/ directory, which can sometimes become a dumping ground if not strictly governed.3  
* **Complex Migrations:** Alembic configuration becomes slightly more complex, as the env.py file must dynamically import models from dozens of nested domain folders rather than a single models/ directory.

### **2.3 The Hybrid Approach**

A hybrid architecture attempts to combine the two by maintaining a layered structure at the root but grouping by domain within those layers, or vice versa. For example, maintaining domain folders for business logic but keeping all database models centralized to simplify SQLAlchemy relationship mapping and migrations.

**Advantages:**

* **Pragmatic Compromise:** It allows for the cohesion of business logic while maintaining the technical simplicity of unified databases.

**Disadvantages:**

* **Architectural Confusion:** Without strict linting and enforcement, developers will be confused about where the boundaries lie. If a schema is used by the database and the router, does it belong in the domain folder or the global models folder? This leads to inconsistent code placement.

| Architectural Strategy | Cohesion | Coupling | Scalability for Large Projects | Navigation Friction |
| :---- | :---- | :---- | :---- | :---- |
| **Layer-per-Folder** | Low (Business logic scattered) | High (Between technical layers) | Poor (Folders become massive) | High (Constant context switching) |
| **Domain-per-Package** | High (Business logic centralized) | Low (Encapsulated by interfaces) | Excellent (Microservice-ready) | Low (All related files in one place) |
| **Hybrid** | Medium | Medium | Moderate | Medium |

**Conclusion on Trade-offs for Zorivest:** For a trading journal with diverse modules like Tax, Behavioral Analytics, and External Broker Integration, the **Domain-per-Package (Domain-Driven)** structure is definitively the superior choice.3 Financial applications generate complex, deeply isolated business rules. The mathematical calculations required for wash sales (Tax domain) are entirely disjointed from the heuristic logic required for trade psychology logging (Behavioral domain). Forcing these distinct functional requirements into a shared technical layer creates rigid, brittle code. The Netflix Dispatch pattern proves that encapsulating these as independent modules within a src/ directory ensures maximum scalability.3

## **3\. Aligning Domain Boundaries: GUI, MCP, and the REST API**

The Zorivest application features dual consumers: an Electron/React GUI and a TypeScript MCP server acting as an agentic interface for IDEs. A critical architectural question arises: Should the REST API's sub-files mirror the exact domain boundaries of the GUI and MCP, or should the REST API maintain its own natural grouping?

### **3.1 The Divergent Needs of UI and AI Consumers**

While the REST API serves as the shared delegation layer, the GUI and the AI agents consume data in fundamentally different ways. Attempting to force a 1:1 mapping across all three layers ignores the reality of consumer constraints.

**The GUI Consumer:**

The React frontend is designed for human interaction. It requires highly granular, fast, paginated endpoints to render specific visual components. A human user clicking through a table needs an endpoint like GET /api/v1/trades?page=2\&limit=50. The frontend architecture (06-gui.md) is correctly split into visual domains: Shell, Trades, Planning, Accounts, Settings, Tax, and Calculator. These boundaries represent physical views or pages within the application.

**The MCP Server Consumer:** The MCP Server is designed for Large Language Models (LLMs). LLMs suffer from severe context window constraints and the "N+1 problem" if forced to navigate highly granular REST APIs.14 If an AI agent needs to analyze a user's trading performance, forcing it to call GET /trades, iterate through the IDs, and then call GET /trades/{id}/analytics exhausts tokens rapidly, consumes massive compute time, and increases the likelihood of hallucination.15

Therefore, MCP tools must be **intent-based** and coarse-grained.16 The model does not want to interact with a database; it wants to execute a workflow. The MCP phases (05-mcp-server.md) are divided into semantic agentic actions: Diagnostics, Analytics, Discovery, etc.

### **3.2 The Backend-for-Frontend (BFF) vs. Shared Core Paradigm**

If the REST API attempts to mirror the GUI, the MCP server will be forced to make too many requests to gather context. If the REST API mirrors the MCP, the GUI will receive bloated, over-fetched payloads containing irrelevant analytical data.17

Therefore, **the REST API should not mirror either consumer perfectly.** Instead, the REST API must reflect the pure **Business Domains** of the application.

The optimal architectural flow, utilizing a variation of the Backend-for-Frontend (BFF) pattern, is as follows:

1. **Service Layer (Phase 3):** Contains the raw business rules, SQLCipher database queries, and calculations (e.g., TaxService.calculate\_wash\_sales()). This layer represents the absolute truth of the domain.  
2. **REST API Layer (Phase 4):** Exposes the Service Layer via HTTP. It should be organized by entity and core business process (e.g., routers/trades.py, routers/tax.py, routers/settings.py). It remains fundamentally agnostic to *who* or *what* is consuming it.  
3. **MCP Server Layer (Phase 5):** Acts as an orchestration layer specifically for the LLM. The MCP server aggregates multiple REST API endpoints into a single, LLM-friendly "Tool".16 For instance, a single MCP tool named analyze\_recent\_mistakes might internally make three REST API calls to /trades, /analytics, and /behavioral, synthesizing the response into a condensed Markdown or JSON block before returning it to the LLM. This drastically reduces token consumption.14  
4. **GUI Layer (Phase 6):** Consumes the REST API directly, utilizing the granular endpoints to populate its specific React components.

By allowing the REST API to maintain its own natural, entity-driven grouping, the architecture avoids tight coupling to any specific UI layout or AI tool definition.18 The REST API sub-files will naturally overlap heavily with the GUI (since UIs often represent data entities), but they should remain independent of the highly aggregated, action-oriented categories of the MCP server.

| Layer | Primary Consumer | Granularity | Organizational Focus | Example |
| :---- | :---- | :---- | :---- | :---- |
| **Service Layer** | Internal Backend | High (Functions) | Business Logic & DB | TaxService.py |
| **REST API Layer** | GUI & MCP Server | High (Endpoints) | Data Entities & Verbs | POST /api/v1/tax/wash-sales |
| **MCP Server** | AI Agents (LLMs) | Low (Aggregated Tools) | Intent & Workflows | analyze\_portfolio\_tax\_liability() |
| **GUI** | Human Users | High (Components) | Visual Layout | TaxDashboard.tsx |

## **4\. Deconstructing the Monolith: The Anatomy of the Hub File**

The current state of the REST API documentation is a 1,102-line monolithic file (04-rest-api.md). When transitioning to a modular, domain-driven structure, the code itself will be split into sub-files, leaving behind a central "hub" file. In FastAPI applications, this hub file translates directly to the main.py file, which utilizes the Application Factory pattern.2

### **4.1 What the Hub File Must Retain**

To ensure the application scales without bottlenecking at the entry point, the hub file must be aggressively stripped of all business logic, routing details, and schemas.1 The purpose of the hub file is to serve as the application's bootstrap and configuration nexus. Based on enterprise implementations like Tiangolo's templates and Netflix Dispatch 2, the main.py file should strictly retain the following five core responsibilities:

1. **FastAPI Application Instantiation:** The creation of the FastAPI() object, including global metadata such as the API title, version, documentation URIs (/docs, /redoc), and OpenAPI schema configurations.  
2. **Lifespan Context Managers:** FastAPI utilizes asynchronous lifespan events to handle startup and shutdown logic. The hub file should orchestrate the initialization of connection pools (e.g., establishing the SQLCipher database connections, testing the encryption key) and the graceful teardown of these resources upon exit.21  
3. **Global Middleware:** Cross-cutting concerns that apply to every request regardless of the domain must be registered here. This critically includes CORS (Cross-Origin Resource Sharing) configuration. Since the Electron GUI will be communicating with the local API server across varying local ports or protocols, permissive but secure CORS setup is required. It also includes global request ID tracking, gzip compression, or latency logging middleware.2  
4. **Global Exception Handlers:** Centralized handlers for converting custom Python exceptions (e.g., TradeNotFoundError, DecryptionKeyInvalid) into standardized HTTP JSON responses.19 This ensures that an error thrown deep in the Service layer is uniformly translated into an HTTP 404 or 403\.  
5. **Router Registration (The Switchboard):** The core function of the hub file is to import the APIRouter objects from the isolated domain packages and mount them to the main application using app.include\_router(). Prefixing and tagging are applied at this level to ensure the generated OpenAPI specification is clean and organized.

### **4.2 The Transformation of 04-rest-api.md**

Following the split, the 04-rest-api.md specification document will transform from a 1,100-line monolith into a lean architectural manifesto. It will specify the global behavior of the application.

**Proposed Structure of the Hub Specification:**

* **Step 4.1: Application Bootstrap:** Defines the FastAPI instantiation parameters.  
* **Step 4.2: Lifespan Management:** Details the precise mechanics of mounting the SQLCipher database, validating the user's master password, and initializing the Service Layer dependencies.  
* **Step 4.3: Middleware Stack:** Specifies CORS, logging ingestions (previously Step 4.4 in the monolith), and MCP guard/authentication middleware (previously Steps 4.5 and 4.6). Placing MCP guards in the hub file ensures that specific route prefixes (e.g., /api/v1/mcp/\*) are protected by a unified security layer.  
* **Step 4.4: Exception Handling:** Defines the standard JSON schema for errors returned to the GUI and MCP.  
* **Step 4.5: Router Manifest:** A simple index defining exactly which sub-files handle which prefixes (e.g., mapping 04a-rest-api-trades.md to /api/v1/trades).

By restricting the hub file to these responsibilities, the architecture adheres strictly to the Open-Closed Principle. When a new domain (e.g., "Brokers") is added, the only modification required in the hub file is a single include\_router statement.2

## **5\. Specification Granularity: Structuring the Build Plan Documentation**

In the context of the build plan documentation, the objective is to split 04-rest-api.md into highly functional sub-files. Because these are specification documents meant to be parsed by both human engineers and AI coding agents (such as Cursor or Claude), the granularity and semantic grouping of the text are critical to project success.

### **5.1 The Danger of Over-Splitting and Context Fragmentation**

A common anti-pattern in technical documentation is mimicking the exact file structure of the layered code. It might be tempting to create separate documentation files for 04a-schemas.md, 04b-routers.md, and 04c-tests.md. This approach is actively detrimental.22

When an AI coding agent is tasked with building or refactoring a specific endpoint, it requires complete systemic context: the expected request payload (schema), the URL path (router), the underlying logic (service call), and the success criteria (tests). If this information is scattered across different markdown files, the agent's context window becomes fragmented. Advanced retrieval-augmented generation (RAG) and embedding models rely on semantic proximity; splitting related technical specifications across files leads to hallucinations, misaligned data types, and broken implementations.22 The AI loses the "plot" of the feature.

### **5.2 The Domain-Centric Specification Model (Vertical Slices)**

The optimal granularity for the sub-files is **Domain-Centric and Self-Contained**.22 The REST API documentation should be split according to the business domains identified earlier, effectively creating "vertical slices" of the application's requirements.

The monolithic file should be partitioned as follows:

* 04-rest-api.md (Hub: Global config, middleware, router manifest, auth)  
* 04a-rest-api-trades.md (Trade CRUD, trade reports, trade plans, and global image routes)  
* 04b-rest-api-tax.md (Simulate, estimate, wash sales, lots, quarterly, harvest, YTD)  
* 04c-rest-api-settings.md (Settings CRUD, user preferences)  
* 04d-rest-api-expansion.md (Brokers, analytics, round-trips, banking, import workflows)

### **5.3 Internal Structure of a Specification Sub-File**

Within each of these domain specification files, the documentation must provide a complete, unbroken narrative of the API requirements. For example, 04b-rest-api-tax.md should contain:

1. **Domain Overview:** A brief summary of the domain's responsibility within Zorivest.  
2. **Pydantic Data Contracts:** The specific request and response validation models (e.g., WashSaleRequest, TaxEstimateResponse). Keeping the schema specification physically adjacent to the route specification ensures absolute data contract fidelity.3  
3. **Route Specifications:** The HTTP methods, paths, and strict logic delegations (e.g., POST /api/v1/tax/wash-sales \-\> delegates to TaxService.calculate). This must explicitly define the interaction with Phase 3 (Service Layer).  
4. **Acceptance Criteria & Test Patterns:** The expected behavior for unit and integration testing. Rather than maintaining a separate master test plan file, embedding the test scenarios directly beneath the route specification guarantees that the developer (or AI) immediately understands the edge cases while writing the code (e.g., "Test: Verify HTTP 400 is returned if the date format is invalid; verify Service Layer exception is caught").6

This vertical-slice approach guarantees that when a developer or agent focuses on building the Tax API, they open a single, cohesive document containing 100% of the context required to execute the task flawlessly from input validation to test assertion.

## **6\. Architectural Anti-Patterns for Dual-Consumer REST APIs**

Designing a shared REST API backend that delegates to a service layer while simultaneously serving a highly interactive local GUI and an AI-driven MCP server introduces unique engineering challenges. Identifying and avoiding common architectural anti-patterns is essential for maintaining performance, security, and scalability.

### **6.1 Anti-Pattern 1: The "API Wrapper" Trap for MCP**

The most prevalent mistake when integrating the Model Context Protocol is treating the MCP server as a thin, automated wrapper over the existing REST API.15 If the Zorivest REST API features 40 granular endpoints (e.g., Get User, Get Trades, Update Trade Tags), exposing all 40 directly to the LLM via MCP is an architectural disaster.

**The Risk:** Every tool exposed via MCP requires a JSON schema definition. Injecting 40 verbose schemas into the LLM's system prompt consumes thousands of tokens before any actual reasoning or conversation occurs.14 Furthermore, if the LLM needs to synthesize data to answer a complex query (e.g., "Why did I lose money last week?"), it will fall into a catastrophic "N+1" request loop. The agent will make dozens of sequential REST API calls, exhausting context limits, triggering rate limits, and introducing severe latency.15

**The Solution:** The shared REST API should provide the granular endpoints for the GUI, but the MCP Server (Phase 5\) must aggregate them. The MCP server should expose a smaller number of coarse-grained, intent-based tools. Instead of exposing GET /trades and GET /tax to the agent, the MCP server exposes a single tool: get\_comprehensive\_portfolio\_status. Internally, the MCP server queries the REST API (or directly accesses the Service Layer) to gather the fragmented data, synthesizes it, and returns a single, highly dense context payload to the LLM.16 This protects the agent's context window and speeds up execution.

### **6.2 Anti-Pattern 2: "Fat Routers" (Business Logic Leakage)**

Because FastAPI is incredibly fast to write and encourages rapid prototyping, developers frequently place business logic directly inside the @router.get() or @router.post() function decorators.27

**The Risk:** If the complex heuristic logic for determining a wash sale exists inside the 04-rest-api router code, it becomes inextricably coupled to the HTTP request lifecycle. The MCP server cannot access that mathematical logic without making a full HTTP round-trip, or worse, duplicating the logic inside the MCP layer. This violates the DRY (Don't Repeat Yourself) principle and shatters the integrity of the Service Layer.

**The Solution:** Strict enforcement of the Service Layer (Phase 3). The REST API routers must act as "dumb pipes." They are authorized to do exactly three things:

1. Accept the HTTP request and validate it via Pydantic.  
2. Pass the validated data directly to the appropriate Service class (e.g., await TaxService.calculate\_wash\_sale(request.data)).  
3. Return the Service class's output formatted as a standard HTTP response. By keeping routers "thin," both the MCP server and the GUI can securely rely on the underlying, centralized business logic without redundancy.19

### **6.3 Anti-Pattern 3: Synchronous Blocking in Async Routes**

FastAPI is built on Starlette and leverages Python's asynchronous event loop (asyncio) to achieve its high throughput.29 A severe anti-pattern in data-heavy financial applications is defining a route as async def but executing synchronous, CPU-bound, or blocking I/O operations within that route.3

**The Risk:** Executing a blocking operation (such as heavy mathematical portfolio calculations over thousands of rows, or using a synchronous database driver) inside an async def function halts the entire ASGI event loop. Because it is a single-threaded loop, if the GUI requests a heavy tax calculation, and the LLM via the MCP server simultaneously requests a simple trade history update, the entire backend will hang until the synchronous tax calculation completes.3 This results in UI freezing and agent timeouts.

**The Solution:** Developers must actively choose between def and async def. Use standard def for synchronous, computationally heavy endpoints. FastAPI is intelligent enough to automatically run standard def routes in an external thread pool, preventing them from blocking the main asynchronous event loop.3 Reserve async def strictly for non-blocking I/O operations, such as async database queries (via asyncpg or an async wrapper for SQLCipher) and async HTTP requests to external broker APIs.

### **6.4 Anti-Pattern 4: Session State within the API Response**

In conversational AI contexts mediated by MCP, developers sometimes attempt to maintain the session state by encoding the state context into the structured content of the REST API response. They then force the client (the MCP server or GUI) to pass that entire state object back in the payload of the subsequent request.18

**The Risk:** This creates bloated, highly inefficient payloads and establishes a brittle, tightly coupled relationship between the API and the consumer.18 If an agent is executing a multi-step trade planning wizard, passing the entire history of the wizard back and forth rapidly consumes token bandwidth and violates the fundamental statelessness principle of RESTful design.

**The Solution:** The REST API must remain entirely stateless. If conversational context or multi-step transaction states are required, they should be persisted in the local SQLCipher database via the Service layer. The API simply receives a lightweight identifier (like a trade\_plan\_session\_id) and fetches the necessary state from the database. This keeps the network layer thin and places the burden of state management securely within the backend's control.

## **Conclusion**

The architecture of the Zorivest desktop trading journal demands a structural approach that balances the rigorous, granular, and visually driven demands of a React GUI with the context-sensitive, token-optimized, and intent-driven requirements of an MCP agent.

This analysis dictates that the REST API must abandon the monolithic 04-rest-api.md file in favor of a **Domain-Driven organizational structure**. This functional grouping aligns the codebase with pure business capabilities (Trades, Tax, Settings), drastically reducing internal coupling and increasing navigational clarity for future development. The main.py hub file will act purely as an application factory and router switchboard, completely devoid of business logic.

Furthermore, the documentation strategy must mirror this functional encapsulation. Creating domain-specific specification sub-files—where the routes, Pydantic schemas, and test acceptance criteria are co-located in vertical slices—will significantly enhance the parsing efficiency of both human engineers and AI coding assistants.

Finally, by strictly maintaining a thin REST API layer that delegates all intelligence to a robust Service Layer, the architecture effectively avoids the fatal "API Wrapper Trap." This ensures that the GUI receives the precise, paginated endpoints it requires for rendering, while the MCP server is free to construct the aggregated, intent-based tools necessary for seamless LLM execution.

#### **Works cited**

1. Python Backend Project Advanced Setup (FastAPI Example) | by Dmytro Parfeniuk | Python in Plain English, accessed February 27, 2026, [https://python.plainenglish.io/python-backend-project-advanced-setup-fastapi-example-7b7e73a52aec](https://python.plainenglish.io/python-backend-project-advanced-setup-fastapi-example-7b7e73a52aec)  
2. Bigger Applications \- Multiple Files \- FastAPI, accessed February 27, 2026, [https://fastapi.tiangolo.com/tutorial/bigger-applications/](https://fastapi.tiangolo.com/tutorial/bigger-applications/)  
3. zhanymkanov/fastapi-best-practices: FastAPI Best Practices ... \- GitHub, accessed February 27, 2026, [https://github.com/zhanymkanov/fastapi-best-practices\#project-structure](https://github.com/zhanymkanov/fastapi-best-practices#project-structure)  
4. FastAPI framework, high performance, easy to learn, fast to code, ready for production \- GitHub, accessed February 27, 2026, [https://github.com/fastapi/fastapi](https://github.com/fastapi/fastapi)  
5. Looking for project's best practices : r/FastAPI \- Reddit, accessed February 27, 2026, [https://www.reddit.com/r/FastAPI/comments/1g5zl81/looking\_for\_projects\_best\_practices/](https://www.reddit.com/r/FastAPI/comments/1g5zl81/looking_for_projects_best_practices/)  
6. Modular or Flat? Struggling with FastAPI Project Structure – Need Advice \- Reddit, accessed February 27, 2026, [https://www.reddit.com/r/ExperiencedDevs/comments/1ly4kj5/modular\_or\_flat\_struggling\_with\_fastapi\_project/](https://www.reddit.com/r/ExperiencedDevs/comments/1ly4kj5/modular_or_flat_struggling_with_fastapi_project/)  
7. CLI to create Fastapi projects easily. \- GitHub, accessed February 27, 2026, [https://github.com/allient/create-fastapi-project](https://github.com/allient/create-fastapi-project)  
8. Project Structures: Domain-Driven vs. Layered Architecture. | by Hector | Medium, accessed February 27, 2026, [https://hector-reyesaleman.medium.com/project-structures-domain-driven-vs-layered-architecture-db8b713c99ef](https://hector-reyesaleman.medium.com/project-structures-domain-driven-vs-layered-architecture-db8b713c99ef)  
9. Exploring the architecture behind the OpenBB Platform, accessed February 27, 2026, [https://openbb.co/blog/exploring-the-architecture-behind-the-openbb-platform](https://openbb.co/blog/exploring-the-architecture-behind-the-openbb-platform)  
10. Open-Agent-Tools/open-paper-trading-mcp: Open Paper ... \- GitHub, accessed February 27, 2026, [https://github.com/Open-Agent-Tools/open-paper-trading-mcp](https://github.com/Open-Agent-Tools/open-paper-trading-mcp)  
11. qu3vipon/python-ddd: Python Domain-Driven-Design(DDD) Example \- GitHub, accessed February 27, 2026, [https://github.com/qu3vipon/python-ddd](https://github.com/qu3vipon/python-ddd)  
12. FastAPI \+ DDD: The Combo for Modern Python Backends \- ELEKS, accessed February 27, 2026, [https://eleks.com/expert-opinion/fastapi-ddd-for-python-backends/](https://eleks.com/expert-opinion/fastapi-ddd-for-python-backends/)  
13. Layered Architecture & Dependency Injection: A Recipe for Clean and Testable FastAPI Code \- Dev.to, accessed February 27, 2026, [https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo)  
14. Scaling Agents with Code Execution and the Model Context Protocol, accessed February 27, 2026, [https://medium.com/@madhur.prashant7/scaling-agents-with-code-execution-and-the-model-context-protocol-a4c263fa7f61](https://medium.com/@madhur.prashant7/scaling-agents-with-code-execution-and-the-model-context-protocol-a4c263fa7f61)  
15. Beyond API Wrappers: Architecting MCP Servers for Production Agentic AI Systems | by Aditya \- Ardent Optimist , Yogi, Technologist | Medium, accessed February 27, 2026, [https://medium.com/@aditya\_mehra/beyond-api-wrappers-architecting-mcp-servers-for-production-agentic-ai-systems-cf93804be22a](https://medium.com/@aditya_mehra/beyond-api-wrappers-architecting-mcp-servers-for-production-agentic-ai-systems-cf93804be22a)  
16. Good MCP design is understanding that every tool response is an opportunity to prompt the model \- Reddit, accessed February 27, 2026, [https://www.reddit.com/r/mcp/comments/1lq69b3/good\_mcp\_design\_is\_understanding\_that\_every\_tool/](https://www.reddit.com/r/mcp/comments/1lq69b3/good_mcp_design_is_understanding_that_every_tool/)  
17. The Pros and Cons of Using a Backend-for-Frontend (BFF) | by Giovanni Hislop \- Medium, accessed February 27, 2026, [https://medium.com/@g.m.hislop93/the-pros-and-cons-of-using-a-backend-for-frontend-bff-a67e2edaefab](https://medium.com/@g.m.hislop93/the-pros-and-cons-of-using-a-backend-for-frontend-bff-a67e2edaefab)  
18. MCP Server Architecture: State Management, Security & Tool Orchestration \- Zeo, accessed February 27, 2026, [https://zeo.org/resources/blog/mcp-server-architecture-state-management-security-tool-orchestration](https://zeo.org/resources/blog/mcp-server-architecture-state-management-security-tool-orchestration)  
19. Best Practices in FastAPI Architecture \- Zyneto, accessed February 27, 2026, [https://zyneto.com/blog/best-practices-in-fastapi-architecture](https://zyneto.com/blog/best-practices-in-fastapi-architecture)  
20. FastAPI Setup Guide for 2025: Requirements, Structure & Deployment \- DEV Community, accessed February 27, 2026, [https://dev.to/zestminds\_technologies\_c1/fastapi-setup-guide-for-2025-requirements-structure-deployment-1gd](https://dev.to/zestminds_technologies_c1/fastapi-setup-guide-for-2025-requirements-structure-deployment-1gd)  
21. FastAPI Best Practices: A Complete Guide for Building Production-Ready APIs \- Medium, accessed February 27, 2026, [https://medium.com/@abipoongodi1211/fastapi-best-practices-a-complete-guide-for-building-production-ready-apis-bb27062d7617](https://medium.com/@abipoongodi1211/fastapi-best-practices-a-complete-guide-for-building-production-ready-apis-bb27062d7617)  
22. RAG Chunking Strategies: Complete Guide to Document Splitting for Better Retrieval, accessed February 27, 2026, [https://latenode.com/blog/ai-frameworks-technical-infrastructure/rag-retrieval-augmented-generation/rag-chunking-strategies-complete-guide-to-document-splitting-for-better-retrieval](https://latenode.com/blog/ai-frameworks-technical-infrastructure/rag-retrieval-augmented-generation/rag-chunking-strategies-complete-guide-to-document-splitting-for-better-retrieval)  
23. Should you split that file? | Path-Sensitive, accessed February 27, 2026, [https://www.pathsensitive.com/2023/12/should-you-split-that-file.html](https://www.pathsensitive.com/2023/12/should-you-split-that-file.html)  
24. Mastering Chunking Strategies for RAG: Best Practices & Code Examples \- Databricks Community, accessed February 27, 2026, [https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089](https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089)  
25. Is it a good practice to mirror the folder structure of the Application, Infrastructure, Presentation, and Domain layers within the test project? What are the pros and cons of following this approach? : r/dotnet \- Reddit, accessed February 27, 2026, [https://www.reddit.com/r/dotnet/comments/1l0in3j/is\_it\_a\_good\_practice\_to\_mirror\_the\_folder/](https://www.reddit.com/r/dotnet/comments/1l0in3j/is_it_a_good_practice_to_mirror_the_folder/)  
26. Best Practices \- FastAPI MCP \- Tadata, accessed February 27, 2026, [https://fastapi-mcp.tadata.com/getting-started/best-practices](https://fastapi-mcp.tadata.com/getting-started/best-practices)  
27. Building a Production-Grade FastAPI Backend with Clean Layered Architecture, accessed February 27, 2026, [https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)  
28. Architecting Scalable FastAPI Systems for Large Language Model (LLM) Applications and External Integrations | by Ali moradi | Medium, accessed February 27, 2026, [https://medium.com/@moradikor296/architecting-scalable-fastapi-systems-for-large-language-model-llm-applications-and-external-cf72f76ad849](https://medium.com/@moradikor296/architecting-scalable-fastapi-systems-for-large-language-model-llm-applications-and-external-cf72f76ad849)  
29. Ultimate guide to FastAPI library in Python \- Deepnote, accessed February 27, 2026, [https://deepnote.com/blog/ultimate-guide-to-fastapi-library-in-python](https://deepnote.com/blog/ultimate-guide-to-fastapi-library-in-python)  
30. Common FastAPI Anti-Patterns: What to Avoid for Production-Ready APIs | by Mahdi Jafari, accessed February 27, 2026, [https://python.plainenglish.io/common-fastapi-anti-patterns-what-to-avoid-for-production-ready-apis-651066b6aab1](https://python.plainenglish.io/common-fastapi-anti-patterns-what-to-avoid-for-production-ready-apis-651066b6aab1)