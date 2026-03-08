# Logging Infrastructure — Implementation Plan

> **Project slug:** `logging-infrastructure`
> **Date:** 2026-03-07
> **MEUs:** MEU-2A → MEU-3A → MEU-1A (dependency order)
> **Build-plan source:** [01a-logging.md](../../../build-plan/01a-logging.md)
> **Phase:** 1A (P0 — parallel with Phase 1)
> **Dependencies:** None (stdlib only)

---

## Reflection Rules Applied

From `2026-03-07-portfolio-display-review-reflection.md`:

- **RULE-1:** Update `BUILD_PLAN.md` and plan `task.md` immediately after each MEU gate pass
- **RULE-2:** Verify truth-table citations point to rows, not prose definitions

---

## Project Scope

| In Scope | Out of Scope |
|---|---|
| New `packages/infrastructure/` package | Settings DB integration (Phase 2) |
| All `zorivest_infra/logging/` modules | GUI settings page (Phase 6) |
| Unit tests for all 3 MEUs | Integration tests with DB |
| `BUILD_PLAN.md` status updates | Phase 2+ modules |
| Root `pyproject.toml` workspace update | |
| MEU registry updates | |

> [!NOTE]
> `01a-logging.md:860` states "No `pyproject.toml` changes needed for this phase" — this refers to **no new external dependencies** (stdlib only). Creating the `packages/infrastructure/pyproject.toml` package file and adding `zorivest-infra` to root `pyproject.toml` sources is infrastructure work, not a dependency addition.

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|---|---|---|---|---|
| T1 | Create `packages/infrastructure/` package scaffold + update root `pyproject.toml` | coder | `packages/infrastructure/pyproject.toml`, `__init__.py` files, root `pyproject.toml` `[tool.uv.sources]` entry | `uv sync && uv run python -c "import zorivest_infra"` | ⬜ |
| T2 | MEU-2A: Write tests for FeatureFilter, CatchallFilter, JsonFormatter (Red) | coder | `tests/unit/test_logging_filters.py`, `tests/unit/test_logging_formatter.py` | `uv run pytest tests/unit/test_logging_filters.py tests/unit/test_logging_formatter.py -x --tb=short -v` — all FAIL | ⬜ |
| T3 | MEU-2A: Implement filters + formatter (Green) | coder | `filters.py`, `formatters.py` | `uv run pytest tests/unit/test_logging_filters.py tests/unit/test_logging_formatter.py -x --tb=short -v` — all PASS | ⬜ |
| T4 | MEU-2A: Quality gate | tester | Zero errors | `uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/logging/filters.py packages/infrastructure/src/zorivest_infra/logging/formatters.py` | ⬜ |
| T4a | MEU-2A: Update `BUILD_PLAN.md` + MEU registry → 🟡 | coder | MEU-2A → 🟡 ready_for_review | `rg "MEU-2A.*🟡" .agent/context/meu-registry.md` | ⬜ |
| T5 | MEU-2A: Create handoff 010 | coder | `010-2026-03-07-logging-filters-bp01as4.md` | `rg -c "^##" .agent/context/handoffs/010-2026-03-07-logging-filters-bp01as4.md` — ≥7 sections | ⬜ |
| T5a | MEU-2A: Codex validation | reviewer | Codex appends to handoff 010 | `rg "approved\|changes_required" .agent/context/handoffs/010-2026-03-07-logging-filters-bp01as4.md` — shows `approved` | ⬜ |
| T6 | MEU-2A: Update `BUILD_PLAN.md` + MEU registry → ✅ | coder | MEU-2A → ✅ approved | `rg "MEU-2A.*✅ approved" .agent/context/meu-registry.md` | ⬜ |
| T7 | MEU-3A: Write tests for RedactionFilter (Red) | coder | `tests/unit/test_logging_redaction.py` | `uv run pytest tests/unit/test_logging_redaction.py -x --tb=short -v` — all FAIL | ⬜ |
| T8 | MEU-3A: Implement RedactionFilter (Green) | coder | `redaction.py` | `uv run pytest tests/unit/test_logging_redaction.py -x --tb=short -v` — all PASS | ⬜ |
| T9 | MEU-3A: Quality gate | tester | Zero errors | `uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/logging/redaction.py` | ⬜ |
| T9a | MEU-3A: Update `BUILD_PLAN.md` + MEU registry → 🟡 | coder | MEU-3A → 🟡 ready_for_review | `rg "MEU-3A.*🟡" .agent/context/meu-registry.md` | ⬜ |
| T10 | MEU-3A: Create handoff 011 | coder | `011-2026-03-07-logging-redaction-bp01as4.md` | `rg -c "^##" .agent/context/handoffs/011-2026-03-07-logging-redaction-bp01as4.md` — ≥7 sections | ⬜ |
| T10a | MEU-3A: Codex validation | reviewer | Codex appends to handoff 011 | `rg "approved\|changes_required" .agent/context/handoffs/011-2026-03-07-logging-redaction-bp01as4.md` — shows `approved` | ⬜ |
| T11 | MEU-3A: Update `BUILD_PLAN.md` + MEU registry → ✅ | coder | MEU-3A → ✅ approved | `rg "MEU-3A.*✅ approved" .agent/context/meu-registry.md` | ⬜ |
| T12 | MEU-1A: Write tests for LoggingManager (Red) | coder | `tests/unit/test_logging_config.py` | `uv run pytest tests/unit/test_logging_config.py -x --tb=short -v` — all FAIL | ⬜ |
| T13 | MEU-1A: Implement LoggingManager + config + bootstrap (Green) | coder | `config.py`, `bootstrap.py`, `__init__.py` exports | `uv run pytest tests/unit/test_logging_config.py -x --tb=short -v` — all PASS | ⬜ |
| T14 | MEU-1A: Quality gate | tester | Zero errors | `uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/logging/config.py` | ⬜ |
| T14a | MEU-1A: Update `BUILD_PLAN.md` + MEU registry → 🟡 | coder | MEU-1A → 🟡 ready_for_review | `rg "MEU-1A.*🟡" .agent/context/meu-registry.md` | ⬜ |
| T15 | MEU-1A: Create handoff 012 | coder | `012-2026-03-07-logging-manager-bp01as1+2+3.md` | `rg -c "^##" .agent/context/handoffs/012-2026-03-07-logging-manager-bp01as1+2+3.md` — ≥7 sections | ⬜ |
| T15a | MEU-1A: Codex validation | reviewer | Codex appends to handoff 012 | `rg "approved\|changes_required" .agent/context/handoffs/012-2026-03-07-logging-manager-bp01as1+2+3.md` — shows `approved` | ⬜ |
| T16 | MEU-1A: Update `BUILD_PLAN.md` + MEU registry → ✅ | coder | MEU-1A → ✅ approved, Phase 1A → ✅ | `rg "MEU-1A.*✅ approved" .agent/context/meu-registry.md` | ⬜ |
| T17 | Review/update `BUILD_PLAN.md` hub for drift | reviewer | Verify no stale references | `uv run python tools/validate_build_plan.py 2>$null; rg -n "logging-infrastructure\|Phase 1A" docs/BUILD_PLAN.md` | ⬜ |
| T18 | Create reflection file | tester | `docs/execution/reflections/2026-03-07-logging-infrastructure-reflection.md` | `Test-Path docs/execution/reflections/2026-03-07-logging-infrastructure-reflection.md` | ⬜ |
| T19 | Update metrics row | tester | `docs/execution/metrics.md` (append row) | `rg "logging-infrastructure" docs/execution/metrics.md` | ⬜ |
| T20 | Save session state | orchestrator | Pomera note saved | `pomera_notes search --search_term "Memory/Session/Zorivest-logging-infrastructure*"` | ⬜ |

**Role progression per MEU:** orchestrator (gate) → coder (FIC + Red + Green) → tester (quality gate) → coder (🟡 state update + handoff) → reviewer/Codex (validation) → coder (✅ state update)

---

## Spec Sufficiency — MEU-2A (Logging Filters + JsonFormatter)

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| FeatureFilter accepts records matching logger prefix | Spec | [01a:417–425](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| FeatureFilter rejects non-matching records | Spec | [01a:417–425](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| CatchallFilter accepts non-feature records | Spec | [01a:428–444](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| CatchallFilter rejects known-feature records | Spec | [01a:428–444](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| JsonFormatter outputs valid single-line JSON | Spec | [01a:467–499](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Standard fields: timestamp, level, logger, thread, module, funcName, lineno, message | Spec | [01a:476–487](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Arbitrary extras preserved via deny-list approach | Spec | [01a:468–472, 488–491](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Exception info serialized (type, message, traceback) | Spec | [01a:493–498](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| _RESERVED_ATTRS deny set matches spec | Spec | [01a:458–464](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Timestamp in ISO-8601 UTC | Spec | [01a:477–479](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |

### FIC — MEU-2A

| AC | Description | Source |
|---|---|---|
| AC-1 | `FeatureFilter("zorivest.trades")` accepts `LogRecord(name="zorivest.trades.service")` | Spec |
| AC-2 | `FeatureFilter("zorivest.trades")` rejects `LogRecord(name="zorivest.marketdata")` | Spec |
| AC-3 | `CatchallFilter(known_prefixes)` accepts record whose name matches no prefix | Spec |
| AC-4 | `CatchallFilter(known_prefixes)` rejects record whose name matches a known prefix | Spec |
| AC-5 | `JsonFormatter.format()` returns valid JSON string (parseable by `json.loads`) | Spec |
| AC-6 | Output JSON contains all 8 standard fields | Spec |
| AC-7 | Non-reserved extras (e.g., `record.trade_id`) appear in output JSON | Spec |
| AC-8 | Reserved attrs and underscore-prefixed attrs excluded from output | Spec |
| AC-9 | Exception info serialized as `exception.{type, message, traceback}` | Spec |
| AC-10 | Timestamp uses UTC timezone in ISO-8601 format | Spec |

---

## Spec Sufficiency — MEU-3A (Logging Redaction)

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| 13 regex patterns with specified replacements | Spec | [01a:519–563](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Sensitive key denylist (18 keys) | Spec | [01a:566–572](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Layer 1: regex applied to `record.msg` | Spec | [01a:574–575](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Layer 1: regex applied to string `record.args` | Spec | [01a:600–611](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Layer 2: denylist applied to dict extras on record | Spec | [01a:578–591](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Recursive dict redaction | Spec | [01a:613–621](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Filter always returns True (never drops records) | Spec | [01a:592](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |

### FIC — MEU-3A

| AC | Description | Source |
|---|---|---|
| AC-1 | URL query param `apikey=SECRET` redacted to `apikey=[REDACTED]` | Spec |
| AC-2 | Bearer token `Bearer eyJ...` redacted to `Bearer [REDACTED]` | Spec |
| AC-3 | Fernet `ENC:gAAAA...` redacted to `[ENCRYPTED_VALUE]` | Spec |
| AC-4 | JWT `eyJhbGci...` redacted to `[JWT_REDACTED]` | Spec |
| AC-5 | AWS access key `AKIA...` redacted to `[AWS_KEY_REDACTED]` | Spec |
| AC-6 | Connection string credentials redacted | Spec |
| AC-7 | Credit card PAN `4111-2222-...` redacted to `[CC_REDACTED]` | Spec |
| AC-8 | SSN `123-45-6789` redacted to `[SSN_REDACTED]` | Spec |
| AC-9 | Zorivest API key `zrv_sk_...` redacted to `[ZRV_KEY_REDACTED]` | Spec |
| AC-10 | Dict key `password` → value replaced with `[REDACTED]` | Spec |
| AC-11 | Dict key `api_key` → value replaced regardless of format | Spec |
| AC-12 | Nested dict values redacted recursively | Spec |
| AC-13 | Filter always returns True (`record.msg` modified in-place) | Spec |
| AC-14 | Non-reserved extras on LogRecord scanned and redacted | Spec |

---

## Spec Sufficiency — MEU-1A (Logging Manager)

| Behavior / Contract | Source Type | Source | Resolved? |
|---|---|---|---|
| FEATURES registry (12 features) | Spec | [01a:267–280](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| `get_feature_logger()` raises ValueError for unknown features | Spec | [01a:287–291](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| `get_log_directory()` resolves per-platform | Spec | [01a:294–304](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| `bootstrap()` creates bootstrap.jsonl + root handler | Spec | [01a:318–330](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| `configure_from_settings()` builds queue pipeline | Spec | [01a:332–394](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Per-feature RotatingFileHandler with filter routing | Spec | [01a:344–362](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Catchall handler routes to misc.jsonl | Spec | [01a:364–376](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| QueueListener with `respect_handler_level=True` | Spec | [01a:379–380](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| `update_feature_level()` runtime no-restart change | Spec | [01a:396–401](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| `shutdown()` stops listener | Spec | [01a:403–406](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Thread-safe concurrent logging produces valid JSONL | Spec | [01a:807–840](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |
| Default values: INFO, 10 MB, 5 backups | Spec | [01a:282–284](file:///p:/zorivest/docs/build-plan/01a-logging.md) | ✅ |

### FIC — MEU-1A

| AC | Description | Source |
|---|---|---|
| AC-1 | FEATURES dict contains exactly 12 entries with correct prefixes | Spec |
| AC-2 | `get_feature_logger("trades")` returns logger named `zorivest.trades` | Spec |
| AC-3 | `get_feature_logger("unknown")` raises `ValueError` | Spec |
| AC-4 | `get_log_directory()` returns platform-appropriate path | Spec |
| AC-5 | `bootstrap()` creates `bootstrap.jsonl` in log directory | Spec |
| AC-6 | After `bootstrap()`, logging to `zorivest.app` writes to bootstrap.jsonl | Spec |
| AC-7 | `configure_from_settings({})` creates per-feature JSONL files when logged to | Spec |
| AC-8 | Feature routing: `zorivest.trades` logs appear in `trades.jsonl`, not in other files | Spec |
| AC-9 | Catchall: `some.random.logger` logs appear in `misc.jsonl` | Spec |
| AC-10 | `update_feature_level("trades", "WARNING")` gates INFO messages from `trades.jsonl` | Spec |
| AC-11 | `shutdown()` stops the QueueListener cleanly | Spec |
| AC-12 | Concurrent logging from 3 threads produces valid JSONL (no interleaving) | Spec |
| AC-13 | Settings key `logging.trades.level` = "WARNING" is respected by configure | Spec |
| AC-14 | Default rotation: 10 MB, 5 backups per file | Spec |

---

## Proposed Changes

### Package Scaffold (T1)

#### [NEW] pyproject.toml
`packages/infrastructure/pyproject.toml` — Hatchling package config for `zorivest-infra`, stdlib only.

#### [NEW] __init__.py (package)
`packages/infrastructure/src/zorivest_infra/__init__.py` — Empty package marker.

#### [MODIFY] pyproject.toml (root)
`pyproject.toml` — Add `zorivest-infra` to `[tool.uv.sources]` and `[project.dependencies]`. Note: `[tool.uv.workspace].members = ["packages/*"]` already auto-discovers the new package.

---

### MEU-2A: Filters + Formatter (T2–T6)

#### [NEW] filters.py
`packages/infrastructure/src/zorivest_infra/logging/filters.py` — `FeatureFilter` and `CatchallFilter`.

#### [NEW] formatters.py
`packages/infrastructure/src/zorivest_infra/logging/formatters.py` — `JsonFormatter` with deny-list extras approach.

#### [NEW] test_logging_filters.py
`tests/unit/test_logging_filters.py` — Tests for FeatureFilter (AC-1, AC-2) and CatchallFilter (AC-3, AC-4).

#### [NEW] test_logging_formatter.py
`tests/unit/test_logging_formatter.py` — Tests for JsonFormatter (AC-5 through AC-10).

---

### MEU-3A: Redaction (T7–T11)

#### [NEW] redaction.py
`packages/infrastructure/src/zorivest_infra/logging/redaction.py` — `RedactionFilter` with 13 regex patterns + key denylist.

#### [NEW] test_logging_redaction.py
`tests/unit/test_logging_redaction.py` — Tests for all 14 acceptance criteria.

---

### MEU-1A: Manager (T12–T16)

#### [NEW] config.py
`packages/infrastructure/src/zorivest_infra/logging/config.py` — `LoggingManager`, `FEATURES`, `get_feature_logger()`, `get_log_directory()`.

#### [NEW] bootstrap.py
`packages/infrastructure/src/zorivest_infra/logging/bootstrap.py` — Usage documentation module (docstring only, no executable code).

#### [NEW] __init__.py (logging)
`packages/infrastructure/src/zorivest_infra/logging/__init__.py` — Public API exports.

#### [NEW] test_logging_config.py
`tests/unit/test_logging_config.py` — Tests for LoggingManager lifecycle, feature routing, thread safety (AC-1 through AC-14).

---

### Hub/Registry Updates (T4a/T6, T9a/T11, T14a/T16, T17)

#### [MODIFY] BUILD_PLAN.md
`docs/BUILD_PLAN.md` — Phase 1A status → ✅ Complete, MEU-1A/2A/3A → ✅, summary row update.

#### [MODIFY] meu-registry.md
`.agent/context/meu-registry.md` — 3 status changes ⬜ → 🟡 → ✅ approved.

---

## Verification Plan

### Per-MEU Gate

```powershell
# MEU-2A gate (runs pyright + ruff + pytest + anti-placeholder)
uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/logging/filters.py packages/infrastructure/src/zorivest_infra/logging/formatters.py

# MEU-3A gate
uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/logging/redaction.py

# MEU-1A gate
uv run python tools/validate_codebase.py --scope meu --files packages/infrastructure/src/zorivest_infra/logging/config.py
```

### Phase Gate (after all 3 MEUs approved)

```powershell
uv run python tools/validate_codebase.py
```

### Anti-Placeholder Scan

```powershell
rg "TODO|FIXME|NotImplementedError" packages/infrastructure/
```

### Manual Verification

No manual verification needed — all components are pure Python stdlib with no external services, DB, or GUI dependencies.

---

## Handoff File Paths

Continuing from highest existing sequence (009):

| MEU | Handoff Path |
|---|---|
| MEU-2A | `.agent/context/handoffs/010-2026-03-07-logging-filters-bp01as4.md` |
| MEU-3A | `.agent/context/handoffs/011-2026-03-07-logging-redaction-bp01as4.md` |
| MEU-1A | `.agent/context/handoffs/012-2026-03-07-logging-manager-bp01as1+2+3.md` |

## Post-Project Artifacts

| Artifact | Path | Owner | Timing |
|----------|------|-------|--------|
| Reflection | `docs/execution/reflections/2026-03-07-logging-infrastructure-reflection.md` | tester | After Codex validation |
| Metrics row | `docs/execution/metrics.md` (append row) | tester | After Codex validation |
| Session state | `pomera_notes` title: `Memory/Session/Zorivest-logging-infrastructure-2026-03-07` | orchestrator | End of session |

---

## Stop Conditions

- **Stop for human:** If any behavior not covered by spec is discovered during implementation
- **Stop on Red failure:** If tests fail for reasons unrelated to missing implementation (import errors, fixture issues)
- **Stop on quality gate failure:** If `pyright` or `ruff` surface issues requiring design changes
- **Stop on thread safety issues:** If concurrent logging test reveals non-deterministic failures
