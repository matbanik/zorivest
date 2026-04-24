# Adversarial review of the Zorivest pipeline engine

Zorivest's architecture is solid in conception but **under-hardened at the boundaries that matter most for an LLM-authored policy engine**: data immutability, SQL authorizer scope, URL validation, and event-loop protection against synchronous-C blocking calls. The dominant threat model is not network attackers — it is trusted LLMs authoring untrusted *code* (policies, SQL, Jinja, URLs), and many current mitigations are structural conventions rather than enforced invariants. Meanwhile, several documented cloud patterns (OTel, circuit breakers, saga compensation, DLQ) are being considered for a context where they add ceremony without insight. The single highest-value move is not a new pattern — it is tightening five existing boundaries so the LLM cannot accidentally (or deliberately) corrupt state the engine claims is append-only.

---

## 1. Executive summary

**Top 3 risks.** First, **StepContext mutable-dict aliasing** silently corrupts downstream steps and the audit log. Pydantic v2's `model_copy()` is shallow by default, pandas DataFrames alias view/copy semantics unpredictably across versions, and LLM-authored policies routinely reuse references. Today, "steps don't mutate shared state" is a convention, not an enforced invariant. Second, the **SQL authorizer default-deny is necessary but not sufficient**: ATTACH DATABASE, PRAGMA manipulation, recursive CTE DOS, and virtual-table triggers remain reachable unless explicitly locked out, and compile-time hardening (`SQLITE_OMIT_LOAD_EXTENSION`, `SQLITE_DQS=0`, `sqlite3_limit` caps) is typically missing. Third, **SQLCipher's 256K PBKDF2-HMAC-SHA512 iterations stalls the event loop for 200–500 ms per open** unless routed through `asyncio.to_thread`, and the raw-key pattern (unlock once, re-open with `PRAGMA key = "x'..'"`) is the only way to avoid paying KDF cost on every connection.

**Top 3 recommendations.** First, **freeze the StepContext boundary with deep-copy on `put` and `get`, Pydantic models with `frozen=True`, and `pandas.options.mode.copy_on_write = True`** — this single change eliminates an entire class of silent-corruption bugs at ~5–20 ms/step cost. Second, **introduce a dual-connection SQL sandbox**: trusted app connection with full authorizer; a separate read-only connection with `query_only=ON`, `trusted_schema=OFF`, a sqlglot pre-parser rejecting non-SELECT and ATTACH/PRAGMA, and `sqlite3_limit(SQLITE_LIMIT_VDBE_OP, ...)` to bound recursive-CTE cost. Third, **refactor the 8-parameter `PipelineRunner.__init__` into two frozen dataclasses — `Infra` (app-lifetime) and `RunContext` (per-run) — rather than adopting a DI container**, because at this scale dishka/dependency-injector/that-depends add indirection the app does not need, while scope-separation-as-types gives you the benefit for free.

---

## 2. Risk matrix

Scoring: Likelihood × Impact, adjusted for single-user desktop, ~50 API calls/run, LLM-authored policies as dominant threat vector.

| # | Risk | Likelihood | Impact | Current mitigation | Recommended mitigation |
|---|---|---|---|---|---|
| 1 | **StepContext mutable-dict aliasing** corrupts downstream steps via Pydantic shallow `model_copy` and pandas view/copy ambiguity | High | Silent corruption of audit log and report output | Implicit "steps don't mutate" convention | Deep-copy on `put`/`get`; Pydantic `frozen=True` + tuple collections; `pd.options.mode.copy_on_write = True`; CI integrity-hash assertion per-step |
| 2 | **SQL authorizer bypass** via ATTACH DATABASE, PRAGMA, recursive CTE DOS, virtual-table triggers | Med–High | Data exfil / DOS / silent schema change | `set_authorizer` default-deny + PRAGMA `query_only` | Dual-connection sandbox; sqlglot pre-parser; `trusted_schema=OFF`; `sqlite3_limit` VDBE-op cap; compile-time `OMIT_LOAD_EXTENSION`, `DQS=0` |
| 3 | **GenericUrlBuilder SSRF** to 169.254.169.254, 127.0.0.1, `file://`, RFC1918, DNS rebinding | Medium | Credential/data exfil; local-IPC abuse | Unspecified | Allowlist host + scheme (`https` only); resolve-verify-connect pattern pinning to checked IP; block private/loopback/link-local |
| 4 | **ConditionEvaluator edge cases** — NaN ≠ NaN, `Decimal('1.1') != 1.1`, `"5" < "10"` lexicographic, coerced Pydantic lax mode | High | Wrong skip/execute decisions | Pydantic v2 validation on policy schema (structural only) | Canonical operand coercion (NaN rejected, float→Decimal via str); Pydantic strict mode globally; missing-path raises; record every evaluation in audit |
| 5 | **Email template + SMTP header injection** via Jinja2 default `autoescape=False` and CRLF in headers | High | Phishing, XSS at webmail, BCC exfil | Implied Jinja2 + aiosmtplib | `Environment(autoescape=select_autoescape([...]), undefined=StrictUndefined)`; build via `email.message.EmailMessage` (stdlib rejects CRLF in headers); regex-filter attachment names; app-owned From |
| 6 | **SQLCipher PBKDF2 blocks event loop** 200–500 ms per open at 256K iter (SQLCipher 4 default) | High | UI freeze; cascaded asyncio cancellation bugs | Unspecified | `asyncio.to_thread` for every open; unlock-once + raw-key pattern (`PRAGMA key = "x'...'"`) skips KDF on subsequent opens; keep connection alive whole session |
| 7 | **Electron SIGKILL + power loss** loses last committed transactions in WAL `synchronous=NORMAL` — violates append-only durability | Medium | Audit-tail data loss | SQLite defaults (consistency yes, durability no against power loss) | `PRAGMA synchronous=FULL`; `fullfsync=ON` on macOS; aggressive checkpointing; IPC-mediated graceful shutdown handshake with 5s hard timeout |
| 8 | **APScheduler suspend/resume misfire** — default `misfire_grace_time` silently drops runs or bursts on wake | High | Missed scheduled runs or thundering herd | `max_instances=1` (prevents overlap only, not misfire/burst) | Explicit per-job `misfire_grace_time`; `coalesce=True`; persistent SQLAlchemyJobStore; Electron `powerMonitor` → Python resume-reconciliation |
| 9 | **Content-hash non-determinism** — `json.dumps` without `sort_keys`, float repr, UTC-Z vs `+00:00`, deprecated `datetime.utcnow()` | Med–High | Silent dedup bypass / double inserts | SHA-256 (implied) | Canonical encoder (`sort_keys=True, separators=(",",":")`, Decimal→str, UTC-Z datetimes); ban `utcnow` via ruff DTZ003/DTZ005; dedup keyed on `(policy_id, step_id, run_id)` not just content |
| 10 | **INSERT OR IGNORE + NULL-distinct UNIQUE** silently inserts duplicates on nullable dedup columns | High | Duplicate audit rows, broken append-only invariant | `INSERT OR IGNORE` | `ON CONFLICT(cols) DO NOTHING` with explicit target; NOT NULL dedup columns or partial unique indexes (`WHERE col IS NULL` / `WHERE col IS NOT NULL`); end-of-pipeline duplicate assertion |
| 11 | **WeasyPrint infinite loops / hangs** on malformed HTML; no subprocess isolation | Medium | App hang, memory leak | None described | Run in `subprocess.run(..., timeout=60)`; custom `url_fetcher` allowlist (`data://`, template dir only); `resource.setrlimit(RLIMIT_AS)` in child; size/node-count caps |
| 12 | **Cooperative cancellation during Store/Send** partial commit | Medium | Audit says "failed" but side-effect happened (or vice-versa) | Append-only audit log (not sufficient by itself) | `asyncio.shield(session.commit())` on unsafe critical sections; audit row in same transaction as business write; two-phase `send_attempted`/`send_confirmed` for SMTP |
| 13 | **`asyncio.wait_for` cancellation edge cases in 3.12** (CPython #133747, #42130, #43389) | Medium | Leaked resources, half-commits | Depends on step discipline | Prefer `async with asyncio.timeout():`; lint-ban `wait_for` in step code; `except Exception` never `BaseException`; re-raise `CancelledError` |
| 14 | **Fetch TTL market-session / DST / holidays bugs**; `utcnow()` deprecated in 3.12 | Medium | Stale data labeled fresh | Unspecified | `zoneinfo` only (never pytz); `exchange_calendars` for NYSE sessions; UTC persistence; ruff DTZ bans |
| 15 | **aiosmtplib indefinite hang** — connect-phase timeout has known issues (issue #50) | Medium | 60s+ UX delay, stuck pipeline | Default 60 s per command | Explicit 30 s per-op + 45 s aggregate `asyncio.timeout`; prefer implicit TLS on 465; two-phase audit so recovery is possible |
| 16 | **RefResolver cross-context exfiltration** if scope spans policies/runs | Medium | Cross-policy data leak | Unclear (design-dependent) | Per-run isolated StepContext; refs only resolve within current run; sensitivity labels (`public`/`internal`/`secret`); high-entropy-string scrub post-step |

---

## 3. Architecture decision records

### ADR-001 — Immutable StepContext with deep-copy boundary
- **Status.** Proposed, high priority.
- **Context.** LLM-authored policies cannot be trusted to respect reference ownership. Pydantic v2's `model_copy()` is shallow by default (per the v2 concepts docs and discussion #9313); pandas DataFrame copy semantics shifted with Copy-on-Write in 3.0 and are version-sensitive. A Transform that normalizes prices in-place silently poisons every downstream Render, Store, and Send — and the audit log then records different values than were actually sent.
- **Decision.** `StepContext.put(step_id, value)` performs `copy.deepcopy(value)`; `get(step_id)` returns a deep copy. All PolicyDocument step schemas declare `model_config = ConfigDict(frozen=True)` with tuple-typed collections and `types.MappingProxyType` wrappers for dicts. DataFrames are deep-copied on exit from Transform. Global `pd.options.mode.copy_on_write = True` is set at startup. CI runs an integrity assertion that hashes each `ctx[step_id]` after step completion and re-checks at run end; any divergence fails the build.
- **Consequences.** Added 5–20 ms/step for deep copies (acceptable at 50 calls/run). Policies must use explicit merge/update steps rather than in-place mutation — a minor API clarification. Eliminates a class of silent corruption that currently depends on developer discipline.

### ADR-002 — Dual-connection SQL sandbox
- **Status.** Proposed, high priority.
- **Context.** Default-deny `set_authorizer` is necessary but not sufficient: SQLite's own security page documents the need for `trusted_schema=OFF`, `SQLITE_DQS=0`, and `sqlite3_limit` caps. Recursive CTEs within SELECT can exhaust CPU/memory even with `query_only=ON`. ATTACH DATABASE can mount a malicious file and trigger side effects on read. The LLM-policy threat model makes this non-hypothetical.
- **Decision.** Two SQLCipher connections: a trusted app connection with full authorizer, used only by native repos; and a sandbox connection opened with `PRAGMA query_only=ON; PRAGMA trusted_schema=OFF;` plus `sqlite3_limit(SQLITE_LIMIT_VDBE_OP, N)`, `SQLITE_LIMIT_SQL_LENGTH`, and `SQLITE_LIMIT_COMPOUND_SELECT` reductions. All policy-authored SQL goes through a sqlglot pre-parser rejecting non-SELECT, ATTACH, PRAGMA (except a whitelist), CREATE VTABLE, CREATE TRIGGER, and `.load_extension`. SQLCipher built with `-DSQLITE_OMIT_LOAD_EXTENSION -DSQLITE_TRUSTED_SCHEMA=0 -DSQLITE_DQS=0`.
- **Consequences.** Slight complexity at connection-wiring time; robust isolation; DOS via recursive CTE bounded to a defined instruction budget. The sandbox connection cannot write — any policy that thinks it can write via side-channel will fail loudly at the authorizer.

### ADR-003 — Allowlist URL fetcher with pre-resolved IP pinning
- **Status.** Proposed.
- **Context.** OWASP SSRF Cheat Sheet: "Deny-lists are bypass-prone. Prefer allow-lists." A `GenericUrlBuilder` fed by LLM input is an SSRF primitive; decimal/octal IP encoding, DNS rebinding, and scheme confusion (`file://`, `gopher://`) all defeat naive filters. On desktop this is still actionable — local services, Electron devtools ports, cohabiting VPN tunnels, and `file://` reads of local filesystem are all reachable.
- **Decision.** Schemes restricted to `https`. Hostnames allowlisted per-provider. `socket.getaddrinfo` resolves the hostname once; every resolved IP is checked with `ipaddress.ip_address(ip).is_private | is_loopback | is_link_local | is_multicast` and rejected if matched; the HTTP connect is then made to the verified IP with the original Host header, defeating DNS rebinding. A network-level belt-and-braces: outbound connect attempts to 169.254.169.254, RFC1918, or loopback hard-fail the run with a loud security event.
- **Consequences.** Adding a provider is a deliberate act (registration in allowlist). SSRF class eliminated at the library boundary. ~1 ms added per Fetch for DNS + validation.

### ADR-004 — Raw-key SQLCipher connection pattern
- **Status.** Proposed, high priority.
- **Context.** SQLCipher 4 defaults to 256,000 PBKDF2-HMAC-SHA512 iterations (per the SQLCipher CHANGELOG), translating to 200–500 ms per connection open on typical laptop CPUs. Called inside an async frame, this stalls the entire event loop — freezing FastAPI, APScheduler ticks, and cancellation delivery. Lowering `kdf_iter` to gain speed is wrong: OWASP password-storage guidance targets ≥600K SHA-256 iterations, so 256K SHA-512 is already near the floor.
- **Decision.** The user's password derives the raw 64-hex key *once* at app unlock, via `asyncio.to_thread`. Subsequent connections open with `PRAGMA key = "x'<hex>'"` (raw-key form), which skips KDF entirely per the Zetetic SQLCipher API docs. A single long-lived primary connection per DB is maintained; short-lived connections are banned. Key held in process memory for the session only.
- **Consequences.** Startup pays the KDF cost once in a visible "Unlocking…" UI; zero freezes thereafter. Raw key in memory is mitigated by the fact that any attacker with process-memory access has already bypassed the encryption-at-rest threat model.

### ADR-005 — `asyncio.timeout()` + structured concurrency; ban `wait_for`
- **Status.** Proposed.
- **Context.** Python 3.12 has documented edge cases in `wait_for` + TaskGroup cancellation (CPython #133747, historical #42130/#43389/#44371) where cancellations can be swallowed under races. Cancelled SQLAlchemy commits, aiosmtplib socket writes, and WeasyPrint renders leave inconsistent state unless wrapped in `async with` and `CancelledError` re-raised cleanly.
- **Decision.** Replace `asyncio.wait_for` with `async with asyncio.timeout(t):` everywhere in step code. Use `TaskGroup` for any fan-out. `asyncio.shield(session.commit())` around critical commits. Audit rows written in the same transaction as business writes. Lint-ban `wait_for` in step modules. Every `except Exception` explicitly excludes `CancelledError`.
- **Consequences.** Slight refactor; dramatically more predictable cancellation; eliminates the "caught CancelledError silently" bug pattern.

### ADR-006 — Durable audit writes with graceful-quit IPC
- **Status.** Proposed, high priority.
- **Context.** Per SQLite WAL docs: `synchronous=NORMAL` provides consistency across crashes but can lose recently-committed transactions to power failure. Desktop laptops lose power; Electron's `SIGKILL` is routine; the "append-only audit log" invariant is currently violated any time the tail of recent commits vanishes on next boot.
- **Decision.** The audit-writing connection runs `PRAGMA synchronous=FULL;` (and `PRAGMA fullfsync=ON;` on macOS per avi.im/SQLite-fsync). `PRAGMA wal_autocheckpoint=100` plus explicit `sqlite3_wal_checkpoint_v2(FULL)` after each pipeline run. On normal quit, Electron IPCs "prepare to quit" → Python runs `PRAGMA wal_checkpoint(TRUNCATE); conn.close();` → acks → Electron terminates. Hard 5-second timeout so a hang still gets killed.
- **Consequences.** Commits become ~2–5× slower (acceptable at ~50 writes/run). Audit durability restored. Graceful shutdown path defined; ungraceful remains safe-on-reopen, just without power-loss durability guarantees for the final few milliseconds.

### ADR-007 — Refactor PipelineRunner to two frozen dataclasses (no DI container)
- **Status.** Proposed.
- **Context.** The 8-kwarg `__init__` is a Fowler "Long Parameter List" smell; the prescribed refactor is Introduce Parameter Object. dishka/dependency-injector/that-depends all solve real problems at scale but add indirection this app does not need: 8 deps, one scope boundary (app vs run), no plugin-loaded providers, no multi-tenancy. Scope separation can be expressed directly in the type system.
- **Decision.** Two `@dataclass(frozen=True, slots=True, kw_only=True)` bundles: `Infra` (app-lifetime — HTTP client, rate limiter, mailer, PDF renderer, clock, config) and `RunContext` (per-run — AsyncSession, repos). `PipelineRunner.__init__(*, infra: Infra, ctx: RunContext)`. Config loads through Pydantic Settings into `Infra.config`. The composition root is a single `async def compose(stack: AsyncExitStack) -> Infra` function called at app boot; APScheduler job entry constructs `RunContext` per run. DI-container adoption threshold set at ~20 providers OR genuine plugin/multi-tenant scoping.
- **Consequences.** Two-line `__init__`; scope distinction visible to the type checker; `AsyncLimiter` and HTTP pool correctly survive run boundaries (preventing rate-limit-budget burn across retried runs); zero new dependencies; perfect mypy/pyright support.

### ADR-008 — Suspend-aware scheduling with persistent jobstore
- **Status.** Proposed.
- **Context.** APScheduler 3.x `max_instances=1` prevents in-process overlap but does nothing about the suspend/resume problem: default `misfire_grace_time=1` silently skips missed runs; `None` can fire a burst on wake; laptop sleep for 2+ hours is routine. `max_instances=1` also does not survive a crash cleanly with a persistent jobstore.
- **Decision.** Persistent `SQLAlchemyJobStore` into SQLCipher. Per-job explicit `misfire_grace_time` aligned to semantics (15 min for hourly fetch, 1 h for daily report). `coalesce=True` to collapse bursts. Electron `powerMonitor` resume event IPCs to Python, which calls `scheduler.wakeup()` plus a resume-reconciliation that scans `audit_log` for missed runs and prompts the user (run catch-up / skip). App startup logs `(now - last_completed_run)` and warns if beyond expected interval.
- **Consequences.** Electron↔Python IPC contract gains one event. User may see a prompt after long sleeps — preferable to silent data gaps. No silent skip or thundering herd.

### ADR-009 — Strict ConditionEvaluator and canonical serialization
- **Status.** Proposed.
- **Context.** Python's comparison semantics combined with LLM-authored operand types produce silent logic faults: `float('nan') == float('nan')` is False; `Decimal('1.1') == 1.1` is False; `"5" < "10"` is False lexicographically. Pydantic v2 lax mode coerces `"5"` → `5` silently. `datetime.utcnow()` is deprecated in 3.12 and returns naive datetimes that compare-raise against aware ones. `json.dumps` without `sort_keys=True` produces non-deterministic hashes.
- **Decision.** All operands pass through a canonicaliser: `None` preserved, `float` → `Decimal(str(x))` with NaN rejected, mixed-type comparisons raise. `ConfigDict(strict=True)` enforced on PolicyDocument. Missing ref paths raise rather than evaluating falsy. All hashing uses `json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_canon)` with Decimals as `str(d.normalize())` and datetimes as UTC-Z ISO. `ruff` rules DTZ003/DTZ005 ban `utcnow`. Dedup keys include `(policy_id, step_id, run_id)`, not just content hash.
- **Consequences.** LLM policies must be explicit about types; slightly more parse-time validation errors; dramatic reduction in silent mis-evaluations and dedup bypass.

### ADR-010 — Explicit conflict targets; no bare `INSERT OR IGNORE`
- **Status.** Proposed.
- **Context.** SQLite unique indexes treat every NULL as distinct from every other NULL; `INSERT OR IGNORE` silently swallows CHECK and NOT NULL violations in addition to uniqueness conflicts. This produces silent duplicates and silently accepted bad data.
- **Decision.** Ban bare `INSERT OR IGNORE`. Use `INSERT ... ON CONFLICT(col1, col2) DO NOTHING` with explicit target columns. Dedup columns declared `NOT NULL` or protected by partial unique indexes (`CREATE UNIQUE INDEX ux_nn ON t(a,b) WHERE c IS NULL; CREATE UNIQUE INDEX ux_yn ON t(a,b,c) WHERE c IS NOT NULL`). Pipeline post-condition runs `SELECT COUNT(*) ... GROUP BY dedup_key HAVING COUNT(*) > 1` and aborts if non-zero.
- **Consequences.** Migration needed for existing tables. Loud failures on previously-silent constraint violations will surface latent bugs. Audit invariants finally guaranteed.

### ADR-011 — Subprocess-isolated WeasyPrint with locked-down url_fetcher
- **Status.** Proposed.
- **Context.** WeasyPrint's own docs acknowledge documented infinite-loop bugs (issues #560, #691). It runs in-process, so a hang takes down the FastAPI event loop; the default `url_fetcher` has no timeout for `file://` URLs. LLM-generated HTML/CSS meaningfully increases the probability of hitting these paths.
- **Decision.** Render in a `subprocess.run(..., timeout=60)` child. Custom `url_fetcher` allows only `data:` and `file://` under a pre-approved template directory; blocks `/dev`, `/proc`, arbitrary filesystem reads. HTML pre-validated against a size cap (2 MB) and node-count cap via lxml. Child process applies `resource.setrlimit(RLIMIT_AS, ...)`. WeasyPrint version pinned; bumps require CHANGELOG review.
- **Consequences.** ~100 ms fork overhead per PDF (negligible on desktop). Hang isolated to one process. Clear failure mode with user-presentable timeout message.

### ADR-012 — EmailMessage-based composition with autoescape on
- **Status.** Proposed.
- **Context.** Jinja2's default is `autoescape=False` (flagged by Bandit B701, CodeQL `py/jinja2/autoescape-false`, ruff `S701`). LLM-authored templates plus string-concatenated SMTP headers produce the classic template-injection + CRLF-injection double hit (CVE-2006-0712-class). Python's `email.policy.default` rejects CRLF in headers since 3.6, but only if you use it.
- **Decision.** Jinja2 `Environment(autoescape=select_autoescape(["html", "htm", "xml"]), undefined=StrictUndefined)`. All emails built via `email.message.EmailMessage` with `policy=policy.default` — never raw `sendmail(msg_str)`. `From` is app-owned (never policy-settable). Attachment filenames validated against `[A-Za-z0-9._-]{1,80}`. Addresses validated via `email.headerregistry.Address`.
- **Consequences.** Minor template rewrite; eliminates phishing/XSS/header-injection class at the boundary.

### ADR-013 — Idempotent send with two-phase audit; no saga
- **Status.** Proposed.
- **Context.** Three side-effect steps (Store, Render, Send). On Send failure, full saga compensation would delete a validly-generated report — destroying evidence the user wants to retain. Richardson's saga pattern targets distributed consistency across services with separate databases; Zorivest has one DB, one process, one user. Applying saga here is cargo-culting.
- **Decision.** No saga. No full outbox. Instead: Store and Render commit normally. Send runs with an SHA-256 idempotency key already in the schema; `status = 'sending'` written before network call, `status = 'sent'` after 250 OK. On crash-mid-send, recovery sees `sending` and reconciles via Message-ID or user confirmation. Failed sends appear in a GUI "Unsent reports" inbox with a Retry button. Next scheduled run naturally retries and the idempotency key prevents double-delivery.
- **Consequences.** No compensating logic to maintain. Partial state is genuinely consistent (report exists, delivery pending — that's true). User has a direct resolution path. At-least-once semantics; dual-write race has a 20-line recovery pattern, not a framework.

---

## 4. Testing strategy ranking (risk-adjusted ROI)

| Rank | Strategy | Setup | Maint/mo | Primary bug classes caught | Flakiness | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Pydantic v2 contracts at every stage boundary** (with `extra='forbid'`, `strict=True`, `AwareDatetime`, `condecimal`) | 4–8 h | 1–2 h | Provider API schema drift; silent field creep; Decimal precision; naive-datetime leakage | Very low | **Do first.** Schemas are the tests; near-zero maintenance; catches the existentially threatening bug classes (precision, timezone, field drift) in a financial app. |
| 2 | **Weekly schema-drift CI against live APIs** (GitHub Actions cron; 3 canonical symbols per provider; contracts as oracle) | 4–8 h | 1–3 h | "Yahoo/Polygon/Finnhub changed their API overnight" | Low (scoped to schema, not values) | **Do second.** Stays within Polygon's 5 req/min free tier; detects the #1 production outage risk before users do. Alert via built-in GH Actions email + `known_provider_issues.json` flag committed to a status branch that the Electron app reads on launch and surfaces as an in-app banner. |
| 3 | **Golden-file/snapshot tests (syrupy) for rendered PDF/email/report JSON** | 3–6 h | 2–4 h | Template regressions, LLM-policy-output drift, SQL-migration output changes | Low but churn-prone (inject a fixed clock) | **Do early.** Especially valuable for locking LLM-authored policy documents — any re-generation produces a reviewable diff. |
| 4 | **Hypothesis property-based, applied surgically** (Decimal round-trips; `RuleBasedStateMachine` over the SQLCipher ledger with `@invariant` balance checks) | 12–24 h | 2–4 h | Forgot-about-zero, Decimal rounding asymmetry, DST edges, ledger invariants | Medium (shrinker exposes real bugs that look like flakes) | **Do selectively.** Property-based shines for mathematical invariants; portfolio accounting's *conditional* invariants are mostly hand-coded. Use for ledger state machine and money round-trips, not broadly. |
| 5 | **VCR/cassette (vcrpy) as fast replay under contract tests** (`record_mode='none'` in CI; `filter_headers`) | 6–12 h | 4–12 h | Request-construction regression, auth-header handling | Medium–High (cassette staleness, binary encoding drift, cassettes-record-bugs) | **Use narrowly as replay layer, not as truth.** Contract tests are the real assertion; cassettes just make them fast. Never `record_mode=any` in CI. |
| 6 | **Shadow pipeline against live data** | 10–20 h | 8–20 h | End-to-end drift, unit/scale regressions | High (markets move; tolerance windows are hard) | **Skip for this app.** Repurpose as a manual pre-release smoke run. Schema-drift monitor catches most of the signal far cheaper. |

### Email-testing stack (Topic 3c)

Primary: `smtpdfix` (aiosmtpd under the hood; captures real `email.message.Message` via real SMTP on localhost) + `email.policy.default` structural assertions + `syrupy` snapshots of rendered plain and HTML bodies + parametrized CRLF-injection tests against recipient and attachment-filename paths + a threaded `Barrier`-based concurrency test for the idempotency-key dedup via SQLCipher `PRIMARY KEY` + `INSERT ... ON CONFLICT DO NOTHING`. ~3 hours of setup, 95% of realistic bugs caught. Add SpamAssassin local scanning (`spamc < rendered.eml`, assert score < 3) only if deliverability-to-Gmail is a stated requirement. Skip Mailpit in CI (it replaced the abandoned MailHog and is excellent for dev-time visual review, but Docker is too heavy for desktop CI).

---

## 5. Gap analysis verdicts

**Aggregation / Calculation as its own step.** *For*: portfolio metrics have distinct characteristics — windowing over full history, numerical stability concerns (Welford, log-returns), Decimal tolerance, and they are the output users care about. *Against*: still `data in → data out`, the platonic Transform; YAGNI until you have >5 metrics with materially different lifecycles. **Verdict: keep in Transform with a `kind: "metric"` sub-discriminator and structured metadata (`calculation_version`, `assumptions`).** Revisit when you have 5+ distinct metrics needing their own caching or scheduling.

**Notification beyond email.** *For*: OS toasts (macOS Notification Center, Windows Action Center, libnotify) are 100× more useful than email for a user staring at their laptop. *Against*: toasts live in Electron, requiring Python→FastAPI→frontend IPC. **Verdict: Send step is already polymorphic — add `desktop_toast` and `email` adapters, defer SMS/push to pluggable user-configured adapters (Pushover, ntfy).** The Python↔Electron bridge is a one-time IPC investment worth making for run-progress too.

**Export (CSV/Excel).** *For*: different lifecycle from PDF reports — user-chosen paths, no retention, different libraries (`openpyxl` vs `csv`). *Against*: both are "write structured data to a file"; lifecycle is a destination concern, not a taxonomy concern. **Verdict: sub-type within Render with `output_intent: {archive|download|ephemeral}` — the intent drives retention, default path, and whether the artifact is indexed in the reports table.**

**Archive/Cleanup.** *For*: consistency — everything else runs through the pipeline engine with audit events. *Against*: cleanup is cross-cutting maintenance, not business logic; SQLite `VACUUM` needs exclusive lock, no open transactions — awkward inside an async pipeline. **Verdict: APScheduler-triggered maintenance function, outside the pipeline engine, but emitting to the same `pipeline_run_events` table.** Force-fitting `VACUUM` into the 5-step vocabulary teaches the wrong lesson to future step authors.

**Validation/Assertion beyond Pandera.** *For*: Pandera validates schema inside a step; quality gates validate semantics across the run ("portfolio dropped 23% since last run — likely a data error, do not Send"). These are business-rule halts, and MCP policies deserve a declarative slot for them. *Against*: any Transform can raise; adding a type creates a false distinction. **Verdict: Transform sub-kind `kind: "assertion"` with halt-on-fail semantics, structured `assertion_failed` events, and a GUI override path. This is the single most under-weighted gap in the current design — silently rendering a 20%-drop report because nobody wrote the check is a real and embarrassing failure mode. Ship pre-Send assertions (drawdown, staleness, coverage) before launch.**

**Enrichment (multi-source join).** *For*: Yahoo quotes + Polygon fundamentals + Finnhub news is the canonical fan-out/fan-in pattern; needs parallel fetch, per-source error attribution, per-source retry. *Against*: engine-level DAG support (multiple Fetch → one Transform) expresses this natively without a new type. **Verdict: invest in engine-level parallel Fetch via `depends_on` DAG semantics + `asyncio.gather`, not a new Enrich step.** The fan-out/fan-in terminology is cloud-workflow jargon; in a single-process asyncio app it is `asyncio.gather`.

**Branch/Fork.** *For*: real cases — portfolio-type-driven templates, success/failure diverging paths, regional provider routing. *Against*: branching invites Airflow-esque DAG complexity; for 3–5 portfolios, one pipeline per variant selected at schedule time is simpler and more auditable. **Verdict: no Branch step — one pipeline per variant plus `skip_if` for minor per-step toggles.** If you find yourself writing `skip_if` on 4+ steps to encode two paths, split the pipeline. The one exception worth considering is an *engine-level* `on_error_pipeline` hook — configuration, not a step type.

**Wait/Gate.** *For*: market-open waits, human-approval waits keep the run atomic with contiguous audit. *Against*: a paused pipeline is a liability in a desktop app the user can close; its state must live in the DB, so it's already two pipelines with handoff. **Verdict: APScheduler handles timing; human approval is a separate workflow.** Schedule runs after market open; make the first Fetch an *assertion* ("market is open, abort otherwise"), not a wait. For approval, split into `propose` (creates an `approval_request`, notifies) and `execute` (reads approved request). Short in-pipeline delays for rate-limit cooldowns belong in the HTTP client (tenacity delay), not the step taxonomy.

---

## 6. If we do one thing per topic

- **Data integrity.** Deep-copy the StepContext boundary and set `pd.options.mode.copy_on_write = True` globally. One afternoon of work; eliminates an entire class of silent corruption that `frozen=True` alone doesn't prevent.
- **Concurrency.** Ban `asyncio.wait_for` in favor of `async with asyncio.timeout():`, and wrap every commit in `asyncio.shield()`. Write audit rows in the same transaction as business writes.
- **Security.** Ship the dual-connection SQL sandbox. Everything else (Jinja autoescape, EmailMessage, URL allowlist) is important but cheap to retrofit; SQL authorizer hardening has the largest blast radius and the most subtle bypasses.
- **Operational.** Adopt the SQLCipher raw-key unlock-once pattern with `asyncio.to_thread`. Fixes the 200–500 ms event-loop stall that is currently cascading into the cancellation bugs and making every other async issue worse.
- **DI / service layer.** Refactor 8 kwargs into frozen `Infra` and `RunContext` dataclasses. Do not adopt a DI container. Two hours of work; makes the scope distinction visible in the type system; zero new dependencies.
- **Saga.** Do not build one. Ship idempotent Send + two-phase audit + "Unsent reports" GUI inbox.
- **Testing.** Write Pydantic contracts at every stage boundary with `extra='forbid'`, `strict=True`, `AwareDatetime`, `condecimal`. One discipline catches provider drift, Decimal precision, and timezone bugs.
- **Observability.** Stay on structlog + contextvars; add a `pipeline_run_events` append-only table that the Electron GUI queries. Skip OpenTelemetry until you have remote telemetry or a second process.
- **Resilience.** Provider health log surfaced as GUI banner, not a circuit breaker. The user is the ops team; do not hide information from them with an automated state machine.
- **Error handling.** One `failed_records` table + an Electron "Errors" inbox view with per-record Replay. That *is* the DLQ, stripped of its vocabulary and its assumption of a separate ops team.
- **Gap analysis.** Ship assertion-kind Transforms with pre-Send halt-on-fail. It is the most under-weighted gap and the most user-visible failure mode in a financial app.

---

## 7. Anti-patterns for desktop apps

**OpenTelemetry with a local file exporter.** OTel's value proposition is standardized wire format to a distributed backend. With no collector, you get a second log stream nobody opens, plus 5–15 MB of wheels in your Electron bundle (`opentelemetry-sdk`, `protobuf`, optionally `grpcio`) and Elastic's own overhead benchmarks show non-trivial instrumentation cost. In a single-process sequential pipeline, a nested structlog event tree gives you the same insight with code you already own.

**Circuit breakers with shared state.** pybreaker/purgatory/aiobreaker are well-designed for multi-worker systems where breaker state must be shared (Redis backend is the tell). Zorivest has one user, one process, no concurrent clients. Tenacity already caps per-call retries. The "provider has failed last N runs" signal the user actually wants is a health-log row, not a half-open probing state machine.

**Saga compensation for non-transactional report generation.** Richardson's saga targets distributed consistency across services with separate databases. Zorivest has one SQLCipher DB. "Un-rendering" a validly-generated PDF on Send failure destroys evidence the user wants. Use an idempotency key (which the schema already has) and at-least-once retry semantics — exactly what event-driven delivery-guarantee literature prescribes.

**Transactional outbox with polling relay.** The outbox pattern solves the dual-write problem when two different systems must stay consistent. Inside one process talking to one DB, "commit the audit row first, then call SMTP, then commit the send-confirmed row" is sufficient. Spinning up a polling worker inside a single-process app to relay from an outbox table is scheduler-inside-a-scheduler.

**Dead letter queue with an assumed ops team.** Hohpe & Woolf's DLQ presumes an async messaging system with a separate ops consumer. A desktop user opening SQLCipher with DB Browser is not the target. The concept survives — keep the table — but the vocabulary and the mental model of "someone else will look at this later" do not.

**DI containers for 8 dependencies and one scope boundary.** dishka, dependency-injector, and that-depends solve real problems at 20+ providers, multi-tenant scoping, or plugin-loaded services. Adopted at this scale, they introduce runtime resolution, magic wiring, and a second mental model over plain Python types — paying costs for benefits you will not realize until growth you may never have.

**Message queues and distributed workers for a 50-call/run workload.** Introducing Redis/Kafka/RabbitMQ to "decouple the fetcher from the renderer" is the canonical desktop-to-cloud anti-pattern. A single-process `asyncio` pipeline with a TaskGroup and a rate limiter is the correct implementation at this scale; the coordination primitive is the event loop, not a broker.

**Kubernetes / containerization of the desktop runtime.** PyInstaller/Electron/briefcase bundles, not Docker images. USB-drive portability requires filesystem-native paths and a single SQLCipher file — container runtimes fight this directly.

**Cloud-metadata-inspired configuration (Vault, Consul, etcd).** Pydantic Settings reading from env + an encrypted row in SQLCipher is sufficient. Secrets management in a single-user desktop app is the OS keychain (`keyring` library), not a distributed secret store.

**Automated remediation without user consent.** In a NOC context, auto-trip-and-skip is correct because no human is watching. In desktop, the user clicked "Run" and is looking at the GUI right now. Every automated decision the app makes without asking is a decision the user cannot learn from or override. Err toward visible, overridable, logged prompts.

---

## Closing note on epistemics

Several findings here are high-confidence from primary docs (SQLCipher KDF cost, WAL durability semantics, APScheduler misfire behavior, OWASP SSRF guidance, Jinja2 autoescape default, `datetime.utcnow` deprecation). Others are adversarial judgement calls where the answer depends on product priorities not in scope (assertion severity thresholds, exact retry windows, whether SpamAssassin's deliverability score matters). Where the review pushed back against a pattern — OTel, saga, DI containers, circuit breakers, DLQ — the argument is not that these patterns are wrong; it is that their value proposition does not survive the single-process, single-user, ~50-call/run desktop context. If Zorivest's scope changes toward multi-process, multi-tenant, or server-hosted operation, several of these verdicts should be revisited immediately. The highest-leverage changes — StepContext immutability, SQL sandbox hardening, SQLCipher raw-key pattern, assertion-kind gates, and the `Infra`/`RunContext` refactor — are independent of scale assumptions and should proceed regardless.
