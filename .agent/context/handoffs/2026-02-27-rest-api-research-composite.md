# REST API Layer Research — Composite Analysis & Zorivest Application

> Cross-model synthesis from Gemini Deep Research, Claude Extended Thinking, and ChatGPT o3 Deep Research.
> Source files: `_inspiration/fastapi_research/`

---

## 1. Where All Three Models Agree (High-Confidence Consensus)

These findings appeared independently in all three reports — strongest signal.

### 1A. Domain-per-package is the right pattern for Zorivest

| Model | Verdict | Key Evidence |
|-------|---------|-------------|
| **Gemini** | "Definitively the superior choice" for trading apps | Netflix Dispatch, OpenBB hierarchical routers |
| **Claude** | "Resource-oriented foundation" — Google AIP, Zalando, Microsoft guidelines all mandate it | Mealie, Polar, fastapi-best-practices (16.5k ⭐) |
| **ChatGPT** | "Option C or D" as the code organization axis | Prefect (23 routers), Dispatch (52 router inclusions), Freqtrade (12 routers) |

**Zorivest implication:** The REST API sub-files should be organized around **Zorivest's own business domains** — not mirroring MCP categories or GUI modules.

### 1B. The REST API must NOT mirror either consumer

All three models independently arrived at the same conclusion:

- **Gemini:** "The REST API should not mirror either consumer perfectly... it must reflect the pure Business Domains"
- **Claude:** "The REST API layer should define its own identity independent of both consumers. The MCP server and Electron GUI are adapters."
- **ChatGPT:** "Organize routes by domain/resource first (stable, shared contract). Add consumer-specific slices sparingly."

**Why this matters for Zorivest:** The MCP server already acts as a BFF-like adapter (it aggregates REST calls into coarse-grained tools). The GUI is a direct consumer. The REST API sits in the middle as the **stable contract** both depend on.

### 1C. Hub file = thin composition root only

All three models agree the hub file should contain exactly these responsibilities:

1. **FastAPI app factory** (instantiation, metadata, OpenAPI config)
2. **Lifespan management** (DB init, shutdown)
3. **Global middleware** (CORS, error handlers, request logging)
4. **Router registration table** (the `include_router()` switchboard)
5. **Cross-domain integration tests** (Claude) / **consumer mapping appendix** (Claude)

**What moves OUT of the hub:** All routes, all Pydantic schemas, all per-domain tests. Only the wiring remains.

### 1D. Auth deserves its own domain package

Every real project surveyed treats auth as a first-class domain:

- Dispatch: `auth/views.py`, `auth/service.py`, `auth/permissions.py`
- FastAPI-users: 5 separate auth router factories
- Mealie: `routes/auth/auth.py`
- Freqtrade: dedicated `api_auth.py`

**Zorivest implication:** `04c-api-auth.md` gets its own sub-file. The envelope encryption, API key management, and unlock/lock flow are complex enough to justify dedicated ownership.

### 1E. Operational/infra routes get one small "system" file

Health, version, diagnostics, logging ingestion, service status, and graceful shutdown — all three models agree these are tiny, rarely-changing endpoints that belong in a single `system/router.py`:

- Freqtrade: dedicated `api_webserver.py` for ops
- Prefect: health endpoint on the API router
- Claude's explicit table separating auth from system routes

---

## 2. Where Models Disagree or Add Unique Insight

### 2A. Schema placement strategy

| Model | Recommendation | Nuance |
|-------|---------------|--------|
| **Gemini** | Co-located in domain packages | Self-contained, Netflix Dispatch model |
| **Claude** | Domain-scoped `schemas.py` per domain + shared `common/schemas.py` for pagination/errors | Most detailed — explicit import strategy |
| **ChatGPT** | Acknowledges both patterns exist in production | Prefect uses shared schema package; Dispatch co-locates |

**Resolution for Zorivest:** Claude's approach is the most pragmatic. For the **spec documents**, schemas go inline with routes (the reader needs the full contract in one place). For **code**, each domain gets `schemas.py` alongside `router.py`, with a `common/schemas.py` for shared types (PaginatedResponse, ErrorEnvelope, standard envelopes).

### 2B. Where MCP guard routes live

| Model | Recommendation | Reasoning |
|-------|---------------|-----------|
| **Gemini** | In the hub's middleware stack | MCP guard is cross-cutting auth middleware |
| **Claude** | In `system/router.py` | "Consumer-specific circuit breaker, not identity concern" |
| **ChatGPT** | Only introduce `/mcp/*` in FastAPI if performance/security justifies it | Keep agent-specific concerns in the MCP layer |

**Resolution for Zorivest:** Claude's placement is best. The MCP guard has its own REST routes (`/api/v1/mcp-guard/*`) that are consumed by the MCP middleware and displayed in the GUI settings page. It's an operational infrastructure concern → `system` file, alongside version/health/logging.

### 2C. How granular should the domain splits be?

| Model | Number of sub-files suggested |
|-------|-------------------------------|
| **Gemini** | 4 + hub (trades, tax, settings, expansion) — most conservative |
| **Claude** | 6 + hub (trades, playbooks, analysis, tags, auth, system) — entity-oriented |
| **ChatGPT** | 7 + hub (Option D — trades, settings, auth, analytics, accounts, tax, infra) — closest to our Phase 5/6 |

**Resolution for Zorivest:** Gemini's 4-file split is too coarse — the "expansion" bucket becomes a dumping ground (the same anti-pattern Dispatch avoids by having finely sliced packages). ChatGPT's Option D is closest to what makes sense. The question is where Claude's unique suggestions (playbooks, tags, analysis as separate domains) fit in Zorivest's actual domain model.

---

## 3. Unique Insights Per Model

### From Gemini (things the others missed)

- **OpenBB architecture**: Shows how financial platforms handle 100+ endpoints with hierarchical router nesting and a TET pipeline
- **open-paper-trading-mcp**: The *only* real-world project found that implements dual-interface (REST + MCP) with shared service layer — exactly Zorivest's architecture
- **AI context window consideration**: Monolithic spec files "exceed optimal context windows for AI-assisted coding agents, leading to hallucinations." Vertical slices prevent this.
- **Async/sync anti-pattern**: Critical for trading apps — heavy tax calculations must use `def` (not `async def`) to avoid blocking the event loop when GUI and MCP call simultaneously
- **Stateless REST for MCP**: Don't encode session state in REST responses for multi-step MCP workflows — use DB-persisted session IDs

### From Claude (things the others missed)

- **"Thin layers benefit MORE from splitting, not less"**: Counterintuitive but correct — the spec documents for a thin API layer are NOT thin because they include schemas, validation rules, error cases, and test scenarios (80+ lines per "thin" route)
- **Consumer mapping appendix**: A documentation-only concept — add a section showing which MCP tools and GUI modules call which domain endpoints. No code analog, purely navigational.
- **Specification by Example methodology**: Spec files should co-locate tests with routes (Gojko Adzic); code should separate tests into `tests/` (pytest convention). **Different answers for spec vs code**.
- **Community threshold**: <5 endpoints → one file; 5–15 → split recommended; 15+ → split clearly necessary. Zorivest has 40+ endpoints across 13+ groups → splitting is mandatory.

### From ChatGPT (things the others missed)

- **Prefect's 23 routers**: The strongest "shared backend for multiple consumers" evidence — Prefect serves Python SDK + Dashboard + background services, organized by resource
- **Dispatch's 52 router inclusions**: Enterprise scale proof that domain-per-package works at significant complexity
- **Freqtrade's mode-gating pattern**: `is_trading_mode` / `is_webserver_mode` dependencies gate which routes are active — potentially useful for Zorivest if certain routes should only be available when the DB is unlocked
- **Contract-first option**: If Zorivest later generates SDKs from OpenAPI, aligning spec-doc splits with OpenAPI tags early prevents rework
- **Sam Newman's BFF warning**: "One big API customized for all clients" becomes messy — reorganizing around one consumer reintroduces that mess

---

## 4. Proposed Zorivest Split — Synthesis of All Three Models

Based on the convergence across all three research reports, here's the recommended split that applies their findings to Zorivest's actual domain model:

### Hub File: `04-rest-api.md`

**Content (lean — ~150 lines):**
- Goal statement + architectural principles (thin delegation layer)
- FastAPI app factory specification
- Lifespan management (SQLCipher init, shutdown)
- Global middleware stack (CORS, error handlers, request ID tracking)
- Router registration table (the switchboard)
- Cross-domain integration test scenarios
- Consumer mapping appendix (which MCP tools + GUI modules call which API endpoints)
- Shared schemas reference (PaginatedResponse, ErrorEnvelope)
- Exit criteria (aggregated from sub-files)

### Sub-Files

| File | Domain | Current Steps | Routes | Aligns With |
|------|--------|---------------|--------|-------------|
| `04a-api-trades.md` | Trade lifecycle | 4.1, 4.1b, 4.1c, 4.8§16 | Trade CRUD, trade reports, trade plans, images (trade-scoped), journal linking, round-trips | 05c, 05d, 06b, 06c |
| `04b-api-accounts.md` | Account & data ingest | 4.8§1,§2,§18,§19,§24,§25,§26 | Brokers, banking, import CSV/PDF, identifiers, positions | 05f, 06d |
| `04c-api-auth.md` | Security & identity | 4.5 | Unlock/lock, API key CRUD, session management, `/status` | 05-mcp (bootstrap) |
| `04d-api-settings.md` | Configuration | 4.3 | Settings CRUD, validation, resolved settings | 05a, 06f |
| `04e-api-analytics.md` | Quantitative analysis | 4.8§10-§15,§21,§22 | Expectancy, drawdown, SQN, execution quality, PFOF, strategy breakdown, cost-of-free, AI review, mistakes, fees | 05c, 05i |
| `04f-api-tax.md` | Tax engine | 4.9 | Simulate, estimate, wash sales, lots, quarterly, harvest, YTD summary | 05h, 06g |
| `04g-api-system.md` | Infrastructure & ops | 4.4, 4.6, 4.7, 4.8§5 | Version, logging, MCP guard, service status/shutdown, health, images (global) | 05b, 06a, 10 |

**Total: 7 sub-files + 1 hub = 8 files** (comparable to GUI's 8 sub-files, slightly fewer than MCP's 10)

### Why this grouping?

1. **Trades (04a)** — Core entity. Reports, plans, images, journal links are all trade-scoped operations. This is the biggest domain and maps to the central user workflow.

2. **Accounts (04b)** — Everything about *where money lives*. Broker adapters, bank accounts, CSV/PDF import, identifier resolution. Distinct from trades (which are *what happened*).

3. **Auth (04c)** — Own domain per every research report. Envelope encryption, key management, session lifecycle. Security boundary isolation.

4. **Settings (04d)** — Small but distinct. Settings CRUD + validation + resolved endpoints. Consumed heavily by both GUI and MCP.

5. **Analytics (04e)** — All quantitative computations that analyze historical trades. Includes mistakes and fees because they're analytical lenses on trade data, not separate entities.

6. **Tax (04f)** — Complex, isolated domain with unique business rules (wash sales, lot matching, quarterly estimates). Every model flagged this as a natural bounded context.

7. **System (04g)** — Infrastructure ops. Small endpoints that rarely change. MCP guard, health, version, logging, service lifecycle.

### Internal Structure of Each Sub-File (Vertical Slice)

Per Gemini's and Claude's convergence on the **Specification by Example** pattern:

```
## Domain Overview
Brief responsibility statement + service layer dependencies

## Pydantic Schemas
Request/response models with field-level validation rules

## Route Specifications  
HTTP methods, paths, delegated service calls, error codes

## E2E Tests
Immediately following the routes they verify

## Consumer Notes (optional)
Which MCP tools / GUI pages call these endpoints
```

---

## 5. Resolved Decisions

### Q1: ✅ Analytics ABSORBS mistakes + fees

**Evidence:** Web research into production trading journals confirms that mistakes and fees are universally treated as **tag-based analytics dimensions** on trades, not standalone entities:

| Trading Journal | How They Handle Mistakes/Fees |
|----------------|------------------------------|
| **TraderSync** | "Mistakes" is a dedicated **analytics report** alongside other reports — not a separate entity. Mistakes are assigned as tags to trades, then analyzed in aggregate. |
| **TradesViz** | Tracks "goals, commissions, fees, strategies, mistakes" as **filterable analytics categories**. 600+ statistics include mistake frequency as an analytics dimension. |
| **Tradervue** | Uses tags for mistake categorization, analyzed via reports. |
| **Bookmap** | Recommends "Note down all your findings under separate headings" — mistakes as an analytical lens on trades. |

**Decision:** Mistakes (~4 routes) and fees (~4 routes) stay in `04e-api-analytics.md`. They are analytical perspectives on trade data, not standalone business entities.

---

### Q2: ✅ ALL images merge into trades (`04a-api-trades.md`)

**Sequential thinking analysis:**

1. All images in Zorivest are **trade-owned** — every image has a `trade_execution_id` FK. No orphaned images exist.
2. The "global" `/images/{id}` endpoint is just a **convenience accessor** for when the PK is known (e.g., analytics dashboard thumbnails). It still queries trade-owned images.
3. REST best practices (Moesif, Stack Overflow) confirm: sub-resources should be co-located with parent resources.
4. Only ~5 image endpoints total — below the <5 threshold for justifying a separate file.

**Decision:** All image routes (both nested `/trades/{exec_id}/images/*` and flat `/images/{id}`) go in `04a-api-trades.md`. The System file table is updated to remove "images (global)":

| File | Updated Routes |
|------|---------------|
| `04a-api-trades.md` | Trade CRUD, reports, plans, **all images**, journal linking, round-trips |
| `04g-api-system.md` | Version, logging, MCP guard, service status/shutdown, health |

---

### Q3: ✅ Per-sub-file consumer notes (co-located, NOT in hub)

**Sequential thinking analysis:**

Two audiences for consumer mapping:
1. **Developer finding "what calls this endpoint?"** → per-sub-file notes are best (co-located)
2. **Architect seeing the full picture** → centralized table is nice but creates sync problems

Analysis of the centralized approach:
- Hub table = ~50 rows × 3 columns ≈ 70 lines of markdown
- Would need updating when MCP tools or GUI components change — **churn in the REST API spec caused by consumer changes** violates separation of concerns
- Three different phases (04, 05, 06) would need coordination to keep it in sync

**Decision:** Each sub-file gets a brief **"Consumer Notes"** section (~3 lines max) listing primary consumers. The hub file simply states: *"Each sub-file contains a Consumer Notes section documenting which MCP tools and GUI components consume its endpoints."* If a full cross-reference is needed later, it can be auto-generated.

---

### Q4: ✅ Mode-gating pattern WILL be documented

Freqtrade's `is_trading_mode` / `is_webserver_mode` dependency injection maps directly to Zorivest's concept of **"unlocked DB required"** routes.

**What this looks like in the hub file's middleware section:**

```python
# Dependencies that gate route availability
def require_unlocked_db(db: SQLCipherDB = Depends(get_db)):
    """All domain routes require an unlocked database.
    Only system routes (health, version, MCP guard status) 
    are available before unlock."""
    if not db.is_unlocked:
        raise HTTPException(403, "Database is locked")
```

**Routes available before unlock:** health, version, unlock endpoint itself, MCP guard status
**Routes requiring unlock:** everything else (trades, accounts, settings, analytics, tax)

This is already implicit in the service-layer `Depends(get_*_service)` calls but will now be **explicitly documented** as a first-class architectural pattern.

---

### Q5: ✅ OpenAPI tags defined NOW

One tag per sub-file domain, defined in the hub file's app factory section:

```python
tags_metadata = [
    {"name": "trades",    "description": "Trade lifecycle: CRUD, reports, plans, images, journal"},
    {"name": "accounts",  "description": "Brokers, banking, import, identifiers, positions"},
    {"name": "auth",      "description": "Unlock/lock, API keys, session management"},
    {"name": "settings",  "description": "Configuration CRUD, validation, resolved settings"},
    {"name": "analytics", "description": "Quantitative analysis: expectancy, drawdown, SQN, fees, mistakes"},
    {"name": "tax",       "description": "Simulate, estimate, wash sales, lots, quarterly, harvest"},
    {"name": "system",    "description": "Health, version, logging, MCP guard, service lifecycle"},
]
```

**Why now:** ChatGPT's research showed that stable `operationId` and `tags` prevent rework if Zorivest later uses FastAPI's built-in SDK generation (`fastapi.tiangolo.com/advanced/generate-clients/`). The 7 tags map 1:1 to the 7 sub-files — clean and predictable.

---

## 6. Final Proposed Split (All Decisions Applied)

### Hub: `04-rest-api.md` (~150 lines)

| Section | Content |
|---------|---------|
| Goal & Principles | Thin delegation layer, service-layer dependency |
| App Factory | FastAPI instantiation, OpenAPI tags metadata (Q5) |
| Lifespan | SQLCipher init/shutdown |
| Middleware | CORS, error handlers, request ID, **mode-gating pattern (Q4)** |
| Router Manifest | 7 `include_router()` registrations with prefixes |
| Shared Schemas | PaginatedResponse, ErrorEnvelope |
| Cross-Domain Tests | Integration tests spanning multiple domains |
| Exit Criteria | Aggregated from sub-files |

### Sub-Files (7 total)

| File | Domain | Endpoints | Key Change |
|------|--------|-----------|------------|
| `04a-api-trades.md` | Trade lifecycle | CRUD, reports, plans, **all images (Q2)**, journal, round-trips | Images moved here from system |
| `04b-api-accounts.md` | Accounts & ingest | Brokers, banking, import, identifiers, positions | — |
| `04c-api-auth.md` | Security | Unlock/lock, API keys, session, `/status` | — |
| `04d-api-settings.md` | Configuration | Settings CRUD, validation, resolved | — |
| `04e-api-analytics.md` | Analysis | Expectancy, drawdown, SQN, PFOF, AI review, **mistakes, fees (Q1)** | Absorbs mistakes + fees |
| `04f-api-tax.md` | Tax engine | Simulate, estimate, wash sales, lots, quarterly, harvest | — |
| `04g-api-system.md` | Infrastructure | Health, version, logging, MCP guard, service lifecycle | Images removed |

### Each Sub-File Structure

```
## Domain Overview + Service Dependencies
## Pydantic Schemas (inline with routes)
## Route Specifications (HTTP methods, paths, delegation, errors)  
## E2E Tests (immediately following routes)
## Consumer Notes (~3 lines: which MCP tools + GUI pages call these) [Q3]
```
