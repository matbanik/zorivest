# Project: portfolio-display-review

Final Phase 1 Domain Layer MEUs: portfolio balance computation, display mode formatting, and account review workflow.

**Project slug:** `portfolio-display-review`
**MEUs:** MEU-9 → MEU-10 → MEU-11
**Build plan:** [01-domain-layer.md](file:///p:/zorivest/docs/build-plan/01-domain-layer.md) §1.2 + [domain-model-reference.md](file:///p:/zorivest/docs/build-plan/domain-model-reference.md)
**Date:** 2026-03-07

---

## Standing Project Rules

Per human decision (2026-03-07, from domain-entities-ports v3 plan):

1. **Full contract always.** Entities/commands implement the complete field set from canonical docs. No narrowing, no P0 subsets, no deferrals.
2. **Validators always.** Dataclasses include validation sourced from canonical docs. Document each rule in the FIC with its source.

## Design Rules (from prior reflection)

Per `2026-03-07-domain-entities-ports-reflection.md`:

- **RULE-1:** Record per-MEU `tests_passing` count, not final project total.
- **RULE-2:** Mark reflection/metrics as "(provisional)" when created before Codex validation.
- **RULE-3:** Use `write_to_file` with `Overwrite=true` for small structured files to avoid CRLF/LF corruption.

---

## Task Table

| # | Task | Owner Role | Deliverable | Validation | Status |
|---|------|-----------|-------------|------------|--------|
| 0 | Gate: confirm all deps ✅ | orchestrator | MEU-1–8 approved in registry | `rg "MEU-[1-8]\b.*✅ approved" .agent/context/meu-registry.md` — 8 matches | ✅ |
| 1 | MEU-9 FIC + Red tests | coder | `tests/unit/test_portfolio_balance.py` | `uv run pytest tests/unit/test_portfolio_balance.py -x --tb=short -m "unit" -v` — all FAIL | ✅ |
| 2 | MEU-9 Green implementation | coder | `domain/portfolio_balance.py` | `uv run pytest tests/unit/test_portfolio_balance.py -x --tb=short -m "unit" -v` — all PASS | ✅ |
| 3 | MEU-9 quality gate | tester | Zero errors | `uv run pyright packages/core/src/zorivest_core/domain/portfolio_balance.py` + `uv run ruff check packages/core/src/zorivest_core/domain/portfolio_balance.py` + `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/domain/portfolio_balance.py \|\| Write-Output "Anti-placeholder: clean"` | ✅ |
| 4 | MEU-9 handoff | coder | `007-2026-03-07-portfolio-balance-bp01s1.2.md` | `rg -c "^##" .agent/context/handoffs/007-2026-03-07-portfolio-balance-bp01s1.2.md` — ≥7 sections | ✅ |
| 5 | MEU-9 validation | reviewer | Codex appends to handoff 007 | `rg "approved\|changes_required" .agent/context/handoffs/007-2026-03-07-portfolio-balance-bp01s1.2.md` — shows `approved` | ✅ |
| 6 | MEU-10 FIC + Red tests | coder | `tests/unit/test_display_mode.py` | `uv run pytest tests/unit/test_display_mode.py -x --tb=short -m "unit" -v` — all FAIL | ✅ |
| 7 | MEU-10 Green implementation | coder | `domain/display_mode.py` | `uv run pytest tests/unit/test_display_mode.py -x --tb=short -m "unit" -v` — all PASS | ✅ |
| 8 | MEU-10 quality gate | tester | Zero errors | `uv run pyright packages/core/src/zorivest_core/domain/display_mode.py` + `uv run ruff check packages/core/src/zorivest_core/domain/display_mode.py` + `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/domain/display_mode.py \|\| Write-Output "Anti-placeholder: clean"` | ✅ |
| 9 | MEU-10 handoff | coder | `008-2026-03-07-display-mode-bp01s1.2.md` | `rg -c "^##" .agent/context/handoffs/008-2026-03-07-display-mode-bp01s1.2.md` — ≥7 sections | ✅ |
| 10 | MEU-10 validation | reviewer | Codex appends to handoff 008 | `rg "approved\|changes_required" .agent/context/handoffs/008-2026-03-07-display-mode-bp01s1.2.md` — shows `approved` | ✅ |
| 11 | MEU-11 FIC + Red tests | coder | `tests/unit/test_account_review.py` | `uv run pytest tests/unit/test_account_review.py -x --tb=short -m "unit" -v` — all FAIL | ✅ |
| 12 | MEU-11 Green implementation | coder | `domain/account_review.py` | `uv run pytest tests/unit/test_account_review.py -x --tb=short -m "unit" -v` — all PASS | ✅ |
| 13 | MEU-11 quality gate | tester | Zero errors | `uv run pyright packages/core/src/zorivest_core/domain/account_review.py` + `uv run ruff check packages/core/src/zorivest_core/domain/account_review.py` + `rg "TODO\|FIXME\|NotImplementedError" packages/core/src/zorivest_core/domain/account_review.py \|\| Write-Output "Anti-placeholder: clean"` | ✅ |
| 14 | MEU-11 handoff | coder | `009-2026-03-07-account-review-bp01s1.2.md` | `rg -c "^##" .agent/context/handoffs/009-2026-03-07-account-review-bp01s1.2.md` — ≥7 sections | ✅ |
| 15 | MEU-11 validation | reviewer | Codex appends to handoff 009 | `rg "approved\|changes_required" .agent/context/handoffs/009-2026-03-07-account-review-bp01s1.2.md` — shows `approved` | ✅ |
| 16 | Post-project: reflection + metrics (after all Codex validations) | tester | Updated artifacts | `Test-Path docs/execution/reflections/2026-03-07-portfolio-display-review-reflection.md` + `rg "portfolio-display-review" docs/execution/metrics.md` | ✅ |
| 17 | Post-project: session state | orchestrator | Pomera note saved | `pomera_notes search --search_term "Memory/Session/Zorivest-portfolio-display-review*"` | ✅ |

**Role progression per MEU:** orchestrator (gate) → coder (FIC + Red + Green + handoff) → tester (quality gate) → reviewer/Codex (validation appended to handoff)

---

## Proposed Changes

### MEU-9: Portfolio Balance (bp01 §3a)

#### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| `TotalPortfolioBalance` as sum of latest balances | Spec | [domain-model-ref lines 115–122](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | "Computed: SUM of latest balance for every Account" |
| Includes negative balances (credit cards, loans) | Spec | [domain-model-ref line 117](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Explicit: "includes negative balances" |
| Used as denominator for percent mode | Spec | [domain-model-ref line 121](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | "Used as: Reference denominator for percentage mode" |
| Updated on any balance snapshot change | Spec | [domain-model-ref line 122](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | "Updated: Whenever any account balance snapshot changes" |
| Per-account latest balance extraction | Local Canon | [entities.py line 88](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py) — `Account.balance_snapshots: list[BalanceSnapshot]` | ✅ | Access via `balance_snapshots[-1]` or max by datetime |
| Pure fn: `calculate_total_portfolio_balance(accounts) → TotalPortfolioBalance` | Local Canon | [build-priority-matrix.md line 15](file:///p:/zorivest/docs/build-plan/build-priority-matrix.md) "pure fn: sum all latest balances" | ✅ | Stateless, no UoW |

No gaps require web research or human decision.

#### FIC — Feature Intent Contract

Pure function that computes total portfolio balance from a list of accounts. Sourced from [domain-model-reference.md lines 115–122](file:///p:/zorivest/docs/build-plan/domain-model-reference.md).

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `TotalPortfolioBalance` frozen dataclass: `total` (Decimal), `per_account` (dict[str, Decimal] — account_id → latest balance), `computed_at` (datetime) | Local Canon: derived from computed concept at [domain-model-ref lines 115–122](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-2 | `calculate_total_portfolio_balance(accounts: list[Account]) → TotalPortfolioBalance` — sums the latest `BalanceSnapshot.balance` for each account | Local Canon: derived from "SUM of latest balance" at [domain-model-ref line 116](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-3 | Accounts with empty `balance_snapshots` list contribute `Decimal("0")` to the total | Local Canon: no snapshots = no balance data |
| AC-4 | Accounts with negative latest balances (credit cards, loans) are included in the sum | Spec: [domain-model-ref line 117](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-5 | "Latest" is determined by `max(snapshot.datetime)` among the account's snapshots, not list position | Local Canon: chronological correctness |
| AC-6 | Empty accounts list returns `total=Decimal("0")` with empty `per_account` dict | Local Canon: null-safe design |
| AC-7 | Module imports only from `__future__`, `dataclasses`, `datetime`, `decimal`, `zorivest_core.domain.entities` | Local Canon: import surface pattern from MEU-1–8 |

#### [NEW] [portfolio_balance.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/portfolio_balance.py)

- `TotalPortfolioBalance` frozen dataclass
- `calculate_total_portfolio_balance(accounts: list[Account]) → TotalPortfolioBalance`

#### [NEW] [test_portfolio_balance.py](file:///p:/zorivest/tests/unit/test_portfolio_balance.py)

- ~8 test functions covering AC-1 through AC-7

---

### MEU-10: Display Mode (bp01 §3b)

#### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Three display flags: `hide_dollars`, `hide_percentages`, `percent_mode` | Spec | [domain-model-ref lines 124–157](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Explicit state table |
| Dollar masking: `"••••••"` when hide_dollars True | Spec | [domain-model-ref lines 149–156](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Truth table rows 3–5 |
| Percentage masking: `"••%"` when hide_percentages True | Spec | [domain-model-ref lines 149–156](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Truth table row 4 |
| Percent mode: show `$X (Y%)` relative to TotalPortfolioBalance | Spec | [domain-model-ref lines 135–140](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Examples in spec |
| 6-state combination table | Spec | [domain-model-ref lines 148–156](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Full truth table |
| `DisplayModeFlag` enum already exists | Local Canon | [enums.py lines 41–45](file:///p:/zorivest/packages/core/src/zorivest_core/domain/enums.py) | ✅ | Built in MEU-2 |

No gaps require web research or human decision.

#### FIC — Feature Intent Contract

Display mode formatting functions. Sourced from [domain-model-reference.md lines 113–159](file:///p:/zorivest/docs/build-plan/domain-model-reference.md).

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `DisplayMode` frozen dataclass: `hide_dollars` (bool, default False), `hide_percentages` (bool, default False), `percent_mode` (bool, default False) | Local Canon: derived from toggle definitions at [domain-model-ref lines 126–135](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-2 | `format_dollar(amount: Decimal, mode: DisplayMode, total_portfolio: Decimal \| None = None) → str` — returns formatted dollar string (e.g., `"$437,903"`) | Local Canon: derived from truth table at [domain-model-ref line 151](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-3 | When `hide_dollars=True`, `format_dollar` returns `"••••••"` regardless of amount | Spec: truth table rows at [domain-model-ref lines 149–156](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) (rows 3–5: `✗` in `$` visible → `••••••`) |
| AC-4 | When `percent_mode=True` and `total_portfolio` provided, `format_dollar` appends ` (X.XX%)` to dollar output | Spec: [domain-model-ref lines 136–140](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-5 | When `hide_dollars=True` and `percent_mode=True`, returns `"•••••• (X.XX%)"` | Spec: [domain-model-ref line 153](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-6 | When `hide_percentages=True`, any percentage part becomes `"••%"` | Spec: truth table rows at [domain-model-ref lines 149–156](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) (row 4: `✗` in `%` visible → `••%`) |
| AC-7 | `format_percentage(value: Decimal, mode: DisplayMode) → str` — returns `"X.XX%"` or `"••%"` if hidden | Local Canon: derived from masking semantics at [domain-model-ref lines 131–133](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-8 | All 6 state combinations from the truth table produce correct output | Spec: [domain-model-ref lines 148–156](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-9 | `format_dollar` with `total_portfolio=Decimal("0")` and `percent_mode=True` shows `"$X (N/A%)"` instead of division-by-zero | Local Canon: defensive math |
| AC-10 | Module imports only from `__future__`, `dataclasses`, `decimal`, `zorivest_core.domain.enums` | Local Canon: import surface pattern |

#### [NEW] [display_mode.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/display_mode.py)

- `DisplayMode` frozen dataclass
- `format_dollar(amount, mode, total_portfolio) → str`
- `format_percentage(value, mode) → str`

#### [NEW] [test_display_mode.py](file:///p:/zorivest/tests/unit/test_display_mode.py)

- ~12 test functions covering AC-1 through AC-10 (including all 6 truth table combinations)

---

### MEU-11: Account Review Workflow (bp01 §3c)

#### Spec Sufficiency

| Behavior / Contract | Source Type | Source | Resolved? | Notes |
|---|---|---|---|---|
| Guided step-through process for all accounts | Spec | [domain-model-ref lines 161–207](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Full workflow diagram |
| BROKER accounts: API fetch option | Spec | [domain-model-ref line 198](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | "Offer API fetch button" |
| Non-BROKER: manual entry with last balance pre-filled | Spec | [domain-model-ref line 199](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | — |
| Dedup: log balance only if value changed | Spec | [domain-model-ref line 200](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Prevents snapshot spam |
| Skip moves to next without saving | Spec | [domain-model-ref line 201](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | — |
| Summary on completion: updated count, skipped count, new total | Spec | [domain-model-ref lines 186–195](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | Full summary UI |
| Account entity with `balance_snapshots`, `account_type` | Local Canon | [entities.py lines 75–88](file:///p:/zorivest/packages/core/src/zorivest_core/domain/entities.py) | ✅ | Built in MEU-3 |
| Priority P0 — core feature | Spec | [domain-model-ref line 207](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) | ✅ | — |

No gaps require web research or human decision.

#### FIC — Feature Intent Contract

Account review workflow domain logic. Sourced from [domain-model-reference.md lines 161–207](file:///p:/zorivest/docs/build-plan/domain-model-reference.md). This is the **pure domain logic** for the review process — the GUI/API presentation layer is built in later phases.

| AC | Description | Source |
|----|-------------|--------|
| AC-1 | `AccountReviewItem` frozen dataclass: `account_id` (str), `name` (str), `account_type` (AccountType), `institution` (str), `last_balance` (Decimal \| None), `last_balance_datetime` (datetime \| None), `supports_api_fetch` (bool) | Local Canon: derived from UI walkthrough at [domain-model-ref lines 170–176](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-2 | `AccountReviewResult` frozen dataclass: `account_id` (str), `action` (str — "updated" \| "skipped"), `old_balance` (Decimal \| None), `new_balance` (Decimal \| None) | Local Canon: derived from summary UI at [domain-model-ref lines 186–195](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-3 | `AccountReviewSummary` frozen dataclass: `total_accounts` (int), `updated_count` (int), `skipped_count` (int), `old_total` (Decimal), `new_total` (Decimal), `results` (list[AccountReviewResult]) | Local Canon: derived from summary UI at [domain-model-ref lines 186–195](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-4 | `prepare_review_checklist(accounts: list[Account]) → list[AccountReviewItem]` — builds the item list from accounts. BROKER type sets `supports_api_fetch=True` | Spec: [domain-model-ref lines 198–199](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-5 | `prepare_review_checklist` extracts last_balance and last_balance_datetime from most recent snapshot (max datetime), or None if no snapshots | Local Canon: chronological correctness |
| AC-6 | `apply_balance_update(account: Account, new_balance: Decimal, snapshot_datetime: datetime) → AccountReviewResult` — creates a new BalanceSnapshot and returns "updated" result | Local Canon: derived from "Update & Next" button at [domain-model-ref line 183](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-7 | `apply_balance_update` returns "skipped" result (no snapshot created) if `new_balance` equals the latest existing balance — dedup rule | Spec: [domain-model-ref line 200](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) "Balance only logged if value actually changed" |
| AC-8 | `skip_account(account: Account) → AccountReviewResult` — returns "skipped" result, no side effects | Spec: [domain-model-ref line 201](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-9 | `summarize_review(results: list[AccountReviewResult], accounts: list[Account]) → AccountReviewSummary` — aggregates counts and computes old/new totals | Local Canon: derived from summary UI at [domain-model-ref lines 186–195](file:///p:/zorivest/docs/build-plan/domain-model-reference.md) |
| AC-10 | Module imports only from `__future__`, `dataclasses`, `datetime`, `decimal`, `zorivest_core.domain.entities`, `zorivest_core.domain.enums` | Local Canon: import surface pattern |

> [!NOTE]
> **Scope boundary**: This MEU implements the pure domain logic for account review (prepare checklist, apply updates, summarize). The GUI presentation (wizard screens, keyboard shortcuts, progress bar) is Phase 6 ([06d-gui-accounts.md](file:///p:/zorivest/docs/build-plan/06d-gui-accounts.md)). The MCP tool (`get_account_review_checklist`) is Phase 5. The API fetch via TWS adapter is Phase 2+ (external_apis/ibkr_adapter.py).

#### [NEW] [account_review.py](file:///p:/zorivest/packages/core/src/zorivest_core/domain/account_review.py)

- `AccountReviewItem`, `AccountReviewResult`, `AccountReviewSummary` — frozen dataclasses
- `prepare_review_checklist(accounts) → list[AccountReviewItem]`
- `apply_balance_update(account, new_balance, snapshot_datetime) → AccountReviewResult`
- `skip_account(account) → AccountReviewResult`
- `summarize_review(results, accounts) → AccountReviewSummary`

#### [NEW] [test_account_review.py](file:///p:/zorivest/tests/unit/test_account_review.py)

- ~14 test functions covering AC-1 through AC-10

---

### State Management

#### [MODIFY] [meu-registry.md](file:///p:/zorivest/.agent/context/meu-registry.md)

- MEU-9, MEU-10, MEU-11 status updates as each completes

---

## Plan Location

Per `create-plan.md` §4:

```
docs/execution/plans/2026-03-07-portfolio-display-review/
├── implementation-plan.md   ← this file (source of truth)
└── task.md
```

## Handoff Naming

Continuing from highest existing sequence (006):

| Seq | Handoff Path |
|-----|-------------|
| 007 | `.agent/context/handoffs/007-2026-03-07-portfolio-balance-bp01s1.2.md` |
| 008 | `.agent/context/handoffs/008-2026-03-07-display-mode-bp01s1.2.md` |
| 009 | `.agent/context/handoffs/009-2026-03-07-account-review-bp01s1.2.md` |

## Post-Project Artifacts

| Artifact | Path | Owner | Timing |
|----------|------|-------|--------|
| Reflection | `docs/execution/reflections/2026-03-07-portfolio-display-review-reflection.md` | tester | After Codex validation (per `execution-session.md` §5) |
| Metrics row | `docs/execution/metrics.md` (append row) | tester | After Codex validation |
| Session state | `pomera_notes` title: `Memory/Session/Zorivest-portfolio-display-review-2026-03-07` | orchestrator | End of session |

---

## Verification Plan

### Per-MEU Gate

```powershell
# MEU-9
uv run pytest tests/unit/test_portfolio_balance.py -x --tb=short -m "unit" -v
uv run pytest tests/unit/ -x --tb=short -m "unit"
uv run pyright packages/core/src/zorivest_core/domain/portfolio_balance.py
uv run ruff check packages/core/src/zorivest_core/domain/portfolio_balance.py
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/portfolio_balance.py || Write-Output "Anti-placeholder: clean"

# MEU-10
uv run pytest tests/unit/test_display_mode.py -x --tb=short -m "unit" -v
uv run pytest tests/unit/ -x --tb=short -m "unit"
uv run pyright packages/core/src/zorivest_core/domain/display_mode.py
uv run ruff check packages/core/src/zorivest_core/domain/display_mode.py
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/display_mode.py || Write-Output "Anti-placeholder: clean"

# MEU-11
uv run pytest tests/unit/test_account_review.py -x --tb=short -m "unit" -v
uv run pytest tests/unit/ -x --tb=short -m "unit"
uv run pyright packages/core/src/zorivest_core/domain/account_review.py
uv run ruff check packages/core/src/zorivest_core/domain/account_review.py
rg "TODO|FIXME|NotImplementedError" packages/core/src/zorivest_core/domain/account_review.py || Write-Output "Anti-placeholder: clean"
```

### Phase Gate (run AFTER all 3 MEUs pass)

After MEU-11 is approved, Phase 1 is complete. Run the full phase gate:

```powershell
.\tools\validate.ps1
```

---

## Stop Conditions

- ❌ Do NOT commit or push
- ❌ Do NOT start Track B (logging MEUs)
- ❌ Do NOT modify existing `calculator.py`, `enums.py`, `entities.py`, `value_objects.py`, `ports.py`, `commands.py`, `queries.py`, `dtos.py`, `events.py`, or `analytics/`
- ❌ Do NOT build GUI components (Phase 6), MCP tools (Phase 5), or API routes (Phase 4)
- ❌ Do NOT implement API fetch logic for broker accounts (Phase 2+)
- ✅ Save session state to `pomera_notes` at end
- ✅ Present commit messages to human
