# Design research for a local-first scheduled investment data pipeline

## Orchestration and policy model

A practical way to reconcile “AI-authored JSON policy” with reliable execution in a single-process desktop app is to treat the policy as *a declarative plan that must be compiled into an executable run graph* before any external side effects occur. That compile step resolves criteria (e.g., “watchlist tickers”, “positions where position > 0”, “since last run”) into concrete work items, and validates that the policy is safe, internally consistent, and feasible under known provider constraints. This mirrors a pattern used by larger workflow engines: a static author-time graph can expand into runtime work based on current data (e.g., dynamic task mapping creates tasks at runtime from upstream results). citeturn1search3

For scheduling semantics, APScheduler gives you mechanisms that map well to a local-first pipeline: (a) a single scheduler instance typically “binds everything together”, (b) default job storage is in-memory, but persistent job stores exist, and (c) jobs can be constrained to avoid concurrent overlapping runs. APScheduler also explicitly documents “misfires” (missed runs due to downtime or delays) and “coalescing” (collapsing multiple missed run times into one run), both of which matter in a desktop environment where the app may be suspended or closed. citeturn11view0turn11view1

Inside an async FastAPI process, lifecycle matters because you want the scheduler to start exactly once and stop cleanly. FastAPI’s lifespan mechanism is the modern, recommended place to attach startup/shutdown logic (e.g., initialize DB connections, start the scheduler, register jobs, then tear down). citeturn2search2

Because your policy is authored by an agent that can call tools via MCP, the most important governance mechanism is *validation plus capability-bounded execution*. MCP is explicitly designed for exposing tools with schemas and metadata, including dynamic discovery of tool definitions; that strengthens the case for treating your pipeline steps (fetchers, renderers, senders) as “tools” with strict input schemas. citeturn14search0turn14search5turn14search1 entity["company","Anthropic","ai company"]

However, both MCP specs and entity["company","OpenAI","ai company"]’s MCP guidance emphasize a risk boundary: tool connections can leak sensitive data and can be misused if you accept untrusted tool definitions or allow unconstrained actions. Concretely, for your policy engine this implies: validate policy structure; restrict what tool calls can do; record all side effects; and ensure the agent cannot directly execute arbitrary SQL, arbitrary filesystem operations, or arbitrary code execution unless those are explicitly mediated and sandboxed. citeturn14search2turn14search15turn14search7

A high-leverage design choice is to make the “policy” itself a versioned document with a formal schema (JSON Schema), so that (a) you can reject malformed/unsafe policies deterministically, (b) the agent can be prompted against the schema, and (c) you can migrate old policies when your pipeline evolves. JSON Schema’s current meta-schema is 2020-12, and using an explicit draft level helps prevent the “schema drift” that otherwise tends to happen in agent-authored JSON. citeturn8search6turn8search2

## Fetch stage

### Criteria-driven fetching as a compilation problem

Your examples (“all watchlist tickers”, “last 30 days for tickers where position > 0”, “new earnings since last run”) are easiest to support if the policy language distinguishes *selectors* from *fetch operations*:

- **Selectors** resolve to concrete sets (tickers, accounts, CIKs, URLs) using DB queries and/or literal lists.
- **Fetch operations** specify a provider + dataset + parameterization, and reference selectors as inputs.

This matches the orchestration pattern where runtime data expands the work plan: the “selector” step produces a list and the engine then maps a fetch over that list (possibly batching), akin to how runtime task expansion works in dynamic task mapping. citeturn1search3

For “delta/incremental” cases, you generally want a persistent cursor/watermark per (policy, provider, dataset, logical entity) so you can ask “since last successful run” without re-downloading history. The dlt incremental model is informative here: it frames incremental loading as “only new/changed data” plus durable state tracking of what has been loaded, with cursor-based approaches that track max/min cursor values and persist last-seen state. citeturn3search1turn3search3turn0search3

A concrete local-first implementation is a `pipeline_state` table keyed by `(policy_id, provider_id, data_type, entity_key)` storing:
- last_success_at
- last_cursor_value (typed as text + a declared cursor_type)
- last_result_hash (for idempotency checks)
- last_error (for diagnostics)

This is the same functional role as dlt’s “state” concept, but implemented inside your encrypted local DB. citeturn3search14turn0search3

### Provider abstraction and registry

To avoid changing the pipeline engine when adding sources, you want “provider registration” to be data-driven and, ideally, plugin-friendly:

- At the code level, a `FetchProvider` interface can be expressed as either an ABC (runtime enforcement) or a Protocol (structural typing / static duck typing). Protocols were standardized specifically for this kind of “type by behavior rather than inheritance.” citeturn10search0turn10search1turn10search4
- At the packaging level, Python entry points allow discoverable plugins (installed distributions advertise implementations that your app can load at runtime). This is a mature pattern for extensibility without hardcoding provider lists. citeturn10search10turn10search16turn10search2

A robust provider registry usually needs two layers:
1. **Static capability declaration** (in code): supported datasets (prices, fundamentals, options, filings), symbol universes, max lookback, pagination model, batching hints, and which freshness semantics apply.
2. **Instance configuration** (in DB): API keys, base URLs, account IDs, and any user-tuned throttling overrides.

This also aligns with MCP’s tool model where each tool has a schema and metadata, and tools can be listed/discovered dynamically. citeturn14search0turn14search5

### Rate limiting, batching, and parallelism in one process

In a single-process async app, the “right” concurrency model is nearly always **parallelize across independent providers**, but **serialize/pace within each provider** using per-provider concurrency limits and rate tokens.

Why: many financial sources enforce provider-specific pacing rules and will return 429 or “pacing violation” errors if you burst.

Examples you can design against:
- entity["company","Interactive Brokers","brokerage firm"]’ TWS API documents explicit pacing violations for historical data requests, including rules like “identical requests within 15 seconds” and ceilings like “more than 60 requests within any ten minute period.” Your fetch layer should treat these as provider-enforced invariants and schedule accordingly (dedupe identical requests, enforce per-contract pacing, and spread requests over time). citeturn4search2
- IBKR’s Web API documentation also describes a global request rate limit (10 requests/second per authenticated username) and 429 on limit exceedance, which is a different but compatible throttling model. citeturn4search9turn7search13
- The entity["organization","U.S. Securities and Exchange Commission","us financial regulator"]’s EDGAR “fair access” guidance states a max request rate of 10 requests/second and asks clients to use efficient scripting and moderate requests. citeturn0search5turn0search13turn0search1
- Polygon’s own knowledge base states free-tier subscriptions have a limit of 5 API requests per minute (paid tiers differ), implying your provider config must be tier-aware rather than hardcoded. citeturn7search0

For Alpha Vantage, the situation illustrates why you should store rate limits in provider config and also detect limits dynamically:
- Alpha Vantage’s premium page references a “standard API usage limit” of 25 API requests/day (and points users to premium plans if they exceed it). citeturn6search3
- Yet many client-observed error payloads still contain the older “standard API call frequency is 5 calls per minute and 500 calls per day” message. citeturn6search1turn6search4turn6search9  
Treat this as a compatibility constraint: implement throttling based on configured tier + observed runtime errors, not assumptions.

For “50 tickers across multiple APIs,” batching strategy should be provider-declared (capabilities) rather than globally chosen:
- Some endpoints accept “multiple tickers per call”; others don’t; the provider should expose `max_symbols_per_request` and `supports_bulk_quotes`-style flags and let the engine batch accordingly.
- Where the provider does not define explicit numeric limits, you can still implement adaptive throttling based on HTTP 429 semantics: 429 indicates “too many requests,” and `Retry-After` can tell you how long to wait. citeturn7search13
- Rate limit headers are not standardized across providers, but industry patterns include `X-RateLimit-*` (legacy) and newer drafts define `RateLimit`/`RateLimit-Policy` headers for a more uniform approach—useful as a parsing strategy when available, but never assume they exist. citeturn12search14turn7search8 entity["organization","Internet Engineering Task Force","standards org"]

### Freshness and caching: turning “don’t refetch” into a contract

In a local-first application, caching isn’t an optimization—it's how you keep responsiveness and stay under rate limits.

A clean mental model is: **every fetch returns a cacheability contract**:
- *Key*: normalized request identity (provider + dataset + canonical params).
- *Validators*: ETag / Last-Modified if the source is HTTP cacheable.
- *TTL policy*: per dataset and per market session (“intraday price”, “EOD bars”, “filings index”, “RSS feed”).  

HTTP has a formal revalidation mechanism: cached responses can be validated with `If-None-Match` (ETag) or `If-Modified-Since`, and the caching rules are specified in RFC 9111. citeturn5search2turn5search7

For sources that are not standard HTTP APIs (e.g., broker sockets) you can still apply the same concept: store a provider-defined “freshness horizon” and “market session sensitivity” in provider capabilities, then use a shared `fetch_cache` table so any pipeline run can reuse results fetched minutes earlier (if still within freshness bounds). The result is that “should I refetch AAPL if fetched 5 minutes ago?” becomes a deterministic decision: consult the dataset’s TTL and market session rules, not the pipeline. citeturn5search2turn5search7

### Fetch output contract: provenance-first envelopes

To handle unknown/novel sources gracefully, Fetch should output **an envelope with provenance and schema hints**, not “just JSON.”

A proven approach in ingestion systems is “raw + normalized”:
- Keep raw payload bytes/JSON to preserve provider schemas for audit/debugging.
- Optionally attach a normalized representation if you have a mapping for that dataset/provider.

SQLite’s JSON support matters downstream, but even in Fetch it affects how you store raw: SQLite’s JSON functions assume JSON is stored as text, and functions like `json_extract()` return SQL scalars for scalar paths (and JSON only for arrays/objects), which can surprise code that expects “JSON in, JSON out.” citeturn0search2turn1search2turn15search8

A Fetch envelope that anticipates Transform would include:
- provider_id, dataset_id, request_id (stable hash), fetched_at
- cache_status (hit/miss/validated)
- raw_payload + content_type
- observed_schema_version (if provider publishes versioning) or inferred schema hash
- warnings (rate-limited, partial response, stale market, missing fields)

This makes “unknown data shapes” survivable because you can always store the envelope even if normalization fails.

## Transform stage

### Schema-on-write vs schema-on-read in SQLite: why hybrid wins locally

For an investment app, you need two opposing properties:
- Fast, indexed queries for core canonical entities (positions, transactions, OHLCV, corporate actions).
- The ability to persist and later inspect arbitrary JSON from user-defined sources without losing data.

A hybrid is usually the best fit for SQLite:
- **Schema-on-write** for known, high-value tables: typed columns, constraints, careful indexes.
- **Schema-on-read** for novel payloads: store raw JSON envelopes and optionally develop “late-bound” extraction via views/indexes when needed.

SQLite now supports **STRICT tables**, which enforce rigid type constraints more like other RDBMSs. This improves data quality gates for your canonical tables, but also has compatibility implications: databases containing STRICT tables require SQLite 3.37.0+ for read/write. citeturn10search3

### Catch-all storage designs: SQLite-specific trade-offs

When data doesn’t fit predefined tables, you outlined four options. In SQLite, the most maintainable and performant shape usually combines A and D.

**JSON document table (A) with expression indexes / generated columns (D)**  
SQLite’s JSON1 extension provides JSON functions and operators; you can then add indexes on expressions (e.g., `json_extract(payload, '$.ticker')`) and/or generated columns that compute extracted fields from the JSON and index those generated columns. These are first-class SQLite features: expression indexes are documented, and generated columns are documented as computed columns whose values derive from other columns. citeturn15search8turn2search0turn2search1turn2search8

This pattern is powerful for “unknown but later important” fields:
- Start by storing the full payload JSON.
- When a field becomes query-critical, add a generated column (or an expression index) without rewriting historical rows, then index it.
- You end up with “schema-on-read that can be partially materialized,” which is the core idea behind option D. citeturn2search1turn2search0turn15search8

**EAV (B)**  
EAV is classically used for sparse, unpredictable attributes, but it trades schema simplicity for query complexity and enforcement complexity. Even pro-EAV discussions emphasize the core trade: fewer null columns vs harder queries, type enforcement, and constraints living in metadata/code rather than the DB. In SQLite specifically, EAV often means many joins and aggregations across key-value rows, which tends to be slower and harder to index effectively as your dataset grows. citeturn8search5turn8search9turn8search13

**Dynamic table creation (C)**  
SQLite supports `ALTER TABLE` and schema changes, but making schema creation a runtime side-effect of unknown API payloads increases long-term fragility: migrations become hard to reason about, indices proliferate unpredictably, and the “AI agent created a new table” path becomes hard to secure and test. If you want some of the benefits of C, a safer compromise is: keep raw JSON, derive a proposed schema offline/in a “draft schema” layer, and only create new tables when a human (or a well-scoped deterministic rule set) accepts the schema.

**Recommendation for SQLite**: store unknowns in a JSON envelope table, then promote frequently-used fields into generated columns / expression indexes, optionally adding curated views for analysis. This uses SQLite’s strengths (JSON functions + expression indexes + generated columns) rather than fighting SQLite into becoming a dynamic-schema document DB. citeturn15search8turn2search0turn2search1turn2search8

### Normalization for known data: mapping, unification, dedupe, validation

For canonical financial datasets, normalization is less about “rename fields” and more about guaranteeing *unit, timebase, and identity correctness*.

A robust FinancialDataNormalizer pattern typically needs:
- **Field mapping**: provider-specific names → canonical names. (In practice this is a mapping table keyed by `(provider_id, dataset_id, provider_field)` with canonical target + transform function or transform descriptor.)
- **Time series alignment**: decide canonical timestamp semantics (exchange local time vs UTC) and bar labeling (start vs end time). This isn’t covered in the sources above, but it’s pivotal to avoid subtle P&L distortions.
- **Unit and currency normalization**: normalize currencies consistently (or persist both “native currency” and “base currency converted” values with explicit FX source and timestamp).
- **Deduplication and conflict resolution**: if the same ticker arrives from two providers, you need a deterministic “winner” rule (policy-defined precedence, recency, or “provider reliability score”), and you need DB constraints that prevent duplicate bars/articles.

SQLite supports **UPSERT** via `INSERT ... ON CONFLICT DO UPDATE`, which provides the core primitive you need for “merge-ish” behavior when loading time series or de-duplicating news items by unique URL/hash. citeturn9search3

dlt’s loading strategies are an excellent conceptual blueprint: it explicitly distinguishes append, replace, and merge; merge requires identifying keys (primary_key/merge_key) and supports different merge strategies. Even if you do not embed dlt as a runtime dependency, copying its semantics into your Transform stage gives you a clear, policy-addressable vocabulary (“append OHLCV, replace positions snapshot, merge news by URL”). citeturn3search1turn3search0turn3search19

### Transform as a validation gate: fail-fast vs quarantine

For local scheduled pipelines, “fail-fast always” tends to produce brittle UX (a single bad response blocks the whole report), but “accept everything silently” produces untrustworthy portfolios. A policy-driven middle path is usually best:

- Canonical tables (prices used in valuation, positions used in exposure) should enforce type/constraints (STRICT tables where feasible) and reject irreparably malformed rows. citeturn10search3
- Novel/catch-all payloads should be stored even when they fail normalization, but with quality metadata and an explicit “quarantine” status so you can inspect and iterate mappings later.

SQLite performance and concurrency considerations matter here. In WAL mode, SQLite provides more concurrency because readers do not block writers and vice versa, but it still fundamentally supports only one writer at a time, and extremely large transactions (>~100MB) may perform worse or fail in WAL. That pushes you toward batching writes into moderate-sized transactions and keeping write phases short. citeturn1search1turn9search12

Because you are using SQLCipher, it’s also relevant that SQLCipher encrypts WAL files using the database key when WAL mode is enabled—important for a local investment app where raw payloads may contain sensitive account or trading data. citeturn9search5 entity["company","Zetetic","sqlcipher vendor"]

## Store Report stage

### Reports as first-class entities: versioning, auditability, reproducibility

Treating “report” as a persisted domain object is the right instinct for a local scheduled system because it gives you:
- a stable history of what was produced when,
- the ability to re-render or re-send,
- and an audit trail for what data the AI agent used.

In a local-first app, “report versioning” is especially valuable because your schemas and normalization rules will evolve. Practically, you want:
- `report_spec_version` (schema/DSL version)
- `report_template_version` (renderer version)
- `data_snapshot_version` or `snapshot_hash` (immutability marker)

This is analogous to a migration discipline: the stored report must carry enough version metadata that future code can interpret it safely.

### Report specification schema: constrain power, keep flexibility

Your example spec embeds raw SQL queries per section. That gives maximum power but introduces two classes of risk:
- correctness bugs (bad SQL, bad parameters, slow queries),
- and security/safety bugs (untrusted SQL changing data, or reading unintended tables, if the agent is compromised).

Even in a single-user desktop app, treating agent-generated SQL as “untrusted input” is the safest baseline. entity["organization","OWASP","web app security org"] recommends parameterized queries / prepared statements as a primary defense against SQL injection because they separate code from data. citeturn12search0turn12search8

But parameterization has an important limitation: bound parameters can only replace literal values, not identifiers or SQL keywords (e.g., column names in ORDER BY). If your report spec allows dynamic ordering or column selection, you must implement allowlists / structured representations for those elements rather than trying to parameter-bind them. citeturn12search1

Given those constraints, a strong pattern for report specs is:
- Prefer a structured query representation (a minimal DSL) for common cases (select table/view, filters, group by, order by, limit).
- Allow raw SQL only in explicitly privileged contexts (e.g., “advanced mode”), always read-only, and always audited.

SQLite has two mechanisms that can help you enforce “read-only report queries” even if the spec contains SQL:
- `PRAGMA query_only` can prevent data changes by causing CREATE/INSERT/UPDATE/DELETE/etc. to yield SQLITE_READONLY errors when enabled. citeturn13search0
- The SQLite authorizer API (`sqlite3_set_authorizer`) exists specifically for preparing SQL from untrusted sources and denying disallowed operations (like writes, schema changes, or access to sensitive tables). citeturn13search5

Those features are a good match for an AI-authored report spec: you can safely execute limited SQL to populate a report snapshot while ensuring the report generator cannot mutate the portfolio database. citeturn13search0turn13search5

### Conditional and narrative sections: JSON-native rule languages

For conditional blocks (“show alerts section if count > 0”), you have three viable approaches:

- Run a SQL query and compare the scalar result (simple but can explode into “SQL everywhere”).
- Use a JSON-native rule language like JsonLogic for conditions evaluated against already-fetched metrics (keeps report logic in JSON, not SQL). JsonLogic is explicitly designed for “complex rules serialized as JSON,” where rules are a JSON abstract syntax tree. citeturn8search3turn8search11
- Use a JSON query language like JMESPath to compute derived values or select data from JSON snapshots (helpful when report data is already in JSON). JMESPath is a defined JSON query language with a formal specification. citeturn12search3turn12search15

A durable design is: keep SQL responsible for *data retrieval* from canonical tables/views; keep JsonLogic/JMESPath responsible for *section gating and light reshaping* on the retrieved snapshot. That reduces the attack surface and makes the report spec more portable and testable. citeturn8search3turn12search3

### Data snapshots: storing results with provenance

If you want auditability (“what did we send?”), you need a snapshot. The key is: snapshot must be tied to provenance fields (query text/DSL, bound parameters used, the time, and the source data versions).

A practical envelope per section in `data_snapshot JSON` typically includes:
- `section_id`, `generated_at`
- `query` (or DSL structure) + `params`
- `rows` (data)
- `row_count`, `duration_ms`
- `warnings` (missing data, staleness)

This makes the report reproducible even if later prices update.

## Render stage

Rendering should be treated as a deterministic function of `(report_spec, data_snapshot, renderer_version, locale settings)` and should produce a stored artifact (HTML and/or PDF) plus metadata (hash, render time, size).

Electron provides a direct primitive for PDF generation from rendered web content: `webContents.printToPDF()` returns a Promise resolving to the generated PDF data (Buffer), and it documents interactions like `@page` CSS overriding landscape settings. citeturn2search3

In a local-first app, this suggests a robust rendering workflow:
1. Compile report spec → HTML (with embedded references to data snapshot, charts, tables).
2. Render in an offscreen BrowserWindow/webContents (or a hidden window).
3. Call `printToPDF()` and store the output on disk, linking it from your Report record. citeturn2search3

To keep rendering efficient and stable, you can cache rendered outputs keyed by a hash of `(specification JSON + data_snapshot JSON + renderer_version)`—if unchanged, skip rendering and reuse existing artifacts. This matches the broader caching principle in HTTP systems (keyed resources + validators), even though you’re applying it locally rather than over the network. citeturn5search2

## Send stage and operational footing

Even though you’re not building a cloud system, “Send” introduces user-impacting side effects, so it benefits from some of the same reliability primitives as distributed pipelines: idempotency, logged attempts, backoff, and user-visible status.

### Idempotent sends and retry discipline

A local pipeline should record send attempts in a `report_delivery` table (report_id, channel, destination, attempt_no, status, error, sent_at). This allows “retry failed sends” without regenerating the report and avoids duplicates by checking whether a given report+channel+destination has already succeeded.

When sends touch rate-limited APIs (email providers, webhook endpoints, broker APIs), follow HTTP’s standard semantics:
- Treat HTTP 429 as a signal to slow down.
- Respect `Retry-After` when present. citeturn7search13

### Security boundaries relevant to local apps

Because you plan to accept “user-defined sources” and “agent-authored policies,” the biggest local risk is executing something you didn’t mean to execute. Two SQLite-adjacent security points are particularly relevant:

- If you execute untrusted SQL (e.g., in report specs), enforce read-only using `PRAGMA query_only` and/or authorizer callbacks as described above. citeturn13search0turn13search5
- Avoid enabling SQLite extension loading for untrusted SQL; extension loading can create a code execution path if enabled and abused. Discussions in the ecosystem explicitly warn that enabling extension loading can turn SQL injection into extension loading capability, and real-world issues demonstrate malicious usage of `load_extension()` when it is enabled. citeturn13search6turn13search2

### SQLCipher operational details to bake into the pipeline

Because your pipeline will write frequently (prices/news snapshots, report snapshots), you will care about both performance and confidentiality:
- WAL improves concurrency and is often faster, but has transaction-size caveats; keep transactions moderate rather than enormous. citeturn1search1turn9search12
- SQLCipher documents that when WAL mode is used, content in the WAL file is encrypted using the database key—important if you store raw provider payloads and report snapshots. citeturn9search5
- SQLCipher’s API docs show that encryption parameters (e.g., `PRAGMA key`, `cipher_page_size`) must be set at the correct time (after keying, before first DB operation), and must be consistently applied when reopening databases that use non-default parameters. citeturn1search0

Finally, if you use SQLAlchemy with SQLite/SQLCipher, note that SQLAlchemy’s SQLite dialect explicitly lists `pysqlcipher` among DBAPI options, which can simplify integration patterns in your single-process environment. citeturn15search1