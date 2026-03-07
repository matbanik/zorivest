# Task: commands-events-analytics (v3)

> Project: `2026-03-07-commands-events-analytics`
> MEUs: MEU-6, MEU-7, MEU-8
> Plan: [implementation-plan.md](file:///p:/zorivest/docs/execution/plans/2026-03-07-commands-events-analytics/implementation-plan.md)

---

## Gate

- [x] Confirm all deps ✅ (MEU-1–5 approved in registry)

## MEU-6: Commands & DTOs (bp01 §1.2)

- [x] Write FIC acceptance criteria (AC-1 through AC-20)
- [x] Write `tests/unit/test_commands_dtos.py` — Red phase (all tests fail)
- [x] Implement `application/commands.py` (CreateTrade, AttachImage, CreateAccount, UpdateBalance)
- [x] Implement `application/queries.py` (GetTrade, ListTrades, GetAccount, ListAccounts, GetImage, ListImages)
- [x] Implement `application/dtos.py` (TradeDTO, AccountDTO, BalanceSnapshotDTO, ImageAttachmentDTO)
- [x] Green phase — all tests pass
- [x] Quality gate: `pyright`, `ruff check`, anti-placeholder scan
- [x] Create handoff: `004-2026-03-07-commands-dtos-bp01s1.2.md`
- [x] Update MEU registry: MEU-6 → 🟡
- [x] Codex validation (reviewer) — approved 2026-03-07

## MEU-7: Domain Events (bp01 §1.2)

- [x] Write FIC acceptance criteria (AC-1 through AC-7)
- [x] Write `tests/unit/test_events.py` — Red phase
- [x] Implement `domain/events.py` (DomainEvent, TradeCreated, BalanceUpdated, ImageAttached, PlanCreated)
- [x] Green phase — all tests pass
- [x] Quality gate: `pyright`, `ruff check`, anti-placeholder scan
- [x] Create handoff: `005-2026-03-07-events-bp01s1.2.md`
- [x] Update MEU registry: MEU-7 → 🟡
- [x] Codex validation (reviewer) — approved 2026-03-07

## MEU-8: Analytics — Result Types + Expectancy + SQN (bp01 §1.2)

- [x] Write FIC acceptance criteria (AC-1 through AC-19)
- [x] Write `tests/unit/test_analytics.py` — Red phase
- [x] Implement `domain/analytics/__init__.py`
- [x] Implement `domain/analytics/results.py` (all 8 result types from 03-service-layer.md)
- [x] Implement `domain/analytics/expectancy.py` (calculate_expectancy)
- [x] Implement `domain/analytics/sqn.py` (calculate_sqn)
- [x] Green phase — all tests pass
- [x] Quality gate: `pyright`, `ruff check`, anti-placeholder scan
- [x] Create handoff: `006-2026-03-07-analytics-bp01s1.2.md`
- [x] Update MEU registry: MEU-8 → 🟡
- [x] Codex validation (reviewer) — approved 2026-03-07

## Post-Project (after Codex validation)

- [x] Create reflection (after all Codex verdicts, per `execution-session.md` §5)
- [x] Update metrics table
- [x] Save session state to `pomera_notes`
- [x] Present commit messages to human
