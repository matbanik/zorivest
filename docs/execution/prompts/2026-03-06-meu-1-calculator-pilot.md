# Zorivest Day-1 Prompt - MEU-1 Calculator Pilot

> Purpose: paste this into a fresh Opus 4.6 / Antigravity session.
>
> Read-first workflow set:
> - `.agent/workflows/execution-session.md`
> - `.agent/workflows/tdd-implementation.md`
> - `.agent/workflows/meu-handoff.md`

---

## Session Contract

Read these files in order before planning or coding:

1. `SOUL.md`
2. `GEMINI.md`
3. `AGENTS.md`
4. `.agent/context/current-focus.md`
5. `.agent/context/known-issues.md`
6. `.agent/context/meu-registry.md`
7. `docs/build-plan/01-domain-layer.md` sections 1.1 and 1.3
8. `docs/build-plan/testing-strategy.md`
9. `.agent/workflows/execution-session.md`
10. `.agent/workflows/tdd-implementation.md`
11. `.agent/workflows/meu-handoff.md`
12. `.agent/workflows/validation-review.md`

Task: complete MEU-1 only as the day-1 pilot.

In scope:
- the minimum Python workspace/bootstrap needed to run MEU-1
- `PositionSizeResult` and `calculate_position_size()`
- tests for all MEU-1 acceptance criteria
- the MEU handoff artifact
- MEU registry status update
- session note in `pomera_notes`
- execution reflection and metrics update after implementation

Out of scope:
- all future-MEU modules and package scaffolds that are not required for MEU-1
- `entities.py`, `value_objects.py`, `enums.py`, `events.py`, `ports.py`, `commands.py`, `dtos.py`, `services/`, and any infrastructure/api/ui/mcp work
- placeholder stubs for future work
- auto-commits
- unrelated documentation rewrites

If any repo rule conflicts with this prompt, stop and ask the human before proceeding.

---

## Planning Phase

Start in PLANNING mode.

Before coding, generate both:
- `implementation_plan.md`
- `task.md`

The plan must include a table where every task has:
- `task`
- `owner_role`
- `deliverable`
- `validation`
- `status`

The plan must also include:
- exact file paths to create or modify
- the MEU-1 Feature Intent Contract
- exact validation commands for this run
- explicit stop conditions
- the handoff file path to write

Present the plan to the human for approval before switching to EXECUTION mode.

After approval, archive the approved planning artifacts into:
- `docs/execution/plans/2026-03-06-implementation-plan.md`
- `docs/execution/plans/2026-03-06-task.md`

Use the native shell for the host OS. On PowerShell, the archive step is:

```powershell
Copy-Item "$HOME\.gemini\antigravity\brain\{conversation-id}\implementation_plan.md" `
  "docs\execution\plans\2026-03-06-implementation-plan.md"

Copy-Item "$HOME\.gemini\antigravity\brain\{conversation-id}\task.md" `
  "docs\execution\plans\2026-03-06-task.md"
```

---

## Execution Phase

### A. Minimum Bootstrap Only

Create only the files required to execute MEU-1:

- `pyproject.toml`
- `packages/core/pyproject.toml`
- `packages/core/src/zorivest_core/__init__.py`
- `packages/core/src/zorivest_core/domain/__init__.py`
- `packages/core/src/zorivest_core/domain/calculator.py`
- `tests/conftest.py`
- `tests/unit/__init__.py`
- `tests/unit/test_calculator.py`

Create additional config only if it is required to make the MEU-1 test, lint, or type-check commands deterministic.

Do not create future-MEU modules just to mirror the final target tree.

For `pyproject.toml`, include at least:

```toml
[project]
name = "zorivest"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["packages/*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
  "unit: Pure unit tests",
  "integration: Integration tests with real DB",
  "e2e: End-to-end tests",
]
```

For `packages/core/pyproject.toml`, create a normal Python package build config for `src/zorivest_core`.

Install only the day-1 Python tooling needed for this pilot:

```powershell
uv sync
uv add --dev pytest pyright ruff
```

### B. MEU-1 Feature Intent Contract

Write the FIC before writing implementation code.

Intent statement:
- The calculator accepts account balance, risk percentage, entry, stop, and target prices and returns a frozen result dataclass with seven computed fields using pure arithmetic only.

Acceptance criteria:
- AC-1: Basic calculation matches the known values in `docs/build-plan/01-domain-layer.md` section 1.3.
- AC-2: Zero entry returns zero shares and zero risk per share.
- AC-3: Risk percentage out of range (`<= 0` or `> 100`) defaults to `1%`.
- AC-4: `entry == stop` returns zero shares and zero reward/risk ratio.
- AC-5: Zero balance returns `0.0` for position-to-account percentage.
- AC-6: `PositionSizeResult` is a frozen dataclass.
- AC-7: The implementation is pure and imports only `__future__`, `math`, and `dataclasses`.

Negative cases:
- Must not raise for numeric inputs covered by the FIC.
- Must not import from any other Zorivest module.
- Must not change tests in Green phase to force a pass.

### C. Red Phase

Create `tests/unit/test_calculator.py` first.

Requirements for the test module:
- cover all seven acceptance criteria
- use the calculator values from `docs/build-plan/01-domain-layer.md` section 1.3
- include a frozen-dataclass immutability test
- include an import-surface test for AC-7
- set module-level unit marking so the shared unit-suite command is deterministic

Suggested command:

```powershell
uv run pytest tests/unit/test_calculator.py -x --tb=short -v
```

Capture the failing output for the handoff FAIL_TO_PASS table.

### D. Green Phase

Implement only:
- `packages/core/src/zorivest_core/domain/calculator.py`

Do not broaden scope beyond the calculator.

Suggested command:

```powershell
uv run pytest tests/unit/test_calculator.py -x --tb=short -v
```

### E. Verification Gate for This Session

Run these commands after Green:

```powershell
uv run pytest tests/unit/ -x --tb=short -v
uv run pyright packages/core/src
uv run ruff check packages/core/src tests
rg "TODO|FIXME|NotImplementedError|pass\s+#\s*placeholder" packages tests
```

Run `.\validate.ps1` only as an informational probe after the MEU gate above.

If `.\validate.ps1` fails because unrelated repo surfaces are intentionally out of scope on day 1, do not widen scope to "fix the repo." Record the exact failure in the handoff under known risks / follow-up required and stop at `ready_for_review`.

### F. Handoff and State

Create the handoff file:
- `.agent/context/handoffs/2026-03-06-meu-1-calculator.md`

Use `.agent/workflows/meu-handoff.md` and include:
- scope summary
- FIC
- test mapping
- changed files
- commands executed with results
- FAIL_TO_PASS evidence
- design decisions
- known risks and follow-up items

Update:
- `.agent/context/meu-registry.md` -> set MEU-1 to `ready_for_review`

Save session state to `pomera_notes` with:
- title: `Memory/Session/Zorivest-MEU-1-2026-03-06`

Do not create git commits. Instead, propose the exact conventional commit message(s) to the human in your final summary.

---

## Codex Validation Trigger

After implementation is complete, give the human this exact follow-up text for a separate Codex session:

```text
Follow .agent/workflows/validation-review.md exactly.

Read the handoff at .agent/context/handoffs/2026-03-06-meu-1-calculator.md.
Read all changed files listed in the handoff.
Run the validation workflow and append the Codex Validation Report to the handoff.

Scope: packages/core/src/ and tests/unit/ only.
```

---

## Post-Execution Reflection

After the implementation and handoff are complete:

1. Create `docs/execution/reflections/2026-03-06-reflection.md` from `docs/execution/reflections/TEMPLATE.md`.
2. Update the Day 1 row in `docs/execution/metrics.md` using the existing table columns already in that file.
3. In the reflection, state at least:
   - what slowed the session down
   - what instructions were ambiguous
   - what should change in the next prompt
   - whether `validate.ps1` was usable as a MEU gate or only as a later checkpoint

---

## Completion Target

This session is successful when all of the following are true:

- MEU-1 tests were written first and shown failing before implementation
- calculator implementation is green on the day-1 MEU gate
- handoff file exists and is self-contained
- MEU registry is updated to `ready_for_review`
- `pomera_notes` entry exists
- reflection file exists
- metrics row is updated
- the human receives the Codex validation trigger text and proposed commit message(s)
