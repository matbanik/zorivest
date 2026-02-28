# Splitting a FastAPI monolith into domain-aligned sub-files

**Organize around your own resource/domain model — not around either consumer's grouping.** Every major API design authority (Google, Microsoft, Zalando) and every production FastAPI codebase converges on this principle. For Zorivest, this means the REST API's file structure should mirror the trading journal's domain entities (trades, playbooks, analysis, tags, accounts), letting both the MCP server's 10 tool categories and the GUI's 8 modules adapt to the API rather than the reverse. FastAPI's `tags` parameter then lets you create consumer-friendly Swagger groupings that differ entirely from file organization. The five tensions below each resolve clearly once this resource-oriented foundation is in place.

---

## 1. Let the domain model own the boundaries

The three canonical API design guidelines — Google's AIP-121, Microsoft's REST best practices, and Zalando's RESTful API guidelines — all mandate resource-oriented design. Google states: *"Resource-oriented APIs emphasize resources (data model) over the methods performed on those resources."* Zalando goes further: *"API resources represent elements of the application's domain model. Using domain-specific nomenclature for resource names helps developers understand the functionality."*

Every major FastAPI project follows this in practice. Tiangolo's full-stack template splits routers by entity (`login.py`, `users.py`, `items.py`). Mealie uses domain subdirectories (`routes/recipe/`, `routes/auth/`, `routes/households/`). Polar organizes under `api/v1/` with one file per resource. The Netflix Dispatch–inspired best-practices repo (16.5k GitHub stars) goes furthest: each domain gets a full package with `router.py`, `schemas.py`, `models.py`, `service.py`, and `dependencies.py`.

**Recommended approach:** Define Zorivest's sub-files around your resource model — likely `trades/`, `playbooks/`, `analysis/`, `tags/`, `journal_entries/`, and so on. Each consumer then maps its own groupings to these stable domain endpoints. The MCP server's "trade-analysis" tool category might call endpoints from both `trades/` and `analysis/`; that's expected and correct.

**Strongest counter-argument:** If one consumer accounts for 90%+ of traffic and the other is a thin wrapper, aligning with the dominant consumer reduces impedance mismatch. But Zorivest has two roughly co-equal consumers, so this doesn't apply.

**Spec vs. code context:** In a specification document, you can additionally provide a consumer-oriented "mapping appendix" that shows which MCP tool categories and GUI modules call which domain endpoints. This navigation aid has no analog in code.

---

## 2. Auth gets its own domain; operational routes get one small file

Cross-cutting infrastructure routes fall into two distinct categories that should not be mixed. **Auth routes** (unlock, lock, API keys, session management) have enough complexity and distinct security concerns to warrant their own domain package. Every surveyed project treats auth this way: FastAPI-users splits auth into five separate router factories (`auth.py`, `register.py`, `reset.py`, `verify.py`, `users.py`); Mealie puts auth in `routes/auth/auth.py`; the best-practices repo treats `auth/` as a first-class domain package.

**Operational routes** (health/readiness, version/diagnostics, circuit breaker status, frontend log ingestion, service shutdown) are a different story. These are typically **2–6 tiny endpoints** that rarely change. The pattern across real projects is pragmatic: Tiangolo's template puts no explicit health check anywhere (relying on `/docs` as a liveness signal); most production apps add a small `routers/system.py` or register these directly on `main.py`.

**Recommended approach for Zorivest:**

| Category | Location | Rationale |
|---|---|---|
| Auth/unlock/lock/API keys | `auth/router.py` (own domain package) | Complex enough for own module; distinct security surface |
| Circuit breaker / MCP guard | `system/router.py` | Operational, not business domain |
| Frontend log ingestion | `system/router.py` | Infrastructure concern |
| Version / diagnostics | `system/router.py` | Tiny; groups naturally with other ops endpoints |
| Service status / shutdown | `system/router.py` | Lifecycle management |

**Strongest counter-argument:** You could argue the MCP guard belongs with auth since it's access-control adjacent. But the MCP guard is a consumer-specific circuit breaker, not an identity/credential concern — keeping it in `system/` maintains cleaner separation.

**Spec vs. code:** In a spec document, the `system` sub-file doubles as operational documentation. Consider adding a brief "operational runbook" section here describing expected health check behavior, shutdown sequences, and circuit breaker states — something you'd never put in a Python router file.

---

## 3. Domain-scoped schema files are the scalable answer

Three options exist for Pydantic schema placement, and the community has converged on one. **Option A** (schemas inline with routes) appears only in tutorials and single-file demos. **Option B** (centralized `schemas/` directory) is what FastAPI's official tutorial shows and works for small projects. **Option C** (domain-scoped schema files — `trades/schemas.py` alongside `trades/router.py`) is the dominant recommendation for production applications with multiple domains.

The reasoning is cohesion. When you modify a trade endpoint's request shape, you want `trades/schemas.py` right next to `trades/router.py`, not buried in a shared directory alongside unrelated schemas. The Netflix Dispatch pattern, adopted by the fastapi-best-practices repo, codifies this: each domain package self-contains its router, schemas, models, service, dependencies, and exceptions.

For **shared schemas** (pagination wrappers, standard error responses, common envelopes), place these in a top-level `common/schemas.py` or `schemas.py`. Cross-domain imports use explicit module paths: `from src.auth import schemas as auth_schemas`.

**Recommended structure for Zorivest:**
```
src/
├── trades/
│   ├── router.py          # Trade CRUD endpoints
│   ├── schemas.py         # TradeCreate, TradeResponse, TradeFilter
│   └── service.py         # Already exists in service layer
├── playbooks/
│   ├── router.py
│   ├── schemas.py         # PlaybookCreate, PlaybookResponse
│   └── service.py
├── auth/
│   ├── router.py
│   └── schemas.py         # UnlockRequest, TokenResponse
├── system/
│   ├── router.py
│   └── schemas.py         # HealthResponse, VersionInfo
├── common/
│   └── schemas.py         # PaginatedResponse, ErrorEnvelope, etc.
└── main.py
```

**Strongest counter-argument:** Tiangolo's own template uses a single `models.py` for everything (leveraging SQLModel's dual-purpose classes). This works at the template's scale (~4 entities) but breaks down with **10+ domain concepts** and two consumers requiring different response shapes for the same data.

**Spec vs. code:** In specification documents, co-locating schema definitions with route definitions in the same sub-file is even more clearly correct — the reader examining a route spec immediately sees the contract. No import mechanism exists in markdown, so "shared schemas" should be defined once in a conventions section and referenced by name.

---

## 4. Spec documents should co-locate tests; code should not

This is the tension where spec and code contexts diverge most sharply.

**For build-plan specification documents**, the Specification by Example methodology (Gojko Adzic) explicitly advocates merging requirements and test cases into a single artifact. Kent C. Dodds' co-location principle reinforces this: *"Things that change together should be located as close as reasonable."* When a route definition changes in your spec, the person updating it should immediately see what tests verify it. There's no build system, no import resolution, no CI pipeline — the only concern is **readability and sync**. Separating route specs from test specs in a documentation context creates exactly the synchronization problem that Specification by Example was invented to prevent.

However, **cross-domain integration tests** don't belong to any single route sub-file. These scenarios ("create a trade, then run analysis, then verify the playbook linkage") span boundaries and need their own home.

**Recommended spec document structure:**
Each domain sub-file contains route definitions followed immediately by E2E test cases for those routes. A hub document contains: (1) the table of contents / navigation map, (2) cross-domain integration test scenarios, (3) shared test data definitions and conventions, and (4) the consumer-mapping appendix showing how MCP tools and GUI modules map to domain endpoints.

**For actual code** (when implementation begins), Python's pytest ecosystem has a clear convention: a separate `tests/` directory at the project root, mirroring the source structure. Tiangolo's template uses `tests/api/test_users.py` mirroring `api/routes/users.py`. Mealie splits further into `unit_tests/` and `integration_tests/`. The best-practices repo mirrors domain packages directly (`tests/auth/`, `tests/posts/`).

**Strongest counter-argument for separating tests in specs:** Long spec files become hard to navigate. But this is solved by clear section headers and a table of contents, not by splitting tests into a separate document where they'll inevitably drift out of sync with the routes they verify.

---

## 5. Thin layers benefit *more* from splitting, not less

This is the most counterintuitive finding. The "thin controller" pattern — where routes do only validation, delegation, and error mapping — is an **intentional architectural choice** endorsed by Clean Architecture, the layered architecture literature, and every surveyed FastAPI codebase. The thinness is a feature. And thin files are actually *easier* to split because each one is trivially maintainable.

The practical benefits of splitting remain fully intact regardless of per-file line count. **Navigability** improves: "where are the trade endpoints?" has an instant answer when `trades/router.py` exists. **Merge conflicts** drop: two developers working on trades and playbooks never touch the same file. **OpenAPI documentation** gets automatic structure from FastAPI's router tags and prefixes. **Testing** gains natural correspondence: `tests/trades/` maps to `trades/router.py`. **Ownership boundaries** become explicit for parallel development.

Community consensus on thresholds: fewer than **5 total endpoints** → one file is fine; **5–15 endpoints across 2–3 domains** → splitting is recommended; **15+ endpoints across 4+ domains** → splitting is clearly necessary. A trading journal with trades, playbooks, analysis, tags, accounts, and journal entries almost certainly exceeds 15 endpoints across 5+ domains.

**Strongest counter-argument:** If each router file contains only 2–3 endpoints of 5–6 lines each, the file-navigation overhead (opening multiple files) exceeds the organizational benefit. But this argument assumes single-developer, single-consumer context. With two consumers and parallel development, even tiny files justify their existence through **boundary clarity**.

**A key reframe for spec documents:** In a build specification, each sub-file isn't just a thin list of route signatures — it includes request/response schemas, error shapes, status code semantics, E2E test cases, and design rationale. **Spec sub-files for thin API layers are not thin documents.** A "thin" route like `POST /trades` might have 5 lines of Python but 80+ lines of specification covering the schema, validation rules, error cases, and test scenarios. The splitting question barely applies in spec context because the files will have substantial content regardless of the delegation layer's thinness.

---

## Conclusion: a decision matrix for Zorivest

Three structural decisions lock in the architecture. First, **domain-scoped packages** (trades, playbooks, analysis, tags, auth, system) with co-located router + schemas per domain. Second, **auth separated from operational routes** — auth is a domain, system ops are infrastructure. Third, **spec documents co-locate tests with routes** while code separates them into a mirrored `tests/` directory.

The deeper insight across all five tensions is that **the REST API layer should define its own identity** independent of both consumers. The MCP server and Electron GUI are adapters that translate between their UX paradigms and the API's resource model. Tying the API's internal structure to either consumer creates coupling that will generate friction every time a consumer refactors. Domain alignment gives you a stable spine that both consumers can depend on and that survives UI redesigns, MCP tool reorganizations, and the eventual addition of a third consumer you haven't imagined yet.