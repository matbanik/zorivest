# MEU-88: SendStep — Task List

## TDD Implementation

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 1 | Write red-phase tests (AC-S1..AC-S20) | coder | `tests/unit/test_send_step.py` | `uv run pytest tests/unit/test_send_step.py -v` — 20 FAILED | [x] |
| 2 | Implement `send_step.py` | coder | `packages/core/src/zorivest_core/pipeline_steps/send_step.py` | `uv run pytest tests/unit/test_send_step.py -k "ac_s1 or ac_s2 or ac_s3 or ac_s4 or ac_s5 or ac_s6 or ac_s7 or ac_s8 or ac_s9 or ac_s15 or ac_s16 or ac_s17 or ac_s20" -v` | [x] |
| 3 | Implement `email_sender.py` | coder | `packages/infrastructure/src/zorivest_infra/email/email_sender.py` | `uv run pytest tests/unit/test_send_step.py -k "ac_s12 or ac_s13 or ac_s14" -v` | [x] |
| 4 | Implement `delivery_tracker.py` | coder | `packages/infrastructure/src/zorivest_infra/email/delivery_tracker.py` | `uv run pytest tests/unit/test_send_step.py -k "ac_s10 or ac_s11" -v` | [x] |
| 5 | Create email `__init__.py` | coder | `packages/infrastructure/src/zorivest_infra/email/__init__.py` | `uv run python -c "import zorivest_infra.email"` | [x] |
| 6 | Update pipeline_steps `__init__.py` | coder | Add `send_step` import | `uv run python -c "from zorivest_core.domain.step_registry import get_step; assert get_step('send') is not None"` | [x] |
| 7 | Add `DeliveryRepository` to `scheduling_repositories.py` | coder | `packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py` | `uv run pytest tests/unit/test_send_step.py -k "ac_s18 or ac_s19" -v` | [x] |
| 8 | Add `deliveries` property to `SqlAlchemyUnitOfWork` | coder | `packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | `uv run python -c "from zorivest_infra.database.unit_of_work import SqlAlchemyUnitOfWork"` | [x] |
| 9 | Add `aiosmtplib` dependency | coder | `packages/infrastructure/pyproject.toml` | `uv run python -c "import aiosmtplib"` | [x] |
| 10 | All 20 AC tests green | tester | — | `uv run pytest tests/unit/test_send_step.py -v` — 20 PASSED | [x] |
| 11 | Full regression green | tester | — | `uv run pytest tests/ -v` | [x] |
| 12 | Type check clean | tester | — | `uv run pyright packages/core/src/zorivest_core/pipeline_steps/send_step.py packages/infrastructure/src/zorivest_infra/email/ packages/infrastructure/src/zorivest_infra/database/scheduling_repositories.py packages/infrastructure/src/zorivest_infra/database/unit_of_work.py` | [x] |

## Post-MEU Deliverables

| # | task | owner_role | deliverable | validation | status |
|---|------|------------|-------------|------------|--------|
| 11 | MEU gate | tester | — | `uv run python tools/validate_codebase.py --scope meu` | [x] |
| 12 | Update meu-registry.md | coder | MEU-88 row | `rg "MEU-88" .agent/context/meu-registry.md` | [x] |
| 13 | Update BUILD_PLAN.md | coder | MEU-88 ✅, P2.5 12, total 77 | `rg "MEU-88.*✅" docs/BUILD_PLAN.md` | [x] |
| 14 | Create handoff | coder | `075-2026-03-17-send-step-bp09s9.8.md` | `Test-Path .agent/context/handoffs/075-2026-03-17-send-step-bp09s9.8.md` returns True; `rg "## Evidence" .agent/context/handoffs/075-2026-03-17-send-step-bp09s9.8.md` | [x] |
| 15 | Create reflection | coder | `docs/execution/reflections/2026-03-17-send-step-reflection.md` | `Test-Path docs/execution/reflections/2026-03-17-send-step-reflection.md` returns True | [x] |
| 16 | Update metrics table | coder | `docs/execution/metrics.md` | `rg "send-step" docs/execution/metrics.md` returns row | [x] |
| 17 | Save session state | coder | pomera_notes | `pomera_notes search --search_term "Memory/Session/SendStep*" --limit 1` returns note | [x] |
| 18 | Prepare commit messages | coder | — | `rg "MEU-88" .agent/context/handoffs/075-2026-03-17-send-step-bp09s9.8.md` | [x] |
